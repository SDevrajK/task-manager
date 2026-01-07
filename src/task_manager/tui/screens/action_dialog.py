"""Action dialog screen for task operations."""

from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, Label
from textual.binding import Binding

from task_manager.models import Task


class ActionDialog(ModalScreen):
    """Modal dialog for selecting task actions based on task status."""

    CSS = """
    ActionDialog {
        align: center middle;
    }

    #action-dialog {
        width: 50;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1;
    }

    #title {
        width: 1fr;
        height: auto;
        content-align: center middle;
    }

    #actions {
        width: 1fr;
        height: auto;
    }

    Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, task: Task):
        """Initialize action dialog for a specific task."""
        super().__init__()
        self.task = task

    def compose(self):
        """Create dialog content."""
        with Container(id="action-dialog"):
            yield Label(f"Task #{self.task.id}: {self.task.description[:30]}", id="title")
            with Vertical(id="actions"):
                yield from self._get_action_buttons()

    def _get_action_buttons(self):
        """Generate action buttons based on task status."""
        status = self.task.status

        if status == "TODO":
            yield Button("Activate", id="activate", variant="primary")
            yield Button("Edit Notes", id="edit_notes")
            yield Button("Delete", id="delete", variant="error")
        elif status == "IN_PROGRESS":
            yield Button("Mark Complete", id="complete", variant="success")
            yield Button("Deactivate", id="deactivate")
            yield Button("Edit Notes", id="edit_notes")
            yield Button("Delete", id="delete", variant="error")
        elif status == "DONE":
            yield Button("Reopen", id="reopen")
            yield Button("Edit Notes", id="edit_notes")
        elif status == "BLOCKED":
            yield Button("Activate", id="activate", variant="primary")
            yield Button("Unblock", id="unblock")
            yield Button("Edit Notes", id="edit_notes")
            yield Button("Delete", id="delete", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        action = event.button.id
        self.dismiss(action)

    def action_cancel(self) -> None:
        """Cancel the dialog."""
        self.dismiss(None)
