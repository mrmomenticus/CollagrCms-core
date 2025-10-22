import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from src.core.categories import CategoryService
from src.models.models import Category


class CategoryCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Название категории (обязательное, от 1 до 255 символов)",
    )
    description: str | None = Field(
        None, max_length=1000, description="Описание категории (до 1000 символов)"
    )
    is_active: bool = Field(True, description="Статус активности категории")


class CategoryUpdateRequest(BaseModel):
    name: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="Название категории (от 1 до 255 символов)",
    )
    description: str | None = Field(
        None, max_length=1000, description="Описание категории (до 1000 символов)"
    )
    is_active: bool | None = Field(None, description="Статус активности категории")


# Создаем роутер для категорий
router = APIRouter(prefix="/categories", tags=["categories"])
log = logging.getLogger(__name__)


@router.get("/", response_model=list[Category], response_description="OK")
async def get_categories(is_only_active: bool = True) -> list[Category]:
    """Возвращает все категории (включая неактивные).

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
        log.error(f"API ошибка при получении категорий: {e}")
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Ошибка получения категорий"
        ) from e


@router.get("/{category_id}", response_model=Category)
async def get_category(category_id: int) -> Category:
    """Получает категорию по ID.

    Args:
        category_id: ID категории

    Returns:
        Модель бд найденной категории.

    Raises:
        HTTPException: 404 - Не найдена категория.

    """
    log.info(f"API запрос: получение категории по ID {category_id}")
    try:
        category = await CategoryService.get_category_by_id(category_id)
        log.info(f"API ответ: возвращена категория {category.name}")
        return category
    except HTTPException as e:
        log.error(f"API ошибка при получении категории {category_id}: {e}")
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Ошибка получения категории"
        ) from e


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Category)
async def create_category(request: CategoryCreateRequest) -> Category:
    """Создает новую категорию.

    Args:
        request: Модель для создания данных.

    Returns:
        Созданная категория.

    Raises:
        HTTPException: 400 - Ошибка создания категории.

    """
    log.info(f"API запрос: создание категории {request.name}")
    try:
        category = await CategoryService.create_category(
            request.name, request.description
        )
        log.info(f"API ответ: категория создана {category.name} (ID: {category.id})")
        return category
    except HTTPException as e:
        raise e
    except Exception as e:
        log.error(f"API ошибка при создании категории {request.name}: {e}")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Ошибка создания категории"
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
        HTTPException: Не найденная категория

    """
    log.info(f"API запрос: обновление категории ID {category_id}")
    try:
        category = await CategoryService.update_category(category_id, request)
        log.info(f"API ответ: категория обновлена {category.name}")
        return category
    except HTTPException as e:
        log.error(f"API ошибка при обновлении категории {category_id}: {e}")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Ошибка обновления категории."
        ) from e


@router.delete("/{category_id}")
async def delete_category(category_id: int) -> dict[str, str]:
    """Удаляет категорию (мягкое удаление - деактивирует).

    Args:
        category_id: ID категории

    Returns:
        Сообщение об успешном удалении

    Raises:
        HTTPException: 500 - ошибка при удаление категории.

    """
    log.info(f"API запрос: мягкое удаление категории ID {category_id}")
    try:
        await CategoryService.delete_category(category_id, hard_delete=False)
        log.info("API ответ: категория успешно деактивирована")
        return {"message": "Категория успешно удалена"}
    except HTTPException as e:
        log.error(f"API ошибка при удалении категории {category_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления категории") from e


@router.delete("/{category_id}/hard")
async def hard_delete_category(category_id: int) -> dict[str, str]:
    """Полностью удаляет категорию из базы данных.

    Args:
        category_id: ID категории

    Returns:
        Сообщение об успешном удалении

    Raises:
        HTTPException: Если не получилось удалить категорию.

    """
    log.info(f"API запрос: полное удаление категории ID {category_id}")
    try:
        await CategoryService.delete_category(category_id, hard_delete=True)
        log.info("API ответ: категория полностью удалена")
        return {"message": "Категория полностью удалена"}
    except HTTPException as e:
        log.error(f"API ошибка при полном удалении категории {category_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Ошибка полного удаления категории"
        ) from e
