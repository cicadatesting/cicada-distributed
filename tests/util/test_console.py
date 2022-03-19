from rich.align import Align
from rich.panel import Panel
from rich.spinner import Spinner

from cicadad.util import console


def test_task_display_spinner():
    task_display = console.TaskDisplay("task_name", "abc")

    renderable = task_display.get_renderable()

    assert isinstance(renderable, Spinner)


def test_task_display_succeeded():
    task_display = console.TaskDisplay("task_name", "abc")
    task_display.set_succeeded()

    renderable = task_display.get_renderable()

    assert isinstance(renderable, str)


def test_task_display_failed():
    task_display = console.TaskDisplay("task_name", "abc")
    task_display.set_failed()

    renderable = task_display.get_renderable()

    assert isinstance(renderable, str)


def test_metrics_display():
    metrics_display = console.MetricDisplay("task_name")

    metrics_display.update_metrics({"a": "a", "b": "b", "c": "c"})

    table = metrics_display.get_renderable()

    assert table.row_count == 3


def test_tasks_panel_no_tasks():
    tasks_panel = console.TasksPanel()

    assert tasks_panel.get_renderable() is None


def test_tasks_panel_running_task():
    tasks_panel = console.TasksPanel()

    tasks_panel.add_running_task("task_name", "abc")

    assert isinstance(tasks_panel.get_renderable().renderable.renderables[0], Spinner)


def test_tasks_panel_multiple_tasks():
    tasks_panel = console.TasksPanel()

    tasks_panel.add_running_task("task_name_a", "abc")
    tasks_panel.add_running_task("task_name_b", "def")
    tasks_panel.add_running_task("task_name_c", "ghi")

    assert len(tasks_panel.get_renderable().renderable.renderables) == 3


def test_tasks_panel_running_succeeded():
    tasks_panel = console.TasksPanel()

    tasks_panel.add_running_task("task_name", "abc")
    tasks_panel.update_task_success("task_name")

    assert isinstance(tasks_panel.get_renderable().renderable.renderables[0], str)


def test_tasks_panel_running_failed():
    tasks_panel = console.TasksPanel()

    tasks_panel.add_running_task("task_name", "abc")
    tasks_panel.update_task_failed("task_name")

    assert isinstance(tasks_panel.get_renderable().renderable.renderables[0], str)


def test_metrics_panel_empty():
    metrics_panel = console.MetricsPanel()

    assert metrics_panel.get_renderable() is None


def test_metrics_panel_multiple():
    metrics_panel = console.MetricsPanel()

    metrics_panel.add_metric("task_a", {"a": "a"})
    metrics_panel.add_metric("task_b", {"b": "b"})
    metrics_panel.add_metric("task_c", {"c": "c"})

    assert len(metrics_panel.get_renderable().renderable.renderables) == 3


def test_live_panel_empty():
    tasks_panel = console.TasksPanel()
    metrics_panel = console.MetricsPanel()

    live_panel = console.LivePanel("test_name", tasks_panel, metrics_panel)

    assert isinstance(live_panel.get_renderable(), Align)


def test_live_panel_populated():
    tasks_panel = console.TasksPanel()
    metrics_panel = console.MetricsPanel()

    live_panel = console.LivePanel("test_name", tasks_panel, metrics_panel)

    tasks_panel.add_running_task("task_name", "abc")

    assert isinstance(live_panel.get_renderable(), Panel)
