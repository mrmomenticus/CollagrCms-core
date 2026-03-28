import pathlib

import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers.collages import router as collages_router
from src.routers.images import router as images_router

# Создаем основное приложение FastAPI


app = FastAPI(
    title="CollagrCms API",
    version="0.1.0",
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

# Подключаем роутеры для коллажей и изображений
app.include_router(collages_router)
app.include_router(images_router)


with pathlib.Path("docs/openapi.yaml").open("w") as f:
    yaml.dump(app.openapi(), f, indent=3)
