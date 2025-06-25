from pydantic import BaseModel


class Image(BaseModel):
    id: int
    product_id: int


class Product(BaseModel):
    name: str
    description: str
    category: str
    price: int

