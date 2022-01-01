from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from pydantic.main import BaseModel


class Result(BaseModel):
    """Result generated by a user or scenario."""

    id: Optional[str]
    output: Optional[Any]
    exception: Optional[Any]
    logs: Optional[str]
    timestamp: Optional[datetime]
    time_taken: Optional[int]

    class Config:
        """Encode class as JSON."""

        json_encoders = {
            Exception: lambda e: str(e),
        }


class UserEvent(BaseModel):
    kind: str
    payload: dict


class IScenarioCommands(ABC):
    """Interface to decouple scenario commands from scenario."""

    @property
    @abstractmethod
    def test_id(self) -> str:
        """Get ID of current test"""
        pass

    @property
    @abstractmethod
    def scenario_id(self) -> str:
        """Get ID of current scenario"""
        pass

    @property
    @abstractmethod
    def aggregated_results(self) -> Any:
        """Get result based on all results gathered from users."""
        pass

    @aggregated_results.setter
    def aggregated_results(self, val: Any):
        pass

    @property
    @abstractmethod
    def num_users(self) -> int:
        """Get number of users currently running in scenario."""
        pass

    @property
    @abstractmethod
    def num_results_collected(self) -> int:
        """Get number of results collected from users."""
        pass

    @property
    @abstractmethod
    def errors(self) -> List[str]:
        """List of errors reported by users."""
        pass

    @abstractmethod
    def scale_users(self, n: int):
        """Change number of running users.

        Args:
            n (int): Desired number of users
        """

    @abstractmethod
    def start_users(self, n: int):
        """Start users for a scenario.

        Args:
            n (int): number of users to start
        """
        pass

    @abstractmethod
    def stop_users(self, n: int):
        """Stop users for a scenario.

        Args:
            n (int): number of users to stop
        """
        pass

    @abstractmethod
    def add_work(self, n: int):
        """Distribute work (iterations) to all users in scenario.

        Args:
            n (int): Amount of work to distribute across user pool
        """
        pass

    @abstractmethod
    def send_user_events(self, kind: str, payload: dict):
        """Send an event to all user in the user pool.

        Args:
            kind (str): Type of event
            payload (dict): JSON dict to send to user
        """
        pass

    @abstractmethod
    def get_latest_results(
        self,
        timeout_ms: Optional[int] = 1000,
        limit: int = 500,
    ) -> List[Result]:
        """Gathers results produced by users.

        Args:
            timeout_ms (int, optional): Time to wait for results. Defaults to 1000.
            limit (int): Max results to return. Defaults to 500

        Returns:
            List[Result]: List of latest results collected
        """
        pass

    @abstractmethod
    def aggregate_results(self, latest_results: List[Result]) -> Any:
        """Run scenario aggregator function against latest gathered results and
        save aggregate.

        Args:
            latest_results (List[Result]): Results to run aggregator function on

        Returns:
            Any: Result of scenario aggregator function
        """
        pass

    @abstractmethod
    def verify_results(self, latest_results: List[Result]) -> Optional[List[str]]:
        """Run scenario result verification function against latest results.

        Args:
            latest_results (List[Result]): Last results to be collected

        Returns:
            Optional[List[str]]: List of error strings gathered for scenario
        """
        pass

    @abstractmethod
    def collect_datastore_metrics(self, latest_results: List[Result]):
        """Parse latest results and save metrics if any can be parsed from result set.

        Args:
            latest_results (List[Result]): List of latest collected results
        """
        pass


class IUserCommands(ABC):
    """Interface to decouple user commands from scenario."""

    @property
    @abstractmethod
    def available_work(self) -> int:
        """Get amount of work available to user."""
        pass

    @abstractmethod
    def is_up(self) -> bool:
        """Check if user is still running.

        Returns:
            bool: User is up
        """
        pass

    @abstractmethod
    def has_work(self, timeout_ms: Optional[int] = 1000) -> bool:
        """Check if user has remaining invocations.

        Args:
            timeout_ms (int, optional): Time to wait for work event to appear before returning. Defaults to 1000.

        Returns:
            bool: User has work
        """
        pass

    @abstractmethod
    def run(self, *args, log_traceback=True, **kwargs) -> Tuple[Any, Exception, str]:
        """Run scenario function with arguments; capture exception and logs.

        Args:
            log_traceback (bool, optional): Print out traceback for exception. Defaults to True.

        Returns:
            Tuple[Any, Exception, str]: Output, exception, and logs captured
        """
        pass

    @abstractmethod
    def report_result(
        self, output: Any, exception: Any, logs: Optional[str], time_taken: int
    ):
        """Report result for scenario invocation from user to scenario.

        Args:
            output (Any): Function output
            exception (Any): Function exception
            logs (Optional[str]): Function logs
            time_taken (int): Time taken in seconds to call function once
        """
        pass


