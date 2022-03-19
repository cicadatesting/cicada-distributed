from unittest.mock import Mock, patch

from cicadad.metrics import console


def sample_collector(latest_results):
    return [
        float(result.output) for result in latest_results if result.exception is None
    ]


def test_console_stats():
    backend = Mock()

    backend.get_metric_statistics.return_value = {
        "min": 1.23456,
        "median": 1.23456,
        "max": 1.23456,
        "average": 1.23456,
        "len": 1,
    }

    console_stats = console.console_stats("foo")

    metrics_string = console_stats("foo", "bar", backend)

    assert (
        metrics_string
        == "Min: 1.235, Median: 1.235, Average: 1.235, Max: 1.235, Len: 1"
    ), "Metrics string not equal to expected"


def test_console_stats_none():
    backend = Mock()

    backend.get_metric_statistics.return_value = None

    console_stats = console.console_stats("foo")

    metrics_string = console_stats("foo", "bar", backend)

    assert metrics_string is None, "Metrics string not equal to expected"


def test_console_count():
    backend = Mock()

    backend.get_metric_total.return_value = 60

    console_count = console.console_count("foo")

    metrics_string = console_count("foo", "bar", backend)

    assert metrics_string == "60", "Metrics string not equal to expected"


def test_console_count_none():
    backend = Mock()

    backend.get_metric_total.return_value = None

    console_count = console.console_count("foo")

    metrics_string = console_count("foo", "bar", backend)

    assert metrics_string is None, "Metrics string not equal to expected"


def test_console_latest():
    backend = Mock()

    backend.get_last_metric.return_value = 1.2345

    console_latest = console.console_latest("foo")

    metrics_string = console_latest("foo", "bar", backend)

    assert metrics_string == "1.234", "Metrics string not equal to expected"


def test_console_latest_none():
    backend = Mock()

    backend.get_last_metric.return_value = None

    console_latest = console.console_latest("foo")

    metrics_string = console_latest("foo", "bar", backend)

    assert metrics_string is None, "Metrics string not equal to expected"


def test_console_percent():
    backend = Mock()

    backend.get_metric_rate.return_value = 1.2345

    console_percent = console.console_percent("foo", 1)

    metrics_string = console_percent("foo", "bar", backend)

    assert metrics_string == "1.234", "Metrics string not equal to expected"


def test_console_percent_none():
    backend = Mock()

    backend.get_metric_rate.return_value = None

    console_percent = console.console_percent("foo", 1)

    metrics_string = console_percent("foo", "bar", backend)

    assert metrics_string is None, "Metrics string not equal to expected"
