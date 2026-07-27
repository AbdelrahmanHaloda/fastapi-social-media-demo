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
            "formatters": {
                "console": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "%(name)s:%(lineno)d - %(message)s",
                }
            },
            "handlers": {
                "default": {
                    "class": "rich.logging.RichHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                    # Source information is already included by the formatter.
                    "show_path": False,
                }
            },
           "loggers": {
                # Use the shared console handler for Uvicorn server and access logs.
                "uvicorn": {
                    "handlers": ["default"],
                    "level": "INFO",
                    "propagate": False,
                },
                # Enable environment-specific logging for app and its child modules.
                "app": {
                    "handlers": ["default"],
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
