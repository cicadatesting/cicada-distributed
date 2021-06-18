from typing import Any, Callable, Dict, List, Optional, Set
from datetime import datetime, timedelta
import uuid
import time
import json
import io
import traceback

from pydantic import BaseModel, Field

from cicadad.util.context import encode_context
from cicadad.core import containers
from cicadad.services import datastore, container_service
from cicadad.util import printing


class UserCommands(object):
    def __init__(
        self,
        scenario: "Scenario",
        user_id: str,
        datastore_address: str,
    ):
        """Commands available to user functions.

        Args:
            scenario (Scenario): Scenario being run
            user_id (str): ID of current user
            scenario_id (str): ID of current scenario
            datastore_address: Address of datastore client
        """
        self.scenario = scenario
        self.user_id = user_id
        self.datastore_address = datastore_address

        self.available_work = 0

    def is_up(self):
        """Check if user is still running

        Returns:
            bool: User is up
        """
        # HACK: User is stopped by scenario, but may be useful to explicitly
        # tell user to stop to allow for a graceful user-defined exit
        return True

    def has_work(self, timeout_ms: Optional[int] = 1000):
        """Check if user has remaining invocations

        Args:
            timeout_ms (int, optional): Time to wait for work event to appear before returning. Defaults to 1000.

        Returns:
            bool: User has work
        """
        if self.available_work < 1:
            self.available_work = datastore.get_work(
                self.user_id, self.datastore_address
            )

            if self.available_work < 1 and timeout_ms is not None:
                time.sleep(timeout_ms / 1000)
                self.available_work = datastore.get_work(
                    self.user_id, self.datastore_address
                )

        has_available_work = self.available_work > 0

        if has_available_work:
            self.available_work -= 1

        return has_available_work

    def run(self, *args, log_traceback=True, **kwargs):
        """Run scenario function with arguments; capture exception and logs

        Args:
            log_traceback (bool, optional): Print out traceback for exception. Defaults to True.

        Returns:
            Tuple[Any, Exception, str]: Output, exception, and logs captured
        """
        buffer = io.StringIO()

        with printing.stdout_redirect(buffer):
            try:
                output, exception = self.scenario.fn(*args, **kwargs), None
            except Exception as e:
                output, exception = None, e

                if log_traceback:
                    print("Exception traceback:")
                    traceback.print_tb(e.__traceback__)

        return output, exception, buffer.getvalue()

    def report_result(
        self, output: Any, exception: Any, logs: Optional[str], time_taken: int
    ):
        """Report result for scenario invocation from user to scenario

        Args:
            output (Any): Function output
            exception (Any): Function exception
            logs (Optional[str]): Function logs
            time_taken (int): Time taken in seconds to call function once
        """
        result = datastore.Result(
            id=str(uuid.uuid4()),
            output=output,
            exception=exception,
            logs=logs,
            timestamp=datetime.now(),
            time_taken=time_taken,
        )

        datastore.add_user_result(self.user_id, result, self.datastore_address)


