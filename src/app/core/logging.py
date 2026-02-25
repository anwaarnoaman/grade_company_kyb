import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.core.config import settings

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


class LevelFilter(logging.Filter):
    """Filter logs by level."""
    def __init__(self, level: int):
        self.level = level
        super().__init__()

    def filter(self, record: logging.LogRecord) -> bool:
        # Only pass records that match the specified level
        if self.level == logging.INFO:  # include DEBUG + INFO
            return record.levelno <= logging.INFO
        return record.levelno == self.level


def setup_logging() -> None:
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handlers: list[logging.Handler] = []

    # ---- Console handler (always on) ----
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handlers.append(console_handler)

    # ---- File handlers (optional) ----
    if settings.log_to_file:
        log_dir = Path(settings.log_file_path)
        log_dir.parent.mkdir(parents=True, exist_ok=True)

        # Info + Debug log
        info_handler = RotatingFileHandler(
            filename=log_dir.parent / "info.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        info_handler.setLevel(logging.DEBUG)
        info_handler.addFilter(LevelFilter(logging.INFO))
        info_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handlers.append(info_handler)

        # Warning log
        warning_handler = RotatingFileHandler(
            filename=log_dir.parent / "warning.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        warning_handler.setLevel(logging.WARNING)
        warning_handler.addFilter(LevelFilter(logging.WARNING))
        warning_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handlers.append(warning_handler)

        # Error log
        error_handler = RotatingFileHandler(
            filename=log_dir.parent / "error.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.addFilter(LevelFilter(logging.ERROR))
        error_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handlers.append(error_handler)

    logging.basicConfig(
        level=log_level,
        handlers=handlers,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)