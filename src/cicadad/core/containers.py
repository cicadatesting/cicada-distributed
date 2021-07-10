from typing import Any, Dict, List, Optional
import os
import uuid
import socket

from pydantic import BaseModel
from docker.errors import APIError, NotFound  # type: ignore
import docker  # type: ignore

from cicadad.util.constants import (
    CICADA_VERSION,
    DEFAULT_DOCKER_NETWORK,
    DOCKER_CONTAINER_MODE,
)
from cicadad import configs as configs_module
from cicadad import templates as templates_module


class Volume(BaseModel):
    source: str
    destination: str


class DockerServerArgs(BaseModel):
    docker_client_args: dict = {}
    image: str
    name: Optional[str]
    command: Optional[List[str]]
    container_id: Optional[str]
    labels: List[str] = []
    env: Dict[str, str] = {}
    volumes: Optional[List[Volume]]
    host_port: Optional[int]
    container_port: Optional[int]
    network: str = DEFAULT_DOCKER_NETWORK
    create_network: bool = True


def get_free_port() -> int:
    """Return a free port on the host to bind a container to

    Returns:
        int: Port found
    """
    sock = socket.socket()
    sock.bind(("", 0))

    return sock.getsockname()[1]


def docker_network_exists(client: docker.DockerClient, network: str):
    """Check if network exists

    Args:
        client (docker.DockerClient): Docker client
        network (str): name of network to check

    Returns:
        bool: Network exists
    """
    try:
        client.networks.get(network)
        return True
    except docker.errors.NotFound:
        return False


def create_docker_network(client: docker.DockerClient, network: str):
    """Create docker network

    Args:
        client (docker.DockerClient): Docker client
        network (str): Name of network to create

    Raises:
        RuntimeError: Raised if network could not be created
    """
    try:
        client.networks.create(network)
    except APIError as err:
        raise RuntimeError(f"Unable to configure docker network: {err}")


def configure_docker_network(
    client: docker.DockerClient,
    network: str,
    create_network: bool,
):
    """Determine if docker network exists and create one if not found and specified

    Args:
        client (docker.DockerClient): Docker client
        network (str): Name of network to check or create
        create_network (bool): Create network if not found

    Raises:
        ValueError: Raised if docker network was not found and not allowed to be created
    """
    if not docker_network_exists(client, network):
        if create_network:
            create_docker_network(client, network)
        else:
            raise ValueError(f"Docker network {network} not configured")


def pull_docker_image(client: docker.DockerClient, image: str):
    """Pulls image from remote

    Args:
        client (docker.DockerClient): Docker client
        image (str): image to pull (ex: redis:6)
    """
    parts = image.split(":")

    repository = parts[0]
    tag = parts[1] if len(parts) > 1 else "latest"

    client.images.pull(repository, tag)


def create_docker_container(
    client: docker.DockerClient,
    args: DockerServerArgs,
):
    """
    Creates and configures docker container for docker runner

    Args:
        client: Docker client
        image: docker image to launch
        env_map: env vars to provide to container
        run_id: cicada run ID (to provide as a tag to the container)
        network: Docker network to add container to
        create_network: Creates the network if not found if set to True
        volumes: List of absolute paths to directories on local machine to share with runner container

    Returns:
        Docker container object
    """
    # NOTE: client may need more config options (probably get from env)
    # client: docker.DockerClient = docker.from_env()

    configure_docker_network(client, args.network, args.create_network)

    if args.volumes is None:
        volume_map = {}
    else:
        volume_map = {
            vol.source: {"bind": vol.destination, "mode": "rw"} for vol in args.volumes
        }

    if args.network != "host" and args.container_port is not None:
        if args.host_port is None:
            host_port = get_free_port()
        else:
            host_port = args.host_port

        port_map = {f"{args.container_port}/tcp": host_port}
    else:
        port_map = {}

    try:
        # Start container
        # LOGGER.debug("Starting Docker container with image %s", image)
        return client.containers.run(
            args.image,
            command=args.command,
            name=args.name,
            detach=True,
            environment=args.env,
            network=args.network,
            labels=["cicada-distributed"] + args.labels,
            ports=port_map,
            volumes=volume_map,
        )
    except APIError as err:
        raise RuntimeError(f"Unable to create container: {err}")