class ScenarioCommands(object):
    def __init__(
        self,
        scenario: "Scenario",
        image: str,
        network: str,
        scenario_id: str,
        datastore_address: str,
        container_service_address: str,
        context: dict,
    ):
        """Commands available to a scenario

        Args:
            scenario (Scenario): Scenario being run
            image (str): Docker image for scenario
            network (str): Docker network for scenario
            scenario_id (str): ID of scenario run
            datastore_address (str): Address of datastore to pass to users
            container_service (str): Address of container service to start and stop users
            context (dict): Context data to pass to users
        """
        self.scenario = scenario
        self.image = image
        self.network = network
        self.datastore_address = datastore_address
        self.container_service_address = container_service_address
        self.context = context

        self.scenario_id = scenario_id
        self.user_ids: Set[str] = set()
        self.num_users = 0
        self.buffered_work = 0
        self.aggregated_results = None
        self.errors: List[str] = []

    def scale_users(self, n: int):
        """Change number of running users

        Args:
            n (int): Desired number of users
        """
        if n > self.num_users:
            self.start_users(n - self.num_users)
        else:
            self.stop_users(self.num_users - n)

    def start_users(self, n: int):
        """Start users for scenario

        Args:
            n (int): Number of users to start
        """
        # FEATURE: will need to determine whether docker or kube args
        # FEATURE: attach additional container args to scenario
        if n < 0:
            raise ValueError("Must supply a positive number of users to start")

        if n == 0:
            return

        # FEATURE: mount env and volumes for user
        for _ in range(n):
            user_id = f"user-{self.scenario.name}-{str(uuid.uuid4())[:8]}"
            encoded_context = encode_context(self.context)

            args = containers.DockerServerArgs(
                image=self.image,
                name=user_id,
                command=[
                    "run-user",
                    "--name",
                    self.scenario.name,
                    "--user-id",
                    user_id,
                    "--datastore-address",
                    self.datastore_address,
                    "--encoded-context",
                    encoded_context,
                ],
                labels=["cicada-distributed-user", self.scenario.name],
                # env: Dict[str, str]={}
                # volumes: Optional[List[Volume]]
                # host_port: Optional[int]
                # container_port: Optional[int]
                network=self.network,
                # create_network: bool=True
            )

            self.user_ids.add(user_id)
            container_service.start_container(args, self.container_service_address)

        self.num_users += n

        # If called add_work before start_users, flush the saved work to the
        # new group of users
        if self.buffered_work > 0:
            self.add_work(self.buffered_work)
            self.buffered_work = 0

    def stop_users(self, n: int):
        """Stop a given number of users

        Args:
            n (int): Number of users to stop
        """
        if self.num_users < n:
            raise ValueError(f"Scenario currently has less than {n} users")

        if n < 0:
            raise ValueError("Must supply a positive number of users to stop")

        if n == 0:
            return

        remaining = n

        for user_id in self.user_ids.copy():
            if remaining < 1:
                break

            container_service.stop_container(user_id, self.container_service_address)
            self.user_ids.remove(user_id)
            self.num_users -= 1
            remaining -= 1

    def add_work(self, n: int):
        """Distribute work to all users in scenario

        Args:
            n (int): Amount of work to distribute across user pool
        """
        # If no users exist, save in a buffer
        if self.user_ids == set():
            self.buffered_work += n
            return

        datastore.distribute_work(n, list(self.user_ids), self.datastore_address)

    def get_latest_results(
        self,
        timeout_ms: Optional[int] = 1000,
    ):
        """Gathers results produced by users

        Args:
            timeout_ms (int, optional): Time to wait for results. Defaults to 1000.

        Returns:
            List[Result]: List of latest results collected
        """
        results = datastore.move_user_results(self.user_ids, self.datastore_address)

        if results == [] and timeout_ms is not None:
            time.sleep(timeout_ms / 1000)
            results = datastore.move_user_results(self.user_ids, self.datastore_address)

        return results

    def aggregate_results(self, latest_results: List[datastore.Result]) -> Any:
        """Run scenario aggregator function against latest gathered results and
        save aggregate

        Args:
            latest_results (List[Result]): Results to run aggregator function on

        Returns:
            Any: Result of scenario aggregator function
        """
        if self.scenario.result_aggregator is not None:
            self.aggregated_results = self.scenario.result_aggregator(
                self.aggregated_results, latest_results
            )
        elif latest_results != []:
            # Default aggregator when results are not empty
            self.aggregated_results = latest_results[-1].output

        return self.aggregated_results

    def verify_results(
        self, latest_results: List[datastore.Result]
    ) -> Optional[List[str]]:
        """Run scenario result verification function against latest results

        Args:
            latest_results (List[Result]): Last results to be collected

        Returns:
            Optional[List[str]]: List of error strings gathered for scenario
        """
        if self.scenario.result_verifier is not None:
            errors = self.scenario.result_verifier(latest_results)

            self.errors.extend(errors)
            return errors

        return None

    # FEATURE: get number of healthy users in scenario, healthy users per group

    # def create_metric(
    #     name: str, description: Union[str, int, float], type: str = "HISTOGRAM"
    # ):
    #     # NOTE: name must be prometheus allowed
    #     return

    # def put_metric(name: str, value: str, description: str, type: str = "HISTOGRAM"):
    #     # create metric if not created yet, then report metric
    #     return

    # def report_metric(name: str, value: str):
    #     return


