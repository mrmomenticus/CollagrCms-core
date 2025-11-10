import logging

from sqlalchemy import delete, insert, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import joinedload

from src.database.connection import db
from src.database.schema.products import ProductDb, product_categories
from src.models.models import Product

log = logging.getLogger(__name__)
class ProductRepository:
    @staticmethod
    @db.with_session
    async def add(session, new_product: Product) -> ProductDb:
        """Добавляет новый продукт в базу данных.

        Args:
            session: Сессия базы данных
            new_product: Модель продукта для добавления

        Returns:
            Созданный продукт

        Raises:
            Exception: При ошибке создания продукта

        """
        log.info(f"Добавление продукта в БД: {new_product.name}")
        product = ProductDb()
        product.name = new_product.name
        product.description = new_product.description
        product.price = new_product.price
        try:
            session.add(product)
            await session.commit()
            log.info(
                f"Продукт успешно добавлен в БД: {new_product.name} (ID: {product.id})",
            )
        except Exception as e:
            log.exception("Ошибка при добавлении продукта в БД: %s", e)
            await session.rollback()
            raise e
        return product

    @staticmethod
    @db.with_session
    async def get_all(session) -> list[ProductDb]:
        """Получает все продукты из базы данных.

        Args:
            session: Сессия базы данных

        Returns:
            Список всех продуктов

        Raises:
            Exception: При ошибке получения продуктов

        """
        log.info("Получение всех продуктов из БД")
        try:
            result = await session.execute(select(ProductDb))
            products = result.scalars().all()
            log.info(f"Получено продуктов из БД: {len(products)}")
            return products
        except Exception as e:
            log.exception("Ошибка при получении продуктов из БД: %s", e)
            raise e

    @staticmethod
    @db.with_session
    async def delete(session, product_id: int):
        """Удаляет продукт из базы данных.

        Args:
            session: Сессия базы данных
            product_id: ID продукта

        Raises:
            ProductNotFoundError: Если продукт не найден
            Exception: При ошибке удаления продукта

        """
        log.info("Удаление продукта из БД: ID %s", product_id)
        try:
            result = await session.execute(
                select(ProductDb).where(ProductDb.id == product_id),
            )
            product = result.scalars().first()
            if not product:
                log.warning(
                    "Продукт с ID %s не найден в БД для удаления", product_id,
                )
                raise NoResultFound(f"Product with ID {product_id} not found")

            product_name = product.name
            await session.delete(product)
            await session.commit()
            log.info("Продукт успешно удален из БД: %s", product_name)
        except NoResultFound:
            raise
        except Exception as e:
            log.exception("Ошибка при удалении продукта из БД: %s", e)
            await session.rollback()
            raise e

    @staticmethod
    @db.with_session
    async def update(session, new_product: Product):
        """Обновляет продукт в базе данных.

        Args:
            session: Сессия базы данных
            new_product: Модель продукта с обновленными данными

        Raises:
            ProductNotFoundError: Если продукт не найден
            Exception: При ошибке обновления продукта

        """
        log.info(f"Обновление продукта в БД: ID {new_product.id}")
        try:
            result = await session.execute(
                select(ProductDb).where(ProductDb.id == new_product.id),
            )
            product = result.scalars().first()
            if not product:
                log.warning(
                    f"Продукт с ID {new_product.id} не найден в БД для обновления",
                )
                raise NoResultFound(f"Product with ID {new_product.id} not found")

            product.name = new_product.name
            product.description = new_product.description
            product.price = new_product.price
            await session.commit()
            log.info(f"Продукт успешно обновлен в БД: {new_product.name}")
        except NoResultFound:
            raise
        except Exception as e:
            log.exception("Ошибка при обновлении продукта в БД: %s", e)
            await session.rollback()
            raise e

    @staticmethod
    @db.with_session
    async def get_by_id(session, product_id: int) -> ProductDb | None:
        """Получает продукт по ID из базы данных.

        Args:
            session: Сессия базы данных
            product_id: ID продукта

        Returns:
            Продукт или None если не найден

        Raises:
            Exception: При ошибке получения продукта

        """
        log.info("Получение продукта из БД по ID: %s", product_id)
        try:
            result = await session.execute(
                select(ProductDb).where(ProductDb.id == product_id),
            )
            product = result.scalars().first()
            if product:
                log.info(f"Продукт найден в БД: {product.name}")
            else:
                log.info("Продукт с ID %s не найден в БД", product_id)
            return product
        except Exception as e:
            log.exception(
                "Ошибка при получении продукта из БД по ID %s: %s", product_id, e,
            )
            raise e

    @staticmethod
    @db.with_session
    async def get_by_id_with_categories(session, product_id: int) -> ProductDb | None:
        """Получает продукт по ID с загруженными категориями.

        Args:
            session: Сессия базы данных
            product_id: ID продукта

        Returns:
            Продукт с категориями или None если не найден

        Raises:
            Exception: При ошибке получения продукта

        """
        log.info("Получение продукта из БД по ID с категориями: %s", product_id)
        try:
            result = await session.execute(
                select(ProductDb)
                .options(joinedload(ProductDb.categories))
                .where(ProductDb.id == product_id),
            )
            product = result.unique().scalars().first()
            if product:
                log.info(f"Продукт найден в БД: {product.name}")
            else:
                log.info("Продукт с ID %s не найден в БД", product_id)
            return product
        except Exception as e:
            log.exception(
                "Ошибка при получении продукта из БД по ID %s: %s", product_id, e,
            )
            raise e

    @staticmethod
    @db.with_session
    async def update_categories(session, product_id: int, category_ids: list[int]):
        """Обновляет категории продукта.

        Args:
            session: Сессия базы данных
            product_id: ID продукта
            category_ids: Список ID категорий

        Raises:
            Exception: При ошибке обновления

        """
        log.info("Обновление категорий продукта ID %s", product_id)
        try:
            # Удаляем старые связи
            await session.execute(
                delete(product_categories).where(
                    product_categories.c.product_id == product_id,
                ),
            )

            # Добавляем новые связи
            if category_ids:
                await session.execute(
                    insert(product_categories).values([
                        {"product_id": product_id, "category_id": cat_id}
                        for cat_id in category_ids
                    ]),
                )

            await session.commit()
            log.info("Категории продукта %s успешно обновлены", product_id)
        except Exception as e:
            log.exception("Ошибка при обновлении категорий продукта %s: %s", product_id, e)
            await session.rollback()
            raise e
