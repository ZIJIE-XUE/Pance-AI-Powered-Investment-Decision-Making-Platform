"""Structured logging configuration using structlog."""

import logging
import structlog


def setup_logging() -> None:
    """Configure structlog for structured JSON logging."""
    from config.settings import settings

    # Set the log level on the standard library
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # Merge extra kwargs into the event dict BEFORE rendering
            # so they never reach logging.Logger._log().
            structlog.stdlib.ExtraAdder(),
            structlog.dev.ConsoleRenderer()
            if settings.LOG_LEVEL.upper() == "DEBUG"
            else structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger for the given module name."""
    return structlog.get_logger(name)
