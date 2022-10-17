from unittest.mock import Mock

from cicadad.core import decorators, scenario
from cicadad.metrics.collectors import runtime_seconds
from cicadad.metrics.console import console_collector, console_stats


def test_scenario():
    e = Mock()

    @decorators.scenario(e, "my-test")
    def test_fn():
        return 42

    assert isinstance(test_fn, scenario.Scenario)
    assert test_fn.name == "my-test"
    assert test_fn.user_loop is not None
    assert test_fn.load_model is not None
    assert test_fn.result_verifier is not None
    assert test_fn.dependencies == []
    assert test_fn.tags == []


def test_user_loop():
    e = Mock()
    ul = Mock()

    @decorators.scenario(e)
    @decorators.user_loop(ul)
    def test_fn():
        return 42

    assert test_fn.user_loop == ul


def test_add_attribute_backwards():
    e = Mock()
    ul = Mock()

    @decorators.user_loop(ul)
    @decorators.scenario(e)
    def test_fn():
        return 42

    assert test_fn.user_loop == ul


def test_load_model():
    e = Mock()
    lm = Mock()

    @decorators.scenario(e)
    @decorators.load_model(lm)
    def test_fn():
        return 42

    assert test_fn.load_model == lm


def test_dependency():
    e = Mock()

    @decorators.scenario(e)
    def test_fn_1():
        return 42

    @decorators.scenario(e)
    @decorators.dependency(test_fn_1)
    def test_fn_2():
        return 42

    assert test_fn_2.dependencies == [test_fn_1]


def test_result_aggregator():
    e = Mock()
    ra = Mock()

    @decorators.scenario(e)
    @decorators.result_aggregator(ra)
    def test_fn():
        return 42

    assert test_fn.result_aggregator == ra


def test_result_verifier():
    e = Mock()
    rv = Mock()

    @decorators.scenario(e)
    @decorators.result_verifier(rv)
    def test_fn():
        return 42

    assert test_fn.result_verifier == rv


def test_result_verifier_none():
    e = Mock()

    @decorators.scenario(e)
    @decorators.result_verifier(None)
    def test_fn():
        return 42

    assert test_fn.result_verifier is None


def test_output_transformer():
    e = Mock()
    ot = Mock()

    @decorators.scenario(e)
    @decorators.output_transformer(ot)
    def test_fn():
        return 42

    assert test_fn.output_transformer == ot


def test_tags():
    e = Mock()

    @decorators.scenario(e)
    @decorators.tag("foo")
    def test_fn():
        return 42

    assert test_fn.tags == ["foo"]


def test_overwrite_metrics_collectors():
    e = Mock()

    @decorators.scenario(e)
    @decorators.metrics_collectors([])
    def test_fn():
        return 42

    assert test_fn.metric_collectors == []


def test_add_metrics_collector():
    e = Mock()

    @decorators.scenario(e)
    @decorators.metrics_collector(console_collector("foo", runtime_seconds))
    def test_fn():
        return 42

    assert len(test_fn.metric_collectors) == 4


def test_overwrite_console_metrics_displays():
    e = Mock()

    @decorators.scenario(e)
    @decorators.console_metric_displays({})
    def test_fn():
        return 42

    assert test_fn.console_metric_displays == {}


def test_add_console_metrics_displays():
    e = Mock()

    @decorators.scenario(e)
    @decorators.console_metric_display("foo", console_stats("bar"))
    def test_fn():
        return 42

    assert len(test_fn.console_metric_displays) == 4
