import glob
import logging
import os
import pathlib
import shutil
import tempfile
import uuid
import zipfile

from fastapi import HTTPException, status

from src.core.collage_creator import CollageCreator
from src.core.images import ImageService
from src.models.models import ImageWithProduct

log = logging.getLogger(__name__)


class CollageService:
    """Сервис для работы с коллажами."""

    @staticmethod
    async def create_collage_by_ids(
        list_id: list[int], filename: str = "collage.jpg", is_price: bool = True,
    ) -> str:
        """Создает коллаж из выбранных изображений по их ID.

        Args:
            list_id: Список ID изображений (от 1 до 16)
            filename: Имя файла коллажа
            is_price: Флаг, указывающий, нужно ли добавлять цену на оверлей

        Returns:
            Путь к созданному коллажу

        Raises:
            CollageCreationError: Если ошибка создания коллажа
            ImageNotFoundError: Если изображения не найдены

        """
        log.info(f"Создание коллажа из {len(list_id)} изображений")

        if len(list_id) < 1 or len(list_id) > 12:
            error_msg = f"Количество изображений должно быть от 1 до 12, получено: {len(list_id)}"
            log.warning(error_msg)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg,
            )

        try:
            # Получаем изображения с продуктами
            images_db = await ImageService.get_images_by_ids(list_id_images=list_id)

            # Проверяем, что все изображения найдены
            if len(images_db) != len(list_id):
                found_ids = [img.id for img in images_db]
                missing_ids = [img_id for img_id in list_id if img_id not in found_ids]
                error_msg = f"Изображения с ID {missing_ids} не найдены"
                log.warning(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_msg,
                )

            # Создаем модели для коллажа
            image_models = [ImageWithProduct.model_validate(img) for img in images_db]

            # Создаем коллаж
            collage_path = CollageCreator().create(image_models, filename, is_price)
            log.info("Коллаж успешно создан: %s", collage_path)
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
    async def get_all_products_info() -> dict | None:
        """Возвращает информацию о всех доступных товарах для создания коллажей.

        Returns:
            Словарь с информацией о товарах и возможностях создания коллажей

        """
        log.info("Получение информации о всех продуктах для коллажей")

        try:
            # Получаем все изображения с товарами
            all_images_db = await ImageService.get_all_images_with_products()

            if not all_images_db:
                log.info("Products not found")
                return {
                    "total_images": 0,
                    "total_batches": 0,
                    "batch_size": 12,
                    "has_images": False,
                    "message": "Products not found",
                }

            total_images = len(all_images_db)
            batch_size = 12
            total_batches = (total_images + batch_size - 1) // batch_size

            # Формируем информацию о товарах
            products_info = ImageService.format_products_info(all_images_db)

            result = {
                "total_images": total_images,
                "total_batches": total_batches,
                "batch_size": batch_size,
                "has_images": True,
                "products": products_info,
                "message": f"Found {total_images} products. Can create {total_batches} collages with {batch_size} products each.",
            }

            log.info("Информация о продуктах получена: %s товаров", total_images)
            return result

        except Exception as e:
            log.exception("Ошибка при получении информации о продуктах: %s", e)
            raise

    @staticmethod
    async def get_products_by_categories(
        category_names: list[str]
    ) -> dict | None:
        """Возвращает информацию о товарах по заданным категориям для создания коллажей.

        Args:
            category_names: Список названий категорий для фильтрации

        Returns:
            Словарь с информацией о товарах и возможностях создания коллажей

        """
        log.debug(
            "Получение информации о продуктах для категорий: %s", category_names,
        ) 

        try:
            # Получаем все изображения с товарами
            all_images_db = await ImageService.get_all_images_with_products()

            if not all_images_db:
                return None
            filtered_images_db = all_images_db
            if category_names:
                filtered_images_db = [
                    img
                    for img in all_images_db
                    if any(cat.name in category_names for cat in img.product.categories)
                ]

            if not filtered_images_db:
                log.info("Products not found for categories: %s", category_names)
                return {
                    "total_images": 0,
                    "total_batches": 0,
                    "batch_size": 12,
                    "has_images": False,
                    "categories": category_names,
                    "message": f"Products not found for categories: {category_names}",
                }

            total_images = len(filtered_images_db)
            batch_size = 12
            total_batches = (total_images + batch_size - 1) // batch_size

            # Формируем информацию о товарах
            products_info = ImageService.format_products_info(filtered_images_db)

            result = {
                "total_images": total_images,
                "total_batches": total_batches,
                "batch_size": batch_size,
                "has_images": True,
                "categories": category_names,
                "products": products_info,
                "message": f"Found {total_images} products in categories {category_names}. Can create {total_batches} collages with {batch_size} products each.",
            }

            log.info(
                "Информация о продуктах для категорий получена: %s товаров", total_images,
            )
            return result

        except Exception as e:
            log.exception(
                "Ошибка при получении информации о продуктах по категориям: %s", e,
            )
            raise

    @staticmethod
    async def create_batch_collage(
        batch_size: int = 12,
        start_index: int = 0,
        is_price: bool = True,
        category_names: list[str] | None = None,
    ) -> tuple[str, dict]:
        """Создает коллаж из текущего пакета товаров

        Args:
            batch_size: Размер пакета (по умолчанию 12)
            start_index: Начальный индекс для обработки
            is_price: Флаг, указывающий, нужно ли добавлять цену на оверлей
            category_names: Список названий категорий для фильтрации товаров

        Returns:
            Кортеж (путь_к_коллажу, информация_о_пакете)

        Raises:
            CollageCreationError: Если ошибка создания коллажа
            ImageNotFoundError: Если товары не найдены

        """
        if category_names:
            log.info(
                "Создание коллажа пакета по категориям: %s, размер %s, начальный индекс %s", category_names, batch_size, start_index,
            )
        else:
            log.info(
                "Создание коллажа пакета: размер %s, начальный индекс %s", batch_size, start_index,
            )

        try:
            # Получаем изображения с товарами, возможно, отфильтрованные по категориям
            all_images_db = await ImageService.get_all_images_with_products()

            if not all_images_db:
                log.warning("Products not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Products not found",
                )

            # Фильтруем по категориям, если указаны
            if category_names:
                all_images_db = [
                    img
                    for img in all_images_db
                    if any(cat.name in category_names for cat in img.product.categories)
                ]

            if not all_images_db:
                log.warning("Products not found for categories: %s", category_names)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Products not found for categories: {category_names}",
                )

            total_images = len(all_images_db)
            total_batches = (total_images + batch_size - 1) // batch_size

            # Проверяем, не выходит ли start_index за пределы
            if start_index >= total_images:
                error_msg = f"Начальный индекс {start_index} превышает общее количество товаров ({total_images})"
                log.warning(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg,
                )

            # Обрабатываем текущий пакет
            end_index = min(start_index + batch_size, total_images)
            current_batch = all_images_db[start_index:end_index]

            # Создаем коллаж для текущего пакета
            image_models = [
                ImageWithProduct.model_validate(img) for img in current_batch
            ]

            # Генерируем уникальное имя файла
            batch_number = start_index // batch_size + 1
            collage_filename = (
                f"collage_batch_{batch_number}_{uuid.uuid4().hex[:8]}.jpg"
            )

            # Создаем временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                collage_path = CollageCreator().create(
                    image_models, tmp_file.name, is_price,
                )

            # Информация о пакете
            batch_info = {
                "batch_number": batch_number,
                "total_batches": total_batches,
                "processed_images": len(current_batch),
                "total_images": total_images,
                "start_index": start_index,
                "end_index": end_index,
                "has_more": end_index < total_images,
                "next_start_index": end_index if end_index < total_images else -1,
                "filename": collage_filename,
                "categories": category_names,
                "message": f"Collage {batch_number} of {total_batches} (products {start_index + 1}-{end_index} of {total_images})",
            }

            log.info("Коллаж пакета создан: %s", collage_filename)
            return collage_path, batch_info

        except HTTPException:
            raise
        except Exception as e:
            log.exception("Ошибка при создании коллажа пакета: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при создании коллажа пакета: {e}",
            ) from e

    @staticmethod
    async def create_all_collages_zip(
        batch_size: int = 12,
        is_price: bool = True,
        category_names: list[str] | None = None,
    ) -> tuple[str, dict]:
        """Создает все коллажи из всех товаров и упаковывает в ZIP-архив

        Args:
            batch_size: Размер пакета (по умолчанию 12)
            is_price: Флаг, указывающий, нужно ли добавлять цену на оверлей
            category_names: Список названий категорий для фильтрации товаров

        Returns:
            Кортеж (путь_к_zip_файлу, информация_о_создании)

        Raises:
            CollageCreationError: Если ошибка создания коллажей
            ImageNotFoundError: Если товары не найдены

        """
        if category_names:
            log.info(
                "Создание всех коллажей в ZIP-архиве по категориям: %s с размером пакета %s", category_names, batch_size,
            )
        else:
            log.info(
                "Создание всех коллажей в ZIP-архиве с размером пакета %s", batch_size,
            )

        try:
            # Получаем все изображения с товарами
            all_images_db = await ImageService.get_all_images_with_products()

            if not all_images_db:
                log.warning("Products not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Products not found",
                )

            # Фильтруем по категориям, если указаны
            if category_names:
                all_images_db = [
                    img
                    for img in all_images_db
                    if any(cat.name in category_names for cat in img.product.categories)
                ]

            if not all_images_db:
                log.warning("Products not found for categories: %s", category_names)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Products not found for categories: {category_names}",
                )

            # Создаем временную папку для коллажей
            temp_collages_dir = tempfile.mkdtemp(prefix="collages_")

            total_images = len(all_images_db)
            total_batches = (total_images + batch_size - 1) // batch_size

            # Создаем временный ZIP-файл
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
                zip_path = tmp_zip.name

                with zipfile.ZipFile(zip_path, "w") as zip_file:
                    for batch_num in range(total_batches):
                        start_index = batch_num * batch_size
                        end_index = min(start_index + batch_size, total_images)
                        current_batch = all_images_db[start_index:end_index]

                        # Создаем коллаж для текущего пакета
                        image_models = [
                            ImageWithProduct.model_validate(img)
                            for img in current_batch
                        ]

                        # Генерируем уникальное имя файла
                        collage_filename = (
                            f"collage_batch_{batch_num + 1}_{uuid.uuid4().hex[:8]}.jpg"
                        )
                        collage_path = os.path.join(temp_collages_dir, collage_filename)

                        CollageCreator().create(image_models, collage_path, is_price)

                        # Добавляем файл в ZIP-архив
                        zip_file.write(collage_path, collage_filename)

                        log.info(
                            f"Создан коллаж {batch_num + 1}/{total_batches}: {collage_filename}",
                        )

            # Удаляем временную папку с коллажами
            try:
                if pathlib.Path(temp_collages_dir).exists():
                    shutil.rmtree(temp_collages_dir)
            except Exception as e:
                log.warning(
                    "Не удалось удалить временную папку %s: %s", temp_collages_dir, e,
                )

            # Информация о создании
            creation_info = {
                "total_batches": total_batches,
                "total_images": total_images,
                "batch_size": batch_size,
                "categories": category_names,
                "zip_filename": f"all_collages_{uuid.uuid4().hex[:8]}.zip",
                "message": f"Created {total_batches} collages from {total_images} products in categories {category_names}",
            }

            log.info(
                f"Все коллажи созданы и упакованы в ZIP: {creation_info['zip_filename']}",
            )
            return zip_path, creation_info

        except HTTPException:
            raise
        except Exception as e:
            log.exception("Ошибка при создании всех коллажей: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при создании всех коллажей: {e}",
            ) from e

    @staticmethod
    async def get_batch_info(
        start_index: int = 0,
        batch_size: int = 12,
        category_names: list[str] | None = None,
    ) -> dict:
        """Возвращает информацию о текущем пакете товаров без создания коллажа

        Args:
            start_index: Начальный индекс для обработки
            batch_size: Размер пакета (по умолчанию 12)
            category_names: Список названий категорий для фильтрации товаров

        Returns:
            Информация о текущем пакете

        Raises:
            CollageCreationError: Если индекс выходит за пределы
            ImageNotFoundError: Если товары не найдены

        """
        if category_names:
            log.info(
                "Получение информации о пакете по категориям: %s, индекс %s, размер %s", category_names, start_index, batch_size,
            )
        else:
            log.info(
                "Получение информации о пакете: индекс %s, размер %s", start_index, batch_size,
            )

        try:
            # Получаем все изображения с товарами
            all_images_db = await ImageService.get_all_images_with_products()

            if not all_images_db:
                log.warning("Products not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Products not found",
                )

            # Фильтруем по категориям, если указаны
            if category_names:
                all_images_db = [
                    img
                    for img in all_images_db
                    if any(cat.name in category_names for cat in img.product.categories)
                ]

            if not all_images_db:
                log.warning("Products not found for categories: %s", category_names)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Products not found for categories: {category_names}",
                )

            total_images = len(all_images_db)
            total_batches = (total_images + batch_size - 1) // batch_size

            # Проверяем, не выходит ли start_index за пределы
            if start_index >= total_images:
                error_msg = f"Начальный индекс {start_index} превышает общее количество товаров ({total_images})"
                log.warning(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg,
                )

            # Обрабатываем текущий пакет
            end_index = min(start_index + batch_size, total_images)
            current_batch = all_images_db[start_index:end_index]

            # Формируем информацию о товарах в текущем пакете
            batch_products = ImageService.format_products_info(current_batch)

            # Проверяем, есть ли ещё пакеты для обработки
            has_more = end_index < total_images
            next_start_index = end_index if has_more else None
            batch_number = start_index // batch_size + 1

            result = {
                "current_batch": batch_number,
                "total_batches": total_batches,
                "processed_images": len(current_batch),
                "total_images": total_images,
                "start_index": start_index,
                "end_index": end_index,
                "has_more": has_more,
                "next_start_index": next_start_index,
                "batch_products": batch_products,
                "categories": category_names,
                "message": f"Batch {batch_number} of {total_batches} (products {start_index + 1}-{end_index} of {total_images})",
            }

            log.info(
                "Информация о пакете получена: пакет %s/%s", batch_number, total_batches,
            )
            return result

        except HTTPException:
            raise
        except Exception as e:
            log.exception("Ошибка при получении информации о пакете: %s", e)
            raise

    @staticmethod
    async def get_batch_processing_status(
        category_names: list[str] | None = None,
    ) -> dict:
        """Возвращает статус пакетной обработки коллажей

        Args:
            category_names: Список названий категорий для фильтрации товаров

        Returns:
            Информация о статусе

        """
        if category_names:
            log.info(
                "Получение статуса пакетной обработки для категорий: %s", category_names,
            )
        else:
            log.info("Получение статуса пакетной обработки")

        try:
            # Получаем все изображения с товарами
            all_images_db = await ImageService.get_all_images_with_products()

            if not all_images_db:
                log.info("Products not found")
                return {
                    "total_images": 0,
                    "total_batches": 0,
                    "batch_size": 12,
                    "has_images": False,
                    "categories": category_names,
                    "message": "Products not found",
                }

            # Фильтруем по категориям, если указаны
            if category_names:
                all_images_db = [
                    img
                    for img in all_images_db
                    if any(cat.name in category_names for cat in img.product.categories)
                ]

            if not all_images_db:
                log.info("Products not found for categories: %s", category_names)
                return {
                    "total_images": 0,
                    "total_batches": 0,
                    "batch_size": 12,
                    "has_images": False,
                    "categories": category_names,
                    "message": f"Products not found for categories: {category_names}",
                }

            total_images = len(all_images_db)
            batch_size = 12
            total_batches = (total_images + batch_size - 1) // batch_size

            result = {
                "total_images": total_images,
                "total_batches": total_batches,
                "batch_size": batch_size,
                "has_images": True,
                "categories": category_names,
                "message": f"Found {total_images} products in categories {category_names}. Can create {total_batches} collages with {batch_size} products each.",
            }

            log.info(
                "Статус получен: %s товаров, %s пакетов", total_images, total_batches,
            )
            return result

        except Exception as e:
            log.exception("Ошибка при получении статуса: %s", e)
            raise

    @staticmethod
    def cleanup_temp_files() -> dict:
        """Очищает временные файлы коллажей

        Returns:
            Результат очистки

        """
        log.info("Очистка временных файлов коллажей")

        try:
            # Очищаем временные файлы в /tmp
            temp_patterns = ["/tmp/collages_*", "/tmp/tmp*", "/tmp/*.jpg", "/tmp/*.zip"]

            cleaned_files = []
            cleaned_dirs = []

            for pattern in temp_patterns:
                try:
                    # Удаляем файлы
                    for file_path in glob.glob(pattern):
                        if pathlib.Path(file_path).is_file():
                            pathlib.Path(file_path).unlink()
                            cleaned_files.append(file_path)

                    # Удаляем папки
                    for dir_path in glob.glob(pattern):
                        if pathlib.Path(dir_path).is_dir():
                            shutil.rmtree(dir_path)
                            cleaned_dirs.append(dir_path)
                except Exception as e:
                    log.warning("Не удалось очистить шаблон %s: %s", pattern, e)

            result = {
                "cleaned_files": cleaned_files,
                "cleaned_directories": cleaned_dirs,
                "total_cleaned": len(cleaned_files) + len(cleaned_dirs),
                "message": f"Очищено {len(cleaned_files)} файлов и {len(cleaned_dirs)} папок",
            }

            log.info(f"Очистка завершена: {result['total_cleaned']} элементов")
            return result

        except Exception as e:
            log.exception("Ошибка при очистке временных файлов: %s", e)
            raise
