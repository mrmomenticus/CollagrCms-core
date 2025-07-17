import logging
from src.database.schema.images import ImagesDb
from src.database.schema.products import ProductDb
from src.database.connection import db
from src.models.models import Product
from sqlalchemy import select
from sqlalchemy.orm import joinedload


class ProductRepository:
    @staticmethod
    @db.with_session
    async def add(session, new_product: Product) -> ProductDb:
        product = ProductDb()
        product.name = new_product.name
        product.description = new_product.description
        product.category = new_product.category
        product.price = new_product.price
        try:
            session.add(product)
            await session.commit()
        except Exception as e:
            logging.error(e)
            await session.rollback()
            raise e
        return product

    @staticmethod
    @db.with_session
    async def get_all(session):
        try:
            result = await session.execute(select(ProductDb))
            return result.scalars().all()
        except Exception as e:
            logging.error(e)
            raise e
    
    @staticmethod
    @db.with_session
    async def delete(session, product_id: int):
        try:
            result = await session.execute(select(ProductDb).where(ProductDb.id == product_id))
            product = result.scalars().first()
            await session.delete(product)
            await session.commit()
        except Exception as e:
            logging.error(e)
            await session.rollback()
            raise e

    @staticmethod
    @db.with_session
    async def update(session, new_product: Product):
        try:
            result = await session.execute(select(ProductDb).where(ProductDb.id == new_product.id))
            product = result.scalars().first()
            product.name = new_product.name
            product.description = new_product.description
            product.category = new_product.category
            product.price = new_product.price
            await session.commit()
        except Exception as e:
            logging.error(e)
            await session.rollback()
            raise e

