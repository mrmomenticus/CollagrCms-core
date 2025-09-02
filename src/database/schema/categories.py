from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class CategoryDb(BaseModel):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    description: Mapped[str] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Связь с продуктами (many-to-many)
    products: Mapped[list["ProductDb"]] = relationship(  # noqa: F821 # type: ignore
        "ProductDb", secondary="product_categories", back_populates="categories"
    )
