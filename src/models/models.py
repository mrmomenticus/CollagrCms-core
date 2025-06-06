from pydantic import BaseModel


class ImageInfo(BaseModel):
    """Информация об изображении для коллажа"""

    path: str
    price: str
    description: str


class Product(BaseModel):
    name: str
    description: str
    category: str
    price: str
