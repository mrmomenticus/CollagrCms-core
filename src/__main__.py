from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers.collages import router as collages_router
from src.utils.config import config
from src.utils.logs import LoggerConfigurator


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Lifespan context manager for startup/shutdown events."""
    LoggerConfigurator().configure()
    yield None


def create_app() -> FastAPI:
    """Создает и настраивает FastAPI приложение."""
    application = FastAPI(
        title="CollagrCms API",
        version="0.2.0",
        description="API для генерации коллажей",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(collages_router)

    return application


app = create_app()


def main() -> None:
    """Entry point для запуска приложения."""
    server_config = config.get_server_config()
    uvicorn.run(
        "src.__main__:app",
        host=server_config.get("host", "0.0.0.0"),
        port=server_config.get("port", 8000),
        log_level="debug" if server_config.get("debug", False) else "info",
    )


if __name__ == "__main__":
    main()
