import logging

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from src.database.connection import db
from src.database.schema.categories import CategoryDb


class CategoryRepository:
    @staticmethod
    @db.with_session
    async def add(session, name: str, description: str | None = None) -> CategoryDb:
        """Добавляет новую категорию в базу данных.

        Args:
            session: Сессия базы данных
            name: Название категории
            description: Описание категории

        Returns:
            Созданная категория

        Raises:
            Exception: При ошибке создания категории

        """
        logging.info("Добавление категории в БД: %s", name)
        category = CategoryDb()
        category.name = name
        category.description = description if description is not None else ""
        category.is_active = True
        try:
            session.add(category)
            await session.commit()
            logging.info(
                f"Категория успешно добавлена в БД: {name} (ID: {category.id})",
            )
        except Exception as e:
            logging.exception("Ошибка при добавлении категории в БД: %s", e)
            await session.rollback()
            raise e
        return category

    @staticmethod
    @db.with_session
    async def get_all(session) -> list[CategoryDb]:
        """Получает все активные категории из базы данных

        Args:
            session: Сессия базы данных

        Returns:
            Список активных категорий

        Raises:
            Exception: При ошибке получения категорий

        """
        logging.info("Получение всех активных категорий из БД")
        try:
            result = await session.execute(
                select(CategoryDb).where(CategoryDb.is_active).order_by(CategoryDb.name),
            )
            categories = result.scalars().all()
            logging.info(f"Получено активных категорий из БД: {len(categories)}")
            return categories
        except Exception as e:
            logging.exception("Ошибка при получении активных категорий из БД: %s", e)
            raise e

    @staticmethod
    @db.with_session
    async def get_all_including_inactive(session) -> list[CategoryDb]:
        """Получает все категории из базы данных (включая неактивные)

        Args:
            session: Сессия базы данных

        Returns:
            Список всех категорий

        Raises:
            Exception: При ошибке получения категорий

        """
        logging.info("Получение всех категорий из БД (включая неактивные)")
        try:
            result = await session.execute(select(CategoryDb).order_by(CategoryDb.name))
            categories = result.scalars().all()
            logging.info(f"Получено всех категорий из БД: {len(categories)}")
            return categories
        except Exception as e:
            logging.exception("Ошибка при получении всех категорий из БД: %s", e)
            raise e

    @staticmethod
    @db.with_session
    async def get_by_id(session, category_id: int) -> CategoryDb | None:
        """Получает категорию по ID из базы данных

        Args:
            session: Сессия базы данных
            category_id: ID категории

        Returns:
            Категория или None если не найдена

        Raises:
            Exception: При ошибке получения категории

        """
        logging.info("Получение категории из БД по ID: %s", category_id)
        try:
            result = await session.execute(
                select(CategoryDb)
                .where(CategoryDb.id == category_id)
                .order_by(CategoryDb.name),
            )
            category = result.scalars().first()
            if category:
                logging.info(f"Категория найдена в БД: {category.name}")
            else:
                logging.info("Категория с ID %s не найдена в БД", category_id)
            return category
        except Exception as e:
            logging.exception(
                "Ошибка при получении категории из БД по ID %s: %s", category_id, e,
            )
            raise e

    @staticmethod
    @db.with_session
    async def get_by_name(session, name: str) -> CategoryDb | None:
        """Получает категорию по названию из базы данных

        Args:
            session: Сессия базы данных
            name: Название категории

        Returns:
            Категория или None если не найдена

        Raises:
            Exception: При ошибке получения категории

        """
        logging.info("Получение категории из БД по названию: %s", name)
        try:
            result = await session.execute(
                select(CategoryDb)
                .where(CategoryDb.name == name, CategoryDb.is_active)
                .order_by(CategoryDb.name),
            )
            category = result.scalars().first()
            if category:
                logging.info("Категория найдена в БД: %s", name)
            else:
                logging.info("Категория '%s' не найдена в БД", name)
            return category
        except Exception as e:
            logging.exception(
                "Ошибка при получении категории из БД по названию '%s': %s", name, e,
            )
            raise e

    @staticmethod
    @db.with_session
    async def update(
        session,
        category_id: int,
        name: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
    ):
        """Обновляет категорию в базе данных

        Args:
            session: Сессия базы данных
            category_id: ID категории
            name: Новое название категории
            description: Новое описание категории
            is_active: Новый статус активности

        Raises:
            CategoryNotFoundError: Если категория не найдена
            Exception: При ошибке обновления категории

        """
        logging.info("Обновление категории в БД: ID %s", category_id)
        try:
            result = await session.execute(
                select(CategoryDb).where(CategoryDb.id == category_id),
            )
            category = result.scalars().first()
            if not category:
                logging.warning(
                    "Категория с ID %s не найдена в БД для обновления", category_id,
                )
                raise NoResultFound(f"Category with ID {category_id} not found")

            if name is not None:
                category.name = name
            if description is not None:
                category.description = description
            if is_active is not None:
                category.is_active = is_active
            await session.commit()
            logging.info(f"Категория успешно обновлена в БД: {category.name}")
        except NoResultFound:
            raise
        except Exception as e:
            logging.exception("Ошибка при обновлении категории в БД: %s", e)
            await session.rollback()
            raise

    @staticmethod
    @db.with_session
    async def delete(session, category_id: int):
        """Мягко удаляет категорию (деактивирует) в базе данных

        Args:
            session: Сессия базы данных
            category_id: ID категории

        Raises:
            CategoryNotFoundError: Если категория не найдена
            Exception: При ошибке удаления категории

        """
        logging.info("Мягкое удаление категории в БД: ID %s", category_id)
        try:
            result = await session.execute(
                select(CategoryDb).where(CategoryDb.id == category_id),
            )
            category = result.scalars().first()
            if not category:
                logging.warning(
                    "Категория с ID %s не найдена в БД для удаления", category_id,
                )
                raise NoResultFound(f"Category with ID {category_id} not found")

            # Мягкое удаление - просто деактивируем
            category.is_active = False
            await session.commit()
            logging.info(f"Категория успешно деактивирована в БД: {category.name}")
        except NoResultFound:
            raise
        except Exception as e:
            logging.exception("Ошибка при деактивации категории в БД: %s", e)
            await session.rollback()
            raise

    @staticmethod
    @db.with_session
    async def hard_delete(session, category_id: int):
        """Полностью удаляет категорию из базы данных

        Args:
            session: Сессия базы данных
            category_id: ID категории

        Raises:
            CategoryNotFoundError: Если категория не найдена
            Exception: При ошибке удаления категории

        """
        logging.info("Полное удаление категории из БД: ID %s", category_id)
        try:
            result = await session.execute(
                select(CategoryDb).where(CategoryDb.id == category_id),
            )
            category = result.scalars().first()
            if not category:
                logging.warning(
                    "Категория с ID %s не найдена в БД для полного удаления", category_id,
                )
                raise NoResultFound(f"Category with ID {category_id} not found")

            category_name = category.name
            await session.delete(category)
            await session.commit()
            logging.info("Категория полностью удалена из БД: %s", category_name)
        except NoResultFound:
            raise
        except Exception as e:
            logging.exception("Ошибка при полном удалении категории из БД: %s", e)
            await session.rollback()
            raise