def filter_scenarios_by_tag(scenarios: List["Scenario"], tags: List[str]):
    """Filter scenarios that have tags in the list of tags provided. Returns
    all scenarios if tag list is empty

    Args:
        scenarios (List[Scenario]): List of scenarios
        tags (List[str]): List of tags to filter scenarios with

    Returns:
        List[Scenario]: List of filtered scenarios
    """
    if tags == []:
        return scenarios

    return [s for s in scenarios if set(s.tags).intersection(set(tags)) != set()]


class TestStatus(BaseModel):
    type: str
    scenario: str
    message: str
    context: str


def test_runner(
    scenarios: List["Scenario"],
    image: str,
    network: str,
    datastore_address: str,
    container_service_address: str,
):
    started: Dict[str, str] = {}
    results: Dict[str, dict] = {}

    # Start scenarios with no dependencies
    for scenario in scenarios:
        if scenario.dependencies == []:
            # FIXME: move to function
            scenario_id = str(uuid.uuid4())[:8]
            container_id = f"scenario-{scenario.name}-{scenario_id}"
            encoded_context = encode_context(results)

            args = containers.DockerServerArgs(
                image=image,
                name=container_id,
                command=[
                    "run-scenario",
                    "--name",
                    scenario.name,
                    "--scenario-id",
                    scenario_id,
                    "--image",
                    image,
                    "--network",
                    network,
                    "--encoded-context",
                    encoded_context,
                    "--datastore-address",
                    datastore_address,
                    "--container-service-address",
                    container_service_address,
                ],
                labels=["cicada-distributed-scenario", scenario.name],
                # env: Dict[str, str]={}
                # volumes: Optional[List[Volume]]
                # host_port: Optional[int]
                # container_port: Optional[int]
                network=network,
                # create_network: bool=True
            )

            container_service.start_container(args, container_service_address)
            started[scenario.name] = scenario_id

            yield TestStatus(
                type="SCENARIO_STARTED",
                scenario=scenario.name,
                message=f"Started scenario: {scenario.name} ({container_id})",
                context=json.dumps(results),
            )

    # listen to completed events and start scenarios with dependencies
    while len(results) != len(scenarios):
        for scenario_name in [sn for sn in started if sn not in results]:
            # FIXME: move logic to eventing function
            # FEATURE: stream back metrics gathered from scenarios
            result = datastore.move_scenario_result(
                started[scenario_name],
                datastore_address,
            )

            if result is not None:
                results[scenario_name] = result

                yield TestStatus(
                    type="SCENARIO_FINISHED",
                    scenario=scenario_name,
                    message=f"Finished Scenario: {scenario_name}",
                    context=json.dumps(results),
                )

        for scenario in [s for s in scenarios if s.name not in started]:
            # FIXME: move filtering to function
            if all(
                dep.name in results and results[dep.name]["exception"] is None
                for dep in scenario.dependencies
            ):
                scenario_id = str(uuid.uuid4())[:8]
                container_id = f"scenario-{scenario.name}-{scenario_id}"
                encoded_context = encode_context(results)

                args = containers.DockerServerArgs(
                    image=image,
                    name=container_id,
                    command=[
                        "run-scenario",
                        "--name",
                        scenario.name,
                        "--scenario-id",
                        scenario_id,
                        "--image",
                        image,
                        "--network",
                        network,
                        "--encoded-context",
                        encoded_context,
                        "--datastore-address",
                        datastore_address,
                        "--container-service-address",
                        container_service_address,
                    ],
                    labels=["cicada-distributed-scenario", scenario.name],
                    # env: Dict[str, str]={}
                    # volumes: Optional[List[Volume]]
                    # host_port: Optional[int]
                    # container_port: Optional[int]
                    network=network,
                    # create_network: bool=True
                )

                container_service.start_container(args, container_service_address)
                started[scenario.name] = scenario_id

                yield TestStatus(
                    type="SCENARIO_STARTED",
                    scenario=scenario.name,
                    message=f"Started scenario: {scenario.name} ({container_id})",
                    context=json.dumps(results),
                )
            elif all(dep.name in results for dep in scenario.dependencies):
                # has all dependencies but some are failed
                started[scenario.name] = str(uuid.uuid4())[:8]
                results[scenario.name] = json.loads(
                    datastore.Result(
                        id=str(uuid.uuid4()),
                        output=None,
                        exception="Skipped",
                        logs="",
                        timestamp=datetime.now(),
                    ).json()
                )

                yield TestStatus(
                    type="SCENARIO_FINISHED",
                    scenario=scenario.name,
                    message=f"Skipped Scenario: {scenario.name}",
                    context=json.dumps(results),
                )

        # NOTE: maybe make this configurable or shorter?
        time.sleep(1)


