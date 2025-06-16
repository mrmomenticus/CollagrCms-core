import asyncio
import logging

import uvicorn
from src.database.connection import db
from src.database.queries.base import BaseQueries
from src.database.queries.init_db import InitDatabase
from src.utils.config import config
from src.routers.api import api


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


# TODO: вынести
def create_url() -> str:
    db_config = config.get_database_config()
    return (
        f"{db_config['type']}://{db_config['user']}:{db_config['password']}@"
        f"{db_config['host']}:{db_config['port']}/{db_config['name']}"
    )


async def async_main():
    setup_logging()
    config.load()

    # Инициализация базы данных
    await db.connect(create_url())
    schema = InitDatabase()
    await schema.initialize()

    try:
        server_config = config.get_server_config()
        server = uvicorn.Server(
            config=uvicorn.Config(
                "src.routers.api:api",
                host=server_config.get("host", "0.0.0.0"),
                port=server_config.get("port", 8000),
                log_level="debug" if server_config.get("debug", False) else "info",
            )
        )
        await server.serve()
    finally:
        await db.close()


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
