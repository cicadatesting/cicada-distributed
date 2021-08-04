from datetime import datetime
from unittest.mock import Mock, patch, call
from pytest import raises

from cicadad.core import scenario as scenario_module
from cicadad.services import datastore
from cicadad.util.constants import DOCKER_CONTAINER_MODE


@patch("cicadad.services.datastore.get_work")
def test_has_work(get_work_mock):
    user_id = "abc"
    address = "some address"
    s = Mock()
    get_work_mock.return_value = 1

    uc = scenario_module.UserCommands(s, user_id, address)

    assert uc.has_work()
    assert uc.available_work == 0

    get_work_mock.assert_called_with(user_id, address)


@patch("cicadad.services.datastore.get_work")
def test_has_more_work(get_work_mock):
    user_id = "abc"
    address = "some address"
    s = Mock()
    get_work_mock.return_value = 2

    uc = scenario_module.UserCommands(s, user_id, address)

    assert uc.has_work(500)
    assert uc.has_work(500)
    assert uc.available_work == 0

    get_work_mock.assert_called_once_with(user_id, address)


@patch("cicadad.services.datastore.get_work")
def test_has_no_work(get_work_mock):
    user_id = "abc"
    address = "some address"
    s = Mock()
    get_work_mock.return_value = 0

    uc = scenario_module.UserCommands(s, user_id, address)

    assert not uc.has_work()
    assert get_work_mock.call_count == 2

    get_work_mock.assert_called_with(user_id, address)


def test_run_logs():
    def test_fn():
        print("foo")

    user_id = "abc"
    address = "some address"
    s = Mock()

    s.fn = test_fn

    uc = scenario_module.UserCommands(s, user_id, address)

    output, exception, logs = uc.run()

    assert output is None
    assert exception is None
    assert logs == "foo\n"


def test_run_output():
    def test_fn():
        return 42

    user_id = "abc"
    address = "some address"
    s = Mock()

    s.fn = test_fn

    uc = scenario_module.UserCommands(s, user_id, address)

    output, exception, logs = uc.run()

    assert output == 42
    assert exception is None
    assert logs == ""


def test_run_exception():
    def test_fn():
        raise ValueError("some error")

    user_id = "abc"
    address = "some address"
    s = Mock()

    s.fn = test_fn

    uc = scenario_module.UserCommands(s, user_id, address)

    output, exception, logs = uc.run(log_traceback=False)

    assert output is None
    assert isinstance(exception, ValueError)
    assert str(exception) == "some error"
    assert logs == ""


def test_scale_users_up():
    s = Mock()
    tid = "t-123"
    image = "foo"
    network = "bar"
    namespace = "default"
    sid = "abc"
    datastore_addr = "fizz"
    container_service_addr = "buzz"
    container_mode = DOCKER_CONTAINER_MODE
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        tid,
        image,
        network,
        namespace,
        sid,
        datastore_addr,
        container_service_addr,
        container_mode,
        ctx,
    )

    sc.start_users = Mock()
    sc.stop_users = Mock()

    sc.scale_users(10)

    sc.start_users.assert_called_once_with(10)


def test_scale_users_down():
    s = Mock()
    tid = "t-123"
    image = "foo"
    network = "bar"
    namespace = "default"
    sid = "abc"
    datastore_addr = "fizz"
    container_service_addr = "buzz"
    container_mode = DOCKER_CONTAINER_MODE
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        tid,
        image,
        network,
        namespace,
        sid,
        datastore_addr,
        container_service_addr,
        container_mode,
        ctx,
    )

    sc.start_users = Mock()
    sc.stop_users = Mock()

    sc.num_users = 20

    sc.scale_users(10)

    sc.stop_users.assert_called_once_with(10)


@patch("cicadad.core.scenario.container_service.start_docker_container")
@patch("cicadad.core.scenario.datastore.add_user_event")
def test_start_users(add_user_event_mock, start_container_mock):
    s = Mock()
    tid = "t-123"
    image = "foo"
    network = "bar"
    namespace = "default"
    sid = "abc"
    datastore_addr = "fizz"
    container_service_addr = "buzz"
    container_mode = DOCKER_CONTAINER_MODE
    ctx = {}

    s.name = "s"
    s.users_per_container = 3

    sc = scenario_module.ScenarioCommands(
        s,
        tid,
        image,
        network,
        namespace,
        sid,
        datastore_addr,
        container_service_addr,
        container_mode,
        ctx,
    )

    sc.buffered_work = 10
    sc.add_work = Mock()

    sc.start_users(5)

    assert start_container_mock.call_count == 2
    assert add_user_event_mock.call_count == 2

    sc.add_work.assert_called_once_with(10)
    assert sc.buffered_work == 0


