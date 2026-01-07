"""JSON storage with backups and atomic writes."""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .models import TaskBucket, Task
from .validation import validate_bucket_schema
from .logger import TaskLogger
from .config import Config


class TaskStorage:
    """Handle reading and writing task data."""

    def __init__(self, config: Config):
        """Initialize storage with config."""
        self.config = config
        self.logger = TaskLogger.get()
        self.bucket_path = config.get_path("task_bucket_path")
        self.backup_dir = config.get_path("backup_dir") if config.get("backup_enabled") else None

        # Ensure directories exist
        config.ensure_directories()
        self.bucket_path.parent.mkdir(parents=True, exist_ok=True)
        if self.backup_dir:
            self.backup_dir.mkdir(parents=True, exist_ok=True)

    def load_bucket(self) -> TaskBucket:
        """Load task bucket from file."""
        try:
            if not self.bucket_path.exists():
                self.logger.info(f"Task bucket not found at {self.bucket_path}, creating new")
                return TaskBucket()

            with open(self.bucket_path, "r") as f:
                data = json.load(f)

            # Validate schema
            valid, errors = validate_bucket_schema(data)
            if not valid:
                self.logger.warning(f"Schema validation warnings: {errors}")

            bucket = TaskBucket.from_dict(data)
            self.logger.debug(f"Loaded {len(bucket.tasks)} tasks")
            return bucket

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse task-bucket.json: {e}")
            raise ValueError(f"Invalid JSON in {self.bucket_path}: {e}")
        except Exception as e:
            self.logger.error(f"Failed to load task bucket: {e}")
            raise

    def save_bucket(self, bucket: TaskBucket) -> None:
        """Save task bucket with atomic write and backup."""
        try:
            # Create backup if enabled
            if self.backup_dir and self.bucket_path.exists():
                self._create_backup()

            # Atomic write: write to temp file, then rename
            temp_path = self.bucket_path.with_suffix(".tmp")
            with open(temp_path, "w") as f:
                json.dump(bucket.to_dict(), f, indent=2)

            # Atomic rename
            temp_path.replace(self.bucket_path)

            self.logger.info(f"Saved {len(bucket.tasks)} tasks to {self.bucket_path}")

        except Exception as e:
            self.logger.error(f"Failed to save task bucket: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise

    def _create_backup(self) -> None:
        """Create timestamped backup of current bucket."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"task-bucket.backup.{timestamp}.json"
            shutil.copy2(self.bucket_path, backup_path)
            self.logger.debug(f"Created backup: {backup_path}")

            # Keep only last 10 backups
            self._cleanup_old_backups()

        except Exception as e:
            self.logger.warning(f"Failed to create backup: {e}")

    def _cleanup_old_backups(self, keep: int = 10) -> None:
        """Remove old backups, keeping only the most recent."""
        try:
            if not self.backup_dir.exists():
                return

            backups = sorted(self.backup_dir.glob("task-bucket.backup.*.json"))
            if len(backups) > keep:
                for old_backup in backups[:-keep]:
                    old_backup.unlink()
                    self.logger.debug(f"Removed old backup: {old_backup}")

        except Exception as e:
            self.logger.warning(f"Failed to cleanup old backups: {e}")

    def load_projects(self) -> Dict[str, Any]:
        """Load projects configuration."""
        projects_path = self.config.get_path("projects_path")
        try:
            if not projects_path.exists():
                self.logger.debug(f"Projects file not found at {projects_path}")
                return {}

            with open(projects_path, "r") as f:
                data = json.load(f)

            # Handle both formats: top-level dict or wrapped in "projects" key
            if "projects" in data:
                projects = data["projects"]
            else:
                projects = data

            self.logger.debug(f"Loaded {len(projects)} projects")
            return projects

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse projects.json: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Failed to load projects: {e}")
            return {}

    def project_exists(self, project_id: str) -> bool:
        """Check if project exists."""
        projects = self.load_projects()
        return project_id in projects

    def get_project_name(self, project_id: str) -> Optional[str]:
        """Get human-readable project name."""
        projects = self.load_projects()
        if project_id in projects:
            return projects[project_id].get("name", project_id)
        return None

    def get_project_codes(self) -> Dict[str, str]:
        """Get mapping of project_id to project_code."""
        projects = self.load_projects()
        codes = {}
        for project_id, project_data in projects.items():
            code = project_data.get("code", project_id[:5])  # Default to first 5 chars if no code
            codes[project_id] = code
        return codes

    def resolve_project_identifier(self, identifier: str) -> Optional[str]:
        """Resolve a project identifier (ID or code) to project ID.

        Args:
            identifier: Project ID or project code

        Returns:
            The project ID if found, None otherwise
        """
        projects = self.load_projects()

        # Check if it's a direct project ID match
        if identifier in projects:
            return identifier

        # Check if it matches a project code (case-insensitive)
        identifier_upper = identifier.upper()
        for project_id, project_data in projects.items():
            code = project_data.get("code", "")
            if code.upper() == identifier_upper:
                return project_id

        return None

    def save_projects(self, projects: Dict[str, Any]) -> None:
        """Save projects configuration."""
        projects_path = self.config.get_path("projects_path")
        try:
            # Wrap in "projects" key if it's not already wrapped
            if "projects" not in projects and projects:
                data = {"projects": projects}
            else:
                data = projects

            with open(projects_path, "w") as f:
                json.dump(data, f, indent=2)

            self.logger.debug(f"Saved {len(projects)} projects")

        except Exception as e:
            self.logger.error(f"Failed to save projects: {e}")
            raise
