from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional
import json
import time
import io
import traceback
import uuid

from distributed.client import Client, fire_and_forget  # type: ignore
from distributed.threadpoolexecutor import secede  # type: ignore

from cicadad.core.commands import ScenarioCommands, UserCommands
from cicadad.core.scenario import Scenario
from cicadad.core.types import (
    IScenarioBackend,
    ITestBackend,
    IUserBackend,
    IUserManagerBackend,
    Result,
    ScenarioMetric,
    TestEvent,
    TestStatus,
)
from cicadad.util import printing
from cicadad.util.context import encode_context


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
    results: Dict[str, dict],
    backend: ITestBackend,
) -> str:
    encoded_context = encode_context(results)

    scenario_id = backend.create_scenario(
        scenario_name=scenario.name,
        context=encoded_context,
        users_per_instance=scenario.users_per_instance,
        tags=scenario.tags,
    )

    backend.add_test_event(
        event=TestEvent(
            kind="SCENARIO_STARTED",
            payload=TestStatus(
                scenario=scenario.name,
                scenario_id=scenario_id,
                message=f"Started scenario: {scenario.name} ({scenario_id})",
                context=json.dumps(results),
            ),
        ),
    )

    return scenario_id


def test_runner(scenarios: Iterable[Scenario], tags: List[str], backend: ITestBackend):
    started: Dict[str, str] = {}
    scenarios_by_id: Dict[str, Scenario] = {}
    results: Dict[str, dict] = {}

    valid_scenarios = filter_scenarios_by_tag(scenarios, tags)

    # Start scenarios with no dependencies
    for scenario in valid_scenarios:
        if scenario.dependencies == []:
            scenario_id = start_scenario(
                scenario=scenario,
                results=results,
                backend=backend,
            )

            started[scenario.name] = scenario_id
            scenarios_by_id[scenario_id] = scenario

    backend.add_test_event(
        event=TestEvent(
            kind="TEST_STARTED",
            payload=TestStatus(
                message=f"Collected {len(valid_scenarios)} Scenario(s)",
            ),
        ),
    )

    # listen to completed events and start scenarios with dependencies
    while len(results) != len(valid_scenarios):
        for scenario_name in [sn for sn in started if sn not in results]:
            scenario = scenarios_by_id[started[scenario_name]]

            if scenario.console_metric_displays is not None:
                backend.add_test_event(
                    event=TestEvent(
                        kind="SCENARIO_METRIC",
                        payload=ScenarioMetric(
                            scenario=scenario_name,
                            metrics={
                                name: display_fn(
                                    name,
                                    started[scenario_name],
                                    backend.get_console_metrics_backend(),
                                )
                                for name, display_fn in scenario.console_metric_displays.items()
                            },
                        ),
                    ),
                )

            result = backend.move_scenario_result(
                started[scenario_name],
            )

            if result is not None:
                results[scenario_name] = result

                backend.add_test_event(
                    event=TestEvent(
                        kind="SCENARIO_FINISHED",
                        payload=TestStatus(
                            scenario=scenario_name,
                            scenario_id=started[scenario_name],
                            message=f"Finished Scenario: {scenario_name}",
                            context=json.dumps(results),
                        ),
                    ),
                )
            # NOTE: may be helpful to get two not running calls before canceling scenario
            elif not backend.scenario_running(started[scenario_name]):
                results[scenario_name] = json.loads(
                    Result(
                        id=str(uuid.uuid4()),
                        output=None,
                        exception="Scenario Exited",
                        logs="",
                        timestamp=datetime.now(),
                    ).json()
                )

                backend.add_test_event(
                    event=TestEvent(
                        kind="SCENARIO_FINISHED",
                        payload=TestStatus(
                            scenario=scenario_name,
                            scenario_id=started[scenario_name],
                            message=f"Scenario Exited Unexpectedly: {scenario_name}",
                            context=json.dumps(results),
                        ),
                    ),
                )

        for scenario in [s for s in valid_scenarios if s.name not in started]:
            if all(
                dep.name in results and results[dep.name]["exception"] is None
                for dep in scenario.dependencies
            ):
                scenario_id = start_scenario(
                    scenario=scenario,
                    results=results,
                    backend=backend,
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

                backend.add_test_event(
                    event=TestEvent(
                        kind="SCENARIO_FINISHED",
                        payload=TestStatus(
                            scenario=scenario.name,
                            scenario_id=started[scenario.name],
                            message=f"Skipped Scenario: {scenario.name}",
                            context=json.dumps(results),
                        ),
                    ),
                )

        # NOTE: maybe make this configurable or shorter?
        time.sleep(1)

    backend.add_test_event(
        event=TestEvent(
            kind="TEST_FINISHED",
            payload=TestStatus(
                message=f"Finished running {len(valid_scenarios)} Scenario(s)",
            ),
        ),
    )


def scenario_runner(
    scenario: Scenario,
    test_id: str,
    scenario_id: str,
    backend: IScenarioBackend,
    context: dict,
):
    """Set up scenario environment and run scenario. Capture output and exceptions.

    Args:
        scenario (Scenario): Scenario being run
        test_id (str): Test id to send results
        scenario_id (str): ID generated for scenario run
        backend (IScenarioBackend): backend methods available to scenario
        context (dict): Test context to pass to users
    """
    scenario_commands = ScenarioCommands(
        scenario=scenario,
        test_id=test_id,
        scenario_id=scenario_id,
        backend=backend,
        context=context,
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

            if (
                scenario_commands.errors != []
                and output is None
                and scenario.raise_exception
            ):
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
    # NOTE: possible shutdown hook
    scenario_commands.scale_users(0)

    failed = len(scenario_commands.errors)

    backend.set_scenario_result(
        output=output,
        exception=exception,
        logs=buffer.getvalue(),
        time_taken=(end - start).total_seconds(),
        succeeded=scenario_commands.num_results_collected - failed,
        failed=failed,
    )


def user_scheduler(
    scheduler: Client,
    scenario: Scenario,
    backend: IUserManagerBackend,
    context: dict,
):
    """Schedules users inside user manager on events from scenario.

    Args:
        scheduler (Client): Dask client to start users
        scenario (Scenario): User Scenario
        user_manager_id (str): ID of this user manager
        backend (IUserManagerBackend): Backend implementation for user manager to use
        context (dict): Test context
    """

    while True:
        for user_id in backend.get_new_users():
            fut = scheduler.submit(
                user_runner,
                scenario=scenario,
                user_id=user_id,
                backend=backend.get_user_backend(user_id),
                context=context,
                pure=False,
            )

            # NOTE: may be better waiting for all futures to finish
            fire_and_forget(fut)

        backend.send_user_results()
        time.sleep(1)


def user_runner(
    scenario: Scenario,
    user_id: str,
    backend: IUserBackend,
    context: dict,
):
    """Set up environment for user and run user.

    Args:
        scenario (Scenario): Scenario being run
        user_id (str): ID generated for user
        backend (IUserBackend): Backend client to save results
        context (dict): Test context containing previous scenario results
    """
    secede()

    user_commands = UserCommands(
        scenario,
        user_id,
        backend,
    )

    # FEATURE: report errors here back to scenario
    scenario.user_loop(user_commands, context)  # type: ignore
