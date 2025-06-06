from fastapi import APIRouter, HTTPException
from src.database.queries.product_queries import ProductQueries
from src.database.queries.image_queries import ImageQueries
from src.models.models import Product

router = APIRouter()


@router.post("/product")
async def add_product(product: Product):
    pass
