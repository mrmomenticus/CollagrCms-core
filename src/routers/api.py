import logging
from typing import List
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, status, Query, Request
from fastapi.responses import FileResponse
from src.core.collage_creator import CollageCreator
from src.database.repository.images import ImagesRepository
from src.database.repository.products import ProductRepository
from src.database.schema.images import ImagesDb
from src.models.models import ImageWithProduct, Product
from src.utils.file import create_path, create_uuid, created_file


api = FastAPI(title="CollagrCms", version="0.1.0")


async def handle_file_upload(image: UploadFile) -> str:
    if not image.filename:
        raise HTTPException(status_code=400, detail="Invalid file name")
    uuid = await create_uuid(image.filename)
    path = await create_path(uuid)
    await created_file(image, path)
    return path


@api.post("/products/", status_code=status.HTTP_201_CREATED)
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    price: int = Form(...),
    image: UploadFile = File(...),  # noqa: B008
):
    path = await handle_file_upload(image)
    product_model = Product(
        id=0, name=name, description=description, category=category, price=price
    )
    try:
        product_db = await ProductRepository.add(product_model)
        image_db = await ImagesRepository.add(product_db.id, path)
        return {"product": product_model, "image": image_db}
    except Exception as e:
        logging.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail="Error creating product")  # noqa: B904


@api.get("/products/", response_model=List[ImageWithProduct])
async def get_products(request: Request):
    try:
        image_db = await ImagesRepository.get_all_with_products()
        base_url = str(request.base_url).rstrip("/")
        result = []
        for img in image_db:
            model = ImageWithProduct.model_validate(img)
            model.path = f"{base_url}/media/{img.id}"
            result.append(model)
        return result
    except Exception as e:
        logging.error(f"Error getting products: {e}")
        raise HTTPException(status_code=500, detail="Error getting products")  # noqa: B904


@api.get("/collage/")
async def create_collage(list_id: List[int] = Query(..., min_length=9, max_length=9)):  # noqa: B008
    if len(list_id) != 9:  # TODO: Заменить из конфига
        raise HTTPException(status_code=422, detail="Invalid count of images")
    try:
        images_db: List[ImagesDb] = await ImagesRepository.get_by_ids_with_products(list_id)
        image_models: List[ImageWithProduct] = [ImageWithProduct.model_validate(img) for img in images_db]
        collag = CollageCreator().create(image_models, "collage.jpg")
        return FileResponse(collag, media_type="image/jpeg", filename="collage.jpg")
    except Exception as e:
        logging.error(f"Error creating collage: {e}")
        raise HTTPException(status_code=500, detail="Error creating collage")  # noqa: B904


@api.get("/media/{image_id}")
async def get_image(image_id: int):
    image = await ImagesRepository.get_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image.path, media_type="image/jpeg")