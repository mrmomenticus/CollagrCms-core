from fastapi import APIRouter, HTTPException
from src.database.queries.product import ProductQueries
from src.database.queries.image import ImageQueries
from src.models.models import Product

router = APIRouter()


@router.post("/product")
async def add_product(product: Product):
    pass
