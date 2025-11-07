"""Secure logging configuration."""
import logging
import sys
from typing import Any
import json


class SecureJSONFormatter(logging.Formatter):
    """JSON formatter that masks sensitive data."""

    SENSITIVE_FIELDS = {
        "access_token",
        "token",
        "client_secret",
        "secret",
        "password",
        "authorization",
        "x-consent-id",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record, masking sensitive fields."""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields, but mask sensitive ones
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "created", "filename", "funcName", "levelname", "levelno", "lineno", "module", "msecs", "message", "pathname", "process", "processName", "relativeCreated", "thread", "threadName", "exc_info", "exc_text", "stack_info"]:
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                    if isinstance(value, str):
                        log_data[key] = self._mask_value(value)
                    else:
                        log_data[key] = "***"
                else:
                    log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

    @staticmethod
    def _mask_value(value: str) -> str:
        """Mask sensitive value."""
        if not value or len(value) <= 4:
            return "***"
        return "*" * (len(value) - 4) + value[-4:]


def setup_logging() -> None:
    """Setup secure logging configuration."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(SecureJSONFormatter())
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

