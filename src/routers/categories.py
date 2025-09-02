"""
API роутеры для работы с категориями
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.core.categories import CategoryService
from src.models.models import Category
# Заменены кастомные исключения на стандартные - импорт больше не нужен


class CategoryCreateRequest(BaseModel):
    name: str
    description: str | None = None
    is_active: bool = True


class CategoryUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


# Создаем роутер для категорий
router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=List[Category])
async def get_categories():
    """
    Получает все категории (включая неактивные)

    Returns:
        Список всех категорий
    """
    logging.info("API запрос: получение всех категорий")
    try:
        categories = await CategoryService.get_all_categories(include_inactive=True)
        logging.info(f"API ответ: возвращено {len(categories)} категорий")
        return categories
    except Exception as e:
        logging.error(f"API ошибка при получении категорий: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения категорий") from e


@router.get("/simple/")
async def get_categories_simple():
    """
    Получает все категории в упрощенном формате

    Returns:
        Список категорий с id и названием
    """
    logging.info("API запрос: получение категорий в простом формате")
    try:
        categories = await CategoryService.get_all_categories(include_inactive=True)
        result = [
            {
                "id": cat.id,
                "name": cat.name,
                "description": cat.description,
                "is_active": cat.is_active,
            }
            for cat in categories
        ]
        logging.info(f"API ответ: возвращено {len(result)} категорий в простом формате")
        return result
    except Exception as e:
        logging.error(f"API ошибка при получении категорий в простом формате: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения категорий") from e


@router.get("/all/")
async def get_all_categories():
    """
    Получает все категории (включая неактивные)

    Returns:
        Список всех категорий с id, названием и статусом активности
    """
    logging.info("API запрос: получение всех категорий включая неактивные")
    try:
        categories = await CategoryService.get_all_categories(include_inactive=True)
        result = [
            {
                "id": cat.id,
                "name": cat.name,
                "description": cat.description,
                "is_active": cat.is_active,
            }
            for cat in categories
        ]
        logging.info(f"API ответ: возвращено {len(result)} всех категорий")
        return result
    except Exception as e:
        logging.error(f"API ошибка при получении всех категорий: {e}")
        raise HTTPException(
            status_code=500, detail="Ошибка получения всех категорий"
        ) from e


@router.get("/active/")
async def get_active_categories():
    """
    Получает только активные категории

    Returns:
        Список только активных категорий
    """
    logging.info("API запрос: получение только активных категорий")
    try:
        categories = await CategoryService.get_all_categories(include_inactive=False)
        result = [
            {"id": cat.id, "name": cat.name, "description": cat.description}
            for cat in categories
        ]
        logging.info(f"API ответ: возвращено {len(result)} активных категорий")
        return result
    except Exception as e:
        logging.error(f"API ошибка при получении активных категорий: {e}")
        raise HTTPException(
            status_code=500, detail="Ошибка получения активных категорий"
        ) from e


@router.get("/{category_id}", response_model=Category)
async def get_category(category_id: int):
    """
    Получает категорию по ID

    Args:
        category_id: ID категории

    Returns:
        Категория
    """
    logging.info(f"API запрос: получение категории по ID {category_id}")
    try:
        category = await CategoryService.get_category_by_id(category_id)
        logging.info(f"API ответ: возвращена категория {category.name}")
        return category
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"API ошибка при получении категории {category_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения категории") from e


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Category)
async def create_category(request: CategoryCreateRequest):
    """
    Создает новую категорию

    Args:
        request: Данные для создания категории

    Returns:
        Созданная категория
    """
    logging.info(f"API запрос: создание категории {request.name}")
    try:
        category = await CategoryService.create_category(
            request.name, request.description
        )
        logging.info(
            f"API ответ: категория создана {category.name} (ID: {category.id})"
        )
        return category
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"API ошибка при создании категории {request.name}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания категории") from e


@router.put("/{category_id}", response_model=Category)
async def update_category(
    category_id: int,
    request: CategoryUpdateRequest,
):
    """
    Обновляет категорию

    Args:
        category_id: ID категории
        request: Данные для обновления категории

    Returns:
        Обновленная категория
    """
    logging.info(f"API запрос: обновление категории ID {category_id}")
    try:
        category = await CategoryService.update_category(
            category_id, request.name, request.description, request.is_active
        )
        logging.info(f"API ответ: категория обновлена {category.name}")
        return category
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"API ошибка при обновлении категории {category_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Ошибка обновления категории"
        ) from e


@router.delete("/{category_id}")
async def delete_category(category_id: int):
    """
    Удаляет категорию (мягкое удаление - деактивирует)

    Args:
        category_id: ID категории

    Returns:
        Сообщение об успешном удалении
    """
    logging.info(f"API запрос: мягкое удаление категории ID {category_id}")
    try:
        await CategoryService.delete_category(category_id, hard_delete=False)
        logging.info("API ответ: категория успешно деактивирована")
        return {"message": "Категория успешно удалена"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"API ошибка при удалении категории {category_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления категории") from e


@router.delete("/{category_id}/hard")
async def hard_delete_category(category_id: int):
    """
    Полностью удаляет категорию из базы данных

    Args:
        category_id: ID категории

    Returns:
        Сообщение об успешном удалении
    """
    logging.info(f"API запрос: полное удаление категории ID {category_id}")
    try:
        await CategoryService.delete_category(category_id, hard_delete=True)
        logging.info("API ответ: категория полностью удалена")
        return {"message": "Категория полностью удалена"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"API ошибка при полном удалении категории {category_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Ошибка полного удаления категории"
        ) from e
