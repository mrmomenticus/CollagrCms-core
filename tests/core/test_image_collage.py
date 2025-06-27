import os
import pytest
from src.models.models import ImageWithProduct, Product
from src.core.collage_creator import CollageCreator


@pytest.mark.parametrize("output_path", ["test_collage_output.jpg"])
def test_collage_creation(output_path):
    images = [
        ImageWithProduct(
            id=1,
            product_id=1,
            path="tests/core/img/input/1.jpg",
            product=Product(
                id=1,
                name="Брелок",
                category="Брелок",
                price=1500,
                description='"Летний закат" брелок двусторонний, акрил с блёстками, 6 см',
            ),
        ),
        ImageWithProduct(
            id=2,
            product_id=2,
            path="tests/core/img/input/2.jpg",
            product=Product(
                id=2,
                name="Стикерпак",
                category="Стикеры",
                price=2000,
                description='"Офисные друзья" стикерпак, сахарная ламинация, А7',
            ),
        ),
        ImageWithProduct(
            id=3,
            product_id=3,
            path="tests/core/img/input/3.jpg",
            product=Product(
                id=3,
                name="Значок",
                category="Значки",
                price=3500,
                description='"Замок" значок прямоугольный, с эффектом "металлик", 25*70мм',
            ),
        ),
        ImageWithProduct(
            id=4,
            product_id=4,
            path="tests/core/img/input/4.jpg",
            product=Product(
                id=4,
                name="Оскорблинки",
                category="Значки",
                price=1200,
                description='"Оскорблинки" набор значков, 5 шт. 25 мм и 1 шт. 28*85 мм',
            ),
        ),
        ImageWithProduct(
            id=5,
            product_id=5,
            path="tests/core/img/input/5.jpg",
            product=Product(
                id=5,
                name="Пейзаж",
                category="Картины",
                price=4000,
                description="Городской пейзаж на закате",
            ),
        ),
        ImageWithProduct(
            id=6,
            product_id=6,
            path="tests/core/img/input/6.jpg",
            product=Product(
                id=6,
                name="Морской пейзаж",
                category="Картины",
                price=2500,
                description="Морской пейзаж с кораблями",
            ),
        ),
        ImageWithProduct(
            id=7,
            product_id=7,
            path="tests/core/img/input/7.jpg",
            product=Product(
                id=7,
                name="Цветы в вазе",
                category="Картины",
                price=1800,
                description="Цветочная композиция в вазе",
            ),
        ),
        ImageWithProduct(
            id=8,
            product_id=8,
            path="tests/core/img/input/8.jpeg",
            product=Product(
                id=8,
                name="Зимний лес",
                category="Картины",
                price=3000,
                description="Зимний лес в снегу",
            ),
        ),
        ImageWithProduct(
            id=9,
            product_id=9,
            path="tests/core/img/input/9.jpg",
            product=Product(
                id=9,
                name="Абстракция",
                category="Картины",
                price=2200,
                description="Абстрактная геометрия в ярких цветах",
            ),
        ),
    ]
    creator = CollageCreator()
    result_path = creator.create(images, output_path)
    assert os.path.exists(result_path)
    # Удаляем файл после теста
    os.remove(result_path)
