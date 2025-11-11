import os
from typing import Any

from dotenv import load_dotenv


class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "_initialized"):
            load_dotenv()  # Load environment variables from .env file
            self._initialized = True

    def get_config(self) -> dict[str, Any]:
        # Return a dictionary with all configuration values
        return {
            "database": self.get_database_config(),
            "server": self.get_server_config(),
            "logger": self.get_logger_config(),
        }

    def get_database_config(self) -> dict[str, Any]:
        return {
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "postgres"),
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "name": os.getenv("DB_NAME", "collagrcms"),
        }

    def get_server_config(self) -> dict[str, Any]:
        return {
            "host": os.getenv("SERVER_HOST", "0.0.0.0"),
            "port": int(os.getenv("SERVER_PORT", "8000")),
            "debug": os.getenv("DEBUG", "False").lower() in ("true", "1", "yes", "on"),
        }

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


# Create a singleton instance
config = Config()
