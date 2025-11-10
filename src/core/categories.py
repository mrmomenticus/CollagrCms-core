import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.core.images import ImageService
from src.database.connection import db
from src.database.repository.categories import CategoryRepository
from src.database.repository.products import ProductRepository
from src.database.schema.products import ProductDb
from src.models.models import Category, CategoryUpdateRequest
from src.utils.exceptions import NotFoundError
from src.utils.file import delete_file

log = logging.getLogger(__name__)


class CategoryService:
    """Сервис для работы с категориями."""

    @staticmethod
    async def create_category(name: str, description: str | None = None) -> Category:
        """Создает новую категорию.

        Args:
            name: Название категории
            description: Описание категории

        Returns:
            Созданная категория

        Raises:
            CategoryAlreadyExistsError: Если категория с таким именем уже существует

        """
        log.info(f"Создание категории: {name}")

        # Проверяем, что категория с таким именем не существует
        existing_category = await CategoryRepository.get_by_name(name)
        if existing_category:
            log.warning(f"Попытка создать существующую категорию: {name}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Категория с названием '{name}' уже существует",
            )

        try:
            category_db = await CategoryRepository.add(name, description)
            log.info(f"Категория успешно создана: {name} (ID: {category_db.id})")
            return Category.model_validate(category_db)
        except Exception as e:
            log.error(f"Ошибка при создании категории {name}: {e}")
            raise

    @staticmethod
    async def get_all_categories(is_active_categories: bool = False) -> list[Category]:
        """Получает все категории.

        Args:
            is_active_categories: Включать ли неактивные категории

        Returns:
            Список категорий

        """
        log.info(
            f"Получение всех категорий (включая неактивные: {is_active_categories})"
        )

        try:
            if is_active_categories:
                categories_db = await CategoryRepository.get_all_including_inactive()
            else:
                categories_db = await CategoryRepository.get_all()

            categories = [Category.model_validate(cat) for cat in categories_db]
            log.info(f"Получено категорий: {len(categories)}")
            return categories
        except Exception as e:
            log.error(f"Ошибка при получении категорий: {e}")
            raise

    @staticmethod
    async def get_category_by_id(category_id: int) -> Category:
        """Получает категорию по ID.

        Args:
            category_id: ID категории

        Returns:
            Категория

        Raises:
            CategoryNotFoundError: Если категория не найдена

        """
        log.info(f"Получение категории по ID: {category_id}")

        try:
            category_db = await CategoryRepository.get_by_id(category_id)
            if not category_db:
                log.warning(f"Категория с ID {category_id} не найдена")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Категория с ID {category_id} не найдена",
                )

            log.info(f"Категория найдена: {category_db.name}")
            return Category.model_validate(category_db)
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Ошибка при получении категории {category_id}: {e}")
            raise

    @staticmethod
    async def get_category_by_name(name: str, check_active: bool = True) -> Category:
        """Получает категорию по названию.

        Args:
            name: Название категории
            check_active: Проверять ли активность категории

        Returns:
            Категория

        Raises:
            CategoryNotFoundError: Если категория не найдена
            CategoryInactiveError: Если категория неактивна

        """
        log.info(f"Получение категории по имени: {name}")

        try:
            category_db = await CategoryRepository.get_by_name(name)
            if not category_db:
                log.warning(f"Категория '{name}' не найдена")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Категория '{name}' не найдена",
                )

            if check_active and not category_db.is_active:
                log.warning(f"Категория '{name}' неактивна")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Категория '{name}' неактивна",
                )

            log.info(f"Категория найдена: {name}")
            return Category.model_validate(category_db)
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Ошибка при получении категории '{name}': {e}")
            raise

    @staticmethod
    async def update_category(
        category_id: int, request: CategoryUpdateRequest
    ) -> Category:
        """Обновляет категорию.

        Args:
            category_id: ID категории
            request: Обновленная категория(name, description, is_active)

        Returns:
            Обновленная категория

        Raises:
            CategoryNotFoundError: Если категория не найдена
            CategoryAlreadyExistsError: Если новое имя уже занято

        """
        log.info(f"Обновление категории ID {category_id}")

        try:
            # Проверяем существование категории
            existing_category = await CategoryRepository.get_by_id(category_id)
            if not existing_category:
                log.warning(f"Категория с ID {category_id} не найдена")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Категория с ID {category_id} не найдена",
                )

            # Если меняем имя, проверяем что новое имя не занято
            if request.name != existing_category.name:
                category_with_name = await CategoryRepository.get_by_name(request.name)
                if category_with_name:
                    log.warning(f"Категория с именем '{request.name}' уже существует")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Категория с названием '{request.name}' уже существует",
                    )

            await CategoryRepository.update(category_id, request)

            # Получаем обновленную категорию
            updated_category = await CategoryRepository.get_by_id(category_id)
            if not updated_category:
                log.error(
                    f"Не удалось получить обновленную категорию с ID {category_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Категория с ID {category_id} не найдена",
                )
            log.info(f"Категория успешно обновлена: {updated_category.name}")
            return Category.model_validate(updated_category)
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Ошибка при обновлении категории {category_id}: {e}")
            raise

    @staticmethod
    async def delete_category(category_id: int, hard_delete: bool = False) -> str:
        """Удаляет категорию (мягкое или жесткое удаление).

        Args:
            category_id: ID категории
            hard_delete: Полностью удалить из БД или только деактивировать

        Raises:
            NotFound: Если категория не найдена
        Return:
            Название удаленной категории

        """
        log.info(f"Удаление категории ID {category_id} (жесткое: {hard_delete})")
        # Проверяем существование категории
        existing_category = await CategoryRepository.get_by_id(category_id)
        if not existing_category:
            log.warning(f"Категория с ID {category_id} не найдена")
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
            log.info(
                f"Удаление продукта {product.name} (ID: {product.id}) из-за удаления единственной категории"
            )
            # Удаляем изображения
            images = await ImageService.get_images_by_ids(list_id_products=[product.id])
            if images:
                for img in images:
                    await delete_file(img.path)
            # Удаляем продукт
            await ProductRepository.delete(product.id)
        if hard_delete:
            await CategoryRepository.hard_delete(category_id)
            log.info(f"Категория {existing_category.name} полностью удалена")
        else:
            await CategoryRepository.delete(category_id)
            log.info(f"Категория {existing_category.name} деактивирована")
        return existing_category.name
