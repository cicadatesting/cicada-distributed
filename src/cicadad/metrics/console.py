from typing import Callable, Dict, List, Optional

from cicadad.services import datastore
from cicadad.util.constants import DEFAULT_DATASTORE_ADDRESS


class ConsoleMetricField(object):
    def __init__(self, name: str, collector: Optional[Callable] = None) -> None:
        self.name = name
        self.collector = collector

    def collect_metric(
        self,
        scenario_id: str,
        results: List[datastore.Result],
        datastore_address: str = DEFAULT_DATASTORE_ADDRESS,
    ):
        if self.collector is not None:
            for value in self.collector(results):
                datastore.add_metric(scenario_id, self.name, value, datastore_address)

    def get_metric(
        self, scenario_id: str, datastore_address: str, **kwargs
    ) -> Optional[str]:
        raise NotImplementedError("Add metric not implemented")


class ConsoleStats(ConsoleMetricField):
    def get_metric(
        self,
        scenario_id: str,
        datastore_address: str = DEFAULT_DATASTORE_ADDRESS,
        **kwargs,
    ):
        # get stats from datastore
        stats = datastore.get_metric_statistics(
            scenario_id, self.name, datastore_address
        )

        if stats is None:
            return None

        return (
            f"Min: {round(stats['min'], 3)}, "
            f"Median: {round(stats['median'], 3)}, "
            f"Average: {round(stats['average'], 3)}, "
            f"Max: {round(stats['max'], 3)}, "
            f"Len: {stats['len']}"
        )


class ConsoleCount(ConsoleMetricField):
    def get_metric(
        self,
        scenario_id: str,
        datastore_address: str = DEFAULT_DATASTORE_ADDRESS,
        **kwargs,
    ):
        # get stats from datastore
        count = datastore.get_metric_total(scenario_id, self.name, datastore_address)

        if count is None:
            return None

        return str(round(count, 3))


class ConsoleLatest(ConsoleMetricField):
    def get_metric(
        self,
        scenario_id: str,
        datastore_address: str = DEFAULT_DATASTORE_ADDRESS,
        **kwargs,
    ):
        # get stats from datastore
        last = datastore.get_last_metric(scenario_id, self.name, datastore_address)

        if last is None:
            return None

        return str(round(last, 3))


class ConsolePercent(ConsoleMetricField):
    def get_metric(
        self,
        scenario_id: str,
        # split_point: float,
        datastore_address: str = DEFAULT_DATASTORE_ADDRESS,
        **kwargs,
    ):
        # get stats from datastore
        last = datastore.get_metric_rate(
            scenario_id, self.name, kwargs["split_point"], datastore_address
        )

        if last is None:
            return None

        return str(round(last, 3))


class ConsoleMetrics(object):
    def __init__(self, *fields: ConsoleMetricField) -> None:
        self.fields = {}

        for field in fields:
            self.fields[field.name] = field

    def collect_metrics(
        self,
        scenario_id: str,
        results: List[datastore.Result],
        datastore_address: str = DEFAULT_DATASTORE_ADDRESS,
    ):
        for field in self.fields:
            self.fields[field].collect_metric(scenario_id, results, datastore_address)

    def get_current(
        self,
        scenario_id: str,
        datastore_address: str = DEFAULT_DATASTORE_ADDRESS,
        **kwargs,
    ) -> Dict[str, Optional[str]]:
        return {
            field: self.fields[field].get_metric(
                scenario_id, datastore_address, **kwargs
            )
            for field in self.fields
        }
