from concurrent.futures import Future, ThreadPoolExecutor
from logging import getLogger
from multiprocessing.connection import Connection
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel

from jaiger.models import Call, CallResult
from jaiger.tool import Tool, ToolSpec
from jaiger.tool_process import ToolProcess


class ToolInfo(BaseModel):
    name: str
    specs: List[ToolSpec]


class ToolManager:
    def __init__(self):
        self._conns: Dict[str, Connection] = {}
        self._processes: Dict[str, ToolProcess] = {}

        self._pool = ThreadPoolExecutor()

        self._logger = getLogger("jaiger")

    def tools(self) -> List[ToolInfo]:
        def get_tool_info(name: str, conn: Connection) -> ToolInfo:
            conn.send(Call(function=Tool.specs.__name__))
            result: CallResult = conn.recv()

            return ToolInfo(name=name, specs=result.result)

        return [
            tool_info for tool_info in self._pool.map(lambda kv: get_tool_info(kv[0], kv[1]), self._conns.items())
        ]

    def start(
        self, name: str, conn: Connection, tool_process: ToolProcess
    ) -> "ToolManager":
        if name in self._conns:
            raise ValueError(f'Tool named "{name}" already exists!')
        else:
            self._conns[name] = conn
            self._processes[name] = tool_process
            tool_process.start()

        return self

    def start_many(
        self, args: List[Tuple[str, Connection, ToolProcess]]
    ) -> "ToolManager":
        processes = []
        for name, _, _ in args:
            if name in self._conns:
                raise ValueError(f'Tool named "{name}" already exists!')

        for name, conn, tool_process in args:
            self._conns[name] = conn
            self._processes[name] = tool_process
            processes.append(tool_process)

        for _ in self._pool.map(lambda p: p.start(), processes):
            pass

        return self

    def stop(self, name: str) -> "ToolManager":
        if name not in self._conns:
            raise ValueError(f'Tool named "{name}" does not exist!')
        else:
            process = self._processes[name]
            process.stop()
            process.join(timeout=10)

            if process.is_alive():
                self._logger.warning(
                    f"Tried to terminate tool '{name}' (PID: {process.pid}) but it is still alive."
                )

            del self._conns[name]
            del self._processes[name]

        return self

    def stop_many(self, names: List[str]) -> "ToolManager":
        for name in names:
            if name not in self._conns:
                raise ValueError(f'Tool named "{name}" does not exist!')

        def stop_process(process: ToolProcess):
            process = self._processes[name]
            process.stop()
            process.join(timeout=10)

            if process.is_alive():
                self._logger.warning(
                    f"Tried to terminate tool '{name}' (PID: {process.pid}) but it is still alive."
                )

        for _ in self._pool.map(
            stop_process, (self._processes[name] for name in names)
        ):
            pass

        for name in names:
            del self._conns[name]
            del self._processes[name]

        return self

    def call(
        self,
        tool: str,
        function: str,
        args: List[Any] = list(),
        kwargs: Dict[str, Any] = dict(),
    ) -> Any:
        if tool not in self._conns:
            raise ValueError(f'Tool named "{tool}" does not exist!')
        else:
            conn = self._conns[tool]
            conn.send(Call(function=function, args=args, kwargs=kwargs))
            result: CallResult = conn.recv()

            if result.error is not None:
                raise RuntimeError(
                    f"Error when calling {tool}:\n"
                    f"> function: {function}\n"
                    f"> args: {args}\n"
                    f"> kwargs: {kwargs}\n"
                    f"Error message:\n{result.error}"
                )
            else:
                return result.result

    def call_async(
        self,
        tool: str,
        function: str,
        args: List[Any] = list(),
        kwargs: Dict[str, Any] = dict(),
    ) -> Future:
        return self._pool.submit(self.call, tool, function, args, kwargs)
