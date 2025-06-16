import asyncio
import logging

import uvicorn
from src.database.connection import db
from src.database.queries.base import BaseQueries
from src.database.init_db import InitDatabase
from src.utils.config import config
from src.routers.api import api


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def create_url() -> str:
    db_config = config.get_database_config()
    return (
        f"{db_config['type']}://{db_config['user']}:{db_config['password']}@"
        f"{db_config['host']}:{db_config['port']}/{db_config['name']}"
    )


async def main():
    # Setup logging
    setup_logging()

    # Load configuration
    config.load()

    # Initialize database connection
    await db.connect(create_url())
    schema = InitDatabase()
    await schema.initialize()

    # try:
    #     # Create FastAPI application

    #     # Get server configuration
    #     server_config = config.get_server_config()

    #     # Run the server
    #     uvicorn.run(
    #         "",
    #         host=server_config.get("host", "0.0.0.0"),
    #         port=server_config.get("port", 8000),
    #         log_level="debug" if server_config.get("debug", False) else "info",
    #     )
    # finally:
    #     await db.close()


if __name__ == "__main__":
    asyncio.run(main())
