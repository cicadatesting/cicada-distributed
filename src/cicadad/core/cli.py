import json
import uuid
import time
import sys
import os
import shutil

from google.protobuf.empty_pb2 import Empty
from blessed import Terminal  # type: ignore
import click
import docker  # type: ignore
import grpc  # type: ignore

from cicadad.core import containers
from cicadad.protos import hub_pb2_grpc, hub_pb2
from cicadad.util import constants
from cicadad import templates as templates_module


@click.group()
@click.option("--debug", type=bool, default=False, is_flag=True)
@click.pass_context
def cli(ctx, debug):
    ctx.ensure_object(dict)

    ctx.obj["DEBUG"] = debug


@cli.command()
@click.argument("build-path", type=str, default=".")
@click.pass_context
def init(ctx, build_path):
    # Create dockerfile from template if not exists
    if not os.path.exists(os.path.join(build_path, "Dockerfile")):

        if os.getenv("ENV") == "local":
            dockerfile_path = os.path.join(
                os.path.dirname(templates_module.__file__), "local.dockerfile"
            )
        elif os.getenv("ENV") == "dev":
            dockerfile_path = os.path.join(
                os.path.dirname(templates_module.__file__), "dev.dockerfile"
            )
        else:
            dockerfile_path = os.path.join(
                os.path.dirname(templates_module.__file__), "Dockerfile"
            )

        # NOTE: Does not build subdirs to copy file
        shutil.copyfile(dockerfile_path, os.path.join(build_path, "Dockerfile"))

        if ctx.obj["DEBUG"]:
            click.echo("Added Dockerfile")

    # Create engine file from template if not exists
    if not os.path.exists(os.path.join(build_path, "test.py")):

        test_file = os.path.join(
            os.path.dirname(templates_module.__file__),
            "test.py",
        )

        shutil.copyfile(test_file, os.path.join(build_path, "test.py"))

        if ctx.obj["DEBUG"]:
            click.echo("Added test.py")


@cli.command()
@click.pass_context
@click.option("--network", type=str, default=constants.DEFAULT_DOCKER_NETWORK)
@click.option("--create-network/--no-create-network", default=True)
def start_cluster(ctx, network, create_network):
    # FEATURE: more options for docker client
    docker_client = docker.from_env()

    containers.configure_docker_network(docker_client, network, create_network)

    zookeeper_container = containers.docker_zookeeper_up(docker_client, network)

    if ctx.obj["DEBUG"]:
        click.echo(f"Created Zookeeper: {zookeeper_container.id}")

    kafka_container = containers.docker_kafka_up(docker_client, network)

    if ctx.obj["DEBUG"]:
        click.echo(f"Created Kafka: {kafka_container.id}")

    manager_container = containers.docker_manager_up(docker_client, network)

    if ctx.obj["DEBUG"]:
        click.echo(f"Created Manager: {manager_container.id}")


@cli.command()
@click.pass_context
def stop_cluster(ctx):
    docker_client = docker.from_env()

    containers.docker_manager_down(docker_client)

    if ctx.obj["DEBUG"]:
        click.echo("Stopped Manager")

    containers.docker_kafka_down(docker_client)

    if ctx.obj["DEBUG"]:
        click.echo("Stopped Kafka")

    containers.docker_zookeeper_down(docker_client)

    if ctx.obj["DEBUG"]:
        click.echo("Stopped Zookeeper")

    containers.clean_docker_containers(
        docker_client,
        [
            "cicada-distributed-test",
            "cicada-distributed-scenario",
            "cicada-distributed-user",
        ],
    )

    # NOTE: remove network?


