from pydantic import BaseModel, ConfigDict, computed_field
from typing import Optional


class Category(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
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
        """Возвращает названия категорий для удобства"""
        return [cat.name for cat in self.categories] if self.categories else []

    model_config = ConfigDict(from_attributes=True)


class ImageWithProduct(BaseModel):
    id: int
    product_id: int
    path: str
    product: Product

    model_config = ConfigDict(from_attributes=True)
