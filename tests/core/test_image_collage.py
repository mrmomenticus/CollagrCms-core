import os
import pytest
from src.core.image_info import ImageInfo
from src.core.collage_creator import CollageCreator

@pytest.mark.parametrize("output_path", ["test_collage_output.jpg"])
def test_collage_creation(output_path):
    images = [
        ImageInfo("input/1.jpg", "1500 ₽", '"Летний закат" брелок двусторонний, акрил с блёстками, 6 см'),
        ImageInfo("2.jpg", "2000 ₽", '"Офисные друзья" стикерпак, сахарная ламинация, А7'),
        ImageInfo("3.jpg", "3500 ₽", '"Замок" значок прямоугольный, с эффектом "металлик", 25*70мм'),
        ImageInfo("4.jpg", "1200 ₽", '"Оскорблинки" набор значков, 5 шт. 25 мм и 1 шт. 28*85 мм'),
        ImageInfo("5.jpg", "4000 ₽", "Городской пейзаж на закате"),
        ImageInfo("6.jpg", "2500 ₽", "Морской пейзаж с кораблями"),
        ImageInfo("7.jpg", "1800 ₽", "Цветочная композиция в вазе"),
        ImageInfo("8.jpeg", "3000 ₽", "Зимний лес в снегу"),
        ImageInfo("9.jpg", "2200 ₽", "Абстрактная геометрия в ярких цветах"),
    ]
    creator = CollageCreator()
    result_path = creator.create(images, output_path)
    assert os.path.exists(result_path)
    # Удаляем файл после теста
    os.remove(result_path)
