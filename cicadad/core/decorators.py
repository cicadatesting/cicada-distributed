from typing import Any, Callable, Dict, List, Optional, Union

from cicadad.core.types import (
    ConsoleMetricDisplayer,
    ConsoleMetricDisplays,
    MetricCollector,
    LoadModelFn,
    UserLoopFn,
    ResultAggregatorFn,
    ResultVerifierFn,
    OutputTransformerFn,
)
from cicadad.core.scenario import Scenario
from cicadad.core.engine import Engine


def scenario(
    engine: Engine,
    name: str = None,
    raise_exception: bool = True,
):
    """Mark a function as a scenario

    Args:
        engine (Engine): Engine to attach scenario to
        name (str, optional): Name to give to scenario. Defaults to function name if None.
        raise_exception (bool): Raise exception if user loop fails.
    """

    def wrapper(fn):
        if isinstance(fn, Scenario):
            raise TypeError("Function is already a Scenario")

        scenario = make_scenario(name=name or fn.__qualname__, fn=fn)

        scenario.raise_exception = raise_exception

        engine.add_scenario(scenario)

        return scenario

    return wrapper


def user_loop(user_loop_fn: UserLoopFn):
    """Function to handle how the user function is run

    Args:
        user_loop_fn (UserLoopFn): User defined user loop function
    """

    def wrapper(fn):
        _set_scenario_attribute(fn, "user_loop", user_loop_fn)

        return fn

    return wrapper


def users_per_instance(users_per_instance: int):
    """Sets how many users can fit inside a single user manager instance.
    Default is 50 users per instance

    Args:
        users_per_instance (int): Number of users to fit in a single instance
    """

    def wrapper(fn):
        _set_scenario_attribute(fn, "users_per_instance", users_per_instance)

        return fn

    return wrapper


def load_model(load_model_fn: LoadModelFn):
    """Handle how scenario is run with regards to starting users and administering work.

    Args:
        load_model_fn (LoadModelFn): User defined load model function
    """

    def wrapper(fn):
        _set_scenario_attribute(fn, "load_model", load_model_fn)

        return fn

    return wrapper


def dependency(dep: Scenario):
    """Set a scenario as a dependency for this scenario to run.

    Args:
        dep (Scenario): Scenario this function is dependent on being successful
    """

    def wrapper(fn):
        dependencies = _get_scenario_attribute(fn, "dependencies")
        entry = [dep]

        if dependencies is None:
            _set_scenario_attribute(fn, "dependencies", entry)
        else:
            _set_scenario_attribute(fn, "dependencies", dependencies + entry)

        return fn

    return wrapper


def result_aggregator(aggregator_fn: ResultAggregatorFn):
    """Transform previous aggregate and list of results into an aggregated single result.

    Called by load model function.

    Args:
        aggregator_fn (ResultAggregatorFn): Aggregator function
    """

    def wrapper(fn):
        _set_scenario_attribute(fn, "result_aggregator", aggregator_fn)

        return fn

    return wrapper


def result_verifier(verifier_fn: ResultVerifierFn):
    """Create error messages for errors found in a list of results.

    Called by load model function.

    Args:
        verifier_fn (ResultVerifierFn): Verifier function
    """

    def wrapper(fn):
        _set_scenario_attribute(fn, "result_verifier", verifier_fn)

        return fn

    return wrapper


def output_transformer(transformer_fn: OutputTransformerFn):
    """Transform the aggregated result of the scenario after load model is called.

    Args:
        transformer_fn (OutputTransformerFn): Transformer function
    """

    def wrapper(fn):
        _set_scenario_attribute(fn, "output_transformer", transformer_fn)

        return fn

    return wrapper


def metrics_collectors(collectors: List[MetricCollector]):
    """Set list of metrics collectors functions used to save metric data about
    user results reported during run of a scenario

    Args:
        collectors (List[MetricCollector]): Collector functions given to be given a list of results
    """

    def wrapper(fn):
        _set_scenario_attribute(fn, "metric_collectors", collectors)

        return fn

    return wrapper


def metrics_collector(collector: MetricCollector):
    """Add a collector function to parse and send metrics from scenario.

    Args:
        collector (MetricCollector): Collector function
    """

    def wrapper(fn):
        collectors = _get_scenario_attribute(fn, "metric_collectors")
        additional_collectors = _get_additional_scenario_attribute(
            fn, "additional_metric_collectors"
        )
        entry = [collector]

        if collectors is None and additional_collectors is None:
            _set_additional_scenario_attribute(
                fn, "additional_metric_collectors", entry
            )
        elif collectors is None:
            _set_additional_scenario_attribute(
                fn, "additional_metric_collectors", additional_collectors + entry
            )
        else:
            _set_scenario_attribute(fn, "metric_collectors", collectors + entry)

        return fn

    return wrapper


