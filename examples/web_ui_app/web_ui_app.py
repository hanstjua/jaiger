import time
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Queue

import uvicorn
from components import ReplyBubble, ReplyLoading, Root, UserBubble
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from jaiger.main import Jaiger


class PromptParams(BaseModel):
    text: str


class WebUiApp:
    def __init__(self, config: str) -> None:
        self._jaiger = Jaiger(config)

        app = FastAPI()
        app.get("/")(self.index)
        app.post("/prompt")(self.prompt)
        app.post("/new-chat")(self.new_chat)
        app.get("/sse")(self.sse)
        app.get("/quit")(self.quit)

        self._server = uvicorn.Server(
            uvicorn.Config(app=app, host="127.0.0.1", port=7613, workers=2)
        )

        self._events_queue = Queue()

        self._pool = ThreadPoolExecutor()

    def __enter__(self):
        self._jaiger.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._jaiger.stop()
        self._pool.shutdown()

    def on_call(self, call):
        args = [repr(arg) for arg in call.args] + [
            f"{k}={repr(v)}" for k, v in call.kwargs.items()
        ]

        message = f"Calling {call.tool}.{call.function}({', '.join(args)}) ..."

        event = f'event: newCall\ndata: <p sse-swap="newCall" hx-swap="outerHTML">{message}</p>\n\n'
        self._events_queue.put(event)

    def run(self):
        print(f"Starting web ui at http://127.0.0.1:7613 ...")
        self._server.run()

    async def index(self):
        return HTMLResponse(Root().render(0))

    async def prompt(self, params: PromptParams):
        def get_ai_answer():
            answer = self._jaiger.prompt("my_ai", params.text, on_call=self.on_call)
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

    async def new_chat(self):
        self._jaiger.stop()

        self._jaiger.start()

        return HTMLResponse("")

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

    async def quit(self):
        self._server.should_exit = True
        self._events_queue.put("stop")

        return HTMLResponse("")


if __name__ == "__main__":
    from pathlib import Path

    with WebUiApp(Path(__file__).parent / "web_ui_app.json") as app:
        app.run()
