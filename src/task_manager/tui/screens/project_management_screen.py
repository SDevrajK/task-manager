"""Project management screen for adding and deleting projects."""

from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Input, Label, Button, Static
from textual.binding import Binding


class ConfirmDialog(ModalScreen):
    """Simple confirmation dialog."""

    CSS = """
    ConfirmDialog {
        align: center middle;
    }

    #confirm-box {
        width: 50;
        height: auto;
        border: solid $warning;
        background: $surface;
        padding: 1;
    }

    #message {
        width: 1fr;
        height: auto;
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

    def __init__(self, message: str):
        """Initialize confirm dialog."""
        super().__init__()
        self.message = message

    def compose(self):
        """Create dialog."""
        with Container(id="confirm-box"):
            yield Label(self.message, id="message")
            with Horizontal(id="buttons"):
                yield Button("Yes", id="confirm", variant="error")
                yield Button("No", id="cancel", variant="warning")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)


class ProjectsList(Static):
    """Display projects list."""

    DEFAULT_CSS = """
    ProjectsList {
        width: 1fr;
        height: auto;
        overflow: auto;
    }
    """

    def __init__(self, projects=None, *args, **kwargs):
        """Initialize projects list."""
        super().__init__(*args, **kwargs)
        self.projects = projects or {}
        self.selected_index = 0

    def render(self) -> str:
        """Render projects list."""
        if not self.projects:
            return "[dim]No projects[/dim]"

        lines = []
        for i, (project_id, project_data) in enumerate(self.projects.items()):
            code = project_data.get("code", project_id[:5])
            name = project_data.get("name", project_id)
            prefix = "[bold cyan]> [/]" if i == self.selected_index else "  "
            lines.append(f"{prefix}{code:6s} {name}")

        return "\n".join(lines)

    def update_projects(self, projects):
        """Update the projects list."""
        self.projects = projects
        self.selected_index = min(self.selected_index, len(projects) - 1) if projects else 0
        self.refresh()

    def select_next(self):
        """Select next project."""
        if self.projects:
            self.selected_index = min(self.selected_index + 1, len(self.projects) - 1)
            self.refresh()

    def select_previous(self):
        """Select previous project."""
        if self.projects:
            self.selected_index = max(self.selected_index - 1, 0)
            self.refresh()

    def get_selected_project_id(self):
        """Get the selected project ID."""
        if not self.projects:
            return None
        return list(self.projects.keys())[self.selected_index]


class ProjectManagementScreen(ModalScreen):
    """Modal screen for managing projects."""

    CSS = """
    ProjectManagementScreen {
        align: center middle;
    }

    #project-dialog {
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

    #projects-section {
        width: 1fr;
        height: auto;
        margin-bottom: 1;
    }

    #projects-label {
        width: 1fr;
        height: 1;
        margin-bottom: 0;
    }

    #projects-list {
        width: 1fr;
        height: 8;
        margin-bottom: 1;
    }

    #add-section {
        width: 1fr;
        height: auto;
        margin-bottom: 1;
    }

    .form-label {
        width: 1fr;
        height: 1;
    }

    Input {
        width: 1fr;
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
        Binding("up", "select_previous", "Previous"),
        Binding("down", "select_next", "Next"),
    ]

    def __init__(self, projects: dict, storage):
        """Initialize project management screen."""
        super().__init__()
        self.projects = projects
        self.storage = storage

    def compose(self):
        """Create project management interface."""
        with Container(id="project-dialog"):
            yield Label("Project Management", id="title")

            with Vertical(id="projects-section"):
                yield Label("Projects (↑↓ select):", id="projects-label")
                self.projects_list = ProjectsList(self.projects)
                yield self.projects_list
                yield Button("Delete Selected", id="delete", variant="error")

            with Vertical(id="add-section"):
                yield Label("Add Project:", classes="form-label")
                yield Input(
                    id="project-code",
                    placeholder="Code (4-5 chars, e.g., 'nserc3')"
                )
                yield Input(
                    id="project-name",
                    placeholder="Name (e.g., 'NSERC Grant 3')"
                )

                with Vertical(id="buttons"):
                    yield Button("Add Project", id="add", variant="primary")
                    yield Button("Close", id="close", variant="warning")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close":
            self.dismiss(None)
        elif event.button.id == "add":
            self._add_project()
        elif event.button.id == "delete":
            self._prompt_delete_project()

    def _add_project(self) -> None:
        """Add a new project."""
        code = self.query_one("#project-code", Input).value.strip()
        name = self.query_one("#project-name", Input).value.strip()

        if not code or not name:
            self.notify("Code and name are required", title="Error")
            return

        if len(code) < 4 or len(code) > 5:
            self.notify("Code must be 4-5 characters", title="Error")
            return

        # Create project ID from code
        project_id = code.lower()

        if project_id in self.projects:
            self.notify(f"Project '{project_id}' already exists", title="Error")
            return

        # Add to projects
        self.projects[project_id] = {
            "code": code,
            "name": name,
            "status": "active"
        }

        # Save projects
        try:
            self.storage.save_projects(self.projects)
            self.notify(f"Project '{name}' added", title="Success")

            # Clear inputs and refresh list
            self.query_one("#project-code", Input).value = ""
            self.query_one("#project-name", Input).value = ""
            self.projects_list.update_projects(self.projects)
        except Exception as e:
            self.notify(f"Error saving project: {str(e)}", title="Error")

    def _prompt_delete_project(self) -> None:
        """Show confirmation dialog before deleting project."""
        project_id = self.projects_list.get_selected_project_id()
        if not project_id:
            self.notify("No project selected", title="Error")
            return

        project_name = self.projects[project_id].get("name", project_id)
        message = f"Delete project '{project_name}'?\nThis cannot be undone."

        self.app.push_screen(
            ConfirmDialog(message),
            callback=self._handle_delete_confirmation
        )

    def _handle_delete_confirmation(self, confirmed: bool) -> None:
        """Handle delete confirmation result."""
        if not confirmed:
            return

        project_id = self.projects_list.get_selected_project_id()
        if not project_id:
            return

        project_name = self.projects[project_id].get("name", project_id)

        if project_id in self.projects:
            del self.projects[project_id]

            try:
                self.storage.save_projects(self.projects)
                self.notify(f"Project '{project_name}' deleted", title="Success")
                self.projects_list.update_projects(self.projects)
            except Exception as e:
                self.notify(f"Error deleting project: {str(e)}", title="Error")

    def action_cancel(self) -> None:
        """Cancel and close."""
        self.dismiss(None)

    def action_select_previous(self) -> None:
        """Select previous project."""
        self.projects_list.select_previous()

    def action_select_next(self) -> None:
        """Select next project."""
        self.projects_list.select_next()
