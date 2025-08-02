import logging

from sqlalchemy import select
from src.database.schema.images import ImagesDb
from src.database.schema.products import ProductDb
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
    async def get_by_ids_with_products(
        session,
        list_id_images: list[int] | None = None,
        list_id_products: list[int] | None = None,
    ) -> list[ImagesDb] | None:
        try:
            if list_id_products:
                result = await session.execute(
                    select(ImagesDb)
                    .options(joinedload(ImagesDb.product).joinedload(ProductDb.category))
                    .where(ImagesDb.product_id.in_(list_id_products))
                )
                return result.scalars().all()
            if list_id_images:
                result = await session.execute(
                    select(ImagesDb)
                    .options(joinedload(ImagesDb.product).joinedload(ProductDb.category))
                    .where(ImagesDb.id.in_(list_id_images))
                )
                return result.scalars().all()
            # Если не переданы ID, возвращаем None
            return None
        except Exception as e:
            logging.error(e)
            raise e

    @staticmethod
    @db.with_session
    async def get_all_with_products(session) -> list[ImagesDb]:
        try:
            result = await session.execute(
                select(ImagesDb).options(
                    joinedload(ImagesDb.product).joinedload(ProductDb.category)
                )
            )
            return result.scalars().all()
        except Exception as e:
            logging.error(f"Error in get_all_with_products: {e}")
            raise

    @staticmethod
    @db.with_session
    async def get_by_id(session, image_id: int) -> ImagesDb:
        try:
            result = await session.execute(
                select(ImagesDb)
                .options(joinedload(ImagesDb.product).joinedload(ProductDb.category))
                .where(ImagesDb.id == image_id)
            )
            return result.scalars().first()
        except Exception as e:
            logging.error(e)
            raise
        
    @staticmethod
    @db.with_session
    async def update(session, image_id: int, path: str):
        try:
            result = await session.execute(select(ImagesDb).where(ImagesDb.id == image_id))
            image = result.scalars().first()
            image.path = path
            await session.commit()
        except Exception as e:
            logging.error(e)
            await session.rollback()
            raise
