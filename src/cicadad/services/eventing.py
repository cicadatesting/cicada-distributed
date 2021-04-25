from typing import List, Optional, Set, Union
import uuid
import pickle  # nosec

from kafka import KafkaProducer, KafkaConsumer  # type: ignore
from kafka.errors import NoBrokersAvailable  # type: ignore
from pydantic import BaseModel

from cicadad.core.containers import DockerServerArgs
from cicadad.services.datastore import Result
from cicadad.util.backoff import exponential_backoff
from cicadad.util.constants import (
    CONTAINERS_STREAM,
    DEFAULT_EVENT_POLLING_MS,
    DEFAULT_MAX_EVENTS,
)


def get_event_producer(address: str = "localhost:29092", tries: int = 3):
    """Get a Kafka producer client with exponential backoff

    Args:
        address (str, optional): Address of Kafka event brokers. Defaults to "localhost:29092".
        tries (int, optional): Number of times to retry attempting to get client. Defaults to 3.

    Returns:
        KafkaProducer: Kafka producer client
    """

    return exponential_backoff(
        lambda: KafkaProducer(
            bootstrap_servers=address,
            value_serializer=pickle.dumps,
        ),
        error_class=NoBrokersAvailable,
        tries=tries,
    )


def get_event_consumer(
    topic: str,
    address: str = "localhost:29092",
    auto_offset_reset="earliest",
    group_id: Optional[str] = None,
    tries: int = 3,
):
    """Configure a Kafka consumer client for a particular topic

    Args:
        topic (str): Topic to bind client to.
        address (str, optional): Address of Kafka broker. Defaults to "localhost:29092".
        auto_offset_reset (str, optional): Where to begin reading from topic. Defaults to "earliest".
        group_id (Optional[str], optional): Consumer group to assign consumer to. Creates UUID if None.
        tries (int, optional): Number of times to retry attempting to get client. Defaults to 3.

    Returns:
        KafkaConsumer: configured Kafka consumer client
    """
    return exponential_backoff(
        lambda: KafkaConsumer(
            topic,
            group_id=str(uuid.uuid4()) if not group_id else group_id,
            auto_offset_reset=auto_offset_reset,
            bootstrap_servers=address,
            value_deserializer=pickle.loads,
        ),
        error_class=NoBrokersAvailable,
        tries=tries,
    )


class Event(BaseModel):
    action: str
    event_id: str


class ContainerEvent(Event):
    container_id: str
    container_args: Optional[Union[DockerServerArgs]]


class WorkEvent(Event):
    amount: int
    user_id_limit: Optional[int]


class ResultEvent(Event):
    scenario_name: str
    result: Result


def submit_event(producer: KafkaProducer, topic: str, event: Event):
    """Submit an event to a Kafka topic

    Args:
        producer (KafkaProducer): Producer client to submit event
        topic (str): Topic to submit event to
        event (Event): Event data
    """

    def errback(err):
        print("Message send failed:", err)

    producer.send(topic, event).add_errback(errback)


def get_events(
    consumer: KafkaConsumer,
    timeout_ms: int = DEFAULT_EVENT_POLLING_MS,
    max_records: int = DEFAULT_MAX_EVENTS,
) -> List[Event]:
    """Get events for Kafka topic

    Args:
        consumer (KafkaConsumer): Consumer client to receive events
        timeout_ms (int, optional): Time to wait for events before returning empty.
        Defaults to DEFAULT_EVENT_POLLING_MS.
        max_records (int, optional): Max number of events to return. Defaults to DEFAULT_MAX_EVENTS.

    Returns:
        List[Event]: List of events received
    """
    received = consumer.poll(timeout_ms, max_records=max_records)
    records = []

    for partition in received:
        records.extend(received[partition])

    return [record.value for record in records]


