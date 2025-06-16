import os
from typing import Annotated, List
import uuid
from fastapi import FastAPI, File, Form, UploadFile, HTTPException

from src.database.queries.product import ProductQueries
from src.models.models import Product
from src.utils.file import create_path, create_uuid, created_file


api = FastAPI(title="CollagrCms", version="0.1.0")


@api.post("/createProduct/")
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    price: int = Form(...),
    image: UploadFile = File(...),  # noqa: B008
):
    if image.filename:
        uuid = await create_uuid(image.filename)
        path = await create_path(uuid)
        await created_file(image, path)
    else:
        raise HTTPException(status_code=400, detail="Invalid file name")
    product_data = Product(
        name=name,
        description=description,
        category=category,
        price=price,
        image_path=path,
    )

    product_db = ProductQueries()
    await product_db.add_product(product_data)

    return {"product": product_data, "uuid": uuid, "path": path}
