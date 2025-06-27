from pydantic import BaseModel, ConfigDict


class Product(BaseModel):
    id: int
    name: str
    description: str
    category: str
    price: int

    model_config = ConfigDict(from_attributes=True)


class ImageWithProduct(BaseModel):
    id: int
    product_id: int
    path: str
    product: Product

    model_config = ConfigDict(from_attributes=True)
