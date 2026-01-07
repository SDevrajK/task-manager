"""Task command implementations."""

from typing import Optional, List
from datetime import datetime, timedelta

from .models import Task, TaskBucket
from .storage import TaskStorage
from .queries import TaskQuery
from .formatters import TaskFormatter
from .date_parser import DateParser
from .logger import TaskLogger
from .config import Config


class TaskCommands:
    """Implementations of task commands."""

    def __init__(self, config: Config):
        """Initialize with config and storage."""
        self.config = config
        self.storage = TaskStorage(config)
        TaskLogger.setup(config)

    def add(
        self,
        description: str,
        project: str,
        task_type: str = "work",
        priority: str = "medium",
        deadline: Optional[str] = None,
        time_estimate: Optional[float] = None,
        employer_client: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
    ) -> Task:
        """Add new task."""
        # Load bucket
        bucket = self.storage.load_bucket()

        # Resolve project identifier (ID or code) to project ID
        resolved_project = self.storage.resolve_project_identifier(project)
        if not resolved_project:
            raise ValueError(f"Project '{project}' not found. Check project ID or code")
        project = resolved_project

        # Parse deadline if provided
        if deadline:
            deadline = DateParser.parse_or_raise(deadline)

        # Create task
        task = Task(
            id=bucket.get_next_id(),
            description=description,
            project=project,
            task_type=task_type.lower(),
            priority=priority.lower(),
            deadline=deadline,
            time_estimate_hours=time_estimate,
            employer_client=employer_client,
            tags=tags or [],
            notes=notes,
        )

        # Add to bucket
        bucket.tasks.append(task)

        # Save
        self.storage.save_bucket(bucket)
        TaskLogger.log_operation("ADD", f"Task {task.id}: {description}")

        return task

    def list(
        self,
        status: Optional[str] = None,
        project: Optional[str] = None,
        task_type: Optional[str] = None,
        priority: Optional[str] = None,
        deadline_before: Optional[str] = None,
        tags: Optional[List[str]] = None,
        all_tags: Optional[str] = None,
        overdue: bool = False,
        due_today: bool = False,
        due_this_week: bool = False,
        due_next: Optional[int] = None,
        sort_by: str = "deadline",
        format: str = "table",
    ) -> str:
        """List tasks with optional filtering."""
        bucket = self.storage.load_bucket()

        # Resolve project identifier (ID or code) to project ID
        if project:
            resolved_project = self.storage.resolve_project_identifier(project)
            if not resolved_project:
                raise ValueError(f"Project '{project}' not found (check project ID or code)")
            project = resolved_project

        # Filter
        tasks = TaskQuery.filter(
            bucket,
            status=status,
            project=project,
            task_type=task_type,
            priority=priority,
            deadline_before=deadline_before,
            tags=tags,
        )

        # Apply date filters (preserve other filters)
        if overdue:
            tasks = [t for t in tasks if t.is_overdue()]
        elif due_today:
            today = datetime.now().strftime("%Y-%m-%d")
            tasks = [t for t in tasks if t.deadline == today]
        elif due_this_week:
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            start = start_of_week.strftime("%Y-%m-%d")
            end = end_of_week.strftime("%Y-%m-%d")
            tasks = [t for t in tasks if t.deadline and start <= t.deadline <= end]
        elif due_next:
            today = datetime.now().strftime("%Y-%m-%d")
            end_date = (datetime.now() + timedelta(days=due_next)).strftime("%Y-%m-%d")
            tasks = [t for t in tasks if t.deadline and today <= t.deadline <= end_date]

        # Apply all-tags filter
        if all_tags:
            tag_list = [t.strip() for t in all_tags.split(",")]
            tasks = [t for t in tasks if all(tag in t.tags for tag in tag_list)]

        # Sort
        if sort_by == "deadline":
            tasks = TaskQuery.sort_by_deadline(tasks)
        elif sort_by == "priority":
            tasks = TaskQuery.sort_by_priority(tasks)
        elif sort_by == "status":
            tasks = TaskQuery.sort_by_status(tasks)

        # Format
        if format == "json":
            return TaskFormatter.format_bucket_json(
                TaskBucket(tasks=tasks)
            )
        elif format == "simple":
            return "\n".join(TaskFormatter.format_task_simple(t) for t in tasks)
        else:  # table (default)
            color = self.config.get("color_enabled", True)
            project_codes = self.storage.get_project_codes()
            return TaskFormatter.format_task_list_table(tasks, color=color, project_codes=project_codes)

    def show(self, task_id: int, format: str = "detailed") -> str:
        """Show detailed task information."""
        bucket = self.storage.load_bucket()
        task = bucket.get_task_by_id(task_id)

        if not task:
            raise ValueError(f"Task {task_id} not found")

        if format == "json":
            return TaskFormatter.format_task_json(task)
        else:  # detailed (default)
            color = self.config.get("color_enabled", True)
            return TaskFormatter.format_task_detailed(task, color=color)

    def update(
        self,
        task_id: int,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        deadline: Optional[str] = None,
        notes: Optional[str] = None,
        task_type: Optional[str] = None,
        employer_client: Optional[str] = None,
        time_estimate: Optional[float] = None,
        tags: Optional[List[str]] = None,
    ) -> Task:
        """Update task fields."""
        bucket = self.storage.load_bucket()
        task = bucket.get_task_by_id(task_id)

        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Update fields
        if description is not None:
            task.description = description
        if status is not None:
            task.status = status.upper()
        if priority is not None:
            task.priority = priority.lower()
        if deadline is not None:
            task.deadline = DateParser.parse_or_raise(deadline) if deadline else None
        if notes is not None:
            task.notes = notes
        if task_type is not None:
            task.task_type = task_type.lower()
        if employer_client is not None:
            task.employer_client = employer_client
        if time_estimate is not None:
            task.time_estimate_hours = time_estimate
        if tags is not None:
            task.tags = tags

        # Save
        self.storage.save_bucket(bucket)
        TaskLogger.log_operation("UPDATE", f"Task {task_id}: {task.description}")

        return task

    def complete(self, task_id: int, notes: Optional[str] = None) -> Task:
        """Mark task as complete."""
        bucket = self.storage.load_bucket()
        task = bucket.get_task_by_id(task_id)

        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.status = "DONE"
        task.completed = datetime.now().strftime("%Y-%m-%d")

        if notes:
            if task.notes:
                task.notes += f"\n[Completed] {notes}"
            else:
                task.notes = f"[Completed] {notes}"

        self.storage.save_bucket(bucket)
        TaskLogger.log_operation("COMPLETE", f"Task {task_id}: {task.description}")

        return task

    def delete(self, task_id: int, confirm: bool = False) -> None:
        """Delete task."""
        bucket = self.storage.load_bucket()
        task = bucket.get_task_by_id(task_id)

        if not task:
            raise ValueError(f"Task {task_id} not found")

        if not confirm:
            raise ValueError(f"Delete requires --confirm flag")

        bucket.tasks = [t for t in bucket.tasks if t.id != task_id]
        self.storage.save_bucket(bucket)
        TaskLogger.log_operation("DELETE", f"Task {task_id}: {task.description}")

    def log_time(
        self,
        task_id: int,
        hours: float,
        description: str = "",
        date: Optional[str] = None,
    ) -> Task:
        """Log time spent on task."""
        bucket = self.storage.load_bucket()
        task = bucket.get_task_by_id(task_id)

        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Parse date if provided
        if date:
            date = DateParser.parse_or_raise(date)
        else:
            date = datetime.now().strftime("%Y-%m-%d")

        # Create time log entry
        from .models import TimeLog
        log_entry = TimeLog(
            date=date,
            hours=hours,
            description=description,
            logged_at=datetime.now().isoformat(),
        )

        # Add to task
        task.time_logs.append(log_entry)
        task.time_spent_hours += hours

        self.storage.save_bucket(bucket)
        TaskLogger.log_operation(
            "LOG_TIME",
            f"Task {task_id}: {hours}h - {description}",
        )

        return task

    def search(self, query: str, search_in: Optional[str] = None, format: str = "table") -> str:
        """Search tasks by query."""
        bucket = self.storage.load_bucket()
        tasks = TaskQuery.search(bucket, query, search_in=search_in)

        if format == "json":
            return TaskFormatter.format_bucket_json(TaskBucket(tasks=tasks))
        else:  # table (default)
            color = self.config.get("color_enabled", True)
            project_codes = self.storage.get_project_codes()
            return TaskFormatter.format_task_list_table(tasks, color=color, project_codes=project_codes)

    def stats(self) -> str:
        """Get task statistics."""
        bucket = self.storage.load_bucket()
        return TaskFormatter.format_stats(bucket)

    def time_report(
        self,
        project: Optional[str] = None,
        client: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        group_by: str = "project",
    ) -> str:
        """Generate time tracking report."""
        bucket = self.storage.load_bucket()

        # Resolve project identifier (ID or code) to project ID
        if project:
            resolved_project = self.storage.resolve_project_identifier(project)
            if not resolved_project:
                raise ValueError(f"Project '{project}' not found (check project ID or code)")
            project = resolved_project

        # Filter by project if specified
        if project:
            tasks = [t for t in bucket.tasks if t.project == project]
        elif client:
            tasks = [t for t in bucket.tasks if t.employer_client == client]
        else:
            tasks = bucket.tasks

        # Filter by date range if specified
        if start_date or end_date:
            start = start_date if start_date else "2000-01-01"
            end = end_date if end_date else "2099-12-31"
            tasks = TaskQuery.get_by_deadline_range(
                TaskBucket(tasks=tasks), start, end
            )

        return TaskFormatter.format_time_report(tasks, group_by=group_by)

    def add_project(
        self,
        project_id: str,
        name: str,
        code: str,
        lab: Optional[str] = None,
        path: Optional[str] = None,
        status: str = "active",
        description: Optional[str] = None,
    ) -> None:
        """Add new project."""
        # Load existing projects
        projects = self.storage.load_projects()

        # Check if project already exists
        if project_id in projects:
            raise ValueError(f"Project '{project_id}' already exists")

        # Validate code length
        if not (4 <= len(code) <= 5):
            raise ValueError("Project code must be 4-5 characters")

        # Create project entry
        project_data = {
            "name": name,
            "code": code,
            "lab": lab,
            "path": path,
            "status": status,
            "last_accessed": datetime.now().strftime("%Y-%m-%d"),
            "has_claude_md": False,
            "has_readme": False,
            "has_docs": False,
            "description": description,
        }

        # Add to projects
        projects[project_id] = project_data

        # Save
        self.storage.save_projects(projects)
        TaskLogger.log_operation("ADD_PROJECT", f"Project {project_id} ({code}): {name}")
