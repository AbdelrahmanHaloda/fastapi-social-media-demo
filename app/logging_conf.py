"""Central logging configuration for application modules."""

from logging.config import dictConfig

from app.config import DevConfig, config


def configure_logging() -> None:
    """Configure environment-specific console logging for the application."""

    log_level = "DEBUG" if isinstance(config, DevConfig) else "INFO"

    dictConfig(
        {
            "version": 1,
            # Preserve loggers configured by Uvicorn and installed libraries.
            "disable_existing_loggers": False,
            "filters": {
                "correlation_id": {
                    "()": "asgi_correlation_id.CorrelationIdFilter",
                    "uuid_length": 8 if isinstance(config, DevConfig) else 32,
                    "default_value": "-",
                },
            },
            "formatters": {
                "console": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "(%(correlation_id)s) %(name)s:%(lineno)d - %(message)s",
                },
                "file": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "%(asctime)s.%(msecs)03dZ | %(levelname)-8s | [%(correlation_id)s] %(name)s:%(lineno)d - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "class": "rich.logging.RichHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                    "filters": ["correlation_id"],
                    # Source information is already included by the formatter.
                    "show_path": True,
                },
                "rotating_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "file",
                    "filename": "app.log",
                    "maxBytes": 1024 * 1024 * 1,  # in bytes (1 mega bytes)
                    "backupCount": 2,
                    "encoding": "utf8",
                    "filters": ["correlation_id"],
                },
            },
            "loggers": {
                # Use the shared console handler for Uvicorn server and access logs.
                "uvicorn": {
                    "handlers": ["default", "rotating_file"],
                    "level": "INFO",
                    "propagate": False,
                },
                # Enable environment-specific logging for app and its child modules.
                "app": {
                    "handlers": ["default", "rotating_file"],
                    "level": log_level,
                    "propagate": False,
                },
                # Report only warnings and errors from the database abstraction layer.
                "databases": {
                    "handlers": ["default"],
                    "level": "WARNING",
                    "propagate": False,
                },
                # Suppress verbose SQLite driver messages during normal operation.
                "aiosqlite": {
                    "handlers": ["default"],
                    "level": "WARNING",
                    "propagate": False,
                },
            },
        }
    )