def add_work(
    producer: KafkaProducer,
    user_group: str,
    user_id_limit: Optional[int],
    amount: int,
):
    """Send work events to users

    Args:
        producer (KafkaProducer): Producer client to submit work events
        user_group (str): Group to send work events to
        user_id_limit (Optional[int]): Only users with a hashed ID less than or equal will respond to this work event
        amount (int): Amount of work to bundle in event
    """
    submit_event(
        producer,
        user_group,
        WorkEvent(
            action="WORK",
            event_id=str(uuid.uuid4()),
            amount=amount,
            user_id_limit=user_id_limit,
        ),
    )


class NewWork(BaseModel):
    amount: int
    ids: Set[str]


def get_work(
    consumer: KafkaConsumer,
    user_id_hash: int,
    previous_received_events: Set[str],
    timeout_ms=DEFAULT_EVENT_POLLING_MS,
):
    """Get work events for a user

    Args:
        consumer (KafkaConsumer): Kafka consumer client to collect work events
        user_id_hash (int): Hash of user's ID
        previous_received_events (Set[str]): ID's of work events previously received by user
        timeout_ms ([type], optional): Time to wait for work events to arrive. Defaults to DEFAULT_EVENT_POLLING_MS.

    Returns:
        NewWork: Amount of work and ID's of received work events
    """
    work_amount = 0
    received_events = set()

    for event in get_events(consumer, timeout_ms):
        if (
            isinstance(event, WorkEvent)
            and event.event_id not in received_events
            and event.event_id not in previous_received_events
            and (event.user_id_limit is None or user_id_hash <= event.user_id_limit)
        ):
            work_amount += event.amount
            received_events.add(event.event_id)

    return NewWork(amount=work_amount, ids=received_events)


def start_container(producer: KafkaProducer, container_id, args: DockerServerArgs):
    """Send event to start a container

    Args:
        producer (KafkaProducer): Kafka producer client to send events
        container_id ([type]): ID to give to container
        args (DockerServerArgs): Args to start container with
    """
    msg = ContainerEvent(
        action="START",
        event_id=str(uuid.uuid4()),
        container_id=container_id,
        container_args=args.dict(),
    )

    submit_event(producer, CONTAINERS_STREAM, msg)


def stop_user(producer: KafkaProducer, user_id: str):
    """Send events to stop user containers

    Args:
        producer (KafkaProducer): Kafka producer client to send stop user events
        user_id (str): ID of user to stop
    """
    msg = ContainerEvent(
        action="STOP",
        event_id=str(uuid.uuid4()),
        container_id=user_id,
    )

    submit_event(producer, CONTAINERS_STREAM, msg)


def report_result(
    producer: KafkaProducer,
    scenario_name: str,
    stream_name: str,
    result: Result,
):
    """Send event to report a generic result

    Args:
        producer (KafkaProducer): Kafka producer client to send results
        scenario_name (str): Name of scenario being reported
        stream_name (str): Result stream to send to
        result (Result): Result to send
    """
    msg = ResultEvent(
        action="RESULT",
        event_id=str(uuid.uuid4()),
        scenario_name=scenario_name,
        result=result,
    )

    submit_event(producer, stream_name, msg)


def report_user_result(
    producer: KafkaProducer,
    scenario_name: str,
    scenario_id: str,
    result: Result,
):
    """Report a result for a user invocation

    Args:
        producer (KafkaProducer): Kafka producer client to send results
        scenario_name (str): Name of scenario being reported
        stream_name (str): Result stream to send to
        result (Result): Result to send
    """
    report_result(
        producer, scenario_name, f"{scenario_name}-{scenario_id}-results", result
    )


def report_scenario_result(
    producer: KafkaProducer,
    scenario_name: str,
    test_id: str,
    result: Result,
):
    """Report a result for a scenario

    Args:
        producer (KafkaProducer): Kafka producer client to send results
        scenario_name (str): Name of scenario being reported
        stream_name (str): Result stream to send to
        result (Result): Result to send
    """
    report_result(producer, scenario_name, f"{test_id}-results", result)
