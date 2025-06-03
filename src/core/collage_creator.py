from typing import List
from PIL import Image, ImageDraw
import logging
from src.schema.image_info import ImageInfo
from src.core.overlay import Overlay


class CollageCreator:
    """Класс для создания коллажа из изображений с текстом"""

    def __init__(self):
        self._cell_img_width = 1200
        self._cell_img_height = 1200
        self._cell_margin = 60
        self._grid_cols = 3
        self._grid_rows = 3
        self._background_color = (53, 3, 61)
        self._border_color = (126, 100, 126)
        self._border_thickness = 30
        self._overlay = Overlay(self._cell_img_width, self._cell_img_height)

    def _resize_image_to_cell(self, img: Image.Image) -> Image.Image:
        scale = max(
            self._cell_img_width / img.width, self._cell_img_height / img.height
        )
        new_width = int(img.width * scale)
        new_height = int(img.height * scale)
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        x_offset = max(0, (new_width - self._cell_img_width) // 2)
        y_offset = max(0, (new_height - self._cell_img_height) // 2)
        cropped = resized.crop((
            x_offset,
            y_offset,
            x_offset + self._cell_img_width,
            y_offset + self._cell_img_height,
        ))
        return cropped

    def create(self, images: List[ImageInfo], output_path: str) -> str:
        if len(images) != (self._grid_cols * self._grid_rows):
            raise ValueError(f"Требуется ровно {(self._grid_cols * self._grid_rows)}")
        collage_width = (
            self._grid_cols * self._cell_img_width
            + (self._grid_cols + 1) * self._cell_margin
        )
        collage_height = (
            self._grid_rows * self._cell_img_height
            + (self._grid_rows + 1) * self._cell_margin
        )
        collage = Image.new(
            "RGB", (collage_width, collage_height), self._background_color
        )
        draw = ImageDraw.Draw(collage)
        for i in range(self._border_thickness):
            draw.rectangle(
                [(i, i), (collage_width - 1 - i, collage_height - 1 - i)],
                outline=self._border_color,
            )
        for idx, img_info in enumerate(images):
            try:
                img = Image.open(img_info.path)
                cell_img = self._resize_image_to_cell(img)
                cell_img = self._overlay.add_text_overlay(cell_img, img_info)
                row = idx // self._grid_cols
                col = idx % self._grid_cols
                x = col * self._cell_img_width + (col + 1) * self._cell_margin
                y = row * self._cell_img_height + (row + 1) * self._cell_margin
                collage.paste(cell_img, (x, y))
            except Exception as e:
                logging.error(f"Ошибка при обработке изображения {img_info.path}: {e}")
                raise
        collage.save(output_path, "JPEG", quality=95)
        logging.info(f"Коллаж сохранён в {output_path}")
        return output_path
