import logging
import shutil
import tempfile
import uuid
from pathlib import Path

import httpx
from fastapi import HTTPException, status

from src.core.collage_creator import CollageCreator
from src.models.models import (
    Category,
    CollageLayout,
    CollageSettings,
    ImageData,
    ImageWithProduct,
    Product,
)
from src.utils.config import config

log = logging.getLogger(__name__)

#TODO: пофиксить 
def _transform_directus_url(url: str) -> str:
    """Трансформирует URL Directus: /directus-assets → /assets, /directus-api удаляется."""
    if url.startswith("/directus-assets"):
        return url.replace("/directus-assets", "/assets", 1)
    if url.startswith("/directus-api"):
        return url.replace("/directus-api", "", 1)
    return url


async def _download_images(
    images: list[ImageData],
    directus_token: str | None = None,
) -> tuple[list[ImageWithProduct | None], Path]:
    """Скачивает изображения во временную папку и возвращает модели изображений."""
    temp_dir = Path(tempfile.mkdtemp(prefix="collage_images_"))
    image_models: list[ImageWithProduct | None] = []

    headers = {}
    if directus_token:
        headers["Authorization"] = f"Bearer {directus_token}"
        log.info("Токен Directus получен, будет использован для запросов")
    else:
        log.warning("Токен Directus НЕ получен! directus_token=%s", directus_token)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for idx, img_data in enumerate(images, start=1):
                # Пропускаем пустые слоты (плейсхолдеры)
                if img_data.id == -1 or not img_data.url:
                    image_models.append(None)
                    continue

                transformed_url = _transform_directus_url(img_data.url)
                if transformed_url.startswith(("http://", "https://")):
                    image_url = transformed_url
                else:
                    image_url = f"{config.get_directus_url().rstrip('/')}{transformed_url}"
                log.info(
                    "Запрос к Directus: URL=%s, headers=%s, image_id=%s, product_id=%s",
                    image_url,
                    {"Authorization": "Bearer <token>"}
                    if headers.get("Authorization")
                    else {},
                    img_data.id,
                    img_data.product_id,
                )
                try:
                    response = await client.get(image_url, headers=headers)
                    response.raise_for_status()

                    temp_file = temp_dir / f"image_{idx}.jpg"
                    temp_file.write_bytes(response.content)

                    log.info(
                        "Успешно скачано изображение: URL=%s, size=%d bytes, image_id=%s",
                        image_url,
                        len(response.content),
                        img_data.id,
                    )

                    categories = [
                        Category(id=i, name=cat_name, description=None)
                        for i, cat_name in enumerate(img_data.categories, start=1)
                    ]
                    product = Product(
                        id=img_data.product_id,
                        name=img_data.product_name,
                        description=img_data.product_description,
                        price=img_data.product_price,
                        categories=categories,
                    )
                    image_models.append(
                        ImageWithProduct(
                            id=img_data.id,
                            product_id=img_data.product_id,
                            path=str(temp_file),
                            product=product,
                        )
                    )
                    log.debug("Изображение %d скачано: %s", idx, img_data.url)

                except httpx.HTTPError as e:
                    if isinstance(e, httpx.HTTPStatusError):
                        log.error(
                            "Ошибка скачивания изображения: URL=%s, headers_sent=%s, status_code=%s, error=%s",
                            image_url,
                            {"Authorization": "Bearer <token>"}
                            if headers.get("Authorization")
                            else {},
                            e.response.status_code,
                            e,
                        )
                    else:
                        log.error(
                            "Ошибка скачивания изображения: URL=%s, headers_sent=%s, error=%s",
                            image_url,
                            {"Authorization": "Bearer <token>"}
                            if headers.get("Authorization")
                            else {},
                            e,
                        )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Ошибка скачивания изображения {image_url}: {e}",
                    ) from e
    except HTTPException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise

    return image_models, temp_dir


class CollageService:
    """Сервис для работы с коллажами."""

    @staticmethod
    async def create_collage_from_data(
        images: list[ImageData],
        is_price: bool = True,
        directus_token: str | None = None,
    ) -> str:
        """Создает коллаж из переданных данных об изображениях."""
        log.info("Создание коллажа из %d изображений", len(images))

        if not images:
            log.warning("Список изображений пуст")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Список изображений не может быть пустым",
            )

        collage_path = (
            config.get_collage_output_dir() / f"collage_{uuid.uuid4().hex}.jpg"
        )

        try:
            image_models, temp_dir = await _download_images(images, directus_token)

            try:
                valid_image_models = [img for img in image_models if img is not None]
                CollageCreator().create(valid_image_models, str(collage_path), is_price)
                log.info("Коллаж успешно создан: %s", collage_path)
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
                log.debug("Временная папка удалена: %s", temp_dir)

            return str(collage_path)

        except HTTPException:
            raise
        except Exception:
            log.exception("Ошибка при создании коллажа")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при создании коллажа",
            ) from None

    @staticmethod
    async def create_collage_with_layout(
        images: list[ImageData],
        layout: CollageLayout,
        settings: CollageSettings,
        directus_token: str | None = None,
    ) -> str:
        """Создает коллаж с пользовательским макетом."""
        log.info("Создание коллажа с макетом из %d изображений", len(images))

        if not images:
            log.warning("Список изображений пуст")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Список изображений не может быть пустым",
            )

        collage_path = (
            config.get_collage_output_dir() / f"collage_{uuid.uuid4().hex}.jpg"
        )

        try:
            image_models, temp_dir = await _download_images(images, directus_token)

            try:
                CollageCreator().create_with_layout(
                    image_models,
                    layout,
                    settings,
                    str(collage_path),
                )
                log.info("Коллаж с макетом успешно создан: %s", collage_path)
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
                log.debug("Временная папка удалена: %s", temp_dir)

            return str(collage_path)

        except HTTPException:
            raise
        except Exception:
            log.exception("Ошибка при создании коллажа с макетом")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при создании коллажа",
            ) from None

    @staticmethod
    async def create_batch_collages_with_layout(
        images: list[ImageData],
        layout: CollageLayout,
        settings: CollageSettings,
        directus_token: str | None = None,
    ) -> list[str]:
        """Создает несколько коллажей с пользовательским макетом."""
        image_cells_count = sum(cell.type == "image" for cell in layout.cells)

        if image_cells_count == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="В макете нет ячеек для изображений",
            )

        log.info(
            "Пакетная генерация: %d изображений, %d ячеек на коллаж",
            len(images),
            image_cells_count,
        )

        collage_paths: list[str] = []
        total_collages = (len(images) + image_cells_count - 1) // image_cells_count

        for collage_idx in range(total_collages):
            start_idx = collage_idx * image_cells_count
            end_idx = min(start_idx + image_cells_count, len(images))
            batch_images = images[start_idx:end_idx]

            log.info(
                "Генерация коллажа %d/%d: изображения %d-%d",
                collage_idx + 1,
                total_collages,
                start_idx + 1,
                end_idx,
            )

            collage_path = await CollageService.create_collage_with_layout(
                batch_images,
                layout,
                settings,
                directus_token,
            )
            collage_paths.append(collage_path)

        log.info("Пакетная генерация завершена: %d коллажей", len(collage_paths))
        return collage_paths
