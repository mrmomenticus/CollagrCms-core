import os
import pytest
from src.models.image_info import ImageInfo
from src.core.collage_creator import CollageCreator


@pytest.mark.parametrize("output_path", ["test_collage_output.jpg"])
def test_collage_creation(output_path):
    images = [
        ImageInfo(
            path="tests/core/img/input/1.jpg",
            price="1500 ₽",
            description='"Летний закат" брелок двусторонний, акрил с блёстками, 6 см',
        ),
        ImageInfo(
            path="tests/core/img/input/2.jpg",
            price="2000 ₽",
            description='"Офисные друзья" стикерпак, сахарная ламинация, А7',
        ),
        ImageInfo(
            path="tests/core/img/input/3.jpg",
            price="3500 ₽",
            description='"Замок" значок прямоугольный, с эффектом "металлик", 25*70мм',
        ),
        ImageInfo(
            path="tests/core/img/input/4.jpg",
            price="1200 ₽",
            description='"Оскорблинки" набор значков, 5 шт. 25 мм и 1 шт. 28*85 мм',
        ),
        ImageInfo(
            path="tests/core/img/input/5.jpg",
            price="4000 ₽",
            description="Городской пейзаж на закате",
        ),
        ImageInfo(
            path="tests/core/img/input/6.jpg",
            price="2500 ₽",
            description="Морской пейзаж с кораблями",
        ),
        ImageInfo(
            path="tests/core/img/input/7.jpg",
            price="1800 ₽",
            description="Цветочная композиция в вазе",
        ),
        ImageInfo(
            path="tests/core/img/input/8.jpeg",
            price="3000 ₽",
            description="Зимний лес в снегу",
        ),
        ImageInfo(
            path="tests/core/img/input/9.jpg",
            price="2200 ₽",
            description="Абстрактная геометрия в ярких цветах",
        ),
    ]
    creator = CollageCreator()
    result_path = creator.create(images, output_path)
    assert os.path.exists(result_path)
    # Удаляем файл после теста
    os.remove(result_path)
