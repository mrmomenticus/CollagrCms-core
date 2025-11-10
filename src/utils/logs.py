import logging
import os
import pathlib
from logging.handlers import RotatingFileHandler

from src.utils.config import config


class LoggerConfigurator:
    def __init__(self) -> None:
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(
            self._get_level_from_string(
                config.get_logger_config().get("log_level", "INFO"),
            ),
        )
        self._rotate: bool = config.get_logger_config().get("rotate", False)
        self._path: str = config.get_logger_config().get("path", "/logs")
        self._max_bytes: int = config.get_logger_config().get("max_bytes", 1000000)
        self._backup_count: int = config.get_logger_config().get("backup_count", 3)
        self._level: str = config.get_logger_config().get("level", "INFO")
        self._file_write: bool = config.get_logger_config().get("file_write", False)
        self._format: bool = config.get_logger_config().get("format_full", False)

    def _get_level_from_string(self, level_str):
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return levels.get(level_str.upper(), logging.NOTSET)

    def _setup_formatter_full(self):
        return logging.Formatter(
            "%(asctime)s.%(msecs)03d] [%(levelname)-5s] [%(process)d] "
            "%(filename)s:%(lineno)d %(funcName)s() - %(message)s",
            datefmt="[%d-%m-%Y] [%H:%M:%S",
        )

    def _setup_formatter(self):
        return logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")

    def _setup_handlers(self):
        handlers = []
        if self._rotate:
            if not pathlib.Path(self._path).exists():
                pathlib.Path(self._path).mkdir(parents=True)
            log_handler = RotatingFileHandler(
                f"{self._path}/all_log.log",
                maxBytes=self._max_bytes,
                backupCount=self._backup_count,
            )
        else:
            log_handler = logging.FileHandler(
                f"{self._path}/all_log_{os.getpid()}.log", mode="w",
            )

        log_handler.setLevel(self._get_level_from_string(self._level))
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(self._get_level_from_string(self._level))
        if self._format:
            log_handler.setFormatter(self._setup_formatter())
            stream_handler.setFormatter(self._setup_formatter())
        else:
            log_handler.setFormatter(self._setup_formatter_full())
            stream_handler.setFormatter(self._setup_formatter_full())

        handlers.append(log_handler)
        if self._file_write:
            handlers.append(stream_handler)

        return handlers

    def configure(self):
        self.root_logger.handlers = self._setup_handlers()
        # Логгеры FastAPI и Uvicorn будут писать в файл
        for logger_name in ("fastapi", "uvicorn.error", "uvicorn.access"):
            logger = logging.getLogger(logger_name)
            logger.propagate = True
            logger.handlers = []  # Удаляем их стандартные хендлеры, чтобы не было дублей