def get_docker_container(client: docker.DockerClient, name: str):
    """Get a docker container by name

    Args:
        client (docker.DockerClient): Docker client
        name (str): Name of container to find

    Returns:
        Optional[Container]: Container or none if not found
    """
    try:
        return client.containers.get(name)
    except NotFound:
        return None


def container_is_running(container: Any):
    """Check if container is running by running top

    Args:
        container (any): Container to check

    Returns:
        bool: Container is running
    """
    try:
        container.top()
        return True
    except APIError:
        return False


def container_logs(container: Any) -> str:
    """Get logs for a container

    Args:
        container (any): Container to get logs for

    Returns:
        str: Logs from container
    """
    return container.logs().decode()


def stop_docker_container_by_name(client: docker.DockerClient, container_id: str):
    """Find container by name and stop it

    Args:
        client (docker.DockerClient): Docker client
        container_id (str): Name of container to find
    """
    container = get_docker_container(client, container_id)

    stop_docker_container(container)


def stop_docker_container(container: Any):
    """Stop a docker container

    Args:
        container (any): Docker container to stop
    """
    if container is not None:
        container.stop(timeout=3)


def remove_docker_container_by_name(client: docker.DockerClient, container_id: str):
    """Find a docker container by name and remove it

    Args:
        client (docker.DockerClient): Docker client
        container_id (str): Name of container
    """
    container = get_docker_container(client, container_id)

    remove_docker_container(container)


def remove_docker_container(container: Any):
    """Remove a docker container

    Args:
        container (any): Container to remove
    """
    if container is not None:
        container.remove()


def build_docker_image(client: docker.DockerClient, path: str, dockerfile: str):
    """Build a docker image given path and path to dockerfile and add to local
    registry

    Args:
        client (docker.DockerClient): Docker client
        path (str): Path to build context
        dockerfile (str): Path to dockerfile

    Raises:
        RuntimeError: Raised if unable to build image

    Returns:
        str: Tag generated for container
    """
    tag = f"cicada-test-container-{str(uuid.uuid4())[:8]}"

    try:
        client.images.build(tag=tag, path=path, dockerfile=dockerfile)
        return tag
    except APIError as err:
        raise RuntimeError(f"Unable to build Cicada image: {err}")


def docker_container_up(client: docker.DockerClient, name: str, args: DockerServerArgs):
    """Check if docker container is running, start container is not running

    Args:
        client (docker.DockerClient): Docker client
        name (str): Name of docker container to check
        args (DockerServerArgs): Args to start container with

    Returns:
        Container: Container found or started with name
    """
    container = get_docker_container(client, name)

    if container is not None and not container_is_running(container):
        remove_docker_container(container)
        container = create_docker_container(client, args)
    elif container is None:
        container = create_docker_container(client, args)

    return container


def docker_container_down_by_name(client: docker.DockerClient, name: str):
    """Stop and remove container if it is found

    Args:
        client (docker.DockerClient): Docker client
        name (str): Name of container to stop and remove
    """
    container = get_docker_container(client, name)

    docker_container_down(container)


def docker_container_down(container: Any):
    """Stop provided container

    Args:
        container (Any): Container to stop and remove
    """
    # NOTE: should it check if running too?
    if container is not None:
        stop_docker_container(container)
        remove_docker_container(container)


def clean_docker_containers(client: docker.DockerClient, label: str):
    """Stop and remove containers given a list of labels

    Args:
        client (docker.DockerClient): Docker client
        label (str): labels to match containers against
    """
    containers = client.containers.list(filters={"label": label})

    # FIXME: may need performance enhancement
    for container in containers:
        docker_container_down(container)


