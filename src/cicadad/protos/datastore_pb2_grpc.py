# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from cicadad.protos import datastore_pb2 as cicadad_dot_protos_dot_datastore__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


class DatastoreStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.AddUserResult = channel.unary_unary(
                '/datastore.Datastore/AddUserResult',
                request_serializer=cicadad_dot_protos_dot_datastore__pb2.AddUserResultRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.SetScenarioResult = channel.unary_unary(
                '/datastore.Datastore/SetScenarioResult',
                request_serializer=cicadad_dot_protos_dot_datastore__pb2.SetScenarioResultRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.MoveUserResults = channel.unary_unary(
                '/datastore.Datastore/MoveUserResults',
                request_serializer=cicadad_dot_protos_dot_datastore__pb2.MoveUserResultsRequest.SerializeToString,
                response_deserializer=cicadad_dot_protos_dot_datastore__pb2.MoveUserResultsResponse.FromString,
                )
        self.MoveScenarioResult = channel.unary_unary(
                '/datastore.Datastore/MoveScenarioResult',
                request_serializer=cicadad_dot_protos_dot_datastore__pb2.MoveScenarioResultRequest.SerializeToString,
                response_deserializer=cicadad_dot_protos_dot_datastore__pb2.MoveScenarioResultResponse.FromString,
                )
        self.DistributeWork = channel.unary_unary(
                '/datastore.Datastore/DistributeWork',
                request_serializer=cicadad_dot_protos_dot_datastore__pb2.DistributeWorkRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.GetUserWork = channel.unary_unary(
                '/datastore.Datastore/GetUserWork',
                request_serializer=cicadad_dot_protos_dot_datastore__pb2.GetUserWorkRequest.SerializeToString,
                response_deserializer=cicadad_dot_protos_dot_datastore__pb2.GetUserWorkResponse.FromString,
                )


class DatastoreServicer(object):
    """Missing associated documentation comment in .proto file."""

    def AddUserResult(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetScenarioResult(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def MoveUserResults(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def MoveScenarioResult(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DistributeWork(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetUserWork(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_DatastoreServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'AddUserResult': grpc.unary_unary_rpc_method_handler(
                    servicer.AddUserResult,
                    request_deserializer=cicadad_dot_protos_dot_datastore__pb2.AddUserResultRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'SetScenarioResult': grpc.unary_unary_rpc_method_handler(
                    servicer.SetScenarioResult,
                    request_deserializer=cicadad_dot_protos_dot_datastore__pb2.SetScenarioResultRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'MoveUserResults': grpc.unary_unary_rpc_method_handler(
                    servicer.MoveUserResults,
                    request_deserializer=cicadad_dot_protos_dot_datastore__pb2.MoveUserResultsRequest.FromString,
                    response_serializer=cicadad_dot_protos_dot_datastore__pb2.MoveUserResultsResponse.SerializeToString,
            ),
            'MoveScenarioResult': grpc.unary_unary_rpc_method_handler(
                    servicer.MoveScenarioResult,
                    request_deserializer=cicadad_dot_protos_dot_datastore__pb2.MoveScenarioResultRequest.FromString,
                    response_serializer=cicadad_dot_protos_dot_datastore__pb2.MoveScenarioResultResponse.SerializeToString,
            ),
            'DistributeWork': grpc.unary_unary_rpc_method_handler(
                    servicer.DistributeWork,
                    request_deserializer=cicadad_dot_protos_dot_datastore__pb2.DistributeWorkRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'GetUserWork': grpc.unary_unary_rpc_method_handler(
                    servicer.GetUserWork,
                    request_deserializer=cicadad_dot_protos_dot_datastore__pb2.GetUserWorkRequest.FromString,
                    response_serializer=cicadad_dot_protos_dot_datastore__pb2.GetUserWorkResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'datastore.Datastore', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Datastore(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def AddUserResult(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/datastore.Datastore/AddUserResult',
            cicadad_dot_protos_dot_datastore__pb2.AddUserResultRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SetScenarioResult(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/datastore.Datastore/SetScenarioResult',
            cicadad_dot_protos_dot_datastore__pb2.SetScenarioResultRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def MoveUserResults(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/datastore.Datastore/MoveUserResults',
            cicadad_dot_protos_dot_datastore__pb2.MoveUserResultsRequest.SerializeToString,
            cicadad_dot_protos_dot_datastore__pb2.MoveUserResultsResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def MoveScenarioResult(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/datastore.Datastore/MoveScenarioResult',
            cicadad_dot_protos_dot_datastore__pb2.MoveScenarioResultRequest.SerializeToString,
            cicadad_dot_protos_dot_datastore__pb2.MoveScenarioResultResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def DistributeWork(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/datastore.Datastore/DistributeWork',
            cicadad_dot_protos_dot_datastore__pb2.DistributeWorkRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetUserWork(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/datastore.Datastore/GetUserWork',
            cicadad_dot_protos_dot_datastore__pb2.GetUserWorkRequest.SerializeToString,
            cicadad_dot_protos_dot_datastore__pb2.GetUserWorkResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)