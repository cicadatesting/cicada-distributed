from typing import Any, Dict, List, Optional
import time
import pickle  # nosec
import json
import random
from distributed.client import Future  # type: ignore

import grpc  # type: ignore

from google.protobuf import wrappers_pb2

from cicadad.core.types import (
    ICLIBackend,
    IConsoleMetricsBackend,
    IScenarioBackend,
    ITestBackend,
    IUserBackend,
    IUserManagerBackend,
    Result,
    TestEvent,
    UserEvent,
)
from cicadad.protos import backend_pb2, backend_pb2_grpc
from cicadad.util.constants import DEFAULT_BACKEND_ADDRESS, ONE_SEC_MS


class CLIBackend(ICLIBackend):
    def __init__(self, address: str) -> None:
        self.__address = address

    def create_test(
        self,
        scheduling_metadata: str,
        backend_address: str,
        tags: List[str],
        env: Dict[str, str],
    ) -> str:
        # NOTE: backend address in instance may be different from outside instance on CLI
        return _create_test(
            scheduling_metadata, tags, env, backend_address, self.__address
        )

    def get_test_events(self, test_id: str) -> List[TestEvent]:
        return _get_test_events(test_id, self.__address)

    def clean_test_instances(self, test_id: str):
        _clean_test_instances(test_id, self.__address)


class UserBufferActor(object):
    """Actor to buffer work and events for users."""

    def __init__(self, user_manager_id: str, backend_address: str):
        self.__user_manager_id = user_manager_id
        self.__backend_address = backend_address

        self.__user_events: Dict[str, List[UserEvent]] = {}
        self.__user_work: Dict[str, int] = {}
        self.__results: List[Result] = []

    def add_users(self, user_ids: List[str]) -> Future:
        """Add a user for tracking events and work.

        Args:
            user_ids (List[str]): User IDs to add
        """
        for user_id in user_ids:
            self.__user_events[user_id] = []
            self.__user_work[user_id] = 0

    def get_user_events(self, user_id: str, kind: str) -> Future:
        """Get events for a user in the user manager or refresh events.

        Args:
            user_id (str): User ID to get events for
            kind (str): Type of event to retrieve

        Returns:
            List[UserEvent]: List of events for this user
        """
        if user_id not in self.__user_events:
            return []

        if self.__user_events[user_id] == []:
            user_manager_events = _get_user_events(
                self.__user_manager_id,
                kind,
                self.__backend_address,
            )

            for event in user_manager_events:
                for user_id in self.__user_events:
                    self.__user_events[user_id].append(event)

        user_events = self.__user_events[user_id]
        self.__user_events[user_id] = []

        return user_events

    def get_user_work(self, user_id: str) -> Future:
        """Get work for user or refresh work for all users.

        Args:
            user_id (str): User ID to get work for

        Returns:
            int: Amount of work allocated to user
        """
        if user_id not in self.__user_work:
            return 0

        if self.__user_work[user_id] == 0:
            user_manager_work = _get_user_work(
                self.__user_manager_id,
                self.__backend_address,
            )

            shuffled_user_ids = list(self.__user_work.keys())
            random.shuffle(shuffled_user_ids)

            # FEATURE: backend might be able to do this
            base_work = user_manager_work // len(shuffled_user_ids)
            remaining_work = user_manager_work % len(shuffled_user_ids)

            for user_id in shuffled_user_ids:
                self.__user_work[user_id] += base_work

            for (_, user_id) in zip(range(remaining_work), shuffled_user_ids):
                self.__user_work[user_id] += 1

        user_work = self.__user_work[user_id]
        self.__user_work[user_id] = 0

        return user_work

    def add_user_result(self, result: Result) -> Future:
        """Add user result to buffer.

        Args:
            result (Result): User result
        """
        self.__results.append(result)

    def send_user_results(self) -> Future:
        """Flushes buffer of user results and sends them to datastore."""
        # TODO: user results should be less than 1MB
        _add_user_results(
            self.__user_manager_id, self.__results, self.__backend_address
        )

        self.__results = []


class UserBackend(IUserBackend):
    def __init__(self, user_id: str, buffer: UserBufferActor):
        self.__user_id = user_id
        self.__buffer = buffer

    def get_user_events(self, kind: str) -> List[UserEvent]:
        return self.__buffer.get_user_events(self.__user_id, kind).result()

    def get_work(self, timeout_ms: Optional[int] = ONE_SEC_MS) -> int:
        work = self.__buffer.get_user_work(self.__user_id).result()

        if work < 1 and timeout_ms is not None:
            time.sleep(timeout_ms / ONE_SEC_MS)
            work = self.__buffer.get_user_work(self.__user_id).result()

        return work

    def add_user_result(self, result: Result):
        self.__buffer.add_user_result(result).result()


