import logging
from typing import List
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from src.database.repository.images import ImagesRepository
from src.database.repository.products import ProductRepository
from src.models.models import Image, ImagesList, Product
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
        id=0,
        name=name,
        description=description,
        category=category,
        price=price,
        image_path=Image(id=0, path=path),
    )
    try:
        await ProductRepository.add(product_data)
        return {"product": product_data, "uuid": uuid, "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error creating product") from e


@api.get("/getProducts/")
async def get_products():
    try:
        products = await ProductRepository.get_all()
        product_models: List[Product] = [
            Product(
                id=product.id,
                name=product.name,
                description=product.description,
                category=product.category,
                price=product.price,
                image_path=Image(id=product.image.id, path=product.image.path),
            )
            for product in products
        ]

        return {"products": product_models}
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="Error getting products") from e


@api.get("/getImages/")
async def get_images():
    try:
        image = await ImagesRepository.get_all_image()
        return {"images": image}
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="Error getting images") from e
    
# @api.post("/createCollage/")
# async def create_collage(images_list: ImagesList):
    
    