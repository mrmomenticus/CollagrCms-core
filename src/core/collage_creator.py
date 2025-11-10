import logging
import math

from PIL import Image, ImageDraw

from src.core.overlay import Overlay
from src.models.models import ImageWithProduct

log = logging.getLogger(__name__)


class CollageCreator:
    """Класс для создания коллажа из изображений с текстом, размер холста зависит от количества изображений."""

    def __init__(self) -> None:
        self._cell_size = 900  # Размер каждой ячейки (изображения) 900x900
        self._background_color = (53, 3, 61)
        self._border_color = (126, 100, 126)
        self._border_thickness = 10  # Меньше, т.к. холст меньше
        self._cell_margin = 8  # Минимальный отступ между картинками

    def _calculate_grid_dimensions(self, image_count: int) -> tuple[int, int]:
        """Рассчитывает оптимальные размеры сетки для заданного количества изображений (до 16).
        Возвращает (колонки, строки).
        """  # noqa: D205
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
        """Изменяет размер изображения до 900x900 с сохранением пропорций и обрезкой.

        Изображение масштабируется так, чтобы короткая сторона стала 900, затем обрезается по центру до 900x900.
        Возвращает картинку и box (0, 0, 900, 900) для совместимости с overlay.
        """
        original_width, original_height = img.size

        # Определяем коэффициент масштабирования, чтобы короткая сторона стала 900
        scale_factor = self._cell_size / min(original_width, original_height)

        # Новые размеры после масштабирования
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)

        # Масштабируем изображение
        scaled_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Обрезаем до 900x900 по центру
        left = (new_width - self._cell_size) // 2
        top = (new_height - self._cell_size) // 2
        right = left + self._cell_size
        bottom = top + self._cell_size

        cell_img = scaled_img.crop((left, top, right, bottom))
        return cell_img, (0, 0, self._cell_size, self._cell_size)

    def create(
        self,
        image_models: list[ImageWithProduct],
        output_path: str,
        is_price: bool = True,
    ) -> str:
        """Создает коллаж из переданных изображений, все изображения 900x900, холст минимального размера.

        Args:
            image_models: Список изображений с продуктами (от 1 до 12)
            output_path: Путь для сохранения коллажа
            is_price: Флаг, указывающий, нужно ли добавлять цену на оверлей
        Returns:
            Путь к созданному коллажу

        """
        image_count = len(image_models)
        if image_count < 1 or image_count > 16:
            raise ValueError(
                f"Количество изображений должно быть от 1 до 12, получено: {image_count}",
            )
        # Рассчитываем размеры сетки
        grid_cols, grid_rows = self._calculate_grid_dimensions(image_count)
        # Размер холста
        canvas_width = grid_cols * self._cell_size + (grid_cols - 1) * self._cell_margin
        canvas_height = (
            grid_rows * self._cell_size + (grid_rows - 1) * self._cell_margin
        )
        # Создаем изображение
        collage = Image.new(
            "RGB",
            (canvas_width, canvas_height),
            self._background_color,
        )
        draw = ImageDraw.Draw(collage)
        # Рисуем рамку
        for i in range(self._border_thickness):
            draw.rectangle(
                [(i, i), (canvas_width - 1 - i, canvas_height - 1 - i)],
                outline=self._border_color,
            )
        # Overlay для 900x900 всегда создается, но цена добавляется в зависимости от is_price
        overlay = Overlay(self._cell_size, self._cell_size)
        # Размещаем изображения
        for idx, img_model in enumerate(image_models):
            try:
                img = Image.open(img_model.path)
                cell_img, img_box = self._resize_image_to_cell(img)
                # Всегда добавляем оверлей, но с ценой или без в зависимости от is_price
                cell_img = overlay.add_text_overlay(
                    cell_img,
                    img_model,
                    img_box,
                    is_price,
                )
                row = idx // grid_cols
                col = idx % grid_cols
                x = col * (self._cell_size + self._cell_margin)
                y = row * (self._cell_size + self._cell_margin)
                collage.paste(cell_img, (x, y))
            except Exception as e:
                log.exception(f"Ошибка при обработке изображения {img_model.path}: {e}")
                raise
        collage.save(output_path, "JPEG", quality=95)
        log.info(
            "Коллаж сохранён в %s (сетка: %sx%s, изображений: %s)",
            output_path,
            grid_cols,
            grid_rows,
            image_count,
        )
        return output_path
