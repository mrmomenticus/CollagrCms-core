import os
import glob
from typing import List
from PIL import Image, ImageDraw, ImageFont
import logging
from src.core.image import Image
from src.core.font import Font


class CollageCreator:
    """Класс для создания коллажа из изображений с текстом"""

    def __init__(self):
        self.cell_img_width = 1200
        self.cell_img_height = 1200
        self.cell_margin = 60
        self.grid_cols = 3
        self.grid_rows = 3
        self.background_color = (53, 3, 61)
        self.border_color = (126, 100, 126)
        self.border_thickness = 30
        self.overlay_height = 220
        self.overlay_alpha = 128
        self.text_margin_x = 30
        self.price_font_size = 60
        self.desc_font_size = 48
        self.price_color = (65, 65, 65)
        self.desc_color = (40, 40, 40)
        self.font_family = self.Font()


    def _get_font_object(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        if self.font_family:
            try:
                if bold and self.font_family.endswith("-Regular.ttf"):
                    bold_font = self.font_family.replace("-Regular.ttf", "-Bold.ttf")
                    if os.path.exists(bold_font):
                        return ImageFont.truetype(bold_font, size)
                return ImageFont.truetype(self.font_family, size)
            except Exception as e:
                logging.warning(f"Ошибка загрузки шрифта: {e}")
        return ImageFont.load_default()

    def _resize_image_to_cell(self, img: Image.Image) -> Image.Image:
        scale = max(self.cell_img_width / img.width, self.cell_img_height / img.height)
        new_width = int(img.width * scale)
        new_height = int(img.height * scale)
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        x_offset = max(0, (new_width - self.cell_img_width) // 2)
        y_offset = max(0, (new_height - self.cell_img_height) // 2)
        cropped = resized.crop((
            x_offset,
            y_offset,
            x_offset + self.cell_img_width,
            y_offset + self.cell_img_height,
        ))
        return cropped

    def _add_text_overlay(
        self, img: Image.Image, price: str, description: str
    ) -> Image.Image:
        img_with_overlay = img.copy()
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        overlay_y = self.cell_img_height - self.overlay_height
        draw_overlay.rectangle(
            [(0, overlay_y), (self.cell_img_width, self.cell_img_height)],
            fill=(255, 255, 255, self.overlay_alpha),
        )
        img_with_overlay = Image.alpha_composite(img.convert("RGBA"), overlay).convert(
            "RGB"
        )
        draw = ImageDraw.Draw(img_with_overlay)
        price_font = self._get_font_object(self.price_font_size, bold=True)
        desc_font = self._get_font_object(self.desc_font_size)
        price_y = self.cell_img_height - self.overlay_height + 10
        draw.text(
            (self.text_margin_x, price_y), price, font=price_font, fill=self.price_color
        )
        if len(description) > 120:
            logging.warning(f"Описание слишком длинное, обрезано: {description[:20]}...")
            description = description[:120]
        desc_y = price_y + self.price_font_size + 10
        self._draw_multiline_text(
            draw,
            description,
            (self.text_margin_x, desc_y),
            desc_font,
            self.desc_color,
            max_width=self.cell_img_width - 2 * self.text_margin_x,
            line_spacing=7,
        )
        return img_with_overlay

    def _draw_multiline_text(
        self,
        draw: ImageDraw.Draw,
        text: str,
        position,
        font,
        color,
        max_width,
        line_spacing=5,
    ):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            if line_width > max_width and current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                current_line.append(word)
        if current_line:
            lines.append(" ".join(current_line))
        x, y = position
        for line in lines:
            draw.text((x, y), line, font=font, fill=color)
            bbox = draw.textbbox((0, 0), line, font=font)
            line_height = bbox[3] - bbox[1]
            y += line_height + line_spacing

    def create(self, images: List[Image], output_path: str) -> str:
        if len(images) != 9:
            raise ValueError("Требуется ровно 9 элементов для коллажа 3x3")
        collage_width = (
            self.grid_cols * self.cell_img_width
            + (self.grid_cols + 1) * self.cell_margin
        )
        collage_height = (
            self.grid_rows * self.cell_img_height
            + (self.grid_rows + 1) * self.cell_margin
        )
        collage = Image.new(
            "RGB", (collage_width, collage_height), self.background_color
        )
        draw = ImageDraw.Draw(collage)
        for i in range(self.border_thickness):
            draw.rectangle(
                [(i, i), (collage_width - 1 - i, collage_height - 1 - i)],
                outline=self.border_color,
            )
        for idx, img_info in enumerate(images):
            try:
                img = Image.open(img_info.path)
                cell_img = self._resize_image_to_cell(img)
                cell_img = self._add_text_overlay(
                    cell_img, img_info.price, img_info.description
                )
                row = idx // self.grid_cols
                col = idx % self.grid_cols
                x = col * self.cell_img_width + (col + 1) * self.cell_margin
                y = row * self.cell_img_height + (row + 1) * self.cell_margin
                collage.paste(cell_img, (x, y))
            except Exception as e:
                logging.error(f"Ошибка при обработке изображения {img_info.path}: {e}")
                raise
        collage.save(output_path, "JPEG", quality=95)
        logging.info(f"Коллаж сохранён в {output_path}")
        return output_path
