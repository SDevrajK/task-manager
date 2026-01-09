"""Main Textual TUI application for task manager."""

from datetime import datetime
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Button
from textual.binding import Binding
from textual.screen import Screen

from task_manager.config import Config
from task_manager.commands import TaskCommands
from task_manager.queries import TaskQuery
from task_manager.storage import TaskStorage
from task_manager.models import Task
from task_manager.claude_integration import ClaudeIntegration
from task_manager.tui.screens.action_dialog import ActionDialog
from task_manager.tui.screens.create_task_screen import CreateTaskScreen
from task_manager.tui.screens.edit_notes_screen import EditNotesScreen
from task_manager.tui.screens.edit_task_screen import EditTaskScreen
from task_manager.tui.screens.search_screen import SearchScreen
from task_manager.tui.screens.project_management_screen import ProjectManagementScreen


class TaskListDisplay(Static):
    """Widget for displaying scrollable task list with headers."""

    DEFAULT_CSS = """
    TaskListDisplay {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
        overflow: auto;
    }
    """

    def __init__(self, tasks=None, storage=None, *args, **kwargs):
        """Initialize task list widget."""
        super().__init__(*args, **kwargs)
        self.tasks = tasks or []
        self.storage = storage
        self.project_codes = storage.get_project_codes() if storage else {}

    def render(self) -> str:
        """Render the task list with headers."""
        lines = []

        # Refresh project codes in case they changed
        if self.storage:
            self.project_codes = self.storage.get_project_codes()

        # Add header row
        header = f"{'ID':>3s} Pr {'Project':<6s} {'Status':<7s}  {'Deadline':10s}  {'Description'}"
        lines.append(f"[bold cyan]{header}[/]")
        lines.append("[dim]" + "─" * 80 + "[/]")

        if not self.tasks:
            lines.append("[dim]No tasks[/dim]")
            return "\n".join(lines)

        for task in self.tasks:
            status_color = self._get_status_color(task.status)
            priority_sym = {"high": "🔴", "medium": "🟡", "low": "🔵"}.get(task.priority, "⚪")
            deadline = task.deadline if task.deadline else "-"

            # Truncate description to 40 chars without wrapping
            desc = task.description[:40]
            if len(task.description) > 40:
                desc = desc.rstrip() + "…"

            project_code = self.project_codes.get(task.project, task.project[:5])
            status_display = task.status.replace("IN_PROGRESS", "IN_PROG")
            line = (
                f"{task.id:>3d} {priority_sym} {project_code:<6s} "
                f"[{status_color}]{status_display:<7s}[/]  "
                f"{deadline:10s}  "
                f"{desc}"
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
            f"[bold]Description:[/]",
            f"{self.selected_task.description}",
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
        Binding("tab", "cycle_view", "Cycle [Tab]"),
        Binding("ctrl+n", "new_task", "New [Ctrl-N]"),
        Binding("ctrl+e", "show_actions", "Actions [Ctrl-E]"),
        Binding("ctrl+f", "search", "Search [Ctrl-F]"),
        Binding("ctrl+s", "cycle_sort", "Sort [Ctrl-S]"),
        Binding("ctrl+l", "manage_projects", "Projects [Ctrl-L]"),
        Binding("escape", "clear_filter", "Clear Filter [Esc]"),
        Binding("ctrl+q", "quit", "Quit [Ctrl-Q]"),
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

    #bottom-section {
        height: auto;
        border-top: solid $primary;
    }

    #footer {
        height: 1;
        background: $panel;
    }
    """

    def __init__(self, config: Config, *args, **kwargs):
        """Initialize the screen."""
        super().__init__(*args, **kwargs)
        self.config = config
        self.commands = TaskCommands(config)
        self.storage = TaskStorage(config)
        self.claude = ClaudeIntegration(config)
        self.tasks = []
        self.bucket = None
        self.current_filter_index = 0
        self.filter_modes = ["All", "TODO", "IN_PROGRESS", "DONE", "BLOCKED"]
        self.task_list_display = None
        self.task_detail_display = None
        self.filter_bar = None
        self.selected_task_index = 0
        self.search_filter = None  # Track active search filter
        self.sort_modes = ["id", "deadline", "priority", "status"]
        self.current_sort_index = 0  # Default: by ID

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("[bold]TASK MANAGER[/bold]", id="header")

        with Horizontal(id="main"):
            with ScrollableContainer():
                self.task_list_display = TaskListDisplay(storage=self.storage)
                yield self.task_list_display
            self.task_detail_display = TaskDetailDisplay()
            yield self.task_detail_display

        with Vertical(id="bottom-section"):
            self.filter_bar = TaskFilterBar(self.config)
            yield self.filter_bar
            yield Static(
                "[bold cyan]↑↓[/] navigate | [bold cyan]Tab[/] cycle | [bold cyan]Ctrl-F[/] search | [bold cyan]Ctrl-S[/] sort | [bold cyan]Esc[/] clear | [bold cyan]Ctrl-E[/] actions | [bold cyan]Ctrl-N[/] new | [bold cyan]Ctrl-L[/] projects | [bold cyan]Ctrl-Q[/] quit",
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
        if current_status == "All":
            self.tasks = self.bucket.tasks
        else:
            self.tasks = TaskQuery.filter(self.bucket, status=current_status)

        # Apply search filter if active
        if self.search_filter:
            search_query = self.search_filter.lower()
            project_codes = self.storage.get_project_codes()
            self.tasks = [
                task for task in self.tasks
                if search_query in task.description.lower()
                or task.project == self.search_filter  # Exact match for project ID
                or search_query in project_codes.get(task.project, task.project[:5]).lower()
            ]

        # Apply sorting
        self._sort_tasks()

        self.selected_task_index = 0  # Reset selection on filter change

        if self.task_list_display:
            self.task_list_display.update_tasks(self.tasks)

        if self.filter_bar:
            self.filter_bar.update_counts(current_status)

        # Update detail display with first task if available
        self.update_detail_display()

    def _sort_tasks(self) -> None:
        """Sort tasks based on current sort mode."""
        sort_mode = self.sort_modes[self.current_sort_index]

        if sort_mode == "deadline":
            # Sort by deadline (None values last)
            self.tasks.sort(key=lambda t: (t.deadline is None, t.deadline))
        elif sort_mode == "priority":
            # Sort by priority (high -> medium -> low)
            priority_order = {"high": 0, "medium": 1, "low": 2}
            self.tasks.sort(key=lambda t: priority_order.get(t.priority, 3))
        elif sort_mode == "status":
            # Sort by status (TODO -> IN_PROGRESS -> DONE -> BLOCKED)
            status_order = {"TODO": 0, "IN_PROGRESS": 1, "DONE": 2, "BLOCKED": 3}
            self.tasks.sort(key=lambda t: status_order.get(t.status, 4))
        else:  # "id" is default
            self.tasks.sort(key=lambda t: t.id)

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
        current_status = self.filter_modes[self.current_filter_index]
        self.notify(f"Switched to {current_status} view", title="Filter")
        self.refresh_task_list()

    def action_new_task(self) -> None:
        """Create new task."""
        projects = self.storage.get_project_codes().keys()
        self.app.push_screen(
            CreateTaskScreen(list(projects)),
            callback=self._handle_create_task_result
        )

    def _handle_create_task_result(self, form_data: dict) -> None:
        """Handle result from create task screen."""
        if form_data is None:
            return

        try:
            task = self.commands.add(
                description=form_data["description"],
                project=form_data["project"],
                priority=form_data.get("priority", "medium"),
                deadline=form_data.get("deadline") or None,
                task_type=form_data.get("task_type", "work"),
                tags=form_data.get("tags", []),
                notes=form_data.get("notes") or None,
            )
            self.notify(f"Task #{task.id} created", title="Success")
            self.refresh_task_list()
        except Exception as e:
            self.notify(f"Error: {str(e)}", title="Error")

    def action_search(self) -> None:
        """Open search dialog."""
        self.app.push_screen(
            SearchScreen(self.bucket, self.storage.get_project_codes()),
            callback=self._handle_search_result
        )

    def action_clear_filter(self) -> None:
        """Clear the active search filter."""
        if self.search_filter:
            self.search_filter = None
            self.notify("Search filter cleared", title="Info")
            self.refresh_task_list()
        else:
            self.notify("No active filter", title="Info")

    def action_cycle_sort(self) -> None:
        """Cycle through sorting modes."""
        self.current_sort_index = (self.current_sort_index + 1) % len(self.sort_modes)
        sort_mode = self.sort_modes[self.current_sort_index]
        sort_labels = {
            "id": "ID",
            "deadline": "Deadline",
            "priority": "Priority",
            "status": "Status"
        }
        self.notify(f"Sorting by {sort_labels[sort_mode]}", title="Sort")
        self.refresh_task_list()

    def action_manage_projects(self) -> None:
        """Open project management dialog."""
        projects = self.storage.load_projects()
        self.app.push_screen(
            ProjectManagementScreen(projects, self.storage),
            callback=self._handle_project_management_result
        )

    def _handle_project_management_result(self, result) -> None:
        """Handle result from project management screen."""
        # Projects have been added/deleted, we may need to reload the bucket
        # But for now, just close the dialog - user can create new tasks with new projects
        pass

    def action_show_actions(self) -> None:
        """Show action dialog for selected task."""
        if not self.tasks or self.selected_task_index >= len(self.tasks):
            self.notify("No task selected", title="Error")
            return

        selected_task = self.tasks[self.selected_task_index]
        self.app.push_screen(
            ActionDialog(selected_task),
            callback=self._handle_action_result
        )

    def _handle_action_result(self, action: str) -> None:
        """Handle the result from the action dialog."""
        if action is None:
            return

        if not self.tasks or self.selected_task_index >= len(self.tasks):
            return

        task = self.tasks[self.selected_task_index]

        try:
            if action == "activate":
                self.commands.update(task.id, status="IN_PROGRESS")
                # Update CLAUDE.md
                success, msg = self.claude.activate_task(task, mode="quick")
                if success:
                    self.notify(msg, title="Success")
                else:
                    self.notify(f"Task activated. CLAUDE.md: {msg}", title="Info")
            elif action == "deactivate":
                self.commands.update(task.id, status="TODO")
                # Remove from CLAUDE.md
                success, msg = self.claude.deactivate_task(task)
                if success:
                    self.notify(msg, title="Success")
            elif action == "complete":
                self.commands.complete(task.id)
                # Move in CLAUDE.md
                success, msg = self.claude.complete_task(task)
                if success:
                    self.notify(msg, title="Success")
            elif action == "reopen":
                self.commands.update(task.id, status="TODO")
                self.notify(f"Task #{task.id} reopened", title="Success")
            elif action == "unblock":
                self.commands.update(task.id, status="TODO")
                self.notify(f"Task #{task.id} unblocked", title="Success")
            elif action == "delete":
                self.commands.delete(task.id, confirm=True)
                # Remove from CLAUDE.md
                success, msg = self.claude.deactivate_task(task)
                if success:
                    self.notify(msg, title="Success")
            elif action == "edit":
                self.app.push_screen(
                    EditTaskScreen(task),
                    callback=self._handle_edit_task_result
                )
                return

            # Refresh task list after action
            self.refresh_task_list()
        except Exception as e:
            self.notify(f"Error: {str(e)}", title="Error")

    def _handle_edit_notes_result(self, notes: str) -> None:
        """Handle result from edit notes screen."""
        if notes is None:
            return

        if not self.tasks or self.selected_task_index >= len(self.tasks):
            return

        task = self.tasks[self.selected_task_index]

        try:
            self.commands.update(task.id, notes=notes)
            self.notify(f"Notes updated for Task #{task.id}", title="Success")
            self.refresh_task_list()
        except Exception as e:
            self.notify(f"Error: {str(e)}", title="Error")

    def _handle_edit_task_result(self, form_data: dict) -> None:
        """Handle result from edit task screen."""
        if form_data is None:
            return

        try:
            # Get the task ID from the most recent selected task before we refresh
            if self.tasks and self.selected_task_index < len(self.tasks):
                task_id = self.tasks[self.selected_task_index].id
            else:
                return

            # Convert deadline to None if empty
            deadline = form_data.get("deadline") or None

            self.commands.update(
                task_id,
                description=form_data.get("description"),
                deadline=deadline,
                priority=form_data.get("priority"),
                task_type=form_data.get("task_type"),
                tags=form_data.get("tags", []),
                notes=form_data.get("notes"),
            )

            # Reload the bucket to get fresh data
            self.bucket = self.storage.load_bucket()
            self.notify(f"Task #{task_id} updated", title="Success")
            # Use call_later to ensure refresh happens after screen stack is updated
            self.app.call_later(self.refresh_task_list)
        except Exception as e:
            self.notify(f"Error updating task: {str(e)}", title="Error")
            import traceback
            traceback.print_exc()

    def _handle_search_result(self, result: dict) -> None:
        """Handle result from search screen."""
        if result is None:
            # Clear search filter if no result selected
            self.search_filter = None
            self.notify("Search cleared", title="Info")
        else:
            # Set search filter based on result type
            if result["type"] == "task":
                self.search_filter = result["task"].description
                self.notify(f"Filtering by: {result['task'].description}", title="Search")
            elif result["type"] == "project":
                self.search_filter = result["project"]
                self.notify(f"Filtering by project: {result['project']}", title="Search")

        self.refresh_task_list()

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
