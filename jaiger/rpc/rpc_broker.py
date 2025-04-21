import time
from logging import getLogger
from multiprocessing import Event, Process
from typing import Optional

import zmq

from jaiger.configs import RpcConfig


def broker_task(endpoint: str, start_event: Event, stop_event: Event):
    """
    A broker loop that routes messages between RPC clients and servers using ZeroMQ ROUTER sockets.

    This function is intended to be run as a background process. It listens for incoming multipart
    messages and forwards them to their destinations based on the envelope routing format.

    :param endpoint str: The ZeroMQ endpoint to bind to (e.g., "tcp://localhost:5555").
    :param start_event Event: A multiprocessing event used to signal that the broker has started.
    :param stop_event Event: A multiprocessing event used to signal the broker to stop running.
    """

    start_event.set()

    context = zmq.Context()
    socket = context.socket(zmq.ROUTER)
    socket.bind(endpoint)

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    logger = getLogger("jaiger")

    while not stop_event.is_set():
        sockets = dict(poller.poll(1))
        if sockets[socket] == zmq.POLLIN:
            src, dst, content = socket.recv_multipart()
            logger.debug(f"Routing [{src}] > [{dst}]: {content}")
            socket.send_multipart([dst, src, content])

        time.sleep(0)

    context.destroy(0)

    logger.debug("Broker task exitting ...")


class RpcBroker:
    """
    A broker manager for handling the lifecycle of an RPC message router.

    This class launches the `broker_task` in a separate process using Python's multiprocessing
    facilities. It allows starting and stopping the broker that forwards messages between
    RPC clients and servers via ZeroMQ.
    """

    def __init__(self, config: RpcConfig) -> None:
        """
        Initializes the RpcBroker with the given configuration.

        :param config RpcConfig: Configuration object containing the host, port, and timeout.
        """

        self._endpoint = f"tcp://{config.host}:{config.port}"
        self._timeout = config.timeout

        self._task: Optional[Process] = None
        self._stop_event: Optional[Event] = None

    def start(self) -> 'RpcBroker':
        """
        Starts the RPC broker in a background process.

        If a broker process is already running, it is first terminated before starting a new one.
        Uses multiprocessing events to coordinate startup and shutdown signaling.

        :returns: The instance itself for chaining.
        :rtype: RpcBroker
        """

        logger = getLogger("jaiger")
        if self._task is not None:
            logger.warning(
                f"Terminating existing broker process ({self._task.pid}) ..."
            )
            self.stop()

        start_event = Event()
        self._stop_event = Event()
        self._task = Process(
            target=broker_task,
            args=(self._endpoint, start_event, self._stop_event),
            daemon=True,
        )
        self._task.start()

        start_event.wait()

        logger.info(f"Broker process ({self._task.pid}) has started.")

        return self

    def stop(self) -> 'RpcBroker':
        """
        Stops the RPC broker process gracefully.

        Waits for the background process to terminate within the configured timeout period.
        Logs whether the termination was successful or if the process remained alive.

        :returns: The instance itself for chaining.
        :rtype: RpcBroker
        """

        if self._task is not None:
            self._stop_event.set()

            self._task.join(timeout=self._timeout)

            logger = getLogger("jaiger")
            if self._task.is_alive():
                logger.warning(f"Broker task ({self._task.pid}) is not terminated.")
            else:
                logger.info(f"Broker task ({self._task.pid}) has been terminated.")

            self._task = None
            self._stop_event = None

        return self
