"""API роутеры для работы с изображениями
"""

import logging
from typing import cast

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from src.core.images import ImageService

# Создаем роутер для изображений
router = APIRouter(prefix="/v1/media", tags=["images"])


@router.get("/{image_id}")
async def get_image(image_id: int):
    """Возвращает файл изображения по ID

    Args:
        image_id: ID изображения

    Returns:
        Файл изображения

    Raises:
        HTTPException: 500 - Ошибка получения изображения

    """
    log = logging.getLogger(__name__)
    log.info("API запрос: получение файла изображения ID %s", image_id)
    try:
        image = await ImageService.get_image_by_id(image_id)

        log.info("API ответ: возвращен файл изображения %s", image.path)
        return FileResponse(image.path, media_type="image/jpeg")

    except HTTPException as e:
        log.warning("API ошибка: %s", getattr(e, "detail", str(e)))
        raise e
    except Exception as e:
        log.exception("API ошибка при получении изображения %s: %s", image_id, e)
        raise HTTPException(
            status_code=500, detail="Ошибка получения изображения",
        ) from e


@router.put("/{image_id}")
async def update_image(image_id: int, image: UploadFile = File(...)):  # noqa: B008
    """Обновляет изображение

    Args:
        image_id: ID изображения
        image: Новый файл изображения

    Returns:
        Сообщение об успешном обновлении

    Raises:
        HTTPException: 404 - Изображение не найдено
        HTTPException: 500 - Ошибка обновления изображения

    """
    log = logging.getLogger(__name__)
    log.info("API запрос: обновление изображения ID %s", image_id)
    try:
        # Получаем существующее изображение для определения категории
        existing_images = await ImageService.get_images_by_ids(
            list_id_images=[image_id],
        )
        if not existing_images:
            log.warning("Изображение с ID %s не найдено", image_id)
            raise HTTPException(
                status_code=404, detail=f"Изображение с ID {image_id} не найдено",
            )

        existing_image = existing_images[0]
        category_name = (
            existing_image.product.categories[0].name
            if existing_image.product.categories
            else "default"
        )

        # Обновляем изображение
        await ImageService.update_image(image_id, image, category_name)

        log.info("API ответ: изображение обновлено")
        return {"message": "Изображение обновлено"}

    except HTTPException as e:
        log.warning("API ошибка: %s", getattr(e, "detail", str(e)))
        raise e
    except Exception as e:
        log.exception("API ошибка при обновлении изображения %s: %s", image_id, e)
        raise HTTPException(
            status_code=500, detail="Ошибка обновления изображения",
        ) from e
