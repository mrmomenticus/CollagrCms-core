import logging
import yaml
from argparse import ArgumentParser
from typing import Dict, Any, Optional


class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "_initialized"):
            self._parser = ArgumentParser(description="CollagrCMS Backend Service")
            self._init_args()
            self._args: Optional[Any] = None
            self._config: Dict[str, Any] = {}
            self._initialized = True

    def _init_args(self) -> None:
        self._parser.add_argument(
            "-c", "--config", type=str, required=True, help="Path to configuration file"
        )

    def parse_args(self) -> None:
        if self._args is None:
            logging.debug("Parsing command line arguments")
            self._args = self._parser.parse_args()

    def load(self) -> None:
        self.parse_args()  # Убедимся, что аргументы распарсены

        if not self._args or not hasattr(self._args, "config"):
            raise ValueError(
                "Configuration file path not provided. Use -c or --config option."
            )

        try:
            with open(self._args.config, "r") as f:
                self._config = yaml.safe_load(f)
                logging.debug("Configuration loaded successfully")
        except FileNotFoundError:
            logging.error(f"Configuration file not found: {self._args.config}")
            raise
        except yaml.YAMLError as e:
            logging.error(f"Error parsing configuration file: {e}")
            raise

    def get_config(self) -> Dict[str, Any]:
        if not self._config:
            self.load()
        return self._config

    def get_database_config(self) -> Dict[str, Any]:
        return self.get_config().get("database", {})

    def get_server_config(self) -> Dict[str, Any]:
        return self.get_config().get("server", {})


# Create a singleton instance
config = Config()
