# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from cicadad.protos import hub_pb2 as cicadad_dot_protos_dot_hub__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


class HubStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Run = channel.unary_stream(
                '/cicada_distributed.Hub/Run',
                request_serializer=cicadad_dot_protos_dot_hub__pb2.RunTestRequest.SerializeToString,
                response_deserializer=cicadad_dot_protos_dot_hub__pb2.TestStatus.FromString,
                )
        self.Healthcheck = channel.unary_unary(
                '/cicada_distributed.Hub/Healthcheck',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=cicadad_dot_protos_dot_hub__pb2.HealthcheckReply.FromString,
                )


class HubServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Run(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Healthcheck(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_HubServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Run': grpc.unary_stream_rpc_method_handler(
                    servicer.Run,
                    request_deserializer=cicadad_dot_protos_dot_hub__pb2.RunTestRequest.FromString,
                    response_serializer=cicadad_dot_protos_dot_hub__pb2.TestStatus.SerializeToString,
            ),
            'Healthcheck': grpc.unary_unary_rpc_method_handler(
                    servicer.Healthcheck,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=cicadad_dot_protos_dot_hub__pb2.HealthcheckReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'cicada_distributed.Hub', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Hub(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Run(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(request, target, '/cicada_distributed.Hub/Run',
            cicadad_dot_protos_dot_hub__pb2.RunTestRequest.SerializeToString,
            cicadad_dot_protos_dot_hub__pb2.TestStatus.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Healthcheck(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/cicada_distributed.Hub/Healthcheck',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            cicadad_dot_protos_dot_hub__pb2.HealthcheckReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
