import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers.collages import router as collages_router
from src.utils.config import config
from src.utils.logs import LoggerConfigurator

# Создаем основное приложение FastAPI
app = FastAPI(
    title="CollagrCms API",
    version="0.2.0",
    description="API для генерации коллажей",
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

# Подключаем роутер для коллажей
app.include_router(collages_router)


@app.on_event("startup")
def startup_event() -> None:
    """Настройка логирования при запуске приложения."""
    LoggerConfigurator().configure()


if __name__ == "__main__":
    # Запуск через uvicorn
    server_config = config.get_server_config()
    LoggerConfigurator().configure()
    uvicorn.run(
        "src.__main__:app",
        host=server_config.get("host", "0.0.0.0"),
        port=server_config.get("port", 8000),
        log_level="debug" if server_config.get("debug", False) else "info",
    )
