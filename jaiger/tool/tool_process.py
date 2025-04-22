import time
import traceback
from multiprocessing import Event, Process
from multiprocessing.connection import Connection
from typing import Type

from jaiger.configs import ToolConfig
from jaiger.models import Call, CallResult
from jaiger.tool.tool import Tool


class ToolProcess(Process):
    def __init__(
        self,
        start_event: Event,
        stop_event: Event,
        tool_class: Type[Tool],
        config: ToolConfig,
        conn: Connection,
    ):
        super().__init__()

        self._start_event = start_event
        self._stop_event = stop_event
        self._tool_class = tool_class
        self._config = config
        self._conn = conn

    def run(self):
        self._start_event.set()

        tool = None

        try:
            tool = self._tool_class(self._config)
            tool.setup()
            while not self._stop_event.is_set():
                try:
                    if self._conn.poll():
                        request: Call = self._conn.recv()
                        function = getattr(tool, request.function)
                        self._conn.send(
                            CallResult(result=function(*request.args, **request.kwargs))
                        )

                except Exception as e:
                    self._conn.send(
                        CallResult(
                            error="".join(
                                traceback.TracebackException.from_exception(e).format()
                            )
                        )
                    )

                time.sleep(0)

        except Exception as e:
            self._conn.send(
                CallResult(
                    error="".join(
                        traceback.TracebackException.from_exception(e).format()
                    )
                )
            )

        finally:
            if tool is not None:
                tool.teardown()

            self._conn.close()

    def stop(self):
        self._stop_event.set()
