import time

import requests
import uuid

import util

from cicadad.core.decorators import (
    dependency,
    load_model,
    user_loop,
    scenario,
    result_aggregator,
    output_transformer,
)
from cicadad.core.engine import Engine
from cicadad.core.scenario import n_iterations, n_seconds, while_alive, load_stages

engine = Engine()


@scenario(engine)
# @load_model(n_iterations(100, 1, timeout=None))
# @load_model(
#     load_stages(
#         n_seconds(30, 10, skip_scaledown=True),
#         n_seconds(30, 20, skip_scaledown=True),
#         n_seconds(30, 30, skip_scaledown=True),
#     )
# )
# @user_loop(while_alive())
# @result_aggregator(util.post_user_aggregator)
# @output_transformer(util.print_get_user_output)
def post_user(context):
    email = f"{str(uuid.uuid4())[:8]}@gmail.com"

    response = requests.post(
        url="http://172.17.0.1:8080/users",
        # url="http://api:8080/users",
        json={
            "name": "jeremy",
            "age": 23,
            "email": email,
        },
    )

    assert response.status_code == 200
    body = response.json()

    return {"email": email, "id": body["id"]}


@scenario(engine)
@dependency(post_user)
def post_user_duplicate_email(context):
    response = requests.post(
        url="http://172.17.0.1:8080/users",
        json={
            "name": "jeremy",
            "age": 23,
            "email": context["post_user"]["output"]["email"],
        },
    )

    assert response.status_code == 400, f"Status code is {response.status_code}"


@scenario(engine)
@dependency(post_user)
def get_user(context):
    response = requests.get(
        url=f"http://172.17.0.1:8080/users/{context['post_user']['output']['id']}",
    )

    assert response.status_code == 200


@scenario(engine)
def get_user_not_found(context):
    response = requests.get(
        url="http://172.17.0.1:8080/users/0",
    )

    assert response.status_code == 404


if __name__ == "__main__":
    engine.start()
