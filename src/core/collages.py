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
from src.models.models import CollageInfoResponse, ImageWithProduct, Product

log = logging.getLogger(__name__)


class CollageService:
    """Сервис для работы с коллажами."""

    # Путь к папке с изображениями
    IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "images")

    @staticmethod
    def _get_all_image_files() -> list[str]:
        """Получает все файлы изображений из папки images."""
        if not os.path.exists(CollageService.IMAGES_DIR):
            log.warning("Папка с изображениями не найдена: %s", CollageService.IMAGES_DIR)
            return []

        image_extensions = ('*.jpg', '*.jpeg', '*.png', '*.webp')
        image_files = []
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(CollageService.IMAGES_DIR, ext)))

        # Сортируем по имени файла для стабильного порядка
        image_files.sort()
        log.info("Найдено изображений: %d", len(image_files))
        return image_files

    @staticmethod
    def _create_image_model(image_path: str, image_id: int) -> ImageWithProduct:
        """Создает модель изображения с продуктом из файла."""
        # Извлекаем имя файла без расширения как название продукта
        filename = os.path.basename(image_path)
        product_name = os.path.splitext(filename)[0]

        # Создаем продукт с базовой информацией
        product = Product(
            id=image_id,
            name=product_name,
            description=f"Изображение {filename}",
            price=0,
            categories=[],
        )

        return ImageWithProduct(
            id=image_id,
            product_id=image_id,
            path=image_path,
            product=product,
        )

    @staticmethod
    async def create_collage_by_ids(
        list_id: list[int],
        filename: str = "collage.jpg",
        is_price: bool = True,
    ) -> str:
        """Создает коллаж из выбранных изображений по их ID.

        Args:
            list_id: Список ID изображений (от 1 до 16)
            filename: Имя файла коллажа
            is_price: Флаг, указывающий, нужно ли добавлять цену на оверлей

        Returns:
            Путь к созданному коллажу

        Raises:
            HTTPException: Если ошибка создания коллажа

        """
        log.info(f"Создание коллажа из {len(list_id)} изображений")

        if len(list_id) < 1 or len(list_id) > 16:
            error_msg = f"Количество изображений должно быть от 1 до 16, получено: {len(list_id)}"
            log.warning(error_msg)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg,
            )

        try:
            # Получаем все файлы изображений
            all_image_files = CollageService._get_all_image_files()

            if not all_image_files:
                error_msg = "Изображения не найдены в папке images"
                log.warning(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_msg,
                )

            # Проверяем, что все ID существуют
            max_id = len(all_image_files)
            invalid_ids = [img_id for img_id in list_id if img_id < 1 or img_id > max_id]
            if invalid_ids:
                error_msg = f"Изображения с ID {invalid_ids} не найдены (доступно от 1 до {max_id})"
                log.warning(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_msg,
                )

            # Создаем модели для коллажа
            image_models = []
            for img_id in list_id:
                image_path = all_image_files[img_id - 1]  # ID начинаются с 1
                image_model = CollageService._create_image_model(image_path, img_id)
                image_models.append(image_model)

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
    async def get_all_products_info() -> CollageInfoResponse | None:
        """Возвращает информацию о всех доступных товарах для создания коллажей.

        Returns:
            Словарь с информацией о товарах и возможностях создания коллажей

        """
        log.debug("Получение информации о всех продуктах для коллажей")

        # Получаем все изображения
        all_image_files = CollageService._get_all_image_files()

        if not all_image_files:
            log.warning("Изображения не найдены")
            return None

        total_images = len(all_image_files)
        batch_size = 16
        total_batches = (total_images + batch_size - 1) // batch_size

        # Формируем информацию о товарах
        products_info = []
        for idx, image_path in enumerate(all_image_files, start=1):
            filename = os.path.basename(image_path)
            product_name = os.path.splitext(filename)[0]
            products_info.append({
                "id": idx,
                "product_id": idx,
                "name": product_name,
                "description": f"Изображение {filename}",
                "categories": [],
                "price": 0,
                "path": image_path,
            })

        result = CollageInfoResponse(
            total_images=total_images,
            total_batches=total_batches,
            batch_size=batch_size,
            has_images=True,
            products=products_info,
            categories=None,
            message=f"Found {total_images} products. Can create {total_batches} collages with {batch_size} products each.",
        )
        log.debug("Информация о продуктах получена: %s товаров", total_images)
        return result

    @staticmethod
    async def create_batch_collage(
        batch_size: int = 16,
        start_index: int = 0,
        is_price: bool = True,
    ) -> tuple[str, dict]:
        """Создает коллаж из текущего пакета товаров

        Args:
            batch_size: Размер пакета (по умолчанию 16)
            start_index: Начальный индекс для обработки
            is_price: Флаг, указывающий, нужно ли добавлять цену на оверлей

        Returns:
            Кортеж (путь_к_коллажу, информация_о_пакете)

        Raises:
            HTTPException: Если ошибка создания коллажа

        """
        log.info(
            "Создание коллажа пакета: размер %s, начальный индекс %s",
            batch_size,
            start_index,
        )

        try:
            # Получаем все изображения
            all_image_files = CollageService._get_all_image_files()

            if not all_image_files:
                log.warning("Изображения не найдены")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Изображения не найдены",
                )

            total_images = len(all_image_files)
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
            current_batch_files = all_image_files[start_index:end_index]

            # Создаем модели для коллажа
            image_models = []
            for idx, image_path in enumerate(current_batch_files, start=start_index + 1):
                image_model = CollageService._create_image_model(image_path, idx)
                image_models.append(image_model)

            # Генерируем уникальное имя файла
            batch_number = start_index // batch_size + 1
            collage_filename = (
                f"collage_batch_{batch_number}_{uuid.uuid4().hex[:8]}.jpg"
            )

            # Создаем временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                collage_path = CollageCreator().create(
                    image_models,
                    tmp_file.name,
                    is_price,
                )

            # Информация о пакете
            batch_info = {
                "batch_number": batch_number,
                "total_batches": total_batches,
                "processed_images": len(current_batch_files),
                "total_images": total_images,
                "start_index": start_index,
                "end_index": end_index,
                "has_more": end_index < total_images,
                "next_start_index": end_index if end_index < total_images else -1,
                "filename": collage_filename,
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
        batch_size: int = 16,
        is_price: bool = True,
    ) -> tuple[str, dict]:
        """Создает все коллажи из всех товаров и упаковывает в ZIP-архив

        Args:
            batch_size: Размер пакета (по умолчанию 16)
            is_price: Флаг, указывающий, нужно ли добавлять цену на оверлей

        Returns:
            Кортеж (путь_к_zip_файлу, информация_о_создании)

        Raises:
            HTTPException: Если ошибка создания коллажей

        """
        log.info(
            "Создание всех коллажей в ZIP-архиве с размером пакета %s",
            batch_size,
        )

        try:
            # Получаем все изображения
            all_image_files = CollageService._get_all_image_files()

            if not all_image_files:
                log.warning("Изображения не найдены")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Изображения не найдены",
                )

            # Создаем временную папку для коллажей
            temp_collages_dir = tempfile.mkdtemp(prefix="collages_")

            total_images = len(all_image_files)
            total_batches = (total_images + batch_size - 1) // batch_size

            # Создаем временный ZIP-файл
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
                zip_path = tmp_zip.name

                with zipfile.ZipFile(zip_path, "w") as zip_file:
                    for batch_num in range(total_batches):
                        start_index = batch_num * batch_size
                        end_index = min(start_index + batch_size, total_images)
                        current_batch_files = all_image_files[start_index:end_index]

                        # Создаем модели для коллажа
                        image_models = []
                        for idx, image_path in enumerate(current_batch_files, start=start_index + 1):
                            image_model = CollageService._create_image_model(image_path, idx)
                            image_models.append(image_model)

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
                    "Не удалось удалить временную папку %s: %s",
                    temp_collages_dir,
                    e,
                )

            # Информация о создании
            creation_info = {
                "total_batches": total_batches,
                "total_images": total_images,
                "batch_size": batch_size,
                "zip_filename": f"all_collages_{uuid.uuid4().hex[:8]}.zip",
                "message": f"Created {total_batches} collages from {total_images} products",
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
        batch_size: int = 16,
    ) -> dict:
        """Возвращает информацию о текущем пакете товаров без создания коллажа

        Args:
            start_index: Начальный индекс для обработки
            batch_size: Размер пакета (по умолчанию 16)

        Returns:
            Информация о текущем пакете

        Raises:
            HTTPException: Если индекс выходит за пределы

        """
        log.info(
            "Получение информации о пакете: индекс %s, размер %s",
            start_index,
            batch_size,
        )

        try:
            # Получаем все изображения
            all_image_files = CollageService._get_all_image_files()

            if not all_image_files:
                log.warning("Изображения не найдены")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Изображения не найдены",
                )

            total_images = len(all_image_files)
            total_batches = (total_images + batch_size - 1) // batch_size

            # Проверяем, не выходит ли start_index за пределы
            if start_index >= total_images:
                error_msg = f"Начальный индекс {start_index} превышает общее количество товаров ({total_images})"
                log.warning(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg,
                )

            # Информация о текущем пакете
            end_index = min(start_index + batch_size, total_images)
            current_batch = start_index // batch_size + 1

            batch_info = {
                "current_batch": current_batch,
                "total_batches": total_batches,
                "start_index": start_index,
                "end_index": end_index,
                "batch_size": batch_size,
                "total_images": total_images,
                "has_more": end_index < total_images,
                "next_start_index": end_index if end_index < total_images else -1,
                "message": f"Пакет {current_batch} из {total_batches} (изображения {start_index + 1}-{end_index} из {total_images})",
            }

            log.info(
                "Информация о пакете получена: пакет %d/%d",
                current_batch,
                total_batches,
            )
            return batch_info

        except HTTPException:
            raise
        except Exception as e:
            log.exception("Ошибка при получении информации о пакете: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при получении информации о пакете: {e}",
            ) from e

    @staticmethod
    async def get_batch_processing_status() -> CollageInfoResponse:
        """Возвращает статус пакетной обработки коллажей

        Returns:
            Информация о статусе

        """
        log.info("Получение статуса пакетной обработки")

        # Получаем все изображения
        all_image_files = CollageService._get_all_image_files()

        total_images = len(all_image_files)
        batch_size = 16
        total_batches = (total_images + batch_size - 1) // batch_size if total_images > 0 else 0

        result = CollageInfoResponse(
            total_images=total_images,
            total_batches=total_batches,
            batch_size=batch_size,
            has_images=total_images > 0,
            products=None,
            categories=None,
            message=f"Найдено {total_images} изображений. Можно создать {total_batches} коллажей.",
        )

        log.info("Статус получен: %d товаров", total_images)
        return result

    @staticmethod
    def cleanup_temp_files() -> dict:
        """Очищает временные файлы коллажей

        Returns:
            Результат очистки

        """
        log.info("Очистка временных файлов")

        temp_dir = tempfile.gettempdir()
        cleaned_count = 0

        # Удаляем временные файлы коллажей
        for pattern in ["collage_*.jpg", "collage_batch_*.jpg", "all_collages_*.zip"]:
            for file_path in glob.glob(os.path.join(temp_dir, pattern)):
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                    log.debug("Удален временный файл: %s", file_path)
                except Exception as e:
                    log.warning("Не удалось удалить файл %s: %s", file_path, e)

        result = {
            "total_cleaned": cleaned_count,
            "message": f"Очищено {cleaned_count} временных файлов",
        }

        log.info("Очистка завершена: удалено %d файлов", cleaned_count)
        return result
