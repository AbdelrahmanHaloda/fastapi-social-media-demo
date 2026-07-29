"""Centralized logging configuration for the application."""

import logging
from logging.config import dictConfig

from app.config import DevConfig, config


def obfuscate_email(email: str, visible_characters: int) -> str:
    """Mask the local part of an email while preserving its domain.

    Examples:
        obfuscate_email("user@example.com", 2) -> "us**@example.com"
        obfuscate_email("user@example.com", 0) -> "****@example.com"

    Invalid email-like values are returned unchanged.
    """
    local_part, separator, domain = email.partition("@")

    # Without an "@" separator, the value cannot be safely treated as an email.
    if not separator:
        return email

    # Keep the requested length within the local-part boundaries.
    visible_length = min(
        max(visible_characters, 0),
        len(local_part),
    )

    visible_part = local_part[:visible_length]
    masked_part = "*" * (len(local_part) - visible_length)

    return f"{visible_part}{masked_part}@{domain}"


class EmailObfuscationFilter(logging.Filter):
    """Obfuscate an email stored in a LogRecord's structured fields."""

    def __init__(
        self,
        name: str = "",
        visible_characters: int = 2,
    ) -> None:
        # Initialize the standard logging.Filter functionality.
        super().__init__(name)

        # Store the masking policy for use when processing log records.
        self.visible_characters = visible_characters

    def filter(self, record: logging.LogRecord) -> bool:
        """Obfuscate record.email when present and allow the record through."""
        email = getattr(record, "email", None)

        # Only process valid string values. Most log records do not contain
        # an email field and should pass through without modification.
        if isinstance(email, str):
            record.email = obfuscate_email(
                email,
                self.visible_characters,
            )

        # Returning True allows the handler to process the log record.
        return True


handlers = ["default", "rotating_file"]
if isinstance(config, DevConfig):
    handlers = ["default", "rotating_file", "logtail"]

def configure_logging() -> None:
    """Configure environment-specific application logging."""
    is_development = isinstance(config, DevConfig)
    app_log_level = "DEBUG" if is_development else "INFO"

    dictConfig(
        {
            "version": 1,
            # Preserve loggers created by Uvicorn and third-party libraries.
            "disable_existing_loggers": False,
            "filters": {
                # Add the current request's correlation ID to each log record.
                "correlation_id": {
                    "()": "asgi_correlation_id.CorrelationIdFilter",
                    "uuid_length": 8 if is_development else 32,
                    "default_value": "-",
                },
                # Show two local-part characters during development, but mask
                # the complete local part in production-like environments.
                "email_obfuscation": {
                    "()": EmailObfuscationFilter,
                    "visible_characters": 2 if is_development else 0,
                },
            },
            "formatters": {
                # Human-readable output intended for local development.
                "console": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": (
                        "(%(correlation_id)s) %(name)s:%(lineno)d - %(message)s"
                    ),
                },
                # Structured JSON output intended for log files and log
                # aggregation systems.
                "file": {
                    "class": ("pythonjsonlogger.jsonlogger.JsonFormatter"),
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": (
                        "%(asctime)s.%(msecs)03dZ "
                        "%(levelname)s "
                        "%(correlation_id)s "
                        "%(name)s "
                        "%(lineno)d "
                        "%(message)s"
                    ),
                },
            },
            "handlers": {
                # Colored, human-readable console output.
                "default": {
                    "class": "rich.logging.RichHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                    "filters": [
                        "correlation_id",
                        "email_obfuscation",
                    ],
                    "show_path": True,
                },
                # Size-based rotating JSON log files.
                "rotating_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "file",
                    "filters": [
                        "correlation_id",
                        "email_obfuscation",
                    ],
                    "filename": "app.log",
                    # Rotate after 1 MiB and retain the two latest backups.
                    "maxBytes": 1 * 1024 * 1024,
                    "backupCount": 2,
                    "encoding": "utf-8",
                },
                # Cloud Logging - Optional
                "logtail": {
                    "class": "logtail.LogtailHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                    "filters": [
                        "correlation_id",
                        "email_obfuscation",
                    ],
                    "source_token": config.LOGTAIL_API_KEY,
                    "host": config.LOGTAIL_INGESTING_HOST,
                },
            },
            "loggers": {
                # Capture Uvicorn server and access logs.
                "uvicorn": {
                    "handlers": ["default", "rotating_file"],
                    "level": "INFO",
                    "propagate": False,
                },
                # Capture application logs using an environment-specific level.
                "app": {
                    "handlers": handlers,
                    "level": app_log_level,
                    "propagate": False,
                },
                # Reduce noise from the database abstraction layer.
                "databases": {
                    "handlers": ["default"],
                    "level": "WARNING",
                    "propagate": False,
                },
                # Suppress verbose SQLite driver messages.
                "aiosqlite": {
                    "handlers": ["default"],
                    "level": "WARNING",
                    "propagate": False,
                },
            },
        }
    )
