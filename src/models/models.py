from pydantic import BaseModel, ConfigDict, Field, computed_field


class Category(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class Product(BaseModel):
    id: int
    name: str
    description: str
    price: int
    categories: list[Category] = []

    @computed_field
    @property
    def category_names(self) -> list[str]:
        """Возвращает названия категорий для удобства."""
        return [cat.name for cat in self.categories] if self.categories else []

    model_config = ConfigDict(from_attributes=True)


class ImageWithProduct(BaseModel):
    id: int
    product_id: int
    path: str
    product: Product

    model_config = ConfigDict(from_attributes=True)


class CategoryCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Название категории (обязательное, от 1 до 255 символов)",
    )
    description: str | None = Field(
        None, max_length=1000, description="Описание категории (до 1000 символов)",
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
        None, max_length=1000, description="Описание категории (до 1000 символов)",
    )
    is_active: bool | None = Field(None, description="Статус активности категории")


class CollageInfoResponse(BaseModel):
    total_images: int = Field(0, description="Общее количество изображений")
    total_batches: int = Field(0, description="Общее количество пакетов")
    batch_size: int = Field(16, description="Размер пакета")
    has_images: bool = Field(False, description="Есть ли изображения")
    message: str = Field("", description="Сообщение о статусе")
    products: list[dict] | None = Field(None, description="Список продуктов (опционально)")
    categories: list[str] | None = Field(None, description="Список категорий (опционально)")
