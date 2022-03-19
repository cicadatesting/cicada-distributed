from typing import List
import math

from cicadad.core.types import Result


def runtime_seconds(latest_results: List[Result]) -> List[float]:
    """Strip runtime from results.

    Args:
        latest_results (List[Result]): Most recently collected user results

    Returns:
        List[float]: List of result runtimes in seconds
    """
    return [
        0 if result.time_taken is None else result.time_taken
        for result in latest_results
    ]


def pass_or_fail(latest_results: List[Result]) -> List[float]:
    """Generate numeric values for result successes or failures.

    Args:
        latest_results (List[Result]): Most recently collected user results

    Returns:
        List[float]: 0 if fail, 1 if success
    """
    return [0 if result.exception is not None else 1 for result in latest_results]


def results_per_second(latest_results: List[Result]) -> List[float]:
    """Determine number of results collected in one second.

    Args:
        latest_results (List[Result]): Most recently collected user results

    Returns:
        List[float]: Single element array containing number of results per second
    """
    if len(latest_results) < 2:
        return []

    min_timestamp = latest_results[0].timestamp
    max_timestamp = latest_results[0].timestamp

    if min_timestamp is None or max_timestamp is None:
        return []

    for result in latest_results:
        if result.timestamp is not None and result.timestamp < min_timestamp:
            min_timestamp = result.timestamp

        if result.timestamp is not None and result.timestamp > max_timestamp:
            max_timestamp = result.timestamp

    seconds = math.ceil((max_timestamp - min_timestamp).total_seconds())

    return [len(latest_results) / seconds]
