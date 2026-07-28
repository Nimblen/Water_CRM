import os
import sys
import socket
import logging
import logging.config
from pathlib import Path

import structlog

from app.core.context import get_trace_id, get_request_id
LOG_DIR = Path(os.getenv("LOG_DIR", "/var/log/app"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

HOSTNAME = socket.gethostname()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

WORKER_ID = os.getenv("WORKER_ID", str(os.getpid()))


class DropHealthcheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "/health" not in record.getMessage()

SECRET_KEYS = {
    "password",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "set-cookie",
    "cookie",
    "jwt",
    "api_key",
    "api-key",
}


def mask_secrets(_, __, event_dict: dict) -> dict:
    def _scrub(value):
        if isinstance(value, dict):
            return {
                k: ("REDACTED" if k.lower() in SECRET_KEYS else _scrub(v))
                for k, v in value.items()
            }
        if isinstance(value, list):
            return [_scrub(v) for v in value]
        return value

    return _scrub(event_dict)


def add_context(_, __, event_dict: dict) -> dict:
    event_dict["trace_id"] = get_trace_id()
    event_dict["request_id"] = get_request_id()
    event_dict["worker_id"] = WORKER_ID
    event_dict["hostname"] = HOSTNAME
    return event_dict


def setup_logger() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
        add_context,
        mask_secrets,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    logging_config = {
        "version":1,
        "disable_existing_loggers": False,
        "filters": {
            "drop_healthcheck": {"()": DropHealthcheckFilter},
        },
        "formatters": {
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
                "foreign_pre_chain": shared_processors,
            },
            "console": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(colors=True),
                "foreign_pre_chain": shared_processors,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": LOG_LEVEL,
                "formatter": "console",
                "stream": sys.stdout,
                "filters": ["drop_healthcheck"],
            },
            "error_console": {
                "class": "logging.StreamHandler",
                "level": "ERROR",
                "formatter": "console",
                "stream": sys.stderr,
                "filters": ["drop_healthcheck"],
            },
            "json_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": LOG_LEVEL,
                "formatter": "json",
                "filename": LOG_DIR / "app.log",
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
                "filters": ["drop_healthcheck"],
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": LOG_DIR / "error.log",
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
                "filters": ["drop_healthcheck"],
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "json_file", "error_console", "error_file"],
                "level": LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console", "json_file"],
                "level": LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["error_console", "error_file"],
                "level": LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console", "json_file"],
                "level": LOG_LEVEL,
                "propagate": False,
            },
            "celery":{
                "handlers": ["console", "json_file", "error_file"],
                "level": LOG_LEVEL,
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            timestamper,
            add_context,
            mask_secrets,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)