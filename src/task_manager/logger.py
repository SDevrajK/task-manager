"""Logging setup and utilities."""

import logging
from pathlib import Path
from typing import Optional
from .config import Config


class TaskLogger:
    """Logger for task operations."""

    _logger: Optional[logging.Logger] = None
    _config: Optional[Config] = None

    @classmethod
    def setup(cls, config: Config) -> logging.Logger:
        """Initialize logger with config."""
        cls._config = config
        log_path = config.get_path("log_path")
        log_level = config.get("log_level", "INFO")

        # Ensure log directory exists
        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)

        # Create logger
        logger = logging.getLogger("task")
        logger.setLevel(getattr(logging, log_level))

        # Clear existing handlers
        logger.handlers = []

        # File handler
        if log_path:
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(getattr(logging, log_level))
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        # Console handler (for verbose output)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter("%(levelname)s: %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        cls._logger = logger
        return logger

    @classmethod
    def get(cls) -> logging.Logger:
        """Get logger instance."""
        if cls._logger is None:
            config = Config()
            cls.setup(config)
        return cls._logger

    @classmethod
    def log_operation(cls, operation: str, details: str) -> None:
        """Log an operation."""
        logger = cls.get()
        logger.info(f"{operation}: {details}")

    @classmethod
    def log_error(cls, operation: str, error: str) -> None:
        """Log an error."""
        logger = cls.get()
        logger.error(f"{operation}: {error}")

    @classmethod
    def log_debug(cls, message: str) -> None:
        """Log debug message."""
        logger = cls.get()
        logger.debug(message)
