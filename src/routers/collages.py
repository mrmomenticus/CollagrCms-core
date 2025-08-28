"""
API роутеры для работы с коллажами
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from src.core.collages import CollageService
# Кастомные исключения удалены — используем стандартные HTTPException

# Создаем роутер для коллажей
router = APIRouter(prefix="/collage", tags=["collages"])


@router.get("/")
async def create_collage(list_id: List[int] = Query(..., min_length=1, max_length=12)):  # noqa: B008
    """
    Создает коллаж из выбранных изображений

    Args:
        list_id: Список ID изображений (от 1 до 12)

    Returns:
        Файл коллажа в формате JPEG
    """
    logging.info(f"API запрос: создание коллажа из {len(list_id)} изображений")

    if len(list_id) < 1 or len(list_id) > 12:
        error_msg = (
            f"Количество изображений должно быть от 1 до 12, получено: {len(list_id)}"
        )
        logging.warning(f"API ошибка: {error_msg}")
        raise HTTPException(status_code=422, detail=error_msg)

    try:
        collage_path = await CollageService.create_collage_by_ids(
            list_id, "collage.jpg"
        )

        logging.info(f"API ответ: коллаж создан и возвращен")
        return FileResponse(
            collage_path, media_type="image/jpeg", filename="collage.jpg"
        )

    except HTTPException as e:
        logging.warning(f"API ошибка: {getattr(e, 'detail', str(e))}")
        raise e
    except Exception as e:
        logging.error(f"API ошибка при создании коллажа: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания коллажа")


@router.get("/select-all/")
async def get_all_product_for_collage():
    """
    Возвращает все доступные товары для создания коллажей

    Returns:
        JSON с информацией о всех товарах и возможностях создания коллажей
    """
    logging.info("API запрос: получение всех продуктов для коллажей")
    try:
        result = await CollageService.get_all_products_info()

        logging.info(f"API ответ: информация о {result.get('total_images', 0)} товарах")
        return result

    except Exception as e:
        logging.error(f"API ошибка при получении всех продуктов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения всех продуктов")


@router.get("/batch/")
async def create_batch_collage(
    batch_size: int = Query(default=12, ge=1, le=12),
    start_index: int = Query(default=0, ge=0),
):
    """
    Создает коллаж из текущего пакета товаров (по умолчанию 12 штук)
    Используется для кнопки "Дальше" - создает следующий коллаж и сразу отправляет его пользователю

    Args:
        batch_size: Размер пакета (по умолчанию 12)
        start_index: Начальный индекс для обработки

    Returns:
        Файл коллажа для скачивания
    """
    logging.info(
        f"API запрос: создание коллажа пакета (размер: {batch_size}, индекс: {start_index})"
    )
    try:
        collage_path, batch_info = await CollageService.create_batch_collage(
            batch_size, start_index
        )

        # Отправляем файл пользователю для скачивания
        response = FileResponse(
            collage_path,
            media_type="image/jpeg",
            filename=batch_info["filename"],
            headers={
                "X-Collage-Batch": str(batch_info["batch_number"]),
                "X-Collage-Total-Batches": str(batch_info["total_batches"]),
                "X-Collage-Processed-Images": str(batch_info["processed_images"]),
                "X-Collage-Total-Images": str(batch_info["total_images"]),
                "X-Collage-Start-Index": str(batch_info["start_index"]),
                "X-Collage-End-Index": str(batch_info["end_index"]),
                "X-Collage-Has-More": str(batch_info["has_more"]),
                "X-Collage-Next-Start-Index": str(batch_info["next_start_index"]),
                "X-Collage-Message": batch_info["message"],
            },
        )

        logging.info(f"API ответ: коллаж пакета создан {batch_info['filename']}")
        return response

    except HTTPException as e:
        logging.warning(f"API ошибка: {getattr(e, 'detail', str(e))}")
        raise e
    except Exception as e:
        logging.error(f"API ошибка при создании коллажа пакета: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания коллажа пакета")


@router.get("/batch/all/")
async def create_all_collage_info(
    batch_size: int = Query(default=12, ge=1, le=12),
):
    """
    Создает все коллажи из всех товаров, обрабатывая их пакетами
    Используется для кнопки "Выбрать все" - создает все коллажи сразу

    Args:
        batch_size: Размер пакета (по умолчанию 12)

    Returns:
        JSON с информацией о всех созданных коллажах
    """
    logging.info(f"API запрос: создание всех коллажей (размер пакета: {batch_size})")
    try:
        result = await CollageService.get_all_products_info()

        if not result["has_images"]:
            logging.warning("Товары не найдены для создания коллажей")
            raise HTTPException(status_code=404, detail="Товары не найдены")

        # Возвращаем информацию о том, что можно создать
        creation_info = {
            "total_batches": result["total_batches"],
            "total_images": result["total_images"],
            "batch_size": batch_size,
            "message": f"Можно создать {result['total_batches']} коллажей из {result['total_images']} товаров",
        }

        logging.info(
            f"API ответ: информация о создании {creation_info['total_batches']} коллажей"
        )
        return creation_info

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"API ошибка при получении информации о всех коллажах: {e}")
        raise HTTPException(
            status_code=500, detail="Ошибка получения информации о всех коллажах"
        )


@router.get("/batch/all/download/")
async def create_and_dowload_all_collages(
    batch_size: int = Query(default=12, ge=1, le=12),
):
    """
    Создает все коллажи из всех товаров и отправляет их пользователю в виде ZIP-архива
    Используется для кнопки "Выбрать все" - создает все коллажи и сразу отправляет для скачивания

    Args:
        batch_size: Размер пакета (по умолчанию 12)

    Returns:
        ZIP-архив со всеми созданными коллажами
    """
    logging.info(
        f"API запрос: создание и скачивание всех коллажей (размер пакета: {batch_size})"
    )
    try:
        zip_path, creation_info = await CollageService.create_all_collages_zip(
            batch_size
        )

        # Отправляем ZIP-файл пользователю
        response = FileResponse(
            zip_path,
            media_type="application/zip",
            filename=creation_info["zip_filename"],
            headers={
                "X-Collage-Total-Batches": str(creation_info["total_batches"]),
                "X-Collage-Total-Images": str(creation_info["total_images"]),
                "X-Collage-Batch-Size": str(creation_info["batch_size"]),
                "X-Collage-Message": creation_info["message"],
            },
        )

        logging.info(
            f"API ответ: ZIP-архив с коллажами создан {creation_info['zip_filename']}"
        )
        return response

    except HTTPException as e:
        logging.warning(f"API ошибка: {getattr(e, 'detail', str(e))}")
        raise e
    except Exception as e:
        logging.error(f"API ошибка при создании и скачивании всех коллажей: {e}")
        raise HTTPException(
            status_code=500, detail="Ошибка создания и скачивания всех коллажей"
        )


@router.get("/batch/status/")
async def get_batch_processing_status():
    """
    Возвращает статус пакетной обработки коллажей

    Returns:
        JSON с информацией о статусе
    """
    logging.info("API запрос: получение статуса пакетной обработки")
    try:
        result = await CollageService.get_batch_processing_status()

        logging.info(
            f"API ответ: статус получен ({result.get('total_images', 0)} товаров)"
        )
        return result

    except Exception as e:
        logging.error(f"API ошибка при получении статуса: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статуса")


@router.get("/batch/info/")
async def get_batch_info(
    start_index: int = Query(default=0, ge=0),
    batch_size: int = Query(default=12, ge=1, le=12),
):
    """
    Возвращает информацию о текущем пакете товаров без создания коллажа
    Используется для получения информации перед созданием коллажа

    Args:
        start_index: Начальный индекс для обработки
        batch_size: Размер пакета (по умолчанию 12)

    Returns:
        JSON с информацией о текущем пакете
    """
    logging.info(
        f"API запрос: получение информации о пакете (индекс: {start_index}, размер: {batch_size})"
    )
    try:
        result = await CollageService.get_batch_info(start_index, batch_size)

        logging.info(
            f"API ответ: информация о пакете {result['current_batch']}/{result['total_batches']}"
        )
        return result

    except HTTPException as e:
        logging.warning(f"API ошибка: {getattr(e, 'detail', str(e))}")
        raise e
    except Exception as e:
        logging.error(f"API ошибка при получении информации о пакете: {e}")
        raise HTTPException(
            status_code=500, detail="Ошибка получения информации о пакете"
        )


@router.post("/cleanup/")
async def cleanup_temp_files():
    """
    Очищает временные файлы коллажей

    Returns:
        JSON с результатом очистки
    """
    logging.info("API запрос: очистка временных файлов")
    try:
        result = CollageService.cleanup_temp_files()

        logging.info(f"API ответ: очищено {result['total_cleaned']} элементов")
        return result

    except Exception as e:
        logging.error(f"API ошибка при очистке временных файлов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка очистки временных файлов")
