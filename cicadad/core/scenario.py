from typing import Any, Callable, List, Optional
from datetime import datetime, timedelta
import time

from pydantic import BaseModel, Field

from cicadad.metrics.collectors import runtime_seconds, pass_or_fail, results_per_second
from cicadad.metrics.console import console_stats, console_collector, console_percent

from cicadad.core.types import (
    ConsoleMetricDisplays,
    IScenarioCommands,
    IUserCommands,
    LoadModelFn,
    MetricCollector,
    OutputTransformerFn,
    Result,
    ResultAggregatorFn,
    ResultVerifierFn,
    UserLoopFn,
)

# NOTE: maybe move to loops module


def while_has_work(polling_timeout_ms: int = 1000):
    """Run user if work is available or continue polling.

    Args:
        polling_timeout_ms (int): Time to wait for work before cycling
    """

    def closure(user_commands: IUserCommands, context: dict):
        while user_commands.is_up():
            if user_commands.has_work(polling_timeout_ms):
                start = datetime.now()
                output, exception, logs = user_commands.run(context=context)
                end = datetime.now()
                user_commands.report_result(
                    output,
                    exception,
                    logs,
                    time_taken=(end - start).total_seconds(),
                )

    return closure


def while_alive():
    """Run user if hasn't been shut down yet."""

    def closure(user_commands: IUserCommands, context: dict):
        while user_commands.is_up():
            start = datetime.now()
            output, exception, logs = user_commands.run(context=context)
            end = datetime.now()
            user_commands.report_result(
                output,
                exception,
                logs,
                time_taken=(end - start).total_seconds(),
            )

    return closure


def iterations_per_second_limited(limit: int):
    """Allow a user to run a limited number of iterations per second.

    Args:
        limit (int): Max iterations per second for user
    """

    def closure(user_commands: IUserCommands, context: dict):
        remaining_iterations = limit
        second_start_time = datetime.now()

        while user_commands.is_up():
            if remaining_iterations > 0:
                start = datetime.now()

                output, exception, logs = user_commands.run(context=context)

                end = datetime.now()

                remaining_iterations -= 1
                user_commands.report_result(
                    output,
                    exception,
                    logs,
                    time_taken=(end - start).total_seconds(),
                )
            else:
                td = (second_start_time + timedelta(seconds=1)) - datetime.now()

                time.sleep(td.seconds + (td.microseconds / 1000000))

            if datetime.now() >= second_start_time + timedelta(seconds=1):
                remaining_iterations = limit
                second_start_time = datetime.now()

    return closure


def n_iterations(
    iterations: int,
    users: int,
    wait_period: int = 1,
    timeout: Optional[int] = 15,
    skip_scaledown: bool = False,
):
    """Create a load model where a pool of users is called n times.
    Args:
        iterations (int): Number of shared iterations for users to run
        users (int): Size of user pool
        wait_period (int, optional): Time in seconds to between polling for results. Defaults to 1.
        timeout (Optional[int], optional): Time in seconds for scenario to complete before failing. Defaults to 15.
        skip_scaledown (bool): Skip scaledown of users after running load function
    """

    def closure(scenario_commands: IScenarioCommands, context: dict):
        scenario_commands.scale_users(users)
        scenario_commands.add_work(iterations)

        # wait for completion
        num_results = 0
        start_time = datetime.now()

        while num_results < iterations:
            if (
                timeout is not None
                and timeout > 0
                and datetime.now() > start_time + timedelta(seconds=timeout)
            ):
                scenario_commands.scale_users(0)
                raise AssertionError("Timed out waiting for results")

            latest_results = scenario_commands.get_latest_results()

            scenario_commands.aggregate_results(latest_results)
            scenario_commands.verify_results(latest_results)
            scenario_commands.collect_datastore_metrics(latest_results)
            num_results += len(latest_results)

            time.sleep(wait_period)

        if skip_scaledown:
            return

        scenario_commands.scale_users(0)

    return closure


