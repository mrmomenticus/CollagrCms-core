import asyncio
import logging
import uvicorn
from src.database.connection import db
from src.utils.config import config


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)-8s %(filename)s:%(lineno)d %(funcName)s %(message)s",
    )


def create_url() -> str:
    db_config = config.get_database_config()
    return (
        f"postgresql+asyncpg://{db_config['user']}:{db_config['password']}@"
        f"{db_config['host']}:{db_config['port']}/{db_config['name']}"
    )


async def async_main():
    setup_logging()
    config.load()

    # Инициализация базы данных
    await db.connect(create_url())
    await db.init_database()

    try:
        server_config = config.get_server_config()
        server = uvicorn.Server(
            config=uvicorn.Config(
                "src.routers.api:api",
                host=server_config.get("host", "0.0.0.0"),
                port=server_config.get("port", 8000),
                log_level="debug" if server_config.get("debug", False) else "info",
                reload=True
            )
        )
        await server.serve()
    finally:
        await db.close()


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
