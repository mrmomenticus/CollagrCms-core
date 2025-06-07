import asyncio
import logging
from src.database.connection import db
from src.utils.config import config


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def create_url() -> str:
    db_config = config.get_database_config()
    return (f"{db_config['type']}://{db_config['user']}:{db_config['password']}@"
            f"{db_config['host']}:{db_config['port']}/{db_config['name']}")


# async def init_app() -> FastAPI:
#     app = FastAPI(title="CollagrCMS")
#     app.include_router(api)
#     return app


async def main():
    # Setup logging
    setup_logging()
    
    # Load configuration
    config.load()
    
    # Initialize database connection
    await db.connect(create_url())
    
    # try:
    #     # Create FastAPI application
    #     # app = await init_app()
        
    #     # Get server configuration
    #     server_config = config.get_server_config()
        
    #     # Run the server
    #     uvicorn.run(
    #         app,
    #         host=server_config.get('host', '0.0.0.0'),
    #         port=server_config.get('port', 8000),
    #         log_level='debug' if server_config.get('debug', False) else 'info'
    #     )
    # finally:
    #     await db.close()


if __name__ == "__main__":
    asyncio.run(main())

