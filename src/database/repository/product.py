from src.database.schema.product import ProductDb
from src.database.connection import db
from src.models.models import Product


class ProductRepository:
    @staticmethod
    @db.with_session
    async def create(session, new_product: Product):
        product = ProductDb()
        product.name = new_product.name
        product.description = new_product.description
        product.category = new_product.category
        product.price = new_product.price
        product.image_path = new_product.image_path
        try:
            session.add(product)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
