"""
Бизнес-логика для работы с изображениями
"""

import logging
from typing import List
from fastapi import UploadFile, Request, HTTPException, status

from src.database.repository.images import ImagesRepository
from src.database.schema.images import ImagesDb
from src.models.models import ImageWithProduct
# Заменены кастомные исключения на стандартные HTTPException


class ImageService:
    """Сервис для работы с изображениями"""

    @staticmethod
    async def create_image(
        product_id: int, image_file: UploadFile, category_name: str
    ) -> ImagesDb:
        """
        Создает новое изображение для продукта

        Args:
            product_id: ID продукта
            image_file: Загружаемый файл изображения
            category_name: Название категории для создания пути

        Returns:
            Созданное изображение

        Raises:
            InvalidFileError: Если файл неверный
        """
        logging.info(f"Создание изображения для продукта ID {product_id}")

        try:
            if not image_file.filename:
                logging.warning("Неверное имя файла")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Неверное имя файла",
                )

            # Обрабатываем загрузку файла
            path = await handle_file_upload(image_file, category_name)

            # Создаем запись в БД
            image_db = await ImagesRepository.add(product_id, path)
            logging.info(f"Изображение успешно создано: {path} (ID: {image_db.id})")
            return image_db

        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"Ошибка при создании изображения для продукта {product_id}: {e}"
            )
            raise

    @staticmethod
    async def get_all_images() -> List[ImagesDb]:
        """
        Получает все изображения

        Returns:
            Список всех изображений
        """
        logging.info("Получение всех изображений")

        try:
            images_db = await ImagesRepository.get_all()
            logging.info(f"Получено изображений: {len(images_db)}")
            return images_db
        except Exception as e:
            logging.error(f"Ошибка при получении изображений: {e}")
            raise

    @staticmethod
    async def get_all_images_with_products() -> List[ImagesDb]:
        """
        Получает все изображения с информацией о продуктах

        Returns:
            Список изображений с продуктами
        """
        logging.info("Получение всех изображений с продуктами")

        try:
            images_db = await ImagesRepository.get_all_with_products()
            logging.info(f"Получено изображений с продуктами: {len(images_db)}")
            return images_db
        except Exception as e:
            logging.error(f"Ошибка при получении изображений с продуктами: {e}")
            raise

    @staticmethod
    async def get_image_by_id(image_id: int) -> ImagesDb:
        """
        Получает изображение по ID

        Args:
            image_id: ID изображения

        Returns:
            Изображение

        Raises:
            ImageNotFoundError: Если изображение не найдено
        """
        logging.info(f"Получение изображения по ID: {image_id}")

        try:
            image_db = await ImagesRepository.get_by_id(image_id)
            if not image_db:
                logging.warning(f"Изображение с ID {image_id} не найдено")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Изображение с ID {image_id} не найдено",
                )

            logging.info(f"Изображение найдено: {image_db.path}")
            return image_db
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Ошибка при получении изображения {image_id}: {e}")
            raise

    @staticmethod
    async def get_images_by_ids(
        list_id_images: List[int] | None = None,
        list_id_products: List[int] | None = None,
    ) -> List[ImagesDb]:
        """
        Получает изображения по списку ID изображений или продуктов

        Args:
            list_id_images: Список ID изображений
            list_id_products: Список ID продуктов

        Returns:
            Список изображений

        Raises:
            ImageNotFoundError: Если изображения не найдены
        """
        if list_id_images:
            logging.info(f"Получение изображений по ID: {list_id_images}")
        elif list_id_products:
            logging.info(f"Получение изображений по ID продуктов: {list_id_products}")
        else:
            logging.warning("Не переданы ID для поиска изображений")
            return []

        try:
            images_db = await ImagesRepository.get_by_ids_with_products(
                list_id_images=list_id_images, list_id_products=list_id_products
            )

            if not images_db:
                if list_id_images:
                    logging.warning(f"Изображения с ID {list_id_images} не найдены")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Изображения с ID {list_id_images} не найдены",
                    )
                elif list_id_products:
                    logging.warning(
                        f"Изображения для продуктов {list_id_products} не найдены"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Изображения для продуктов {list_id_products} не найдены",
                    )
                return []

            logging.info(f"Найдено изображений: {len(images_db)}")
            return images_db
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Ошибка при получении изображений: {e}")
            raise

    @staticmethod
    async def update_image(
        image_id: int, new_image_file: UploadFile, category_name: str
    ) -> None:
        """
        Обновляет изображение

        Args:
            image_id: ID изображения
            new_image_file: Новый файл изображения
            category_name: Название категории для создания пути

        Raises:
            ImageNotFoundError: Если изображение не найдено
            InvalidFileError: Если файл неверный
        """
        logging.info(f"Обновление изображения ID {image_id}")

        try:
            # Проверяем существование изображения
            existing_images = await ImagesRepository.get_by_ids_with_products(
                list_id_images=[image_id]
            )
            if not existing_images:
                logging.warning(f"Изображение с ID {image_id} не найдено")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Изображение с ID {image_id} не найдено",
                )

            existing_image = existing_images[0]

            # Обрабатываем новый файл
            new_path = await handle_file_upload(new_image_file, category_name)

            # Обновляем запись в БД
            await ImagesRepository.update(image_id, new_path)

            # Удаляем старый файл
            from src.utils.file import delete_file

            await delete_file(existing_image.path)

            logging.info(f"Изображение успешно обновлено: {new_path}")

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Ошибка при обновлении изображения {image_id}: {e}")
            raise

    @staticmethod
    def format_products_with_images(
        images_db: List[ImagesDb], request: Request, include_categories: bool = False
    ) -> List[dict]:
        """
        Форматирует изображения с продуктами для API ответа

        Args:
            images_db: Список изображений из БД
            request: HTTP запрос для получения base_url
            include_categories: Включать ли информацию о категориях

        Returns:
            Список отформатированных продуктов с изображениями
        """
        logging.info(f"Форматирование {len(images_db)} продуктов с изображениями")

        base_url = str(request.base_url).rstrip("/")
        result = []

        for img in images_db:
            if include_categories:
                product_data = {
                    "id": img.product.id,
                    "name": img.product.name,
                    "description": img.product.description,
                    "price": img.product.price,
                    "category_id": img.product.category_id,
                    "category_name": img.product.category.name
                    if img.product.category
                    else None,
                    "image_id": img.id,
                    "image_path": f"{base_url}/media/{img.id}",
                }
            else:
                model = ImageWithProduct.model_validate(img)
                model.path = f"{base_url}/media/{img.id}"
                product_data = model.model_dump()

            result.append(product_data)

        logging.info(f"Отформатировано продуктов: {len(result)}")
        return result

    @staticmethod
    def format_products_info(images_db: List[ImagesDb]) -> List[dict]:
        """
        Форматирует информацию о продуктах для коллажей

        Args:
            images_db: Список изображений из БД

        Returns:
            Список информации о продуктах
        """
        logging.info(f"Форматирование информации о {len(images_db)} продуктах")

        products_info = []
        for img in images_db:
            products_info.append({
                "id": img.id,
                "product_id": img.product_id,
                "name": img.product.name,
                "description": img.product.description,
                "category_id": img.product.category_id,
                "category_name": img.product.category.name
                if img.product.category
                else None,
                "price": img.product.price,
                "path": img.path,
            })

        logging.info(f"Отформатирована информация о {len(products_info)} продуктах")
        return products_info


# Вспомогательная функция для обработки загрузки файлов
async def handle_file_upload(image: UploadFile, tag: str) -> str:
    """
    Обрабатывает загрузку файла изображения

    Args:
        image: Загружаемый файл
        tag: Тег для создания пути

    Returns:
        Путь к сохраненному файлу

    Raises:
        InvalidFileError: Если файл неверный
    """
    from src.utils.file import create_uuid, create_path, created_file

    if not image.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверное имя файла",
        )

    uuid = await create_uuid(image.filename)
    path = await create_path(uuid, tag)
    await created_file(image, path, tag)
    return path
