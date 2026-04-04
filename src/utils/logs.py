from __future__ import annotations

import logging
import pathlib
from logging.handlers import RotatingFileHandler

from src.utils.config import config


class LoggerConfigurator:
    __slots__ = (
        "_backup_count",
        "_file_write",
        "_format",
        "_level",
        "_max_bytes",
        "_path",
        "_rotate",
    )

    def __init__(self) -> None:
        logger_config = config.get_logger_config()
        self._rotate: bool = logger_config.get("rotate", False)
        self._path: str = logger_config.get("path", "/logs")
        self._max_bytes: int = logger_config.get("max_bytes", 1000000)
        self._backup_count: int = logger_config.get("backup_count", 3)
        self._level: str = logger_config.get("level", "INFO")
        self._file_write: bool = logger_config.get("file_write", False)
        self._format: bool = logger_config.get("format_full", False)

    @staticmethod
    def _get_level_from_string(level_str: str) -> int:
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return levels.get(level_str.upper(), logging.NOTSET)

    def _setup_formatter_full(self) -> logging.Formatter:
        return logging.Formatter(
            "%(asctime)s.%(msecs)03d] [%(levelname)-5s] [%(process)d] "
            "%(filename)s:%(lineno)d %(funcName)s() - %(message)s",
            datefmt="[%d-%m-%Y] [%H:%M:%S]",
        )

    def _setup_formatter(self) -> logging.Formatter:
        return logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")

    def _setup_handlers(self) -> list[logging.Handler]:
        handlers: list[logging.Handler] = []
        log_path = pathlib.Path(self._path)
        if not log_path.exists():
            log_path.mkdir(parents=True, exist_ok=True)

        level = self._get_level_from_string(self._level)

        if self._rotate:
            log_handler: logging.Handler = RotatingFileHandler(
                f"{self._path}/all_log.log",
                maxBytes=self._max_bytes,
                backupCount=self._backup_count,
            )
        else:
            log_handler = logging.StreamHandler()

        log_handler.setLevel(level)
        formatter = (
            self._setup_formatter_full() if self._format else self._setup_formatter()
        )
        log_handler.setFormatter(formatter)
        handlers.append(log_handler)

        if self._file_write:
            file_handler = logging.FileHandler(
                f"{self._path}/all_log.log",
                mode="w",
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)

        return handlers

    def configure(self) -> None:
        root_logger = logging.getLogger()
        root_logger.setLevel(self._get_level_from_string(self._level))
        root_logger.handlers = self._setup_handlers()
        for logger_name in ("fastapi", "uvicorn.error", "uvicorn.access"):
            logger = logging.getLogger(logger_name)
            logger.propagate = True
            logger.handlers = []
