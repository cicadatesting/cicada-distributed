import time
import os

from kafka.errors import NoBrokersAvailable  # type: ignore
from dask.distributed import Client, fire_and_forget, secede, rejoin  # type: ignore
import docker  # type: ignore

from cicadad.core import containers
from cicadad.services import eventing
from cicadad.util import constants, printing


EVENT_ADDRESS = os.getenv("EVENT_ADDRESS", constants.DEFAULT_EVENT_ADDRESS)
EVENT_GROUP = os.getenv("EVENT_GROUP")
LOGGER = printing.get_logger("manager")


def get_consumer(sleep_period):
    """Wait for broker to be available and return Kafka consumer

    Args:
        sleep_period ([type]): Time in seconds to wait before trying to create
    consumer again

    Returns:
        KafkaConsumer: Configured consumer
    """
    consumer = None

    while consumer is None:
        try:
            consumer = eventing.get_event_consumer(
                constants.CONTAINERS_STREAM,
                EVENT_ADDRESS,
                "latest",
                EVENT_GROUP,
            )
        except NoBrokersAvailable:
            LOGGER.info("Waiting for Kafka brokers...")
            time.sleep(sleep_period)

    return consumer


def create_docker_container(args: containers.DockerServerArgs):
    """Wrapper to create docker container in thread

    Args:
        args (containers.DockerServerArgs): Args to create container with
    """
    secede()

    try:
        client = docker.from_env()

        c = containers.create_docker_container(client, args)
        # NOTE: maybe store container ID in stream
        LOGGER.info("created container: %s", c.id)
    except Exception:
        LOGGER.exception("Error creating docker container")


def stop_docker_container(container_id: str):
    """Wrapper to stop docker container by ID for thread

    Args:
        container_id (str): ID of container to stop
    """
    secede()

    try:
        client = docker.from_env()

        containers.stop_docker_container_by_name(client, container_id)
        LOGGER.info("stopped container: %s", container_id)
    except Exception:
        LOGGER.exception("Error stopping docker container")
    finally:
        rejoin()


def process_message(msg: eventing.ContainerEvent, client: Client):
    """Handle container event and start or stop container

    Args:
        msg (eventing.ContainerEvent): Received event to process
        client (Client): Dask client to launch thread
    """
    if msg.action == "START" and isinstance(
        msg.container_args, containers.DockerServerArgs
    ):
        fut = client.submit(
            create_docker_container,
            msg.container_args,
        )

        fire_and_forget(fut)

    elif msg.action == "STOP":
        # NOTE: will need to differentiate between docker containers and pods
        fut = client.submit(
            stop_docker_container,
            msg.container_id,
        )

        fire_and_forget(fut)


def main():
    """Receive container events and start or stop containers"""
    consumer = get_consumer(sleep_period=3)
    dask_client = Client(processes=False)

    while True:
        messages = eventing.get_events(consumer)

        for msg in messages:
            LOGGER.debug("received message: %s", msg)

            if msg is None:
                continue

            process_message(msg, dask_client)


if __name__ == "__main__":
    main()
