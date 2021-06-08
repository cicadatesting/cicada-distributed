from typing import Dict
from concurrent import futures
import uuid

import click
import grpc  # type: ignore

from cicadad.services.eventing import get_event_consumer, get_event_producer
from cicadad.core.scenario import Scenario, scenario_runner, user_runner
from cicadad.util.constants import (
    DEFAULT_DATASTORE_ADDRESS,
    DEFAULT_CONTEXT_STRING,
    DEFAULT_EVENT_ADDRESS,
    DEFAULT_DOCKER_NETWORK,
)
from cicadad.util.context import decode_context
from cicadad.server.hub import HubServer
from cicadad.protos import hub_pb2_grpc


class Engine:
    def __init__(self) -> None:
        """Entrypoint for Cicada tests. Links tests to Cicada infrastructure"""
        self.scenarios: Dict[str, Scenario] = {}

    def add_scenario(self, scenario: Scenario):
        """Add a scenario to the engine

        Args:
            scenario (Scenario): Scenario being added to engine
        """
        self.scenarios[scenario.name] = scenario

    def start(self):
        """Called internally when test container is started to parse args"""
        # read sys.argv and start scenario or user (Already in container)
        engine_cli(obj=self)

    def run_test(
        self,
        image: str,
        network: str,
        event_broker_address: str,
        datastore_address: str,
    ):
        """Startup function when test container is created. Starts hub server.

        Args:
            image (str): Image containing test code. Passed to scenarios
            network (str): Network to start scenarios in
            event_broker_address (str): Address of event broker to connect to scenarios
        """
        event_producer = get_event_producer(event_broker_address)

        server = grpc.server(futures.ThreadPoolExecutor())

        hub_pb2_grpc.add_HubServicer_to_server(
            HubServer(
                scenarios=self.scenarios.values(),
                image=image,
                network=network,
                event_producer=event_producer,
                datastore_address=datastore_address,
                event_broker_address=event_broker_address,
            ),
            server,
        )

        # TODO: supply port
        server.add_insecure_port("[::]:50051")
        server.start()
        server.wait_for_termination()

    def run_scenario(
        self,
        scenario_name: str,
        scenario_id: str,
        image: str,
        network: str,
        event_broker_address: str,
        datastore_address: str,
        encoded_context: str,
    ):
        """Startup function when scenario is started. Begins running scenario's
        load function

        Args:
            scenario_name (str): Name of scenario being run
            image (str): Image containing test code
            network (str): Network to start users in
            test_id (str): ID of test run
            event_broker_address (str): Address of event broker to connect to test container and users
            datastore_address (str): Address of datastore client to test container and users
            encoded_context (str): Context from test containing previous results
        """
        scenario = self.scenarios[scenario_name]
        event_producer = get_event_producer(event_broker_address)
        result_consumer = get_event_consumer(
            f"{scenario_name}-{scenario_id}-results",
            event_broker_address,
            "latest",
        )

        context = decode_context(encoded_context)

        try:
            scenario_runner(
                scenario,
                image,
                network,
                scenario_id,
                event_producer,
                result_consumer,
                datastore_address,
                context,
            )
        finally:
            # NOTE: do we need to commit here?
            result_consumer.close()

            event_producer.flush()
            event_producer.close()

    def run_user(
        self,
        scenario_name: str,
        user_id: str,
        datastore_address: str,
        encoded_context: str,
    ):
        """Startup function when user is started. Runs scenario user loop.

        Args:
            scenario_name (str): Name of scenario being run
            group_id (str): ID of group of users this user belongs to
            user_id (str): Unique ID of user assigned by scenario
            scenario_id (str): ID of scenario this user was started by
            event_broker_address (str): Address of event broker to connect to test container and users
            encoded_context (str): Context from test containing previous results
        """
        scenario = self.scenarios[scenario_name]
        context = decode_context(encoded_context)

        user_runner(
            scenario,
            user_id,
            datastore_address,
            context,
        )


@click.group()
@click.pass_context
def engine_cli(ctx):
    ctx.ensure_object(Engine)


@engine_cli.command()
@click.pass_context
@click.option("--image", type=str, required=True)
@click.option("--network", type=str, default=DEFAULT_DOCKER_NETWORK)
@click.option("--event-broker-address", type=str, default=DEFAULT_EVENT_ADDRESS)
@click.option("--datastore-address", type=str, default=DEFAULT_DATASTORE_ADDRESS)
def run_test(ctx, image, network, event_broker_address, datastore_address):
    engine: Engine = ctx.obj

    engine.run_test(
        image,
        network,
        event_broker_address,
        datastore_address,
    )


@engine_cli.command()
@click.pass_context
@click.option("--name", type=str, required=True)
@click.option("--scenario-id", type=str, required=True)
@click.option("--image", type=str, required=True)
@click.option("--network", type=str, default=DEFAULT_DOCKER_NETWORK)
@click.option("--event-broker-address", type=str, default=DEFAULT_EVENT_ADDRESS)
@click.option("--datastore-address", type=str, default=DEFAULT_DATASTORE_ADDRESS)
@click.option(
    "--encoded-context",
    type=str,
    default=DEFAULT_CONTEXT_STRING,
)
def run_scenario(
    ctx,
    name,
    scenario_id,
    image,
    network,
    event_broker_address,
    datastore_address,
    encoded_context,
):
    engine: Engine = ctx.obj

    engine.run_scenario(
        name,
        scenario_id,
        image,
        network,
        event_broker_address,
        datastore_address,
        encoded_context,
    )


@engine_cli.command()
@click.pass_context
@click.option("--name", type=str, required=True)
@click.option("--user-id", type=str, required=True)
@click.option("--datastore-address", type=str, default=DEFAULT_DATASTORE_ADDRESS)
@click.option(
    "--encoded-context",
    type=str,
    default=DEFAULT_CONTEXT_STRING,
)
def run_user(
    ctx,
    name,
    user_id,
    datastore_address,
    encoded_context,
):
    engine: Engine = ctx.obj

    engine.run_user(
        name,
        user_id,
        datastore_address,
        encoded_context,
    )
