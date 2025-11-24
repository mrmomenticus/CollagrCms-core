import logging
from typing import cast

from fastapi import APIRouter, HTTPException, status
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from src.core.categories import CategoryService
from src.models.models import Category, CategoryCreateRequest, CategoryUpdateRequest

# Создаем роутер для категорий
router = APIRouter(prefix="/v1/categories", tags=["categories"])
log = logging.getLogger(__name__)


@router.get("/", response_model=list[Category], response_description="OK")
async def get_categories(is_only_active: bool = True) -> list[Category]:
    """Возвращает все категории.

    Args:
        is_only_active: Фильтровать только активные категории

    Returns:
        Список всех категорий.

    """
    log.info("API запрос: получение всех категорий, is_only_active=%s", is_only_active)
    try:
        categories = await CategoryService.get_all_categories(is_only_active)
        log.info("API ответ: возвращено %d категорий", len(categories))
        return categories
    except Exception as e:
        log.exception("API ошибка при получении категорий: %s", e)
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Категории не найдены",
        ) from e


@router.get("/{category_id}", response_model=Category)
async def get_category(category_id: int) -> Category:
    """Получает категорию по ID.

    Args:
        category_id: ID категории

    Returns:
        Модель бд найденной категории.

    Raises:
        HTTPException: 404 - Категория не найдена

    """
    log.info("API запрос: получение категории по ID %s", category_id)
    try:
        category = await CategoryService.get_category_by_id(category_id)
        log.info("API ответ: возвращена категория %s", category.name)
        return category
    except Exception as e:
        log.error("API ошибка при получении категории %s: %s", category_id, e)
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Категория не найдена",
        ) from e


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Category)
async def create_category(request: CategoryCreateRequest) -> Category:
    """Создает новую категорию.

    Args:
        request: Модель для создания данных.

    Returns:
        Созданная категория.

    Raises:
        HTTPException: 400 - Ошибка при создании категории

    """
    log.info("API запрос: создание категории %s", request.name)
    try:
        category = await CategoryService.create_category(
            request.name,
            request.description,
        )
        log.info("API ответ: категория создана %s (ID: %d)", category.name, category.id)
        return category
    except Exception as e:
        log.error("API ошибка при создании категории %s: %s", request.name, e)
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Ошибка создания категории",
        ) from e


@router.put("/{category_id}", response_model=Category)
async def update_category(
    category_id: int,
    request: CategoryUpdateRequest,
) -> Category:
    """Обновляет категорию.

    Args:
        category_id: ID категории
        request: Данные для обновления категории

    Returns:
        Обновленная категория

    Raises:
        HTTPException: 400 - Ошибка при обновлении категории

    """
    log.info("API запрос: обновление категории ID %s", category_id)
    try:
        category = await CategoryService.update_category(category_id, request)
        log.info("API ответ: категория обновлена %s", category.name)
        return category
    except Exception as e:
        log.exception("API ошибка при обновлении категории %s", category_id)
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Ошибка обновления категории.",
        ) from e


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    hard_delete: bool = False,
) -> dict[str, str]:
    """Удаляет категорию (мягкое - деактивирует, хард - удаляет из БД).

    Args:
        category_id: ID категории
        hard_delete: Флаг деактивация или удаление

    Returns:
        Сообщение об успешном удалении

    Raises:
        HTTPException: 500 - Ошибка удаления категории

    """
    delete_type = "жесткое" if hard_delete else "мягкое"
    log.info("API запрос: %s удаление категории ID %s", delete_type, category_id)
    try:
        name_category = await CategoryService.delete_category(category_id, hard_delete)
        if hard_delete:
            message = f"Категория: {name_category} удалена"
        else:
            message = "Категория успешно деактивирована"
        log.info("API ответ: %s", message)
        return {"message": message}
    except Exception as e:
        log.exception("API ошибка при удалении категории %s", category_id)
        raise HTTPException(status_code=500, detail="Ошибка удаления категории") from e
