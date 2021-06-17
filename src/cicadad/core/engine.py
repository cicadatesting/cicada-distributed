from typing import Dict
from concurrent import futures

import click
import grpc  # type: ignore

from cicadad.core.scenario import Scenario, scenario_runner, user_runner
from cicadad.util.constants import (
    DEFAULT_CONTAINER_SERVICE_ADDRESS,
    DEFAULT_DATASTORE_ADDRESS,
    DEFAULT_CONTEXT_STRING,
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
        datastore_address: str,
        container_service_address: str,
    ):
        """Startup function when test container is created. Starts hub server.

        Args:
            image (str): Image containing test code. Passed to scenarios
            network (str): Network to start scenarios in
            datastore_address (str): Address of datastore client to receive scenario results
            container_service_address (str): Address of container service to start scenarios
        """
        server = grpc.server(futures.ThreadPoolExecutor())

        hub_pb2_grpc.add_HubServicer_to_server(
            HubServer(
                scenarios=self.scenarios.values(),
                image=image,
                network=network,
                datastore_address=datastore_address,
                container_service_address=container_service_address,
            ),
            server,
        )

        server.add_insecure_port("[::]:50051")
        server.start()
        server.wait_for_termination()

    def run_scenario(
        self,
        scenario_name: str,
        scenario_id: str,
        image: str,
        network: str,
        datastore_address: str,
        container_service_address: str,
        encoded_context: str,
    ):
        """Startup function when scenario is started. Begins running scenario's
        load function

        Args:
            scenario_name (str): Name of scenario being run
            scenario_id (str): ID of scenario run
            image (str): Image containing test code
            network (str): Network to start users in
            datastore_address (str): Address of datastore client to save and receive results
            container_service_address (str): Address of container service to start and stop users
            encoded_context (str): Context from test containing previous results
        """
        scenario = self.scenarios[scenario_name]
        context = decode_context(encoded_context)

        scenario_runner(
            scenario,
            image,
            network,
            scenario_id,
            datastore_address,
            container_service_address,
            context,
        )

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
            user_id (str): Unique ID of user assigned by scenario
            datastore_address (str): Address of datastore client to receive work and save results
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
@click.option("--datastore-address", type=str, default=DEFAULT_DATASTORE_ADDRESS)
@click.option(
    "--container-service-address", type=str, default=DEFAULT_CONTAINER_SERVICE_ADDRESS
)
def run_test(ctx, image, network, datastore_address, container_service_address):
    engine: Engine = ctx.obj

    engine.run_test(
        image,
        network,
        datastore_address,
        container_service_address,
    )


@engine_cli.command()
@click.pass_context
@click.option("--name", type=str, required=True)
@click.option("--scenario-id", type=str, required=True)
@click.option("--image", type=str, required=True)
@click.option("--network", type=str, default=DEFAULT_DOCKER_NETWORK)
@click.option("--datastore-address", type=str, default=DEFAULT_DATASTORE_ADDRESS)
@click.option(
    "--container-service-address", type=str, default=DEFAULT_CONTAINER_SERVICE_ADDRESS
)
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
    datastore_address,
    container_service_address,
    encoded_context,
):
    engine: Engine = ctx.obj

    engine.run_scenario(
        name,
        scenario_id,
        image,
        network,
        datastore_address,
        container_service_address,
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
