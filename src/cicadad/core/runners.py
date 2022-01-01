from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional
import json
import time
import io
import traceback
import uuid

from distributed.client import Client, fire_and_forget
from distributed.threadpoolexecutor import secede

from cicadad.core.commands import ScenarioCommands, UserCommands
from cicadad.core.scenario import Scenario
from cicadad.core.types import Result
from cicadad.util import printing
from cicadad.util.constants import KUBE_CONTAINER_MODE
from cicadad.util.context import encode_context
from cicadad.services import container_service, datastore


def filter_scenarios_by_tag(
    scenarios: Iterable[Scenario], tags: List[str]
) -> List[Scenario]:
    """Filter scenarios that have tags in the list of tags provided.

    Returns all scenarios if tag list is empty.

    Args:
        scenarios (List[Scenario]): List of scenarios
        tags (List[str]): List of tags to filter scenarios with

    Returns:
        List[Scenario]: List of filtered scenarios
    """
    if tags == []:
        return list(scenarios)

    return [s for s in scenarios if set(s.tags).intersection(set(tags)) != set()]


def start_scenario(
    scenario: Scenario,
    scenario_id: str,
    results: Dict[str, dict],
    container_mode: str,
    image: str,
    test_id: str,
    network: str,
    namespace: str,
    datastore_address: str,
    container_service_address: str,
):
    encoded_context = encode_context(results)

    if container_mode == KUBE_CONTAINER_MODE:
        container_service.start_kube_container(
            container_service.StartKubeContainerArgs(
                image=image,
                name=scenario_id,
                command=[
                    "run-scenario",
                    "--name",
                    scenario.name,
                    "--test-id",
                    test_id,
                    "--scenario-id",
                    scenario_id,
                    "--image",
                    image,
                    "--network",
                    network,
                    "--namespace",
                    namespace,
                    "--encoded-context",
                    encoded_context,
                    "--datastore-address",
                    datastore_address,
                    "--container-service-address",
                    container_service_address,
                    "--container-mode",
                    container_mode,
                ],
                labels={
                    "type": "cicada-distributed-scenario",
                    "scenario": scenario.name,
                    "test": test_id,
                },
                # env: Dict[str, str]={}
                namespace=namespace,
            ),
            container_service_address,
        )
    else:
        container_service.start_docker_container(
            container_service.StartDockerContainerArgs(
                image=image,
                name=scenario_id,
                command=[
                    "run-scenario",
                    "--name",
                    scenario.name,
                    "--test-id",
                    test_id,
                    "--scenario-id",
                    scenario_id,
                    "--image",
                    image,
                    "--network",
                    network,
                    "--namespace",
                    namespace,
                    "--encoded-context",
                    encoded_context,
                    "--datastore-address",
                    datastore_address,
                    "--container-service-address",
                    container_service_address,
                    "--container-mode",
                    container_mode,
                ],
                labels={
                    "type": "cicada-distributed-scenario",
                    "scenario": scenario.name,
                    "test": test_id,
                },
                # env: Dict[str, str]={}
                network=network,
            ),
            container_service_address,
        )

    datastore.add_test_event(
        test_id=test_id,
        event=datastore.TestEvent(
            kind="SCENARIO_STARTED",
            payload=datastore.TestStatus(
                scenario=scenario.name,
                scenario_id=scenario_id,
                message=f"Started scenario: {scenario.name} ({scenario_id})",
                context=json.dumps(results),
            ),
        ),
        address=datastore_address,
    )


def test_runner(
    scenarios: Iterable[Scenario],
    tags: List[str],
    test_id: str,
    image: str,
    network: str,
    namespace: str,
    datastore_address: str,
    container_service_address: str,
    container_mode: str,
):
    started: Dict[str, str] = {}
    scenarios_by_id: Dict[str, Scenario] = {}
    results: Dict[str, dict] = {}

    valid_scenarios = filter_scenarios_by_tag(scenarios, tags)

    datastore.add_test_event(
        test_id=test_id,
        event=datastore.TestEvent(
            kind="TEST_STARTED",
            payload=datastore.TestStatus(
                message=f"Collected {len(valid_scenarios)} Scenario(s)",
            ),
        ),
        address=datastore_address,
    )

    # Start scenarios with no dependencies
    for scenario in valid_scenarios:
        if scenario.dependencies == []:
            scenario_id = f"scenario-{str(uuid.uuid4())[:8]}"

            start_scenario(
                scenario,
                scenario_id,
                results,
                container_mode,
                image,
                test_id,
                network,
                namespace,
                datastore_address,
                container_service_address,
            )

            started[scenario.name] = scenario_id
            scenarios_by_id[scenario_id] = scenario

    # listen to completed events and start scenarios with dependencies
    # FEATURE: scenario timeout counter here as well
    while len(results) != len(valid_scenarios):
        for scenario_name in [sn for sn in started if sn not in results]:
            scenario = scenarios_by_id[started[scenario_name]]

            if scenario.console_metric_displays is not None:
                datastore.add_test_event(
                    test_id=test_id,
                    event=datastore.TestEvent(
                        kind="SCENARIO_METRIC",
                        payload=datastore.ScenarioMetric(
                            scenario=scenario_name,
                            metrics={
                                name: display_fn(
                                    name, started[scenario_name], datastore_address
                                )
                                for name, display_fn in scenario.console_metric_displays.items()
                            },
                        ),
                    ),
                    address=datastore_address,
                )

            result = datastore.move_scenario_result(
                started[scenario_name],
                datastore_address,
            )

            if result is not None:
                results[scenario_name] = result

                datastore.add_test_event(
                    test_id=test_id,
                    event=datastore.TestEvent(
                        kind="SCENARIO_FINISHED",
                        payload=datastore.TestStatus(
                            scenario=scenario_name,
                            scenario_id=started[scenario_name],
                            message=f"Finished Scenario: {scenario_name}",
                            context=json.dumps(results),
                        ),
                    ),
                    address=datastore_address,
                )

        for scenario in [s for s in valid_scenarios if s.name not in started]:
            if all(
                dep.name in results and results[dep.name]["exception"] is None
                for dep in scenario.dependencies
            ):
                scenario_id = f"scenario-{str(uuid.uuid4())[:8]}"

                start_scenario(
                    scenario,
                    scenario_id,
                    results,
                    container_mode,
                    image,
                    test_id,
                    network,
                    namespace,
                    datastore_address,
                    container_service_address,
                )

                started[scenario.name] = scenario_id
                scenarios_by_id[scenario_id] = scenario
            elif all(dep.name in results for dep in scenario.dependencies):
                # has all dependencies but some are failed
                started[scenario.name] = str(uuid.uuid4())[:8]
                results[scenario.name] = json.loads(
                    Result(
                        id=str(uuid.uuid4()),
                        output=None,
                        exception="Skipped",
                        logs="",
                        timestamp=datetime.now(),
                    ).json()
                )

                datastore.add_test_event(
                    test_id=test_id,
                    event=datastore.TestEvent(
                        kind="SCENARIO_FINISHED",
                        payload=datastore.TestStatus(
                            scenario=scenario.name,
                            scenario_id=started[scenario.name],
                            message=f"Skipped Scenario: {scenario.name}",
                            context=json.dumps(results),
                        ),
                    ),
                    address=datastore_address,
                )

        # NOTE: maybe make this configurable or shorter?
        time.sleep(1)

    datastore.add_test_event(
        test_id=test_id,
        event=datastore.TestEvent(
            kind="TEST_FINISHED",
            payload=datastore.TestStatus(
                message=f"Finished running {len(valid_scenarios)} Scenario(s)",
            ),
        ),
        address=datastore_address,
    )


