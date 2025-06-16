from typing import List, Optional
from src.database.connection import db
from src.database.queries.base import BaseQueries
from src.models.models import Product


class ProductQueries(BaseQueries):
    async def add_product(self, product: Product):
        query = "INSERT INTO products (name, description, category, price, image_path) VALUES ($1, $2, $3, $4, $5)"
        try:
            await self.execute_query(
                query,
                product.name,
                product.description,
                product.category,
                product.price,
                product.image_path,
            )
        except Exception as e:
            raise e
