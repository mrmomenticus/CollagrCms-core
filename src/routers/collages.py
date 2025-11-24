import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from src.core.collages import CollageService
from src.models.models import CollageInfoResponse

router = APIRouter(prefix="/v1/collage", tags=["collages"])
log = logging.getLogger(__name__)


@router.post("/")
async def create_collage(
    list_id: list[int] = Query(..., min_length=1, max_length=16),  # noqa: B008
    is_price: bool = True,
) -> FileResponse:
    """Создает коллаж из выбранных изображений.

    Args:
        list_id: Список ID изображений (от 1 до 16)
        is_price: Флаг, указывающий, нужно ли добавлять цену на оверлей

    Returns:
        Файл коллажа в формате JPEG

    Raises:
        HTTPException: 422 - Неверное количество изображений
        HTTPException: 500 - Ошибка создания коллажа

    """
    if not (1 <= len(list_id) <= 16):
        error_msg = (
            f"Количество изображений должно быть от 1 до 16, получено: {len(list_id)}"
        )
        log.warning(error_msg)
        raise HTTPException(status_code=422, detail=error_msg)

    try:
        collage_path = await CollageService.create_collage_by_ids(
            list_id,
            "collage.jpg",
            is_price,
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


@router.get("/", response_model=CollageInfoResponse)
async def get_all_product_for_collage() -> CollageInfoResponse:
    """Возвращает все доступные товары для создания коллажей.

    Returns:
        JSON с информацией о всех товарах и возможностях создания коллажей

    Raises:
        HTTPException: 500 - Ошибка получения продуктов
        HTTPException: 404 - Продукты не найдены

    """
    log.info("API запрос: получение всех продуктов для коллажа")
    try:
        result = await CollageService.get_all_products_info()
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Товары не найдены",
            )
        log.info("API ответ: получена информация о %d продуктах", result.total_images)
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.exception("API ошибка при получении всех продуктов: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Ошибка получения всех продуктов",
        ) from e


@router.get("/categories/", response_model=CollageInfoResponse)
async def get_products_by_categories(category_names: list[str]) -> CollageInfoResponse:
    """Возвращает товары по заданным категориям для создания коллажей.

    Args:
        category_names: Список названий категорий для фильтрации

    Returns:
        JSON с информацией о товарах и возможностях создания коллажей

    Raises:
        HTTPException: 500 - Ошибка получения продуктов по категориям

    """
    log.info("API запрос: получение продуктов по категориям %s", category_names)
    try:
        result = await CollageService.get_products_by_categories(category_names)
        log.info(
            "API ответ: получена информация о %d продуктах по категориям",
            result.total_images,
        )
        return result
    except Exception as e:
        log.exception("API ошибка при получении продуктов по категориям: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Ошибка получения продуктов по категориям",
        ) from e


@router.get("/batch/")
async def create_batch_collage(
    batch_size: int = Query(default=16, ge=1, le=16),
    start_index: int = Query(default=0, ge=0),
    is_price: bool = True,
    category_names: list[str] | None = None,
):
    """Создает коллаж из текущего пакета товаров (по умолчанию 16 штук)
    Используется для кнопки "Дальше" - создает следующий коллаж и сразу отправляет его пользователю.
    Args:
        batch_size: Размер пакета (по умолчанию 16)
        start_index: Начальный индекс для обработки
        is_price: Флаг, указывающий, нужно ли добавлять цену на оверлей
        category_names: Список названий категорий для фильтрации.
    Returns:
        Файл коллажа для скачивания
    Raises:
        HTTPException: 500 - Ошибка создания коллажа пакета.
    """  # noqa: D205
    log.info(
        "API запрос: создание коллажа пакета (размер: %d, индекс: %d, категория: %s)",
        batch_size,
        start_index,
        category_names if category_names else "all",
    )
    try:
        collage_path, batch_info = await CollageService.create_batch_collage(
            batch_size,
            start_index,
            is_price,
            category_names,
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
                # Добавляем информацию о категориях в заголовки, если они указаны
                "X-Collage-Categories": str(category_names)
                if category_names
                else "all",
                # Убираем кириллицу из заголовков
                "X-Collage-Message": f"Batch {batch_info['batch_number']} of {batch_info['total_batches']} (images {batch_info['start_index'] + 1}-{batch_info['end_index']} of {batch_info['total_images']})",
            },
        )

        log.info("API ответ: коллаж пакета создан %s", batch_info["filename"])
        return response

    except HTTPException as e:
        log.warning("API ошибка: %s", getattr(e, "detail", str(e)))
        raise e
    except Exception as e:
        log.exception("API ошибка при создании коллажа пакета: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Ошибка создания коллажа пакета",
        ) from e


