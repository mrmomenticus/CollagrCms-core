import logging

from sqlalchemy import select
from src.database.schema.images import ImagesDb
from src.database.connection import db
from sqlalchemy.orm import joinedload


class ImagesRepository:
    @staticmethod
    @db.with_session
    async def add(session, product_id: int, path: str) -> ImagesDb:
        image = ImagesDb()
        image.path = path
        image.product_id = product_id
        try:
            session.add(image)
            await session.commit()
        except Exception as e:
            logging.error(e)
            await session.rollback()
            raise e
        return image

    @staticmethod
    @db.with_session
    async def get_all(session):
        try:
            result = await session.execute(select(ImagesDb))
            return result.scalars().all()
        except Exception as e:
            logging.error(e)
            raise e
        
    @staticmethod
    @db.with_session
    async def get_by_ids_with_products(session, list_id: list[int]):
        try:
            result = await session.execute(select(ImagesDb).options(joinedload(ImagesDb.product)).where(ImagesDb.id.in_(list_id)))
            return result.scalars().all()
        except Exception as e:
            logging.error(e)
            raise e
        