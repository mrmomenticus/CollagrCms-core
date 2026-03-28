"""API роутеры для работы с изображениями
"""

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from src.core.images import ImageService

# Создаем роутер для изображений
router = APIRouter(prefix="/media", tags=["images"])


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

        log.info("API ответ: возвращен файл изображения %s", image["path"])
        return FileResponse(image["path"], media_type="image/jpeg")

    except HTTPException as e:
        log.warning("API ошибка: %s", getattr(e, "detail", str(e)))
        raise e
    except Exception as e:
        log.exception("API ошибка при получении изображения %s: %s", image_id, e)
        raise HTTPException(
            status_code=500, detail="Ошибка получения изображения",
        ) from e
