import logging
from src.database.schema.products import ProductDb
from src.database.connection import db
from src.database.schema.images import ImagesDb
from src.models.models import Product
from sqlalchemy import select


class ProductRepository:
    @staticmethod
    @db.with_session
    async def add(session, new_product: Product):
        product = ProductDb()
        product.name = new_product.name
        product.description = new_product.description
        product.category = new_product.category
        product.price = new_product.price
        product.image = ImagesDb(path=new_product.image_path.path)
        try:
            session.add(product)
            await session.commit()
        except Exception as e:
            logging.error(e)
            await session.rollback()
            raise e

    @staticmethod
    @db.with_session
    async def get_all(session):
        try:
            result = await session.execute(select(ProductDb))
            return result.scalars().all()
        except Exception as e:
            logging.error(e)
            raise e
