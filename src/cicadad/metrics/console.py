from typing import Callable, Iterable, List

from cicadad.core.types import IConsoleMetricsBackend, IScenarioBackend, Result


ConsoleCollectorFn = Callable[[List[Result]], Iterable[float]]


def console_collector(name: str, collector: ConsoleCollectorFn):
    """Send metric created by collector function to backend.

    Helper for scenarios that want to leverage the backend to store metrics.

    Args:
        name (str): Name of metric
        collector (ConsoleCollectorFn): Function to convert results to list of metric values
    """

    def collect_metric(results: List[Result], backend: IScenarioBackend):
        for value in collector(results):
            backend.add_metric(name, value)

    return collect_metric


def console_stats():
    """Get stats for metric from datastore."""

    def get(
        name: str,
        scenario_id: str,
        backend: IConsoleMetricsBackend,
    ):
        stats = backend.get_metric_statistics(scenario_id, name)

        if stats is None:
            return None

        return (
            f"Min: {round(stats['min'], 3)}, "
            f"Median: {round(stats['median'], 3)}, "
            f"Average: {round(stats['average'], 3)}, "
            f"Max: {round(stats['max'], 3)}, "
            f"Len: {stats['len']}"
        )

    return get


def console_count():
    """Get count metric from datastore."""

    def get(
        name: str,
        scenario_id: str,
        backend: IConsoleMetricsBackend,
    ):
        count = backend.get_metric_total(scenario_id, name)

        if count is None:
            return None

        return str(round(count, 3))

    return get


def console_latest():
    """Get latest metric from datastore."""

    def get(
        name: str,
        scenario_id: str,
        backend: IConsoleMetricsBackend,
    ):
        last = backend.get_last_metric(scenario_id, name)

        if last is None:
            return None

        return str(round(last, 3))

    return get


def console_percent(split_point: float):
    """Get percent above split point for metric from datastore.

    Args:
        split_point (float): Point to split metric values at
    """

    def get(
        name: str,
        scenario_id: str,
        backend: IConsoleMetricsBackend,
    ):
        rate = backend.get_metric_rate(scenario_id, name, split_point)

        if rate is None:
            return None

        return str(round(rate, 3))

    return get
