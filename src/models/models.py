from pydantic import BaseModel


class ImageInfo(BaseModel):
    path: str
    price: str
    description: str


class Product(BaseModel):
    id: int
    name: str
    description: str
    category: str
    price: int
    image_path: str


class ImagesList(BaseModel):
    images: list
