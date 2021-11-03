from typing import Dict

from rich.align import Align
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Group
from rich.columns import Columns
from rich.spinner import Spinner
from rich.text import Text
from rich.table import Table
from rich import box


class TaskDisplay(object):
    def __init__(self, task_name: str, task_id: str):
        self.task_name = task_name
        self.task_id = task_id
        self.renderable = Spinner(
            "dots", text=Text(f"{task_name} ({task_id})"), style="green"
        )

    def set_succeeded(self):
        self.renderable = f"[green]:heavy_check_mark: {self.task_name} ({self.task_id})"

    def set_failed(self):
        self.renderable = f"[red]:x: {self.task_name} ({self.task_id})"

    def get_renderable(self):
        return self.renderable


class MetricDisplay(object):
    def __init__(self, scenario: str) -> None:
        self.scenario = scenario
        self.metrics: Dict[str, str] = {}

    def update_metrics(self, metrics: Dict[str, str]):
        self.metrics = metrics

    def get_renderable(self):
        table = Table(
            "name",
            "value",
            title=f"{self.scenario} metrics",
            box=box.HORIZONTALS,
            show_lines=False,
        )

        for name, value in self.metrics.items():
            table.add_row(name, value)

        return table


class TasksPanel(object):
    def __init__(self) -> None:
        self.tasks: Dict[str, TaskDisplay] = {}

    def add_running_task(self, name: str, scenario_id: str):
        self.tasks[name] = TaskDisplay(name, scenario_id)

    def update_task_success(self, name: str):
        self.tasks[name].set_succeeded()

    def update_task_failed(self, name: str):
        self.tasks[name].set_failed()

    def get_renderable(self):
        if self.tasks == {}:
            return None
        else:
            return Panel(
                Group(*(display.get_renderable() for display in self.tasks.values()))
            )


class MetricsPanel(object):
    def __init__(self) -> None:
        self.displays: Dict[str, MetricDisplay] = {}

    def add_metric(self, scenario: str, metrics: Dict[str, str]):
        if scenario not in self.displays:
            self.displays[scenario] = MetricDisplay(scenario)

        display = self.displays[scenario]

        display.update_metrics(metrics)

    def get_renderable(self):
        if self.displays == {}:
            return None

        return Panel(
            Columns([display.get_renderable() for display in self.displays.values()]),
            title="metrics",
        )


class LivePanel(object):
    def __init__(
        self,
        test_name: str,
        tasks_panel: TasksPanel,
        metrics_panel: MetricsPanel,
    ):
        self.test_name = test_name
        self.tasks_panel = tasks_panel
        self.metrics_panel = metrics_panel

    def get_renderable(self):
        tasks_panel_rendered = self.tasks_panel.get_renderable()
        metrics_panel_rendered = self.metrics_panel.get_renderable()

        if tasks_panel_rendered is None and metrics_panel_rendered is None:
            return Align(Text(f"Started Test: {self.test_name}"), align="center")

        layout = Layout()

        layout.split_row(
            Layout(name="running", visible=False),
            Layout(name="metrics", ratio=2, visible=False),
        )

        if metrics_panel_rendered is not None:
            layout["metrics"].visible = True
            layout["metrics"].update(metrics_panel_rendered)

        if tasks_panel_rendered is not None:
            layout["running"].visible = True
            layout["running"].update(tasks_panel_rendered)

        return Panel(layout, title=self.test_name)
