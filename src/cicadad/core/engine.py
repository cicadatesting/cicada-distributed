from typing import Dict, List

from distributed.client import Client  # type: ignore
import click

from cicadad.core.scenario import (
    Scenario,
    test_runner,
    scenario_runner,
    user_scheduler,
)
from cicadad.util.constants import (
    DEFAULT_CONTAINER_MODE,
    DEFAULT_CONTAINER_SERVICE_ADDRESS,
    DEFAULT_DATASTORE_ADDRESS,
    DEFAULT_CONTEXT_STRING,
    DEFAULT_DOCKER_NETWORK,
    DEFAULT_KUBE_NAMESPACE,
)
from cicadad.util.context import decode_context


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
        tags: List[str],
        test_id: str,
        image: str,
        network: str,
        namespace: str,
        datastore_address: str,
        container_service_address: str,
        container_mode: str,
    ):
        """Startup function when test container is created. Starts hub server.

        Args:
            tags: (List[str]): List of tags to filter scenarios by
            test_id: ID of test to event back to client
            image (str): Image containing test code. Passed to scenarios
            network (str): Network to start scenarios in
            namepace (str): Kube namespace to place jobs in
            datastore_address (str): Address of datastore client to receive scenario results
            container_service_address (str): Address of container service to start scenarios
            container_mode (str): DOCKER or KUBE container modes
        """
        test_runner(
            self.scenarios.values(),
            list(tags),
            test_id,
            image,
            network,
            namespace,
            datastore_address,
            container_service_address,
            container_mode,
        )

    def run_scenario(
        self,
        scenario_name: str,
        test_id: str,
        scenario_id: str,
        image: str,
        network: str,
        namespace: str,
        datastore_address: str,
        container_service_address: str,
        container_mode: str,
        encoded_context: str,
    ):
        """Startup function when scenario is started. Begins running scenario's
        load function

        Args:
            scenario_name (str): Name of scenario being run
            test_id (str): Test ID to send results to
            scenario_id (str): ID of scenario run
            image (str): Image containing test code
            network (str): Network to start users in
            namespace (str): Namespace to place kube jobs in
            datastore_address (str): Address of datastore client to save and receive results
            container_service_address (str): Address of container service to start and stop users
            container_mode (str): DOCKER or KUBE container modes
            encoded_context (str): Context from test containing previous results
        """
        scenario = self.scenarios[scenario_name]
        context = decode_context(encoded_context)

        scenario_runner(
            scenario,
            test_id,
            image,
            network,
            namespace,
            scenario_id,
            datastore_address,
            container_service_address,
            container_mode,
            context,
        )

    def run_user(
        self,
        scenario_name: str,
        user_manager_id: str,
        datastore_address: str,
        encoded_context: str,
    ):
        """Startup function when user is started. Runs scenario user loop.

        Args:
            scenario_name (str): Name of scenario being run
            user_manager_id (str): Unique ID of user manager assigned by scenario
            datastore_address (str): Address of datastore client to receive work and save results
            encoded_context (str): Context from test containing previous results
        """
        scenario = self.scenarios[scenario_name]
        context = decode_context(encoded_context)
        client = Client()

        user_scheduler(
            client,
            scenario,
            user_manager_id,
            datastore_address,
            context,
        )


@click.group()
@click.pass_context
def engine_cli(ctx):
    ctx.ensure_object(Engine)


@engine_cli.command()
@click.pass_context
@click.option("--tag", "-t", type=str, multiple=True, default=[])
@click.option("--test-id", type=str, required=True)
@click.option("--image", type=str, required=True)
@click.option("--network", type=str, default=DEFAULT_DOCKER_NETWORK)
@click.option("--namespace", type=str, default=DEFAULT_KUBE_NAMESPACE)
@click.option("--datastore-address", type=str, default=DEFAULT_DATASTORE_ADDRESS)
@click.option(
    "--container-service-address", type=str, default=DEFAULT_CONTAINER_SERVICE_ADDRESS
)
@click.option("--container-mode", type=str, default=DEFAULT_CONTAINER_MODE)
def run_test(
    ctx,
    tag,
    test_id,
    image,
    network,
    namespace,
    datastore_address,
    container_service_address,
    container_mode,
):
    engine: Engine = ctx.obj

    engine.run_test(
        tag,
        test_id,
        image,
        network,
        namespace,
        datastore_address,
        container_service_address,
        container_mode,
    )


@engine_cli.command()
@click.pass_context
@click.option("--name", type=str, required=True)
@click.option("--test-id", type=str, required=True)
@click.option("--scenario-id", type=str, required=True)
@click.option("--image", type=str, required=True)
@click.option("--network", type=str, default=DEFAULT_DOCKER_NETWORK)
@click.option("--namespace", type=str, default=DEFAULT_KUBE_NAMESPACE)
@click.option("--datastore-address", type=str, default=DEFAULT_DATASTORE_ADDRESS)
@click.option(
    "--container-service-address", type=str, default=DEFAULT_CONTAINER_SERVICE_ADDRESS
)
@click.option("--container-mode", type=str, default=DEFAULT_CONTAINER_MODE)
@click.option(
    "--encoded-context",
    type=str,
    default=DEFAULT_CONTEXT_STRING,
)
def run_scenario(
    ctx,
    name,
    test_id,
    scenario_id,
    image,
    network,
    namespace,
    datastore_address,
    container_service_address,
    container_mode,
    encoded_context,
):
    engine: Engine = ctx.obj

    engine.run_scenario(
        name,
        test_id,
        scenario_id,
        image,
        network,
        namespace,
        datastore_address,
        container_service_address,
        container_mode,
        encoded_context,
    )


@engine_cli.command()
@click.pass_context
@click.option("--name", type=str, required=True)
@click.option("--user-manager-id", type=str, required=True)
@click.option("--datastore-address", type=str, default=DEFAULT_DATASTORE_ADDRESS)
@click.option(
    "--encoded-context",
    type=str,
    default=DEFAULT_CONTEXT_STRING,
)
def run_user(
    ctx,
    name,
    user_manager_id,
    datastore_address,
    encoded_context,
):
    engine: Engine = ctx.obj

    engine.run_user(
        name,
        user_manager_id,
        datastore_address,
        encoded_context,
    )
