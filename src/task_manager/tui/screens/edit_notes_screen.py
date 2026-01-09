"""Edit notes screen for updating task notes."""

from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Input, Label, Button, TextArea
from textual.binding import Binding


class EditNotesScreen(ModalScreen):
    """Modal screen for editing task notes."""

    CSS = """
    EditNotesScreen {
        align: center middle;
    }

    #edit-dialog {
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

    #notes-input {
        width: 1fr;
        height: 10;
        margin-bottom: 1;
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

    def __init__(self, task_id: int, current_notes: str = ""):
        """Initialize edit notes screen."""
        super().__init__()
        self.task_id = task_id
        self.current_notes = current_notes

    def compose(self):
        """Create form fields."""
        with Container(id="edit-dialog"):
            yield Label(f"Edit Notes for Task #{self.task_id}", id="title")

            with Vertical():
                yield Label("Notes:", classes="form-label")
                yield Input(
                    id="notes-input",
                    value=self.current_notes,
                    placeholder="Enter your notes here..."
                )

                with Horizontal(id="buttons"):
                    yield Button("Save", id="save", variant="primary")
                    yield Button("Cancel", id="cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "save":
            notes = self.query_one("#notes-input", Input).value
            self.dismiss(notes)

    def action_cancel(self) -> None:
        """Cancel the dialog."""
        self.dismiss(None)