class UserManagerBackend(IUserManagerBackend):
    def __init__(self, user_manager_id: str, buffer: UserBufferActor, address: str):
        self.__user_manager_id = user_manager_id
        self.__buffer = buffer
        self.__address = address

    def get_new_users(self) -> List[str]:
        events = _get_user_events(self.__user_manager_id, "START_USERS", self.__address)

        user_ids = [user_id for event in events for user_id in event.payload["IDs"]]

        self.__buffer.add_users(user_ids).result()
        return user_ids

    def get_user_backend(self, user_id: str) -> IUserBackend:
        return UserBackend(
            user_id=user_id,
            buffer=self.__buffer,
        )

    def send_user_results(self):
        self.__buffer.send_user_results().result()


class ScenarioBackend(IScenarioBackend):
    def __init__(self, test_id: str, scenario_id: str, address: str) -> None:
        self.__test_id = test_id
        self.__scenario_id = scenario_id
        self.__address = address

    def create_users(self, amount: int) -> List[str]:
        return _create_users(self.__test_id, self.__scenario_id, amount, self.__address)

    def stop_users(self, amount: int):
        _stop_users(self.__scenario_id, amount, self.__address)

    def distribute_work(self, n: int):
        _distribute_work(
            scenario_id=self.__scenario_id, amount=n, address=self.__address
        )

    def send_user_events(self, kind: str, payload: dict):
        _add_user_event(
            scenario_id=self.__scenario_id,
            kind=kind,
            payload=payload,
            address=self.__address,
        )

    def move_user_results(
        self, limit: int, timeout_ms: Optional[int] = ONE_SEC_MS
    ) -> List[Result]:
        # Wait timeout_ms and get results again if no results
        results = _move_user_results(
            scenario_id=self.__scenario_id, limit=limit, address=self.__address
        )

        if results == [] and timeout_ms is not None:
            time.sleep(timeout_ms / ONE_SEC_MS)
            results = _move_user_results(
                scenario_id=self.__scenario_id, limit=limit, address=self.__address
            )

        return results

    def set_scenario_result(
        self,
        output: Any,
        exception: Any,
        logs: str,
        time_taken: float,
        succeeded: int,
        failed: int,
    ):
        _set_scenario_result(
            scenario_id=self.__scenario_id,
            output=output,
            exception=exception,
            logs=logs,
            time_taken=time_taken,
            succeeded=succeeded,
            failed=failed,
            address=self.__address,
        )

    def add_metric(self, name: str, value: float):
        _add_metric(
            scenario_id=self.__scenario_id,
            name=name,
            value=value,
            address=self.__address,
        )


class ConsoleMetricsBackend(IConsoleMetricsBackend):
    def __init__(self, address: str) -> None:
        self.__address = address

    def get_metric_statistics(self, scenario_id: str, name: str) -> Optional[dict]:
        return _get_metric_statistics(scenario_id, name, self.__address)

    def get_metric_total(self, scenario_id: str, name: str) -> Optional[float]:
        return _get_metric_total(scenario_id, name, self.__address)

    def get_last_metric(self, scenario_id: str, name: str) -> Optional[float]:
        return _get_last_metric(scenario_id, name, self.__address)

    def get_metric_rate(
        self, scenario_id: str, name: str, split_point: float
    ) -> Optional[float]:
        return _get_metric_rate(scenario_id, name, split_point, self.__address)


class TestBackend(ITestBackend):
    def __init__(self, test_id: str, address: str) -> None:
        self.__test_id = test_id
        self.__address = address

    def create_scenario(
        self,
        scenario_name: str,
        context: str,
        users_per_instance: int,
        tags: List[str],
    ) -> str:
        return _create_scenario(
            self.__test_id,
            scenario_name,
            context,
            users_per_instance,
            tags,
            self.__address,
        )

    def add_test_event(self, event: TestEvent):
        _add_test_event(self.__test_id, event, self.__address)

    def move_scenario_result(self, scenario_id: str) -> Optional[dict]:
        return _move_scenario_result(scenario_id, self.__address)

    def get_console_metrics_backend(self) -> IConsoleMetricsBackend:
        return ConsoleMetricsBackend(self.__address)

    def scenario_running(self, scenario_id: str) -> bool:
        return _check_test_instance(self.__test_id, scenario_id, self.__address)


