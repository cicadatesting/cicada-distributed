from unittest.mock import Mock, patch

from cicadad.core import containers
from cicadad.server import manager
from cicadad.services import eventing


@patch("cicadad.server.manager.fire_and_forget")
def test_process_start(fire_and_forget_mock):
    msg = eventing.ContainerEvent(
        action="START", event_id="123", container_id="abc", container_args={}
    )

    client = Mock()

    manager.process_message(msg, client)

    client.submit.assert_called_once_with(
        manager.create_docker_container, containers.DockerServerArgs()
    )


@patch("cicadad.server.manager.fire_and_forget")
def test_process_stop(fire_and_forget_mock):
    msg = eventing.ContainerEvent(
        action="STOP", event_id="123", container_id="abc", container_args={}
    )

    client = Mock()

    manager.process_message(msg, client)

    client.submit.assert_called_once_with(manager.stop_docker_container, "abc")
