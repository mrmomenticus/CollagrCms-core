"""Бизнес-логика для работы с продуктами
"""

import logging

from fastapi import HTTPException, status

from src.database.repository.categories import CategoryRepository
from src.database.repository.products import ProductRepository
from src.database.schema.products import ProductDb
from src.models.models import Product


class ProductService:
    """Сервис для работы с продуктами"""

    @staticmethod
    async def create_product(
        name: str,
        description: str,
        category_names: list[str],
        price: int,
    ) -> ProductDb:
        """Создает новый продукт

        Args:
            name: Название продукта
            description: Описание продукта
            category_names: Список названий категорий
            price: Цена продукта

        Returns:
            Созданный продукт (DB модель)

        Raises:
            CategoryNotFoundError: Если категория не найдена
            CategoryInactiveError: Если категория неактивна

        """
        logging.info("Создание продукта: %s в категориях %s", name, category_names)

        try:
            categories = []
            for category_name in category_names:
                # Проверяем существование и активность категории
                category = await CategoryRepository.get_by_name(category_name)
                if not category:
                    logging.warning("Категория '%s' не найдена", category_name)
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Категория '{category_name}' не найдена",
                    )

                if not category.is_active:
                    logging.warning("Категория '%s' неактивна", category_name)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Категория '{category_name}' неактивна",
                    )
                categories.append(category)

            # Создаем продукт
            product_model = Product(
                id=0,
                name=name,
                description=description,
                price=price,
            )

            product_db = await ProductRepository.add(product_model)

            # Добавляем категории к продукту
            await ProductRepository.update_categories(
                product_db.id, [cat.id for cat in categories],
            )

            # Получаем обновленный продукт с категориями
            product_with_categories = await ProductRepository.get_by_id_with_categories(
                product_db.id,
            )
            if product_with_categories:
                logging.info(f"Продукт успешно создан: {name} (ID: {product_db.id})")
                return product_with_categories
            logging.error(
                "Не удалось получить созданный продукт с категориями: %s", name,
            )
            return product_db

        except HTTPException:
            raise
        except Exception as e:
            logging.exception("Ошибка при создании продукта %s: %s", name, e)
            raise

    @staticmethod
    async def get_all_products() -> list[ProductDb]:
        """Получает все продукты

        Returns:
            Список всех продуктов

        """
        logging.info("Получение всех продуктов")

        try:
            products_db = await ProductRepository.get_all()
            logging.info(f"Получено продуктов: {len(products_db)}")
            return products_db
        except Exception as e:
            logging.exception("Ошибка при получении продуктов: %s", e)
            raise

    @staticmethod
    async def get_product_by_id(product_id: int) -> ProductDb:
        """Получает продукт по ID

        Args:
            product_id: ID продукта

        Returns:
            Продукт

        Raises:
            ProductNotFoundError: Если продукт не найден

        """
        logging.info("Получение продукта по ID: %s", product_id)

        try:
            # В текущей реализации ProductRepository нет метода get_by_id
            # Используем get_all и фильтруем
            products = await ProductRepository.get_all()
            product = next((p for p in products if p.id == product_id), None)

            if not product:
                logging.warning("Продукт с ID %s не найден", product_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Продукт с ID {product_id} не найден",
                )

            logging.info(f"Продукт найден: {product.name}")
            return product
        except HTTPException:
            raise
        except Exception as e:
            logging.exception("Ошибка при получении продукта %s: %s", product_id, e)
            raise

    @staticmethod
    async def update_product(
        product_id: int,
        name: str,
        description: str,
        category_names: list[str],
        price: int,
    ) -> None:
        """Обновляет продукт

        Args:
            product_id: ID продукта
            name: Новое название продукта
            description: Новое описание продукта
            category_names: Список названий категорий
            price: Новая цена продукта

        Raises:
            ProductNotFoundError: Если продукт не найден
            CategoryNotFoundError: Если категория не найдена
            CategoryInactiveError: Если категория неактивна

        """
        logging.info("Обновление продукта ID %s", product_id)

        try:
            # Проверяем существование продукта
            await ProductService.get_product_by_id(product_id)

            categories = []
            for category_name in category_names:
                # Проверяем существование и активность категории
                category = await CategoryRepository.get_by_name(category_name)
                if not category:
                    logging.warning("Категория '%s' не найдена", category_name)
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Категория '{category_name}' не найдена",
                    )

                if not category.is_active:
                    logging.warning("Категория '%s' неактивна", category_name)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Категория '{category_name}' неактивна",
                    )
                categories.append(category)

            # Обновляем продукт
            product_model = Product(
                id=product_id,
                name=name,
                description=description,
                price=price,
            )

            await ProductRepository.update(product_model)

            # Обновляем категории
            await ProductRepository.update_categories(
                product_id, [cat.id for cat in categories],
            )

            logging.info("Продукт успешно обновлен: %s", name)

        except HTTPException:
            raise
        except Exception as e:
            logging.exception("Ошибка при обновлении продукта %s: %s", product_id, e)
            raise

    @staticmethod
    async def delete_product(product_id: int) -> None:
        """Удаляет продукт

        Args:
            product_id: ID продукта

        Raises:
            ProductNotFoundError: Если продукт не найден

        """
        logging.info("Удаление продукта ID %s", product_id)

        try:
            # Проверяем существование продукта
            product = await ProductService.get_product_by_id(product_id)

            await ProductRepository.delete(product_id)
            logging.info(f"Продукт успешно удален: {product.name}")

        except HTTPException:
            raise
        except Exception as e:
            logging.exception("Ошибка при удалении продукта %s: %s", product_id, e)
            raise
