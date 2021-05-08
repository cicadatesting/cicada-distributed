from collections import OrderedDict
from unittest.mock import Mock, patch, call
from pytest import raises
import hashlib

from cicadad.core import scenario as scenario_module
from cicadad.services import datastore, eventing


@patch("cicadad.services.eventing.get_work")
def test_has_work(get_work_mock):
    user_id = "abc"
    scenario_id = "def"
    s = Mock()
    c = Mock()
    p = Mock()
    get_work_mock.return_value = eventing.NewWork(amount=1, ids=set("1"))

    uc = scenario_module.UserCommands(s, user_id, scenario_id, c, p)

    assert uc.has_work()
    assert uc.available_work == 0

    get_work_mock.assert_called_with(
        c,
        int(hashlib.sha1(user_id.encode("ascii")).hexdigest(), 16),
        set(),
        1000,
    )


@patch("cicadad.services.eventing.get_work")
def test_has_more_work(get_work_mock):
    user_id = "abc"
    scenario_id = "def"
    s = Mock()
    c = Mock()
    p = Mock()
    get_work_mock.return_value = eventing.NewWork(amount=2, ids=set("1"))

    uc = scenario_module.UserCommands(s, user_id, scenario_id, c, p)

    assert uc.has_work(500)
    assert uc.has_work(500)
    assert uc.available_work == 0

    get_work_mock.assert_called_once_with(
        c,
        int(hashlib.sha1(user_id.encode("ascii")).hexdigest(), 16),
        set(),
        500,
    )


@patch("cicadad.services.eventing.get_work")
def test_has_no_work(get_work_mock):
    user_id = "abc"
    scenario_id = "def"
    s = Mock()
    c = Mock()
    p = Mock()
    get_work_mock.return_value = eventing.NewWork(amount=0, ids=set())

    uc = scenario_module.UserCommands(s, user_id, scenario_id, c, p)

    assert not uc.has_work()
    assert uc.work_event_ids == set()

    get_work_mock.assert_called_once_with(
        c,
        int(hashlib.sha1(user_id.encode("ascii")).hexdigest(), 16),
        set(),
        1000,
    )


def test_run_logs():
    def test_fn():
        print("foo")

    user_id = "abc"
    scenario_id = "def"
    s = Mock()
    c = Mock()
    p = Mock()

    s.fn = test_fn

    uc = scenario_module.UserCommands(s, user_id, scenario_id, c, p)

    output, exception, logs = uc.run()

    assert output is None
    assert exception is None
    assert logs == "foo\n"


def test_run_output():
    def test_fn():
        return 42

    user_id = "abc"
    scenario_id = "def"
    s = Mock()
    c = Mock()
    p = Mock()

    s.fn = test_fn

    uc = scenario_module.UserCommands(s, user_id, scenario_id, c, p)

    output, exception, logs = uc.run()

    assert output == 42
    assert exception is None
    assert logs == ""


def test_run_exception():
    def test_fn():
        raise ValueError("some error")

    user_id = "abc"
    scenario_id = "def"
    s = Mock()
    c = Mock()
    p = Mock()

    s.fn = test_fn

    uc = scenario_module.UserCommands(s, user_id, scenario_id, c, p)

    output, exception, logs = uc.run(log_traceback=False)

    assert output is None
    assert isinstance(exception, ValueError)
    assert str(exception) == "some error"
    assert logs == ""


def test_scale_users_up():
    s = Mock()
    image = "foo"
    network = "bar"
    sid = "abc"
    ep = Mock()
    rc = Mock()
    addr = "fizz"
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        image,
        network,
        sid,
        ep,
        rc,
        addr,
        ctx,
    )

    sc.start_users = Mock()
    sc.stop_users = Mock()

    sc.scale_users(10)

    sc.start_users.assert_called_once_with(10)


def test_scale_users_down():
    s = Mock()
    image = "foo"
    network = "bar"
    sid = "abc"
    ep = Mock()
    rc = Mock()
    addr = "fizz"
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        image,
        network,
        sid,
        ep,
        rc,
        addr,
        ctx,
    )

    sc.start_users = Mock()
    sc.stop_users = Mock()

    sc.num_users = 20

    sc.scale_users(10)

    sc.stop_users.assert_called_once_with(10)


@patch("cicadad.services.eventing.start_container")
def test_start_users(start_container_mock):
    s = Mock()
    image = "foo"
    network = "bar"
    sid = "abc"
    ep = Mock()
    rc = Mock()
    addr = "fizz"
    ctx = {}

    s.name = "s"

    sc = scenario_module.ScenarioCommands(
        s,
        image,
        network,
        sid,
        ep,
        rc,
        addr,
        ctx,
    )

    sc.buffered_work = 10
    sc.add_work = Mock()

    sc.start_users(5)

    assert start_container_mock.call_count == 5

    sc.add_work.assert_called_once_with(10)
    assert sc.buffered_work == 0


