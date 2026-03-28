import logging
import shutil
import tempfile
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

log = logging.getLogger(__name__)


class CollageService:
    """Сервис для работы с коллажами."""

    @staticmethod
    async def create_collage_from_data(
        images: list[ImageData],
        filename: str = "collage.jpg",
        is_price: bool = True,
    ) -> str:
        """Создает коллаж из переданных данных об изображениях.

        Оптимизированный метод, который принимает все данные от фронтенда
        и не требует дополнительных запросов к Directus.

        Args:
            images: Список данных об изображениях
            filename: Имя файла коллажа
            is_price: Флаг, указывающий, нужно ли добавлять цену на оверлей

        Returns:
            Путь к созданному коллажу

        Raises:
            HTTPException: Если ошибка создания коллажа

        """
        log.info(f"Создание коллажа из {len(images)} изображений")

        if len(images) < 1 or len(images) > 16:
            error_msg = f"Количество изображений должно быть от 1 до 16, получено: {len(images)}"
            log.warning(error_msg)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg,
            )

        try:
            # Скачиваем изображения во временную папку
            temp_dir = tempfile.mkdtemp(prefix="collage_images_")
            image_models = []

            async with httpx.AsyncClient(timeout=30.0) as client:
                for idx, img_data in enumerate(images, start=1):
                    try:
                        # Скачиваем изображение
                        response = await client.get(img_data.url)
                        response.raise_for_status()

                        # Сохраняем во временный файл
                        temp_file = Path(temp_dir) / f"image_{idx}.jpg"
                        temp_file.write_bytes(response.content)

                        # Создаем продукт
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

                        # Создаем модель изображения
                        image_model = ImageWithProduct(
                            id=img_data.id,
                            product_id=img_data.product_id,
                            path=str(temp_file),
                            product=product,
                        )
                        image_models.append(image_model)

                        log.debug("Изображение %d скачано: %s", idx, img_data.url)

                    except httpx.HTTPError as e:
                        log.error("Ошибка скачивания изображения %s: %s", img_data.url, e)
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Ошибка скачивания изображения {img_data.url}: {e}",
                        ) from e

            # Создаем коллаж
            collage_path = CollageCreator().create(image_models, filename, is_price)
            log.info("Коллаж успешно создан: %s", collage_path)

            # Очищаем временные файлы
            try:
                shutil.rmtree(temp_dir)
                log.debug("Временная папка удалена: %s", temp_dir)
            except Exception as e:
                log.warning("Не удалось удалить временную папку %s: %s", temp_dir, e)

            return collage_path

        except HTTPException:
            raise
        except Exception as e:
            log.exception("Ошибка при создании коллажа: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при создании коллажа: {e}",
            ) from e

    @staticmethod
    async def create_collage_with_layout(
        images: list[ImageData],
        layout: CollageLayout,
        settings: CollageSettings,
        filename: str = "collage.jpg",
    ) -> str:
        """Создает коллаж с пользовательским макетом.

        Принимает данные об изображениях, макет холста и настройки отображения.
        Позволяет создавать коллажи с произвольным расположением ячеек,
        текстовыми надписями и настройками отображения.

        Args:
            images: Список данных об изображениях
            layout: Макет коллажа с ячейками
            settings: Настройки отображения
            filename: Имя файла коллажа

        Returns:
            Путь к созданному коллажу

        Raises:
            HTTPException: Если ошибка создания коллажа

        """
        log.info(f"Создание коллажа с макетом из {len(images)} изображений")

        if len(images) < 1 or len(images) > 16:
            error_msg = f"Количество изображений должно быть от 1 до 16, получено: {len(images)}"
            log.warning(error_msg)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg,
            )

        try:
            # Скачиваем изображения во временную папку
            temp_dir = tempfile.mkdtemp(prefix="collage_images_")
            image_models = []

            async with httpx.AsyncClient(timeout=30.0) as client:
                for idx, img_data in enumerate(images, start=1):
                    try:
                        # Скачиваем изображение
                        response = await client.get(img_data.url)
                        response.raise_for_status()

                        # Сохраняем во временный файл
                        temp_file = Path(temp_dir) / f"image_{idx}.jpg"
                        temp_file.write_bytes(response.content)

                        # Создаем продукт
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

                        # Создаем модель изображения
                        image_model = ImageWithProduct(
                            id=img_data.id,
                            product_id=img_data.product_id,
                            path=str(temp_file),
                            product=product,
                        )
                        image_models.append(image_model)

                        log.debug("Изображение %d скачано: %s", idx, img_data.url)

                    except httpx.HTTPError as e:
                        log.error("Ошибка скачивания изображения %s: %s", img_data.url, e)
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Ошибка скачивания изображения {img_data.url}: {e}",
                        ) from e

            # Создаем коллаж с макетом
            collage_path = CollageCreator().create_with_layout(
                image_models,
                layout,
                settings,
                filename,
            )
            log.info("Коллаж с макетом успешно создан: %s", collage_path)

            # Очищаем временные файлы
            try:
                shutil.rmtree(temp_dir)
                log.debug("Временная папка удалена: %s", temp_dir)
            except Exception as e:
                log.warning("Не удалось удалить временную папку %s: %s", temp_dir, e)

            return collage_path

        except HTTPException:
            raise
        except Exception as e:
            log.exception("Ошибка при создании коллажа с макетом: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при создании коллажа: {e}",
            ) from e