def test_start_users_negative():
    s = Mock()
    tid = "t-123"
    image = "foo"
    network = "bar"
    namespace = "default"
    sid = "abc"
    datastore_addr = "fizz"
    container_service_addr = "buzz"
    container_mode = DOCKER_CONTAINER_MODE
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        tid,
        image,
        network,
        namespace,
        sid,
        datastore_addr,
        container_service_addr,
        container_mode,
        ctx,
    )

    with raises(ValueError, match="Must supply a positive number of users to start"):
        sc.start_users(-1)


@patch("cicadad.services.container_service.stop_docker_container")
@patch("cicadad.services.datastore.add_user_event")
def test_stop_users(add_user_event_mock, stop_container_mock):
    s = Mock()
    tid = "t-123"
    image = "foo"
    network = "bar"
    namespace = "default"
    sid = "abc"
    datastore_addr = "fizz"
    container_service_addr = "buzz"
    container_mode = DOCKER_CONTAINER_MODE
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        tid,
        image,
        network,
        namespace,
        sid,
        datastore_addr,
        container_service_addr,
        container_mode,
        ctx,
    )

    add_user_event_mock.return_value = None
    stop_container_mock.return_value = None

    sc.num_users = 4
    sc.user_ids = ["1", "2", "3", "4"]
    sc.user_locations = {"1": "a", "2": "a", "3": "b", "4": "b"}
    sc.user_manager_counts = {"a": 2, "b": 2}

    sc.stop_users(3)

    assert sc.num_users == 1
    assert sc.user_ids == ["4"]


def test_stop_users_too_many():
    s = Mock()
    tid = "t-123"
    image = "foo"
    network = "bar"
    namespace = "default"
    sid = "abc"
    datastore_addr = "fizz"
    container_service_addr = "buzz"
    container_mode = DOCKER_CONTAINER_MODE
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        tid,
        image,
        network,
        namespace,
        sid,
        datastore_addr,
        container_service_addr,
        container_mode,
        ctx,
    )

    with raises(ValueError, match="Scenario currently has less than 3 users"):
        sc.stop_users(3)


def test_stop_users_negative():
    s = Mock()
    tid = "t-123"
    image = "foo"
    network = "bar"
    namespace = "default"
    sid = "abc"
    datastore_addr = "fizz"
    container_service_addr = "buzz"
    container_mode = DOCKER_CONTAINER_MODE
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        tid,
        image,
        network,
        namespace,
        sid,
        datastore_addr,
        container_service_addr,
        container_mode,
        ctx,
    )

    with raises(ValueError, match="Must supply a positive number of users to stop"):
        sc.stop_users(-1)


@patch("cicadad.services.datastore.distribute_work")
def test_add_work(distribute_work_mock):
    s = Mock()
    tid = "t-123"
    image = "foo"
    network = "bar"
    namespace = "default"
    sid = "abc"
    datastore_addr = "fizz"
    container_service_addr = "buzz"
    container_mode = DOCKER_CONTAINER_MODE
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        tid,
        image,
        network,
        namespace,
        sid,
        datastore_addr,
        container_service_addr,
        container_mode,
        ctx,
    )

    distribute_work_mock.return_value = None

    sc.num_users = 3
    sc.user_ids = ["1", "2", "3"]

    sc.add_work(11)

    assert distribute_work_mock.call_count == 1


def test_has_work_buffered():
    s = Mock()
    tid = "t-123"
    image = "foo"
    network = "bar"
    namespace = "default"
    sid = "abc"
    datastore_addr = "fizz"
    container_service_addr = "buzz"
    container_mode = DOCKER_CONTAINER_MODE
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        tid,
        image,
        network,
        namespace,
        sid,
        datastore_addr,
        container_service_addr,
        container_mode,
        ctx,
    )

    sc.add_work(10)

    assert sc.buffered_work == 10


