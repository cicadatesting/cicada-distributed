from google.protobuf import wrappers_pb2
import grpc

from cicadad.core.containers import DockerServerArgs
from cicadad.protos import container_service_pb2, container_service_pb2_grpc
from cicadad.util.constants import DEFAULT_CONTAINER_SERVICE_ADDRESS


# message StartContainerRequest {
#     string image = 1;
#     string name = 2;
#     repeated string command = 3;
#     repeated string labels = 4;
#     map<string, string> env = 5;
#     repeated DockerVolume volumes = 6;
#     google.protobuf.Int32Value hostPort = 7;
#     google.protobuf.Int32Value containerPort = 8;
#     google.protobuf.StringValue network = 9;
#     google.protobuf.BoolValue createNetwork = 10;
# }


def start_container(
    args: DockerServerArgs,
    address: str = DEFAULT_CONTAINER_SERVICE_ADDRESS,
):
    with grpc.insecure_channel(address) as channel:
        stub = container_service_pb2_grpc.ContainerServiceStub(channel)
        request = container_service_pb2.StartContainerRequest(
            image=args.image,
            name=args.name,
            command=args.command,
            labels=args.labels,
            env=args.env,
            volumes=[]
            if args.volumes is None
            else [
                container_service_pb2.DockerVolume(
                    source=vol.source, destination=vol.destination
                )
                for vol in args.volumes
            ],
            hostPort=wrappers_pb2.Int32Value(value=args.host_port),
            containerPort=wrappers_pb2.Int32Value(value=args.container_port),
            network=wrappers_pb2.StringValue(value=args.network),
            createNetwork=wrappers_pb2.BoolValue(value=args.create_network),
        )

        stub.StartContainer(request)


def stop_container(
    container_id: str,
    address: str = DEFAULT_CONTAINER_SERVICE_ADDRESS,
):
    with grpc.insecure_channel(address) as channel:
        stub = container_service_pb2_grpc.ContainerServiceStub(channel)
        request = container_service_pb2.StopContainerRequest(containerID=container_id)

        stub.StopContainer(request)
