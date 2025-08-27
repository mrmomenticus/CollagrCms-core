"""
Исключения для CollagrCms с русскими сообщениями
"""

from fastapi import HTTPException, status


class BaseCollagrException(Exception):
    """Базовое исключение для CollagrCms"""

    def __init__(self, message: str = "Произошла ошибка"):
        self.message = message
        super().__init__(self.message)


class NotFoundError(BaseCollagrException):
    """Исключение для случаев, когда данные не найдены"""

    def __init__(self, entity: str = "Данные"):
        super().__init__(f"{entity} не найдены")


class CategoryNotFoundError(NotFoundError):
    """Категория не найдена"""

    def __init__(
        self, category_name: str | None = None, category_id: int | None = None
    ):
        if category_name:
            super().__init__(f"Категория '{category_name}'")
        elif category_id:
            super().__init__(f"Категория с ID {category_id}")
        else:
            super().__init__("Категория")


class ProductNotFoundError(NotFoundError):
    """Продукт не найден"""

    def __init__(self, product_id: int | None = None):
        if product_id:
            super().__init__(f"Продукт с ID {product_id}")
        else:
            super().__init__("Продукт")


class ImageNotFoundError(NotFoundError):
    """Изображение не найдено"""

    def __init__(self, image_id: int | None = None):
        if image_id:
            super().__init__(f"Изображение с ID {image_id}")
        else:
            super().__init__("Изображение")


class CategoryInactiveError(BaseCollagrException):
    """Категория неактивна"""

    def __init__(self, category_name: str):
        super().__init__(f"Категория '{category_name}' неактивна")


class CategoryAlreadyExistsError(BaseCollagrException):
    """Категория уже существует"""

    def __init__(self, category_name: str):
        super().__init__(f"Категория с названием '{category_name}' уже существует")


class InvalidFileError(BaseCollagrException):
    """Неверный файл"""

    def __init__(self, message: str = "Неверный файл"):
        super().__init__(message)


class CollageCreationError(BaseCollagrException):
    """Ошибка создания коллажа"""

    def __init__(self, message: str = "Ошибка создания коллажа"):
        super().__init__(message)


def convert_to_http_exception(exc: BaseCollagrException) -> HTTPException:
    """Конвертирует внутренние исключения в HTTP исключения"""
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    elif isinstance(
        exc, (CategoryInactiveError, CategoryAlreadyExistsError, InvalidFileError)
    ):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message
        )
    elif isinstance(exc, CollageCreationError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.message
        )
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc.message
        )