def test_aggregate_results():
    s = Mock()
    tid = "t-123"
    image = "foo"
    network = "bar"
    namespace = "default"
    sid = "abc"
    datastore_addr = "fizz"
    container_service_addr = "buzz"
    container_mode = DOCKER_CONTAINER_MODE
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        tid,
        image,
        network,
        namespace,
        sid,
        datastore_addr,
        container_service_addr,
        container_mode,
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
    tid = "t-123"
    image = "foo"
    network = "bar"
    namespace = "default"
    sid = "abc"
    datastore_addr = "fizz"
    container_service_addr = "buzz"
    container_mode = DOCKER_CONTAINER_MODE
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        tid,
        image,
        network,
        namespace,
        sid,
        datastore_addr,
        container_service_addr,
        container_mode,
        ctx,
    )

    s.result_aggregator = None

    assert sc.aggregate_results([datastore.Result(output=1)]) == 1
    assert sc.aggregate_results([datastore.Result(output=2)]) == 2
    assert sc.aggregate_results([datastore.Result(output=3)]) == 3

    assert sc.aggregated_results == 3


def test_verify_results():
    s = Mock()
    tid = "t-123"
    image = "foo"
    network = "bar"
    namespace = "default"
    sid = "abc"
    datastore_addr = "fizz"
    container_service_addr = "buzz"
    container_mode = DOCKER_CONTAINER_MODE
    ctx = {}

    sc = scenario_module.ScenarioCommands(
        s,
        tid,
        image,
        network,
        namespace,
        sid,
        datastore_addr,
        container_service_addr,
        container_mode,
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


@patch("cicadad.services.datastore.move_scenario_result")
@patch("cicadad.services.datastore.add_test_event")
@patch("cicadad.services.container_service.start_docker_container")
def test_test_runner(
    start_container_mock, add_test_event_mock, move_scenario_event_mock
):
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
    tags = []
    tid = "test-123"
    img = "foo"
    n = "bar"
    namespace = "default"
    datastore_addr = "fizz"
    container_service_addr = "buzz"
    container_mode = DOCKER_CONTAINER_MODE

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

    move_scenario_event_mock.side_effect = [r1, r2]

    scenario_module.test_runner(
        ss,
        tags,
        tid,
        img,
        n,
        namespace,
        datastore_addr,
        container_service_addr,
        container_mode,
    )

    assert add_test_event_mock.call_count == 7
    assert start_container_mock.call_count == 2


@patch("cicadad.services.datastore.set_scenario_result")
def test_run_scenario(set_scenario_result_mock):
    s = Mock()
    tid = "t-123"
    image = "foo"
    network = "bar"
    namespace = "default"
    sid = "abc"
    datastore_addr = "fizz"
    container_service_addr = "buzz"
    container_mode = DOCKER_CONTAINER_MODE
    ctx = {}

    def load_model(sc, c):
        sc.aggregated_results = 42
        sc.stop_users = Mock()

    s.load_model = load_model
    s.output_transformer = None

    scenario_module.scenario_runner(
        s,
        tid,
        image,
        network,
        namespace,
        sid,
        datastore_addr,
        container_service_addr,
        container_mode,
        ctx,
    )

    # Get kwargs of first call
    assert set_scenario_result_mock.mock_calls[0][2]["output"] == 42


@patch("cicadad.services.datastore.set_scenario_result")
def test_run_scenario_result_transformer(set_scenario_result_mock):
    s = Mock()
    tid = "t-123"
    image = "foo"
    network = "bar"
    namespace = "default"
    sid = "abc"
    datastore_addr = "fizz"
    container_service_addr = "buzz"
    container_mode = DOCKER_CONTAINER_MODE
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
        tid,
        image,
        network,
        namespace,
        sid,
        datastore_addr,
        container_service_addr,
        container_mode,
        ctx,
    )

    # Get kwargs of first call
    assert set_scenario_result_mock.mock_calls[0][2]["output"] == 84


@patch("cicadad.services.datastore.set_scenario_result")
def test_run_scenario_exception(set_scenario_result_mock):
    s = Mock()
    tid = "t-123"
    image = "foo"
    network = "bar"
    namespace = "default"
    sid = "abc"
    datastore_addr = "fizz"
    container_service_addr = "buzz"
    container_mode = DOCKER_CONTAINER_MODE
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
        tid,
        image,
        network,
        namespace,
        sid,
        datastore_addr,
        container_service_addr,
        container_mode,
        ctx,
    )

    # Get first call, then args of call, then 4th arg of call
    assert (
        str(set_scenario_result_mock.mock_calls[0][2]["exception"])
        == "1 error(s) were raised in scenario s:\nsome error"
    )

    assert (
        type(set_scenario_result_mock.mock_calls[0][2]["exception"]) == AssertionError
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