def test_start_users_negative():
    s = Mock()
    image = "foo"
    network = "bar"
    sid = "abc"
    ep = Mock()
    rc = Mock()
    addr = "fizz"
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        image,
        network,
        sid,
        ep,
        rc,
        addr,
        ctx,
    )

    with raises(ValueError, match="Must supply a positive number of users to start"):
        sc.start_users(-1)


@patch("cicadad.services.eventing.stop_user")
def test_stop_users(stop_user_mock):
    s = Mock()
    image = "foo"
    network = "bar"
    sid = "abc"
    ep = Mock()
    rc = Mock()
    addr = "fizz"
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        image,
        network,
        sid,
        ep,
        rc,
        addr,
        ctx,
    )

    stop_user_mock.return_value = None

    sc.num_users = 4
    sc.user_group_ids = OrderedDict([("a", ["1", "2"]), ("b", ["3", "4"])])

    sc.stop_users(3)

    assert sc.num_users == 1
    assert sc.user_group_ids == OrderedDict([("b", ["4"])])


def test_stop_users_too_many():
    s = Mock()
    image = "foo"
    network = "bar"
    sid = "abc"
    ep = Mock()
    rc = Mock()
    addr = "fizz"
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        image,
        network,
        sid,
        ep,
        rc,
        addr,
        ctx,
    )

    with raises(ValueError, match="Scenario currently has less than 3 users"):
        sc.stop_users(3)


def test_stop_users_negative():
    s = Mock()
    image = "foo"
    network = "bar"
    sid = "abc"
    ep = Mock()
    rc = Mock()
    addr = "fizz"
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        image,
        network,
        sid,
        ep,
        rc,
        addr,
        ctx,
    )

    with raises(ValueError, match="Must supply a positive number of users to stop"):
        sc.stop_users(-1)


@patch("cicadad.services.eventing.add_work")
def test_add_work(add_work_mock):
    s = Mock()
    image = "foo"
    network = "bar"
    sid = "abc"
    ep = Mock()
    rc = Mock()
    addr = "fizz"
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        image,
        network,
        sid,
        ep,
        rc,
        addr,
        ctx,
    )

    add_work_mock.return_value = None

    sc.num_users = 3
    sc.user_group_ids = OrderedDict([("a", ["1"]), ("b", ["2", "3"])])

    sc.add_work(11)

    assert add_work_mock.call_count == 4

    # NOTE: hash for "3" is less than has for "2"
    calls = [
        call(ep, "work-a", None, 3),
        call(ep, "work-b", None, 3),
        call(ep, "work-a", None, 1),
        call(ep, "work-b", int(hashlib.sha1("3".encode("ascii")).hexdigest(), 16), 1),
    ]

    add_work_mock.assert_has_calls(calls)


def test_has_work_buffered():
    s = Mock()
    image = "foo"
    network = "bar"
    sid = "abc"
    ep = Mock()
    rc = Mock()
    addr = "fizz"
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        image,
        network,
        sid,
        ep,
        rc,
        addr,
        ctx,
    )

    sc.add_work(10)

    assert sc.buffered_work == 10


def test_aggregate_results():
    s = Mock()
    image = "foo"
    network = "bar"
    sid = "abc"
    ep = Mock()
    rc = Mock()
    addr = "fizz"
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        image,
        network,
        sid,
        ep,
        rc,
        addr,
        ctx,
    )

    def aggregator_fn(previous, latest_results):
        if previous is None:
            p = 0
        else:
            p = previous

        return p + sum(latest_results)

    s.result_aggregator = aggregator_fn

    assert sc.aggregate_results([1]) == 1
    assert sc.aggregate_results([2]) == 3
    assert sc.aggregate_results([3]) == 6

    assert sc.aggregated_results == 6


def test_aggregate_results_default():
    s = Mock()
    image = "foo"
    network = "bar"
    sid = "abc"
    ep = Mock()
    rc = Mock()
    addr = "fizz"
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        image,
        network,
        sid,
        ep,
        rc,
        addr,
        ctx,
    )

    s.result_aggregator = None

    assert sc.aggregate_results([datastore.Result(output=1)]) == 1
    assert sc.aggregate_results([datastore.Result(output=2)]) == 2
    assert sc.aggregate_results([datastore.Result(output=3)]) == 3

    assert sc.aggregated_results == 3


def test_verify_results():
    s = Mock()
    image = "foo"
    network = "bar"
    sid = "abc"
    ep = Mock()
    rc = Mock()
    addr = "fizz"
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        image,
        network,
        sid,
        ep,
        rc,
        addr,
        ctx,
    )

    def result_verifier(results):
        return ["error" for r in results if not r]

    s.result_verifier = result_verifier

    assert sc.verify_results([False, True]) == ["error"]


def test_filter_scenarios():
    s1 = Mock()
    s2 = Mock()

    s1.tags = ["foo", "bar"]
    s2.tags = ["fizz", "buzz"]

    assert scenario_module.filter_scenarios_by_tag([s1, s2], ["fizz", "bizz"]) == [s2]


def test_filter_scenarios_empty():
    s1 = Mock()
    s2 = Mock()

    assert scenario_module.filter_scenarios_by_tag([s1, s2], []) == [s1, s2]


