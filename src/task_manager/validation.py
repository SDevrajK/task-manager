"""Schema validation functions."""

from typing import Dict, Any, Tuple, List
from datetime import datetime


VALID_STATUSES = {"TODO", "IN_PROGRESS", "DONE", "BLOCKED"}
VALID_PRIORITIES = {"high", "medium", "low"}
VALID_TASK_TYPES = {"work", "personal", "daily"}
VALID_RECURRENCES = {"daily", "weekdays", "weekends", "custom"}


def validate_task_schema(task: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate task data structure. Returns (valid, errors)."""
    errors = []

    # Required fields
    if "description" not in task or not task["description"]:
        errors.append("description is required and cannot be empty")
    if "id" not in task:
        errors.append("id is required")
    if "project" not in task:
        errors.append("project is required")

    # Type validation
    if "id" in task and not isinstance(task["id"], int):
        errors.append(f"id must be integer, got {type(task['id']).__name__}")

    if "description" in task and not isinstance(task["description"], str):
        errors.append(f"description must be string, got {type(task['description']).__name__}")

    if "project" in task and not isinstance(task["project"], str):
        errors.append(f"project must be string, got {type(task['project']).__name__}")

    # Status validation
    if "status" in task and task["status"] not in VALID_STATUSES:
        errors.append(f"status must be one of {VALID_STATUSES}, got {task['status']}")

    # Priority validation
    if "priority" in task and task["priority"] not in VALID_PRIORITIES:
        errors.append(f"priority must be one of {VALID_PRIORITIES}, got {task['priority']}")

    # Task type validation
    if "task_type" in task and task["task_type"] not in VALID_TASK_TYPES:
        errors.append(f"task_type must be one of {VALID_TASK_TYPES}, got {task['task_type']}")

    # Recurrence validation (only for daily tasks)
    if "recurrence" in task and task["recurrence"]:
        if task["recurrence"] not in VALID_RECURRENCES:
            errors.append(
                f"recurrence must be one of {VALID_RECURRENCES}, got {task['recurrence']}"
            )

    # Date format validation
    date_fields = ["created", "deadline", "activated", "completed", "last_completed"]
    for field in date_fields:
        if field in task and task[field]:
            if not _is_valid_date(task[field]):
                errors.append(f"{field} must be YYYY-MM-DD format, got {task[field]}")

    # Time format validation
    time_fields = ["time_of_day"]
    for field in time_fields:
        if field in task and task[field]:
            if not _is_valid_time(task[field]):
                errors.append(f"{field} must be HH:MM format, got {task[field]}")

    # Numeric validation
    numeric_fields = {
        "time_estimate_hours": float,
        "time_spent_hours": float,
        "streak_count": int,
    }
    for field, expected_type in numeric_fields.items():
        if field in task and task[field] is not None:
            if not isinstance(task[field], (int, float)):
                errors.append(f"{field} must be numeric, got {type(task[field]).__name__}")

    # Tags validation
    if "tags" in task and task["tags"]:
        if not isinstance(task["tags"], list):
            errors.append(f"tags must be list, got {type(task['tags']).__name__}")
        elif not all(isinstance(t, str) for t in task["tags"]):
            errors.append("all tags must be strings")

    # Time logs validation
    if "time_logs" in task and task["time_logs"]:
        if not isinstance(task["time_logs"], list):
            errors.append(f"time_logs must be list, got {type(task['time_logs']).__name__}")
        else:
            for i, log in enumerate(task["time_logs"]):
                log_errors = _validate_time_log(log, i)
                errors.extend(log_errors)

    return len(errors) == 0, errors


def validate_bucket_schema(bucket: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate task bucket schema. Returns (valid, errors)."""
    errors = []

    if "tasks" not in bucket:
        errors.append("tasks array is required")
    elif not isinstance(bucket["tasks"], list):
        errors.append(f"tasks must be array, got {type(bucket['tasks']).__name__}")
    else:
        for i, task in enumerate(bucket["tasks"]):
            task_valid, task_errors = validate_task_schema(task)
            if not task_valid:
                errors.extend([f"Task {i}: {e}" for e in task_errors])

    if "next_id" not in bucket:
        errors.append("next_id is required")
    elif not isinstance(bucket["next_id"], int):
        errors.append(f"next_id must be integer, got {type(bucket['next_id']).__name__}")

    if "last_updated" in bucket and bucket["last_updated"]:
        try:
            datetime.fromisoformat(bucket["last_updated"])
        except (ValueError, TypeError):
            errors.append(f"last_updated must be ISO8601 format, got {bucket['last_updated']}")

    return len(errors) == 0, errors


def _is_valid_date(date_str: str) -> bool:
    """Check if string is valid YYYY-MM-DD date."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def _is_valid_time(time_str: str) -> bool:
    """Check if string is valid HH:MM time."""
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except (ValueError, TypeError):
        return False


def _validate_time_log(log: Any, index: int) -> List[str]:
    """Validate a single time log entry."""
    errors = []

    if not isinstance(log, dict):
        errors.append(f"Time log {index} must be object")
        return errors

    if "hours" not in log:
        errors.append(f"Time log {index}: hours is required")
    elif not isinstance(log["hours"], (int, float)):
        errors.append(f"Time log {index}: hours must be numeric")

    if "date" in log and log["date"]:
        if not _is_valid_date(log["date"]):
            errors.append(f"Time log {index}: date must be YYYY-MM-DD format")

    if "description" in log and log["description"]:
        if not isinstance(log["description"], str):
            errors.append(f"Time log {index}: description must be string")

    if "logged_at" in log and log["logged_at"]:
        try:
            datetime.fromisoformat(log["logged_at"])
        except (ValueError, TypeError):
            errors.append(f"Time log {index}: logged_at must be ISO8601 format")

    return errors