@cli.command()
@click.pass_context
@click.option("--image", type=str, required=False)
@click.option("--build-path", type=str, default=".")
@click.option("--dockerfile", type=str, default="Dockerfile")
@click.option("--network", type=str, default=constants.DEFAULT_DOCKER_NETWORK)
@click.option("--tag", "-t", type=str, multiple=True, default=[])
@click.option("--no-exit-unsuccessful", is_flag=True)
def run(ctx, image, build_path, dockerfile, network, tag, no_exit_unsuccessful):
    # FIXME: move to function with dependencies removed
    docker_client = docker.from_env()
    term = Terminal()

    if image:
        image_id = image
    else:
        image_id = containers.build_docker_image(
            client=docker_client,
            path=build_path,
            dockerfile=dockerfile,
        )

    name = f"cicada-test-{str(uuid.uuid4())[:8]}"

    click.echo(
        term.bold
        + term.center(f" Starting Test: {name} ", fillchar="=")
        + "\n"
        + term.normal
    )

    args = containers.DockerServerArgs(
        image=image_id,
        name=name,
        command=f"run-test --image {image_id} --network {network}",
        in_cluster=False,
        labels=["cicada-distributed-test"],
        # env: Dict[str, str]={}
        # volumes: Optional[List[Volume]]
        host_port=8282,
        container_port=50051,
        network=network,
        # create_network: bool=True
    )

    test_container = containers.create_docker_container(docker_client, args)

    # FEATURE: Error if cluster is not up

    try:
        # FIXME: move to function
        with grpc.insecure_channel("[::]:8282") as channel:
            stub = hub_pb2_grpc.HubStub(channel)

            # FIXME: integrate with util.backoff
            ready = False
            tries = 0
            period = 2

            while not ready and tries < 3:
                try:
                    response = stub.Healthcheck(Empty())
                    ready = response.ready
                except grpc.RpcError as e:
                    ready = False

                    if ctx.obj["DEBUG"]:
                        click.echo(e)

                    time.sleep(period)

                    tries += 1
                    period *= 2

            if not ready:
                logs = containers.container_logs(test_container)

                raise RuntimeError(f"Could not start test:\n{logs}")

        # FIXME: move to function
        context = {}
        passed = []
        failed = []

        with grpc.insecure_channel("[::]:8282") as channel:
            stub = hub_pb2_grpc.HubStub(channel)
            msg = hub_pb2.RunTestRequest(tags=tag)

            for status in stub.Run(msg):
                # HACK: maybe change this to send back only the results for scenario instead of whole context

                if status.type == "SCENARIO_FINISHED":
                    context = json.loads(status.context)

                    result = context[status.scenario]

                    if result["exception"] is not None:
                        click.echo(
                            term.bold
                            + term.center(
                                f" {status.scenario}: "
                                + term.red
                                + "Failed "
                                + term.normal
                                + term.bold,
                                fillchar="-",
                            )
                            + "\n"
                            + term.normal
                        )

                        click.echo(f"Exception: {result['exception']}")
                        click.echo("\n")

                        failed.append(status.scenario)
                    else:
                        click.echo(
                            term.bold
                            + term.center(
                                f" {status.scenario}: "
                                + term.green
                                + "Passed "
                                + term.normal
                                + term.bold,
                                fillchar="-",
                            )
                            + "\n"
                            + term.normal
                        )

                        passed.append(status.scenario)

                    if result["output"] is not None:
                        click.echo(f"Result: {result['output']}")
                        click.echo("\n")

                    if result["logs"] and (
                        result["exception"] is not None or ctx.obj["DEBUG"]
                    ):
                        click.echo("Logs:")
                        click.echo(result["logs"])
                        click.echo("\n")
                else:
                    click.echo(
                        term.bold
                        + term.center(f" {status.message} ", fillchar="-")
                        + "\n"
                        + term.normal
                    )
    finally:
        if ctx.obj["DEBUG"]:
            click.echo("Cleaning Test Runners")

        containers.stop_docker_container_by_name(docker_client, test_container.id)
        containers.clean_docker_containers(docker_client, "cicada-distributed-test")

        if ctx.obj["DEBUG"]:
            click.echo("Cleaned Test Runners")
            click.echo("Cleaning Scenarios")

        containers.clean_docker_containers(docker_client, "cicada-distributed-scenario")

        if ctx.obj["DEBUG"]:
            click.echo("Cleaned Scenarios")
            click.echo("Cleaning Users")

        containers.clean_docker_containers(docker_client, "cicada-distributed-user")

        if ctx.obj["DEBUG"]:
            click.echo("Cleaned Users")

    # FEATURE: report results in static site
    click.echo(
        term.bold + term.center(" Test Complete ", fillchar="=") + "\n" + term.normal
    )

    if len(passed) > 0:
        click.echo(term.bold + "Passed:\n" + term.normal)

        for scenario in passed:
            click.echo("* " + term.green + scenario + term.normal)

    if len(failed) > 0:
        click.echo(term.bold + "Failed:\n" + term.normal)

        for scenario in failed:
            click.echo("* " + term.red + scenario + term.normal)

    click.echo(
        term.bold
        + "\n"
        + term.center(
            " "
            + term.green
            + f"{len(passed)} passed"
            + term.normal
            + term.bold
            + ", "
            + term.red
            + f"{len(failed)} failed"
            + " "
            + term.normal
            + term.bold,
            fillchar="=",
        )
        + "\n"
        + term.normal
    )

    if no_exit_unsuccessful:
        sys.exit(0)
    elif failed != []:
        sys.exit(1)


# init project (load base files)
# package runner for docker

if __name__ == "__main__":
    cli()
