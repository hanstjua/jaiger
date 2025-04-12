from concurrent.futures import Future, ThreadPoolExecutor
from logging import getLogger
from queue import Queue
from threading import Thread, Event
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple

import zmq
from jaiger.configs import RpcConfig
from jaiger.rpc.models import RpcRequest, RpcResponse


def server_task(id: str,
                callbacks: Dict[str, Callable[[Any], Any]],
                endpoint: str,
                start_event: Event,
                stop_event: Event):
    start_event.set()

    def separate_completed_futures(futures: List[Tuple[str, Future]]) -> Tuple[List[Tuple[str, Future]], List[Tuple[str, Future]]]:
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

    logger = getLogger('jaiger')

    pool = ThreadPoolExecutor()

    futures: List[Tuple[str, Future]] = []

    while not stop_event.is_set():
        sockets = dict(poller.poll(1))
        if sockets[socket] == zmq.POLLIN:
            src, content = socket.recv_multipart()
            logger.debug(f'RPC Server [{id}] from [{src}]: {content}')

            try:
                request = RpcRequest.model_validate(content)
                futures.append(pool.submit(
                    callbacks[request.function],
                    *request.args,
                    **request.kwargs
                ))

            except Exception as e:
                logger.info(f'Server {id} failed to handle RPC request {request}:'
                            f'{traceback.TracebackException.from_exception(e).format()}')
                
            completed, futures = separate_completed_futures(futures)
            for src, future in completed:
                error = future.exception()
                content = RpcResponse(
                    result=future.result() if error is None else future.result(),
                    error=error
                )
                socket.send_multipart([src, content.model_dump()])
        
        time.sleep(0)


class RpcServer:
    def __init__(self, id: str, config: RpcConfig, callbacks: Dict[str, Callable[[Any], Any]]) -> None:
        self._id = id
        self._callbacks = callbacks
        self._endpoint = f'tcp://{config.host}:{config.port}'
        self._timeout = config.timeout

        self._task: Optional[Thread] = None
        self._stop_event: Optional[Event] = None

    def start(self) -> 'RpcServer':
        logger = getLogger('jaiger')
        if self._task is not None:
            logger.warning(f'Terminating existing server task ({self._task.name}) ...')
            self.stop()

        start_event = Event()
        self._stop_event = Event()
        self._task = Thread(target=server_task,
                            args=(
                                self._id,
                                self._callbacks,
                                self._endpoint,
                                start_event,
                                self._stop_event
                            ),
                            daemon=True)
        self._task.start()

        start_event.wait()

        logger.info(f'Server task ({self._task.name}) has started.')

        return self

    def stop(self) -> 'RpcServer':
        if self._task is not None:
            self._stop_event.set()

            self._task.join(timeout=self._timeout)

            logger = getLogger('jaiger')
            if self._task.is_alive():
                logger.warning(f'Server task ({self._task.name}) is not terminated.')
            else:
                logger.info(f'Server task ({self._task.name}) has been terminated.')

            self._task = None
            self._stop_event = None
        
        return self
