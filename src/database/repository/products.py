import logging

from src.database.schema.products import ProductDb, product_categories
from src.database.connection import db
from src.models.models import Product
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import NoResultFound


class ProductRepository:
    @staticmethod
    @db.with_session
    async def add(session, new_product: Product) -> ProductDb:
        """
        Добавляет новый продукт в базу данных

        Args:
            session: Сессия базы данных
            new_product: Модель продукта для добавления

        Returns:
            Созданный продукт

        Raises:
            Exception: При ошибке создания продукта
        """
        logging.info(f"Добавление продукта в БД: {new_product.name}")
        product = ProductDb()
        product.name = new_product.name
        product.description = new_product.description
        product.price = new_product.price
        try:
            session.add(product)
            await session.commit()
            logging.info(
                f"Продукт успешно добавлен в БД: {new_product.name} (ID: {product.id})"
            )
        except Exception as e:
            logging.error(f"Ошибка при добавлении продукта в БД: {e}")
            await session.rollback()
            raise e
        return product

    @staticmethod
    @db.with_session
    async def get_all(session) -> list[ProductDb]:
        """
        Получает все продукты из базы данных

        Args:
            session: Сессия базы данных

        Returns:
            Список всех продуктов

        Raises:
            Exception: При ошибке получения продуктов
        """
        logging.info("Получение всех продуктов из БД")
        try:
            result = await session.execute(select(ProductDb))
            products = result.scalars().all()
            logging.info(f"Получено продуктов из БД: {len(products)}")
            return products
        except Exception as e:
            logging.error(f"Ошибка при получении продуктов из БД: {e}")
            raise e

    @staticmethod
    @db.with_session
    async def delete(session, product_id: int):
        """
        Удаляет продукт из базы данных

        Args:
            session: Сессия базы данных
            product_id: ID продукта

        Raises:
            ProductNotFoundError: Если продукт не найден
            Exception: При ошибке удаления продукта
        """
        logging.info(f"Удаление продукта из БД: ID {product_id}")
        try:
            result = await session.execute(
                select(ProductDb).where(ProductDb.id == product_id)
            )
            product = result.scalars().first()
            if not product:
                logging.warning(
                    f"Продукт с ID {product_id} не найден в БД для удаления"
                )
                raise NoResultFound(f"Product with ID {product_id} not found")

            product_name = product.name
            await session.delete(product)
            await session.commit()
            logging.info(f"Продукт успешно удален из БД: {product_name}")
        except NoResultFound:
            raise
        except Exception as e:
            logging.error(f"Ошибка при удалении продукта из БД: {e}")
            await session.rollback()
            raise e

    @staticmethod
    @db.with_session
    async def update(session, new_product: Product):
        """
        Обновляет продукт в базе данных

        Args:
            session: Сессия базы данных
            new_product: Модель продукта с обновленными данными

        Raises:
            ProductNotFoundError: Если продукт не найден
            Exception: При ошибке обновления продукта
        """
        logging.info(f"Обновление продукта в БД: ID {new_product.id}")
        try:
            result = await session.execute(
                select(ProductDb).where(ProductDb.id == new_product.id)
            )
            product = result.scalars().first()
            if not product:
                logging.warning(
                    f"Продукт с ID {new_product.id} не найден в БД для обновления"
                )
                raise NoResultFound(f"Product with ID {new_product.id} not found")

            product.name = new_product.name
            product.description = new_product.description
            product.price = new_product.price
            await session.commit()
            logging.info(f"Продукт успешно обновлен в БД: {new_product.name}")
        except NoResultFound:
            raise
        except Exception as e:
            logging.error(f"Ошибка при обновлении продукта в БД: {e}")
            await session.rollback()
            raise e

    @staticmethod
    @db.with_session
    async def get_by_id(session, product_id: int) -> ProductDb | None:
        """
        Получает продукт по ID из базы данных

        Args:
            session: Сессия базы данных
            product_id: ID продукта

        Returns:
            Продукт или None если не найден

        Raises:
            Exception: При ошибке получения продукта
        """
        logging.info(f"Получение продукта из БД по ID: {product_id}")
        try:
            result = await session.execute(
                select(ProductDb).where(ProductDb.id == product_id)
            )
            product = result.scalars().first()
            if product:
                logging.info(f"Продукт найден в БД: {product.name}")
            else:
                logging.info(f"Продукт с ID {product_id} не найден в БД")
            return product
        except Exception as e:
            logging.error(
                f"Ошибка при получении продукта из БД по ID {product_id}: {e}"
            )
            raise e

    @staticmethod
    @db.with_session
    async def get_by_id_with_categories(session, product_id: int) -> ProductDb | None:
        """
        Получает продукт по ID с загруженными категориями

        Args:
            session: Сессия базы данных
            product_id: ID продукта

        Returns:
            Продукт с категориями или None если не найден

        Raises:
            Exception: При ошибке получения продукта
        """
        logging.info(f"Получение продукта из БД по ID с категориями: {product_id}")
        try:
            result = await session.execute(
                select(ProductDb)
                .options(joinedload(ProductDb.categories))
                .where(ProductDb.id == product_id)
            )
            product = result.unique().scalars().first()
            if product:
                logging.info(f"Продукт найден в БД: {product.name}")
            else:
                logging.info(f"Продукт с ID {product_id} не найден в БД")
            return product
        except Exception as e:
            logging.error(
                f"Ошибка при получении продукта из БД по ID {product_id}: {e}"
            )
            raise e

    @staticmethod
    @db.with_session
    async def update_categories(session, product_id: int, category_ids: list[int]):
        """
        Обновляет категории продукта

        Args:
            session: Сессия базы данных
            product_id: ID продукта
            category_ids: Список ID категорий

        Raises:
            Exception: При ошибке обновления
        """
        logging.info(f"Обновление категорий продукта ID {product_id}")
        try:
            # Удаляем старые связи
            await session.execute(
                delete(product_categories).where(
                    product_categories.c.product_id == product_id
                )
            )

            # Добавляем новые связи
            if category_ids:
                await session.execute(
                    insert(product_categories).values([
                        {"product_id": product_id, "category_id": cat_id}
                        for cat_id in category_ids
                    ])
                )

            await session.commit()
            logging.info(f"Категории продукта {product_id} успешно обновлены")
        except Exception as e:
            logging.error(f"Ошибка при обновлении категорий продукта {product_id}: {e}")
            await session.rollback()
            raise e
