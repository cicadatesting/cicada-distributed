from typing import Callable, Iterable, List

from cicadad.services import datastore
from cicadad.util.constants import DEFAULT_DATASTORE_ADDRESS


ConsoleCollectorFn = Callable[[List[datastore.Result]], Iterable[float]]


def console_collector(name: str, collector: ConsoleCollectorFn):
    """Send metric created by collector function to datastore.

    Args:
        name (str): Name of metric
        collector (ConsoleCollectorFn): Function to convert results to list of metric values
    """

    def collect_metric(results: List[datastore.Result], scenario_commands):
        for value in collector(results):
            datastore.add_metric(
                scenario_commands.scenario_id,
                name,
                value,
                scenario_commands.datastore_address,
            )

    return collect_metric


def console_stats():
    """Get stats for metric from datastore."""

    def get(
        name: str,
        scenario_id: str,
        datastore_address: str = DEFAULT_DATASTORE_ADDRESS,
    ):
        stats = datastore.get_metric_statistics(scenario_id, name, datastore_address)

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
        datastore_address: str = DEFAULT_DATASTORE_ADDRESS,
    ):
        count = datastore.get_metric_total(scenario_id, name, datastore_address)

        if count is None:
            return None

        return str(round(count, 3))

    return get


def console_latest():
    """Get latest metric from datastore."""

    def get(
        name: str,
        scenario_id: str,
        datastore_address: str = DEFAULT_DATASTORE_ADDRESS,
    ):
        last = datastore.get_last_metric(scenario_id, name, datastore_address)

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
        datastore_address: str = DEFAULT_DATASTORE_ADDRESS,
    ):
        rate = datastore.get_metric_rate(
            scenario_id, name, split_point, datastore_address
        )

        if rate is None:
            return None

        return str(round(rate, 3))

    return get
