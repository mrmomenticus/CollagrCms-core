import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.core.images import ImageService
from src.database.connection import db
from src.database.repository.categories import CategoryRepository
from src.database.repository.products import ProductRepository
from src.database.schema.products import ProductDb
from src.models.models import Category
from src.utils.file import delete_file
from src.utils.exceptions import NotFoundError


class CategoryService:
    """Сервис для работы с категориями"""

    @staticmethod
    async def create_category(name: str, description: str | None = None) -> Category:
        """Создает новую категорию

        Args:
            name: Название категории
            description: Описание категории

        Returns:
            Созданная категория

        Raises:
            CategoryAlreadyExistsError: Если категория с таким именем уже существует

        """
        logging.info(f"Создание категории: {name}")

        # Проверяем, что категория с таким именем не существует
        existing_category = await CategoryRepository.get_by_name(name)
        if existing_category:
            logging.warning(f"Попытка создать существующую категорию: {name}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Категория с названием '{name}' уже существует",
            )

        try:
            category_db = await CategoryRepository.add(name, description)
            logging.info(f"Категория успешно создана: {name} (ID: {category_db.id})")
            return Category.model_validate(category_db)
        except Exception as e:
            logging.error(f"Ошибка при создании категории {name}: {e}")
            raise

    @staticmethod
    async def get_all_categories(is_active_categories: bool = False) -> list[Category]:
        """Получает все категории

        Args:
            include_inactive: Включать ли неактивные категории

        Returns:
            Список категорий

        """
        logging.info(
            f"Получение всех категорий (включая неактивные: {is_active_categories})"
        )

        try:
            if is_active_categories:
                categories_db = await CategoryRepository.get_all_including_inactive()
            else:
                categories_db = await CategoryRepository.get_all()

            categories = [Category.model_validate(cat) for cat in categories_db]
            logging.info(f"Получено категорий: {len(categories)}")
            return categories
        except Exception as e:
            logging.error(f"Ошибка при получении категорий: {e}")
            raise

    @staticmethod
    async def get_category_by_id(category_id: int) -> Category:
        """Получает категорию по ID

        Args:
            category_id: ID категории

        Returns:
            Категория

        Raises:
            CategoryNotFoundError: Если категория не найдена

        """
        logging.info(f"Получение категории по ID: {category_id}")

        try:
            category_db = await CategoryRepository.get_by_id(category_id)
            if not category_db:
                logging.warning(f"Категория с ID {category_id} не найдена")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Категория с ID {category_id} не найдена",
                )

            logging.info(f"Категория найдена: {category_db.name}")
            return Category.model_validate(category_db)
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Ошибка при получении категории {category_id}: {e}")
            raise

    @staticmethod
    async def get_category_by_name(name: str, check_active: bool = True) -> Category:
        """Получает категорию по названию

        Args:
            name: Название категории
            check_active: Проверять ли активность категории

        Returns:
            Категория

        Raises:
            CategoryNotFoundError: Если категория не найдена
            CategoryInactiveError: Если категория неактивна

        """
        logging.info(f"Получение категории по имени: {name}")

        try:
            category_db = await CategoryRepository.get_by_name(name)
            if not category_db:
                logging.warning(f"Категория '{name}' не найдена")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Категория '{name}' не найдена",
                )

            if check_active and not category_db.is_active:
                logging.warning(f"Категория '{name}' неактивна")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Категория '{name}' неактивна",
                )

            logging.info(f"Категория найдена: {name}")
            return Category.model_validate(category_db)
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Ошибка при получении категории '{name}': {e}")
            raise

    @staticmethod
    async def update_category(
        category_id: int, request: CategoryUpdateRequest
    ) -> Category:
        """Обновляет категорию

        Args:
            category_id: ID категории
            name: Новое название категории
            description: Новое описание категории
            is_active: Статус активности

        Returns:
            Обновленная категория

        Raises:
            CategoryNotFoundError: Если категория не найдена
            CategoryAlreadyExistsError: Если новое имя уже занято

        """
        logging.info(f"Обновление категории ID {category_id}")

        try:
            # Проверяем существование категории
            existing_category = await CategoryRepository.get_by_id(category_id)
            if not existing_category:
                logging.warning(f"Категория с ID {category_id} не найдена")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Категория с ID {category_id} не найдена",
                )

            # Если меняем имя, проверяем что новое имя не занято
            if name and name != existing_category.name:
                category_with_name = await CategoryRepository.get_by_name(name)
                if category_with_name:
                    logging.warning(f"Категория с именем '{name}' уже существует")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Категория с названием '{name}' уже существует",
                    )

            await CategoryRepository.update(category_id, name, description, is_active)

            # Получаем обновленную категорию
            updated_category = await CategoryRepository.get_by_id(category_id)
            if not updated_category:
                logging.error(
                    f"Не удалось получить обновленную категорию с ID {category_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Категория с ID {category_id} не найдена",
                )
            logging.info(f"Категория успешно обновлена: {updated_category.name}")
            return Category.model_validate(updated_category)
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Ошибка при обновлении категории {category_id}: {e}")
            raise

    @staticmethod
    async def delete_category(category_id: int, hard_delete: bool = False) -> str:
        """Удаляет категорию (мягкое или жесткое удаление)

        Args:
            category_id: ID категории
            hard_delete: Полностью удалить из БД или только деактивировать

        Raises:
            NotFound: Если категория не найдена
        Return:
            Название удаленной категории
        """
        logging.info(f"Удаление категории ID {category_id} (жесткое: {hard_delete})")

        try:
            # Проверяем существование категории
            existing_category = await CategoryRepository.get_by_id(category_id)
            if not existing_category:
                logging.warning(f"Категория с ID {category_id} не найдена")
                raise NotFoundError(f"Не найдена категория {category_id}")

            # Находим продукты, у которых только эта категория
            products_to_delete = []
            async with db.get_session() as session:
                result = await session.execute(
                    select(ProductDb).options(joinedload(ProductDb.categories))
                )
                all_products = result.unique().scalars().all()

                for product in all_products:
                    if (
                        len(product.categories) == 1
                        and product.categories[0].id == category_id
                    ):
                        products_to_delete.append(product)

            for product in products_to_delete:
                logging.info(
                    f"Удаление продукта {product.name} (ID: {product.id}) из-за удаления единственной категории"
                )
                # Удаляем изображения
                images = await ImageService.get_images_by_ids(
                    list_id_products=[product.id]
                )
                if images:
                    for img in images:
                        await delete_file(img.path)
                # Удаляем продукт
                await ProductRepository.delete(product.id)

            if hard_delete:
                await CategoryRepository.hard_delete(category_id)
                logging.info(f"Категория {existing_category.name} полностью удалена")
            else:
                await CategoryRepository.delete(category_id)
                logging.info(f"Категория {existing_category.name} деактивирована")
            return existing_category.name
