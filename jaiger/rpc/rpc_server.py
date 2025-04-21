import time
import traceback
from concurrent.futures import Future, ThreadPoolExecutor
from logging import getLogger
from threading import Event, Thread
from typing import Any, Callable, Dict, List, Optional, Tuple

import zmq

from jaiger.configs import RpcConfig
from jaiger.models import Call, CallResult


def server_task(
    id: str,
    callbacks: Dict[str, Callable[[Any], Any]],
    endpoint: str,
    start_event: Event,
    stop_event: Event,
):
    """
    A background task that acts as an RPC server using ZeroMQ DEALER sockets.

    The server listens for incoming requests, dispatches them to the corresponding callback functions
    asynchronously using a thread pool, and sends back the results or error traces.

    :param id str: Unique identifier for the server (used as ZeroMQ identity).
    :param callbacks Dict[str, Callable[[Any], Any]]: Mapping of function names to their handler callables.
    :param endpoint str: ZeroMQ endpoint to connect to (e.g., "tcp://localhost:5555").
    :param start_event Event: Event used to signal that the server has started.
    :param stop_event Event: Event used to stop the server gracefully.
    """

    start_event.set()

    def separate_completed_futures(
        futures: List[Tuple[str, Future]],
    ) -> Tuple[List[Tuple[str, Future]], List[Tuple[str, Future]]]:
        completed = []
        not_completed = []
        for f in futures:
            if f[1].done():
                completed.append(f)
            else:
                not_completed.append(f)

        return completed, not_completed

    context = zmq.Context()
    socket = context.socket(zmq.DEALER)
    socket.setsockopt_string(zmq.IDENTITY, id)
    socket.connect(endpoint)

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    logger = getLogger("jaiger")

    pool = ThreadPoolExecutor()

    futures: List[Tuple[str, Future]] = []

    while not stop_event.is_set():
        sockets = dict(poller.poll(1))
        if sockets[socket] == zmq.POLLIN:
            src, content = socket.recv_multipart()
            logger.debug(f"RPC Server [{id}] from [{src}]: {content}")

            try:
                request = Call.model_validate(content)
                futures.append(
                    pool.submit(
                        callbacks[request.function], *request.args, **request.kwargs
                    )
                )

            except Exception as e:
                logger.info(
                    f"Server {id} failed to handle RPC request {request}:"
                    f"{''.join(traceback.TracebackException.from_exception(e).format())}"
                )

            completed, futures = separate_completed_futures(futures)
            for src, future in completed:
                error = future.exception()
                content = CallResult(
                    result=future.result() if error is None else None,
                    error="".join(
                        traceback.TracebackException.from_exception(error).format()
                    )
                    if error is not None
                    else "",
                )
                socket.send_multipart([src, content.model_dump()])

        time.sleep(0)

    context.destroy(0)

    logger.debug(f"Server task {id} exitting ...")


class RpcServer:
    """
    An RPC server wrapper that manages the lifecycle of a server task handling RPC requests.
    """

    def __init__(
        self, id: str, config: RpcConfig, callbacks: Dict[str, Callable[[Any], Any]]
    ) -> None:
        """Initialize the RpcServer.

        :param id str: Unique identifier for the server.
        :param config RpcConfig: Configuration object for the RPC server.
        :param callbacks Dict[str, Callable[[Any], Any]]: Mapping of function names to their handler callables.
        """

        self._id = id
        self._callbacks = callbacks
        self._endpoint = f"tcp://{config.host}:{config.port}"
        self._timeout = config.timeout

        self._task: Optional[Thread] = None
        self._stop_event: Optional[Event] = None

    def start(self) -> "RpcServer":
        """
        Starts the RPC server in a background thread.

        If a server thread is already running, it is first stopped before starting a new one.
        Uses event signaling to manage the server lifecycle.

        :returns: The instance itself, allowing method chaining (RpcServer).
        :rtype: RpcServer
        """

        logger = getLogger("jaiger")
        if self._task is not None:
            logger.warning(f"Terminating existing server task ({self._task.name}) ...")
            self.stop()

        start_event = Event()
        self._stop_event = Event()
        self._task = Thread(
            target=server_task,
            args=(
                self._id,
                self._callbacks,
                self._endpoint,
                start_event,
                self._stop_event,
            ),
            daemon=True,
        )
        self._task.start()

        start_event.wait()

        logger.info(f"Server task ({self._task.name}) has started.")

        return self

    def stop(self) -> "RpcServer":
        """
        Stops the RPC server by signaling the background thread and waiting for termination.

        :returns: The instance itself, allowing method chaining (RpcServer).
        :rtype: RpcServer
        """

        if self._task is not None:
            self._stop_event.set()

            self._task.join(timeout=self._timeout)

            logger = getLogger("jaiger")
            if self._task.is_alive():
                logger.warning(f"Server task ({self._task.name}) is not terminated.")
            else:
                logger.info(f"Server task ({self._task.name}) has been terminated.")

            self._task = None
            self._stop_event = None

        return self
