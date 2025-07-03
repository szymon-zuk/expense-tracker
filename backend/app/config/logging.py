import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Dict

from backend.app.config.settings import get_settings

settings = get_settings()


def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration based on environment"""

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "{asctime} | {levelname:8} | {name:15} | {module}:{lineno} | {message}",
                "style": "{",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {
                "format": "{levelname:8} | {name:15} | {message}",
                "style": "{",
            },
            "json": {
                "()": "pythonjsonlogger.json.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(module)s %(lineno)d %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO" if settings.MODE.value == "PRODUCTION" else "DEBUG",
                "formatter": "simple",
                "stream": sys.stdout,
            },
            "file_info": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "file_error": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": "logs/errors.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
        },
        "loggers": {
            # Root logger
            "": {
                "level": "DEBUG" if settings.DEBUG else "INFO",
                "handlers": ["console", "file_info", "file_error"],
                "propagate": False,
            },
            # App-specific loggers
            "expense_tracker": {
                "level": "DEBUG" if settings.DEBUG else "INFO",
                "handlers": ["console", "file_info", "file_error"],
                "propagate": False,
            },
            "expense_tracker.auth": {
                "level": "DEBUG",
                "handlers": ["console", "file_info", "file_error"],
                "propagate": False,
            },
            "expense_tracker.jwt": {
                "level": "DEBUG",
                "handlers": ["console", "file_info", "file_error"],
                "propagate": False,
            },
            "expense_tracker.oauth": {
                "level": "DEBUG",
                "handlers": ["console", "file_info", "file_error"],
                "propagate": False,
            },
            "expense_tracker.db": {
                "level": "INFO",
                "handlers": ["console", "file_info", "file_error"],
                "propagate": False,
            },
            # Third-party loggers
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file_info"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["file_info"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING" if settings.MODE.value == "PRODUCTION" else "INFO",
                "handlers": ["file_info"],
                "propagate": False,
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console", "file_info"],
                "propagate": False,
            },
        },
    }

    # Adjust for production
    if settings.MODE.value == "PRODUCTION":
        # Less verbose console logging in production
        config["handlers"]["console"]["level"] = "WARNING"
        # Add JSON formatter for production logs
        config["handlers"]["file_json"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": "logs/app.json",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "encoding": "utf8",
        }
        # Add JSON handler to loggers
        for logger_config in config["loggers"].values():
            if "file_info" in logger_config["handlers"]:
                logger_config["handlers"].append("file_json")

    return config


def setup_logging():
    """Initialize logging configuration"""
    config = get_logging_config()
    logging.config.dictConfig(config)

    # Get the main app logger and log startup
    logger = logging.getLogger("expense_tracker")
    logger.info(f"🚀 Expense Tracker API starting in {settings.MODE.value} mode")
    logger.info(f"📝 Debug mode: {settings.DEBUG}")
    logger.info(f"📁 Logs directory: logs/")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(f"expense_tracker.{name}")
