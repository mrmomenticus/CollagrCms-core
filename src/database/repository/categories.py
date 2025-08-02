import logging
from sqlalchemy import select
from src.database.schema.categories import CategoryDb
from src.database.connection import db


class CategoryRepository:
    @staticmethod
    @db.with_session
    async def add(session, name: str, description: str = None) -> CategoryDb:
        category = CategoryDb()
        category.name = name
        category.description = description
        category.is_active = True
        try:
            session.add(category)
            await session.commit()
        except Exception as e:
            logging.error(e)
            await session.rollback()
            raise e
        return category

    @staticmethod
    @db.with_session
    async def get_all(session) -> list[CategoryDb]:
        try:
            result = await session.execute(select(CategoryDb).where(CategoryDb.is_active == True))
            return result.scalars().all()
        except Exception as e:
            logging.error(e)
            raise e

    @staticmethod
    @db.with_session
    async def get_all_including_inactive(session) -> list[CategoryDb]:
        try:
            result = await session.execute(select(CategoryDb))
            return result.scalars().all()
        except Exception as e:
            logging.error(e)
            raise e

    @staticmethod
    @db.with_session
    async def get_by_id(session, category_id: int) -> CategoryDb:
        try:
            result = await session.execute(
                select(CategoryDb).where(CategoryDb.id == category_id)
            )
            return result.scalars().first()
        except Exception as e:
            logging.error(e)
            raise e

    @staticmethod
    @db.with_session
    async def get_by_name(session, name: str) -> CategoryDb:
        try:
            result = await session.execute(
                select(CategoryDb).where(CategoryDb.name == name, CategoryDb.is_active == True)
            )
            return result.scalars().first()
        except Exception as e:
            logging.error(e)
            raise e

    @staticmethod
    @db.with_session
    async def update(session, category_id: int, name: str = None, description: str = None, is_active: bool = None):
        try:
            result = await session.execute(select(CategoryDb).where(CategoryDb.id == category_id))
            category = result.scalars().first()
            if category:
                if name is not None:
                    category.name = name
                if description is not None:
                    category.description = description
                if is_active is not None:
                    category.is_active = is_active
                await session.commit()
        except Exception as e:
            logging.error(e)
            await session.rollback()
            raise

    @staticmethod
    @db.with_session
    async def delete(session, category_id: int):
        try:
            result = await session.execute(select(CategoryDb).where(CategoryDb.id == category_id))
            category = result.scalars().first()
            if category:
                # Мягкое удаление - просто деактивируем
                category.is_active = False
                await session.commit()
        except Exception as e:
            logging.error(e)
            await session.rollback()
            raise

    @staticmethod
    @db.with_session
    async def hard_delete(session, category_id: int):
        try:
            result = await session.execute(select(CategoryDb).where(CategoryDb.id == category_id))
            category = result.scalars().first()
            if category:
                await session.delete(category)
                await session.commit()
        except Exception as e:
            logging.error(e)
            await session.rollback()
            raise 