from datetime import datetime
import io
import traceback
from typing import Any, List, Optional
import uuid

from cicadad.core.scenario import Scenario
from cicadad.core.types import (
    IScenarioCommands,
    IScenarioBackend,
    IUserCommands,
    IUserBackend,
    Result,
)
from cicadad.util import printing
from cicadad.util.constants import ONE_SEC_MS


class ScenarioCommands(IScenarioCommands):
    def __init__(
        self,
        scenario: Scenario,
        test_id: str,
        scenario_id: str,
        backend: IScenarioBackend,
        context: dict,
    ):
        """Commands available to a scenario.

        Args:
            scenario (Scenario): Scenario being run
            test_id (str): ID of test being run, used to send results
            scenario_id (str): ID of scenario run
            backend (IScenarioBackend): Address of backend to pass to users
            context (dict): Context data to pass to users
        """
        self.__scenario = scenario
        self.__test_id = test_id
        self.__backend = backend
        self.__context = context
        self.__scenario_id = scenario_id

        # FEATURE: get number of healthy users in scenario, healthy users per group
        # have method in IScenarioBackend to get num actual users, num user managers
        # See if it can replace __num_users counter
        self.__num_users = 0
        self.__num_results_collected = 0
        self.__aggregated_results = None
        self.__errors: List[str] = []

    @property
    def test_id(self) -> str:
        """Get ID of current test."""
        return self.__test_id

    @property
    def scenario_id(self) -> str:
        """Get ID of current scenario."""
        return self.__scenario_id

    @property
    def context(self) -> dict:
        return self.__context

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
        if n > self.__num_users:
            self.start_users(n - self.__num_users)
        else:
            self.stop_users(self.__num_users - n)

    def start_users(self, n: int):
        self.__backend.create_users(amount=n)
        self.__num_users += n

    def stop_users(self, n: int):
        self.__backend.stop_users(amount=n)
        self.__num_users -= min(n, self.__num_users)

    def add_work(self, n: int):
        self.__backend.distribute_work(n)

    def send_user_events(self, kind: str, payload: dict):
        self.__backend.send_user_events(kind, payload)

    def get_latest_results(
        self,
        timeout_ms: Optional[int] = ONE_SEC_MS,
        limit: int = 500,
    ):
        all_results = self.__backend.move_user_results(limit, timeout_ms)

        # FEATURE: Get rest of results if limit reached
        # all_results = results[:]

        # while len(results) >= limit:
        #     results = datastore.move_user_results(
        #         self.__user_ids, limit, self.datastore_address
        #     )

        #     all_results.extend(results)

        self.__num_results_collected += len(all_results)

        return all_results

    def aggregate_results(self, latest_results: List[Result]) -> Any:
        if self.__scenario.result_aggregator is not None:
            self.__aggregated_results = self.__scenario.result_aggregator(
                self.__aggregated_results, latest_results
            )
        elif latest_results != []:
            # Default aggregator when results are not empty
            self.__aggregated_results = latest_results[-1].output

        return self.__aggregated_results

    def verify_results(self, latest_results: List[Result]) -> Optional[List[str]]:
        if self.__scenario.result_verifier is not None:
            errors = self.__scenario.result_verifier(latest_results)

            self.__errors.extend(errors)
            return errors

        return None

    def collect_datastore_metrics(self, latest_results: List[Result]):
        for collector in self.__scenario.metric_collectors:
            collector(latest_results, self.__backend)


class UserCommands(IUserCommands):
    def __init__(
        self,
        scenario: Scenario,
        user_id: str,
        backend: IUserBackend,
    ):
        """Commands available to user functions.

        Args:
            scenario (Scenario): Scenario being run
            user_id (str): ID of current user
            backend_address: Address of backend client
        """
        self.__scenario = scenario
        self.__user_id = user_id
        self.__backend = backend

        self.__available_work = 0

    @property
    def user_id(self):
        return self.__user_id

    def is_up(self):
        return not any(
            id == self.__user_id
            for event in self.get_events("STOP_USERS")
            for id in event.payload["IDs"]
        )

    def get_events(self, kind: str):
        return self.__backend.get_user_events(kind)

    def has_work(self, timeout_ms: Optional[int] = ONE_SEC_MS):
        if self.__available_work < 1:
            self.__available_work += self.__backend.get_work(timeout_ms)

        has_available_work = self.__available_work > 0

        if has_available_work:
            self.__available_work -= 1

        return has_available_work

    def run(self, *args, log_traceback=True, **kwargs):
        buffer = io.StringIO()

        with printing.stdout_redirect(buffer):
            try:
                output, exception = self.__scenario.fn(*args, **kwargs), None
            except Exception as e:
                output, exception = None, e

                if log_traceback:
                    print("Exception traceback:", file=buffer)
                    traceback.print_tb(e.__traceback__, file=buffer)

        return output, exception, buffer.getvalue()

    def report_result(
        self, output: Any, exception: Any, logs: Optional[str], time_taken: float
    ):
        result = Result(
            id=str(uuid.uuid4()),
            output=output,
            exception=exception,
            logs=logs,
            timestamp=datetime.now(),
            time_taken=time_taken,
        )

        self.__backend.add_user_result(result)
