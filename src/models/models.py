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
    category_id: Optional[int] = None
    price: int
    category: Optional[Category] = None

    @computed_field
    @property
    def category_name(self) -> Optional[str]:
        """Возвращает название категории для удобства"""
        return self.category.name if self.category else None

    model_config = ConfigDict(from_attributes=True)


class ImageWithProduct(BaseModel):
    id: int
    product_id: int
    path: str
    product: Product

    model_config = ConfigDict(from_attributes=True)