def console_metric_displays(displays: ConsoleMetricDisplays):
    """Set map of names to metric displays for scenario.

    Args:
        displays (ConsoleMetricDisplays): Map of names to console metric display getters
    """

    def wrapper(fn):
        _set_scenario_attribute(fn, "console_metric_displays", displays)

        return fn

    return wrapper


def console_metric_display(display_name: str, displayer: ConsoleMetricDisplayer):
    """Add display function to console metric displays

    Args:
        display_name (str): Name of metric when displayed in console
        displayer (ConsoleMetricDisplayer): Function to retrive metric data and return printable string in console
    """

    def wrapper(fn):
        metric_displays = _get_scenario_attribute(fn, "console_metric_displays")
        additional_metric_displays = _get_additional_scenario_attribute(
            fn, "additional_console_metric_displays"
        )

        if metric_displays is None and additional_metric_displays is None:
            _set_additional_scenario_attribute(
                fn, "additional_console_metric_displays", {display_name: displayer}
            )
        elif metric_displays is None:
            additional_metric_displays[display_name] = displayer
            _set_additional_scenario_attribute(
                fn, "additional_console_metric_displays", additional_metric_displays
            )
        else:
            metric_displays[display_name] = displayer
            _set_scenario_attribute(
                fn, "console_metric_displays", additional_metric_displays
            )

        return fn

    return wrapper


def tag(tag: str):
    """Add a tag to a scenario.

    Tags allow for a test run to only cover certain scenarios.

    Args:
        tag (str): Tag name to add to scenario
    """

    def wrapper(fn):
        tags = _get_scenario_attribute(fn, "tags")
        entry = [tag]

        if tags is None:
            _set_scenario_attribute(fn, "tags", entry)
        else:
            _set_scenario_attribute(fn, "tags", tags + entry)

        return fn

    return wrapper


def make_scenario(name: str, fn: Callable):
    if hasattr(fn, "__scenario_attribute__"):
        scenario_kwargs = fn.__scenario_attribute__  # type: ignore
        del fn.__scenario_attribute__  # type: ignore
    else:
        scenario_kwargs = {}

    scenario = Scenario(name=name, fn=fn, **scenario_kwargs)

    additional_console_metric_displays: Optional[
        Dict[str, ConsoleMetricDisplayer]
    ] = _get_additional_scenario_attribute(fn, "additional_console_metric_displays")
    additional_metric_collectors = _get_additional_scenario_attribute(
        fn, "additional_metric_collectors"
    )

    if (
        additional_console_metric_displays is not None
        and scenario.console_metric_displays is not None
    ):
        for display in additional_console_metric_displays:
            scenario.console_metric_displays[
                display
            ] = additional_console_metric_displays[display]

    if additional_metric_collectors is not None:
        for collector in additional_metric_collectors:
            scenario.metric_collectors.append(collector)

    if hasattr(fn, "__additional_scenario_attribute__"):
        del fn.__additional_scenario_attribute__  # type: ignore

    return scenario


def _get_scenario_attribute(obj: Union[Scenario, Callable], name: str):
    if hasattr(obj, name):
        return getattr(obj, name)

    if hasattr(obj, "__scenario_attribute__"):
        return obj.__scenario_attribute__.get(name)  # type: ignore

    return None


def _set_scenario_attribute(obj: Union[Scenario, Callable], name: str, value: Any):
    if hasattr(obj, name):
        return setattr(obj, name, value)

    if hasattr(obj, "__scenario_attribute__"):
        obj.__scenario_attribute__[name] = value  # type: ignore
        return

    obj.__scenario_attribute__ = {name: value}  # type: ignore


def _get_additional_scenario_attribute(obj: Union[Scenario, Callable], name: str):
    if hasattr(obj, name):
        return getattr(obj, name)

    if hasattr(obj, "__additional_scenario_attribute__"):
        return obj.__additional_scenario_attribute__.get(name)  # type: ignore

    return None


def _set_additional_scenario_attribute(
    obj: Union[Scenario, Callable], name: str, value: Any
):
    if hasattr(obj, name):
        return setattr(obj, name, value)

    if hasattr(obj, "__additional_scenario_attribute__"):
        obj.__additional_scenario_attribute__[name] = value  # type: ignore
        return

    obj.__additional_scenario_attribute__ = {name: value}  # type: ignore
