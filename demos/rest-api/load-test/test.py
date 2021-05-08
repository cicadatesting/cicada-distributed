from datetime import datetime
import requests
import uuid
import statistics

from cicadad.core.decorators import (
    scenario,
    load_model,
    user_loop,
    result_aggregator,
    output_transformer,
)
from cicadad.core.engine import Engine
from cicadad.core.scenario import (
    n_seconds,
    iterations_per_second_limited,
    load_stages,
    n_users_ramping,
)

engine = Engine()


def runtime_aggregator(previous_aggregate, latest_results):
    if previous_aggregate is None:
        num_results = 0
        median_ms = 0
        avg_ms = 0
    else:
        num_results = previous_aggregate["num_results"]
        median_ms = previous_aggregate["median_ms"]
        avg_ms = previous_aggregate["avg_ms"]

    runtimes = []

    for result in latest_results:
        if result.exception is None:
            runtimes.append(result.output)

    if runtimes != []:
        latest_num_results = len(runtimes)
        latest_median_ms = statistics.median(runtimes)
        latest_avg_ms = statistics.mean(runtimes)

        new_num_results = num_results + latest_num_results
        new_median = (
            (median_ms * num_results) + (latest_median_ms * latest_num_results)
        ) / (num_results + latest_num_results)
        new_avg_ms = ((avg_ms * num_results) + (latest_avg_ms * latest_num_results)) / (
            num_results + latest_num_results
        )
    else:
        new_num_results = num_results
        new_median = median_ms
        new_avg_ms = avg_ms

    return {
        "num_results": new_num_results,
        "median_ms": new_median,
        "avg_ms": new_avg_ms,
    }


def print_aggregate(aggregate):
    if aggregate is not None:
        return f"""
    * Num Results: {aggregate['num_results']}
    * Median: {aggregate['median_ms']}
    * Average: {aggregate['avg_ms']}
    """


@scenario(engine)
@load_model(
    load_stages(
        n_users_ramping(60, 30, skip_scaledown=True),
        n_seconds(180, 30, skip_scaledown=True),
        n_users_ramping(60, 0, skip_scaledown=True),
    )
)
@user_loop(iterations_per_second_limited(4))
@result_aggregator(runtime_aggregator)
@output_transformer(print_aggregate)
def post_user(context):
    start = datetime.now()

    requests.post(
        url="http://172.17.0.1:8080/users",
        # url="http://api:8080/users",
        json={
            "name": "jeremy",
            "age": 23,
            "email": f"{str(uuid.uuid4())[:8]}@gmail.com",
        },
    )

    end = datetime.now()

    return ((end - start).seconds + (end - start).microseconds / 1000000) * 1000


if __name__ == "__main__":
    engine.start()
