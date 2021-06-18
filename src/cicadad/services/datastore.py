from typing import Any, Iterable, List, Optional
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


def add_user_result(
    user_id: str, result: Result, address: str = DEFAULT_DATASTORE_ADDRESS
):
    with grpc.insecure_channel(address) as channel:
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
    address: str = DEFAULT_DATASTORE_ADDRESS,
):
    with grpc.insecure_channel(address) as channel:
        stub = datastore_pb2_grpc.DatastoreStub(channel)
        request = datastore_pb2.SetScenarioResultRequest(
            scenarioID=scenario_id,
            output=wrappers_pb2.StringValue(value=json.dumps(output)),
            exception=wrappers_pb2.StringValue(
                value=json.dumps(str(exception) if exception is not None else None)
            ),
            logs=logs,
            timeTaken=time_taken,
        )

        stub.SetScenarioResult(request)


def move_user_results(
    user_ids: Iterable[str], address: str = DEFAULT_DATASTORE_ADDRESS
) -> List[Result]:
    with grpc.insecure_channel(address) as channel:
        stub = datastore_pb2_grpc.DatastoreStub(channel)
        request = datastore_pb2.MoveUserResultsRequest(userIDs=user_ids)

        response = stub.MoveUserResults(request)

        return [pickle.loads(result) for result in response.results]  # nosec


def move_scenario_result(
    scenario_id: str, address: str = DEFAULT_DATASTORE_ADDRESS
) -> Optional[dict]:
    with grpc.insecure_channel(address) as channel:
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
            }
        except grpc.RpcError as err:
            if err.code() == grpc.StatusCode.NOT_FOUND:
                return None
            else:
                raise err


def distribute_work(
    work: int, user_ids: List[str], address: str = DEFAULT_DATASTORE_ADDRESS
):
    with grpc.insecure_channel(address) as channel:
        stub = datastore_pb2_grpc.DatastoreStub(channel)
        request = datastore_pb2.DistributeWorkRequest(work=work, userIDs=user_ids)

        stub.DistributeWork(request)


def get_work(user_id: str, address: str = DEFAULT_DATASTORE_ADDRESS) -> int:
    with grpc.insecure_channel(address) as channel:
        stub = datastore_pb2_grpc.DatastoreStub(channel)
        request = datastore_pb2.GetUserWorkRequest(userID=user_id)

        response = stub.GetUserWork(request)

        return response.work


# def get_session(host: str = "0.0.0.0", password: str = "cassandra"):
#     cluster = create_datastore_cluster(host, password)

#     return cluster.connect()


# def setup_datastore(session: Session):
#     create_cicada_keyspace(session)

#     # NOTE: idk if this should be more configurable
#     session.set_keyspace("cicada")

#     create_user_results_table(session)
#     create_scenario_results_table(session)

#     return session


# def create_datastore_cluster(host: str, password: str):
#     # FEATURE: generate password for service creation
#     auth_provider = PlainTextAuthProvider(
#         username="cassandra",
#         password=password,
#     )

#     return Cluster([host], port=9042, auth_provider=auth_provider)


# def create_cicada_keyspace(session: Session):
#     return session.execute(
#         """
#         CREATE KEYSPACE IF NOT EXISTS cicada
#         WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 3 }
#         """,
#     )


# def create_user_results_table(session: Session):
#     return session.execute(
#         """
#         CREATE TABLE IF NOT EXISTS user_results
#         (
#             id UUID,
#             name TEXT,
#             output BLOB,
#             exception BLOB,
#             logs TEXT,
#             timestamp TIMESTAMP,
#             PRIMARY KEY (name, id)
#         )
#         """
#     )


# def create_scenario_results_table(session: Session):
#     return session.execute(
#         """
#         CREATE TABLE IF NOT EXISTS scenario_results
#         (
#             name TEXT PRIMARY KEY,
#             output BLOB,
#             exception BLOB,
#             logs TEXT,
#             timestamp TIMESTAMP
#         )
#         """
#     )


# def put_user_result(session: Session, name: str, result: Result):
#     return session.execute(
#         "INSERT INTO user_results (id, name, output, exception, logs, timestamp) VALUES (%s, %s, %s, %s, %s, %s)",
#         (
#             uuid.UUID(result.id),
#             name,
#             pickle.dumps(result.output),
#             pickle.dumps(result.exception),
#             result.logs,
#             result.timestamp,
#         ),
#     )


# def get_user_results(session: Session, name: str):
#     # NOTE: may be more performant to create a table for each set of user results
#     rows = session.execute(
#         """
#         SELECT * FROM user_results
#         WHERE name=%s
#         ALLOW FILTERING
#         """,
#         (name,),
#     ).all()

#     return [
#         Result(
#             id=str(row.id),
#             output=pickle.loads(row.output),
#             exception=pickle.loads(row.exception),
#             timestamp=row.timestamp,
#         )
#         for row in rows
#     ]


# def clear_user_results(session: Session, name: str):
#     return session.execute(
#         """
#         DELETE FROM user_results WHERE name=%s
#         """,
#         (name,),
#     )


# def put_scenario_result(session: Session, name: str, result: Result):
#     return session.execute(
#         "INSERT INTO scenario_results (name, output, exception, logs, timestamp) VALUES (%s, %s, %s, %s, %s)",
#         (
#             name,
#             pickle.dumps(result.output),
#             pickle.dumps(result.exception),
#             result.logs,
#             result.timestamp,
#         ),
#     )


# def get_scenario_result(session: Session, name: str):
#     row = session.execute(
#         "SELECT * FROM scenario_results WHERE name=%s ALLOW FILTERING", (name,)
#     ).one()

#     # HACK: will need to seperate pickling/unpickling from DB call if using
#     # API to consolidate shared logic
#     return Result(
#         output=pickle.loads(row.output),
#         exception=pickle.loads(row.exception),
#         timestamp=row.timestamp,
#     )


# def clear_scenario_results(session: Session, name: str):
#     return session.execute(
#         """
#         DELETE FROM scenario_results WHERE name=%s
#         """,
#         (name,),
#     )
