from datetime import datetime, timedelta
from typing import Dict, List
import atexit
import json
import time
import sys
import os
import shutil
import configobj  # type: ignore

from rich.live import Live
from rich.console import Console
from blessed import Terminal  # type: ignore
import click
import docker  # type: ignore
from cicadad.core.types import ICLIBackend
from cicadad.services.backend import CLIBackend, DefaultBackendAPI  # type: ignore

from cicadad.util.console import LivePanel, MetricDisplay, MetricsPanel, TasksPanel
from cicadad.core import containers
from cicadad.util import constants
from cicadad import templates as templates_module
from cicadad import backend as backend_module


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
@click.option(
    "--network",
    type=str,
    default=constants.DEFAULT_DOCKER_NETWORK,
    help="Network to add docker cluster to",
)
@click.option(
    "--create-network/--no-create-network",
    default=True,
    help="Create network for cluster and containers",
)
@click.option("--mode", default=constants.DOCKER_SCHEDULING_MODE, help="DOCKER or KUBE")
@click.option(
    "--install-location",
    default=os.path.dirname(backend_module.__file__),
    help="Path to install backend binaries to",
)
def start_cluster(ctx, network, create_network, mode, install_location):
    """Setup backend

    \b
    * DOCKER will create a containerized local cluster
    * KUBE will print out a chart to install the cluster
    """
    if mode == constants.KUBE_SCHEDULING_MODE:
        click.echo(containers.make_concatenated_kube_templates())
    elif mode == constants.DOCKER_SCHEDULING_MODE:
        docker_client = docker.from_env()

        containers.configure_docker_network(
            docker_client,
            network,
            create_network,
        )

        if ctx.obj["DEBUG"]:
            click.echo("Starting Redis")

        redis_container = containers.docker_redis_up(docker_client, network)

        if ctx.obj["DEBUG"]:
            click.echo(f"Created Redis: {redis_container.id}")
            click.echo("Starting Backend")

        backend = containers.docker_backend_up(
            docker_client,
            network,
        )

        if ctx.obj["DEBUG"]:
            click.echo(f"Created Backend: {backend.id}")
    else:
        raise ValueError(f"Invalid mode: {mode}")


