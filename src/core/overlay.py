import logging
from PIL import Image, ImageDraw
from src.core.font import Font
from src.models.models import ImageWithProduct


class Overlay:
    def __init__(self, collag_width: int, collaw_height: int):
        self._collag_width = collag_width
        self._collag_height = collaw_height
        self._overlay_height = 220
        self._overlay_alpha = 128
        self._text_margin_x = 30
        self._max_size_text = 140
        self._price_font_size = 60
        self._desc_font_size = 48
        self._price_color = (65, 65, 65)
        self._desc_color = (40, 40, 40)
        self._font = Font()

    def add_text_overlay(
        self, img: Image.Image, img_model: ImageWithProduct
    ) -> Image.Image:
        img_with_overlay = img.copy()
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        overlay_y = self._collag_height - self._overlay_height
        draw_overlay.rectangle(
            [(0, overlay_y), (self._collag_width, self._collag_height)],
            fill=(255, 255, 255, self._overlay_alpha),
        )
        img_with_overlay = Image.alpha_composite(img.convert("RGBA"), overlay).convert(
            "RGB"
        )
        draw = ImageDraw.Draw(img_with_overlay)
        price_font = self._font.get_font_object(self._price_font_size, bold=True)
        desc_font = self._font.get_font_object(self._desc_font_size)
        price_y = self._collag_height - self._overlay_height + 10
        draw.text(
            (self._text_margin_x, price_y),
            str(img_model.product.price) + " ₽",
            font=price_font,
            fill=self._price_color,
        )
        if len(img_model.product.description) > self._max_size_text:
            logging.warning(f"Описание слишком длинное, обрезано: {img_model.path}")
        description = str(img_model.product.description)[: self._max_size_text]
        desc_y = price_y + self._price_font_size + 10
        self._draw_multiline_text(
            draw,
            description,
            (self._text_margin_x, desc_y),
            desc_font,
            self._desc_color,
            max_width=self._collag_width - 2 * self._text_margin_x,
            line_spacing=7,
        )
        return img_with_overlay

    def _draw_multiline_text(
        self,
        draw: ImageDraw.Draw,  # type: ignore
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