def _create_test(
    scheduling_metadata: str,
    tags: List[str],
    env: Dict[str, str],
    backend_address: str,
    address: str = DEFAULT_BACKEND_ADDRESS,
) -> str:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = backend_pb2_grpc.BackendStub(channel)
        request = backend_pb2.CreateTestRequest(
            backendAddress=backend_address,
            schedulingMetadata=scheduling_metadata,
            tags=tags,
            env=env,
        )

        response = stub.CreateTest(request)

        return response.testID


def _create_scenario(
    test_id: str,
    scenario_name: str,
    context: str,
    users_per_instance: int,
    tags: List[str],
    address: str = DEFAULT_BACKEND_ADDRESS,
) -> str:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = backend_pb2_grpc.BackendStub(channel)
        request = backend_pb2.CreateScenarioRequest(
            testID=test_id,
            scenarioName=scenario_name,
            context=context,
            usersPerInstance=users_per_instance,
            tags=tags,
        )

        response = stub.CreateScenario(request)

        return response.scenarioID


def _create_users(
    test_id: str,
    scenario_id: str,
    amount: int,
    address: str = DEFAULT_BACKEND_ADDRESS,
) -> List[str]:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = backend_pb2_grpc.BackendStub(channel)
        request = backend_pb2.CreateUsersRequest(
            testID=test_id, scenarioID=scenario_id, amount=amount
        )

        response = stub.CreateUsers(request)

        return response.userManagerIDs


def _stop_users(
    scenario_id: str,
    amount: int,
    address: str = DEFAULT_BACKEND_ADDRESS,
):
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = backend_pb2_grpc.BackendStub(channel)
        request = backend_pb2.StopUsersRequest(scenarioID=scenario_id, amount=amount)

        stub.StopUsers(request)


def _clean_test_instances(test_id: str, address: str = DEFAULT_BACKEND_ADDRESS):
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = backend_pb2_grpc.BackendStub(channel)
        request = backend_pb2.CleanTestInstancesRequest(testID=test_id)

        stub.CleanTestInstances(request)


def _check_test_instance(
    test_id: str, instance_id: str, address: str = DEFAULT_BACKEND_ADDRESS
):
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = backend_pb2_grpc.BackendStub(channel)
        request = backend_pb2.CheckTestInstanceRequest(
            testID=test_id, instanceID=instance_id
        )

        response = stub.CheckTestInstance(request)

        return response.running


def _add_test_event(
    test_id: str,
    event: TestEvent,
    address: str = DEFAULT_BACKEND_ADDRESS,
):
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = backend_pb2_grpc.BackendStub(channel)
        request = backend_pb2.AddEventRequest(
            id=test_id,
            event=backend_pb2.Event(
                kind=event.kind,
                payload=pickle.dumps(event.payload),
            ),
        )

        stub.AddTestEvent(request)


def _get_test_events(
    test_id: str, address: str = DEFAULT_BACKEND_ADDRESS
) -> List[TestEvent]:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = backend_pb2_grpc.BackendStub(channel)
        request = backend_pb2.GetEventsRequest(id=test_id)

        response = stub.GetTestEvents(request)

        return [
            TestEvent(kind=event.kind, payload=pickle.loads(event.payload))  # nosec
            for event in response.events
        ]


def _add_user_results(
    user_manager_id: str, results: List[Result], address: str = DEFAULT_BACKEND_ADDRESS
):
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = backend_pb2_grpc.BackendStub(channel)
        request = backend_pb2.AddUserResultsRequest(
            userManagerID=user_manager_id,
            results=[pickle.dumps(result) for result in results],
        )

        stub.AddUserResults(request)


def _set_scenario_result(
    scenario_id: str,
    output: Any,
    exception: Any,
    logs: str,
    time_taken: float,
    succeeded: int,
    failed: int,
    address: str = DEFAULT_BACKEND_ADDRESS,
):
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = backend_pb2_grpc.BackendStub(channel)
        request = backend_pb2.SetScenarioResultRequest(
            scenarioID=scenario_id,
            output=wrappers_pb2.StringValue(value=json.dumps(output)),
            exception=wrappers_pb2.StringValue(
                value=json.dumps(str(exception) if exception is not None else None)
            ),
            logs=logs,
            timeTaken=time_taken,
            succeeded=succeeded,
            failed=failed,
        )

        stub.SetScenarioResult(request)


def _move_user_results(
    scenario_id: str,
    limit: int = 500,
    address: str = DEFAULT_BACKEND_ADDRESS,
) -> List[Result]:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = backend_pb2_grpc.BackendStub(channel)
        request = backend_pb2.MoveUserResultsRequest(
            scenarioID=scenario_id, limit=limit
        )

        response = stub.MoveUserResults(request)

        return [pickle.loads(result) for result in response.results]  # nosec