@cli.command()
@click.pass_context
def stop_cluster(ctx):
    docker_client = docker.from_env()

    containers.docker_backend_down(docker_client)

    if ctx.obj["DEBUG"]:
        click.echo("Stopped Backend")

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
@click.option("--test-file", type=str, default="test.py", show_default=True)
@click.option(
    "--log-path",
    type=str,
    default=".",
    help="Path to put local log files in (such as 'logs')",
    show_default=True,
)
@click.option("--image", type=str, required=False)
@click.option("--build-path", type=str, default=".", show_default=True)
@click.option("--dockerfile", type=str, default="Dockerfile", show_default=True)
@click.option("--network", type=str, default=constants.DEFAULT_DOCKER_NETWORK)
@click.option("--tag", "-t", type=str, multiple=True, default=[], show_default=True)
@click.option(
    "--env",
    "-e",
    nargs=2,
    type=click.Tuple([str, str]),
    multiple=True,
    default=[],
    help="ex. FOO=BAR",
    show_default=True,
)
@click.option(
    "--env-file",
    type=str,
    default=None,
    help="Env file to parse containing key-value pairs",
    show_default=True,
)
@click.option(
    "--mode",
    type=str,
    default=constants.DEFAULT_SCHEDULING_MODE,
    help="LOCAL, DOCKER, or KUBE",
    show_default=True,
)
@click.option(
    "--namespace", type=str, default=constants.DEFAULT_KUBE_NAMESPACE, show_default=True
)
@click.option("--backend-address", type=str, default="localhost:8283")
@click.option(
    "--backend-location",
    default=os.path.dirname(backend_module.__file__),
    help="Path local backend binaries were installed to",
)
@click.option(
    "--test-timeout",
    type=int,
    default=None,
    help="Time limit in seconds for entire test to finish",
    show_default=True,
)
@click.option(
    "--test-start-timeout",
    type=int,
    default=10,
    help="Time limit in seconds to wait for test to start before quitting",
    show_default=True,
)
@click.option("--no-exit-unsuccessful", is_flag=True, help="Return 0 even if failures")
@click.option(
    "--no-cleanup", is_flag=True, help="Do not clean up test processes or containers"
)
def run(
    ctx,
    test_file,
    log_path,
    image,
    build_path,
    dockerfile,
    network,
    backend_location,
    tag,
    env,
    env_file,
    mode,
    namespace,
    backend_address,
    test_timeout,
    test_start_timeout,
    no_exit_unsuccessful,
    no_cleanup,
):
    # TODO: not configurable, probably can get rid of interfaces
    backend = CLIBackend(DefaultBackendAPI(backend_address))
    term = Terminal()

    if mode == constants.LOCAL_SCHEDULING_MODE:
        # make sure test file exists
        # FIXME: may need own function
        if not os.path.isfile(test_file):
            raise ValueError(f"Test file not found: {test_file}")

        image_id = os.path.abspath(test_file)
        local_backend = containers.start_local_backend(
            backend_location, ctx.obj["DEBUG"]
        )

        if ctx.obj["DEBUG"]:
            click.echo(f"Started local backend: {local_backend.pid}")

        # FEATURE: wait for backend to healthcheck
        time.sleep(3)

        atexit.register(lambda: local_backend.terminate())
    elif image:
        image_id = image
    elif mode == constants.DOCKER_SCHEDULING_MODE:
        docker_client = docker.from_env()

        image_id = containers.build_docker_image(
            client=docker_client,
            path=build_path,
            dockerfile=dockerfile,
        )
    else:
        raise ValueError(
            f"Must specify image if not running in {constants.DEFAULT_SCHEDULING_MODE} mode"
        )

    # Parse env file and args
    if env_file is not None:
        env_file_map = configobj.ConfigObj(env_file)
    else:
        env_file_map = {}

    env_map = {key: value for key, value in env}

    # Get test going
    test_id = start_test_instance(
        tag,
        {**env_file_map, **env_map},
        mode,
        image_id,
        log_path,
        network,
        namespace,
        backend,
    )

    # FEATURE: Error if cluster is not up

    context = {}
    metrics = {}
    passed = []
    failed = []
    started = False
    finished = False
    test_start_time = datetime.now()
    rich_console = Console()

    try:
        # FEATURE: option to disable live printing
        tasks_panel = TasksPanel()
        metrics_panel = MetricsPanel()

        live_panel = LivePanel(test_id, tasks_panel, metrics_panel)

        with Live(
            console=rich_console,
            refresh_per_second=20,
        ) as live:
            while not finished:
                if not started and datetime.now() > test_start_time + timedelta(
                    seconds=test_start_timeout
                ):
                    raise RuntimeError("Test failed to start")

                if (
                    test_timeout is not None
                    and datetime.now()
                    > test_start_time + timedelta(seconds=test_timeout)
                ):
                    raise RuntimeError(
                        f"Test timed out after {test_timeout} seconds. "
                        "Check test instance logs for more details"
                    )

                live.update(live_panel.get_renderable())

                # poll for events
                events = backend.get_test_events(test_id)
                skip_sleep = False

                for event in events:
                    if event.kind == "SCENARIO_METRIC":
                        metrics[event.payload.scenario] = event.payload.metrics

                        metrics_panel.add_metric(
                            event.payload.scenario, event.payload.metrics
                        )
                    elif event.kind == "SCENARIO_FINISHED":
                        context = json.loads(event.payload.context)

                        result = context[event.payload.scenario]

                        if result["exception"] is not None:
                            tasks_panel.update_task_failed(event.payload.scenario)

                            failed.append(event.payload.scenario)
                        else:
                            tasks_panel.update_task_success(event.payload.scenario)

                            passed.append(event.payload.scenario)

                        metrics_panel.remove_metric(event.payload.scenario)

                    elif event.kind == "SCENARIO_STARTED":
                        tasks_panel.add_running_task(
                            event.payload.scenario, event.payload.scenario_id
                        )
                    elif event.kind == "TEST_STARTED":
                        started = True

                        if ctx.obj["DEBUG"]:
                            click.echo(
                                f"Started Test: {test_id}: {event.payload.message}"
                            )
                    elif event.kind == "TEST_ERRORED":
                        raise RuntimeError("Test failed:", event.payload.message)
                    elif event.kind == "TEST_FINISHED":
                        finished = True
                        skip_sleep = True

                if not skip_sleep:
                    time.sleep(1)
    finally:
        if not no_cleanup:
            cleanup(
                ctx.obj["DEBUG"],
                test_id,
                backend,
            )

    print_results(
        term,
        rich_console,
        passed,
        failed,
        context,
        metrics,
        ctx.obj["DEBUG"],
    )

    if failed != [] and not no_exit_unsuccessful:
        sys.exit(1)