def scenario_runner(
    scenario: Scenario,
    test_id: str,
    image: str,  # TODO: save network, namespace, container mode and image to test config
    network: str,
    namespace: str,
    scenario_id: str,
    datastore_address: str,  # TODO: abstract datastore and test runner classes
    container_service_address: str,
    container_mode: str,
    context: dict,
):
    """Set up scenario environment and run scenario. Capture output and exceptions.

    Args:
        scenario (Scenario): Scenario being run
        test_id (str): Test id to send results
        image (str): Image for scenario
        network (str): Network to run scenario containers in
        namespace (str): Kube namespace to place jobs in
        scenario_id (str): ID generated for scenario run
        datastore_address (str): Address of datastore passed to users
        container_service (str): Address of container service to start and stop users
        container_mode (str): DOCKER or KUBE container mode
        context (dict): Test context to pass to users
    """
    scenario_commands = ScenarioCommands(
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

    buffer = io.StringIO()

    start = datetime.now()
    output: Optional[Any] = None
    exception: Optional[Exception] = None

    with printing.stdout_redirect(buffer):
        try:
            scenario.load_model(scenario_commands, context)  # type: ignore

            if scenario.output_transformer is not None:
                output = scenario.output_transformer(
                    scenario_commands.aggregated_results
                )
            else:
                output = scenario_commands.aggregated_results

            if scenario_commands.errors != [] and scenario.raise_exception:
                error_strs = [
                    f"{len(scenario_commands.errors)} error(s) were raised in scenario {scenario.name}:"
                ] + scenario_commands.errors

                exception = AssertionError("\n".join(error_strs))
            else:
                exception = None
        except Exception as e:
            output, exception = None, e

    end = datetime.now()

    # NOTE: this doesn't get reported to the user, just stays in container logs
    if exception is not None:
        print(exception)
        traceback.print_tb(exception.__traceback__)

    # Clean up
    scenario_commands.scale_users(0)

    failed = len(scenario_commands.errors)

    datastore.set_scenario_result(
        scenario_id=scenario_id,
        output=output,
        exception=exception,
        logs=buffer.getvalue(),
        time_taken=(end - start).total_seconds(),
        succeeded=scenario_commands.num_results_collected - failed,
        failed=failed,
        address=datastore_address,
    )


def user_scheduler(
    scheduler: Client,
    scenario: Scenario,
    user_manager_id: str,
    datastore_address: str,
    context: dict,
):
    """Schedules users inside user manager on events from scenario.

    Args:
        scheduler (Client): Dask client to start users
        scenario (Scenario): User Scenario
        user_manager_id (str): ID of this user manager
        datastore_address (str): Address of datastore to recieve events from
        context (dict): Test context
    """
    while True:
        events = datastore.get_user_events(
            user_manager_id, "START_USERS", datastore_address
        )

        for event in events:
            for user_id in event.payload["IDs"]:
                fut = scheduler.submit(
                    user_runner,
                    scenario=scenario,
                    user_id=user_id,
                    datastore_address=datastore_address,
                    context=context,
                    pure=False,
                )

                # NOTE: may be better waiting for all futures to finish
                fire_and_forget(fut)


def user_runner(
    scenario: Scenario,
    user_id: str,
    datastore_address: str,
    context: dict,
):
    """Set up environment for user and run user.

    Args:
        scenario (Scenario): Scenario being run
        user_id (str): ID generated for user
        datastore_address (str): Address of datastore client to save results
        context (dict): Test context containing previous scenario results
    """
    secede()

    user_commands = UserCommands(
        scenario,
        user_id,
        datastore_address,
    )

    # FEATURE: report errors here back to scenario
    scenario.user_loop(user_commands, context)  # type: ignore
