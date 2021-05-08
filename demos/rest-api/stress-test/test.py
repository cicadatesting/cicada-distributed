from datetime import datetime
import requests
import uuid
import statistics

from cicadad.core.decorators import (
    scenario,
    load_model,
    user_loop,
    result_aggregator,
)
from cicadad.core.engine import Engine
from cicadad.core.scenario import (
    ramp_users_to_threshold,
    while_alive,
)

engine = Engine()


def runtime_aggregator(previous_aggregate, latest_results):
    if previous_aggregate is None:
        num_results = 0
        mean_ms = 0
    else:
        num_results = previous_aggregate["num_results"]
        mean_ms = previous_aggregate["mean_ms"]

    runtimes = []

    for result in latest_results:
        if result.exception is None:
            runtimes.append(result.output)

    if runtimes != []:
        latest_num_results = len(runtimes)
        latest_mean_ms = statistics.mean(runtimes)

        new_num_results = num_results + latest_num_results
        new_mean = ((mean_ms * num_results) + (latest_mean_ms * latest_num_results)) / (
            num_results + latest_num_results
        )
    else:
        new_num_results = num_results
        new_mean = mean_ms

    return {
        "num_results": new_num_results,
        "mean_ms": new_mean,
    }


@scenario(engine)
@load_model(
    ramp_users_to_threshold(
        initial_users=10,
        threshold_fn=lambda agg: agg is not None and agg["mean_ms"] > 100,
        next_users_fn=lambda n: n + 5,
    )
)
@user_loop(while_alive())
@result_aggregator(runtime_aggregator)
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
