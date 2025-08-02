from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from .base import BaseModel


class ProductDb(BaseModel):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=True)
    price: Mapped[int] = mapped_column(nullable=False)

    image: Mapped["ImagesDb"] = relationship(
        "ImagesDb", back_populates="product", uselist=False, cascade="delete"
    )  # noqa: F821
    
    # Связь с категорией
    category: Mapped["CategoryDb"] = relationship(
        "CategoryDb", back_populates="products"
    )
