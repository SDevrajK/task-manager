"""Task filtering and search logic."""

from typing import List, Optional
from datetime import datetime, timedelta

from .models import Task, TaskBucket


class TaskQuery:
    """Query and filter tasks."""

    @staticmethod
    def filter(
        bucket: TaskBucket,
        status: Optional[str] = None,
        project: Optional[str] = None,
        task_type: Optional[str] = None,
        priority: Optional[str] = None,
        deadline_before: Optional[str] = None,
        deadline_after: Optional[str] = None,
        tags: Optional[List[str]] = None,
        employer_client: Optional[str] = None,
    ) -> List[Task]:
        """Filter tasks by various criteria."""
        results = bucket.tasks[:]

        if status:
            results = [t for t in results if t.status == status.upper()]

        if project:
            results = [t for t in results if t.project.lower() == project.lower()]

        if task_type:
            results = [t for t in results if t.task_type == task_type.lower()]

        if priority:
            results = [t for t in results if t.priority == priority.lower()]

        if deadline_before:
            results = [t for t in results if t.deadline and t.deadline <= deadline_before]

        if deadline_after:
            results = [t for t in results if t.deadline and t.deadline >= deadline_after]

        if tags:
            # Match tasks that have ANY of the specified tags
            results = [t for t in results if any(tag in t.tags for tag in tags)]

        if employer_client:
            results = [
                t for t in results
                if t.employer_client and employer_client.lower() in t.employer_client.lower()
            ]

        return results

    @staticmethod
    def search(bucket: TaskBucket, query: str, search_in: Optional[str] = None) -> List[Task]:
        """Search tasks by description, notes, and tags.

        Args:
            bucket: TaskBucket to search
            query: Search query string
            search_in: Optional field to search in ('description', 'notes', 'tags', 'client')
        """
        query_lower = query.lower()
        results = []

        for task in bucket.tasks:
            match = False

            if search_in == "description" or not search_in:
                if query_lower in task.description.lower():
                    match = True

            if (search_in == "notes" or not search_in) and not match:
                if task.notes and query_lower in task.notes.lower():
                    match = True

            if (search_in == "tags" or not search_in) and not match:
                if any(query_lower in tag.lower() for tag in task.tags):
                    match = True

            if (search_in == "client" or not search_in) and not match:
                if task.employer_client and query_lower in task.employer_client.lower():
                    match = True

            if match:
                results.append(task)

        return results

    @staticmethod
    def get_active_tasks(bucket: TaskBucket) -> List[Task]:
        """Get active tasks (IN_PROGRESS)."""
        return [t for t in bucket.tasks if t.status == "IN_PROGRESS"]

    @staticmethod
    def get_pending_tasks(bucket: TaskBucket) -> List[Task]:
        """Get pending tasks (TODO)."""
        return [t for t in bucket.tasks if t.status == "TODO"]

    @staticmethod
    def get_completed_tasks(bucket: TaskBucket) -> List[Task]:
        """Get completed tasks (DONE)."""
        return [t for t in bucket.tasks if t.status == "DONE"]

    @staticmethod
    def get_overdue_tasks(bucket: TaskBucket) -> List[Task]:
        """Get overdue tasks."""
        return [t for t in bucket.tasks if t.is_overdue()]

    @staticmethod
    def get_by_deadline_range(
        bucket: TaskBucket, start_date: str, end_date: str
    ) -> List[Task]:
        """Get tasks with deadline within range."""
        return [
            t for t in bucket.tasks
            if t.deadline and start_date <= t.deadline <= end_date
        ]

    @staticmethod
    def sort_by_deadline(tasks: List[Task], reverse: bool = False) -> List[Task]:
        """Sort tasks by deadline (earliest first by default)."""
        def deadline_key(task: Task):
            if not task.deadline:
                return "9999-12-31"  # Put tasks without deadlines at end
            return task.deadline

        return sorted(tasks, key=deadline_key, reverse=reverse)

    @staticmethod
    def sort_by_priority(tasks: List[Task], reverse: bool = True) -> List[Task]:
        """Sort tasks by priority (high first by default)."""
        priority_order = {"high": 3, "medium": 2, "low": 1}
        return sorted(
            tasks,
            key=lambda t: priority_order.get(t.priority, 0),
            reverse=reverse
        )

    @staticmethod
    def sort_by_status(tasks: List[Task]) -> List[Task]:
        """Sort tasks by status (IN_PROGRESS, TODO, DONE, BLOCKED)."""
        status_order = {"IN_PROGRESS": 0, "TODO": 1, "BLOCKED": 2, "DONE": 3}
        return sorted(tasks, key=lambda t: status_order.get(t.status, 999))

    @staticmethod
    def get_due_today(bucket: TaskBucket) -> List[Task]:
        """Get tasks due today."""
        today = datetime.now().strftime("%Y-%m-%d")
        return [t for t in bucket.tasks if t.deadline == today]

    @staticmethod
    def get_due_this_week(bucket: TaskBucket) -> List[Task]:
        """Get tasks due this week (Mon-Sun)."""
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        start_date = start_of_week.strftime("%Y-%m-%d")
        end_date = end_of_week.strftime("%Y-%m-%d")

        return TaskQuery.get_by_deadline_range(bucket, start_date, end_date)

    @staticmethod
    def get_due_next_n_days(bucket: TaskBucket, n: int) -> List[Task]:
        """Get tasks due in the next N days."""
        today = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=n)).strftime("%Y-%m-%d")
        return TaskQuery.get_by_deadline_range(bucket, today, end_date)

    @staticmethod
    def get_all_with_tag(bucket: TaskBucket, tag: str, require_all: bool = False) -> List[Task]:
        """Get tasks with specific tag(s).

        Args:
            bucket: TaskBucket to search
            tag: Tag to search for (comma-separated for multiple)
            require_all: If True, require all tags; if False, any tag matches
        """
        tags_list = [t.strip() for t in tag.split(",")]
        tasks = []

        for task in bucket.tasks:
            if require_all:
                if all(t in task.tags for t in tags_list):
                    tasks.append(task)
            else:
                if any(t in task.tags for t in tags_list):
                    tasks.append(task)

        return tasks

    @staticmethod
    def group_by_project(tasks: List[Task]) -> dict:
        """Group tasks by project."""
        groups = {}
        for task in tasks:
            if task.project not in groups:
                groups[task.project] = []
            groups[task.project].append(task)
        return groups

    @staticmethod
    def group_by_status(tasks: List[Task]) -> dict:
        """Group tasks by status."""
        groups = {}
        for task in tasks:
            if task.status not in groups:
                groups[task.status] = []
            groups[task.status].append(task)
        return groups

    @staticmethod
    def get_time_logs_by_date_range(
        bucket: TaskBucket,
        start_date: str,
        end_date: str,
        project: Optional[str] = None,
        client: Optional[str] = None,
    ) -> List[tuple]:
        """Get time logs within date range with task context.

        Returns list of tuples: (task, time_log)
        This allows access to both the log AND task metadata (client, project).
        Filters by log.date, not task.deadline.
        """
        results = []

        for task in bucket.tasks:
            # Filter by project/client if specified
            if project and task.project != project:
                continue
            if client and task.employer_client != client:
                continue

            # Get time logs within range
            for log in task.time_logs:
                if start_date <= log.date <= end_date:
                    results.append((task, log))

        return results


# Import timedelta for get_due_this_week
from datetime import timedelta
