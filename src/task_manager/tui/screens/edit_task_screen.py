"""Edit task screen for modifying task fields."""

from textual.screen import ModalScreen
from textual.containers import Container, Vertical, ScrollableContainer
from textual.widgets import Input, Label, Button, Select
from textual.binding import Binding

from task_manager.models import Task


class EditTaskScreen(ModalScreen):
    """Modal screen for editing task details."""

    CSS = """
    EditTaskScreen {
        align: center middle;
    }

    #edit-dialog {
        width: 70;
        height: 30;
        border: solid $primary;
        background: $surface;
        padding: 1;
        layout: vertical;
    }

    #title {
        width: 1fr;
        height: 1;
        content-align: center middle;
        margin-bottom: 0;
    }

    #form-scroll {
        width: 1fr;
        height: 1fr;
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
        height: 1;
    }

    #buttons {
        width: 1fr;
        height: auto;
        layout: horizontal;
    }

    Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, task: Task):
        """Initialize edit task screen."""
        super().__init__()
        self.edit_task = task
        self.form_data = {
            "description": task.description,
            "deadline": task.deadline or "",
            "priority": task.priority,
            "task_type": task.task_type,
            "tags": ",".join(task.tags) if task.tags else "",
            "notes": task.notes or "",
        }

    def compose(self):
        """Create form fields."""
        with Container(id="edit-dialog"):
            yield Label(f"Edit Task #{self.edit_task.id}", id="title")

            with ScrollableContainer(id="form-scroll"):
                with Vertical():
                    # Description field
                    with Vertical(classes="form-group"):
                        yield Label("Description:", classes="form-label")
                        yield Input(id="description", value=self.form_data["description"])

                    # Deadline field
                    with Vertical(classes="form-group"):
                        yield Label("Deadline (optional):", classes="form-label")
                        yield Input(
                            id="deadline",
                            value=self.form_data["deadline"],
                            placeholder="YYYY-MM-DD or 'tomorrow'"
                        )

                    # Priority field
                    with Vertical(classes="form-group"):
                        yield Label("Priority:", classes="form-label")
                        yield Select(
                            [("Low", "low"), ("Medium", "medium"), ("High", "high")],
                            id="priority",
                            value=self.form_data["priority"],
                        )

                    # Task type field
                    with Vertical(classes="form-group"):
                        yield Label("Task Type:", classes="form-label")
                        yield Select(
                            [("Work", "work"), ("Personal", "personal"), ("Daily", "daily")],
                            id="task_type",
                            value=self.form_data["task_type"],
                        )

                    # Tags field
                    with Vertical(classes="form-group"):
                        yield Label("Tags (comma-separated, optional):", classes="form-label")
                        yield Input(
                            id="tags",
                            value=self.form_data["tags"],
                            placeholder="tag1, tag2, tag3"
                        )

                    # Notes field
                    with Vertical(classes="form-group"):
                        yield Label("Notes (optional):", classes="form-label")
                        yield Input(
                            id="notes",
                            value=self.form_data["notes"],
                            placeholder="Additional notes"
                        )

            # Buttons (always visible at bottom)
            with Vertical(id="buttons"):
                yield Button("Save", id="save", variant="primary")
                yield Button("Cancel", id="cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "save":
            self._collect_form_data()
            if self._validate_form():
                self.dismiss(self.form_data)
            else:
                self.notify("Description is required", title="Error")

    def _collect_form_data(self) -> None:
        """Collect data from form fields."""
        self.form_data = {
            "description": self.query_one("#description", Input).value or "",
            "deadline": self.query_one("#deadline", Input).value or "",
            "priority": self.query_one("#priority", Select).value or "medium",
            "task_type": self.query_one("#task_type", Select).value or "work",
            "tags": [t.strip() for t in self.query_one("#tags", Input).value.split(",") if t.strip()] or [],
            "notes": self.query_one("#notes", Input).value or "",
        }

    def _validate_form(self) -> bool:
        """Validate required fields."""
        return bool(self.form_data["description"])

    def action_cancel(self) -> None:
        """Cancel the dialog."""
        self.dismiss(None)
