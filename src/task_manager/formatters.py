"""Output formatting for tasks."""

import json
from typing import List, Optional, Dict
from colorama import Fore, Style

from .models import Task, TaskBucket


class TaskFormatter:
    """Format task output for different formats."""

    # Color scheme
    COLORS = {
        "DONE": Fore.GREEN,
        "IN_PROGRESS": Fore.YELLOW,
        "TODO": Fore.BLUE,
        "BLOCKED": Fore.RED,
        "OVERDUE": Fore.RED,
    }

    PRIORITY_COLORS = {
        "high": Fore.RED,
        "medium": Fore.YELLOW,
        "low": Fore.BLUE,
    }

    @staticmethod
    def format_status(status: str, color: bool = True) -> str:
        """Format status with color."""
        if not color:
            return status

        color_code = TaskFormatter.COLORS.get(status, "")
        return f"{color_code}{status}{Style.RESET_ALL}"

    @staticmethod
    def format_priority(priority: str, color: bool = True) -> str:
        """Format priority with color."""
        if not color:
            return priority[0].upper()

        color_code = TaskFormatter.PRIORITY_COLORS.get(priority, "")
        abbr = priority[0].upper()
        return f"{color_code}{abbr}{Style.RESET_ALL}"

    @staticmethod
    def format_task_simple(task: Task, color: bool = True) -> str:
        """Format task as single line (simple format)."""
        deadline = task.deadline if task.deadline else "-"
        status = TaskFormatter.format_status(task.status, color)
        return f"{task.id:3d} {task.description:35s} {deadline:12s} {status}"

    @staticmethod
    def format_task_table_row(task: Task, color: bool = True, project_code: Optional[str] = None) -> str:
        """Format task as table row."""
        # Build row
        task_id = str(task.id).ljust(3)
        desc = task.description[:30].ljust(30)
        # Use project code if available, otherwise use project ID
        proj_display = project_code if project_code else task.project
        project = proj_display[:6].ljust(6)
        task_type = task.task_type[:4].ljust(4)
        priority = TaskFormatter.format_priority(task.priority, color)
        deadline = (task.deadline if task.deadline else "-").ljust(10)

        # Time info
        time_est = f"{task.time_estimate_hours}h" if task.time_estimate_hours else "-"
        time_spent = f"{task.time_spent_hours}h" if task.time_spent_hours > 0 else "-"
        time_info = f"{time_est:6s} {time_spent:6s}".strip()

        status = TaskFormatter.format_status(task.status, color)

        return f"{task_id} {desc} {project} {task_type} {priority}  {deadline}  {time_info:12s}  {status}"

    @staticmethod
    def format_task_detailed(task: Task, color: bool = True) -> str:
        """Format task with all details."""
        lines = [
            f"Task #{task.id}",
            f"  Description: {task.description}",
            f"  Status: {TaskFormatter.format_status(task.status, color)}",
            f"  Priority: {task.priority}",
            f"  Project: {task.project}",
            f"  Type: {task.task_type}",
        ]

        if task.deadline:
            lines.append(f"  Deadline: {task.deadline}")

        if task.employer_client:
            lines.append(f"  Client/Employer: {task.employer_client}")

        if task.time_estimate_hours:
            lines.append(f"  Time Estimate: {task.time_estimate_hours} hours")

        if task.time_spent_hours > 0:
            lines.append(f"  Time Spent: {task.time_spent_hours} hours")

        if task.tags:
            lines.append(f"  Tags: {', '.join(task.tags)}")

        if task.notes:
            lines.append(f"  Notes: {task.notes}")

        if task.time_logs:
            lines.append("  Time Logs:")
            for log in task.time_logs:
                lines.append(f"    - {log.date}: {log.hours}h - {log.description}")

        if task.created:
            lines.append(f"  Created: {task.created}")

        if task.activated:
            lines.append(f"  Activated: {task.activated}")

        if task.completed:
            lines.append(f"  Completed: {task.completed}")

        return "\n".join(lines)

    @staticmethod
    def format_task_list_table(
        tasks: List[Task],
        color: bool = True,
        detailed: bool = False,
        project_codes: Optional[Dict[str, str]] = None,
    ) -> str:
        """Format list of tasks as table."""
        if not tasks:
            return "No tasks found."

        if detailed:
            return "\n\n".join(TaskFormatter.format_task_detailed(t, color) for t in tasks)

        # Table header
        header = "ID  Description                    Code Type Pri Due        Est    Spent    Status"
        divider = "-" * len(header)

        rows = [header, divider]
        for task in tasks:
            code = project_codes.get(task.project) if project_codes else None
            rows.append(TaskFormatter.format_task_table_row(task, color, code))

        return "\n".join(rows)

    @staticmethod
    def format_task_json(task: Task) -> str:
        """Format task as JSON."""
        return json.dumps(task.to_dict(), indent=2, default=str)

    @staticmethod
    def format_bucket_json(bucket: TaskBucket) -> str:
        """Format bucket as JSON."""
        return json.dumps(bucket.to_dict(), indent=2, default=str)

    @staticmethod
    def format_stats(bucket: TaskBucket) -> str:
        """Format task statistics."""
        stats = bucket.stats()
        lines = [
            "Task Statistics:",
            f"  Total tasks: {stats['total']}",
            f"  Pending (TODO): {stats['pending']}",
            f"  Active (IN_PROGRESS): {stats['active']}",
            f"  Completed (DONE): {stats['completed']}",
            f"  Blocked: {stats['blocked']}",
            f"  Overdue: {stats['overdue']}",
        ]

        # Time estimates
        total_estimate = sum(
            t.time_estimate_hours for t in bucket.tasks
            if t.time_estimate_hours
        )
        total_spent = sum(t.time_spent_hours for t in bucket.tasks)

        if total_estimate > 0 or total_spent > 0:
            lines.extend([
                f"\nTime Tracking:",
                f"  Total estimated: {total_estimate} hours",
                f"  Total spent: {total_spent} hours",
            ])

        return "\n".join(lines)

    @staticmethod
    def format_time_report(
        tasks: List[Task],
        group_by: str = "project",
    ) -> str:
        """Format time tracking report."""
        if not tasks:
            return "No tasks with time tracking data."

        lines = ["Time Report:", ""]

        if group_by == "project":
            projects = {}
            for task in tasks:
                if task.time_spent_hours > 0:
                    if task.project not in projects:
                        projects[task.project] = {"hours": 0, "count": 0}
                    projects[task.project]["hours"] += task.time_spent_hours
                    projects[task.project]["count"] += 1

            lines.append("By Project:")
            total = 0
            for project in sorted(projects.keys()):
                data = projects[project]
                hours = data["hours"]
                count = data["count"]
                lines.append(f"  {project:20s}: {hours:8.1f} hours ({count} tasks)")
                total += hours

            lines.append(f"\nTotal: {total:.1f} hours")

        elif group_by == "client":
            clients = {}
            for task in tasks:
                if task.time_spent_hours > 0 and task.employer_client:
                    if task.employer_client not in clients:
                        clients[task.employer_client] = {"hours": 0, "count": 0}
                    clients[task.employer_client]["hours"] += task.time_spent_hours
                    clients[task.employer_client]["count"] += 1

            lines.append("By Client/Employer:")
            total = 0
            for client in sorted(clients.keys()):
                data = clients[client]
                hours = data["hours"]
                count = data["count"]
                lines.append(f"  {client:20s}: {hours:8.1f} hours ({count} tasks)")
                total += hours

            lines.append(f"\nTotal: {total:.1f} hours")

        return "\n".join(lines)
