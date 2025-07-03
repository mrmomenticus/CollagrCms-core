import logging
from fastapi import (
    FastAPI,
    File,
    Form,
    UploadFile,
    HTTPException,
    status,
    Query,
    Request,
    Body,
)
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from src.core.collage_creator import CollageCreator
from src.database.repository.images import ImagesRepository
from src.database.repository.products import ProductRepository
from src.database.schema.images import ImagesDb
from src.models.models import ImageWithProduct, Product
from src.utils.file import create_path, create_uuid, created_file, delete_file


api = FastAPI(title="CollagrCms", version="0.1.0")


async def handle_file_upload(image: UploadFile, tag: str) -> str:
    if not image.filename:
        raise HTTPException(status_code=400, detail="Invalid file name")
    uuid = await create_uuid(image.filename)
    path = await create_path(uuid, tag)
    await created_file(image, path, tag)
    return path


@api.post("/products/", status_code=status.HTTP_201_CREATED)
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    price: int = Form(...),
    image: UploadFile = File(...),  # noqa: B008
):
    path = await handle_file_upload(image, category)
    product_model = Product(
        id=0, name=name, description=description, category=category, price=price
    )
    try:
        product_db = await ProductRepository.add(product_model)
        image_db = await ImagesRepository.add(product_db.id, path)
        return {"image": image_db}
    except Exception as e:
        logging.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail="Error creating product")  # noqa: B904


@api.get("/products/", response_model=list[ImageWithProduct])
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
async def create_collage(list_id: list[int] = Query(..., min_length=1, max_length=12)):  # noqa: B008
    """
    Создает коллаж из выбранных изображений.

    Args:
        list_id: Список ID изображений (от 1 до 9)

    Returns:
        Файл коллажа в формате JPEG
    """
    if len(list_id) < 1 or len(list_id) > 9:
        raise HTTPException(
            status_code=422,
            detail=f"Количество изображений должно быть от 1 до 12, получено: {len(list_id)}",
        )
    try:
        if list_id is not None:
            images_db: list[ImagesDb] = await ImagesRepository.get_by_ids_with_products(
                list_id_images=list_id
            )  # type: ignore

        # Проверяем, что все изображения найдены
        if len(images_db) != len(list_id):
            found_ids = [img.id for img in images_db]
            missing_ids = [img_id for img_id in list_id if img_id not in found_ids]
            raise HTTPException(
                status_code=404, detail=f"Изображения с ID {missing_ids} не найдены"
            )

        image_models: list[ImageWithProduct] = [
            ImageWithProduct.model_validate(img) for img in images_db
        ]
        collag = CollageCreator().create(image_models, "collage.jpg")
        return FileResponse(collag, media_type="image/jpeg", filename="collage.jpg")
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating collage: {e}")
        raise HTTPException(status_code=500, detail="Error creating collage")  # noqa: B904


@api.get("/media/{image_id}")
async def get_image(image_id: int):
    image = await ImagesRepository.get_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image.path, media_type="image/jpeg")


@api.delete("/products/{product_id}")
async def delete_product(product_id: int):
    product = await ImagesRepository.get_by_ids_with_products(
        list_id_products=[product_id]
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await delete_file(product[0].path)
    await ProductRepository.delete(product_id)
    return {"message": "Product deleted"}


# --- Simple Auth Stub ---
HARDCODED_USERNAME = "admin"
HARDCODED_PASSWORD = "password123"
SESSION_TOKEN = "secret-token"
ALLOWED_PATHS = ["/login"]


class SimpleAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        allowed = request.url.path in ALLOWED_PATHS or request.url.path.startswith((
            "/docs",
            "/redoc",
            "/openapi",
        ))
        if allowed:
            return await call_next(request)
        auth = request.headers.get("Authorization")
        if (
            not auth
            or not auth.startswith("Bearer ")
            or auth.split(" ", 1)[1] != SESSION_TOKEN
        ):
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        return await call_next(request)


api.add_middleware(SimpleAuthMiddleware)
# --- End Simple Auth Stub ---


@api.post("/login")
async def login(username: str = Body(...), password: str = Body(...)):
    if username == HARDCODED_USERNAME and password == HARDCODED_PASSWORD:
        return {"token": SESSION_TOKEN}
    return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})
