"""
API роутеры для работы с изображениями
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from src.core.images import ImageService
# Кастомные исключения удалены — используем стандартные HTTPException

# Создаем роутер для изображений
router = APIRouter(prefix="/media", tags=["images"])


@router.get("/{image_id}")
async def get_image(image_id: int):
    """
    Возвращает файл изображения по ID

    Args:
        image_id: ID изображения

    Returns:
        Файл изображения
    """
    logging.info(f"API запрос: получение файла изображения ID {image_id}")
    try:
        image = await ImageService.get_image_by_id(image_id)

        logging.info(f"API ответ: возвращен файл изображения {image.path}")
        return FileResponse(image.path, media_type="image/jpeg")

    except HTTPException as e:
        logging.warning(f"API ошибка: {getattr(e, 'detail', str(e))}")
        raise e
    except Exception as e:
        logging.error(f"API ошибка при получении изображения {image_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения изображения") from e


@router.put("/{image_id}")
async def update_image(image_id: int, image: UploadFile = File(...)):  # noqa: B008
    """
    Обновляет изображение

    Args:
        image_id: ID изображения
        image: Новый файл изображения

    Returns:
        Сообщение об успешном обновлении
    """
    logging.info(f"API запрос: обновление изображения ID {image_id}")
    try:
        # Получаем существующее изображение для определения категории
        existing_images = await ImageService.get_images_by_ids(
            list_id_images=[image_id]
        )
        if not existing_images:
            logging.warning(f"Изображение с ID {image_id} не найдено")
            raise HTTPException(status_code=404, detail=f"Изображение с ID {image_id} не найдено")

        existing_image = existing_images[0]
        category_name = (
            existing_image.product.category.name
            if existing_image.product.category
            else "default"
        )

        # Обновляем изображение
        await ImageService.update_image(image_id, image, category_name)

        logging.info("API ответ: изображение обновлено")
        return {"message": "Изображение обновлено"}

    except HTTPException as e:
        logging.warning(f"API ошибка: {getattr(e, 'detail', str(e))}")
        raise e
    except Exception as e:
        logging.error(f"API ошибка при обновлении изображения {image_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления изображения") from e 
