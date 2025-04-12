from logging import getLogger
from multiprocessing import Event, Process
import time
from typing import Optional

import zmq
from jaiger.configs import RpcConfig


def broker_task(endpoint: str, start_event: Event, stop_event: Event):
    start_event.set()

    context = zmq.Context()
    socket = context.socket(zmq.ROUTER)
    socket.bind(endpoint)

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    logger = getLogger('jaiger')

    while not stop_event.is_set():
        if poller.poll(1):
            data = socket.recv_multipart()
            src, dst, content = data
            logger.debug(f'Routing [{src}] > [{dst}]: {content}')
            socket.send_multipart([dst, src, content])

        time.sleep(0)

    context.destroy(0)

    logger.debug('Broker task exitting ...')
            

class RpcBroker:
    def __init__(self, config: RpcConfig) -> None:
        self._endpoint = f'tcp://{config.host}:{config.port}'
        self._timeout = config.timeout

        self._task: Optional[Process] = None
        self._stop_event = Event()

    def start(self):
        if self._task is not None:
            self.stop()

        start_event = Event()
        self._task = Process(target=broker_task,
                             args=(self._endpoint, start_event, self._stop_event),
                             daemon=True)
        self._task.start()

        start_event.wait()

        getLogger('jaiger').info(f'Broker process ({self._task.pid}) has started.')

    def stop(self):
        if self._task is not None:
            self._stop_event.set()

            self._task.join(timeout=self._timeout)

            logger = getLogger('jaiger')
            if self._task.is_alive():
                logger.warning(f'Broker task ({self._task.pid}) is not terminated.')
            else:
                logger.info(f'Broker task ({self._task.pid}) has been terminated.')

            self._task = None
