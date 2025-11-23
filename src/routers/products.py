import logging

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status

from src.core.categories import CategoryService
from src.core.images import ImageService
from src.core.products import ProductService
from src.models.models import ImageWithProduct
from src.utils.file import delete_file

# Кастомные исключения удалены — используем стандартные HTTPException

# Создаем роутер для продуктов
router = APIRouter(prefix="/v1/products", tags=["products"])

log = logging.getLogger(__name__)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    category_names: str = Form(...),  # Список названий через запятую
    price: int = Form(...),
    image: UploadFile = File(...),  # noqa: B008
):
    """Создает новый продукт с изображением.

    Args:
        name: Название продукта
        description: Описание продукта
        category_names: Названия категорий через запятую
        price: Цена продукта
        image: Файл изображения

    Returns:
        Информация о созданном продукте и изображении

    """
    category_list = [name.strip() for name in category_names.split(",") if name.strip()]
    log.info("API запрос: создание продукта %s в категориях %s", name, category_list)
    try:
        # Создаем продукт
        product_db = await ProductService.create_product(
            name, description, category_list, price,
        )

        # Создаем изображение для продукта (используем первую категорию для пути)
        first_category = category_list[0] if category_list else "default"
        image_db = await ImageService.create_image(product_db.id, image, first_category)

        log.info(
            f"API ответ: продукт создан {name} (ID: {product_db.id}) с изображением (ID: {image_db.id})",
        )
        return {"image": image_db}

    except HTTPException as e:
        log.warning(f"API ошибка: {getattr(e, 'detail', str(e))}")
        raise e
    except Exception as e:
        log.exception("API ошибка при создании продукта %s: %s", name, e)
        raise HTTPException(status_code=500, detail="Ошибка создания продукта") from e


@router.get("/", response_model=list[ImageWithProduct])
async def получить_продукты(request: Request):
    """Получает все продукты с изображениями.

    Args:
        request: HTTP запрос для получения base_url

    Returns:
        Список продуктов с изображениями

    """
    log.info("API запрос: получение всех продуктов")
    try:
        # Получаем все изображения с продуктами
        images_db = await ImageService.get_all_images_with_products()

        # Форматируем для API ответа
        result = ImageService.format_products_with_images(
            images_db, request, include_categories=False,
        )

        log.info(f"API ответ: возвращено {len(result)} продуктов")
        return result

    except Exception as e:
        log.exception("API ошибка при получении продуктов: %s", e)
        raise HTTPException(status_code=500, detail="Ошибка получения продуктов") from e


@router.get("/with-categories/")
async def get_product_with_category(request: Request):
    """Получает все продукты с полной информацией о категориях.

    Args:
        request: HTTP запрос для получения base_url

    Returns:
        Список продуктов с информацией о категориях

    """
    log.info("API запрос: получение продуктов с категориями")
    try:
        # Получаем все изображения с продуктами
        images_db = await ImageService.get_all_images_with_products()

        # Форматируем для API ответа с категориями
        result = ImageService.format_products_with_images(
            images_db, request, include_categories=True,
        )

        log.info(f"API ответ: возвращено {len(result)} продуктов с категориями")
        return result

    except Exception as e:
        log.exception("API ошибка при получении продуктов с категориями: %s", e)
        raise HTTPException(
            status_code=500, detail="Ошибка получени from eя продуктов с категориями",
        ) from e


@router.get("/by-category/{category_name}/")
async def get_product_category(category_name: str, request: Request):  # -> dict[str, Any]:
    """Получает все продукты определенной категории.

    Args:
        category_name: Название категории
        request: HTTP запрос для получения base_url

    Returns:
        Список продуктов указанной категории

    """
    log.info("API запрос: получение продуктов категории %s", category_name)
    try:
        # Проверяем существование и активность категории
        category = await CategoryService.get_category_by_name(
            category_name, check_active=True,
        )

        # Получаем все изображения с продуктами
        all_images_db = await ImageService.get_all_images_with_products()

        # Фильтруем по категории
        category_images = [
            img
            for img in all_images_db
            if any(cat.id == category.id for cat in img.product.categories)
        ]

        # Форматируем для API ответа
        products_data = ImageService.format_products_with_images(
            category_images, request, include_categories=True,
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

        log.info(
            f"API ответ: возвращено {len(products_data)} продуктов категории {category_name}",
        )
        return result

    except HTTPException as e:
        log.warning(f"API ошибка: {getattr(e, 'detail', str(e))}")
        raise e
    except Exception as e:
        log.exception(
            "API ошибка при получении продуктов категории %s: %s", category_name, e,
        )
        raise HTTPException(
            status_code=500, detail="Ошибка получени from eя продуктов по категории",
        ) from e


@router.put("/{product_id}")
async def update_product(
    product_id: int,
    name: str = Form(...),
    description: str = Form(...),
    category_names: str = Form(...),  # Список названий через запятую
    price: int = Form(...),
):
    """Обновляет продукт.

    Args:
        product_id: ID продукта
        name: Новое название продукта
        description: Новое описание продукта
        category_names: Названия категорий через запятую
        price: Новая цена продукта

    Returns:
        Сообщение об успешном обновлении

    """
    category_list = [name.strip() for name in category_names.split(",") if name.strip()]
    log.info("API запрос: обновление продукта ID %s", product_id)
    try:
        await ProductService.update_product(
            product_id, name, description, category_list, price,
        )

        log.info("API ответ: продукт обновлен %s", name)
        return {"message": "Продукт обновлен"}

    except HTTPException as e:
        log.warning(f"API ошибка: {getattr(e, 'detail', str(e))}")
        raise e
    except Exception as e:
        log.exception("API ошибка при обновлении продукта %s: %s", product_id, e)
        raise HTTPException(status_code=500, detail="Ошибка обновления продукта") from e


@router.delete("/{product_id}")
async def delete_product(product_id: int):
    """Удаляет продукт и связанное изображение.

    Args:
        product_id: ID продукта

    Returns:
        Сообщение об успешном удалении

    """
    log.info("API запрос: удаление продукта ID %s", product_id)
    try:
        # Получаем изображения продукта для удаления файлов
        images = await ImageService.get_images_by_ids(list_id_products=[product_id])

        # Удаляем файлы изображений
        if images:
            for img in images:
                await delete_file(img.path)

        # Удаляем продукт (изображения удалятся каскадно)
        await ProductService.delete_product(product_id)

        log.info("API ответ: продукт удален")
        return {"message": "Продукт удален"}

    except HTTPException as e:
        log.warning(f"API ошибка: {getattr(e, 'detail', str(e))}")
        raise e
    except Exception as e:
        log.exception("API ошибка при удалении продукта %s: %s", product_id, e)
        raise HTTPException(status_code=500, detail="Ошибка удаления продукта") from e
