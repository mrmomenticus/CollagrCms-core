import logging
import os

from fastapi import HTTPException, Request, UploadFile, status

from src.models.models import ImageWithProduct, Product
from src.utils.file import create_path, create_uuid, created_file, delete_file

log = logging.getLogger(__name__)


class ImageService:
    # Путь к папке с изображениями
    IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "images")

    @staticmethod
    async def create_image(
        product_id: int,
        image_file: UploadFile,
        category_name: str,
    ) -> dict:
        """Создает новое изображение для продукта.

        Args:
            product_id: ID продукта
            image_file: Загружаемый файл изображения
            category_name: Название категории для создания пути

        Returns:
            Информация о созданном изображении

        """
        log.debug("Создание изображения для продукта ID %s", product_id)
        if not image_file.filename:
            log.warning("Неверное имя файла")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверное имя файла",
            )
        # Обрабатываем загрузку файла
        path = await handle_file_upload(image_file, category_name)
        log.debug(f"Изображение успешно создано: {path}")
        return {"id": product_id, "path": path}

    @staticmethod
    async def get_all_images() -> list[dict]:
        """Получает все изображения.

        Returns:
            Список всех изображений

        """
        log.info("Получение всех изображений")

        if not os.path.exists(ImageService.IMAGES_DIR):
            log.warning("Папка с изображениями не найдена: %s", ImageService.IMAGES_DIR)
            return []

        image_extensions = ('.jpg', '.jpeg', '.png', '.webp')
        images = []

        for idx, filename in enumerate(os.listdir(ImageService.IMAGES_DIR), start=1):
            if filename.lower().endswith(image_extensions):
                image_path = os.path.join(ImageService.IMAGES_DIR, filename)
                images.append({
                    "id": idx,
                    "path": image_path,
                    "filename": filename,
                })

        log.info(f"Получено изображений: {len(images)}")
        return images

    @staticmethod
    async def get_all_images_with_products() -> list[ImageWithProduct]:
        """Получает все изображения с информацией о продуктах.

        Returns:
            Список изображений с продуктами

        """
        try:
            images = await ImageService.get_all_images()

            if not images:
                log.warning("Изображений не найдено")
                return []

            image_models = []
            for img in images:
                # Извлекаем имя файла без расширения как название продукта
                filename = img["filename"]
                product_name = os.path.splitext(filename)[0]

                # Создаем продукт с базовой информацией
                product = Product(
                    id=img["id"],
                    name=product_name,
                    description=f"Изображение {filename}",
                    price=0,
                    categories=[],
                )

                image_model = ImageWithProduct(
                    id=img["id"],
                    product_id=img["id"],
                    path=img["path"],
                    product=product,
                )
                image_models.append(image_model)

            log.debug(f"Получено изображений с продуктами: {len(image_models)}")
            return image_models
        except Exception as e:
            log.exception(f"Ошибка при получении изображений с продуктами: {e}")
            raise e

    @staticmethod
    async def get_image_by_id(image_id: int) -> dict:
        """Получает изображение по ID.

        Args:
            image_id: ID изображения

        Returns:
            Изображение

        Raises:
            HTTPException: Если изображение не найдено

        """
        log.info("Получение изображения по ID: %s", image_id)

        try:
            images = await ImageService.get_all_images()

            if not images:
                log.warning("Изображения не найдены")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Изображения не найдены",
                )

            # Ищем изображение по ID
            for img in images:
                if img["id"] == image_id:
                    log.info(f"Изображение найдено: {img['path']}")
                    return img

            log.warning("Изображение с ID %s не найдено", image_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Изображение с ID {image_id} не найдено",
            )
        except HTTPException:
            raise
        except Exception as e:
            log.exception("Ошибка при получении изображения %s: %s", image_id, e)
            raise

    @staticmethod
    async def get_images_by_ids(
        list_id_images: list[int] | None = None,
        list_id_products: list[int] | None = None,
    ) -> list[ImageWithProduct]:
        """Получает изображения по списку ID изображений или продуктов.

        Args:
            list_id_images: Список ID изображений
            list_id_products: Список ID продуктов

        Returns:
            Список изображений

        Raises:
            HTTPException: Если изображения не найдены

        """
        if list_id_images:
            log.info("Получение изображений по ID: %s", list_id_images)
        elif list_id_products:
            log.info("Получение изображений по ID продуктов: %s", list_id_products)
        else:
            log.warning("Не переданы ID для поиска изображений")
            return []

        try:
            all_images = await ImageService.get_all_images_with_products()

            if not all_images:
                if list_id_images:
                    log.warning("Изображения с ID %s не найдены", list_id_images)
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Изображения с ID {list_id_images} не найдены",
                    )
                if list_id_products:
                    log.warning(
                        "Изображения для продуктов %s не найдены",
                        list_id_products,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Изображения для продуктов {list_id_products} не найдены",
                    )
                return []

            # Фильтруем по ID
            if list_id_images:
                filtered_images = [img for img in all_images if img.id in list_id_images]
            else:
                filtered_images = [img for img in all_images if img.product_id in list_id_products]

            if not filtered_images:
                if list_id_images:
                    log.warning("Изображения с ID %s не найдены", list_id_images)
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Изображения с ID {list_id_images} не найдены",
                    )
                if list_id_products:
                    log.warning(
                        "Изображения для продуктов %s не найдены",
                        list_id_products,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Изображения для продуктов {list_id_products} не найдены",
                    )
                return []

            log.info(f"Найдено изображений: {len(filtered_images)}")
            return filtered_images
        except HTTPException:
            raise
        except Exception as e:
            log.exception("Ошибка при получении изображений: %s", e)
            raise

    @staticmethod
    async def update_image(
        image_id: int,
        new_image_file: UploadFile,
        category_name: str,
    ) -> None:
        """Обновляет изображение.

        Args:
            image_id: ID изображения
            new_image_file: Новый файл изображения
            category_name: Название категории для создания пути

        Raises:
            HTTPException: Если изображение не найдено

        """
        log.info("Обновление изображения ID %s", image_id)

        try:
            # Получаем существующее изображение
            existing_image = await ImageService.get_image_by_id(image_id)

            # Обрабатываем новый файл
            new_path = await handle_file_upload(new_image_file, category_name)

            # Удаляем старый файл
            await delete_file(existing_image["path"])

            log.info("Изображение успешно обновлено: %s", new_path)

        except HTTPException:
            raise
        except Exception as e:
            log.exception("Ошибка при обновлении изображения %s: %s", image_id, e)
            raise

    @staticmethod
    def format_products_with_images(
        images_db: list[ImageWithProduct],
        request: Request,
        include_categories: bool = False,
    ) -> list[dict]:
        """Форматирует изображения с продуктами для API ответа.

        Args:
            images_db: Список изображений
            request: HTTP запрос для получения base_url
            include_categories: Включать ли информацию о категориях

        Returns:
            Список отформатированных продуктов с изображениями

        """
        log.info(f"Форматирование {len(images_db)} продуктов с изображениями")

        base_url = str(request.base_url).rstrip("/")
        result = []

        for img in images_db:
            product_data = {
                "id": img.id,
                "product_id": img.product_id,
                "name": img.product.name,
                "description": img.product.description,
                "price": img.product.price,
                "categories": [
                    {"id": cat.id, "name": cat.name} for cat in img.product.categories
                ],
                "image_id": img.id,
                "image_path": f"{base_url}/media/{img.id}",
            }
            result.append(product_data)

        log.info(f"Отформатировано продуктов: {len(result)}")
        return result

    @staticmethod
    def format_products_info(images_db: list[ImageWithProduct]) -> list[dict]:
        """Форматирует информацию о продуктах для коллажей.

        Args:
            images_db: Список изображений

        Returns:
            Список информации о продуктах

        """
        log.info(f"Форматирование информации о {len(images_db)} продуктах")

        products_info = []
        for img in images_db:
            products_info.append({
                "id": img.id,
                "product_id": img.product_id,
                "name": img.product.name,
                "description": img.product.description,
                "categories": [
                    {"id": cat.id, "name": cat.name} for cat in img.product.categories
                ],
                "price": img.product.price,
                "path": img.path,
            })

        log.info(f"Отформатирована информация о {len(products_info)} продуктах")
        return products_info


# Вспомогательная функция для обработки загрузки файлов
async def handle_file_upload(image: UploadFile, tag: str) -> str:
    """Обрабатывает загрузку файла изображения.

    Args:
        image: Загружаемый файл
        tag: Тег для создания пути

    Returns:
        Путь к сохраненному файлу

    Raises:
        HTTPException: Если файл неверный

    """
    if not image.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверное имя файла",
        )

    uuid = await create_uuid(image.filename)
    path = await create_path(uuid, tag)
    await created_file(image, path, tag)
    return path
