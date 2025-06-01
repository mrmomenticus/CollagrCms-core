from typing import NamedTuple

class Image(NamedTuple):
    """Информация об изображении для коллажа"""
    path: str
    price: str
    description: str
