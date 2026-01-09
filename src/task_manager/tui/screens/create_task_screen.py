"""Create task screen for adding new tasks."""

from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Input, Label, Button, Select
from textual.binding import Binding


class CreateTaskScreen(ModalScreen):
    """Modal screen for creating a new task."""

    CSS = """
    CreateTaskScreen {
        align: center middle;
    }

    #create-dialog {
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

    .form-group {
        width: 1fr;
        height: auto;
        margin-bottom: 1;
    }

    .form-label {
        width: 1fr;
        height: 1;
        margin-bottom: 0;
    }

    Input {
        width: 1fr;
    }

    #buttons {
        width: 1fr;
        height: auto;
        margin-top: 1;
        layout: horizontal;
    }

    Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, projects: list = None):
        """Initialize create task screen."""
        super().__init__()
        self.projects = projects or []
        self.form_data = {
            "description": "",
            "project": "",
            "priority": "medium",
            "deadline": "",
            "task_type": "work",
            "tags": "",
            "notes": "",
        }

    def compose(self):
        """Create form fields."""
        with Container(id="create-dialog"):
            yield Label("Create New Task", id="title")

            with Vertical():
                # Description field
                with Vertical(classes="form-group"):
                    yield Label("Description (required):", classes="form-label")
                    yield Input(id="description", placeholder="What needs to be done?")

                # Project field
                with Vertical(classes="form-group"):
                    yield Label("Project (required):", classes="form-label")
                    project_options = [(p, p) for p in self.projects] if self.projects else [("nserc3", "nserc3")]
                    yield Select(
                        project_options,
                        id="project",
                        value=project_options[0][0] if project_options else "",
                    )

                # Priority field
                with Vertical(classes="form-group"):
                    yield Label("Priority:", classes="form-label")
                    yield Select(
                        [("Low", "low"), ("Medium", "medium"), ("High", "high")],
                        id="priority",
                        value="medium",
                    )

                # Deadline field
                with Vertical(classes="form-group"):
                    yield Label("Deadline (optional):", classes="form-label")
                    yield Input(id="deadline", placeholder="YYYY-MM-DD or 'tomorrow', 'next Friday', etc.")

                # Task type field
                with Vertical(classes="form-group"):
                    yield Label("Task Type:", classes="form-label")
                    yield Select(
                        [("Work", "work"), ("Personal", "personal"), ("Daily", "daily")],
                        id="task_type",
                        value="work",
                    )

                # Tags field
                with Vertical(classes="form-group"):
                    yield Label("Tags (comma-separated, optional):", classes="form-label")
                    yield Input(id="tags", placeholder="tag1, tag2, tag3")

                # Notes field
                with Vertical(classes="form-group"):
                    yield Label("Notes (optional):", classes="form-label")
                    yield Input(id="notes", placeholder="Additional notes")

                # Buttons
                with Horizontal(id="buttons"):
                    yield Button("Create", id="create", variant="primary")
                    yield Button("Cancel", id="cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "create":
            self._collect_form_data()
            if self._validate_form():
                self.dismiss(self.form_data)
            else:
                self.notify("Description and Project are required", title="Error")

    def _collect_form_data(self) -> None:
        """Collect data from form fields."""
        self.form_data = {
            "description": self.query_one("#description", Input).value or "",
            "project": self.query_one("#project", Select).value or "",
            "priority": self.query_one("#priority", Select).value or "medium",
            "deadline": self.query_one("#deadline", Input).value or "",
            "task_type": self.query_one("#task_type", Select).value or "work",
            "tags": [t.strip() for t in self.query_one("#tags", Input).value.split(",") if t.strip()] or [],
            "notes": self.query_one("#notes", Input).value or "",
        }

    def _validate_form(self) -> bool:
        """Validate required fields."""
        return bool(self.form_data["description"] and self.form_data["project"])

    def action_cancel(self) -> None:
        """Cancel the dialog."""
        self.dismiss(None)
