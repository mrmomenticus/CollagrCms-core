import logging

from sqlalchemy import select
from src.database.schema.images import ImagesDb
from src.models.models import Image
from src.database.connection import db


class ImagesRepository:

    @staticmethod
    @db.with_session
    async def add(session, new_image: Image):
        image = ImagesDb()
        image.path = new_image.path
        try:
            session.add(image)
            await session.commit()
        except Exception as e:
            logging.error(e)
            await session.rollback()
            raise e
        
    @staticmethod
    @db.with_session
    async def get_all_image(session):
        try:
            result = await session.execute(select(ImagesDb))
            return result.scalars().all()
        except Exception as e:
            logging.error(e)
            raise e