from pydantic import BaseModel


class Image(BaseModel):
    id: int
    path: str


class Product(BaseModel):
    id: int
    name: str
    description: str
    category: str
    price: int
    image_path: Image


class ImagesList(BaseModel):
    images: list
