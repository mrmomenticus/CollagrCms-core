import os
import pytest
from src.core.image_info import ImageInfo
from src.core.collage_creator import CollageCreator


@pytest.mark.parametrize("output_path", ["test_collage_output.jpg"])
def test_collage_creation(output_path):
    images = [
        ImageInfo(
            "tests/core/img/input/1.jpg",
            "1500 ₽",
            '"Летний закат" брелок двусторонний, акрил с блёстками, 6 см',
        ),
        ImageInfo(
            "tests/core/img/input/2.jpg",
            "2000 ₽",
            '"Офисные друзья" стикерпак, сахарная ламинация, А7',
        ),
        ImageInfo(
            "tests/core/img/input/3.jpg",
            "3500 ₽",
            '"Замок" значок прямоугольный, с эффектом "металлик", 25*70мм',
        ),
        ImageInfo(
            "tests/core/img/input/4.jpg",
            "1200 ₽",
            '"Оскорблинки" набор значков, 5 шт. 25 мм и 1 шт. 28*85 мм',
        ),
        ImageInfo("tests/core/img/input/5.jpg", "4000 ₽", "Городской пейзаж на закате"),
        ImageInfo("tests/core/img/input/6.jpg", "2500 ₽", "Морской пейзаж с кораблями"),
        ImageInfo(
            "tests/core/img/input/7.jpg", "1800 ₽", "Цветочная композиция в вазе"
        ),
        ImageInfo("tests/core/img/input/8.jpeg", "3000 ₽", "Зимний лес в снегу"),
        ImageInfo(
            "tests/core/img/input/9.jpg",
            "2200 ₽",
            "Абстрактная геометрия в ярких цветах",
        ),
    ]
    creator = CollageCreator()
    result_path = creator.create(images, output_path)
    assert os.path.exists(result_path)
    # Удаляем файл после теста

    os.remove(result_path)
