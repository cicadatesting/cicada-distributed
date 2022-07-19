from typing import Any, Callable, Dict, List, Optional
import time
import pickle  # nosec
import json
import random
from distributed.client import Future  # type: ignore

import grpc  # type: ignore

from google.protobuf import wrappers_pb2

from cicadad.core.types import (
    IBackendAPI,
    IBackendBuilder,
    ICLIBackend,
    IConsoleMetricsBackend,
    IScenarioBackend,
    ITestBackend,
    IUserBackend,
    IUserBufferActor,
    IUserManagerBackend,
    Result,
    ScenarioMetric,
    TestEvent,
    TestStatus,
    UserEvent,
)
from cicadad.protos import backend_pb2, backend_pb2_grpc
from cicadad.util.constants import DEFAULT_BACKEND_ADDRESS, ONE_SEC_MS


class CLIBackend(ICLIBackend):
    def __init__(self, backend_api: IBackendAPI) -> None:
        self.__backend_api = backend_api

    def create_test(
        self,
        scheduling_metadata: str,
        backend_address: str,
        tags: List[str],
        env: Dict[str, str],
    ) -> str:
        # NOTE: backend address in instance may be different from outside instance on CLI
        return self.__backend_api.create_test(
            scheduling_metadata, tags, env, backend_address
        )

    def get_test_events(self, test_id: str) -> List[TestEvent]:
        return self.__backend_api.get_test_events(test_id)

    def clean_test_instances(self, test_id: str):
        self.__backend_api.clean_test_instances(test_id)


