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
import os
import uuid
import tempfile
import shutil

api = FastAPI(title="CollagrCms", version="0.1.0")

# Добавляем поддержку CORS
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def handle_file_upload(image: UploadFile, tag: str) -> str:
    if not image.filename:
        raise HTTPException(status_code=400, detail="Invalid file name")
    uuid = await create_uuid(image.filename)
    path = await create_path(uuid, tag)
    await created_file(image, path, tag)
    return path


@api.post("/products/", status_code=status.HTTP_201_CREATED)
async def post_product(
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
        logging.warning(f"Error creating product: {e}")
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
        logging.warning(f"Error getting products: {e}")
        raise HTTPException(status_code=500, detail="Error getting products")  # noqa: B904


@api.get("/collage/")
async def create_collage(list_id: list[int] = Query(..., min_length=1, max_length=12)):  # noqa: B008
    """
    Создает коллаж из выбранных изображений.

    Args:
        list_id: Список ID изображений (от 1 до 12)

    Returns:
        Файл коллажа в формате JPEG
    """
    if len(list_id) < 1 or len(list_id) > 12:
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


@api.get("/collage/select-all/")
async def select_all_products():
    """
    Возвращает все доступные товары для создания коллажей.
    
    Returns:
        JSON с информацией о всех товарах и возможностях создания коллажей
    """
    try:
        # Получаем все изображения с товарами
        all_images_db: list[ImagesDb] = await ImagesRepository.get_all_with_products()
        
        if not all_images_db:
            return {
                "total_images": 0,
                "total_batches": 0,
                "batch_size": 12,
                "has_images": False,
                "message": "Товары не найдены"
            }
        
        total_images = len(all_images_db)
        batch_size = 12
        total_batches = (total_images + batch_size - 1) // batch_size
        
        # Формируем информацию о товарах
        products_info = []
        for img in all_images_db:
            products_info.append({
                "id": img.id,
                "product_id": img.product_id,
                "name": img.product.name,
                "description": img.product.description,
                "category": img.product.category,
                "price": img.product.price,
                "path": img.path
            })
        
        return {
            "total_images": total_images,
            "total_batches": total_batches,
            "batch_size": batch_size,
            "has_images": True,
            "products": products_info,
            "message": f"Found {total_images} products. Can create {total_batches} collages with {batch_size} items each."
        }
        
    except Exception as e:
        logging.error(f"Error getting all products: {e}")
        raise HTTPException(status_code=500, detail="Error getting all products")


@api.get("/collage/batch/")
async def create_batch_collage(
    batch_size: int = Query(default=12, ge=1, le=12),
    start_index: int = Query(default=0, ge=0)
):
    """
    Создает коллаж из текущего пакета товаров (по умолчанию 12 штук).
    Используется для кнопки "Дальше" - создает следующий коллаж и сразу отправляет его пользователю.
    
    Args:
        batch_size: Размер пакета (по умолчанию 12)
        start_index: Начальный индекс для обработки
        
    Returns:
        Файл коллажа для скачивания
    """
    try:
        # Получаем все изображения с товарами
        all_images_db: list[ImagesDb] = await ImagesRepository.get_all_with_products()
        
        if not all_images_db:
            raise HTTPException(status_code=404, detail="Products not found")
        
        # Создаем временную папку для коллажей
        import tempfile
        import shutil
        
        temp_collages_dir = tempfile.mkdtemp(prefix="collages_")
        
        total_images = len(all_images_db)
        total_batches = (total_images + batch_size - 1) // batch_size
        
        # Проверяем, не выходит ли start_index за пределы
        if start_index >= total_images:
            raise HTTPException(
                status_code=400, 
                detail=f"Start index {start_index} exceeds total number of products ({total_images})"
            )
        
        # Обрабатываем текущий пакет
        end_index = min(start_index + batch_size, total_images)
        current_batch = all_images_db[start_index:end_index]
        
        # Создаем коллаж для текущего пакета
        image_models: list[ImageWithProduct] = [
            ImageWithProduct.model_validate(img) for img in current_batch
        ]
        
        # Генерируем уникальное имя файла
        batch_number = start_index // batch_size + 1
        collage_filename = f"collage_batch_{batch_number}_{uuid.uuid4().hex[:8]}.jpg"
        collage_path = os.path.join(temp_collages_dir, collage_filename)
        
        collag = CollageCreator().create(image_models, collage_path)
        
        # Создаем временный файл для отправки
        import tempfile
        import shutil
        
        # Создаем временную копию файла
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            shutil.copy2(collage_path, tmp_file.name)
            tmp_path = tmp_file.name
        
        # Оставляем файл для скачивания (будет очищен позже через /collage/cleanup/)
        logging.info(f"Created collage: {collage_path}")
        
        # Отправляем файл пользователю для скачивания
        return FileResponse(
            tmp_path, 
            media_type="image/jpeg", 
            filename=collage_filename,
            headers={
                "X-Collage-Batch": str(batch_number),
                "X-Collage-Total-Batches": str(total_batches),
                "X-Collage-Processed-Images": str(len(current_batch)),
                "X-Collage-Total-Images": str(total_images),
                "X-Collage-Start-Index": str(start_index),
                "X-Collage-End-Index": str(end_index),
                "X-Collage-Has-More": str(end_index < total_images),
                "X-Collage-Next-Start-Index": str(end_index if end_index < total_images else -1),
                "X-Collage-Message": f"Collage {batch_number} of {total_batches} (items {start_index + 1}-{end_index} of {total_images})"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating batch collage: {e}")
        raise HTTPException(status_code=500, detail="Error creating batch collage")


@api.get("/collage/batch/all/")
async def create_all_batch_collages(
    batch_size: int = Query(default=12, ge=1, le=12)
):
    """
    Создает все коллажи из всех товаров, обрабатывая их пакетами.
    Используется для кнопки "Выбрать все" - создает все коллажи сразу.
    
    Args:
        batch_size: Размер пакета (по умолчанию 12)
        
    Returns:
        JSON с информацией о всех созданных коллажах
    """
    try:
        # Получаем все изображения с товарами
        all_images_db: list[ImagesDb] = await ImagesRepository.get_all_with_products()
        
        if not all_images_db:
            raise HTTPException(status_code=404, detail="Products not found")
        
        # Создаем временную папку для коллажей
        import tempfile
        import shutil
        
        temp_collages_dir = tempfile.mkdtemp(prefix="collages_")
        
        total_images = len(all_images_db)
        total_batches = (total_images + batch_size - 1) // batch_size
        
        created_collages = []
        
        for batch_num in range(total_batches):
            start_index = batch_num * batch_size
            end_index = min(start_index + batch_size, total_images)
            current_batch = all_images_db[start_index:end_index]
            
            # Создаем коллаж для текущего пакета
            image_models: list[ImageWithProduct] = [
                ImageWithProduct.model_validate(img) for img in current_batch
            ]
            
            # Генерируем уникальное имя файла
            collage_filename = f"collage_batch_{batch_num + 1}_{uuid.uuid4().hex[:8]}.jpg"
            collage_path = os.path.join(temp_collages_dir, collage_filename)
            
            collag = CollageCreator().create(image_models, collage_path)
            
            # Формируем информацию о товарах в текущем пакете
            batch_products = []
            for img in current_batch:
                batch_products.append({
                    "id": img.id,
                    "product_id": img.product_id,
                    "name": img.product.name,
                    "description": img.product.description,
                    "category": img.product.category,
                    "price": img.product.price
                })
            
            created_collages.append({
                "batch_number": batch_num + 1,
                "processed_images": len(current_batch),
                "start_index": start_index,
                "end_index": end_index,
                "collage_path": collage_path,
                "collage_filename": collage_filename,
                "batch_products": batch_products,
                "message": f"Created collage {batch_num + 1} of {total_batches} (items {start_index + 1}-{end_index} of {total_images})"
            })
        
        # Удаляем временную папку с коллажами
        try:
            if os.path.exists(temp_collages_dir):
                shutil.rmtree(temp_collages_dir)
        except Exception as e:
            logging.warning(f"Could not delete temporary directory {temp_collages_dir}: {e}")
        
        return {
            "total_batches": total_batches,
            "total_images": total_images,
            "batch_size": batch_size,
            "created_collages": created_collages,
            "message": f"Created {total_batches} collages from {total_images} items"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating all batch collages: {e}")
        raise HTTPException(status_code=500, detail="Error creating all batch collages")


@api.get("/collage/batch/all/download/")
async def create_and_download_all_collages(
    batch_size: int = Query(default=12, ge=1, le=12)
):
    """
    Создает все коллажи из всех товаров и отправляет их пользователю в виде ZIP-архива.
    Используется для кнопки "Выбрать все" - создает все коллажи и сразу отправляет для скачивания.
    
    Args:
        batch_size: Размер пакета (по умолчанию 12)
        
    Returns:
        ZIP-архив со всеми созданными коллажами
    """
    try:
        import zipfile
        import tempfile
        
        # Получаем все изображения с товарами
        all_images_db: list[ImagesDb] = await ImagesRepository.get_all_with_products()
        
        if not all_images_db:
            raise HTTPException(status_code=404, detail="Товары не найдены")
        
        # Создаем временную папку для коллажей

        
        temp_collages_dir = tempfile.mkdtemp(prefix="collages_")
        
        total_images = len(all_images_db)
        total_batches = (total_images + batch_size - 1) // batch_size
        
        # Создаем временный ZIP-файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
            with zipfile.ZipFile(tmp_zip.name, 'w') as zip_file:
                
                for batch_num in range(total_batches):
                    start_index = batch_num * batch_size
                    end_index = min(start_index + batch_size, total_images)
                    current_batch = all_images_db[start_index:end_index]
                    
                    # Создаем коллаж для текущего пакета
                    image_models: list[ImageWithProduct] = [
                        ImageWithProduct.model_validate(img) for img in current_batch
                    ]
                    
                    # Генерируем уникальное имя файла
                    collage_filename = f"collage_batch_{batch_num + 1}_{uuid.uuid4().hex[:8]}.jpg"
                    collage_path = os.path.join(temp_collages_dir, collage_filename)
                    
                    collag = CollageCreator().create(image_models, collage_path)
                    
                    # Добавляем файл в ZIP-архив
                    zip_file.write(collage_path, collage_filename)
        
        # Отправляем ZIP-файл пользователю
        zip_filename = f"all_collages_{uuid.uuid4().hex[:8]}.zip"
        response = FileResponse(
            tmp_zip.name,
            media_type="application/zip",
            filename=zip_filename,
            headers={
                "X-Collage-Total-Batches": str(total_batches),
                "X-Collage-Total-Images": str(total_images),
                "X-Collage-Batch-Size": str(batch_size),
                "X-Collage-Message": f"Created {total_batches} collages from {total_images} items"
            }
        )
        
        # Удаляем временные файлы сразу после создания
        try:
            if os.path.exists(temp_collages_dir):
                shutil.rmtree(temp_collages_dir)
        except Exception as e:
            logging.warning(f"Could not delete temporary directory {temp_collages_dir}: {e}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating and downloading all collages: {e}")
        raise HTTPException(status_code=500, detail="Error creating and downloading all collages")


@api.get("/collage/batch/status/")
async def get_batch_status():
    """
    Возвращает статус пакетной обработки коллажей.
    
    Returns:
        JSON с информацией о статусе
    """
    try:
        # Получаем все изображения с товарами
        all_images_db: list[ImagesDb] = await ImagesRepository.get_all_with_products()
        
        if not all_images_db:
            return {
                "total_images": 0,
                "total_batches": 0,
                "batch_size": 12,
                "has_images": False,
                "message": "Товары не найдены"
            }
        
        total_images = len(all_images_db)
        batch_size = 12
        total_batches = (total_images + batch_size - 1) // batch_size
        
        return {
            "total_images": total_images,
            "total_batches": total_batches,
            "batch_size": batch_size,
            "has_images": True,
            "message": f"Found {total_images} products. Can create {total_batches} collages with {batch_size} items each."
        }
        
    except Exception as e:
        logging.error(f"Error getting batch status: {e}")
        raise HTTPException(status_code=500, detail="Error getting batch status")


@api.get("/collage/batch/info/")
async def get_batch_info(
    start_index: int = Query(default=0, ge=0),
    batch_size: int = Query(default=12, ge=1, le=12)
):
    """
    Возвращает информацию о текущем пакете товаров без создания коллажа.
    Используется для получения информации перед созданием коллажа.
    
    Args:
        start_index: Начальный индекс для обработки
        batch_size: Размер пакета (по умолчанию 12)
        
    Returns:
        JSON с информацией о текущем пакете
    """
    try:
        # Получаем все изображения с товарами
        all_images_db: list[ImagesDb] = await ImagesRepository.get_all_with_products()
        
        if not all_images_db:
            raise HTTPException(status_code=404, detail="Products not found")
        
        total_images = len(all_images_db)
        total_batches = (total_images + batch_size - 1) // batch_size
        
        # Проверяем, не выходит ли start_index за пределы
        if start_index >= total_images:
            raise HTTPException(
                status_code=400, 
                detail=f"Start index {start_index} exceeds total number of products ({total_images})"
            )
        
        # Обрабатываем текущий пакет
        end_index = min(start_index + batch_size, total_images)
        current_batch = all_images_db[start_index:end_index]
        
        # Формируем информацию о товарах в текущем пакете
        batch_products = []
        for img in current_batch:
            batch_products.append({
                "id": img.id,
                "product_id": img.product_id,
                "name": img.product.name,
                "description": img.product.description,
                "category": img.product.category,
                "price": img.product.price
            })
        
        # Проверяем, есть ли ещё пакеты для обработки
        has_more = end_index < total_images
        next_start_index = end_index if has_more else None
        batch_number = start_index // batch_size + 1
        
        return {
            "current_batch": batch_number,
            "total_batches": total_batches,
            "processed_images": len(current_batch),
            "total_images": total_images,
            "start_index": start_index,
            "end_index": end_index,
            "has_more": has_more,
            "next_start_index": next_start_index,
            "batch_products": batch_products,
            "message": f"Batch {batch_number} of {total_batches} (items {start_index + 1}-{end_index} of {total_images})"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting batch info: {e}")
        raise HTTPException(status_code=500, detail="Error getting batch info")


@api.get("/collage/download/{filename}")
async def download_collage(filename: str):
    """
    Скачивает созданный коллаж по имени файла.
    
    Args:
        filename: Имя файла коллажа
        
    Returns:
        Файл коллажа
    """
    try:
        collage_path = os.path.join("collages", filename)
        if not os.path.exists(collage_path):
            raise HTTPException(status_code=404, detail="Collage not found")
        
        # Создаем временную копию файла
        import tempfile
        import shutil
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            shutil.copy2(collage_path, tmp_file.name)
            tmp_path = tmp_file.name
        
        # Оставляем файл для скачивания (будет очищен позже через /collage/cleanup/)
        logging.info(f"Downloading collage: {collage_path}")
        
        # Отправляем файл пользователю
        return FileResponse(tmp_path, media_type="image/jpeg", filename=filename)
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error downloading collage: {e}")
        raise HTTPException(status_code=500, detail="Error downloading collage")


@api.get("/collage/list/")
async def list_collages():
    """
    Возвращает список всех созданных коллажей.
    
    Returns:
        JSON со списком коллажей
    """
    try:
        collages_dir = "collages"
        if not os.path.exists(collages_dir):
            return {
                "collages": [],
                "total_collages": 0,
                "message": "No collages found"
            }
        
        collage_files = []
        for filename in os.listdir(collages_dir):
            if filename.endswith('.jpg'):
                file_path = os.path.join(collages_dir, filename)
                file_size = os.path.getsize(file_path)
                collage_files.append({
                    "filename": filename,
                    "size_bytes": file_size,
                    "size_mb": round(file_size / (1024 * 1024), 2)
                })
        
        # Сортируем по имени файла
        collage_files.sort(key=lambda x: x['filename'])
        
        return {
            "collages": collage_files,
            "total_collages": len(collage_files),
            "message": f"Found {len(collage_files)} collages"
        }
        
    except Exception as e:
        logging.error(f"Error listing collages: {e}")
        raise HTTPException(status_code=500, detail="Error listing collages")


@api.post("/collage/cleanup/")
async def cleanup_temp_files():
    """
    Очищает временные файлы коллажей.
    
    Returns:
        JSON с результатом очистки
    """
    try:
        import glob
        
        # Очищаем временные файлы в /tmp
        temp_patterns = [
            "/tmp/collages_*",
            "/tmp/tmp*",
            "/tmp/*.jpg",
            "/tmp/*.zip"
        ]
        
        cleaned_files = []
        cleaned_dirs = []
        
        for pattern in temp_patterns:
            try:
                # Удаляем файлы
                for file_path in glob.glob(pattern):
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        cleaned_files.append(file_path)
                
                # Удаляем папки
                for dir_path in glob.glob(pattern):
                    if os.path.isdir(dir_path):
                        shutil.rmtree(dir_path)
                        cleaned_dirs.append(dir_path)
            except Exception as e:
                logging.warning(f"Could not clean pattern {pattern}: {e}")
        
        return {
            "cleaned_files": cleaned_files,
            "cleaned_directories": cleaned_dirs,
            "total_cleaned": len(cleaned_files) + len(cleaned_dirs),
            "message": f"Cleaned {len(cleaned_files)} files and {len(cleaned_dirs)} directories"
        }
        
    except Exception as e:
        logging.error(f"Error cleaning temp files: {e}")
        raise HTTPException(status_code=500, detail="Error cleaning temp files")


@api.get("/media/{image_id}")
async def get_image(image_id: int):
    image = await ImagesRepository.get_by_id(image_id)
    if not image:
        logging.warning("Image not found")
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image.path, media_type="image/jpeg")


@api.delete("/products/{product_id}")
async def delete_product(product_id: int):
    product = await ImagesRepository.get_by_ids_with_products(
        list_id_products=[product_id]
    )
    if not product:
        logging.warning("Product not found")
        raise HTTPException(status_code=404, detail="Product not found")
    await delete_file(product[0].path)
    await ProductRepository.delete(product_id)
    return {"message": "Product deleted"}

@api.put("/products/{product_id}")
async def put_product(product_id: int, name: str = Form(...), description: str = Form(...), category: str = Form(...), price: int = Form(...)):
    await ProductRepository.update(Product(id=product_id, name=name, description=description, category=category, price=price))
    return {"message": "Product updated"}


@api.put("/media/{image_id}")
async def put_image(image_id: int, image: UploadFile = File(...)):  # noqa: B008
    image_db = await ImagesRepository.get_by_ids_with_products(list_id_images=[image_id])
    if not image_db:
        logging.warning("Image not found")
        raise HTTPException(status_code=404, detail="Image not found")
    path = await handle_file_upload(image, image_db[0].product.category)
    await ImagesRepository.update(image_id, path)
    await delete_file(image_db[0].path)
    return {"message": "Image updated"}




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
