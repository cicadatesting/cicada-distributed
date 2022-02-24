from unittest.mock import Mock, patch, call
from pytest import raises

from cicadad.core import scenario as scenario_module


def test_while_has_work():
    closure = scenario_module.while_has_work(500)

    uc = Mock()
    ctx = {}

    uc.is_up.side_effect = [True, True, False]
    uc.has_work.side_effect = [True, False]
    uc.run.return_value = 42, None, ""

    closure(uc, ctx)

    uc.has_work.assert_called_with(500)
    assert uc.report_result.call_count == 1


def test_while_alive():
    closure = scenario_module.while_alive()

    uc = Mock()
    ctx = {}

    uc.is_up.side_effect = [True, True, False]
    uc.run.return_value = 42, None, ""

    closure(uc, ctx)

    assert uc.report_result.call_count == 2


@patch("cicadad.core.scenario.time")
def test_iterations_per_second_limited(time_mock):
    closure = scenario_module.iterations_per_second_limited(3)

    uc = Mock()
    ctx = {}

    uc.is_up.side_effect = [True, True, True, True, False]
    uc.run.return_value = 42, None, ""

    closure(uc, ctx)

    assert uc.report_result.call_count == 3


@patch("cicadad.core.scenario.time")
def test_n_iterations(time_mock):
    closure = scenario_module.n_iterations(3, 2)

    sc = Mock()
    ctx = {}

    sc.get_latest_results.side_effect = [[1], [2, 3]]

    closure(sc, ctx)

    assert sc.scale_users.call_count == 2
    assert sc.scale_users.mock_calls[0] == call(2)
    sc.add_work.assert_called_with(3)


def test_n_iterations_timeout():
    # NOTE: uses real time
    closure = scenario_module.n_iterations(3, 2, wait_period=1, timeout=1)

    sc = Mock()
    ctx = {}

    sc.get_latest_results.side_effect = [[], []]

    with raises(AssertionError, match="Timed out waiting for results"):
        closure(sc, ctx)


def test_n_seconds():
    # NOTE: depends on real time
    closure = scenario_module.n_seconds(2, 2)

    sc = Mock()
    ctx = {}

    sc.get_latest_results.side_effect = [[1], [2, 3], [4]]

    closure(sc, ctx)

    assert sc.scale_users.call_count == 2
    assert sc.scale_users.mock_calls[0] == call(2)


def test_n_users_ramping_add_users():
    # NOTE: depends on real time
    closure = scenario_module.n_users_ramping(6, 5)

    class ScenarioCommandsMock:
        def __init__(self):
            self.num_users = 0
            self.start_users_calls = 0

        def start_users(self, n):
            self.num_users += n
            self.start_users_calls += 1

        def scale_users(self, n):
            self.num_users = n

        def collect_metrics(self, m):
            return

        def collect_datastore_metrics(self, latest_results):
            return

    sc = ScenarioCommandsMock()
    ctx = {}

    sc.get_latest_results = Mock()
    sc.aggregate_results = Mock()
    sc.verify_results = Mock()

    closure(sc, ctx)

    assert sc.num_users == 5
    assert sc.start_users_calls == 5


def test_n_users_ramping_stop_users():
    # NOTE: depends on real time
    closure = scenario_module.n_users_ramping(5, 6)

    class ScenarioCommandsMock:
        def __init__(self):
            self.num_users = 10
            self.stop_users_calls = 0

        def stop_users(self, n):
            self.num_users -= n
            self.stop_users_calls += 1

        def scale_users(self, n):
            self.num_users = n

        def collect_metrics(self, m):
            return

        def collect_datastore_metrics(self, latest_results):
            return

    sc = ScenarioCommandsMock()
    ctx = {}

    sc.get_latest_results = Mock()
    sc.aggregate_results = Mock()
    sc.verify_results = Mock()

    closure(sc, ctx)

    assert sc.num_users == 6
    assert sc.stop_users_calls == 4


def test_load_stages():
    # NOTE: depends on real time
    s1 = scenario_module.n_seconds(2, 2, skip_scaledown=True)
    s2 = scenario_module.n_iterations(2, 4, skip_scaledown=True)

    closure = scenario_module.load_stages(s1, s2)

    sc = Mock()
    ctx = {}

    sc.get_latest_results.side_effect = [[1], [2, 3], [4], [5, 6]]

    closure(sc, ctx)

    assert sc.scale_users.call_count == 3
    assert sc.scale_users.mock_calls[0] == call(2)
    assert sc.scale_users.mock_calls[1] == call(4)
    assert sc.scale_users.mock_calls[2] == call(0)