def run_scenario_once(wait_period: int = 1, timeout: int = 15):
    """Run scenario one time with one user and retry on failure.

    Args:
        wait_period (int): Time in seconds to wait before polling for results. Defaults to 1.
        timeout (int): Time in seconds to continue trying until a successful result is reached. Defaults to 15.

    Returns:
        Callable: Closure for configured load model
    """

    def closure(scenario_commands: IScenarioCommands, context: dict):
        scenario_commands.scale_users(1)
        scenario_commands.add_work(1)
        start_time = datetime.now()

        # wait for passing result or until timeout reached
        while datetime.now() < start_time + timedelta(seconds=timeout):
            latest_results = scenario_commands.get_latest_results()

            scenario_commands.aggregate_results(latest_results)
            scenario_commands.verify_results(latest_results)
            scenario_commands.collect_datastore_metrics(latest_results)

            if (
                scenario_commands.errors == []
                and scenario_commands.num_results_collected > 0
            ):
                break

            time.sleep(wait_period)
            # TODO: only add work if exception recieved
            scenario_commands.add_work(1)

        scenario_commands.scale_users(0)

    return closure


def n_seconds(
    seconds: int,
    users: int,
    wait_period: int = 1,
    skip_scaledown=False,
):
    """Run the scenario for a specified duration.

    Should be used with the 'while_alive' user loop.

    Args:
        seconds (int): Number of seconds to run scenario
        users (int): Number of users to start for scenario
        wait_period (int, optional): Time in seconds to wait before polling for results. Defaults to 1.
        skip_scaledown (bool): Skip scaledown of users after running load function
    """

    def closure(scenario_commands: IScenarioCommands, context: dict):
        scenario_commands.scale_users(users)

        # collect results for specified seconds
        start_time = datetime.now()

        while True:
            latest_results = scenario_commands.get_latest_results()

            scenario_commands.aggregate_results(latest_results)
            scenario_commands.verify_results(latest_results)
            scenario_commands.collect_datastore_metrics(latest_results)

            if datetime.now() > start_time + timedelta(seconds=seconds):
                break

            time.sleep(wait_period)

        if skip_scaledown:
            return

        scenario_commands.scale_users(0)

    return closure


def n_users_ramping(
    seconds: int,
    target_users: int,
    wait_period: int = 1,
    skip_scaledown: bool = True,
):
    """Scale users to target over the duration of the time specified.

    Use this to scale users smoothly.

    Args:
        seconds (int): Amount of time to spend ramping users
        target_users (int): Number of users to ramp to.
        wait_period (int, optional): Time in seconds to wait between scaling batch of users. Defaults to 1.
        skip_scaledown (bool, optional): Do not scale down users after load model completes. Defaults to True.
    """

    def closure(scenario_commands: IScenarioCommands, context: dict):
        start_time = datetime.now()
        starting_users = scenario_commands.num_users
        buffered_users = float(0)

        while datetime.now() <= start_time + timedelta(seconds=seconds):
            if starting_users > target_users:
                users_to_stop = (starting_users - target_users) / int(
                    seconds / wait_period
                )

                buffered_users += users_to_stop

                if int(buffered_users) > 0:
                    scenario_commands.stop_users(int(buffered_users))
                    buffered_users -= int(buffered_users)
            else:
                users_to_start = (target_users - starting_users) / int(
                    seconds / wait_period
                )

                buffered_users += users_to_start

                if int(buffered_users) > 0:
                    scenario_commands.start_users(int(buffered_users))
                    buffered_users -= int(buffered_users)

            latest_results = scenario_commands.get_latest_results()

            scenario_commands.aggregate_results(latest_results)
            scenario_commands.verify_results(latest_results)
            scenario_commands.collect_datastore_metrics(latest_results)

            time.sleep(wait_period)

        if skip_scaledown:
            scenario_commands.scale_users(target_users)
            return

        scenario_commands.scale_users(0)

    return closure


