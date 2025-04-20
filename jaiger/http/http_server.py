from logging import getLogger
from threading import Event, Thread
import traceback
from typing import Any, Callable, Dict, Optional
from fastapi import FastAPI
import uvicorn

from jaiger.configs import HttpConfig
from jaiger.models import Call, CallResult


class HttpServer:
    def __init__(
        self, config: HttpConfig, callbacks: Dict[str, Callable[[Any], Any]]
    ) -> None:
        self._host = config.host
        self._port = config.port
        self._timeout = config.timeout
        self._callbacks = callbacks

        self._logger = getLogger("jaiger")

        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[Thread] = None

    def start(self) -> "HttpServer":
        if self._thread is not None:
            self._logger.warning(
                f"Terminating existing server thread ({self._thread.native_id}) ..."
            )
            self.stop()

        app = FastAPI()
        app.post('/call')(self.call)

        self._server = uvicorn.Server(
            uvicorn.Config(app=app, host=self._host, port=self._port, workers=4)
        )

        start_event = Event()
        self._thread = Thread(
            target=lambda e: e.set() and self._server.run(),
            args=(start_event,),
            daemon=True,
        )
        self._thread.start()

        start_event.wait()

        self._logger.info(f"Server thread ({self._thread.native_id}) has started.")

        return self

    def stop(self) -> "HttpServer":
        if self._thread is not None:
            self._server.should_exit = True

            self._thread.join(timeout=self._timeout)
            if self._thread.is_alive():
                self._logger.warning(
                    f"Server thread ({self._thread.native_id}) is not terminated."
                )
            else:
                self._logger.info(
                    f"Server thread ({self._thread.native_id}) has been terminated."
                )

            self._thread = None
            self._server = None

        return self
    
    def call(self, call: Call):
        try:
            return CallResult(
                result=self._callbacks[call.function](
                    call.function,
                    call.args,
                    call.kwargs
                )
            )
        
        except Exception as e:
            return CallResult(
                error=''.join(traceback.TracebackException.from_exception(e).format())
            )
