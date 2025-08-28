import logging
from sqlalchemy import select
from src.database.schema.categories import CategoryDb
from src.database.connection import db
from sqlalchemy.exc import NoResultFound


class CategoryRepository:
    @staticmethod
    @db.with_session
    async def add(session, name: str, description: str | None = None) -> CategoryDb:
        """
        Добавляет новую категорию в базу данных

        Args:
            session: Сессия базы данных
            name: Название категории
            description: Описание категории

        Returns:
            Созданная категория

        Raises:
            Exception: При ошибке создания категории
        """
        logging.info(f"Добавление категории в БД: {name}")
        category = CategoryDb()
        category.name = name
        category.description = description if description is not None else ""
        category.is_active = True
        try:
            session.add(category)
            await session.commit()
            logging.info(
                f"Категория успешно добавлена в БД: {name} (ID: {category.id})"
            )
        except Exception as e:
            logging.error(f"Ошибка при добавлении категории в БД: {e}")
            await session.rollback()
            raise e
        return category

    @staticmethod
    @db.with_session
    async def get_all(session) -> list[CategoryDb]:
        """
        Получает все активные категории из базы данных

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
                select(CategoryDb).where(CategoryDb.is_active)
            )
            categories = result.scalars().all()
            logging.info(f"Получено активных категорий из БД: {len(categories)}")
            return categories
        except Exception as e:
            logging.error(f"Ошибка при получении активных категорий из БД: {e}")
            raise e

    @staticmethod
    @db.with_session
    async def get_all_including_inactive(session) -> list[CategoryDb]:
        """
        Получает все категории из базы данных (включая неактивные)

        Args:
            session: Сессия базы данных

        Returns:
            Список всех категорий

        Raises:
            Exception: При ошибке получения категорий
        """
        logging.info("Получение всех категорий из БД (включая неактивные)")
        try:
            result = await session.execute(select(CategoryDb))
            categories = result.scalars().all()
            logging.info(f"Получено всех категорий из БД: {len(categories)}")
            return categories
        except Exception as e:
            logging.error(f"Ошибка при получении всех категорий из БД: {e}")
            raise e

    @staticmethod
    @db.with_session
    async def get_by_id(session, category_id: int) -> CategoryDb | None:
        """
        Получает категорию по ID из базы данных

        Args:
            session: Сессия базы данных
            category_id: ID категории

        Returns:
            Категория или None если не найдена

        Raises:
            Exception: При ошибке получения категории
        """
        logging.info(f"Получение категории из БД по ID: {category_id}")
        try:
            result = await session.execute(
                select(CategoryDb).where(CategoryDb.id == category_id)
            )
            category = result.scalars().first()
            if category:
                logging.info(f"Категория найдена в БД: {category.name}")
            else:
                logging.info(f"Категория с ID {category_id} не найдена в БД")
            return category
        except Exception as e:
            logging.error(
                f"Ошибка при получении категории из БД по ID {category_id}: {e}"
            )
            raise e

    @staticmethod
    @db.with_session
    async def get_by_name(session, name: str) -> CategoryDb | None:
        """
        Получает категорию по названию из базы данных

        Args:
            session: Сессия базы данных
            name: Название категории

        Returns:
            Категория или None если не найдена

        Raises:
            Exception: При ошибке получения категории
        """
        logging.info(f"Получение категории из БД по названию: {name}")
        try:
            result = await session.execute(
                select(CategoryDb).where(CategoryDb.name == name, CategoryDb.is_active)
            )
            category = result.scalars().first()
            if category:
                logging.info(f"Категория найдена в БД: {name}")
            else:
                logging.info(f"Категория '{name}' не найдена в БД")
            return category
        except Exception as e:
            logging.error(
                f"Ошибка при получении категории из БД по названию '{name}': {e}"
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
        """
        Обновляет категорию в базе данных

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
        logging.info(f"Обновление категории в БД: ID {category_id}")
        try:
            result = await session.execute(
                select(CategoryDb).where(CategoryDb.id == category_id)
            )
            category = result.scalars().first()
            if not category:
                logging.warning(
                    f"Категория с ID {category_id} не найдена в БД для обновления"
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
            logging.error(f"Ошибка при обновлении категории в БД: {e}")
            await session.rollback()
            raise

    @staticmethod
    @db.with_session
    async def delete(session, category_id: int):
        """
        Мягко удаляет категорию (деактивирует) в базе данных

        Args:
            session: Сессия базы данных
            category_id: ID категории

        Raises:
            CategoryNotFoundError: Если категория не найдена
            Exception: При ошибке удаления категории
        """
        logging.info(f"Мягкое удаление категории в БД: ID {category_id}")
        try:
            result = await session.execute(
                select(CategoryDb).where(CategoryDb.id == category_id)
            )
            category = result.scalars().first()
            if not category:
                logging.warning(
                    f"Категория с ID {category_id} не найдена в БД для удаления"
                )
                raise NoResultFound(f"Category with ID {category_id} not found")

            # Мягкое удаление - просто деактивируем
            category.is_active = False
            await session.commit()
            logging.info(f"Категория успешно деактивирована в БД: {category.name}")
        except NoResultFound:
            raise
        except Exception as e:
            logging.error(f"Ошибка при деактивации категории в БД: {e}")
            await session.rollback()
            raise

    @staticmethod
    @db.with_session
    async def hard_delete(session, category_id: int):
        """
        Полностью удаляет категорию из базы данных

        Args:
            session: Сессия базы данных
            category_id: ID категории

        Raises:
            CategoryNotFoundError: Если категория не найдена
            Exception: При ошибке удаления категории
        """
        logging.info(f"Полное удаление категории из БД: ID {category_id}")
        try:
            result = await session.execute(
                select(CategoryDb).where(CategoryDb.id == category_id)
            )
            category = result.scalars().first()
            if not category:
                logging.warning(
                    f"Категория с ID {category_id} не найдена в БД для полного удаления"
                )
                raise NoResultFound(f"Category with ID {category_id} not found")

            category_name = category.name
            await session.delete(category)
            await session.commit()
            logging.info(f"Категория полностью удалена из БД: {category_name}")
        except NoResultFound:
            raise
        except Exception as e:
            logging.error(f"Ошибка при полном удалении категории из БД: {e}")
            await session.rollback()
            raise