def start_test_instance(
    tag: List[str],
    env: Dict[str, str],
    mode: str,
    image_id: str,
    log_path: str,
    network: str,
    namespace: str,
    backend: ICLIBackend,
) -> str:
    if mode == constants.KUBE_SCHEDULING_MODE:
        return backend.create_test(
            scheduling_metadata=json.dumps({"image": image_id, "namespace": namespace}),
            backend_address=constants.CONTAINER_BACKEND_ADDRESS,
            tags=tag,
            env=env,
        )
    elif mode == constants.DOCKER_SCHEDULING_MODE:
        return backend.create_test(
            scheduling_metadata=json.dumps({"image": image_id, "network": network}),
            backend_address=constants.CONTAINER_BACKEND_ADDRESS,
            tags=tag,
            env=env,
        )
    else:
        return backend.create_test(
            scheduling_metadata=json.dumps(
                {
                    "pythonExecutable": sys.executable,
                    "testFilePath": image_id,
                    "logdir": log_path,
                }
            ),
            backend_address=constants.DEFAULT_BACKEND_ADDRESS,
            tags=tag,
            env=env,
        )


def cleanup(debug: bool, test_id: str, backend: ICLIBackend):
    if debug:
        click.echo("Cleaning Test Instances")

    backend.clean_test_instances(test_id)

    if debug:
        click.echo("Cleaned test instances")


def print_results(
    term: Terminal,
    rich_console: Console,
    passed: List[str],
    failed: List[str],
    context: dict,
    metrics: Dict[str, Dict[str, str]],
    debug: bool,
):
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

    for scenario in context:
        result = context[scenario]

        if result["exception"] is not None:
            click.echo(
                term.bold
                + term.center(
                    f" {scenario}: " + term.red + "Failed " + term.normal + term.bold,
                    fillchar="-",
                )
                + "\n"
                + term.normal
            )

            click.echo(f"Exception: {result['exception']}")
            click.echo("\n")
        else:
            click.echo(
                term.bold
                + term.center(
                    f" {scenario}: " + term.green + "Passed " + term.normal + term.bold,
                    fillchar="-",
                )
                + "\n"
                + term.normal
            )

        if result["output"] is not None:
            click.echo(f"Result: {result['output']}")
            click.echo("\n")

        if result["logs"] and (result["exception"] is not None or debug):
            click.echo("Logs:")
            click.echo(result["logs"])
            click.echo("\n")

        click.echo(f"Time Taken: {result['time_taken']} Seconds")
        click.echo(f"Succeeded: {result['succeeded']} Loop(s)")
        click.echo(f"Failed: {result['failed']} Loop(s)")

        if scenario in metrics:
            metrics_table = MetricDisplay(scenario)

            metrics_table.update_metrics(metrics[scenario])

            click.echo("Metrics:")
            rich_console.print(metrics_table.get_renderable())
            click.echo("\n")


# init project (load base files)
# package runner for docker

if __name__ == "__main__":
    cli()
