# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from cicadad.protos import container_service_pb2 as cicadad_dot_protos_dot_container__service__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


class ContainerServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.StartContainer = channel.unary_unary(
                '/container_service.ContainerService/StartContainer',
                request_serializer=cicadad_dot_protos_dot_container__service__pb2.StartContainerRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.StopContainer = channel.unary_unary(
                '/container_service.ContainerService/StopContainer',
                request_serializer=cicadad_dot_protos_dot_container__service__pb2.StopContainerRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )


class ContainerServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def StartContainer(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def StopContainer(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ContainerServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'StartContainer': grpc.unary_unary_rpc_method_handler(
                    servicer.StartContainer,
                    request_deserializer=cicadad_dot_protos_dot_container__service__pb2.StartContainerRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'StopContainer': grpc.unary_unary_rpc_method_handler(
                    servicer.StopContainer,
                    request_deserializer=cicadad_dot_protos_dot_container__service__pb2.StopContainerRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'container_service.ContainerService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class ContainerService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def StartContainer(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/container_service.ContainerService/StartContainer',
            cicadad_dot_protos_dot_container__service__pb2.StartContainerRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def StopContainer(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/container_service.ContainerService/StopContainer',
            cicadad_dot_protos_dot_container__service__pb2.StopContainerRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
