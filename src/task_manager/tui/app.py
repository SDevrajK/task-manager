"""Main Textual TUI application for task manager."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Button
from textual.binding import Binding
from textual.screen import Screen

from task_manager.config import Config
from task_manager.commands import TaskCommands
from task_manager.queries import TaskQuery
from task_manager.storage import TaskStorage
from task_manager.models import Task


class TaskListDisplay(Static):
    """Widget for displaying task list."""

    DEFAULT_CSS = """
    TaskListDisplay {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
    }
    """

    def __init__(self, tasks=None, *args, **kwargs):
        """Initialize task list widget."""
        super().__init__(*args, **kwargs)
        self.tasks = tasks or []

    def render(self) -> str:
        """Render the task list."""
        if not self.tasks:
            return "[dim]No tasks[/dim]"

        lines = []
        for task in self.tasks[:50]:  # Show up to 50 tasks
            status_color = self._get_status_color(task.status)
            priority_sym = {"high": "🔴", "medium": "🟡", "low": "🔵"}.get(task.priority, "⚪")
            deadline = task.deadline if task.deadline else "-"

            line = (
                f"{task.id:3d} {priority_sym} "
                f"[{status_color}]{task.status:12s}[/] "
                f"{deadline:10s} "
                f"{task.description[:45]}"
            )
            lines.append(line)

        return "\n".join(lines)

    def update_tasks(self, tasks):
        """Update the task list."""
        self.tasks = tasks
        self.refresh()

    @staticmethod
    def _get_status_color(status: str) -> str:
        """Get color for status."""
        colors = {
            "TODO": "blue",
            "IN_PROGRESS": "yellow",
            "DONE": "green",
            "BLOCKED": "red",
        }
        return colors.get(status, "white")


class TaskDetailDisplay(Static):
    """Widget for displaying task details."""

    DEFAULT_CSS = """
    TaskDetailDisplay {
        width: 50;
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }
    """

    def __init__(self, selected_task=None, *args, **kwargs):
        """Initialize task detail widget."""
        super().__init__(*args, **kwargs)
        self.selected_task = selected_task

    def render(self) -> str:
        """Render task details."""
        if not self.selected_task:
            return "[dim]Select a task[/dim]"

        lines = [
            f"[bold yellow]Task #{self.selected_task.id}[/bold yellow]",
            "",
            f"[bold]Project:[/] {self.selected_task.project}",
            f"[bold]Status:[/] {self.selected_task.status}",
            f"[bold]Priority:[/] {self.selected_task.priority}",
        ]

        if self.selected_task.deadline:
            lines.append(f"[bold]Deadline:[/] {self.selected_task.deadline}")

        if self.selected_task.notes:
            lines.append("")
            lines.append(f"[bold]Notes:[/]")
            lines.append(f"{self.selected_task.notes}")

        if self.selected_task.time_spent_hours:
            lines.append(f"[bold]Time spent:[/] {self.selected_task.time_spent_hours}h")

        return "\n".join(lines)

    def update_task(self, task):
        """Update the displayed task."""
        self.selected_task = task
        self.refresh()


class TaskFilterBar(Static):
    """Widget for showing task counts and current filter."""

    DEFAULT_CSS = """
    TaskFilterBar {
        height: 1;
        width: 1fr;
        background: $panel;
        content-align: left middle;
    }
    """

    def __init__(self, config, *args, **kwargs):
        """Initialize filter bar."""
        super().__init__(*args, **kwargs)
        self.config = config
        self.storage = TaskStorage(config)

    def update_counts(self, current_filter: str):
        """Update task counts and filter display."""
        bucket = self.storage.load_bucket()
        todo = len(TaskQuery.filter(bucket, status="TODO"))
        in_progress = len(TaskQuery.filter(bucket, status="IN_PROGRESS"))
        done = len(TaskQuery.filter(bucket, status="DONE"))
        blocked = len(TaskQuery.filter(bucket, status="BLOCKED"))

        status_line = (
            f"[bright_blue]Pending:[/] {todo} | "
            f"[yellow]Active:[/] {in_progress} | "
            f"[green]Done:[/] {done} | "
            f"[red]Blocked:[/] {blocked} | "
            f"[cyan][{current_filter}][/]"
        )
        self.update(status_line)


class TaskManagerScreen(Screen):
    """Main task manager screen."""

    BINDINGS = [
        Binding("up", "select_previous", "Previous [↑]"),
        Binding("down", "select_next", "Next [↓]"),
        Binding("ctrl+h", "cycle_view", "Cycle [Ctrl-H]"),
        Binding("ctrl+n", "new_task", "New [Ctrl-N]"),
        Binding("ctrl+f", "search", "Search [Ctrl-F]"),
        Binding("q", "quit", "Quit [q]"),
    ]

    CSS = """
    Screen {
        layout: vertical;
    }

    #header {
        height: 1;
        background: $panel;
        border-bottom: solid $primary;
        dock: top;
    }

    #main {
        height: 1fr;
    }

    #footer {
        height: 1;
        background: $panel;
        border-top: solid $primary;
        dock: bottom;
    }
    """

    def __init__(self, config: Config, *args, **kwargs):
        """Initialize the screen."""
        super().__init__(*args, **kwargs)
        self.config = config
        self.commands = TaskCommands(config)
        self.storage = TaskStorage(config)
        self.tasks = []
        self.bucket = None
        self.current_filter_index = 0
        self.filter_modes = ["TODO", "IN_PROGRESS", "DONE", "BLOCKED"]
        self.task_list_display = None
        self.task_detail_display = None
        self.filter_bar = None
        self.selected_task_index = 0

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("[bold]TASK MANAGER[/bold]", id="header")

        with Horizontal(id="main"):
            self.task_list_display = TaskListDisplay()
            yield self.task_list_display
            self.task_detail_display = TaskDetailDisplay()
            yield self.task_detail_display

        self.filter_bar = TaskFilterBar(self.config)
        yield self.filter_bar
        yield Static(
            "[dim]↑↓ navigate | Ctrl-H cycle | Ctrl-N new | Ctrl-F search | q quit[/dim]",
            id="footer",
        )

    def on_mount(self) -> None:
        """Handle mount event."""
        self.bucket = self.storage.load_bucket()
        self.refresh_task_list()

    def refresh_task_list(self) -> None:
        """Refresh task list with current filter."""
        if not self.bucket:
            self.bucket = self.storage.load_bucket()

        current_status = self.filter_modes[self.current_filter_index]
        self.tasks = TaskQuery.filter(self.bucket, status=current_status)
        self.selected_task_index = 0  # Reset selection on filter change

        if self.task_list_display:
            self.task_list_display.update_tasks(self.tasks)

        if self.filter_bar:
            self.filter_bar.update_counts(current_status)

        # Update detail display with first task if available
        self.update_detail_display()

    def update_detail_display(self) -> None:
        """Update detail pane with currently selected task."""
        if self.tasks and self.selected_task_index < len(self.tasks):
            selected_task = self.tasks[self.selected_task_index]
            if self.task_detail_display:
                self.task_detail_display.update_task(selected_task)
        elif self.task_detail_display:
            self.task_detail_display.update_task(None)

    def action_select_previous(self) -> None:
        """Select previous task."""
        if self.tasks:
            self.selected_task_index = max(0, self.selected_task_index - 1)
            self.update_detail_display()

    def action_select_next(self) -> None:
        """Select next task."""
        if self.tasks:
            self.selected_task_index = min(len(self.tasks) - 1, self.selected_task_index + 1)
            self.update_detail_display()

    def action_cycle_view(self) -> None:
        """Cycle through filter views."""
        self.current_filter_index = (self.current_filter_index + 1) % len(self.filter_modes)
        self.refresh_task_list()

    def action_new_task(self) -> None:
        """Create new task."""
        self.notify("New task feature coming soon", title="TODO")

    def action_search(self) -> None:
        """Search tasks."""
        self.notify("Search feature coming soon", title="TODO")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()


class TaskManagerApp:
    """Main application entry point."""

    def __init__(self, config: Config):
        """Initialize the app."""
        self.config = config

    def run(self) -> None:
        """Run the TUI application."""
        from textual.app import App

        config = self.config

        class TaskManagerTUI(App):
            """Textual app wrapper."""

            BINDINGS = [
                Binding("q", "quit", "Quit"),
            ]

            def on_mount(self) -> None:
                """Mount the main screen."""
                self.push_screen(TaskManagerScreen(config))

        app = TaskManagerTUI()
        app.run()
