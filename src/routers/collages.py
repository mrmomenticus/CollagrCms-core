import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
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


@router.post("/generate")
async def generate_collage_from_data(request: CollageRequest) -> FileResponse:
    """Генерирует коллаж из переданных данных об изображениях.

    Оптимизированный endpoint, который принимает все данные от фронтенда
    и не требует дополнительных запросов к Directus.

    Args:
        request: Запрос с данными об изображениях и параметрах коллажа

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
    
    collage_path = None

    try:
        collage_path = await CollageService.create_collage_from_data(
            request.images,
            request.is_price,
        )
        log.info("API ответ: коллаж создан по пути %s", collage_path)
        return FileResponse(
            collage_path,
            media_type="image/jpeg",
            filename="collage.jpg",
        )
    except Exception as e:
        log.exception("API ошибка при создании коллажа: %s", e)
        raise HTTPException(status_code=500, detail="Ошибка создания коллажа") from e
    finally:
        # Cleanup the collage file after serving
        if collage_path and os.path.exists(collage_path):
            try:
                os.remove(collage_path)
                log.debug("Файл коллажа удален: %s", collage_path)
            except Exception as e:
                log.warning("Не удалось удалить файл коллажа %s: %s", collage_path, e)


@router.post("/generate/with-layout")
async def generate_collage_with_layout(request: CollageWithLayoutRequest) -> FileResponse:
    """Генерирует коллаж с пользовательским макетом.

    Принимает данные об изображениях, макет холста и настройки отображения.
    Позволяет создавать коллажи с произвольным расположением ячеек,
    текстовыми надписями и настройками отображения.

    Args:
        request: Запрос с данными об изображениях, макете и настройках

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
    
    collage_path = None

    try:
        collage_path = await CollageService.create_collage_with_layout(
            request.images,
            request.layout,
            request.settings,
        )
        log.info("API ответ: коллаж с макетом создан по пути %s", collage_path)
        return FileResponse(
            collage_path,
            media_type="image/jpeg",
            filename="collage.jpg",
        )
    except Exception as e:
        log.exception("API ошибка при создании коллажа с макетом: %s", e)
        raise HTTPException(status_code=500, detail="Ошибка создания коллажа") from e
    finally:
        # Cleanup the collage file after serving
        if collage_path and os.path.exists(collage_path):
            try:
                os.remove(collage_path)
                log.debug("Файл коллажа удален: %s", collage_path)
            except Exception as e:
                log.warning("Не удалось удалить файл коллажа %s: %s", collage_path, e)


@router.post("/generate/from-directus")
async def generate_collage_from_directus(
    directus_url: str = Query(..., description="URL Directus API"),
    directus_token: str | None = Query(None, description="Токен авторизации"),
    directus_email: str | None = Query(None, description="Email для авторизации"),
    directus_password: str | None = Query(None, description="Пароль для авторизации"),
    product_ids: list[int] | None = Query(None, description="Список ID продуктов"),
    category_ids: list[int] | None = Query(None, description="Список ID категорий"),
    is_price: bool = Query(True, description="Добавлять ли цену на оверлей"),
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
    
    collage_path = None

    try:
        # Создаем конфигурацию Directus
        config = DirectusConfig(
            url=directus_url,
            token=directus_token,
            email=directus_email,
            password=directus_password,
        )

        # Создаем клиент Directus
        client = DirectusClient(config)

        # Получаем продукты с изображениями
        products = await client.get_products_with_images(
            product_ids=product_ids,
            category_ids=category_ids,
        )

        if not products:
            raise HTTPException(
                status_code=404,
                detail="Продукты не найдены в Directus",
            )

        # Преобразуем данные в формат для генерации коллажа
        from src.models.models import ImageData
        images = []
        for product in products:
            product_files = product.get("product_files", [])
            for pf in product_files:
                file_id = pf.get("directus_files_id")
                if file_id:
                    # Handle both direct file ID and nested object
                    file_id_value = file_id.get("id") if isinstance(file_id, dict) else file_id
                    # Получаем категорию
                    category = product.get("category", {})
                    categories = [category["name"]] if category and category.get("name") else []

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

        # Ограничиваем количество изображений до 16
        if len(images) > 16:
            images = images[:16]
            log.warning("Количество изображений ограничено до 16")

        # Генерируем коллаж
        collage_path = await CollageService.create_collage_from_data(
            images,
            is_price,
        )
        log.info("API ответ: коллаж создан по пути %s", collage_path)
        return FileResponse(
            collage_path,
            media_type="image/jpeg",
            filename="collage.jpg",
        )

    except HTTPException:
        raise
    except Exception as e:
        log.exception("API ошибка при создании коллажа из Directus: %s", e)
        raise HTTPException(status_code=500, detail="Ошибка создания коллажа") from e
    finally:
        # Cleanup the collage file after serving
        if collage_path and os.path.exists(collage_path):
            try:
                os.remove(collage_path)
                log.debug("Файл коллажа удален: %s", collage_path)
            except Exception as e:
                log.warning("Не удалось удалить файл коллажа %s: %s", collage_path, e)
