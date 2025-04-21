import json
import traceback
from concurrent.futures import Future
from logging import getLogger
from logging.config import dictConfig
from multiprocessing import Event, Pipe
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from jaiger.ai.ai_manager import AiManager
from jaiger.configs import MainConfig
from jaiger.http.http_server import HttpServer
from jaiger.models import CallResult, ToolCall
from jaiger.rpc.rpc_broker import RpcBroker
from jaiger.rpc.rpc_server import RpcServer
from jaiger.tool.tool_manager import ToolInfo, ToolManager
from jaiger.tool.tool_process import ToolProcess
from jaiger.utils import get_tool_class


class Jaiger:
    """The main class for the Jaiger application, managing AI models, tools, and communication servers."""

    def __init__(self, config: str) -> None:
        """
        Initializes the Jaiger application.

        :param config str: Path to the main configuration file.
        :raises FileNotFoundError: If the configuration file is not found.
        """

        self._config_path = config

        # load config
        p = Path(config)
        if not p.is_file():
            raise FileNotFoundError(f"Failed to load config: {config}")

        self._config = MainConfig.model_validate(json.loads(p.read_text()))

        # configure logger
        dictConfig(
            {
                "version": 1,
                "formatters": {
                    "default": {
                        "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s"
                    }
                },
                "handlers": {
                    "console": {
                        "class": "logging.StreamHandler",
                        "formatter": "default",
                        "level": "DEBUG",
                    }
                },
                "loggers": {"jaiger": {"level": "INFO", "handlers": ["console"]}},
            }
        )

        self._logger = getLogger("jaiger")

        callbacks = {
            self.call_tool.__name__: self.call_tool,
            self.call_tool_async.__name__: self.call_tool_async,
            self.ais.__name__: self.ais,
            self.config.__name__: self.config,
            self.tools.__name__: self.tools,
            self.call_tool.__name__: self.call_tool,
            self.call_tool_async.__name__: self.call_tool_async,
            self.prompt.__name__: self.prompt,
        }

        self._rpc_broker: Optional[RpcBroker] = None
        self._rpc_server: Optional[RpcServer] = None
        if self._config.settings.server.rpc is not None:
            self._rpc_broker = RpcBroker(self._config.settings.server.rpc)
            self._rpc_server = RpcServer(
                "jaiger", self._config.settings.server.rpc, callbacks
            )

        self._http_server: Optional[HttpServer] = None
        if self._config.settings.server.http:
            self._http_server = HttpServer(self._config.settings.server.http, callbacks)

        self._ai_manager = AiManager()
        self._tool_manager = ToolManager()

    def start(self) -> "Jaiger":
        """
        Starts the Jaiger application, including tool processes and AI model registration.

        :returns: The Jaiger instance itself for method chaining.
        :rtype: Jaiger
        """

        for config in self._config.tools:
            conn1, conn2 = Pipe()
            start_event = Event()
            stop_event = Event()
            self._tool_manager.start(
                config.name,
                conn1,
                ToolProcess(
                    start_event, stop_event, get_tool_class(config.type), config, conn2
                ),
            )

        for config in self._config.ais:
            self._ai_manager.add_ai(config)

        self._ai_manager.register_tools(self._tool_manager.tools())

        return self

    def stop(self) -> "Jaiger":
        """
        Stops the Jaiger application, terminating tool processes and removing AI models.

        :returns: The Jaiger instance itself for method chaining.
        :rtype: Jaiger
        """

        for tool in self._tool_manager.tools():
            self._tool_manager.stop(tool.name)

        for ai in self._ai_manager.ais():
            self._ai_manager.remove_ai(ai)

        return self

    def ais(self) -> List[str]:
        """
        Returns a list of the names of the currently managed AI models.

        :returns: A list of AI model names.
        :rtype: List[str]
        """

        return self._ai_manager.ais()

    def config(self) -> MainConfig:
        """
        Returns the main configuration object.

        :returns: The main configuration.
        :rtype: MainConfig
        """

        return self._config

    def tools(self) -> List[ToolInfo]:
        """
        Returns a list of information about the currently managed tools.

        :returns: A list of ToolInfo objects.
        :rtype: List[ToolInfo]
        """

        return self._tool_manager.tools()

    def call_tool(
        self,
        tool: str,
        function: str,
        args: List[Any] = list(),
        kwargs: Dict[str, Any] = dict(),
    ) -> Any:
        """
        Synchronously calls a specific function of a managed tool.

        :param tool str: The name of the tool to call.
        :param function str: The name of the function to execute.
        :param args List[Any]: Positional arguments to pass to the function (default: empty list).
        :param kwargs Dict[str, Any]: Keyword arguments to pass to the function (default: empty dictionary).
        :returns: The result of the tool function call.
        :rtype: Any
        """

        return self._tool_manager.call(tool, function, args, kwargs)

    def call_tool_async(
        self,
        tool: str,
        function: str,
        args: List[Any] = list(),
        kwargs: Dict[str, Any] = dict(),
    ) -> Future:
        """
        Asynchronously calls a specific function of a managed tool.

        :param tool str: The name of the tool to call.
        :param function str: The name of the function to execute.
        :param args List[Any]: Positional arguments to pass to the function (default: empty list).
        :param kwargs Dict[str, Any]: Keyword arguments to pass to the function (default: empty dictionary).
        :returns: A Future object representing the result of the asynchronous call.
        :rtype: Future
        """

        return self._tool_manager.call_async(tool, function, args, kwargs)

    def prompt(
        self,
        name: str,
        text: str,
        auto_call: bool = True,
        on_call: Optional[Callable[[ToolCall], None]] = None,
        on_result: Optional[Callable[[ToolCall, CallResult], None]] = None,
    ) -> str:
        """
        Sends a prompt to a specific AI model and handles potential tool calls.

        :param name str: The name of the AI model to prompt.
        :param text str: The input text to send to the AI model.
        :param auto_call bool: Whether to automatically call tools identified by the AI (default: True).
        :param on_call Optional[Callable[[ToolCall], None]]: An optional callback function to be executed before a tool is called. Receives the ToolCall object.
        :param on_result Optional[Callable[[ToolCall, CallResult], None]]: An optional callback function to be executed after a tool call returns. Receives the ToolCall and CallResult objects.
        :returns: The final response from the AI model after handling any tool calls. If auto_call is False and tool calls are identified, returns a JSON string of the ToolCall objects.
        :rtype: str
        """

        result = self._ai_manager.prompt(name, text)

        if auto_call:
            while result.calls is not None:
                call_results = []
                for call in result.calls:
                    if on_call is not None:
                        try:
                            on_call(call)
                        except Exception as e:
                            self._logger.error(
                                "Error when calling on_call hook:\n"
                                f"{''.join(traceback.TracebackException.from_exception(e).format())}"
                            )
                    try:
                        result = CallResult(
                            result=self._tool_manager.call(
                                call.tool, call.function, call.args, call.kwargs
                            ),
                            error=None,
                        )

                    except Exception as e:
                        result = CallResult(result=None, error=repr(e))

                    if on_result is not None:
                        try:
                            on_result(call, result)
                        except Exception as e:
                            self._logger.error(
                                "Error when calling on_result hook:\n"
                                f"{''.join(traceback.TracebackException.from_exception(e).format())}"
                            )

                    call_results.append(result.model_dump())

                result = self._ai_manager.prompt(name, json.dumps(call_results))

            return result.text

        else:
            ret = result.text
            if ret is None:
                ret = json.dumps([call.model_dump() for call in result.calls])

            return ret
