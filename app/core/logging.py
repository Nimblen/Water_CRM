import os
import sys
import socket
import logging
import logging.config
from pathlib import Path
import structlog
from app.core.context import get_trace_id, get_request_id, get_worker_id, get_user_id



LOG_DIR = Path("logs")

LOG_DIR.mkdir(exist_ok=True)

HOSTNAME = socket.gethostname()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")




class DropHealthcheckFilter(logging.Filter):    
    def filter(self, record):
        return "/health" not in record.getMessage()
    

class SensitiveDataFilter(logging.Filter):

    SECRET_FIELDS = {
        "password",
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "set-cookie",
        "jwt",
        "api-key",
    }

    def filter(self, record):
        if hasattr(record, "msg"):
            msg = str(record.msg).lower()

            for secret in self.SECRET_FIELDS:
                if secret in msg:
                    record.msg = record.msg.replace(secret, "REDACTED")
        return True
    


def add_context(_, __, event_dict):
    event_dict["trace_id"] = get_trace_id()
    event_dict["request_id"] = get_request_id()
    event_dict["user_id"] = get_user_id()
    event_dict["worker_id"] = get_worker_id()
    event_dict["hostname"] = HOSTNAME
    return event_dict


def setup_logger():
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
        add_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.JSONRenderer(),
        structlog.processors.format_exc_info,
    ]

    logging_config = {
        "version":1,
        "disable_existing_loggers": False,
        "filters": {
            "drop_healthcheck": {
                "()": DropHealthcheckFilter,
            },
            "sensitive_data": {
                "()": SensitiveDataFilter,
            },
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
                "filters": ["drop_healthcheck", "sensitive_data"],
            },
            "error_console": {
                "class": "logging.StreamHandler",
                "level": "ERROR",
                "formatter": "console",
                "stream": sys.stderr,
                "filters": ["drop_healthcheck", "sensitive_data"],
            },
            "debug_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "json",
                "filename": LOG_DIR / "debug.log",
                "maxBytes": 10485760,
                "backupCount": 5,
                "filters": ["drop_healthcheck", "sensitive_data"],
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": LOG_DIR / "error.log",
                "maxBytes": 10485760,
                "backupCount": 5,
                "filters": ["drop_healthcheck", "sensitive_data"],
            },
            "warning_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "WARNING",
                "formatter": "json",
                "filename": LOG_DIR / "warning.log",
                "maxBytes": 10485760,
                "backupCount": 5,
                "filters": ["drop_healthcheck", "sensitive_data"],
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "debug_file", "error_console", "error_file", "warning_file"],
                "level": LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console", "debug_file"],
                "level": LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn.error": {
                "level": LOG_LEVEL,
                "handlers": ["error_console", "error_file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": LOG_LEVEL,
                "handlers": ["console", "debug_file"],
                "propagate": False,
            },
            "celery":{
                "handlers": ["console", "debug_file", "error_file"],
                "level": LOG_LEVEL,
                "propagate": False
            }
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
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],

        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)