import textwrap

from PIL import Image, ImageDraw, ImageFont

from src.core.font import Font
from src.models.models import ImageWithProduct


class Overlay:
    def __init__(self, collag_width: int, collaw_height: int):
        self._collag_width = collag_width
        self._collag_height = collaw_height
        self._overlay_height_ratio = 0.25  # overlay = 1/4 высоты изображения
        self._overlay_alpha = 128
        self._text_margin_x = 30
        self._price_color = (30, 30, 30)  # Темнее
        self._desc_color = (20, 20, 20)  # Темнее
        self._price_font_min = 20  # минимальный размер шрифта цены
        self._desc_font_min = 10  # минимальный размер шрифта описания
        self._price_font_overlay_ratio = 0.3  # цена: половина overlay
        self._desc_font_overlay_ratio = 0.20  # описание: треть overlay
        self._max_description_length = 50
        self._max_chars_per_line = 25
        self._line_spacing = 2
        self._font = Font()

    def _find_max_font_size(
        self,
        draw,
        text,
        font_path,
        max_width,
        max_height,
        bold=False,
        min_size=10,
        max_size=80,
        wrap_width=25,
        line_spacing=7,
    ):
        left, right = min_size, max_size
        best_size = min_size
        while left <= right:
            mid = (left + right) // 2
            try:
                font = ImageFont.truetype(font_path, mid)
            except Exception:
                break
            # Для описания — переносим по wrap_width
            lines = textwrap.wrap(text, width=wrap_width)
            total_height = 0
            max_line_width = 0
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_height = bbox[3] - bbox[1]
                line_width = bbox[2] - bbox[0]
                total_height += line_height + line_spacing
                max_line_width = max(max_line_width, line_width)
            if (
                total_height - line_spacing <= max_height
                and max_line_width <= max_width
            ):
                best_size = mid
                left = mid + 1
            else:
                right = mid - 1
        return best_size

    def _get_overlay_box(self, img_size, img_box=None):
        width, height = img_size
        overlay_height = int(height * self._overlay_height_ratio)
        if img_box is not None:
            x_offset, y_offset, img_w, img_h = img_box
            overlay_top = y_offset + img_h - min(overlay_height, img_h)
            overlay_bottom = y_offset + img_h
        else:
            overlay_top = height - min(overlay_height, height)
            overlay_bottom = height
        return overlay_top, overlay_bottom, overlay_height, width, height

    def _get_fonts(self, overlay_height):
        font_path = self._font.get_font()
        price_font_size = max(
            self._price_font_min, int(overlay_height * self._price_font_overlay_ratio),
        )
        desc_font_size = max(
            self._desc_font_min, int(overlay_height * self._desc_font_overlay_ratio),
        )
        price_font = ImageFont.truetype(font_path, price_font_size)
        desc_font = ImageFont.truetype(font_path, desc_font_size)
        return price_font, desc_font, price_font_size

    def add_text_overlay(
        self, img: Image.Image, img_model: ImageWithProduct, img_box=None, is_price=True,
    ) -> Image.Image:
        img_with_overlay = img.copy()
        overlay_top, overlay_bottom, overlay_height, width, height = (
            self._get_overlay_box(img.size, img_box)
        )
        margin_x = self._text_margin_x
        overlay_alpha = self._overlay_alpha
        # Overlay
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_overlay.rectangle(
            [(0, overlay_top), (width, overlay_bottom)],
            fill=(255, 255, 255, overlay_alpha),
        )
        img_with_overlay = Image.alpha_composite(img.convert("RGBA"), overlay).convert(
            "RGB",
        )
        draw = ImageDraw.Draw(img_with_overlay)
        # Fonts
        price_font, desc_font, price_font_size = self._get_fonts(overlay_height)
        # Цена (если is_price=True)
        price_y = overlay_top + 10
        if is_price:
            price_text = str(img_model.product.price) + " ₽"
            draw.text(
                (margin_x, price_y),
                price_text,
                font=price_font,
                fill=self._price_color,
            )
        # Описание
        desc_max_width = width - 2 * margin_x
        desc_y = price_y + (price_font_size + 10 if is_price else 0)
        desc_max_height = overlay_bottom - desc_y - 10
        description = str(img_model.product.description)[: self._max_description_length]
        fitted_text = self._fit_text_to_overlay(
            draw,
            description,
            desc_font,
            desc_max_width,
            desc_max_height,
            line_spacing=self._line_spacing,
        )
        self._draw_multiline_text(
            draw,
            fitted_text,
            (margin_x, desc_y),
            desc_font,
            self._desc_color,
            max_width=desc_max_width,
            line_spacing=self._line_spacing,
        )
        return img_with_overlay

    def _fit_text_to_overlay(
        self, draw, text, font, max_width, max_height, line_spacing=7,
    ):
        text = text[: self._max_description_length]
        lines = textwrap.wrap(
            text,
            width=self._max_chars_per_line,
            break_long_words=True,
            drop_whitespace=True,
        )
        # Ограничиваем до 2 строк
        if len(lines) > 2:
            lines = lines[:2]
            # Добавляем троеточие к последней строке, если текст был обрезан
            if not lines[1].endswith("..."):
                # Обрезаем, чтобы влезло троеточие по ширине
                for cut in range(len(lines[1]), 0, -1):
                    test_line = lines[1][:cut] + "..."
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    if bbox[2] - bbox[0] <= max_width:
                        lines[1] = test_line
                        break
        return "\n".join(lines)

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
        x, y = position
        for line in text.split("\n"):
            if not line.strip():
                y += font.size + line_spacing
                continue
            draw.text((x, y), line, font=font, fill=color)
            bbox = draw.textbbox((0, 0), line, font=font)
            y += bbox[3] - bbox[1] + line_spacing
