class BaseError(Exception):
    """Базовое исключение для CollagrCms."""

    def __init__(self, message: str = "Произошла ошибка"):
        self.message = message
        super().__init__(self.message)


class NotFoundError(BaseError):
    """Исключение для случаев, когда данные не найдены."""

    def __init__(self, entity: str = "Данные"):
        super().__init__(f"{entity} не найдены")
