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
            labels=args.labels,
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
            labels=args.labels,
            namespace=args.namespace,
            kubeContainerArgs=container_service_pb2.KubeContainerArgs(
                image=args.image,
                command=args.command,
                env=args.env,
            ),
        )

        stub.StartContainer(request)


def stop_docker_container(
    name: str,
    address: str = DEFAULT_CONTAINER_SERVICE_ADDRESS,
):

    with grpc.insecure_channel(address) as channel:
        stub = container_service_pb2_grpc.ContainerServiceStub(channel)
        request = container_service_pb2.StopContainerRequest(name=name)

        stub.StopContainer(request)


def stop_docker_containers(
    labels: Dict[str, str],
    address: str = DEFAULT_CONTAINER_SERVICE_ADDRESS,
):

    with grpc.insecure_channel(address) as channel:
        stub = container_service_pb2_grpc.ContainerServiceStub(channel)
        request = container_service_pb2.StopContainersRequest(labels=labels)

        stub.StopContainers(request)


def stop_kube_container(
    name: str,
    namespace: Optional[str] = None,
    address: str = DEFAULT_CONTAINER_SERVICE_ADDRESS,
):
    with grpc.insecure_channel(address) as channel:
        stub = container_service_pb2_grpc.ContainerServiceStub(channel)
        request = container_service_pb2.StopContainerRequest(
            name=name,
            namespace=namespace,
        )

        stub.StopContainer(request)


def stop_kube_containers(
    labels: Dict[str, str],
    namespace: Optional[str] = None,
    address: str = DEFAULT_CONTAINER_SERVICE_ADDRESS,
):
    with grpc.insecure_channel(address) as channel:
        stub = container_service_pb2_grpc.ContainerServiceStub(channel)
        request = container_service_pb2.StopContainersRequest(
            labels=labels,
            namespace=namespace,
        )

        stub.StopContainers(request)


def docker_container_is_running(
    name: str, address: str = DEFAULT_CONTAINER_SERVICE_ADDRESS
) -> bool:
    with grpc.insecure_channel(address) as channel:
        stub = container_service_pb2_grpc.ContainerServiceStub(channel)
        request = container_service_pb2.DescribeContainerRequest(name=name)

        response = stub.ContainerRunning(request)

        return response.running


def kube_container_is_running(
    name: str, namespace: str, address: str = DEFAULT_CONTAINER_SERVICE_ADDRESS
) -> bool:
    with grpc.insecure_channel(address) as channel:
        stub = container_service_pb2_grpc.ContainerServiceStub(channel)
        request = container_service_pb2.DescribeContainerRequest(
            name=name, namespace=namespace
        )

        response = stub.ContainerRunning(request)

        return response.running
