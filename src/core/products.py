"""
Бизнес-логика для работы с продуктами
"""

import logging
from typing import List

from src.database.repository.products import ProductRepository
from src.database.repository.categories import CategoryRepository
from src.database.schema.products import ProductDb
from src.models.models import Product
from src.utils.exceptions import (
    ProductNotFoundError,
    CategoryNotFoundError,
    CategoryInactiveError,
)


class ProductService:
    """Сервис для работы с продуктами"""

    @staticmethod
    async def create_product(
        name: str,
        description: str,
        category_name: str,
        price: int,
    ) -> ProductDb:
        """
        Создает новый продукт

        Args:
            name: Название продукта
            description: Описание продукта
            category_name: Название категории
            price: Цена продукта

        Returns:
            Созданный продукт (DB модель)

        Raises:
            CategoryNotFoundError: Если категория не найдена
            CategoryInactiveError: Если категория неактивна
        """
        logging.info(f"Создание продукта: {name} в категории {category_name}")

        try:
            # Проверяем существование и активность категории
            category = await CategoryRepository.get_by_name(category_name)
            if not category:
                logging.warning(f"Категория '{category_name}' не найдена")
                raise CategoryNotFoundError(category_name=category_name)

            if not category.is_active:
                logging.warning(f"Категория '{category_name}' неактивна")
                raise CategoryInactiveError(category_name)

            # Создаем продукт
            product_model = Product(
                id=0,
                name=name,
                description=description,
                category_id=category.id,
                price=price,
            )

            product_db = await ProductRepository.add(product_model)
            logging.info(f"Продукт успешно создан: {name} (ID: {product_db.id})")
            return product_db

        except (CategoryNotFoundError, CategoryInactiveError):
            raise
        except Exception as e:
            logging.error(f"Ошибка при создании продукта {name}: {e}")
            raise

    @staticmethod
    async def get_all_products() -> List[ProductDb]:
        """
        Получает все продукты

        Returns:
            Список всех продуктов
        """
        logging.info("Получение всех продуктов")

        try:
            products_db = await ProductRepository.get_all()
            logging.info(f"Получено продуктов: {len(products_db)}")
            return products_db
        except Exception as e:
            logging.error(f"Ошибка при получении продуктов: {e}")
            raise

    @staticmethod
    async def get_product_by_id(product_id: int) -> ProductDb:
        """
        Получает продукт по ID

        Args:
            product_id: ID продукта

        Returns:
            Продукт

        Raises:
            ProductNotFoundError: Если продукт не найден
        """
        logging.info(f"Получение продукта по ID: {product_id}")

        try:
            # В текущей реализации ProductRepository нет метода get_by_id
            # Используем get_all и фильтруем
            products = await ProductRepository.get_all()
            product = next((p for p in products if p.id == product_id), None)

            if not product:
                logging.warning(f"Продукт с ID {product_id} не найден")
                raise ProductNotFoundError(product_id)

            logging.info(f"Продукт найден: {product.name}")
            return product
        except ProductNotFoundError:
            raise
        except Exception as e:
            logging.error(f"Ошибка при получении продукта {product_id}: {e}")
            raise

    @staticmethod
    async def update_product(
        product_id: int,
        name: str,
        description: str,
        category_name: str,
        price: int,
    ) -> None:
        """
        Обновляет продукт

        Args:
            product_id: ID продукта
            name: Новое название продукта
            description: Новое описание продукта
            category_name: Название категории
            price: Новая цена продукта

        Raises:
            ProductNotFoundError: Если продукт не найден
            CategoryNotFoundError: Если категория не найдена
            CategoryInactiveError: Если категория неактивна
        """
        logging.info(f"Обновление продукта ID {product_id}")

        try:
            # Проверяем существование продукта
            await ProductService.get_product_by_id(product_id)

            # Проверяем существование и активность категории
            category = await CategoryRepository.get_by_name(category_name)
            if not category:
                logging.warning(f"Категория '{category_name}' не найдена")
                raise CategoryNotFoundError(category_name=category_name)

            if not category.is_active:
                logging.warning(f"Категория '{category_name}' неактивна")
                raise CategoryInactiveError(category_name)

            # Обновляем продукт
            product_model = Product(
                id=product_id,
                name=name,
                description=description,
                category_id=category.id,
                price=price,
            )

            await ProductRepository.update(product_model)
            logging.info(f"Продукт успешно обновлен: {name}")

        except (ProductNotFoundError, CategoryNotFoundError, CategoryInactiveError):
            raise
        except Exception as e:
            logging.error(f"Ошибка при обновлении продукта {product_id}: {e}")
            raise

    @staticmethod
    async def delete_product(product_id: int) -> None:
        """
        Удаляет продукт

        Args:
            product_id: ID продукта

        Raises:
            ProductNotFoundError: Если продукт не найден
        """
        logging.info(f"Удаление продукта ID {product_id}")

        try:
            # Проверяем существование продукта
            product = await ProductService.get_product_by_id(product_id)

            await ProductRepository.delete(product_id)
            logging.info(f"Продукт успешно удален: {product.name}")

        except ProductNotFoundError:
            raise
        except Exception as e:
            logging.error(f"Ошибка при удалении продукта {product_id}: {e}")
            raise
