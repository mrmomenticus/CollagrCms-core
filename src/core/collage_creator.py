from typing import List, Tuple
from PIL import Image, ImageDraw
import logging
import math
from src.core.overlay import Overlay
from src.models.models import ImageWithProduct


class CollageCreator:
    """Класс для создания коллажа из изображений с текстом, размер холста зависит от количества изображений, все изображения 900x900"""

    def __init__(self):
        self._cell_size = 900  # Размер каждой ячейки (изображения) 900x900
        self._background_color = (53, 3, 61)
        self._border_color = (126, 100, 126)
        self._border_thickness = 10  # Меньше, т.к. холст меньше
        self._cell_margin = 8  # Минимальный отступ между картинками

    def _calculate_grid_dimensions(self, image_count: int) -> tuple[int, int]:
        """
        Рассчитывает оптимальные размеры сетки для заданного количества изображений (до 12).
        Возвращает (колонки, строки)
        """
        if image_count <= 0:
            raise ValueError("Количество изображений должно быть больше 0")
        if image_count == 1:
            return 1, 1
        # Ищем наиболее "квадратную" сетку
        best_cols = 1
        best_rows = image_count
        min_diff = image_count
        for cols in range(1, image_count + 1):
            rows = math.ceil(image_count / cols)
            diff = abs(cols - rows)
            if cols * rows >= image_count and diff < min_diff:
                best_cols, best_rows = cols, rows
                min_diff = diff
        return best_cols, best_rows

    def _resize_image_to_cell(self, img: Image.Image):
        """
        Изменяет размер изображения до 900x900 без полос: если меньше — растягивает, если больше — сжимает пропорционально.
        Возвращает картинку и box (0, 0, 900, 900) для совместимости с overlay.
        """
        cell_img = img.resize((self._cell_size, self._cell_size), Image.Resampling.LANCZOS)
        return cell_img, (0, 0, self._cell_size, self._cell_size)

    def create(self, image_models: list[ImageWithProduct], output_path: str) -> str:
        """
        Создает коллаж из переданных изображений, все изображения 900x900, холст минимального размера.
        Args:
            image_models: Список изображений с продуктами (от 1 до 12)
            output_path: Путь для сохранения коллажа
        Returns:
            Путь к созданному коллажу
        """
        image_count = len(image_models)
        if image_count < 1 or image_count > 12:
            raise ValueError(f"Количество изображений должно быть от 1 до 12, получено: {image_count}")
        # Рассчитываем размеры сетки
        grid_cols, grid_rows = self._calculate_grid_dimensions(image_count)
        # Размер холста
        canvas_width = grid_cols * self._cell_size + (grid_cols - 1) * self._cell_margin
        canvas_height = grid_rows * self._cell_size + (grid_rows - 1) * self._cell_margin
        # Создаем изображение
        collage = Image.new(
            "RGB", (canvas_width, canvas_height), self._background_color
        )
        draw = ImageDraw.Draw(collage)
        # Рисуем рамку
        for i in range(self._border_thickness):
            draw.rectangle(
                [(i, i), (canvas_width - 1 - i, canvas_height - 1 - i)],
                outline=self._border_color,
            )
        # Overlay для 900x900
        overlay = Overlay(self._cell_size, self._cell_size)
        # Размещаем изображения
        for idx, img_model in enumerate(image_models):
            try:
                img = Image.open(img_model.path)
                cell_img, img_box = self._resize_image_to_cell(img)
                cell_img = overlay.add_text_overlay(cell_img, img_model, img_box)
                row = idx // grid_cols
                col = idx % grid_cols
                x = col * (self._cell_size + self._cell_margin)
                y = row * (self._cell_size + self._cell_margin)
                collage.paste(cell_img, (x, y))
            except Exception as e:
                logging.error(f"Ошибка при обработке изображения {img_model.path}: {e}")
                raise
        collage.save(output_path, "JPEG", quality=95)
        logging.info(f"Коллаж сохранён в {output_path} (сетка: {grid_cols}x{grid_rows}, изображений: {image_count})")
        return output_path
