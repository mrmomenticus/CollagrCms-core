"""
API роутеры для работы с продуктами
"""

import logging
from typing import List
from fastapi import APIRouter, Form, UploadFile, File, HTTPException, status, Request

from src.core.products import ProductService
from src.core.images import ImageService
from src.models.models import ImageWithProduct
from src.utils.exceptions import (
    ProductNotFoundError,
    CategoryNotFoundError,
    CategoryInactiveError,
    InvalidFileError,
    convert_to_http_exception,
)

# Создаем роутер для продуктов
router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def создать_продукт(
    name: str = Form(...),
    description: str = Form(...),
    category_name: str = Form(...),
    price: int = Form(...),
    image: UploadFile = File(...),  # noqa: B008
):
    """
    Создает новый продукт с изображением

    Args:
        name: Название продукта
        description: Описание продукта
        category_name: Название категории
        price: Цена продукта
        image: Файл изображения

    Returns:
        Информация о созданном продукте и изображении
    """
    logging.info(f"API запрос: создание продукта {name} в категории {category_name}")
    try:
        # Создаем продукт
        product_db = await ProductService.create_product(
            name, description, category_name, price
        )

        # Создаем изображение для продукта
        image_db = await ImageService.create_image(product_db.id, image, category_name)

        logging.info(
            f"API ответ: продукт создан {name} (ID: {product_db.id}) с изображением (ID: {image_db.id})"
        )
        return {"image": image_db}

    except (CategoryNotFoundError, CategoryInactiveError, InvalidFileError) as e:
        logging.warning(f"API ошибка: {e.message}")
        raise convert_to_http_exception(e)
    except Exception as e:
        logging.error(f"API ошибка при создании продукта {name}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания продукта")


@router.get("/", response_model=List[ImageWithProduct])
async def получить_продукты(request: Request):
    """
    Получает все продукты с изображениями

    Args:
        request: HTTP запрос для получения base_url

    Returns:
        Список продуктов с изображениями
    """
    logging.info("API запрос: получение всех продуктов")
    try:
        # Получаем все изображения с продуктами
        images_db = await ImageService.get_all_images_with_products()

        # Форматируем для API ответа
        result = ImageService.format_products_with_images(
            images_db, request, include_categories=False
        )

        logging.info(f"API ответ: возвращено {len(result)} продуктов")
        return result

    except Exception as e:
        logging.error(f"API ошибка при получении продуктов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения продуктов")


@router.get("/with-categories/")
async def получить_продукты_с_категориями(request: Request):
    """
    Получает все продукты с полной информацией о категориях

    Args:
        request: HTTP запрос для получения base_url

    Returns:
        Список продуктов с информацией о категориях
    """
    logging.info("API запрос: получение продуктов с категориями")
    try:
        # Получаем все изображения с продуктами
        images_db = await ImageService.get_all_images_with_products()

        # Форматируем для API ответа с категориями
        result = ImageService.format_products_with_images(
            images_db, request, include_categories=True
        )

        logging.info(f"API ответ: возвращено {len(result)} продуктов с категориями")
        return result

    except Exception as e:
        logging.error(f"API ошибка при получении продуктов с категориями: {e}")
        raise HTTPException(
            status_code=500, detail="Ошибка получения продуктов с категориями"
        )


@router.get("/by-category/{category_name}/")
async def получить_продукты_по_категории(category_name: str, request: Request):
    """
    Получает все продукты определенной категории

    Args:
        category_name: Название категории
        request: HTTP запрос для получения base_url

    Returns:
        Список продуктов указанной категории
    """
    logging.info(f"API запрос: получение продуктов категории {category_name}")
    try:
        from src.core.categories import CategoryService

        # Проверяем существование и активность категории
        category = await CategoryService.get_category_by_name(
            category_name, check_active=True
        )

        # Получаем все изображения с продуктами
        all_images_db = await ImageService.get_all_images_with_products()

        # Фильтруем по категории
        category_images = [
            img for img in all_images_db if img.product.category_id == category.id
        ]

        # Форматируем для API ответа
        products_data = ImageService.format_products_with_images(
            category_images, request, include_categories=True
        )

        result = {
            "category": {
                "id": category.id,
                "name": category.name,
                "description": category.description,
            },
            "products": products_data,
            "total_products": len(products_data),
        }

        logging.info(
            f"API ответ: возвращено {len(products_data)} продуктов категории {category_name}"
        )
        return result

    except (CategoryNotFoundError, CategoryInactiveError) as e:
        logging.warning(f"API ошибка: {e.message}")
        raise convert_to_http_exception(e)
    except Exception as e:
        logging.error(
            f"API ошибка при получении продуктов категории {category_name}: {e}"
        )
        raise HTTPException(
            status_code=500, detail="Ошибка получения продуктов по категории"
        )


@router.put("/{product_id}")
async def обновить_продукт(
    product_id: int,
    name: str = Form(...),
    description: str = Form(...),
    category_name: str = Form(...),
    price: int = Form(...),
):
    """
    Обновляет продукт

    Args:
        product_id: ID продукта
        name: Новое название продукта
        description: Новое описание продукта
        category_name: Название категории
        price: Новая цена продукта

    Returns:
        Сообщение об успешном обновлении
    """
    logging.info(f"API запрос: обновление продукта ID {product_id}")
    try:
        await ProductService.update_product(
            product_id, name, description, category_name, price
        )

        logging.info(f"API ответ: продукт обновлен {name}")
        return {"message": "Продукт обновлен"}

    except (ProductNotFoundError, CategoryNotFoundError, CategoryInactiveError) as e:
        logging.warning(f"API ошибка: {e.message}")
        raise convert_to_http_exception(e)
    except Exception as e:
        logging.error(f"API ошибка при обновлении продукта {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления продукта")


@router.delete("/{product_id}")
async def удалить_продукт(product_id: int):
    """
    Удаляет продукт и связанное изображение

    Args:
        product_id: ID продукта

    Returns:
        Сообщение об успешном удалении
    """
    logging.info(f"API запрос: удаление продукта ID {product_id}")
    try:
        # Получаем изображения продукта для удаления файлов
        images = await ImageService.get_images_by_ids(list_id_products=[product_id])

        # Удаляем файлы изображений
        if images:
            from src.utils.file import delete_file

            for img in images:
                await delete_file(img.path)

        # Удаляем продукт (изображения удалятся каскадно)
        await ProductService.delete_product(product_id)

        logging.info(f"API ответ: продукт удален")
        return {"message": "Продукт удален"}

    except ProductNotFoundError as e:
        logging.warning(f"API ошибка: {e.message}")
        raise convert_to_http_exception(e)
    except Exception as e:
        logging.error(f"API ошибка при удалении продукта {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления продукта")
