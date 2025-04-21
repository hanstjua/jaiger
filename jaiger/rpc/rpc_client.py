from concurrent.futures import Future, ThreadPoolExecutor
from logging import getLogger
from typing import Any, Dict, List, Optional

import zmq

from jaiger.configs import RpcConfig
from jaiger.models import Call, CallResult


class RpcClient:
    """
    A ZeroMQ-based RPC client for sending synchronous and asynchronous requests to remote servers.

    This client uses the DEALER socket pattern and supports both blocking (`call`) and non-blocking (`call_async`)
    method invocation. The client can be configured with connection settings and timeout behavior through `RpcConfig`.
    """

    def __init__(self, config: RpcConfig) -> None:
        """
        Initializes the RPC client with the specified configuration.

        :param config RpcConfig: Configuration object containing host, port, and timeout.
        """

        self._endpoint = f"tcp://{config.host}:{config.port}"
        self._timeout = config.timeout

        self._pool: Optional[ThreadPoolExecutor] = None

        self._context: Optional[zmq.Context] = None
        self._socket: Optional[zmq.Socket] = None
        self._poller: Optional[zmq.Poller] = None

        self._logger = getLogger("jaiger")

    def connect(self) -> "RpcClient":
        """
        Establishes a connection to the RPC server by initializing the socket, context, and poller.

        :returns: The instance itself, allowing method chaining.
        :rtype: RpcClient
        """

        if self._context is not None:
            self.disconnect()

        self._pool = ThreadPoolExecutor()
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.DEALER)
        self._poller = zmq.Poller()
        self._poller.register(self._socket, zmq.POLLIN)

        return self

    def disconnect(self) -> "RpcClient":
        """
        Closes the connection to the RPC server and cleans up resources.

        :returns: The instance itself, allowing method chaining.
        :rtype: RpcClient
        """

        if self._context is not None:
            self._pool.shutdown(wait=True)
            self._context.destroy(0)

            self._pool = None
            self._context = None
            self._socket = None
            self._poller = None

        return self

    def call(
        self,
        server_id: str,
        function: str,
        args: List[Any] = list(),
        kwargs: Dict[str, Any] = dict(),
        timeout: int = 10,
    ) -> Any:
        """
        Sends a synchronous RPC call to a remote server and waits for the response.

        :param server_id str: Identifier of the target server.
        :param function str: Name of the remote function to invoke.
        :param args List[Any]: Positional arguments for the function. Defaults to empty list.
        :param kwargs Dict[str, Any]: Keyword arguments for the function. Defaults to empty dict.
        :param timeout int: Timeout duration in seconds for waiting for the response. Defaults to 10.

        :returns: The result returned by the remote function.
        :rtype: Any

        :raises RuntimeError: If the remote function returns an error.
        :raises TimeoutError: If the response is not received within the timeout period.
        """

        request = Call(function=function, args=args, kwargs=kwargs)
        self._socket.send_multipart([server_id, request.model_dump()])

        return self._wait_for_response(server_id, function, args, kwargs, timeout)

    def call_async(
        self,
        server_id: str,
        function: str,
        args: List[Any] = list(),
        kwargs: Dict[str, Any] = dict(),
        timeout: int = 10,
    ) -> Future:
        """
        Sends an asynchronous RPC call to a remote server.

        :param server_id str: Identifier of the target server.
        :param function str: Name of the remote function to invoke.
        :param args List[Any]: Positional arguments for the function. Defaults to empty list.
        :param kwargs Dict[str, Any]: Keyword arguments for the function. Defaults to empty dict.
        :param timeout int: Timeout duration in seconds for the response. Defaults to 10.

        :returns: A future representing the pending result of the RPC call.
        :rtype: Future
        """

        request = Call(function=function, args=args, kwargs=kwargs)
        self._socket.send_multipart([server_id, request.model_dump()])

        return self._pool.submit(
            self._wait_for_response, server_id, function, args, kwargs, timeout
        )

    def _wait_for_response(
        self,
        server_id: str,
        function: str,
        args: List[Any],
        kwargs: Dict[str, Any],
        timeout_s: int,
    ) -> Any:
        items = dict(self._poller.poll(timeout_s * 1000))
        if items.get(self._socket) == zmq.POLLIN:
            src, content = self._socket.recv_multipart()

            self._logger.debug(f"Received from [{src}]: {content}")

            response = CallResult.model_validate(content)

            if response.error == "":
                return response.result
            else:
                raise RuntimeError(
                    f"Error when calling {server_id}:\n"
                    f"> function: {function}\n"
                    f"> args: {args}\n"
                    f"> kwargs: {kwargs}\n"
                    f"Error message:\n{response.error}"
                )

        raise TimeoutError(
            f"Timeout when calling {server_id}:\n"
            f"> function: {function}\n"
            f"> args: {args}\n"
            f"> kwargs: {kwargs}\n"
        )