def ramp_users_to_threshold(
    initial_users: int,
    threshold_fn: Callable[[Any], bool],
    next_users_fn: Callable[[int], int] = lambda n: n + 10,
    update_aggregate: Callable[[int, Any], Any] = lambda n, agg: f"Users: {n}",
    period_duration: int = 30,
    period_limit: Optional[int] = None,
    wait_period: int = 1,
    skip_scaledown: bool = False,
):
    """Increase number of users in scenario until a threshold based on the aggregated results is reached.

    Update aggregate with number of users determined by scenario.

    Args:
        initial_users (int): Users to start stage with.
        threshold_fn (Callable[[Any], bool]): Checks aggregate and returns True if threshold reached.
        next_users_fn (Callable[[int], int]): Scale number of users given current number of users.
        update_aggregate (Callable[[int, Any], Any], optional): Update scenario aggregate with result of load model.
        period_duration (int, optional): Time in seconds to wait before scaling test. Defaults to 30.
        period_limit (Optional[int], optional): Amount of scaling events before stopping stage. Defaults to None.
        wait_period (int, optional): Time in seconds to wait before polling for results. Defaults to 1.
        skip_scaledown (bool): Skip scaledown of users after running load function
    """

    def closure(scenario_commands: IScenarioCommands, context: dict):
        scenario_commands.scale_users(initial_users)
        period_count = 0
        period_start = datetime.now()

        while not threshold_fn(scenario_commands.aggregated_results) and (
            period_limit is None or period_limit < period_count
        ):
            latest_results = scenario_commands.get_latest_results()

            scenario_commands.aggregate_results(latest_results)
            scenario_commands.verify_results(latest_results)
            scenario_commands.collect_datastore_metrics(latest_results)

            time.sleep(wait_period)

            if datetime.now() >= period_start + timedelta(seconds=period_duration):
                scenario_commands.scale_users(
                    next_users_fn(scenario_commands.num_users)
                )

                period_count += 1
                period_start = datetime.now()

        scenario_commands.aggregated_results = update_aggregate(
            scenario_commands.num_users, scenario_commands.aggregated_results
        )

        if skip_scaledown:
            return

        scenario_commands.scale_users(0)

    return closure


def load_stages(*stages: LoadModelFn) -> LoadModelFn:
    """Type of load model loop that allows multiple load models to be chained together.

    Returns:
        [LoadModelFn]: Combined load model closure
    """
    # FEATURE: signal user loop that stage has changed from scenario commands
    def closure(scenario_commands: IScenarioCommands, context: dict):
        for stage in stages:
            stage(scenario_commands, context)

        scenario_commands.scale_users(0)

    return closure


def basic_verification(latest_results: List[Result], include_logs=True):
    """Create error strings for each errored result.

    Format:
    * {type}: {error}

    Args:
        latest_results (List[Result]): List of results to generate errors for

    Returns:
        List[str]: List of error strings derived from results
    """
    exception_strings = []

    for result in latest_results:
        if result.exception is None:
            continue

        if include_logs:
            exception_strings.append(
                f"""
* {type(result.exception)}: {str(result.exception)}
{result.logs}"""
            )
        else:
            exception_strings.append(
                f"* {type(result.exception)}: {str(result.exception)}"
            )

    return exception_strings


class Scenario(BaseModel):
    """Store information and methods of testing scenario."""

    name: str
    fn: Callable
    user_loop: Optional[UserLoopFn] = Field(while_has_work())
    load_model: Optional[LoadModelFn] = Field(run_scenario_once())
    dependencies: List["Scenario"] = []
    result_aggregator: Optional[ResultAggregatorFn]
    result_verifier: Optional[ResultVerifierFn] = Field(basic_verification)
    raise_exception: bool = True
    output_transformer: Optional[OutputTransformerFn]
    users_per_instance: int = 50
    # NOTE: may be useful to add these to list later to avoid a potential circular dependency
    metric_collectors: List[MetricCollector] = [
        console_collector("runtime", runtime_seconds),
        console_collector("pass_or_fail", pass_or_fail),
        console_collector("results_per_second", results_per_second),
    ]
    console_metric_displays: Optional[ConsoleMetricDisplays] = {
        "runtimes": console_stats("runtime"),
        "results_per_second": console_stats("results_per_second"),
        "success_rate": console_percent("pass_or_fail", 0.5),
    }
    tags: List[str] = []

    class Config:
        """Needed to allow storage of all types."""

        arbitrary_types_allowed = True


Scenario.update_forward_refs()
