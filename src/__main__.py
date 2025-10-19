import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.routers.categories import router as categories_router
from src.routers.products import router as products_router
from src.routers.images import router as images_router
from src.routers.collages import router as collages_router
from src.utils.config import config
from src.utils.logs import LoggerConfigurator
from src.database.connection import db

# Создаем основное приложение FastAPI
app = FastAPI(
    title="CollagrCms API",
    version="0.2.0",
    description="Рефакторированный API для системы управления коллажами",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Добавляем поддержку CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене следует указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры для каждого модуля
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(images_router)
app.include_router(collages_router)


def create_url() -> str:
    db_config = config.get_database_config()
    return (
        f"postgresql+asyncpg://{db_config['user']}:{db_config['password']}@"
        f"{db_config['host']}:{db_config['port']}/{db_config['name']}"
    )


@app.on_event("startup")
async def startup_event():
    LoggerConfigurator().configure()
    # Инициализация базы данных
    await db.connect(create_url())
    await db.init_database()


@app.on_event("shutdown")
async def shutdown_event():
    await db.close()


if __name__ == "__main__":
    # Запуск через uvicorn
    server_config = config.get_server_config()
    uvicorn.run(
        "src.__main__:app",
        host=server_config.get("host", "0.0.0.0"),
        port=server_config.get("port", 8000),
        log_level="debug" if server_config.get("debug", False) else "info",
    )
