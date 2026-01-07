"""Configuration loading and defaults."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration manager for task system."""

    # Determine data directory (in order of priority)
    @staticmethod
    def _get_data_dir() -> Path:
        """Get data directory from environment, CLI, or default."""
        # 1. Check environment variable
        if env_data_dir := os.getenv("TASK_MANAGER_DATA"):
            return Path(env_data_dir)

        # 2. Use default location (project directory)
        project_dir = Path(__file__).parent.parent.parent  # Go up to project root
        return project_dir / "data"

    # Default configuration
    @classmethod
    def _get_defaults(cls) -> Dict[str, Any]:
        """Get defaults with computed data directory."""
        data_dir = cls._get_data_dir()
        return {
            "task_bucket_path": data_dir / "task-bucket.json",
            "projects_path": data_dir / "projects.json",
            "log_path": data_dir / "logs" / "task.log",
            "log_level": "INFO",
            "date_format": "%Y-%m-%d",
            "time_format": "%H:%M",
            "default_task_type": "work",
            "default_priority": "medium",
            "color_enabled": True,
            "backup_enabled": True,
            "backup_dir": data_dir / "backups",
            "day_start_hour": 6,
        }

    def __init__(self, config_file: Optional[str] = None, data_dir: Optional[str] = None):
        """Initialize configuration from file or defaults."""
        # Override data directory if provided
        if data_dir:
            os.environ["TASK_MANAGER_DATA"] = data_dir

        self.DEFAULTS = self._get_defaults()
        self.config = self.DEFAULTS.copy()

        # Determine config file location
        if config_file:
            self.config_file = Path(config_file)
        else:
            data_directory = self._get_data_dir()
            self.config_file = data_directory / "config.json"

        if self.config_file and Path(self.config_file).exists():
            self._load_from_file()
        else:
            self._create_default_config()

        # Ensure paths are Path objects
        self._normalize_paths()

    def _load_from_file(self) -> None:
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, "r") as f:
                file_config = json.load(f)
                # Filter out 'notes' key and merge
                for key, value in file_config.items():
                    if key != "notes":
                        self.config[key] = value
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config from {self.config_file}: {e}")
            print("Using default configuration")

    def _create_default_config(self) -> None:
        """Create default configuration file."""
        config_file = Path(self.config_file)
        config_file.parent.mkdir(parents=True, exist_ok=True)

        # Prepare data for JSON (convert Path objects to strings)
        config_data = {}
        for key, value in self.DEFAULTS.items():
            config_data[key] = str(value) if isinstance(value, Path) else value

        config_data["notes"] = {
            "date_format": "Python strftime format (e.g., %Y-%m-%d)",
            "time_format": "Python strftime format (e.g., %H:%M)",
            "log_level": "DEBUG, INFO, WARNING, ERROR, CRITICAL",
            "day_start_hour": "Hour when daily tasks reset (6 = 6:00 AM)"
        }

        try:
            with open(config_file, "w") as f:
                json.dump(config_data, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not create config file: {e}")

    def _normalize_paths(self) -> None:
        """Ensure all path configs are Path objects."""
        path_keys = ["task_bucket_path", "projects_path", "log_path", "backup_dir"]
        for key in path_keys:
            if key in self.config:
                value = self.config[key]
                if not isinstance(value, Path):
                    self.config[key] = Path(value).expanduser()

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def get_path(self, key: str) -> Path:
        """Get configuration value as Path."""
        value = self.get(key)
        if isinstance(value, Path):
            return value
        return Path(value).expanduser() if value else None

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        # Create log directory
        log_path = self.get_path("log_path")
        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)

        # Create backup directory
        backup_dir = self.get_path("backup_dir")
        if backup_dir:
            backup_dir.mkdir(parents=True, exist_ok=True)

    def __repr__(self) -> str:
        """String representation of config."""
        return f"Config({self.config_file})"
