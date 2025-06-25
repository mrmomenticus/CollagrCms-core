from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.schema.products import ProductDb
from .base import BaseModel


class ImagesDb(BaseModel):
    __tablename__ = "images"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    path: Mapped[str] = mapped_column(nullable=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), unique=True)

    product: Mapped["ProductDb"] = relationship("ProductDb", back_populates="image")
