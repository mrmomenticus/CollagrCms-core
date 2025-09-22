"""
Бизнес-логика для работы с коллажами
"""

import glob
import logging
import os
import shutil
import tempfile
import uuid
import zipfile
from typing import List

from fastapi import HTTPException, status

from src.core.collage_creator import CollageCreator
from src.core.images import ImageService

from src.models.models import ImageWithProduct


class CollageService:
    """Сервис для работы с коллажами"""

    @staticmethod
    async def create_collage_by_ids(
        list_id: List[int], filename: str = "collage.jpg", is_price: bool = True
    ) -> str:
        """
        Создает коллаж из выбранных изображений по их ID

        Args:
            list_id: Список ID изображений (от 1 до 12)
            filename: Имя файла коллажа
            is_price: Флаг, указывающий, нужно ли добавлять цену на оверлей

        Returns:
            Путь к созданному коллажу

        Raises:
            CollageCreationError: Если ошибка создания коллажа
            ImageNotFoundError: Если изображения не найдены
        """
        logging.info(f"Создание коллажа из {len(list_id)} изображений")

        if len(list_id) < 1 or len(list_id) > 12:
            error_msg = f"Количество изображений должно быть от 1 до 12, получено: {len(list_id)}"
            logging.warning(error_msg)
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
                logging.warning(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_msg,
                )

            # Создаем модели для коллажа
            image_models = [ImageWithProduct.model_validate(img) for img in images_db]

            # Создаем коллаж
            collage_path = CollageCreator().create(image_models, filename, is_price)
            logging.info(f"Коллаж успешно создан: {collage_path}")
            return collage_path

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Ошибка при создании коллажа: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при создании коллажа: {e}",
            ) from e

    @staticmethod
    async def get_all_products_info() -> dict:
        """
        Возвращает информацию о всех доступных товарах для создания коллажей

        Returns:
            Словарь с информацией о товарах и возможностях создания коллажей
        """
        logging.info("Получение информации о всех продуктах для коллажей")

        try:
            # Получаем все изображения с товарами
            all_images_db = await ImageService.get_all_images_with_products()

            if not all_images_db:
                logging.info("Products not found")
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

            logging.info(f"Информация о продуктах получена: {total_images} товаров")
            return result

        except Exception as e:
            logging.error(f"Ошибка при получении информации о продуктах: {e}")
            raise

    @staticmethod
    async def create_batch_collage(
        batch_size: int = 12, start_index: int = 0, is_price: bool = True
    ) -> tuple[str, dict]:
        """
        Создает коллаж из текущего пакета товаров

        Args:
            batch_size: Размер пакета (по умолчанию 12)
            start_index: Начальный индекс для обработки
            is_price: Флаг, указывающий, нужно ли добавлять цену на оверлей

        Returns:
            Кортеж (путь_к_коллажу, информация_о_пакете)

        Raises:
            CollageCreationError: Если ошибка создания коллажа
            ImageNotFoundError: Если товары не найдены
        """
        logging.info(
            f"Создание коллажа пакета: размер {batch_size}, начальный индекс {start_index}"
        )

        try:
            # Получаем все изображения с товарами
            all_images_db = await ImageService.get_all_images_with_products()

            if not all_images_db:
                logging.warning("Products not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Products not found",
                )

            total_images = len(all_images_db)
            total_batches = (total_images + batch_size - 1) // batch_size

            # Проверяем, не выходит ли start_index за пределы
            if start_index >= total_images:
                error_msg = f"Начальный индекс {start_index} превышает общее количество товаров ({total_images})"
                logging.warning(error_msg)
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
                collage_path = CollageCreator().create(image_models, tmp_file.name, is_price)

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
                "message": f"Collage {batch_number} of {total_batches} (products {start_index + 1}-{end_index} of {total_images})",
            }

            logging.info(f"Коллаж пакета создан: {collage_filename}")
            return collage_path, batch_info

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Ошибка при создании коллажа пакета: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при создании коллажа пакета: {e}",
            ) from e

    @staticmethod
    async def create_all_collages_zip(
        batch_size: int = 12, is_price: bool = True
    ) -> tuple[str, dict]:
        """
        Создает все коллажи из всех товаров и упаковывает в ZIP-архив

        Args:
            batch_size: Размер пакета (по умолчанию 12)
            is_price: Флаг, указывающий, нужно ли добавлять цену на оверлей

        Returns:
            Кортеж (путь_к_zip_файлу, информация_о_создании)

        Raises:
            CollageCreationError: Если ошибка создания коллажей
            ImageNotFoundError: Если товары не найдены
        """
        logging.info(
            f"Создание всех коллажей в ZIP-архиве с размером пакета {batch_size}"
        )

        try:
            # Получаем все изображения с товарами
            all_images_db = await ImageService.get_all_images_with_products()

            if not all_images_db:
                logging.warning("Products not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Products not found",
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

                        logging.info(
                            f"Создан коллаж {batch_num + 1}/{total_batches}: {collage_filename}"
                        )

            # Удаляем временную папку с коллажами
            try:
                if os.path.exists(temp_collages_dir):
                    shutil.rmtree(temp_collages_dir)
            except Exception as e:
                logging.warning(
                    f"Не удалось удалить временную папку {temp_collages_dir}: {e}"
                )

            # Информация о создании
            creation_info = {
                "total_batches": total_batches,
                "total_images": total_images,
                "batch_size": batch_size,
                "zip_filename": f"all_collages_{uuid.uuid4().hex[:8]}.zip",
                "message": f"Created {total_batches} collages from {total_images} products",
            }

            logging.info(
                f"Все коллажи созданы и упакованы в ZIP: {creation_info['zip_filename']}"
            )
            return zip_path, creation_info

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Ошибка при создании всех коллажей: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при создании всех коллажей: {e}",
            ) from e

    @staticmethod
    async def get_batch_info(start_index: int = 0, batch_size: int = 12) -> dict:
        """
        Возвращает информацию о текущем пакете товаров без создания коллажа

        Args:
            start_index: Начальный индекс для обработки
            batch_size: Размер пакета (по умолчанию 12)

        Returns:
            Информация о текущем пакете

        Raises:
            CollageCreationError: Если индекс выходит за пределы
            ImageNotFoundError: Если товары не найдены
        """
        logging.info(
            f"Получение информации о пакете: индекс {start_index}, размер {batch_size}"
        )

        try:
            # Получаем все изображения с товарами
            all_images_db = await ImageService.get_all_images_with_products()

            if not all_images_db:
                logging.warning("Products not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Products not found",
                )

            total_images = len(all_images_db)
            total_batches = (total_images + batch_size - 1) // batch_size

            # Проверяем, не выходит ли start_index за пределы
            if start_index >= total_images:
                error_msg = f"Начальный индекс {start_index} превышает общее количество товаров ({total_images})"
                logging.warning(error_msg)
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
                "message": f"Batch {batch_number} of {total_batches} (products {start_index + 1}-{end_index} of {total_images})",
            }

            logging.info(
                f"Информация о пакете получена: пакет {batch_number}/{total_batches}"
            )
            return result

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Ошибка при получении информации о пакете: {e}")
            raise

    @staticmethod
    async def get_batch_processing_status() -> dict:
        """
        Возвращает статус пакетной обработки коллажей

        Returns:
            Информация о статусе
        """
        logging.info("Получение статуса пакетной обработки")

        try:
            # Получаем все изображения с товарами
            all_images_db = await ImageService.get_all_images_with_products()

            if not all_images_db:
                logging.info("Products not found")
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

            result = {
                "total_images": total_images,
                "total_batches": total_batches,
                "batch_size": batch_size,
                "has_images": True,
                "message": f"Found {total_images} products. Can create {total_batches} collages with {batch_size} products each.",
            }

            logging.info(
                f"Статус получен: {total_images} товаров, {total_batches} пакетов"
            )
            return result

        except Exception as e:
            logging.error(f"Ошибка при получении статуса: {e}")
            raise

    @staticmethod
    def cleanup_temp_files() -> dict:
        """
        Очищает временные файлы коллажей

        Returns:
            Результат очистки
        """
        logging.info("Очистка временных файлов коллажей")

        try:
            # Очищаем временные файлы в /tmp
            temp_patterns = ["/tmp/collages_*", "/tmp/tmp*", "/tmp/*.jpg", "/tmp/*.zip"]

            cleaned_files = []
            cleaned_dirs = []

            for pattern in temp_patterns:
                try:
                    # Удаляем файлы
                    for file_path in glob.glob(pattern):
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            cleaned_files.append(file_path)

                    # Удаляем папки
                    for dir_path in glob.glob(pattern):
                        if os.path.isdir(dir_path):
                            shutil.rmtree(dir_path)
                            cleaned_dirs.append(dir_path)
                except Exception as e:
                    logging.warning(f"Не удалось очистить шаблон {pattern}: {e}")

            result = {
                "cleaned_files": cleaned_files,
                "cleaned_directories": cleaned_dirs,
                "total_cleaned": len(cleaned_files) + len(cleaned_dirs),
                "message": f"Очищено {len(cleaned_files)} файлов и {len(cleaned_dirs)} папок",
            }

            logging.info(f"Очистка завершена: {result['total_cleaned']} элементов")
            return result

        except Exception as e:
            logging.error(f"Ошибка при очистке временных файлов: {e}")
            raise
