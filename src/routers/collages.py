import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.background import BackgroundTasks
from fastapi.responses import FileResponse

from src.core.collages import CollageService
from src.core.directus_client import DirectusClient
from src.models.models import (
    CollageRequest,
    CollageWithLayoutRequest,
    DirectusConfig,
)

router = APIRouter(prefix="/v1/collage", tags=["collages"])
log = logging.getLogger(__name__)


def _cleanup_file(path: str) -> None:
    """Удаляет файл если он существует."""
    if path and Path(path).exists():
        try:
            Path(path).unlink()
            log.debug("Файл коллажа удален: %s", path)
        except Exception as e:
            log.warning("Не удалось удалить файл коллажа %s: %s", path, e)


@router.post("/generate")
async def generate_collage_from_data(
    request: CollageRequest,
    background_tasks: BackgroundTasks,
) -> FileResponse:
    """Генерирует коллаж из переданных данных об изображениях.

    Оптимизированный endpoint, который принимает все данные от фронтенда
    и не требует дополнительных запросов к Directus.

    Args:
        request: Запрос с данными об изображениях и параметрах коллажа
        background_tasks: Background tasks for cleanup

    Returns:
        Файл коллажа в формате JPEG

    Raises:
        HTTPException: 422 - Неверное количество изображений
        HTTPException: 500 - Ошибка создания коллажа

    """
    log.info(
        "API запрос: генерация коллажа из %d изображений",
        len(request.images),
    )

    collage_path = await CollageService.create_collage_from_data(
        request.images,
        request.is_price,
    )
    log.info("API ответ: коллаж создан по пути %s", collage_path)

    background_tasks.add_task(_cleanup_file, collage_path)

    return FileResponse(
        collage_path,
        media_type="image/jpeg",
        filename="collage.jpg",
    )


@router.post("/generate/with-layout")
async def generate_collage_with_layout(
    request: CollageWithLayoutRequest,
    background_tasks: BackgroundTasks,
) -> FileResponse:
    """Генерирует коллаж с пользовательским макетом.

    Принимает данные об изображениях, макет холста и настройки отображения.
    Позволяет создавать коллажи с произвольным расположением ячеек,
    текстовыми надписями и настройками отображения.

    Args:
        request: Запрос с данными об изображениях, макете и настройках
        background_tasks: Background tasks for cleanup

    Returns:
        Файл коллажа в формате JPEG

    Raises:
        HTTPException: 422 - Неверное количество изображений или макет
        HTTPException: 500 - Ошибка создания коллажа

    """
    log.info(
        "API запрос: генерация коллажа с макетом (%d изображений, %d ячеек)",
        len(request.images),
        len(request.layout.cells),
    )

    collage_path = await CollageService.create_collage_with_layout(
        request.images,
        request.layout,
        request.settings,
    )
    log.info("API ответ: коллаж с макетом создан по пути %s", collage_path)

    background_tasks.add_task(_cleanup_file, collage_path)

    return FileResponse(
        collage_path,
        media_type="image/jpeg",
        filename="collage.jpg",
    )


@router.post("/generate/from-directus")
async def generate_collage_from_directus(
    directus_url: str = Query(..., description="URL Directus API"),
    directus_token: str | None = Query(None, description="Токен авторизации"),
    directus_email: str | None = Query(None, description="Email для авторизации"),
    directus_password: str | None = Query(None, description="Пароль для авторизации"),
    product_ids: list[int] | None = Query(None, description="Список ID продуктов"),
    category_ids: list[int] | None = Query(None, description="Список ID категорий"),
    is_price: bool = Query(True, description="Добавлять ли цену на оверлей"),
    background_tasks: BackgroundTasks = None,
) -> FileResponse:
    """Генерирует коллаж, получая данные напрямую из Directus.

    Оптимизированный endpoint, который делает один запрос к Directus
    для получения всех необходимых данных.

    Args:
        directus_url: URL Directus API
        directus_token: Токен авторизации (опционально)
        directus_email: Email для авторизации (опционально)
        directus_password: Пароль для авторизации (опционально)
        product_ids: Список ID продуктов (опционально)
        category_ids: Список ID категорий (опционально)
        is_price: Добавлять ли цену на оверлей
        background_tasks: Background tasks for cleanup

    Returns:
        Файл коллажа в формате JPEG

    Raises:
        HTTPException: 400 - Ошибка получения данных из Directus
        HTTPException: 500 - Ошибка создания коллажа

    """
    log.info(
        "API запрос: генерация коллажа из Directus (продукты: %s, категории: %s)",
        product_ids,
        category_ids,
    )

    config = DirectusConfig(
        url=directus_url,
        token=directus_token,
        email=directus_email,
        password=directus_password,
    )

    client = DirectusClient(config)

    products = await client.get_products_with_images(
        product_ids=product_ids,
        category_ids=category_ids,
    )

    if not products:
        raise HTTPException(
            status_code=404,
            detail="Продукты не найдены в Directus",
        )

    from src.models.models import ImageData

    images = []
    for product in products:
        product_files = product.get("product_files", [])
        for pf in product_files:
            file_id = pf.get("directus_files_id")
            if file_id:
                file_id_value = (
                    file_id.get("id") if isinstance(file_id, dict) else file_id
                )
                category = product.get("category", {})
                categories = (
                    [category["name"]] if category and category.get("name") else []
                )

                images.append(
                    ImageData(
                        id=pf["id"],
                        url=f"{directus_url}/assets/{file_id_value}",
                        product_id=product["id"],
                        product_name=product.get("name", ""),
                        product_price=product.get("price", 0),
                        product_description=product.get("description", ""),
                        categories=categories,
                    )
                )

    if not images:
        raise HTTPException(
            status_code=404,
            detail="Изображения не найдены в Directus",
        )

    if len(images) > 16:
        images = images[:16]
        log.warning("Количество изображений ограничено до 16")

    collage_path = await CollageService.create_collage_from_data(
        images,
        is_price,
    )
    log.info("API ответ: коллаж создан по пути %s", collage_path)

    if background_tasks:
        background_tasks.add_task(_cleanup_file, collage_path)

    return FileResponse(
        collage_path,
        media_type="image/jpeg",
        filename="collage.jpg",
    )
