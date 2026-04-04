from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()


class _Config:
    __slots__ = ()

    def get_config(self) -> dict[str, Any]:
        return {
            "server": self.get_server_config(),
            "logger": self.get_logger_config(),
        }

    def get_server_config(self) -> dict[str, Any]:
        return {
            "host": os.getenv("SERVER_HOST", "0.0.0.0"),
            "port": int(os.getenv("SERVER_PORT", "8000")),
            "debug": os.getenv("DEBUG", "False").lower() in ("true", "1", "yes", "on"),
        }

    def get_directus_url(self) -> str:
        return os.getenv("DIRECTUS_URL", "http://localhost")

    def get_collage_output_dir(self) -> Path:
        output_dir = Path(os.getenv("COLLAGE_OUTPUT_DIR", "./output"))
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def get_logger_config(self) -> dict[str, Any]:
        return {
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "rotate": os.getenv("LOG_ROTATE", "False").lower()
            in ("true", "1", "yes", "on"),
            "path": os.getenv("LOG_PATH", "./logs"),
            "max_bytes": int(os.getenv("LOG_MAX_BYTES", "1000000")),
            "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "3")),
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "file_write": os.getenv("LOG_FILE_WRITE", "False").lower()
            in ("true", "1", "yes", "on"),
            "format_full": os.getenv("LOG_FORMAT_FULL", "True").lower()
            in ("true", "1", "yes", "on"),
        }


config = _Config()
