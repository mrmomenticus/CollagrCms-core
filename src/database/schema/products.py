from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel


class ProductDb(BaseModel):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    category: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[int] = mapped_column(nullable=False)
    image_path: Mapped[str] = mapped_column(nullable=True)
