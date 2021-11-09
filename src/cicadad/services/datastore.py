from typing import Any, Dict, Iterable, List, Optional, Union
from datetime import datetime
import pickle  # nosec
import json

import grpc  # type: ignore

# from cassandra.cluster import Cluster, Session
# from cassandra.auth import PlainTextAuthProvider
from pydantic import BaseModel
from google.protobuf import wrappers_pb2

from cicadad.protos import datastore_pb2, datastore_pb2_grpc
from cicadad.util.constants import DEFAULT_DATASTORE_ADDRESS


class Result(BaseModel):
    id: Optional[str]
    output: Optional[Any]
    exception: Optional[Any]
    logs: Optional[str]
    timestamp: Optional[datetime]
    time_taken: Optional[int]

    class Config:
        json_encoders = {
            Exception: lambda e: str(e),
        }


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


def add_test_event(
    test_id: str,
    event: TestEvent,
    address: str = DEFAULT_DATASTORE_ADDRESS,
):
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = datastore_pb2_grpc.DatastoreStub(channel)
        request = datastore_pb2.AddEventRequest(
            id=test_id,
            event=datastore_pb2.Event(
                kind=event.kind,
                payload=pickle.dumps(event.payload),
            ),
        )

        stub.AddTestEvent(request)


def get_test_events(
    test_id: str, address: str = DEFAULT_DATASTORE_ADDRESS
) -> List[TestEvent]:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = datastore_pb2_grpc.DatastoreStub(channel)
        request = datastore_pb2.GetEventsRequest(id=test_id)

        response = stub.GetTestEvents(request)

        return [
            TestEvent(kind=event.kind, payload=pickle.loads(event.payload))  # nosec
            for event in response.events
        ]


def add_user_result(
    user_id: str, result: Result, address: str = DEFAULT_DATASTORE_ADDRESS
):
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = datastore_pb2_grpc.DatastoreStub(channel)
        request = datastore_pb2.AddUserResultRequest(
            userID=user_id, result=pickle.dumps(result)
        )

        stub.AddUserResult(request)


def set_scenario_result(
    scenario_id: str,
    output: Any,
    exception: Any,
    logs: str,
    time_taken: float,
    succeeded: int,
    failed: int,
    address: str = DEFAULT_DATASTORE_ADDRESS,
):
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = datastore_pb2_grpc.DatastoreStub(channel)
        request = datastore_pb2.SetScenarioResultRequest(
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
    user_ids: Iterable[str],
    limit: int = 500,
    address: str = DEFAULT_DATASTORE_ADDRESS,
) -> List[Result]:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = datastore_pb2_grpc.DatastoreStub(channel)
        request = datastore_pb2.MoveUserResultsRequest(userIDs=user_ids, limit=limit)

        response = stub.MoveUserResults(request)

        return [pickle.loads(result) for result in response.results]  # nosec


def move_scenario_result(
    scenario_id: str, address: str = DEFAULT_DATASTORE_ADDRESS
) -> Optional[dict]:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        try:
            stub = datastore_pb2_grpc.DatastoreStub(channel)
            request = datastore_pb2.MoveScenarioResultRequest(
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


def distribute_work(
    work: int, user_ids: List[str], address: str = DEFAULT_DATASTORE_ADDRESS
):
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = datastore_pb2_grpc.DatastoreStub(channel)
        request = datastore_pb2.DistributeWorkRequest(work=work, userIDs=user_ids)

        stub.DistributeWork(request)


def get_work(user_id: str, address: str = DEFAULT_DATASTORE_ADDRESS) -> int:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = datastore_pb2_grpc.DatastoreStub(channel)
        request = datastore_pb2.GetUserWorkRequest(userID=user_id)

        response = stub.GetUserWork(request)

        return response.work


def add_user_event(
    user_id: str,
    kind: str,
    payload: dict,
    address: str = DEFAULT_DATASTORE_ADDRESS,
):
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = datastore_pb2_grpc.DatastoreStub(channel)
        request = datastore_pb2.AddEventRequest(
            id=user_id,
            event=datastore_pb2.Event(
                kind=kind,
                payload=json.dumps(payload).encode("utf-8"),
            ),
        )

        stub.AddUserEvent(request)


class UserEvent(BaseModel):
    kind: str
    payload: dict


def get_user_events(user_id: str, kind: str, address: str = DEFAULT_DATASTORE_ADDRESS):
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = datastore_pb2_grpc.DatastoreStub(channel)
        request = datastore_pb2.GetEventsRequest(id=user_id, kind=kind)

        response = stub.GetUserEvents(request)

        return [
            UserEvent(
                kind=event.kind, payload=json.loads(event.payload.decode("utf-8"))
            )
            for event in response.events
        ]


# rpc GetMetricStatistics (GetMetricRequest) returns (MetricStatisticsResponse);

# message AddMetricRequest {
#     string scenarioID = 1;
#     string name = 2;
#     double value = 3;
# }


def add_metric(
    scenario_id: str,
    name: str,
    value: float,
    address: str = DEFAULT_DATASTORE_ADDRESS,
):
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        stub = datastore_pb2_grpc.DatastoreStub(channel)
        request = datastore_pb2.AddMetricRequest(
            scenarioID=scenario_id,
            name=name,
            value=value,
        )

        stub.AddMetric(request)


def get_metric_total(
    scenario_id: str,
    name: str,
    address: str = DEFAULT_DATASTORE_ADDRESS,
) -> Optional[float]:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        try:
            stub = datastore_pb2_grpc.DatastoreStub(channel)
            request = datastore_pb2.GetMetricRequest(
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


def get_last_metric(
    scenario_id: str,
    name: str,
    address: str = DEFAULT_DATASTORE_ADDRESS,
) -> Optional[float]:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        try:
            stub = datastore_pb2_grpc.DatastoreStub(channel)
            request = datastore_pb2.GetMetricRequest(
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
    scenario_id: str,
    name: str,
    split_point: float,
    address: str = DEFAULT_DATASTORE_ADDRESS,
) -> Optional[float]:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        try:
            stub = datastore_pb2_grpc.DatastoreStub(channel)
            request = datastore_pb2.GetMetricRateRequest(
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


def get_metric_statistics(
    scenario_id: str,
    name: str,
    address: str = DEFAULT_DATASTORE_ADDRESS,
) -> Optional[dict]:
    with grpc.insecure_channel(address, compression=grpc.Compression.Gzip) as channel:
        try:
            stub = datastore_pb2_grpc.DatastoreStub(channel)
            request = datastore_pb2.GetMetricRequest(
                scenarioID=scenario_id,
                name=name,
            )

            response = stub.GetMetricStatistics(request)

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
