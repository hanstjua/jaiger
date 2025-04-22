import traceback
from logging import getLogger
from threading import Event, Thread
from typing import Any, Callable, Dict, Optional

import uvicorn
from fastapi import FastAPI

from jaiger.configs import HttpConfig
from jaiger.models import Call, CallResult


class HttpServer:
    """
    A FastAPI-based HTTP server that exposes RPC endpoints and dispatches requests
    to registered callback functions.
    """

    def __init__(
        self, config: HttpConfig, callbacks: Dict[str, Callable[[Any], Any]]
    ) -> None:
        """
        Initializes the HTTP server with given configuration and callbacks.

        :param config HttpConfig: Configuration for server setup.
        :param callbacks Dict[str, Callable[[Any], Any]]: Registered RPC function handlers.
        """

        self._host = config.host
        self._port = config.port
        self._timeout = config.timeout
        self._callbacks = callbacks

        self._logger = getLogger("jaiger")

        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[Thread] = None

    def start(self) -> "HttpServer":
        """
        Starts the HTTP server in a background thread.

        If an existing thread is already running, it will be stopped first.

        :returns: The instance itself for chaining.
        :rtype: HttpServer
        """

        if self._thread is not None:
            self._logger.warning(
                f"Terminating existing server thread ({self._thread.native_id}) ..."
            )
            self.stop()

        app = FastAPI()
        app.post("/call")(self.call)

        self._server = uvicorn.Server(
            uvicorn.Config(app=app, host=self._host, port=self._port, workers=4)
        )

        def run_server(e: Event):
            e.set()
            self._server.run()

        start_event = Event()
        self._thread = Thread(
            target=run_server,
            args=(start_event,),
            daemon=True,
        )
        self._thread.start()

        start_event.wait()

        self._logger.info(f"Server thread ({self._thread.native_id}) has started.")

        return self

    def stop(self) -> "HttpServer":
        """
        Stops the running HTTP server gracefully.

        Waits for the server thread to terminate within the timeout period.

        :returns: The instance itself for chaining.
        :rtype: HttpServer
        """

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
        """
        Handles an incoming HTTP call.

        Dispatches the request to the appropriate callback and returns the result.
        If an error occurs during execution, a formatted traceback is returned.

        :param call Call: The incoming HTTP call containing function name and arguments.

        :returns: A CallResult object with either a result or an error.
        :rtype: CallResult
        """

        try:
            return CallResult(
                result=self._callbacks[call.function](
                    *call.args, **call.kwargs
                )
            )

        except Exception as e:
            return CallResult(
                error="".join(traceback.TracebackException.from_exception(e).format())
            )
