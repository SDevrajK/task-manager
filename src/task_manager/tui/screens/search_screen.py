"""Search screen for filtering tasks by description or project."""

from textual.screen import ModalScreen
from textual.containers import Container, Vertical
from textual.widgets import Input, Label, Static
from textual.binding import Binding

from task_manager.models import TaskBucket


class SearchResultsList(Static):
    """Display search results."""

    DEFAULT_CSS = """
    SearchResultsList {
        width: 1fr;
        height: auto;
        overflow: auto;
    }
    """

    def __init__(self, results=None, *args, **kwargs):
        """Initialize results list."""
        super().__init__(*args, **kwargs)
        self.results = results or []

    def render(self) -> str:
        """Render search results."""
        if not self.results:
            return "[dim]No matches[/dim]"

        lines = []
        for result in self.results[:10]:  # Limit to 10 results
            if "task" in result:
                task = result["task"]
                lines.append(f"[cyan]Task #{task.id}[/cyan]: {task.description[:40]}")
            elif "project" in result:
                project = result["project"]
                lines.append(f"[yellow]Project[/yellow]: {project}")

        return "\n".join(lines)

    def update_results(self, results):
        """Update the results."""
        self.results = results
        self.refresh()


class SearchScreen(ModalScreen):
    """Modal screen for searching tasks and projects."""

    CSS = """
    SearchScreen {
        align: center middle;
    }

    #search-dialog {
        width: 70;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1;
    }

    #title {
        width: 1fr;
        height: auto;
        content-align: center middle;
        margin-bottom: 1;
    }

    #search-input {
        width: 1fr;
        margin-bottom: 1;
    }

    #results {
        width: 1fr;
        height: 10;
        margin-bottom: 1;
    }

    #help {
        width: 1fr;
        height: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "select", "Select"),
    ]

    def __init__(self, bucket: TaskBucket, project_codes: dict):
        """Initialize search screen."""
        super().__init__()
        self.bucket = bucket
        self.project_codes = project_codes
        self.search_query = ""
        self.results = []

    def compose(self):
        """Create search interface."""
        with Container(id="search-dialog"):
            yield Label("Search tasks or projects", id="title")

            yield Input(
                id="search-input",
                placeholder="Type to search task descriptions or project names..."
            )

            self.results_display = SearchResultsList()
            yield self.results_display

            yield Label("[dim]↑↓ navigate | Enter select | Esc cancel[/dim]", id="help")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes and update results."""
        self.search_query = event.value.lower()
        self.results = self._search(self.search_query)
        self.results_display.update_results(self.results)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input field."""
        self.action_select()

    def _search(self, query: str) -> list:
        """Search tasks and projects by query."""
        if not query or len(query) < 1:
            return []

        results = []

        # Search tasks by description
        for task in self.bucket.tasks:
            if query in task.description.lower():
                results.append({"type": "task", "task": task})

        # Search projects by code or name
        for task in self.bucket.tasks:
            project_code = self.project_codes.get(task.project, task.project[:5])
            if query in project_code.lower() or query in task.project.lower():
                if not any(r.get("project") == task.project for r in results):
                    results.append({"type": "project", "project": task.project})

        return results

    def action_cancel(self) -> None:
        """Cancel search."""
        self.dismiss(None)

    def action_select(self) -> None:
        """Select the first result."""
        if self.results:
            result = self.results[0]
            self.dismiss(result)
        else:
            self.dismiss(None)