@router.get("/batch/all/")
async def create_all_collage_info(
    batch_size: int = Query(default=16, ge=1, le=16),
    category_names: list[str] | None = None,
):
    """Создает все коллажи из всех товаров, обрабатывая их пакетами
    Используется для кнопки "Выбрать все" - создает все коллажи сразу. Если есть category_names, то создает коллажи только по ним.

    Args:
        batch_size: Размер пакета (по умолчанию 16)
        category_names: Список названий категорий для фильтрации

    Returns:
        JSON с информацией о всех созданных коллажах

    Raises:
        HTTPException: 404 - Товары не найдены
        HTTPException: 500 - Ошибка получения информации о всех коллажах

    """
    log.info(
        "API запрос: получение информации о создании всех коллажей (размер пакета: %d, категории: %s)",
        batch_size,
        category_names if category_names else "all",
    )

    try:
        if category_names:
            result = await CollageService.get_products_by_categories(category_names)
        else:
            result = await CollageService.get_all_products_info()

        if not result or not result.has_images:
            log.warning("Товары не найдены для создания коллажей")
            raise HTTPException(status_code=404, detail="Товары не найдены")

        # Возвращаем информацию о том, что можно создать
        creation_info = {
            "total_batches": result.total_batches,
            "total_images": result.total_images,
            "batch_size": batch_size,
            "categories": result.categories,
            "message": f"Можно создать {result.total_batches} коллажей из {result.total_images} товаров в категориях {result.categories}",
        }

        log.info(
            "API ответ: информация о создании %d коллажей",
            creation_info["total_batches"],
        )
        return creation_info

    except HTTPException:
        raise
    except Exception as e:
        log.exception("API ошибка при получении информации о всех коллажах: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Ошибка получения информации о всех коллажах",
        ) from e


@router.get("/batch/all/download/")
async def create_and_dowload_all_collages(
    batch_size: int = Query(default=16, ge=1, le=16),
    is_price: bool = True,
    category_names: list[str] = Query(
        None,
        description="Список названий категорий для фильтрации",
    ),
):
    """Создает все коллажи из всех товаров и отправляет их пользователю в виде ZIP-архива
    Используется для кнопки "Выбрать все" - создает все коллажи и сразу отправляет для скачивания

    Args:
        batch_size: Размер пакета (по умолчанию 16)
        is_price: Флаг, указывающий, нужно ли добавлять цену на оверлей
        category_names: Список названий категорий для фильтрации

    Returns:
        ZIP-архив со всеми созданными коллажами

    Raises:
        HTTPException: 500 - Ошибка создания и скачивания всех коллажей

    """
    log.info(
        "API запрос: создание и скачивание всех коллажей (размер пакета: %d, категории: %s)",
        batch_size,
        category_names if category_names else "all",
    )
    try:
        zip_path, creation_info = await CollageService.create_all_collages_zip(
            batch_size,
            is_price,
            category_names,
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
                "X-Collage-Categories": str(category_names)
                if category_names
                else "all",
                # Убираем кириллицу из заголовков, чтобы избежать проблем с кодировкой
                "X-Collage-Message": f"Created {creation_info['total_batches']} collages from {creation_info['total_images']} images in categories {creation_info['categories']}",
            },
        )

        log.info(
            "API ответ: ZIP-архив с коллажами создан %s",
            creation_info["zip_filename"],
        )
        return response

    except HTTPException as e:
        log.warning("API ошибка: %s", getattr(e, "detail", str(e)))
        raise e
    except Exception as e:
        log.exception("API ошибка при создании и скачивании всех коллажей: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Ошибка создания и скачивания всех коллажей",
        ) from e


@router.get("/batch/status/", response_model=CollageInfoResponse)
async def get_batch_processing_status(
    category_names: list[str] = Query(
        None,
        description="Список названий категорий для фильтрации",
    ),
) -> CollageInfoResponse:
    """Возвращает статус пакетной обработки коллажей

    Args:
        category_names: Список названий категорий для фильтрации

    Returns:
        JSON с информацией о статусе

    Raises:
        HTTPException: 500 - Ошибка получения статуса

    """
    log.info(
        "API запрос: получение статуса пакетной обработки (категории: %s)",
        category_names if category_names else "all",
    )
    try:
        result = await CollageService.get_batch_processing_status(category_names)
        log.info("API ответ: статус получен (%d товаров)", result.total_images)
        return result
    except Exception as e:
        log.exception("API ошибка при получении статуса пакетной обработки: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Ошибка получения статуса пакетной обработки",
        ) from e


@router.get("/batch/info/")
async def get_batch_info(
    start_index: int = Query(default=0, ge=0),
    batch_size: int = Query(default=16, ge=1, le=16),
    category_names: list[str] = Query(
        None,
        description="Список названий категорий для фильтрации",
    ),
):
    """Возвращает информацию о текущем пакете товаров без создания коллажа
    Используется для получения информации перед созданием коллажа

    Args:
        start_index: Начальный индекс для обработки
        batch_size: Размер пакета (по умолчанию 16)
        category_names: Список названий категорий для фильтрации

    Returns:
        JSON с информацией о текущем пакете

    Raises:
        HTTPException: 500 - Ошибка получения информации о пакете

    """
    log.info(
        "API запрос: получение информации о пакете (индекс: %d, размер: %d, категории: %s)",
        start_index,
        batch_size,
        category_names if category_names else "all",
    )
    try:
        result = await CollageService.get_batch_info(
            start_index,
            batch_size,
            category_names,
        )

        log.info(
            "API ответ: информация о пакете %d/%d",
            result["current_batch"],
            result["total_batches"],
        )
        return result

    except HTTPException as e:
        log.warning("API ошибка: %s", getattr(e, "detail", str(e)))
        raise e
    except Exception as e:
        log.exception("API ошибка при получении информации о пакете: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Ошибка получения информации о пакете",
        ) from e


@router.post("/cleanup/")
async def cleanup_temp_files():
    """Очищает временные файлы коллажей

    Returns:
        JSON с результатом очистки

    Raises:
        HTTPException: 500 - Ошибка очистки временных файлов

    """
    log.info("API запрос: очистка временных файлов")
    try:
        result = CollageService.cleanup_temp_files()

        log.info("API ответ: очищено %d элементов", result["total_cleaned"])
        return result

    except Exception as e:
        log.exception("API ошибка при очистке временных файлов: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Ошибка очистки временных файлов",
        ) from e
