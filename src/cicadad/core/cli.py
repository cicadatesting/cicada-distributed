import json
import uuid
import time
import sys
import os
import shutil

from blessed import Terminal  # type: ignore
import click
import docker  # type: ignore

from cicadad.services import datastore, container_service
from cicadad.core import containers
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
@click.option("--mode", default=constants.DEFAULT_CONTAINER_MODE)
def start_cluster(ctx, network, create_network, mode):
    # FEATURE: more options for docker client
    if mode == constants.KUBE_CONTAINER_MODE:
        click.echo(containers.make_concatenated_kube_templates())
    elif mode == constants.DOCKER_CONTAINER_MODE:
        docker_client = docker.from_env()

        containers.configure_docker_network(
            docker_client,
            network,
            create_network,
        )

        redis_container = containers.docker_redis_up(docker_client, network)

        if ctx.obj["DEBUG"]:
            click.echo(f"Created Redis: {redis_container.id}")

        datastore_client = containers.docker_datastore_client_up(
            docker_client,
            network,
        )

        if ctx.obj["DEBUG"]:
            click.echo(f"Created Datastore Client: {datastore_client.id}")

        container_service = containers.docker_container_service_up(
            docker_client, network
        )

        if ctx.obj["DEBUG"]:
            click.echo(f"Created Container Service: {container_service.id}")
    else:
        raise ValueError(f"Invalid mode: {mode}")


@cli.command()
@click.pass_context
def stop_cluster(ctx):
    docker_client = docker.from_env()

    containers.docker_container_service_down(docker_client)

    if ctx.obj["DEBUG"]:
        click.echo("Stopped Container Service")

    containers.docker_datastore_client_down(docker_client)

    if ctx.obj["DEBUG"]:
        click.echo("Stopped Datastore Client")

    containers.docker_redis_down(docker_client)

    if ctx.obj["DEBUG"]:
        click.echo("Stopped Redis")

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
@click.option("--mode", type=str, default=constants.DEFAULT_CONTAINER_MODE)
@click.option("--namespace", type=str, default=constants.DEFAULT_KUBE_NAMESPACE)
@click.option("--datastore-client-address", type=str, default="localhost:8283")
@click.option("--container-service-address", type=str, default="localhost:8284")
@click.option("--no-exit-unsuccessful", is_flag=True)
@click.option("--no-cleanup", is_flag=True)
def run(
    ctx,
    image,
    build_path,
    dockerfile,
    network,
    tag,
    mode,
    namespace,
    datastore_client_address,
    container_service_address,
    no_exit_unsuccessful,
    no_cleanup,
):
    # FIXME: move to function with dependencies removed
    docker_client = docker.from_env()
    term = Terminal()

    if image:
        image_id = image
    elif mode == constants.DOCKER_CONTAINER_MODE:
        image_id = containers.build_docker_image(
            client=docker_client,
            path=build_path,
            dockerfile=dockerfile,
        )
    else:
        raise ValueError(
            f"Must specify image if not running in {constants.DEFAULT_CONTAINER_MODE} mode"
        )

    test_id = f"cicada-test-{str(uuid.uuid4())[:8]}"

    click.echo(
        term.bold
        + term.center(f" Starting Test: {test_id} ", fillchar="=")
        + "\n"
        + term.normal
    )

    if tag == []:
        tag_arg = []
    else:
        tag_arg = [e for t in tag for e in ["--tag", t]]

    if mode == constants.KUBE_CONTAINER_MODE:
        container_service.start_kube_container(
            container_service.StartKubeContainerArgs(
                image=image_id,
                name=test_id,
                command=[
                    "run-test",
                    "--test-id",
                    test_id,
                    "--image",
                    image_id,
                    "--network",
                    network,
                    "--namespace",
                    namespace,
                    "--container-mode",
                    mode,
                ]
                + tag_arg,
                labels={
                    "type": "cicada-distributed-test",
                    "test": test_id,
                },
                namespace=namespace,
            ),
            container_service_address,
        )
    else:
        # NOTE: mode is checked earlier
        container_service.start_docker_container(
            container_service.StartDockerContainerArgs(
                image=image_id,
                name=test_id,
                command=[
                    "run-test",
                    "--test-id",
                    test_id,
                    "--image",
                    image_id,
                    "--network",
                    network,
                    "--namespace",
                    namespace,
                    "--container-mode",
                    mode,
                ]
                + tag_arg,
                labels={
                    "type": "cicada-distributed-test",
                    "test": test_id,
                },
                # env: Dict[str, str]={}
                network=network,
            ),
            container_service_address,
        )

    # FEATURE: Error if cluster is not up

    try:
        # FIXME: move to function
        context = {}
        passed = []
        failed = []
        finished = False

        while not finished:
            # poll for events
            events = datastore.get_test_events(test_id, datastore_client_address)
            skip_sleep = False

            for event in events:
                if event.kind == "SCENARIO_FINISHED":
                    context = json.loads(event.payload.context)

                    result = context[event.payload.scenario]

                    if result["exception"] is not None:
                        click.echo(
                            term.bold
                            + term.center(
                                f" {event.payload.scenario}: "
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

                        failed.append(event.payload.scenario)
                    else:
                        click.echo(
                            term.bold
                            + term.center(
                                f" {event.payload.scenario}: "
                                + term.green
                                + "Passed "
                                + term.normal
                                + term.bold,
                                fillchar="-",
                            )
                            + "\n"
                            + term.normal
                        )

                        passed.append(event.payload.scenario)

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
                        + term.center(f" {event.payload.message} ", fillchar="-")
                        + "\n"
                        + term.normal
                    )

                if event.kind == "TEST_FINISHED":
                    finished = True
                    skip_sleep = True

            if not skip_sleep:
                time.sleep(1)
    finally:
        if not no_cleanup:
            if mode == constants.KUBE_CONTAINER_MODE:
                if ctx.obj["DEBUG"]:
                    click.echo("Cleaning Test Runners")

                container_service.stop_kube_container(
                    test_id,
                    namespace=namespace,
                    address=container_service_address,
                )

                if ctx.obj["DEBUG"]:
                    click.echo("Cleaned Test Runners")
                    click.echo("Cleaning Scenarios")

                # containers.clean_docker_containers(
                #     docker_client, "cicada-distributed-scenario"
                # )
                container_service.stop_kube_container(
                    "",
                    namespace=namespace,
                    labels={"type": "cicada-distributed-scenario", "test": test_id},
                    address=container_service_address,
                )

                if ctx.obj["DEBUG"]:
                    click.echo("Cleaned Scenarios")
                    click.echo("Cleaning Users")

                container_service.stop_kube_container(
                    "",
                    namespace=namespace,
                    labels={"type": "cicada-distributed-user", "test": test_id},
                    address=container_service_address,
                )

                if ctx.obj["DEBUG"]:
                    click.echo("Cleaned Users")
            else:
                if ctx.obj["DEBUG"]:
                    click.echo("Cleaning Test Runners")

                container_service.stop_docker_container(
                    test_id,
                    address=container_service_address,
                )

                if ctx.obj["DEBUG"]:
                    click.echo("Cleaned Test Runners")
                    click.echo("Cleaning Scenarios")

                container_service.stop_docker_container(
                    "",
                    labels={"type": "cicada-distributed-scenario", "test": test_id},
                    address=container_service_address,
                )

                if ctx.obj["DEBUG"]:
                    click.echo("Cleaned Scenarios")
                    click.echo("Cleaning Users")

                container_service.stop_docker_container(
                    "",
                    labels={"type": "cicada-distributed-user", "test": test_id},
                    address=container_service_address,
                )

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
