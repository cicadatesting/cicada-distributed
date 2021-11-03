from unittest.mock import patch

from cicadad.metrics import console


def sample_collector(latest_results):
    return [
        float(result.output) for result in latest_results if result.exception is None
    ]


@patch("cicadad.services.datastore.get_metric_statistics")
def test_console_stats(metrics_mock):
    metrics_mock.return_value = {
        "min": 1.23456,
        "median": 1.23456,
        "max": 1.23456,
        "average": 1.23456,
        "len": 1,
    }

    console_stats = console.console_stats()

    metrics_string = console_stats("foo", "bar")

    assert (
        metrics_string
        == "Min: 1.235, Median: 1.235, Average: 1.235, Max: 1.235, Len: 1"
    ), "Metrics string not equal to expected"


@patch("cicadad.services.datastore.get_metric_statistics")
def test_console_stats_none(metrics_mock):
    metrics_mock.return_value = None

    console_stats = console.console_stats()

    metrics_string = console_stats("foo", "bar")

    assert metrics_string is None, "Metrics string not equal to expected"


@patch("cicadad.services.datastore.get_metric_total")
def test_console_count(metrics_mock):
    metrics_mock.return_value = 60

    console_count = console.console_count()

    metrics_string = console_count("foo", "bar")

    assert metrics_string == "60", "Metrics string not equal to expected"


@patch("cicadad.services.datastore.get_metric_total")
def test_console_count_none(metrics_mock):
    metrics_mock.return_value = None

    console_count = console.console_count()

    metrics_string = console_count("foo", "bar")

    assert metrics_string is None, "Metrics string not equal to expected"


@patch("cicadad.services.datastore.get_last_metric")
def test_console_latest(metrics_mock):
    metrics_mock.return_value = 1.2345

    console_latest = console.console_latest()

    metrics_string = console_latest("foo", "bar")

    assert metrics_string == "1.234", "Metrics string not equal to expected"


@patch("cicadad.services.datastore.get_last_metric")
def test_console_latest_none(metrics_mock):
    metrics_mock.return_value = None

    console_latest = console.console_latest()

    metrics_string = console_latest("foo", "bar")

    assert metrics_string is None, "Metrics string not equal to expected"


@patch("cicadad.services.datastore.get_metric_rate")
def test_console_percent(metrics_mock):
    metrics_mock.return_value = 1.2345

    console_percent = console.console_percent(1)

    metrics_string = console_percent("foo", "bar")

    assert metrics_string == "1.234", "Metrics string not equal to expected"


@patch("cicadad.services.datastore.get_metric_rate")
def test_console_percent_none(metrics_mock):
    metrics_mock.return_value = None

    console_percent = console.console_percent(1)

    metrics_string = console_percent("foo", "bar")

    assert metrics_string is None, "Metrics string not equal to expected"
