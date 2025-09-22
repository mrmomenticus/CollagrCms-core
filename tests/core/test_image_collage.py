import os
import pytest
from PIL import Image
from src.models.models import ImageWithProduct, Product, Category
from src.core.collage_creator import CollageCreator


def create_test_image(id: int, name: str, category: str, price: int, description: str) -> ImageWithProduct:
    """Создает тестовое изображение с продуктом"""
    return ImageWithProduct(
        id=id,
        product_id=id,
        path=f"tests/core/img/input/{id}.jpg",
        product=Product(
            id=id,
            name=name,
            categories=[Category(id=id, name=category, description="")],
            price=price,
            description=description,
        ),
    )


@pytest.mark.parametrize("output_path", ["test_collage_output.jpg"])
def test_collage_creation_9_images(output_path):
    """Тест создания коллажа с 9 изображениями (3x3) в формате A3 (горизонтальный)"""
    images = [
        create_test_image(1, "Брелок", "Брелок", 1500, '"Летний закат" брелок двусторонний, акрил с блёстками, 6 см'),
        create_test_image(2, "Стикерпак", "Стикеры", 2000, '"Офисные друзья" стикерпак, сахарная ламинация, А7'),
        create_test_image(3, "Значок", "Значки", 3500, '"Замок" значок прямоугольный, с эффектом "металлик", 25*70мм'),
        create_test_image(4, "Оскорблинки", "Значки", 1200, '"Оскорблинки" набор значков, 5 шт. 25 мм и 1 шт. 28*85 мм'),
        create_test_image(5, "Пейзаж", "Картины", 4000, "Городской пейзаж на закате"),
        create_test_image(6, "Морской пейзаж", "Картины", 2500, "Морской пейзаж с кораблями"),
        create_test_image(7, "Цветы в вазе", "Картины", 1800, "Цветочная композиция в вазе"),
        create_test_image(8, "Зимний лес", "Картины", 3000, "Зимний лес в снегу"),
        create_test_image(9, "Абстракция", "Картины", 2200, "Абстрактная геометрия в ярких цветах"),
    ]
    creator = CollageCreator()
    result_path = creator.create(images, output_path, is_price=True)
    assert os.path.exists(result_path)
    
    # Проверяем размеры A3 (горизонтальный)
    with Image.open(result_path) as img:
        assert img.size == (2716, 2716), f"Размер должен быть A3 (горизонтальный) (4961x3508), получен: {img.size}"
    
    os.remove(result_path)



@pytest.mark.parametrize("image_count", list(range(1, 13)))
def test_collage_creation_dynamic_sizes(image_count):
    """Тест создания коллажей с разным количеством изображений (1-12), проверка размеров холста"""
    images = [
        create_test_image(i + 1, f"Товар {i + 1}", "Тест", 1000 + i * 100, f"Описание товара {i + 1}")
        for i in range(image_count)
    ]
    output_path = f"test_collage_{image_count}_images.jpg"
    creator = CollageCreator()
    result_path = creator.create(images, output_path, is_price=True)
    assert os.path.exists(result_path)
    cols, rows = creator._calculate_grid_dimensions(image_count)
    expected_size = (
        cols * creator._cell_size + (cols - 1) * creator._cell_margin,
        rows * creator._cell_size + (rows - 1) * creator._cell_margin,
    )
    with Image.open(result_path) as img:
        assert img.size == expected_size, f"Размер коллажа должен быть {expected_size}, получен: {img.size}"
    os.remove(result_path)


def test_grid_calculation_new():
    """Тест расчета размеров сетки для разного количества изображений (1-12)"""
    creator = CollageCreator()
    for image_count in range(1, 13):
        cols, rows = creator._calculate_grid_dimensions(image_count)
        assert cols * rows >= image_count
        assert abs(cols - rows) <= image_count  # сетка максимально квадратная


def test_invalid_image_count():
    """Тест обработки некорректного количества изображений (0 и >12)"""
    creator = CollageCreator()
    with pytest.raises(ValueError, match="Количество изображений должно быть больше 0"):
        creator._calculate_grid_dimensions(0)
    with pytest.raises(ValueError, match="Количество изображений должно быть от 1 до 12"):
        creator.create([], "test.jpg", is_price=True)
    images = [create_test_image(i, f"Товар {i}", "Тест", 10, f"Описание {i}") for i in range(1, 14)]
    with pytest.raises(ValueError, match="Количество изображений должно быть от 1 до 12"):
        creator.create(images, "test.jpg", is_price=True)


def test_resize_image_to_cell():
    """Тест метода _resize_image_to_cell с изображениями разных размеров"""
    creator = CollageCreator()
    
    # Создаем тестовое изображение 1000x1200 (вертикальное)
    img_vertical = Image.new("RGB", (1000, 1200), color="red")
    resized_img, box = creator._resize_image_to_cell(img_vertical)
    assert resized_img.size == (900, 900), f"Размер должен быть 900x900, получен: {resized_img.size}"
    assert box == (0, 0, 900, 900), f"Box должен быть (0, 0, 900, 900), получен: {box}"
    
    # Создаем тестовое изображение 1200x1000 (горизонтальное)
    img_horizontal = Image.new("RGB", (1200, 1000), color="blue")
    resized_img, box = creator._resize_image_to_cell(img_horizontal)
    assert resized_img.size == (900, 900), f"Размер должен быть 900x900, получен: {resized_img.size}"
    assert box == (0, 0, 900, 900), f"Box должен быть (0, 0, 900, 900), получен: {box}"
    
    # Создаем тестовое изображение 800x600 (горизонтальное, меньше 900)
    img_small_horizontal = Image.new("RGB", (800, 600), color="green")
    resized_img, box = creator._resize_image_to_cell(img_small_horizontal)
    assert resized_img.size == (900, 900), f"Размер должен быть 900x900, получен: {resized_img.size}"
    assert box == (0, 0, 900, 900), f"Box должен быть (0, 0, 900, 900), получен: {box}"
    
    # Создаем тестовое изображение 600x800 (вертикальное, меньше 900)
    img_small_vertical = Image.new("RGB", (600, 800), color="yellow")
    resized_img, box = creator._resize_image_to_cell(img_small_vertical)
    assert resized_img.size == (900, 900), f"Размер должен быть 900x900, получен: {resized_img.size}"
    assert box == (0, 0, 900, 900), f"Box должен быть (0, 0, 900, 900), получен: {box}"
    
    # Создаем тестовое изображение 900x900 (уже правильного размера)
    img_correct = Image.new("RGB", (900, 900), color="purple")
    resized_img, box = creator._resize_image_to_cell(img_correct)
    assert resized_img.size == (900, 900), f"Размер должен быть 900x900, получен: {resized_img.size}"
    assert box == (0, 0, 900, 900), f"Box должен быть (0, 0, 900, 900), получен: {box}"
