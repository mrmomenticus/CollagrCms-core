from typing import NamedTuple


class ImageInfo(NamedTuple):
    """Информация об изображении для коллажа"""

    path: str
    price: str
    description: str
