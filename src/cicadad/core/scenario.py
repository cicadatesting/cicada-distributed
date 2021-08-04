from typing import Any, Callable, Dict, Iterable, List, Optional, Set
from datetime import datetime, timedelta
import uuid
import time
import json
import io
import traceback

from pydantic import BaseModel, Field
from cicadad.util.constants import KUBE_CONTAINER_MODE
from dask.distributed import Client, fire_and_forget, secede  # type: ignore

from cicadad.util.context import encode_context
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
            datastore_address: Address of datastore client
        """
        self.scenario = scenario
        self.user_id = user_id
        self.event_buffer: List[datastore.UserEvent] = []
        self.datastore_address = datastore_address

        self.available_work = 0

    def is_up(self):
        """Check if user is still running

        Returns:
            bool: User is up
        """
        return self.get_events("STOP_USER") == []

    def get_events(self, kind: str):
        """Get events sent to user from scenario

        Returns:
            List[UserEvent]: List of user events
            kind: type of event to retrieve
        """
        return datastore.get_user_events(self.user_id, kind, self.datastore_address)

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
                    print("Exception traceback:", file=buffer)
                    traceback.print_tb(e.__traceback__, file=buffer)

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
        test_id: str,
        image: str,
        network: str,
        namespace: str,
        scenario_id: str,
        datastore_address: str,
        container_service_address: str,
        container_mode: str,
        context: dict,
    ):
        """Commands available to a scenario

        Args:
            scenario (Scenario): Scenario being run
            test_id (str): ID of test being run, used to send results
            image (str): Docker image for scenario
            network (str): Docker network for scenario
            namespace (str): Kube namespace to place jobs in
            scenario_id (str): ID of scenario run
            datastore_address (str): Address of datastore to pass to users
            container_service (str): Address of container service to start and stop users
            container_mode (str): DOCKER or KUBE mode to create containers
            context (dict): Context data to pass to users
        """
        self.scenario = scenario
        self.test_id = test_id
        self.image = image
        self.network = network
        self.namespace = namespace
        self.datastore_address = datastore_address
        self.container_service_address = container_service_address
        self.container_mode = container_mode
        self.context = context

        self.scenario_id = scenario_id
        self.user_ids: Set[str] = set()
        self.user_locations: Dict[str, str] = {}
        self.user_manager_counts: Dict[str, int] = {}
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
        if n < 0:
            raise ValueError("Must supply a positive number of users to start")

        if n == 0:
            return

        users_to_start: Dict[str, int] = {}
        remaining_users = n

        # Attempt to fill existing user managers
        for user_manager in self.user_manager_counts:
            if remaining_users < 1:
                break

            remaining_capacity = (
                self.scenario.users_per_container
                - self.user_manager_counts[user_manager]
            )

            users_for_manager = min(remaining_capacity, remaining_users)

            users_to_start[user_manager] = users_for_manager
            remaining_users -= users_for_manager

        # start user managers for remaining users
        while remaining_users > 0:
            user_manager_id = f"user-manager-{str(uuid.uuid4())[:8]}"
            encoded_context = encode_context(self.context)

            # FEATURE: mount env for user + specify args in scenario
            if self.container_mode == KUBE_CONTAINER_MODE:
                container_service.start_kube_container(
                    container_service.StartKubeContainerArgs(
                        name=user_manager_id,
                        # env={}
                        labels={
                            "type": "cicada-distributed-user",
                            "scenario": self.scenario.name,
                            "test": self.test_id,
                        },
                        image=self.image,
                        command=[
                            "run-user",
                            "--name",
                            self.scenario.name,
                            "--user-manager-id",
                            user_manager_id,
                            "--datastore-address",
                            self.datastore_address,
                            "--encoded-context",
                            encoded_context,
                        ],
                        namespace=self.namespace,
                    ),
                    self.container_service_address,
                )
            else:
                container_service.start_docker_container(
                    container_service.StartDockerContainerArgs(
                        name=user_manager_id,
                        # env={}
                        labels={
                            "type": "cicada-distributed-user",
                            "scenario": self.scenario.name,
                            "test": self.test_id,
                        },
                        image=self.image,
                        command=[
                            "run-user",
                            "--name",
                            self.scenario.name,
                            "--user-manager-id",
                            user_manager_id,
                            "--datastore-address",
                            self.datastore_address,
                            "--encoded-context",
                            encoded_context,
                        ],
                        network=self.network,
                    ),
                    self.container_service_address,
                )

            users_for_manager = min(self.scenario.users_per_container, remaining_users)

            users_to_start[user_manager_id] = users_for_manager
            remaining_users -= users_for_manager

        # Signal user managers to start users and update counts
        for user_manager, num_users in users_to_start.items():
            user_ids = [f"user-{str(uuid.uuid4())[:8]}" for _ in range(num_users)]

            self._send_user_event(user_manager, "START_USERS", {"IDs": user_ids})

            for user_id in user_ids:
                self.user_ids.add(user_id)
                self.user_locations[user_id] = user_manager

            if user_manager in self.user_manager_counts:
                self.user_manager_counts[user_manager] += num_users
            else:
                self.user_manager_counts[user_manager] = num_users

            self.num_users += num_users

        # If called add_work before start_users, flush the saved work to the
        # new group of users
        # NOTE: may be possible to get rid of this mechanic
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

            location = self.user_locations[user_id]
            self._send_user_event(user_id, "STOP_USER", {})

            self.user_manager_counts[location] -= 1

            if self.user_manager_counts[location] < 1:
                if self.container_mode == KUBE_CONTAINER_MODE:
                    container_service.stop_kube_container(
                        location,
                        namespace=self.namespace,
                        address=self.container_service_address,
                    )
                else:
                    container_service.stop_docker_container(
                        location,
                        address=self.container_service_address,
                    )

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

    def _send_user_event(self, user_id: str, kind: str, payload: dict):
        datastore.add_user_event(user_id, kind, payload, self.datastore_address)

    def send_user_events(self, kind: str, payload: dict):
        """Send an event to all user in the user pool.

        Args:
            kind (str): Type of event
            payload (dict): JSON dict to send to user
        """
        for user_id in self.user_ids:
            self._send_user_event(user_id, kind, payload)

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


def filter_scenarios_by_tag(
    scenarios: Iterable["Scenario"], tags: List[str]
) -> List["Scenario"]:
    """Filter scenarios that have tags in the list of tags provided. Returns
    all scenarios if tag list is empty

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
    scenario: "Scenario",
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
    container_id = f"scenario-{scenario_id}"
    encoded_context = encode_context(results)

    if container_mode == KUBE_CONTAINER_MODE:
        container_service.start_kube_container(
            container_service.StartKubeContainerArgs(
                image=image,
                name=container_id,
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
                name=container_id,
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
        kind="SCENARIO_STARTED",
        event=datastore.TestStatus(
            scenario=scenario.name,
            message=f"Started scenario: {scenario.name} ({container_id})",
            context=json.dumps(results),
        ),
        address=datastore_address,
    )


def test_runner(
    scenarios: Iterable["Scenario"],
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
    results: Dict[str, dict] = {}

    valid_scenarios = filter_scenarios_by_tag(scenarios, tags)

    datastore.add_test_event(
        test_id=test_id,
        kind="TEST_STARTED",
        event=datastore.TestStatus(
            message=f"Collected {len(valid_scenarios)} Scenario(s)",
        ),
        address=datastore_address,
    )

    # Start scenarios with no dependencies
    for scenario in valid_scenarios:
        if scenario.dependencies == []:
            scenario_id = str(uuid.uuid4())[:8]

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

    # listen to completed events and start scenarios with dependencies
    # FEATURE: scenario timeout counter here as well
    while len(results) != len(valid_scenarios):
        for scenario_name in [sn for sn in started if sn not in results]:
            # FIXME: move logic to eventing function
            # FEATURE: stream back metrics gathered from scenarios
            result = datastore.move_scenario_result(
                started[scenario_name],
                datastore_address,
            )

            if result is not None:
                results[scenario_name] = result

                datastore.add_test_event(
                    test_id=test_id,
                    kind="SCENARIO_FINISHED",
                    event=datastore.TestStatus(
                        scenario=scenario_name,
                        message=f"Finished Scenario: {scenario_name}",
                        context=json.dumps(results),
                    ),
                    address=datastore_address,
                )

        for scenario in [s for s in valid_scenarios if s.name not in started]:
            # FIXME: move filtering to function
            if all(
                dep.name in results and results[dep.name]["exception"] is None
                for dep in scenario.dependencies
            ):
                scenario_id = str(uuid.uuid4())[:8]

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

                datastore.add_test_event(
                    test_id=test_id,
                    kind="SCENARIO_FINISHED",
                    event=datastore.TestStatus(
                        scenario=scenario.name,
                        message=f"Skipped Scenario: {scenario.name}",
                        context=json.dumps(results),
                    ),
                    address=datastore_address,
                )

        # NOTE: maybe make this configurable or shorter?
        time.sleep(1)

    datastore.add_test_event(
        test_id=test_id,
        kind="TEST_FINISHED",
        event=datastore.TestStatus(
            message=f"Finished running {len(valid_scenarios)} Scenario(s)",
        ),
        address=datastore_address,
    )


def scenario_runner(
    scenario: "Scenario",
    test_id: str,
    image: str,
    network: str,
    namespace: str,
    scenario_id: str,
    datastore_address: str,
    container_service_address: str,
    container_mode: str,
    context: dict,
):
    """Set up scenario environment and run scenario. Capture output and exceptions

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


def user_scheduler(
    scheduler: Client,
    scenario: "Scenario",
    user_manager_id: str,
    datastore_address: str,
    context: dict,
):
    """Schedules users inside user manager on events from scenario

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
    secede()

    user_commands = UserCommands(
        scenario,
        user_id,
        datastore_address,
    )

    # FEATURE: report errors here back to scenario
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
                # FEATURE: option to retry on failure
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
    """Run user if hasn't been shut down yet"""

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


def basic_verification(latest_results: List[datastore.Result], include_logs=True):
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
    users_per_container: int = 50
    tags: List[str] = []


Scenario.update_forward_refs()


def load_stages(*stages: LoadModelFn):
    # FEATURE: signal user loop that stage has changed from scenario commands
    def closure(scenario_commands: ScenarioCommands, context: dict):
        for stage in stages:
            stage(scenario_commands, context)

        scenario_commands.scale_users(0)

    return closure
