import logging

from fastapi import APIRouter, HTTPException, status
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from src.core.categories import CategoryService
from src.models.models import Category, CategoryCreateRequest, CategoryUpdateRequest

# Создаем роутер для категорий
router = APIRouter(prefix="/categories", tags=["categories"])
log = logging.getLogger(__name__)


@router.get("/", response_model=list[Category], response_description="OK")
async def get_categories(is_only_active: bool = True) -> list[Category]:
    """Возвращает все категории.

    Raises:
        HTTPException: 404 - Не удалось найти нужную категорию.

    Returns:
        Список всех категорий.

    """
    log.info("API запрос: получение всех категорий")
    try:
        categories = await CategoryService.get_all_categories(is_only_active)
        log.info(f"API ответ: возвращено {len(categories)} категорий")
        return categories
    except Exception as e:
        log.exception("API ошибка при получении категорий: %s", e)
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Ошибка получения категорий",
        ) from e


@router.get("/{category_id}", response_model=Category)
async def get_category(category_id: int) -> Category:
    """Получает категорию по ID.

    Args:
        category_id: ID категории

    Returns:
        Модель бд найденной категории.

    """
    log.info("API запрос: получение категории по ID %s", category_id)
    try:
        category = await CategoryService.get_category_by_id(category_id)
        log.info(f"API ответ: возвращена категория {category.name}")
        return category
    except HTTPException as e:
        log.error("API ошибка при получении категории %s: %s", category_id, e)
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Ошибка получения категории",
        ) from e


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Category)
async def create_category(request: CategoryCreateRequest) -> Category:
    """Создает новую категорию.

    Args:
        request: Модель для создания данных.

    Returns:
        Созданная категория.

    """
    log.info(f"API запрос: создание категории {request.name}")
    try:
        category = await CategoryService.create_category(
            request.name,
            request.description,
        )
        log.info(f"API ответ: категория создана {category.name} (ID: {category.id})")
        return category
    except Exception as e:
        log.error(f"API ошибка при создании категории {request.name}: {e}")
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

    """
    log.info("API запрос: обновление категории ID %s", category_id)
    try:
        category = await CategoryService.update_category(category_id, request)
        log.info(f"API ответ: категория обновлена {category.name}")
        return category
    except Exception as e:
        log.exception(f"API ошибка при обновлении категории {category_id}")
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


    """
    log.info("API запрос: мягкое удаление категории ID %s", category_id)
    try:
        name_category = await CategoryService.delete_category(category_id, hard_delete)
        if hard_delete:
            return {"message": f"Категория: {name_category} удалена"}
        else:
            return {"message": "Категория успешно удалена"}
    except Exception as e:
        log.exception(f"API ошибка при удалении категории {category_id}")
        raise HTTPException(status_code=500, detail="Ошибка удаления категории") from e