def _move_scenario_result(
    scenario_id: str, address: str = DEFAULT_BACKEND_ADDRESS
) -> Optional[dict]:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        try:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.MoveScenarioResultRequest(
                scenarioID=scenario_id,
            )

            response = stub.MoveScenarioResult(request)

            return {
                "id": response.id,
                "output": json.loads(response.output.value),
                "exception": json.loads(response.exception.value),
                "logs": response.logs,
                "timestamp": response.timestamp,
                "time_taken": response.timeTaken,
                "succeeded": response.succeeded,
                "failed": response.failed,
            }
        except grpc.RpcError as err:
            if err.code() == grpc.StatusCode.NOT_FOUND:
                return None
            else:
                raise err


def _distribute_work(
    scenario_id: str, amount: int, address: str = DEFAULT_BACKEND_ADDRESS
):
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = backend_pb2_grpc.BackendStub(channel)
        request = backend_pb2.DistributeWorkRequest(
            scenarioID=scenario_id, amount=amount
        )

        stub.DistributeWork(request)


def _get_user_work(user_manager_id: str, address: str = DEFAULT_BACKEND_ADDRESS) -> int:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = backend_pb2_grpc.BackendStub(channel)
        request = backend_pb2.GetUserWorkRequest(userManagerID=user_manager_id)

        response = stub.GetUserWork(request)

        return response.work


def _add_user_event(
    scenario_id: str,
    kind: str,
    payload: dict,
    address: str = DEFAULT_BACKEND_ADDRESS,
):
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = backend_pb2_grpc.BackendStub(channel)
        request = backend_pb2.AddEventRequest(
            id=scenario_id,
            event=backend_pb2.Event(
                kind=kind,
                payload=json.dumps(payload).encode("utf-8"),
            ),
        )

        stub.AddUserEvent(request)


def _get_user_events(
    user_manager_id: str, kind: str, address: str = DEFAULT_BACKEND_ADDRESS
):
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = backend_pb2_grpc.BackendStub(channel)
        request = backend_pb2.GetEventsRequest(id=user_manager_id, kind=kind)

        response = stub.GetUserEvents(request)

        return [
            UserEvent(
                kind=event.kind, payload=json.loads(event.payload.decode("utf-8"))
            )
            for event in response.events
        ]


def _add_metric(
    scenario_id: str,
    name: str,
    value: float,
    address: str = DEFAULT_BACKEND_ADDRESS,
):
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = backend_pb2_grpc.BackendStub(channel)
        request = backend_pb2.AddMetricRequest(
            scenarioID=scenario_id,
            name=name,
            value=value,
        )

        stub.AddMetric(request)


def _get_metric_total(
    scenario_id: str,
    name: str,
    address: str = DEFAULT_BACKEND_ADDRESS,
) -> Optional[float]:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        try:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.GetMetricRequest(
                scenarioID=scenario_id,
                name=name,
            )

            response = stub.GetMetricTotal(request)

            return response.total
        except grpc.RpcError as err:
            if err.code() == grpc.StatusCode.NOT_FOUND:
                return None
            else:
                raise err


def _get_last_metric(
    scenario_id: str,
    name: str,
    address: str = DEFAULT_BACKEND_ADDRESS,
) -> Optional[float]:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        try:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.GetMetricRequest(
                scenarioID=scenario_id,
                name=name,
            )

            response = stub.GetLastMetric(request)

            return response.last
        except grpc.RpcError as err:
            if err.code() == grpc.StatusCode.NOT_FOUND:
                return None
            else:
                raise err


def _get_metric_rate(
    scenario_id: str,
    name: str,
    split_point: float,
    address: str = DEFAULT_BACKEND_ADDRESS,
) -> Optional[float]:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        try:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.GetMetricRateRequest(
                scenarioID=scenario_id,
                name=name,
                splitPoint=split_point,
            )

            response = stub.GetMetricRate(request)

            return response.percentage
        except grpc.RpcError as err:
            if err.code() == grpc.StatusCode.NOT_FOUND:
                return None
            else:
                raise err


def _get_metric_statistics(
    scenario_id: str,
    name: str,
    address: str = DEFAULT_BACKEND_ADDRESS,
) -> Optional[dict]:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        try:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.GetMetricRequest(
                scenarioID=scenario_id,
                name=name,
            )

            response = stub.GetMetricStatistics(request)

            # FEATURE: type for metric statistics
            return {
                "min": response.min,
                "max": response.max,
                "median": response.median,
                "average": response.average,
                "len": response.len,
            }
        except grpc.RpcError as err:
            if err.code() == grpc.StatusCode.NOT_FOUND:
                return None
            else:
                raise err
