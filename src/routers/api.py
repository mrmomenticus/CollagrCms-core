import logging
from typing import List
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from src.database.repository.images import ImagesRepository
from src.database.repository.products import ProductRepository
from src.models.models import Image, Product
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
    product_model = Product(
        name=name, description=description, category=category, price=price
    )
    try:
        product_db = await ProductRepository.add(product_model)
        image_db = await ImagesRepository.add(product_db.id, path)
        return {"product": product_model, "image": image_db}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error creating product") from e


@api.get("/getProducts/")
async def get_products():
    try:
        products_db = await ProductRepository.get_all()
        return {"products": products_db}
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="Error getting products") from e


@api.get("/getImages/")
async def get_images():
    try:
        images_db = await ImagesRepository.get_all()
        return {"images": images_db}
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="Error getting images") from e


@api.post("/createCollage/")
async def create_collage(images_list: list[Image]):
    list_id = [image.id for image in images_list]
    images_db = await ImagesRepository.get_all_with_id(list_id)
    product_db = await ProductRepository.get_all_with_images(images_db)
    return {"products": product_db}