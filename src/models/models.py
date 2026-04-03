from pydantic import BaseModel, ConfigDict, Field


class Category(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class Product(BaseModel):
    id: int
    name: str
    description: str
    price: int
    categories: list[Category] = []

    @property
    def category_names(self) -> list[str]:
        """Возвращает названия категорий для удобства."""
        return [cat.name for cat in self.categories] if self.categories else []

    model_config = ConfigDict(from_attributes=True)


class ImageWithProduct(BaseModel):
    id: int
    product_id: int
    path: str
    product: Product

    model_config = ConfigDict(from_attributes=True)


class ImageData(BaseModel):
    """Модель для передачи данных об изображении от фронтенда."""

    id: int = Field(..., description="ID изображения")
    url: str = Field(..., description="URL изображения")
    product_id: int = Field(..., description="ID продукта")
    product_name: str = Field("", description="Название продукта")
    product_price: int = Field(0, description="Цена продукта")
    product_description: str = Field("", description="Описание продукта")
    categories: list[str] = Field(
        default_factory=list, description="Категории продукта"
    )


class CollageRequest(BaseModel):
    """Модель для запроса генерации коллажа с передачей данных от фронтенда."""

    images: list[ImageData] = Field(
        ...,
        min_length=1,
        max_length=16,
        description="Список изображений для коллажа (от 1 до 16)",
    )
    is_price: bool = Field(True, description="Добавлять ли цену на оверлей")
    batch_size: int = Field(
        16, ge=1, le=16, description="Размер пакета для пакетной генерации"
    )


class DirectusConfig(BaseModel):
    """Конфигурация для подключения к Directus."""

    url: str = Field(..., description="URL Directus API")
    token: str | None = Field(None, description="Токен авторизации")
    email: str | None = Field(None, description="Email для авторизации")
    password: str | None = Field(None, description="Пароль для авторизации")


class CellPosition(BaseModel):
    """Позиция ячейки на холсте."""

    x: float = Field(..., description="Координата X")
    y: float = Field(..., description="Координата Y")


class CellSize(BaseModel):
    """Размер ячейки."""

    width: float = Field(..., description="Ширина")
    height: float = Field(..., description="Высота")


class CaptionStyle(BaseModel):
    """Стиль подписи под изображением."""

    font_size: int = Field(13, description="Размер шрифта подписи")
    color: str = Field("#1f2937", description="Цвет текста подписи")
    background: str = Field("#ffffff", description="Цвет фона подписи")
    per_cell_opacity: int = Field(
        80, ge=0, le=100, description="Прозрачность фона (0-100)"
    )


class TextConfig(BaseModel):
    """Конфигурация текстовой ячейки."""

    type: str = Field(..., description="Тип текста: price, name, description, category")
    font_size: int = Field(14, description="Размер шрифта")
    color: str = Field("#1f2937", description="Цвет текста")


class LayoutCell(BaseModel):
    """Ячейка макета коллажа."""

    id: str = Field(..., description="Уникальный ID ячейки")
    type: str = Field(..., description="Тип ячейки: image или text")
    index: int = Field(..., description="Индекс ячейки в макете")
    position: CellPosition = Field(..., description="Позиция ячейки")
    size: CellSize = Field(..., description="Размер ячейки")
    rotation: float = Field(0, description="Поворот в градусах")
    product_id: int | None = Field(
        None, description="ID продукта для привязки (опционально)"
    )
    text_config: TextConfig | None = Field(
        None, description="Конфигурация текста (для текстовых ячеек)"
    )
    captions: list[str] = Field(
        default_factory=list, description="Типы подписей: name, description, price"
    )
    caption_style: CaptionStyle | None = Field(
        None, description="Стиль подписей (для ячеек изображений)"
    )


class CanvasConfig(BaseModel):
    """Конфигурация холста."""

    width: int = Field(800, description="Ширина холста")
    height: int = Field(600, description="Высота холста")


class CollageLayout(BaseModel):
    """Макет коллажа."""

    canvas: CanvasConfig = Field(..., description="Конфигурация холста")
    cells: list[LayoutCell] = Field(..., description="Список ячеек")
    metadata: dict | None = Field(None, description="Метаданные макета")


class CollageSettings(BaseModel):
    """Настройки генерации коллажа."""

    is_price: bool = Field(True, description="Добавлять ли цену")
    is_name: bool = Field(True, description="Добавлять ли название")
    is_category: bool = Field(True, description="Добавлять ли категорию")
    is_description: bool = Field(False, description="Добавлять ли описание")
    caption_opacity: int = Field(
        80, ge=0, le=100, description="Прозрачность фона подписей (0-100)"
    )


class CollageWithLayoutRequest(BaseModel):
    """Модель для запроса генерации коллажа с макетом."""

    images: list[ImageData] = Field(
        ...,
        min_length=1,
        max_length=16,
        description="Список изображений для коллажа (от 1 до 16)",
    )
    layout: CollageLayout = Field(..., description="Макет коллажа")
    settings: CollageSettings = Field(
        default_factory=CollageSettings, description="Настройки генерации"
    )
