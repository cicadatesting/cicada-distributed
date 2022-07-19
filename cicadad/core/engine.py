import traceback
from typing import Dict, List, Optional
import atexit

from distributed.client import Client, fire_and_forget  # type: ignore
import click

from cicadad.core.types import IBackendBuilder, TestEvent, TestStatus
from cicadad.core.scenario import Scenario
from cicadad.core.runners import scenario_runner, test_runner, user_scheduler
from cicadad.services.backend import (
    BackendBuilder,
    UserBufferActor,
)
from cicadad.util.context import decode_context
from cicadad.util.constants import (
    DEFAULT_BACKEND_ADDRESS,
    DEFAULT_CONTEXT_STRING,
)


class Engine:
    def __init__(self, backend_builder: Optional[IBackendBuilder] = None) -> None:
        """Entrypoint for Cicada tests. Links tests to Cicada infrastructure"""
        self.__scenarios: Dict[str, Scenario] = {}
        self.__test_id: Optional[str] = None
        self.__backend_address: Optional[str] = None
        self.__backend_builder: IBackendBuilder = backend_builder or BackendBuilder()

    def add_scenario(self, scenario: Scenario):
        """Add a scenario to the engine

        Args:
            scenario (Scenario): Scenario being added to engine
        """
        self.__scenarios[scenario.name] = scenario

    def start(self):
        """Called internally when test container is started to parse args"""
        # read sys.argv and start scenario or user (Already in container)
        try:
            engine_cli(obj=self)
        except Exception as e:
            # NOTE: logger message format?
            print("An unexpected error occured while running the test:", e)
            traceback.print_tb(e.__traceback__)

            if self.__test_id is not None and self.__backend_address is not None:
                backend = self.__backend_builder.make_test_backend(
                    test_id=self.__test_id, address=self.__backend_address
                )

                backend.add_test_event(
                    event=TestEvent(
                        kind="TEST_ERRORED",
                        payload=TestStatus(
                            message=(
                                f"Unexpected error while running test: {str(e)} :: "
                                "Check process logs for more details"
                            ),
                        ),
                    ),
                )

    def run_test(
        self,
        tags: List[str],
        test_id: str,
        backend_address: str,
    ):
        """Startup function when test container is created. Starts hub server.

        Args:
            tags: (List[str]): List of tags to filter scenarios by
            test_id: ID of test to event back to client
            backend_address (str): Address of backend client to receive scenario results
        """
        backend = self.__backend_builder.make_test_backend(
            test_id=test_id, address=backend_address
        )

        test_runner(
            scenarios=self.__scenarios.values(),
            tags=list(tags),
            backend=backend,
        )

    def run_scenario(
        self,
        scenario_name: str,
        test_id: str,
        scenario_id: str,
        backend_address: str,
        encoded_context: str,
    ):
        """Startup function when scenario is started. Begins running scenario's
        load function

        Args:
            scenario_name (str): Name of scenario being run
            test_id (str): Test ID to send results to
            scenario_id (str): ID of scenario run
            backend_address (str): Address of backend client to save and receive results
            encoded_context (str): Context from test containing previous results
        """
        scenario = self.__scenarios[scenario_name]
        context = decode_context(encoded_context)

        backend = self.__backend_builder.make_scenario_backend(
            test_id=test_id, scenario_id=scenario_id, address=backend_address
        )

        scenario_runner(
            scenario=scenario,
            test_id=test_id,
            scenario_id=scenario_id,
            backend=backend,
            context=context,
        )

    def run_user(
        self,
        scenario_name: str,
        user_manager_id: str,
        backend_address: str,
        encoded_context: str,
    ):
        """Startup function when user is started. Runs scenario user loop.

        Args:
            scenario_name (str): Name of scenario being run
            user_manager_id (str): Unique ID of user manager assigned by scenario
            backend_address (str): Address of backend client to receive work and save results
            encoded_context (str): Context from test containing previous results
        """
        scenario = self.__scenarios[scenario_name]
        context = decode_context(encoded_context)
        client = Client()

        # Create buffer actor
        buffer_fut = client.submit(
            UserBufferActor,
            user_manager_id=user_manager_id,
            backend_address=backend_address,
            backend_api_maker=self.__backend_builder.get_backend_api_maker(),
            actor=True,
        )

        buffer = buffer_fut.result()

        fire_and_forget(buffer_fut)

        backend = self.__backend_builder.make_user_manager_backend(
            user_manager_id=user_manager_id,
            buffer=buffer,
            address=backend_address,
        )

        atexit.register(lambda: backend.send_user_results())

        user_scheduler(
            client,
            scenario,
            backend,
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
@click.option("--backend-address", type=str, default=DEFAULT_BACKEND_ADDRESS)
def run_test(
    ctx,
    tag,
    test_id,
    backend_address,
):
    engine: Engine = ctx.obj

    engine.__test_id = test_id
    engine.__backend_address = backend_address

    engine.run_test(tags=tag, test_id=test_id, backend_address=backend_address)


@engine_cli.command()
@click.pass_context
@click.option("--name", type=str, required=True)
@click.option("--test-id", type=str, required=True)
@click.option("--scenario-id", type=str, required=True)
@click.option("--backend-address", type=str, default=DEFAULT_BACKEND_ADDRESS)
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
    backend_address,
    encoded_context,
):
    engine: Engine = ctx.obj

    engine.run_scenario(
        scenario_name=name,
        test_id=test_id,
        scenario_id=scenario_id,
        backend_address=backend_address,
        encoded_context=encoded_context,
    )


@engine_cli.command()
@click.pass_context
@click.option("--name", type=str, required=True)
@click.option("--user-manager-id", type=str, required=True)
@click.option("--backend-address", type=str, default=DEFAULT_BACKEND_ADDRESS)
@click.option(
    "--encoded-context",
    type=str,
    default=DEFAULT_CONTEXT_STRING,
)
def run_user(
    ctx,
    name,
    user_manager_id,
    backend_address,
    encoded_context,
):
    engine: Engine = ctx.obj

    engine.run_user(
        scenario_name=name,
        user_manager_id=user_manager_id,
        backend_address=backend_address,
        encoded_context=encoded_context,
    )