def docker_redis_up(client: docker.DockerClient, network: str):
    """Start Redis container

    Args:
        client (docker.DockerClient): Docker client
        network (str): Network to add Redis container to

    Returns:
        Redis container: Created redis container
    """
    image = "redis:6"

    args = DockerServerArgs(
        image=image,
        name="cicada-distributed-redis",
        labels=["cicada-distributed-redis"],
        volumes=[
            Volume(
                source=os.path.dirname(configs_module.__file__),
                destination="/usr/local/etc/redis",
            )
        ],
        host_port=6379,
        container_port=6379,
        network=network,
    )

    pull_docker_image(client, image)
    return docker_container_up(client, "cicada-distributed-redis", args)


def docker_redis_down(client: docker.DockerClient):
    """Stop redis container

    Args:
        client (docker.DockerClient): Docker client
    """
    docker_container_down_by_name(client, "cicada-distributed-redis")


def docker_datastore_client_up(client: docker.DockerClient, network: str):
    """Start Datastore CLient container

    Args:
        client (docker.DockerClient): Docker client
        network (str): Network to add Datastore CLient container to

    Returns:
        Datastore client container: Created datastore client container
    """
    if os.getenv("ENV") == "local":
        image = "cicadatesting/cicada-distributed-datastore-client:latest"
    elif os.getenv("ENV") == "dev":
        image = "cicadatesting/cicada-distributed-datastore-client:pre-release"
    else:
        image = f"cicadatesting/cicada-distributed-datastore-client:{CICADA_VERSION}"
        pull_docker_image(client, image)

    args = DockerServerArgs(
        image=image,
        name="cicada-distributed-datastore-client",
        labels=["cicada-distributed-datastore-client"],
        host_port=8283,
        container_port=8283,
        network=network,
    )

    return docker_container_up(client, "cicada-distributed-datastore-client", args)


def docker_datastore_client_down(client: docker.DockerClient):
    """Stop datastore client container

    Args:
        client (docker.DockerClient): Docker client
    """
    docker_container_down_by_name(client, "cicada-distributed-datastore-client")


def docker_container_service_up(client: docker.DockerClient, network: str):
    """Start Container Service

    Args:
        client (docker.DockerClient): Docker client
        network (str): Network to add Container Service to

    Returns:
        Container: Container Service
    """
    if os.getenv("ENV") == "local":
        image = "cicadatesting/cicada-distributed-container-service:latest"
    elif os.getenv("ENV") == "dev":
        image = "cicadatesting/cicada-distributed-container-service:pre-release"
    else:
        image = f"cicadatesting/cicada-distributed-container-service:{CICADA_VERSION}"
        pull_docker_image(client, image)

    args = DockerServerArgs(
        image=image,
        name="cicada-distributed-container-service",
        labels=["cicada-distributed-container-service"],
        volumes=[
            Volume(source="/var/run/docker.sock", destination="/var/run/docker.sock")
        ],
        host_port=8284,
        container_port=8284,
        env={"RUNNER_TYPE": DOCKER_CONTAINER_MODE},
        network=network,
    )

    return docker_container_up(client, "cicada-distributed-container-service", args)


def docker_container_service_down(client: docker.DockerClient):
    """Stop Container Service

    Args:
        client (docker.DockerClient): Docker client
    """
    docker_container_down_by_name(client, "cicada-distributed-container-service")


def make_kube_template(template_filename: str):
    template_path = os.path.join(
        os.path.dirname(templates_module.__file__), template_filename
    )

    with open(template_path, "r") as template_fp:
        return template_fp.read()


def make_kube_redis_template() -> str:
    return make_kube_template("redis.yaml")


def make_kube_datastore_client_template() -> str:
    return make_kube_template("datastore-client.yaml")


def make_kube_container_service_template() -> str:
    return make_kube_template("container-service.yaml")


def make_kube_job_template() -> str:
    return make_kube_template("job.yaml")


def make_concatenated_kube_templates():
    templates = [
        make_kube_redis_template(),
        make_kube_datastore_client_template(),
        make_kube_container_service_template(),
        make_kube_job_template(),
    ]

    return "---\n".join(templates)
