from typing import List, Tuple
from PIL import Image, ImageDraw
import logging
import math
from src.core.overlay import Overlay
from src.models.models import ImageWithProduct


class CollageCreator:
    """Класс для создания коллажа из изображений с текстом в формате A3 (горизонтальный)"""

    def __init__(self):
        # Размеры A3 в горизонтальной ориентации в пикселях при 300 DPI
        # A3: 297mm x 420mm -> горизонтальный: 420mm x 297mm
        self._a3_width = 4961  # 420mm * 300 DPI / 25.4
        self._a3_height = 3508  # 297mm * 300 DPI / 25.4
        self._margin = 80  # Отступы от краев (увеличил для A3)
        self._cell_margin = 50  # Отступы между ячейками (увеличил для A3)
        self._background_color = (53, 3, 61)
        self._border_color = (126, 100, 126)
        self._border_thickness = 40  # Увеличил толщину рамки для A3

    def _calculate_grid_dimensions(self, image_count: int) -> Tuple[int, int]:
        """
        Рассчитывает оптимальные размеры сетки для заданного количества изображений.
        Возвращает (колонки, строки)
        """
        if image_count <= 0:
            raise ValueError("Количество изображений должно быть больше 0")
        
        if image_count == 1:
            return 1, 1
        elif image_count == 2:
            return 2, 1
        elif image_count == 3:
            return 3, 1
        elif image_count == 4:
            return 2, 2
        elif image_count == 5:
            return 3, 2
        elif image_count == 6:
            return 3, 2
        elif image_count == 7:
            return 4, 2  # 4 в первом ряду, 3 во втором
        elif image_count == 8:
            return 4, 2  # 4 в каждом ряду
        elif image_count == 9:
            return 3, 3
        else:
            raise ValueError("Максимальное количество изображений: 9")

    def _calculate_cell_size(self, grid_cols: int, grid_rows: int) -> Tuple[int, int]:
        """
        Рассчитывает размеры ячейки для заданной сетки в формате A3
        """
        # Доступная область для изображений (с учетом отступов)
        available_width = self._a3_width - 2 * self._margin - (grid_cols - 1) * self._cell_margin
        available_height = self._a3_height - 2 * self._margin - (grid_rows - 1) * self._cell_margin
        
        # Размеры ячейки
        cell_width = available_width // grid_cols
        cell_height = available_height // grid_rows
        
        return cell_width, cell_height

    def _resize_image_to_cell(self, img: Image.Image, cell_width: int, cell_height: int) -> Image.Image:
        """
        Изменяет размер изображения под размер ячейки с сохранением пропорций
        """
        scale = max(
            cell_width / img.width, cell_height / img.height
        )
        new_width = int(img.width * scale)
        new_height = int(img.height * scale)
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Обрезаем по центру, если изображение больше ячейки
        x_offset = max(0, (new_width - cell_width) // 2)
        y_offset = max(0, (new_height - cell_height) // 2)
        cropped = resized.crop((
            x_offset,
            y_offset,
            x_offset + cell_width,
            y_offset + cell_height,
        ))
        return cropped

    def create(self, image_models: list[ImageWithProduct], output_path: str) -> str:
        """
        Создает коллаж из переданных изображений в формате A3 (горизонтальный).
        
        Args:
            image_models: Список изображений с продуктами (от 1 до 9)
            output_path: Путь для сохранения коллажа
            
        Returns:
            Путь к созданному коллажу
        """
        image_count = len(image_models)
        
        if image_count < 1 or image_count > 9:
            raise ValueError(f"Количество изображений должно быть от 1 до 9, получено: {image_count}")
        
        # Рассчитываем размеры сетки
        grid_cols, grid_rows = self._calculate_grid_dimensions(image_count)
        
        # Рассчитываем размеры ячеек
        cell_width, cell_height = self._calculate_cell_size(grid_cols, grid_rows)
        
        # Создаем изображение формата A3 (горизонтальный)
        collage = Image.new(
            "RGB", (self._a3_width, self._a3_height), self._background_color
        )
        draw = ImageDraw.Draw(collage)
        
        # Рисуем рамку
        for i in range(self._border_thickness):
            draw.rectangle(
                [(i, i), (self._a3_width - 1 - i, self._a3_height - 1 - i)],
                outline=self._border_color,
            )
        
        # Создаем overlay с новыми размерами ячейки
        overlay = Overlay(cell_width, cell_height)
        
        # Размещаем изображения
        for idx, img_model in enumerate(image_models):
            try:
                img = Image.open(img_model.path)
                cell_img = self._resize_image_to_cell(img, cell_width, cell_height)
                cell_img = overlay.add_text_overlay(cell_img, img_model)
                
                # Рассчитываем позицию в сетке
                row = idx // grid_cols
                col = idx % grid_cols
                
                # Рассчитываем координаты для размещения
                x = self._margin + col * (cell_width + self._cell_margin)
                y = self._margin + row * (cell_height + self._cell_margin)
                
                collage.paste(cell_img, (x, y))
                
            except Exception as e:
                logging.error(f"Ошибка при обработке изображения {img_model.path}: {e}")
                raise
        
        collage.save(output_path, "JPEG", quality=95)
        logging.info(f"Коллаж A3 (горизонтальный) сохранён в {output_path} (сетка: {grid_cols}x{grid_rows}, ячейки: {cell_width}x{cell_height}, изображений: {image_count})")
        return output_path
