"""Data models for tasks, buckets, and projects."""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class TimeLog:
    """Record of time spent on a task."""
    date: str  # YYYY-MM-DD
    hours: float
    description: str
    logged_at: str  # ISO8601 timestamp

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimeLog":
        return cls(**data)


@dataclass
class Task:
    """Individual task with all metadata."""
    id: int
    description: str
    project: str
    status: str = "TODO"  # TODO, IN_PROGRESS, DONE, BLOCKED
    created: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    priority: str = "medium"  # high, medium, low
    deadline: Optional[str] = None  # YYYY-MM-DD
    notes: Optional[str] = None
    activated: Optional[str] = None
    completed: Optional[str] = None

    # New fields
    task_type: str = "work"  # work, personal, daily
    employer_client: Optional[str] = None
    time_estimate_hours: Optional[float] = None
    time_spent_hours: float = 0.0
    time_logs: List[TimeLog] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # Daily task fields
    recurrence: Optional[str] = None  # daily, weekdays, weekends, custom
    recurrence_days: List[int] = field(default_factory=list)  # 0=Monday, 6=Sunday
    time_of_day: Optional[str] = None  # HH:MM
    streak_count: int = 0
    last_completed: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Convert TimeLog objects to dicts
        if self.time_logs:
            data["time_logs"] = [log.to_dict() if isinstance(log, TimeLog) else log
                                 for log in self.time_logs]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create Task from dictionary, handling time_logs conversion."""
        data = data.copy()
        if "time_logs" in data and data["time_logs"]:
            data["time_logs"] = [
                TimeLog.from_dict(log) if isinstance(log, dict) else log
                for log in data["time_logs"]
            ]
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def is_overdue(self) -> bool:
        """Check if task is overdue (deadline passed and not completed)."""
        if not self.deadline or self.status == "DONE":
            return False
        today = datetime.now().strftime("%Y-%m-%d")
        return self.deadline < today

    def days_until_deadline(self) -> Optional[int]:
        """Return days until deadline, None if no deadline."""
        if not self.deadline:
            return None
        today = datetime.now().strftime("%Y-%m-%d")
        if today <= self.deadline:
            deadline_date = datetime.strptime(self.deadline, "%Y-%m-%d")
            today_date = datetime.strptime(today, "%Y-%m-%d")
            return (deadline_date - today_date).days
        return None


@dataclass
class TaskBucket:
    """Collection of all tasks with metadata."""
    tasks: List[Task] = field(default_factory=list)
    next_id: int = 1
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def pending_tasks(self) -> List[Task]:
        return [t for t in self.tasks if t.status == "TODO"]

    @property
    def active_tasks(self) -> List[Task]:
        return [t for t in self.tasks if t.status == "IN_PROGRESS"]

    @property
    def completed_tasks(self) -> List[Task]:
        return [t for t in self.tasks if t.status == "DONE"]

    @property
    def blocked_tasks(self) -> List[Task]:
        return [t for t in self.tasks if t.status == "BLOCKED"]

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Get task by ID."""
        return next((t for t in self.tasks if t.id == task_id), None)

    def get_next_id(self) -> int:
        """Get and increment next available ID."""
        current = self.next_id
        self.next_id += 1
        return current

    def stats(self) -> Dict[str, int]:
        """Get task statistics."""
        return {
            "total": len(self.tasks),
            "pending": len(self.pending_tasks),
            "active": len(self.active_tasks),
            "completed": len(self.completed_tasks),
            "blocked": len(self.blocked_tasks),
            "overdue": len([t for t in self.tasks if t.is_overdue()]),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON storage."""
        return {
            "tasks": [t.to_dict() for t in self.tasks],
            "next_id": self.next_id,
            "last_updated": datetime.now().isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskBucket":
        """Deserialize from dictionary."""
        bucket = cls()
        bucket.next_id = data.get("next_id", 1)
        bucket.last_updated = data.get("last_updated", datetime.now().isoformat())
        bucket.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        return bucket


@dataclass
class Project:
    """Project metadata."""
    id: str
    name: str
    code: str  # 4-5 character abbreviation
    lab: Optional[str] = None
    path: Optional[str] = None
    status: str = "active"  # active, paused, completed
    last_accessed: Optional[str] = None
    has_claude_md: bool = False
    has_readme: bool = False
    has_docs: bool = False
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
