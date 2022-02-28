from unittest.mock import Mock

from cicadad.core import commands
from cicadad.core.types import Result


def test_scale_users():
    scenario = Mock()
    backend = Mock()
    test_id = "abc"
    scenario_id = "def"
    context = {}

    sc = commands.ScenarioCommands(scenario, test_id, scenario_id, backend, context)

    sc.scale_users(10)

    assert sc.num_users == 10

    sc.scale_users(0)

    assert sc.num_users == 0


def test_stop_users_too_many():
    scenario = Mock()
    backend = Mock()
    test_id = "abc"
    scenario_id = "def"
    context = {}

    sc = commands.ScenarioCommands(scenario, test_id, scenario_id, backend, context)

    sc.start_users(10)

    sc.stop_users(11)

    assert sc.num_users == 0


def test_get_latest_results():
    scenario = Mock()
    backend = Mock()
    test_id = "abc"
    scenario_id = "def"
    context = {}

    sc = commands.ScenarioCommands(scenario, test_id, scenario_id, backend, context)

    backend.move_user_results.return_value = [Mock(), Mock(), Mock()]

    sc.get_latest_results()

    assert sc.num_results_collected == 3


def test_aggregate_results():
    scenario = Mock()
    backend = Mock()
    test_id = "abc"
    scenario_id = "def"
    context = {}

    sc = commands.ScenarioCommands(scenario, test_id, scenario_id, backend, context)

    def aggregator_fn(previous, latest_results):
        if previous is None:
            p = 0
        else:
            p = previous

        return p + sum(latest_results)

    scenario.result_aggregator = aggregator_fn

    assert sc.aggregate_results([1]) == 1
    assert sc.aggregate_results([2]) == 3
    assert sc.aggregate_results([3]) == 6

    assert sc.aggregated_results == 6


def test_aggregate_results_default():
    scenario = Mock()
    backend = Mock()
    test_id = "abc"
    scenario_id = "def"
    context = {}

    sc = commands.ScenarioCommands(scenario, test_id, scenario_id, backend, context)

    scenario.result_aggregator = None

    assert sc.aggregate_results([Result(output=1)]) == 1
    assert sc.aggregate_results([Result(output=2)]) == 2
    assert sc.aggregate_results([Result(output=3)]) == 3

    assert sc.aggregated_results == 3


def test_verify_results():
    scenario = Mock()
    backend = Mock()
    test_id = "abc"
    scenario_id = "def"
    context = {}

    sc = commands.ScenarioCommands(scenario, test_id, scenario_id, backend, context)

    def result_verifier(results):
        return ["error" for r in results if not r]

    scenario.result_verifier = result_verifier

    assert sc.verify_results([False, True]) == ["error"]


def test_is_up():
    scenario = Mock()
    user_id = "abc"
    backend = Mock()

    event = Mock()

    event.payload = {"IDs": ["def"]}

    uc = commands.UserCommands(scenario, user_id, backend)

    backend.get_user_events.return_value = [event]

    assert uc.is_up()


def test_is_not_up():
    scenario = Mock()
    user_id = "abc"
    backend = Mock()

    event = Mock()

    event.payload = {"IDs": ["abc"]}

    uc = commands.UserCommands(scenario, user_id, backend)

    backend.get_user_events.return_value = [event]

    assert not uc.is_up()


def test_has_work():
    scenario = Mock()
    user_id = "abc"
    backend = Mock()

    uc = commands.UserCommands(scenario, user_id, backend)

    backend.get_work.return_value = 1

    assert uc.has_work()


def test_has_no_work():
    scenario = Mock()
    user_id = "abc"
    backend = Mock()

    uc = commands.UserCommands(scenario, user_id, backend)

    backend.get_work.return_value = 0

    assert not uc.has_work()


def test_run_logs():
    def test_fn():
        print("foo")

    scenario = Mock()
    user_id = "abc"
    backend = Mock()

    scenario.fn = test_fn

    uc = commands.UserCommands(scenario, user_id, backend)

    output, exception, logs = uc.run()

    assert output is None
    assert exception is None
    assert logs == "foo\n"


def test_run_output():
    def test_fn():
        return 42

    scenario = Mock()
    user_id = "abc"
    backend = Mock()

    scenario.fn = test_fn

    uc = commands.UserCommands(scenario, user_id, backend)

    output, exception, logs = uc.run()

    assert output == 42
    assert exception is None
    assert logs == ""


def test_run_exception():
    def test_fn():
        raise ValueError("some error")

    scenario = Mock()
    user_id = "abc"
    backend = Mock()

    scenario.fn = test_fn

    uc = commands.UserCommands(scenario, user_id, backend)

    output, exception, logs = uc.run(log_traceback=False)

    assert output is None
    assert isinstance(exception, ValueError)
    assert str(exception) == "some error"
    assert logs == ""
