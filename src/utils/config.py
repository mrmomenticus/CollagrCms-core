import os
from pathlib import Path
from typing import Any, Self

from dotenv import load_dotenv


class Config:
    _instance = None

    def __new__(cls) -> Self:
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
        return os.getenv("DIRECTUS_URL", "http://localhost:8055")

    def get_collage_output_dir(self) -> Path:
        """Returns the directory path for storing generated collages.
        
        Creates the directory if it doesn't exist.
        """
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


# Create a singleton instance
config = Config()
