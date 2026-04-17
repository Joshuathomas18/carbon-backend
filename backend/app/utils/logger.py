"""Logging configuration."""

import json
import logging
import sys
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if record.extra:
            log_data.update(record.extra)

        return json.dumps(log_data)


def setup_logging(level: str = "INFO") -> None:
    """Set up logging configuration."""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)


def get_logger(name: str) -> logging.LoggerAdapter:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