class UserBufferActor(IUserBufferActor):
    """Actor to buffer work and events for users."""

    def __init__(
        self,
        user_manager_id: str,
        backend_address: str,
        backend_api_maker: Callable[[str], IBackendAPI],
    ):
        self.__user_manager_id = user_manager_id
        self.__backend_api = backend_api_maker(backend_address)

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
            user_manager_events = self.__backend_api.get_user_events(
                self.__user_manager_id, kind
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
            user_manager_work = self.__backend_api.get_user_work(self.__user_manager_id)

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
        self.__backend_api.add_user_results(self.__user_manager_id, self.__results)

        self.__results = []


class UserBackend(IUserBackend):
    def __init__(self, user_id: str, buffer: IUserBufferActor):
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
    def __init__(
        self, user_manager_id: str, buffer: IUserBufferActor, backend_api: IBackendAPI
    ):
        self.__user_manager_id = user_manager_id
        self.__buffer = buffer
        self.__backend_api = backend_api

    def get_new_users(self) -> List[str]:
        events = self.__backend_api.get_user_events(
            self.__user_manager_id, "START_USERS"
        )

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
    def __init__(
        self, test_id: str, scenario_id: str, backend_api: IBackendAPI
    ) -> None:
        self.__test_id = test_id
        self.__scenario_id = scenario_id
        self.__backend_api = backend_api

    def create_users(self, amount: int) -> List[str]:
        return self.__backend_api.create_users(
            self.__test_id, self.__scenario_id, amount
        )

    def stop_users(self, amount: int):
        self.__backend_api.stop_users(self.__scenario_id, amount)

    def distribute_work(self, n: int):
        self.__backend_api.distribute_work(scenario_id=self.__scenario_id, amount=n)

    def send_user_events(self, kind: str, payload: dict):
        self.__backend_api.add_user_event(
            scenario_id=self.__scenario_id, kind=kind, payload=payload
        )

    def move_user_results(
        self, limit: int, timeout_ms: Optional[int] = ONE_SEC_MS
    ) -> List[Result]:
        # Wait timeout_ms and get results again if no results
        results = self.__backend_api.move_user_results(
            scenario_id=self.__scenario_id, limit=limit
        )

        if results == [] and timeout_ms is not None:
            time.sleep(timeout_ms / ONE_SEC_MS)
            results = self.__backend_api.move_user_results(
                scenario_id=self.__scenario_id, limit=limit
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
        self.__backend_api.set_scenario_result(
            scenario_id=self.__scenario_id,
            output=output,
            exception=exception,
            logs=logs,
            time_taken=time_taken,
            succeeded=succeeded,
            failed=failed,
        )

    def add_metric(self, name: str, value: float):
        self.__backend_api.add_metric(
            scenario_id=self.__scenario_id, name=name, value=value
        )


class ConsoleMetricsBackend(IConsoleMetricsBackend):
    def __init__(self, backend_api: IBackendAPI) -> None:
        self.__backend_api = backend_api

    def get_metric_statistics(self, scenario_id: str, name: str) -> Optional[dict]:
        return self.__backend_api.get_metric_statistics(scenario_id, name)

    def get_metric_total(self, scenario_id: str, name: str) -> Optional[float]:
        return self.__backend_api.get_metric_total(scenario_id, name)

    def get_last_metric(self, scenario_id: str, name: str) -> Optional[float]:
        return self.__backend_api.get_last_metric(scenario_id, name)

    def get_metric_rate(
        self, scenario_id: str, name: str, split_point: float
    ) -> Optional[float]:
        return self.__backend_api.get_metric_rate(scenario_id, name, split_point)


class TestBackend(ITestBackend):
    def __init__(self, test_id: str, backend_api: IBackendAPI) -> None:
        self.__test_id = test_id
        self.__backend_api = backend_api

    def create_scenario(
        self,
        scenario_name: str,
        context: str,
        users_per_instance: int,
        tags: List[str],
    ) -> str:
        return self.__backend_api.create_scenario(
            self.__test_id,
            scenario_name,
            context,
            users_per_instance,
            tags,
        )

    def add_test_event(self, event: TestEvent):
        self.__backend_api.add_test_event(self.__test_id, event)

    def move_scenario_result(self, scenario_id: str) -> Optional[dict]:
        return self.__backend_api.move_scenario_result(scenario_id)

    def get_console_metrics_backend(self) -> IConsoleMetricsBackend:
        return ConsoleMetricsBackend(self.__backend_api)

    def scenario_running(self, scenario_id: str) -> bool:
        return self.__backend_api.check_test_instance(self.__test_id, scenario_id)


class BackendBuilder(IBackendBuilder):
    def __init__(self) -> None:
        super().__init__()

    def make_backend_api(self, address: str) -> IBackendAPI:
        return DefaultBackendAPI(address)

    def make_test_backend(self, test_id: str, address: str) -> ITestBackend:
        backend_api = self.make_backend_api(address)

        return TestBackend(test_id, backend_api)

    def make_scenario_backend(
        self, test_id: str, scenario_id: str, address: str
    ) -> IScenarioBackend:
        backend_api = self.make_backend_api(address)

        return ScenarioBackend(test_id, scenario_id, backend_api)

    def get_backend_api_maker(self) -> Callable[[str], IBackendAPI]:
        return lambda address: self.make_backend_api(address)

    def make_user_manager_backend(
        self, user_manager_id: str, buffer: IUserBufferActor, address: str
    ) -> IUserManagerBackend:
        backend_api = self.make_backend_api(address)

        return UserManagerBackend(user_manager_id, buffer, backend_api)


class DefaultBackendAPI(IBackendAPI):
    def __init__(
        self,
        backend_address: str = DEFAULT_BACKEND_ADDRESS,
        use_ssl=False,
        use_gzip=True,
    ) -> None:
        self.__backend_address = backend_address
        self.__use_ssl = use_ssl
        self.__use_gzip = use_gzip

    def __get_channel(self) -> grpc.Channel:
        if self.__use_gzip:
            compression = grpc.Compression.Gzip
        else:
            compression = grpc.Compression.NoCompression

        if self.__use_ssl:
            credentials = grpc.ssl_channel_credentials()

            return grpc.secure_channel(
                self.__backend_address, credentials=credentials, compression=compression
            )
        else:
            return grpc.insecure_channel(
                self.__backend_address, compression=compression
            )

    def create_test(
        self,
        scheduling_metadata: str,
        tags: List[str],
        env: Dict[str, str],
        backend_address: str,
    ) -> str:
        with self.__get_channel() as channel:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.CreateTestRequest(
                backendAddress=backend_address,
                schedulingMetadata=scheduling_metadata,
                tags=tags,
                env=env,
            )

            response = stub.CreateTest(request)

            return response.testID

    def create_scenario(
        self,
        test_id: str,
        scenario_name: str,
        context: str,
        users_per_instance: int,
        tags: List[str],
    ) -> str:
        with self.__get_channel() as channel:
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

    def create_users(self, test_id: str, scenario_id: str, amount: int) -> List[str]:
        with self.__get_channel() as channel:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.CreateUsersRequest(
                testID=test_id, scenarioID=scenario_id, amount=amount
            )

            response = stub.CreateUsers(request)

            return response.userManagerIDs

    def stop_users(self, scenario_id: str, amount: int):
        with self.__get_channel() as channel:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.StopUsersRequest(
                scenarioID=scenario_id, amount=amount
            )

            stub.StopUsers(request)

    def clean_test_instances(self, test_id: str):
        with self.__get_channel() as channel:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.CleanTestInstancesRequest(testID=test_id)

            stub.CleanTestInstances(request)

    def check_test_instance(self, test_id: str, instance_id: str):
        with self.__get_channel() as channel:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.CheckTestInstanceRequest(
                testID=test_id, instanceID=instance_id
            )

            response = stub.CheckTestInstance(request)

            return response.running

    def add_test_event(self, test_id: str, event: TestEvent):
        with self.__get_channel() as channel:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.AddEventRequest(
                id=test_id,
                event=backend_pb2.Event(
                    kind=event.kind,
                    payload=event.payload.json().encode("utf-8"),
                ),
            )

            stub.AddTestEvent(request)

    def _load_test_event(self, event: Any):
        if event.kind == "SCENARIO_METRIC":
            return TestEvent(
                kind=event.kind, payload=ScenarioMetric.parse_raw(event.payload)
            )
        else:
            return TestEvent(
                kind=event.kind, payload=TestStatus.parse_raw(event.payload)
            )

    def get_test_events(self, test_id: str) -> List[TestEvent]:
        with self.__get_channel() as channel:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.GetEventsRequest(id=test_id)

            response = stub.GetTestEvents(request)

            return [self._load_test_event(event) for event in response.events]

    def add_user_results(
        self,
        user_manager_id: str,
        results: List[Result],
    ):
        with self.__get_channel() as channel:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.AddUserResultsRequest(
                userManagerID=user_manager_id,
                results=[pickle.dumps(result) for result in results],
            )

            stub.AddUserResults(request)

    def set_scenario_result(
        self,
        scenario_id: str,
        output: Any,
        exception: Any,
        logs: str,
        time_taken: float,
        succeeded: int,
        failed: int,
    ):
        with self.__get_channel() as channel:
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

    def move_user_results(
        self,
        scenario_id: str,
        limit: int = 500,
    ) -> List[Result]:
        with self.__get_channel() as channel:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.MoveUserResultsRequest(
                scenarioID=scenario_id, limit=limit
            )

            response = stub.MoveUserResults(request)

            return [pickle.loads(result) for result in response.results]  # nosec

    def move_scenario_result(self, scenario_id: str) -> Optional[dict]:
        with self.__get_channel() as channel:
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

    def distribute_work(self, scenario_id: str, amount: int):
        with self.__get_channel() as channel:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.DistributeWorkRequest(
                scenarioID=scenario_id, amount=amount
            )

            stub.DistributeWork(request)

    def get_user_work(self, user_manager_id: str) -> int:
        with self.__get_channel() as channel:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.GetUserWorkRequest(userManagerID=user_manager_id)

            response = stub.GetUserWork(request)

            return response.work

    def add_user_event(self, scenario_id: str, kind: str, payload: dict):
        with self.__get_channel() as channel:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.AddEventRequest(
                id=scenario_id,
                event=backend_pb2.Event(
                    kind=kind,
                    payload=json.dumps(payload).encode("utf-8"),
                ),
            )

            stub.AddUserEvent(request)

    def get_user_events(self, user_manager_id: str, kind: str):
        with self.__get_channel() as channel:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.GetEventsRequest(id=user_manager_id, kind=kind)

            response = stub.GetUserEvents(request)

            return [
                UserEvent(
                    kind=event.kind, payload=json.loads(event.payload.decode("utf-8"))
                )
                for event in response.events
            ]

    def add_metric(self, scenario_id: str, name: str, value: float):
        with self.__get_channel() as channel:
            stub = backend_pb2_grpc.BackendStub(channel)
            request = backend_pb2.AddMetricRequest(
                scenarioID=scenario_id,
                name=name,
                value=value,
            )

            stub.AddMetric(request)

    def get_metric_total(self, scenario_id: str, name: str) -> Optional[float]:
        with self.__get_channel() as channel:
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

    def get_last_metric(self, scenario_id: str, name: str) -> Optional[float]:
        with self.__get_channel() as channel:
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

    def get_metric_rate(
        self, scenario_id: str, name: str, split_point: float
    ) -> Optional[float]:
        with self.__get_channel() as channel:
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

    def get_metric_statistics(self, scenario_id: str, name: str) -> Optional[dict]:
        with self.__get_channel() as channel:
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
