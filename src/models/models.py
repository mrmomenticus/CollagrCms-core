from pydantic import BaseModel


class ImageInfo(BaseModel):
    path: str
    price: str
    description: str


class Product(BaseModel):
    name: str
    description: str
    category: str
    price: int
    