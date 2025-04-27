import time
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Queue
import traceback
from typing import Callable

import uvicorn
from components import ReplyBubble, ReplyLoading, Root, UserBubble
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel
from jaiger.configs import HttpConfig
from jaiger.http.http_client import HttpClient

from jaiger.main import Jaiger


class PromptParams(BaseModel):
    text: str

class App(FastAPI):
    def __init__(self, http_config: HttpConfig, on_quit: Callable[[], None], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.get("/")(self.index)
        self.post("/prompt")(self.prompt)
        self.get("/reset")(self.reset)
        self.get("/sse")(self.sse)
        self.get("/quit")(self.quit)

        self._events_queue = Queue()

        self._pool = ThreadPoolExecutor()

        self._jaiger_client = HttpClient(http_config)

        self._on_quit = on_quit

    def index(self):
        return HTMLResponse(Root().render(0))

    def prompt(self, params: PromptParams):
        def get_ai_answer():
            try:
                result = self._jaiger_client.call("prompt", ["my_ai", params.text])
                if result.error:
                    raise RuntimeError(f'Error while prompting:\n{result.error}')
                answer = result.result
            except Exception as e:
                answer = ''.join(traceback.TracebackException.from_exception(e).format())

            event = f"event: newResponse\ndata: {ReplyBubble(answer).render(0)}\n\n"
            self._events_queue.put(event)

        response = HTMLResponse(
            UserBubble(params.text).render() + ReplyLoading().render()
        )

        self._pool.submit(get_ai_answer)

        return response

    def sse(self):
        return StreamingResponse(
            self.events_generator(), media_type="text/event-stream"
        )

    def reset(self):
        try:
            self._jaiger_client.call("stop")
            self._jaiger_client.call("start")

            return RedirectResponse("/")

        except Exception as e:
            return HTMLResponse(f"Failed to reset:\n{''.join(traceback.TracebackException.from_exception(e).format())}")

    def events_generator(self):
        item = ""
        while True:
            try:
                item = self._events_queue.get()
                if item == "stop":
                    break
                else:
                    yield item
            except Empty:
                time.sleep(0.01)

    def quit(self):
        self._events_queue.put("stop")
        self._pool.shutdown(wait=False)

        self._on_quit()

        return HTMLResponse("<h1>Bye bye</h1>")
    
    def on_call(self, call):
        args = [repr(arg) for arg in call.args] + [
            f"{k}={repr(v)}" for k, v in call.kwargs.items()
        ]

        message = f"Calling {call.tool}.{call.function}({', '.join(args)}) ..."

        event = f'event: newCall\ndata: <p sse-swap="newCall" hx-swap="outerHTML">{message}</p>\n\n'
        self._events_queue.put(event)


class WebUiApp(Jaiger):
    def __init__(self, config: str) -> None:
        super().__init__(config)

        self._app = App(self.config().settings.server.http, self._stop_server, workers=2)

        self._server = uvicorn.Server(
            uvicorn.Config(app=self._app, host="127.0.0.1", port=7613, workers=2)
        )

    def __enter__(self):
        self.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def run(self):
        print(f"Starting web ui at http://127.0.0.1:7613 ...")
        self._server.run()

    def prompt(
            self,
            name: str,
            text: str
        ) -> str:
        return super().prompt(
            name,
            text,
            on_call=self._app.on_call
        )
    
    def _stop_server(self):
        self._server.should_exit = True


if __name__ == "__main__":
    from pathlib import Path

    with WebUiApp(Path(__file__).parent / "web_ui_app.json") as app:
        app.run()
