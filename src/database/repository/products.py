import logging
from src.database.schema.images import ImagesDb
from src.database.schema.products import ProductDb
from src.database.connection import db
from src.models.models import Product
from src.utils.exceptions import ProductNotFoundError
from sqlalchemy import select
from sqlalchemy.orm import joinedload


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
        product.category_id = new_product.category_id if new_product.category_id is not None else 0
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
                raise ProductNotFoundError(product_id)

            product_name = product.name
            await session.delete(product)
            await session.commit()
            logging.info(f"Продукт успешно удален из БД: {product_name}")
        except ProductNotFoundError:
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
                raise ProductNotFoundError(new_product.id)

            product.name = new_product.name
            product.description = new_product.description
            product.category_id = new_product.category_id if new_product.category_id is not None else 0
            product.price = new_product.price
            await session.commit()
            logging.info(f"Продукт успешно обновлен в БД: {new_product.name}")
        except ProductNotFoundError:
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
