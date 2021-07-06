from typing import Dict, List, Optional
from google.protobuf import wrappers_pb2
from pydantic.main import BaseModel  # type: ignore
import grpc  # type: ignore

from cicadad.protos import container_service_pb2, container_service_pb2_grpc
from cicadad.util.constants import DEFAULT_CONTAINER_SERVICE_ADDRESS


class StartContainerArgs(BaseModel):
    name: str
    env: Dict[str, str] = {}
    labels: Dict[str, str] = {}
    image: str
    command: List[str] = []


class StartDockerContainerArgs(StartContainerArgs):
    network: str


class StartKubeContainerArgs(StartContainerArgs):
    namespace: str


def start_docker_container(
    args: StartDockerContainerArgs,
    address: str = DEFAULT_CONTAINER_SERVICE_ADDRESS,
):
    with grpc.insecure_channel(address) as channel:
        stub = container_service_pb2_grpc.ContainerServiceStub(channel)
        request = container_service_pb2.StartContainerRequest(
            name=args.name,
            dockerArgs=container_service_pb2.DockerArgs(labels=args.labels),
            dockerContainerArgs=container_service_pb2.DockerContainerArgs(
                image=args.image,
                command=args.command,
                env=args.env,
                network=wrappers_pb2.StringValue(value=args.network),
            ),
        )

        stub.StartContainer(request)


def start_kube_container(
    args: StartKubeContainerArgs,
    address: str = DEFAULT_CONTAINER_SERVICE_ADDRESS,
):
    with grpc.insecure_channel(address) as channel:
        stub = container_service_pb2_grpc.ContainerServiceStub(channel)
        request = container_service_pb2.StartContainerRequest(
            name=args.name,
            kubeArgs=container_service_pb2.KubeArgs(
                labels=args.labels,
                namespace=args.namespace,
            ),
            kubeContainerArgs=container_service_pb2.KubeContainerArgs(
                image=args.image,
                command=args.command,
                env=args.env,
            ),
        )

        stub.StartContainer(request)


def stop_docker_container(
    name: str,
    labels: Dict[str, str] = {},
    address: str = DEFAULT_CONTAINER_SERVICE_ADDRESS,
):

    with grpc.insecure_channel(address) as channel:
        stub = container_service_pb2_grpc.ContainerServiceStub(channel)
        request = container_service_pb2.StopContainerRequest(
            name=name,
            dockerArgs=container_service_pb2.DockerArgs(
                labels=labels,
            ),
        )

        stub.StopContainer(request)


def stop_kube_container(
    name: str,
    labels: Dict[str, str] = {},
    namespace: Optional[str] = None,
    address: str = DEFAULT_CONTAINER_SERVICE_ADDRESS,
):
    # FIXME: make stop container and stop multiple containers seperate methods
    with grpc.insecure_channel(address) as channel:
        stub = container_service_pb2_grpc.ContainerServiceStub(channel)
        request = container_service_pb2.StopContainerRequest(
            name=name,
            kubeArgs=container_service_pb2.KubeArgs(
                labels=labels,
                namespace=namespace,
            ),
        )

        stub.StopContainer(request)
