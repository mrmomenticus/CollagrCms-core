from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, Column, Integer

from src.database.schema.categories import CategoryDb
from src.database.schema.images import ImagesDb
from .base import BaseModel


# Ассоциативная таблица для many-to-many связи между продуктами и категориями
product_categories = Table(
    "product_categories",
    BaseModel.metadata,
    Column("product_id", Integer, ForeignKey("products.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True),
)


class ProductDb(BaseModel):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[int] = mapped_column(nullable=False)

    image: Mapped["ImagesDb"] = relationship(
        "ImagesDb", back_populates="product", uselist=False, cascade="delete"
    )  # noqa: F821

    # Связь с категориями (many-to-many)
    categories: Mapped[list["CategoryDb"]] = relationship(
        "CategoryDb", secondary=product_categories, back_populates="products"
    )
