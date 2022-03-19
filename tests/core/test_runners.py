from datetime import datetime
from unittest.mock import Mock, patch
from cicadad.core import runners
from cicadad.core.scenario import Scenario


def test_filter_scenarios():
    s1 = Mock()
    s2 = Mock()

    s1.tags = ["foo", "bar"]
    s2.tags = ["fizz", "buzz"]

    assert runners.filter_scenarios_by_tag([s1, s2], ["fizz", "bizz"]) == [s2]


def test_filter_scenarios_empty():
    s1 = Mock()
    s2 = Mock()

    assert runners.filter_scenarios_by_tag([s1, s2], []) == [s1, s2]


def test_test_runner():
    s1 = Scenario(name="s1", fn=Mock())
    s2 = Scenario(name="s2", fn=Mock(), timeout=3)
    s3 = Scenario(name="s3", fn=Mock())

    cmd_foo = Mock()

    cmd_foo.return_value = "xyz"

    cmds = {"foo": cmd_foo}

    s1.name = "s1"
    s2.name = "s2"
    s3.name = "s3"

    s1.console_metric_displays = cmds
    s2.console_metric_displays = None
    s3.console_metric_displays = None

    s1.dependencies = []
    s2.dependencies = [s1]
    s3.dependencies = [s2]

    ss = [s1, s2, s3]
    tags = []
    backend = Mock()

    r1 = {
        "output": "42",
        "exception": None,
        "logs": "",
        "timestamp": str(datetime.now()),
        "time_taken": 3,
    }

    r2 = {
        "output": None,
        "exception": "some error",
        "logs": "",
        "timestamp": str(datetime.now()),
        "time_taken": 3,
    }

    backend.move_scenario_result.side_effect = [r1, r2]
    backend.create_scenario.side_effect = ["s1", "s2", "s3"]

    runners.test_runner(ss, tags, backend)

    assert backend.add_test_event.call_count == 8
    assert backend.create_scenario.call_count == 2


def test_run_scenario():
    s = Mock()
    tid = "t-123"
    sid = "abc"
    backend = Mock()
    ctx = {}

    def load_model(sc, c):
        sc.aggregated_results = 42
        sc.stop_users = Mock()

    s.load_model = load_model
    s.output_transformer = None

    runners.scenario_runner(
        s,
        tid,
        sid,
        backend,
        ctx,
    )

    # Get kwargs of first call
    assert backend.set_scenario_result.mock_calls[0][2]["output"] == 42


@patch("cicadad.core.runners.ScenarioCommands")
def test_run_scenario_result_transformer(scenario_commands_mock):
    s = Mock()
    tid = "t-123"
    sid = "abc"
    backend = Mock()
    ctx = {}

    scenario_commands = scenario_commands_mock.return_value

    scenario_commands.aggregated_results = 42

    def double_result(ar):
        return ar * 2

    s.output_transformer = double_result

    runners.scenario_runner(
        s,
        tid,
        sid,
        backend,
        ctx,
    )

    # Get kwargs of first call
    assert backend.set_scenario_result.mock_calls[0][2]["output"] == 84


@patch("cicadad.core.runners.ScenarioCommands")
def test_run_scenario_exception(scenario_commands_mock):
    s = Mock()
    tid = "t-123"
    sid = "abc"
    backend = Mock()
    ctx = {}

    scenario_commands = scenario_commands_mock.return_value

    scenario_commands.errors = ["some error"]
    scenario_commands.aggregated_results = None

    s.output_transformer = None
    s.name = "s"

    runners.scenario_runner(
        s,
        tid,
        sid,
        backend,
        ctx,
    )

    # Get first call, then args of call, then 4th arg of call
    assert (
        str(backend.set_scenario_result.mock_calls[0][2]["exception"])
        == "1 error(s) were raised in scenario s:\nsome error"
    )

    assert (
        type(backend.set_scenario_result.mock_calls[0][2]["exception"])
        == AssertionError
    )
