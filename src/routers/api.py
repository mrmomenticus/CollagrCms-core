from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from src.routers.categories import router as categories_router
from src.routers.products import router as products_router
from src.routers.images import router as images_router
from src.routers.collages import router as collages_router


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
