import logging
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.background import BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse

from src.core.collages import CollageService
from src.core.directus_client import DirectusClient
from src.models.models import (
    CollageRequest,
    CollageWithLayoutRequest,
    DirectusConfig,
    ImageData,
)
from src.utils.config import config

router = APIRouter(prefix="/v1/collage", tags=["collages"])
log = logging.getLogger(__name__)


def _cleanup_file(path: str) -> None:
    """Удаляет файл если он существует."""
    try:
        Path(path).unlink(missing_ok=True)
        log.debug("Файл коллажа удален: %s", path)
    except Exception as e:
        log.warning("Не удалось удалить файл коллажа %s: %s", path, e)


@router.post("/generate")
async def generate_collage_from_data(
    request: CollageRequest,
    background_tasks: BackgroundTasks,
) -> FileResponse:
    """Генерирует коллаж из переданных данных об изображениях."""
    log.info("API запрос: генерация коллажа из %d изображений", len(request.images))

    collage_path = await CollageService.create_collage_from_data(
        request.images,
        request.is_price,
        request.directus_token,
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
    """Генерирует коллаж с пользовательским макетом."""
    log.info(
        "API запрос: генерация коллажа с макетом (%d изображений, %d ячеек)",
        len(request.images),
        len(request.layout.cells),
    )

    collage_path = await CollageService.create_collage_with_layout(
        request.images,
        request.layout,
        request.settings,
        request.directus_token,
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
) -> FileResponse:
    """Генерирует коллаж, получая данные напрямую из Directus."""
    log.info(
        "API запрос: генерация коллажа из Directus (продукты: %s, категории: %s)",
        product_ids,
        category_ids,
    )

    directus_config = DirectusConfig(
        url=directus_url,
        token=directus_token,
        email=directus_email,
        password=directus_password,
    )

    client = DirectusClient(directus_config)

    products = await client.get_products_with_images(
        product_ids=product_ids,
        category_ids=category_ids,
    )

    if not products:
        raise HTTPException(
            status_code=404,
            detail="Продукты не найдены в Directus",
        )

    images: list[ImageData] = []
    for product in products:
        product_files = product.get("product_files", [])
        for pf in product_files:
            file_id = pf.get("directus_files_id")
            if not file_id:
                continue

            file_id_value = file_id.get("id") if isinstance(file_id, dict) else file_id
            category = product.get("category", {})
            categories = [category["name"]] if category and category.get("name") else []

            images.append(
                ImageData(
                    id=pf["id"],
                    url=f"{config.get_directus_url()}/directus-assets/{file_id_value}",
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
        images, is_price, directus_token
    )
    log.info("API ответ: коллаж создан по пути %s", collage_path)

    return FileResponse(
        collage_path,
        media_type="image/jpeg",
        filename="collage.jpg",
    )


@router.post("/generate/batch", response_model=None)
async def generate_batch_collages(
    requests: list[CollageWithLayoutRequest],
    background_tasks: BackgroundTasks,
) -> FileResponse | StreamingResponse:
    """Генерирует несколько коллажей и возвращает архив."""
    log.info("API запрос: пакетная генерация %d коллажей", len(requests))

    if not requests:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Список запросов пуст",
        )

    collage_paths: list[tuple[str, str]] = []

    try:
        for idx, req in enumerate(requests, start=1):
            log.info(
                "Генерация коллажа %d/%d (%d изображений, %d ячеек)",
                idx,
                len(requests),
                len(req.images),
                len(req.layout.cells),
            )

            collage_path = await CollageService.create_collage_with_layout(
                req.images,
                req.layout,
                req.settings,
                req.directus_token,
            )
            collage_paths.append((f"collage_{idx}.jpg", collage_path))
            log.info("Коллаж %d создан: %s", idx, collage_path)

        if len(collage_paths) == 1:
            single_path = collage_paths[0][1]
            background_tasks.add_task(_cleanup_file, single_path)
            return FileResponse(
                single_path,
                media_type="image/jpeg",
                filename="collage.jpg",
            )

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for filename, filepath in collage_paths:
                zip_file.write(filepath, filename)
                background_tasks.add_task(_cleanup_file, filepath)

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=collages.zip"},
        )

    except HTTPException:
        for _, path in collage_paths:
            _cleanup_file(path)
        raise


@router.post("/generate/batch-auto", response_model=None)
async def generate_batch_auto(
    request: CollageWithLayoutRequest,
    background_tasks: BackgroundTasks,
) -> FileResponse | StreamingResponse:
    """Генерирует несколько коллажей автоматически."""
    log.info(
        "API запрос: автопакетная генерация (%d изображений)",
        len(request.images),
    )

    if not request.images:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Список изображений пуст",
        )

    collage_paths = await CollageService.create_batch_collages_with_layout(
        request.images,
        request.layout,
        request.settings,
        request.directus_token,
    )

    collage_paths_with_names = [
        (f"collage_{idx + 1}.jpg", path) for idx, path in enumerate(collage_paths)
    ]

    for _, path in collage_paths_with_names:
        background_tasks.add_task(_cleanup_file, path)

    if len(collage_paths) == 1:
        return FileResponse(
            collage_paths[0],
            media_type="image/jpeg",
            filename="collage.jpg",
        )

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for filename, filepath in collage_paths_with_names:
            zip_file.write(filepath, filename)

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=collages.zip"},
    )
