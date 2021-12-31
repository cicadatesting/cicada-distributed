from datetime import datetime
import io
import traceback
from typing import Any, Dict, List, Optional, Set
import uuid
import time

from cicadad.core.scenario import Scenario
from cicadad.core.types import IScenarioCommands, IUserCommands, Result
from cicadad.util import printing
from cicadad.util.constants import KUBE_CONTAINER_MODE
from cicadad.util.context import encode_context
from cicadad.services import container_service, datastore


class ScenarioCommands(IScenarioCommands):
    def __init__(
        self,
        scenario: Scenario,
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
        self.image = image  # TODO: track test info in datastore
        self.network = network
        self.namespace = namespace
        self.datastore_address = datastore_address  # TODO: take datastore and container service implementation classes
        self.container_service_address = container_service_address
        self.container_mode = container_mode
        self.context = context
        self.scenario_id = scenario_id

        self.user_ids: Set[str] = set()  # TODO: track in datastore
        self.user_locations: Dict[str, str] = {}
        self.user_manager_counts: Dict[str, int] = {}
        self.__num_users = 0
        self.buffered_work = 0  # TODO: track in datastore
        self.__num_results_collected = 0
        self.__aggregated_results = None
        self.__errors: List[str] = []

    @property
    def aggregated_results(self) -> Any:
        return self.__aggregated_results

    @aggregated_results.setter
    def aggregated_results(self, val: Any):
        self.__aggregated_results = val

    @property
    def num_users(self) -> int:
        return self.__num_users

    @property
    def num_results_collected(self):
        return self.__num_results_collected

    @property
    def errors(self) -> List[str]:
        return self.__errors

    def scale_users(self, n: int):
        if n > self.num_users:
            self.start_users(n - self.num_users)
        else:
            self.stop_users(self.num_users - n)

    def start_users(self, n: int):
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

            self.__num_users += num_users

        # If called add_work before start_users, flush the saved work to the
        # new group of users
        # NOTE: may be possible to get rid of this mechanic
        if self.buffered_work > 0:
            self.add_work(self.buffered_work)
            self.buffered_work = 0

    def stop_users(self, n: int):
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
            self.__num_users -= 1
            remaining -= 1

    def add_work(self, n: int):
        # If no users exist, save in a buffer
        if self.user_ids == set():
            self.buffered_work += n
            return

        datastore.distribute_work(n, list(self.user_ids), self.datastore_address)

    def _send_user_event(self, user_id: str, kind: str, payload: dict):
        datastore.add_user_event(user_id, kind, payload, self.datastore_address)

    def send_user_events(self, kind: str, payload: dict):
        for user_id in self.user_ids:
            self._send_user_event(user_id, kind, payload)

    def get_latest_results(
        self,
        timeout_ms: Optional[int] = 1000,
        limit: int = 500,
    ):
        results = datastore.move_user_results(
            self.user_ids, limit, self.datastore_address
        )

        # Wait timeout_ms and get results again if no results
        if results == [] and timeout_ms is not None:
            time.sleep(timeout_ms / 1000)
            results = datastore.move_user_results(
                self.user_ids, limit, self.datastore_address
            )

        # Get rest of results if limit reached
        all_results = results[:]

        while len(results) >= limit:
            results = datastore.move_user_results(
                self.user_ids, limit, self.datastore_address
            )

            all_results.extend(results)

        self.__num_results_collected += len(all_results)

        return all_results

    def aggregate_results(self, latest_results: List[Result]) -> Any:
        if self.scenario.result_aggregator is not None:
            self.__aggregated_results = self.scenario.result_aggregator(
                self.aggregated_results, latest_results
            )
        elif latest_results != []:
            # Default aggregator when results are not empty
            self.__aggregated_results = latest_results[-1].output

        return self.aggregated_results

    def verify_results(self, latest_results: List[Result]) -> Optional[List[str]]:
        if self.scenario.result_verifier is not None:
            errors = self.scenario.result_verifier(latest_results)

            self.__errors.extend(errors)
            return errors

        return None

    # FEATURE: get number of healthy users in scenario, healthy users per group

    def collect_metrics(self, latest_results: List[Result]):
        for collector in self.scenario.metric_collectors:
            collector(latest_results, self)


class UserCommands(IUserCommands):
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

        self.__available_work = 0

    @property
    def available_work(self):
        return self.__available_work

    def is_up(self):
        return self.get_events("STOP_USER") == []

    def get_events(self, kind: str):
        return datastore.get_user_events(self.user_id, kind, self.datastore_address)

    def has_work(self, timeout_ms: Optional[int] = 1000):
        if self.available_work < 1:
            self.__available_work = datastore.get_work(
                self.user_id, self.datastore_address
            )

            if self.available_work < 1 and timeout_ms is not None:
                time.sleep(timeout_ms / 1000)
                self.__available_work = datastore.get_work(
                    self.user_id, self.datastore_address
                )

        has_available_work = self.available_work > 0

        if has_available_work:
            self.__available_work -= 1

        return has_available_work

    def run(self, *args, log_traceback=True, **kwargs):
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
        result = Result(
            id=str(uuid.uuid4()),
            output=output,
            exception=exception,
            logs=logs,
            timestamp=datetime.now(),
            time_taken=time_taken,
        )

        datastore.add_user_result(self.user_id, result, self.datastore_address)
