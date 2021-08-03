from typing import Any, Callable, Union

from cicadad.core.scenario import (
    Scenario,
    LoadModelFn,
    UserLoopFn,
    ResultAggregatorFn,
    ResultVerifierFn,
    OutputTransformerFn,
)
from cicadad.core.engine import Engine


def scenario(engine: Engine, name: str = None):
    """Mark a function as a scenario

    Args:
        engine (Engine): Engine to attach scenario to
        name (str, optional): Name to give to scenario. Defaults to function name if None.
    """

    def wrapper(fn):
        if isinstance(fn, Scenario):
            raise TypeError("Function is already a Scenario")

        scenario = make_scenario(name=name or fn.__qualname__, fn=fn)

        engine.add_scenario(scenario)

        return scenario

    return wrapper


def user_loop(user_loop_fn: UserLoopFn):
    """Function to handle how the user function is run

    Args:
        user_loop_fn (UserLoopFn): User defined user loop function
    """

    def wrapper(fn):
        set_scenario_attribute(fn, "user_loop", user_loop_fn)

        return fn

    return wrapper


def users_per_container(users_per_container: int):
    """Sets how many users can fit inside a single user manager container.
    Default is 50 users per container

    Args:
        users_per_container (int): Number of users to fit in a single container
    """

    def wrapper(fn):
        set_scenario_attribute(fn, "users_per_container", users_per_container)

        return fn

    return wrapper


def load_model(load_model_fn: LoadModelFn):
    """Function to handle how scenario is run with regards to starting users and
    administering work

    Args:
        load_model_fn (LoadModelFn): User defined load model function
    """

    def wrapper(fn):
        set_scenario_attribute(fn, "load_model", load_model_fn)

        return fn

    return wrapper


def dependency(dep: Scenario):
    """Set a scenario as a dependency for this scenario to run

    Args:
        dep (Scenario): Scenario this function is dependent on being successful
    """

    def wrapper(fn):
        dependencies = get_scenario_attribute(fn, "dependencies")
        entry = [dep]

        if dependencies is None:
            set_scenario_attribute(fn, "dependencies", entry)
        else:
            set_scenario_attribute(fn, "dependencies", dependencies + entry)

        return fn

    return wrapper


def result_aggregator(aggregator_fn: ResultAggregatorFn):
    """Transform previous aggregate and list of results into an aggregated
    single result. Called by load model function

    Args:
        aggregator_fn (ResultAggregatorFn): Aggregator function
    """

    def wrapper(fn):
        set_scenario_attribute(fn, "result_aggregator", aggregator_fn)

        return fn

    return wrapper


def result_verifier(verifier_fn: ResultVerifierFn):
    """Create error messages for errors found in a list of results. Called by
    load model function

    Args:
        verifier_fn (ResultVerifierFn): Verifier function
    """

    def wrapper(fn):
        set_scenario_attribute(fn, "result_verifier", verifier_fn)

        return fn

    return wrapper


def output_transformer(transformer_fn: OutputTransformerFn):
    """Transform the aggregated result of the scenario after load model is
    called

    Args:
        transformer_fn (OutputTransformerFn): Transformer function
    """

    def wrapper(fn):
        set_scenario_attribute(fn, "output_transformer", transformer_fn)

        return fn

    return wrapper


def tag(tag: str):
    """Add a tag to a scenario. Tags allow for a test run to only cover certain
    scenarios.

    Args:
        tag (str): Tag name to add to scenario
    """

    def wrapper(fn):
        tags = get_scenario_attribute(fn, "tags")
        entry = [tag]

        if tags is None:
            set_scenario_attribute(fn, "tags", entry)
        else:
            set_scenario_attribute(fn, "tags", tags + entry)

        return fn

    return wrapper


def make_scenario(name: str, fn: Callable):
    if hasattr(fn, "__scenario_attribute__"):
        scenario_kwargs = fn.__scenario_attribute__  # type: ignore
        del fn.__scenario_attribute__  # type: ignore
    else:
        scenario_kwargs = {}

    return Scenario(name=name, fn=fn, **scenario_kwargs)


def get_scenario_attribute(obj: Union[Scenario, Callable], name: str):
    if hasattr(obj, name):
        return getattr(obj, name)

    if hasattr(obj, "__scenario_attribute__"):
        return obj.__scenario_attribute__.get(name)  # type: ignore

    return None


def set_scenario_attribute(obj: Union[Scenario, Callable], name: str, value: Any):
    if hasattr(obj, name):
        return setattr(obj, name, value)

    if hasattr(obj, "__scenario_attribute__"):
        obj.__scenario_attribute__[name] = value  # type: ignore
        return

    obj.__scenario_attribute__ = {name: value}  # type: ignore