UserLoopFn = Callable[[IUserCommands, dict], None]
LoadModelFn = Callable[[IScenarioCommands, dict], Any]
ResultAggregatorFn = Callable[[Optional[Any], List[Result]], Any]
ResultVerifierFn = Callable[[List[Result]], List[str]]
OutputTransformerFn = Callable[[Optional[Any]], Any]
MetricCollector = Callable[[List[Result], IScenarioCommands], None]
ConsoleMetricDisplays = Dict[str, Callable[[str, str, str], Optional[str]]]


class TestStatus(BaseModel):
    scenario: Optional[str]
    scenario_id: Optional[str]
    message: str
    context: Optional[str]


class ScenarioMetric(BaseModel):
    scenario: str
    metrics: Dict[str, Optional[str]]


class TestEvent(BaseModel):
    kind: str
    payload: Union[TestStatus, ScenarioMetric]


class ITestDatastore(ABC):
    """Datastore methods available to test runner"""

    @abstractmethod
    def add_test_event(self, event: TestEvent):
        """Send event from test.

        Args:
            event (TestEvent): Event to send from test
        """
        # TODO: store test_id on implementation
        pass

    @abstractmethod
    def get_test_events(self) -> List[TestEvent]:
        """Get events for test.

        Returns:
            List[TestEvent]: Events gathered for test
        """
        pass

    @abstractmethod
    def move_scenario_result(self, scenario_id: str) -> Optional[dict]:
        """Get result for scenario managed by test.

        Args:
            scenario_id (str): ID of scenario to get result for.

        Returns:
            Optional[dict]: Result returned by scenario
        """
        # TODO: see if it can return Optional[Result] instead of dict
        pass

    @abstractmethod
    def get_metric_statistics(self, scenario_id: str, name: str):
        """Get statistical breakdown of metric (min, median, average, length, max).

        Args:
            scenario_id (str): Scenario ID to get metrics for
            name (str): Name of metric to retrieve
        """
        pass

    @abstractmethod
    def get_metric_total(self, scenario_id: str, name: str):
        """Get total value of metric.

        Args:
            scenario_id (str): Scenario ID to get metrics for
            name (str): Name of metric to retrieve
        """
        pass

    @abstractmethod
    def get_last_metric(self, scenario_id: str, name: str):
        """Get latest reported value for metric.

        Args:
            scenario_id (str): Scenario ID to get metrics for
            name (str): Name of metric to retrieve
        """
        pass

    @abstractmethod
    def get_metric_rate(self, scenario_id: str, name: str, split_point: float):
        """Get amount of results above the split point.

        Args:
            scenario_id (str): Scenario ID to get metrics for
            name (str): Name of metric to retrieve
            split_point (float): Value to split metric groups at
        """
        pass


class IScenarioDatastore(ABC):
    """Datastore methods available to scenario"""

    @abstractmethod
    def distribute_work(self, n: int, user_ids: List[str]):
        """Send work to users in scenario.

        Args:
            n (int): Amount of work to distribute
            user_ids (List[str]): IDs of users to recieve work
        """
        # TODO: store datastore address on implementation
        # TODO: track user ids for scenario in datastore
        pass

    @abstractmethod
    def send_user_events(self, user_ids: List[str], kind: str, payload: dict):
        """Send events to users in scenario.

        Args:
            kind (str): Type of event to send
            payload (dict): Body of event
        """
        # TODO: remove need for user ids
        pass

    @abstractmethod
    def move_user_results(self, user_ids: List[str], limit: int) -> List[Result]:
        """Get user results from datastore.

        Args:
            limit (int): Limit of results to capture

        Returns:
            List[Result]: User results gathered from datastore
        """
        # TODO: remove need for user ids
        pass

    @abstractmethod
    def set_scenario_result(
        output: Any,
        exception: Any,
        logs: str,
        time_taken: float,
        succeeded: int,
        failed: int,
    ):
        """Set result for scenario after completion.

        Args:
            output (Any): Scenario output
            exception (Any): Exception that occured when running scenario
            logs (str): Logs generated by scenario
            time_taken (float): Elapsed time running scenario
            succeeded (int): Amount of succeeded attempts
            failed (int): Amount of failed attempts
        """
        # TODO: store scenario id on implementation
        pass

    @abstractmethod
    def add_metric(self, name: str, value: float):
        """Send metric to from scenario to datastore.

        Args:
            name (str): Name of metric to send
            value (float): Numeric value to report
        """
        pass


class IUserDatastore(ABC):
    """Datastore methods available to user."""

    @abstractmethod
    def get_user_events(self, user_id: str, kind: str) -> List[UserEvent]:
        """Get events for current user.

        Args:
            user_id (str): [description]
            kind (str): Type of event to get

        Returns:
            List[UserEvent]: [description]
        """
        # TODO: store user id on implementation
        pass

    @abstractmethod
    def get_work(self, user_id: str) -> int:
        """Get new work for current user.

        Args:
            user_id (str): [description]

        Returns:
            int: Amount of new work for user
        """
        pass

    @abstractmethod
    def add_user_result(self, user_id: str, result: Result):
        """Report cycle result for user.

        Args:
            user_id (str): [description]
            result (Result): Result to report
        """
        pass
