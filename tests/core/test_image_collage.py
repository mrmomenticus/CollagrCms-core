import os
import pytest
from PIL import Image
from src.models.models import ImageWithProduct, Product
from src.core.collage_creator import CollageCreator


def create_test_image(id: int, name: str, category: str, price: int, description: str) -> ImageWithProduct:
    """Создает тестовое изображение с продуктом"""
    return ImageWithProduct(
        id=id,
        product_id=id,
        path=f"/home/mrmomenticus/Repos/CollagrCms-core/tests/core/img/input/{id}.jpg",
        product=Product(
            id=id,
            name=name,
            category=category,
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
    result_path = creator.create(images, output_path)
    assert os.path.exists(result_path)
    
    # Проверяем размеры A3 (горизонтальный)
    with Image.open(result_path) as img:
        assert img.size == (4961, 3508), f"Размер должен быть A3 (горизонтальный) (4961x3508), получен: {img.size}"
    
    os.remove(result_path)


@pytest.mark.parametrize("image_count,expected_grid", [
    (1, (1, 1)),
    (2, (2, 1)),
    (3, (3, 1)),
    (4, (2, 2)),
    (5, (3, 2)),
    (6, (3, 2)),
    (7, (4, 2)),  # Изменено для A3
    (8, (4, 2)),  # Изменено для A3
    (9, (3, 3)),
])
def test_grid_calculation(image_count, expected_grid):
    """Тест расчета размеров сетки для разного количества изображений"""
    creator = CollageCreator()
    grid = creator._calculate_grid_dimensions(image_count)
    assert grid == expected_grid


@pytest.mark.parametrize("image_count", [1, 2, 3, 4, 5, 6, 7, 8])
def test_collage_creation_different_counts(image_count):
    """Тест создания коллажей с разным количеством изображений в формате A3 (горизонтальный)"""
    images = []
    for i in range(image_count):
        images.append(create_test_image(
            i + 1,
            f"Товар {i + 1}",
            "Тест",
            1000 + i * 100,
            f"Описание товара {i + 1}"
        ))
    
    output_path = f"test_collage_{image_count}_images.jpg"
    creator = CollageCreator()
    result_path = creator.create(images, output_path)
    assert os.path.exists(result_path)
    
    # Проверяем размеры A3 (горизонтальный)
    with Image.open(result_path) as img:
        assert img.size == (4961, 3508), f"Размер должен быть A3 (горизонтальный) (4961x3508), получен: {img.size}"
    
    os.remove(result_path)


def test_cell_size_calculation():
    """Тест расчета размеров ячеек для разных сеток в формате A3"""
    creator = CollageCreator()
    
    # Тест для 1 изображения
    cell_width, cell_height = creator._calculate_cell_size(1, 1)
    assert cell_width > 4500, f"Ширина ячейки для 1 изображения должна быть большой, получена: {cell_width}"
    assert cell_height > 3000, f"Высота ячейки для 1 изображения должна быть большой, получена: {cell_height}"
    
    # Тест для 9 изображений (3x3)
    cell_width, cell_height = creator._calculate_cell_size(3, 3)
    assert 1500 < cell_width < 1600, f"Ширина ячейки для 3x3 должна быть ~1550, получена: {cell_width}"
    assert 1000 < cell_height < 1200, f"Высота ячейки для 3x3 должна быть ~1100, получена: {cell_height}"
    
    # Тест для 2 изображений (2x1)
    cell_width, cell_height = creator._calculate_cell_size(2, 1)
    assert 2300 < cell_width < 2400, f"Ширина ячейки для 2x1 должна быть ~2350, получена: {cell_width}"
    assert cell_height > 3000, f"Высота ячейки для 2x1 должна быть большой, получена: {cell_height}"
    
    # Тест для 7 изображений (4x2) - новая схема для A3
    cell_width, cell_height = creator._calculate_cell_size(4, 2)
    assert 1100 < cell_width < 1200, f"Ширина ячейки для 4x2 должна быть ~1150, получена: {cell_width}"
    assert 1600 < cell_height < 1700, f"Высота ячейки для 4x2 должна быть ~1654, получена: {cell_height}"


def test_a3_format_consistency():
    """Тест консистентности формата A3 (горизонтальный) для всех вариантов"""
    creator = CollageCreator()
    
    for image_count in range(1, 10):
        images = [create_test_image(i, f"Товар {i}", "Тест", 1000, f"Описание {i}") for i in range(1, image_count + 1)]
        output_path = f"test_a3_consistency_{image_count}.jpg"
        
        result_path = creator.create(images, output_path)
        
        with Image.open(result_path) as img:
            assert img.size == (4961, 3508), f"Коллаж с {image_count} изображениями должен быть A3 (4961x3508), получен: {img.size}"
        
        os.remove(result_path)


def test_horizontal_layout_advantages():
    """Тест преимуществ горизонтального формата A3"""
    creator = CollageCreator()
    
    # Тест для 7 изображений - новая схема 4x2
    images = [create_test_image(i, f"Товар {i}", "Тест", 1000, f"Описание {i}") for i in range(1, 8)]
    output_path = "test_horizontal_7_images.jpg"
    
    result_path = creator.create(images, output_path)
    
    with Image.open(result_path) as img:
        assert img.size == (4961, 3508), f"Размер должен быть A3 (4961x3508), получен: {img.size}"
    
    # Проверяем, что ширина больше высоты (горизонтальный формат)
    assert img.size[0] > img.size[1], "Формат должен быть горизонтальным"
    
    os.remove(result_path)


def test_invalid_image_count():
    """Тест обработки некорректного количества изображений"""
    creator = CollageCreator()
    
    # Тест с 0 изображений
    with pytest.raises(ValueError, match="Количество изображений должно быть больше 0"):
        creator._calculate_grid_dimensions(0)
    
    # Тест с более чем 9 изображений
    with pytest.raises(ValueError, match="Максимальное количество изображений: 9"):
        creator._calculate_grid_dimensions(10)
    
    # Тест создания коллажа с пустым списком
    with pytest.raises(ValueError, match="Количество изображений должно быть от 1 до 9"):
        creator.create([], "test.jpg")
    
    # Тест создания коллажа с более чем 9 изображениями
    images = [create_test_image(i, f"Товар {i}", "Тест", 1000, f"Описание {i}") for i in range(1, 11)]
    with pytest.raises(ValueError, match="Количество изображений должно быть от 1 до 9"):
        creator.create(images, "test.jpg")


def test_single_image_collage():
    """Тест создания коллажа с одним изображением в формате A3 (горизонтальный)"""
    images = [create_test_image(1, "Единственный товар", "Тест", 1500, "Описание единственного товара")]
    output_path = "test_single_image_collage.jpg"
    creator = CollageCreator()
    result_path = creator.create(images, output_path)
    assert os.path.exists(result_path)
    
    # Проверяем размеры A3 (горизонтальный)
    with Image.open(result_path) as img:
        assert img.size == (4961, 3508), f"Размер должен быть A3 (горизонтальный) (4961x3508), получен: {img.size}"
    
    os.remove(result_path)


def test_two_images_collage():
    """Тест создания коллажа с двумя изображениями в формате A3 (горизонтальный)"""
    images = [
        create_test_image(1, "Первый товар", "Тест", 1500, "Описание первого товара"),
        create_test_image(2, "Второй товар", "Тест", 2000, "Описание второго товара"),
    ]
    output_path = "test_two_images_collage.jpg"
    creator = CollageCreator()
    result_path = creator.create(images, output_path)
    assert os.path.exists(result_path)
    
    # Проверяем размеры A3 (горизонтальный)
    with Image.open(result_path) as img:
        assert img.size == (4961, 3508), f"Размер должен быть A3 (горизонтальный) (4961x3508), получен: {img.size}"
    
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
    result_path = creator.create(images, output_path)
    assert os.path.exists(result_path)
    # Проверяем размеры холста
    cols, rows = creator._calculate_grid_dimensions(image_count)
    expected_size = (cols * 900, rows * 900)
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
        creator.create([], "test.jpg")
    images = [create_test_image(i, f"Товар {i}", "Тест", 1000, f"Описание {i}") for i in range(1, 14)]
    with pytest.raises(ValueError, match="Количество изображений должно быть от 1 до 12"):
        creator.create(images, "test.jpg")
