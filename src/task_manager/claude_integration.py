"""Integration with CLAUDE.md files in project directories."""

import os
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from task_manager.models import Task
from task_manager.storage import TaskStorage
from task_manager.config import Config


class ClaudeIntegration:
    """Handle updates to CLAUDE.md files in project directories."""

    # CLAUDE.md section markers
    UPCOMING_SECTION = "### Upcoming Tasks"
    COMPLETED_SECTION = "### Recent Completions"
    TASK_ID_COMMENT = "<!-- task-id: {id} -->"

    def __init__(self, config: Config):
        """Initialize with config and storage."""
        self.config = config
        self.storage = TaskStorage(config)
        self.projects = self._load_projects()

    def _load_projects(self) -> Dict[str, Dict]:
        """Load projects from storage."""
        return self.storage.load_projects()

    def get_project_path(self, project_id: str) -> Optional[str]:
        """Get the file path for a project's CLAUDE.md."""
        if project_id not in self.projects:
            return None
        project = self.projects[project_id]
        project_path = project.get("path")
        if not project_path:
            return None
        claude_md = Path(project_path) / "CLAUDE.md"
        return str(claude_md) if claude_md.exists() else None

    def activate_task(self, task: Task, mode: str = "quick") -> Tuple[bool, str]:
        """
        Add task to CLAUDE.md Upcoming Tasks section.

        Args:
            task: The task to activate
            mode: "quick" (just update status) or "prd" (show PRD workflow)

        Returns:
            Tuple of (success, message)
        """
        claude_md_path = self.get_project_path(task.project)
        if not claude_md_path:
            return False, f"No CLAUDE.md found for project {task.project}"

        try:
            with open(claude_md_path, "r") as f:
                content = f.read()

            # Check if task already exists
            task_comment = self.TASK_ID_COMMENT.format(id=task.id)
            if task_comment in content:
                return False, f"Task #{task.id} already in CLAUDE.md"

            # Find or create Upcoming Tasks section
            content = self._ensure_section(content, self.UPCOMING_SECTION)

            # Add task to Upcoming Tasks
            task_entry = self._format_task_entry(task)
            content = self._add_to_section(content, self.UPCOMING_SECTION, task_entry)

            with open(claude_md_path, "w") as f:
                f.write(content)

            if mode == "prd":
                return True, f"Task #{task.id} activated. Next: /create-prd → /generate-tasks → /process-tasks"
            else:
                return True, f"Task #{task.id} added to Upcoming Tasks in CLAUDE.md"

        except Exception as e:
            return False, f"Error updating CLAUDE.md: {str(e)}"

    def complete_task(self, task: Task) -> Tuple[bool, str]:
        """
        Move task from Upcoming Tasks to Recent Completions in CLAUDE.md.

        Args:
            task: The task that was completed

        Returns:
            Tuple of (success, message)
        """
        claude_md_path = self.get_project_path(task.project)
        if not claude_md_path:
            return False, f"No CLAUDE.md found for project {task.project}"

        try:
            with open(claude_md_path, "r") as f:
                content = f.read()

            task_comment = self.TASK_ID_COMMENT.format(id=task.id)

            # Remove from Upcoming Tasks
            content = self._remove_from_section(content, self.UPCOMING_SECTION, task_comment)

            # Add to Recent Completions
            content = self._ensure_section(content, self.COMPLETED_SECTION)
            task_entry = self._format_completed_task_entry(task)
            content = self._add_to_section(content, self.COMPLETED_SECTION, task_entry)

            with open(claude_md_path, "w") as f:
                f.write(content)

            return True, f"Task #{task.id} moved to Recent Completions in CLAUDE.md"

        except Exception as e:
            return False, f"Error updating CLAUDE.md: {str(e)}"

    def deactivate_task(self, task: Task) -> Tuple[bool, str]:
        """
        Remove task from CLAUDE.md.

        Args:
            task: The task to deactivate

        Returns:
            Tuple of (success, message)
        """
        claude_md_path = self.get_project_path(task.project)
        if not claude_md_path:
            return False, f"No CLAUDE.md found for project {task.project}"

        try:
            with open(claude_md_path, "r") as f:
                content = f.read()

            task_comment = self.TASK_ID_COMMENT.format(id=task.id)

            # Remove from both sections
            content = self._remove_from_section(content, self.UPCOMING_SECTION, task_comment)
            content = self._remove_from_section(content, self.COMPLETED_SECTION, task_comment)

            with open(claude_md_path, "w") as f:
                f.write(content)

            return True, f"Task #{task.id} removed from CLAUDE.md"

        except Exception as e:
            return False, f"Error updating CLAUDE.md: {str(e)}"

    def _ensure_section(self, content: str, section_name: str) -> str:
        """Ensure a section exists in the content. Create it if missing."""
        if section_name not in content:
            # Add section at the end (before the footer if present)
            if content.endswith("\n"):
                content += f"\n{section_name}\n\n"
            else:
                content += f"\n\n{section_name}\n\n"
        return content

    def _format_task_entry(self, task: Task) -> str:
        """Format a task as a markdown list entry with task ID comment."""
        deadline_str = f" (Due: {task.deadline})" if task.deadline else ""
        return f"{self.TASK_ID_COMMENT}\n- **#{task.id}**: {task.description}{deadline_str}\n"

    def _format_completed_task_entry(self, task: Task) -> str:
        """Format a completed task as a markdown list entry."""
        completed_date = task.completed or task.status
        return f"{self.TASK_ID_COMMENT}\n- **#{task.id}** ✓: {task.description} (Completed: {completed_date})\n"

    def _add_to_section(self, content: str, section_name: str, entry: str) -> str:
        """Add an entry to a specific section."""
        section_pattern = rf"({re.escape(section_name)}\n+)(.*?)(\n\n###|\Z)"

        match = re.search(section_pattern, content, re.DOTALL)
        if not match:
            return content

        section_header = match.group(1)
        section_content = match.group(2)
        section_end = match.group(3)

        # Add entry to section content
        updated_section = section_content + entry

        # Replace in content
        content = content[:match.start()] + section_header + updated_section + section_end + content[match.end():]
        return content

    def _remove_from_section(self, content: str, section_name: str, task_comment: str) -> str:
        """Remove a task (identified by comment) from a section."""
        section_pattern = rf"({re.escape(section_name)}\n+)(.*?)(\n\n###|\Z)"

        match = re.search(section_pattern, content, re.DOTALL)
        if not match:
            return content

        section_header = match.group(1)
        section_content = match.group(2)
        section_end = match.group(3)

        # Find and remove the task entry (including comment line)
        # Match from the comment to the end of the bullet point
        task_pattern = rf"{re.escape(task_comment)}\n-[^\n]*(?:\n(?!-).*)*"
        updated_section = re.sub(task_pattern, "", section_content)

        # Clean up extra whitespace
        updated_section = re.sub(r"\n\n\n+", "\n\n", updated_section).strip() + "\n"

        # Replace in content
        content = content[:match.start()] + section_header + updated_section + section_end + content[match.end():]
        return content