def scenario_runner(
    scenario: "Scenario",
    image: str,
    network: str,
    scenario_id: str,
    datastore_address: str,
    container_service_address: str,
    context: dict,
):
    """Set up scenario environment and run scenario. Capture output and exceptions

    Args:
        scenario (Scenario): Scenario being run
        image (str): Image for scenario
        network (str): Network to run scenario containers in
        scenario_id (str): ID generated for scenario run
        datastore_address (str): Address of datastore passed to users
        container_service (str): Address of container service to start and stop users
        context (dict): Test context to pass to users
    """
    scenario_commands = ScenarioCommands(
        scenario,
        image,
        network,
        scenario_id,
        datastore_address,
        container_service_address,
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

            if scenario_commands.errors != []:
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

    datastore.set_scenario_result(
        scenario_id=scenario_id,
        output=output,
        exception=exception,
        logs=buffer.getvalue(),
        time_taken=(end - start).seconds,
        address=datastore_address,
    )


def user_runner(
    scenario: "Scenario",
    user_id: str,
    datastore_address: str,
    context: dict,
):
    """Set up environment for user and run user

    Args:
        scenario (Scenario): Scenario being run
        user_id (str): ID generated for user
        datastore_address (str): Address of datastore client to save results
        context (dict): Test context containing previous scenario results
    """
    user_commands = UserCommands(
        scenario,
        user_id,
        datastore_address,
    )

    scenario.user_loop(user_commands, context)  # type: ignore


# FIXME: move these to another module
def while_has_work(polling_timeout_ms: int = 1000):
    """Run user if work is available or continue polling

    Args:
        polling_timeout_ms (UserCommands): Time to wait for work before cycling
    """

    def closure(user_commands: UserCommands, context: dict):
        while user_commands.is_up():
            if user_commands.has_work(polling_timeout_ms):
                start = datetime.now()
                output, exception, logs = user_commands.run(context=context)
                end = datetime.now()
                user_commands.report_result(
                    output,
                    exception,
                    logs,
                    time_taken=(end - start).seconds,
                )

    return closure


def while_alive():
    """Run user if hasn't been shut down yet

    Args:
        polling_timeout_ms (UserCommands): Time to wait for work before cycling
    """

    def closure(user_commands: UserCommands, context: dict):
        while user_commands.is_up():
            start = datetime.now()
            output, exception, logs = user_commands.run(context=context)
            end = datetime.now()
            user_commands.report_result(
                output,
                exception,
                logs,
                time_taken=(end - start).seconds,
            )

    return closure


def iterations_per_second_limited(limit: int):
    """Allows a user to run a limited number of iterations per second.

    Args:
        limit (int): Max iterations per second for user
    """

    def closure(user_commands: UserCommands, context: dict):
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
                    time_taken=(end - start).seconds,
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

    def closure(scenario_commands: ScenarioCommands, context: dict):
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
            num_results += len(latest_results)

            time.sleep(wait_period)

        if skip_scaledown:
            return

        scenario_commands.scale_users(0)

    return closure


def run_scenario_once(wait_period: int = 1, timeout: Optional[int] = 15):
    """Run scenario one time with one user.

    Args:
        wait_period (int, optional): Time in seconds to wait before polling for results. Defaults to 1.
        timeout (int, optional): Time in seconds to wait for scenario to complete before failing. Defaults to 15.

    Returns:
        Callable: Closure for configured load model
    """
    return n_iterations(1, 1, wait_period, timeout)


def n_seconds(
    seconds: int,
    users: int,
    wait_period: int = 1,
    skip_scaledown=False,
):
    """Run the scenario for a specified duration. Should be used with the
    'while_alive' user loop.

    Args:
        seconds (int): Number of seconds to run scenario
        users (int): Number of users to start for scenario
        wait_period (int, optional): Time in seconds to wait before polling for results. Defaults to 1.
        skip_scaledown (bool): Skip scaledown of users after running load function
    """

    def closure(scenario_commands: ScenarioCommands, context: dict):
        scenario_commands.scale_users(users)

        # collect results for specified seconds
        start_time = datetime.now()

        while datetime.now() < start_time + timedelta(seconds=seconds):
            # FIXME: ensure remaining results are collected
            latest_results = scenario_commands.get_latest_results()

            scenario_commands.aggregate_results(latest_results)
            scenario_commands.verify_results(latest_results)

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

    def closure(scenario_commands: ScenarioCommands, context: dict):
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
    """Increase number of users in scenario until a threshold based on the
    aggregated results is reached.

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

    def closure(scenario_commands: ScenarioCommands, context: dict):
        scenario_commands.scale_users(initial_users)
        period_count = 0
        period_start = datetime.now()

        while not threshold_fn(scenario_commands.aggregated_results) and (
            period_limit is None or period_limit < period_count
        ):
            latest_results = scenario_commands.get_latest_results()

            scenario_commands.aggregate_results(latest_results)
            scenario_commands.verify_results(latest_results)

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


def basic_verification(latest_results: List[datastore.Result]):
    """Create error strings for each errored result.

    Format:
    * {type}: {error}

    Args:
        latest_results (List[Result]): List of results to generate errors for

    Returns:
        List[str]: List of error strings derived from results
    """
    return [
        f"* {type(result.exception)}: {str(result.exception)}"
        for result in latest_results
        if result.exception is not None
    ]


UserLoopFn = Callable[[UserCommands, dict], None]
LoadModelFn = Callable[[ScenarioCommands, dict], Any]
ResultAggregatorFn = Callable[[Optional[Any], List[datastore.Result]], Any]
ResultVerifierFn = Callable[[List[datastore.Result]], List[str]]
OutputTransformerFn = Callable[[Optional[Any]], Any]


class Scenario(BaseModel):
    name: str
    fn: Callable
    user_loop: Optional[UserLoopFn] = Field(while_has_work())
    load_model: Optional[LoadModelFn] = Field(run_scenario_once())
    dependencies: List["Scenario"] = []
    result_aggregator: Optional[ResultAggregatorFn]
    result_verifier: Optional[ResultVerifierFn] = Field(basic_verification)
    output_transformer: Optional[OutputTransformerFn]
    tags: List[str] = []


Scenario.update_forward_refs()


def load_stages(*stages: LoadModelFn):
    def closure(scenario_commands: ScenarioCommands, context: dict):
        for stage in stages:
            stage(scenario_commands, context)

        scenario_commands.scale_users(0)

    return closure


# FEATURE: signal user loop that stage has changed from scenario commands