@patch("cicadad.services.eventing.get_events")
@patch("cicadad.services.eventing.start_container")
def test_test_runner(start_container_mock, get_events_mock):
    s1 = Mock()
    s2 = Mock()
    s3 = Mock()

    s1.name = "s1"
    s2.name = "s2"
    s3.name = "s3"

    s1.dependencies = []
    s2.dependencies = [s1]
    s3.dependencies = [s2]

    ss = [s1, s2, s3]
    img = "foo"
    n = "bar"
    tid = "123"
    ep = Mock()
    rc = Mock()
    addr = "abc"

    e1 = eventing.ResultEvent(
        action="result",
        event_id="1",
        scenario_name="s1",
        result=datastore.Result(output=42),
    )

    e2 = eventing.ResultEvent(
        action="result",
        event_id="2",
        scenario_name="s2",
        result=datastore.Result(exception=ValueError("some error")),
    )

    get_events_mock.side_effect = [[e1], [e2]]

    assert len(list(scenario_module.test_runner(ss, img, n, tid, ep, rc, addr))) == 5
    assert start_container_mock.call_count == 2


@patch("cicadad.services.eventing.report_scenario_result")
def test_run_scenario(report_scenario_result_mock):
    s = Mock()
    image = "foo"
    network = "bar"
    sid = "abc"
    tid = "def"
    ep = Mock()
    rc = Mock()
    addr = "fizz"
    ctx = {}

    def load_model(sc, c):
        sc.aggregated_results = 42
        sc.stop_users = Mock()

    s.load_model = load_model
    s.output_transformer = None

    scenario_module.scenario_runner(
        s,
        image,
        network,
        sid,
        tid,
        ep,
        rc,
        addr,
        ctx,
    )

    # Get first call, then args of call, then 4th arg of call
    assert report_scenario_result_mock.mock_calls[0][1][3].output == 42


@patch("cicadad.services.eventing.report_scenario_result")
def test_run_scenario_result_transformer(report_scenario_result_mock):
    s = Mock()
    image = "foo"
    network = "bar"
    sid = "abc"
    tid = "def"
    ep = Mock()
    rc = Mock()
    addr = "fizz"
    ctx = {}

    def load_model(sc, c):
        sc.aggregated_results = 42
        sc.stop_users = Mock()

    def double_result(ar):
        return ar * 2

    s.load_model = load_model
    s.output_transformer = double_result

    scenario_module.scenario_runner(
        s,
        image,
        network,
        sid,
        tid,
        ep,
        rc,
        addr,
        ctx,
    )

    # Get first call, then args of call, then 4th arg of call
    assert report_scenario_result_mock.mock_calls[0][1][3].output == 84


@patch("cicadad.services.eventing.report_scenario_result")
def test_run_scenario_exception(report_scenario_result_mock):
    s = Mock()
    image = "foo"
    network = "bar"
    sid = "abc"
    tid = "def"
    ep = Mock()
    rc = Mock()
    addr = "fizz"
    ctx = {}

    def load_model(sc, c):
        sc.aggregated_results = None
        sc.errors = ["some error"]
        sc.stop_users = Mock()

    s.load_model = load_model
    s.output_transformer = None
    s.name = "s"

    scenario_module.scenario_runner(
        s,
        image,
        network,
        sid,
        tid,
        ep,
        rc,
        addr,
        ctx,
    )

    # Get first call, then args of call, then 4th arg of call
    assert (
        str(report_scenario_result_mock.mock_calls[0][1][3].exception)
        == "1 error(s) were raised in scenario s:\nsome error"
    )

    assert (
        type(report_scenario_result_mock.mock_calls[0][1][3].exception)
        == AssertionError
    )


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


def test_iterations_per_second_limited():
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
    closure = scenario_module.n_iterations(3, 2, wait_period=1, timeout=1)

    sc = Mock()
    ctx = {}

    sc.get_latest_results.side_effect = [[], []]

    with raises(AssertionError, match="Timed out waiting for results"):
        closure(sc, ctx)


def test_n_seconds():
    closure = scenario_module.n_seconds(2, 2)

    sc = Mock()
    ctx = {}

    sc.get_latest_results.side_effect = [[1], [2, 3]]

    closure(sc, ctx)

    assert sc.scale_users.call_count == 2
    assert sc.scale_users.mock_calls[0] == call(2)


def test_n_users_ramping_add_users():
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

    sc = ScenarioCommandsMock()
    ctx = {}

    sc.get_latest_results = Mock()
    sc.aggregate_results = Mock()
    sc.verify_results = Mock()

    closure(sc, ctx)

    assert sc.num_users == 5
    assert sc.start_users_calls == 5


def test_n_users_ramping_stop_users():
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

    sc = ScenarioCommandsMock()
    ctx = {}

    sc.get_latest_results = Mock()
    sc.aggregate_results = Mock()
    sc.verify_results = Mock()

    closure(sc, ctx)

    assert sc.num_users == 6
    assert sc.stop_users_calls == 4


def test_load_stages():
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
