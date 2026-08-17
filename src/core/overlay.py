from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw, ImageFont

from src.core.font import Font
from src.utils.colors import parse_hex_color

if TYPE_CHECKING:
    from src.models.models import CaptionStyle, ImageWithProduct

log = logging.getLogger(__name__)


class Overlay:
    __slots__ = ("_font", "_price_color", "_text_margin_x")

    def __init__(self) -> None:
        self._text_margin_x = 30
        self._price_color = (30, 30, 30)
        self._font = Font()

    def add_text_overlay(
        self,
        img: Image.Image,
        img_model: ImageWithProduct,
        _img_box: tuple[int, int, int, int] | None = None,
        is_price: bool = True,
        captions: list[str] | None = None,
        caption_style: CaptionStyle | None = None,
        caption_opacity: int = 80,
    ) -> Image.Image:
        """Добавляет текстовый оверлей на изображение."""
        show_captions = captions if captions is not None else []
        if not show_captions:
            return img

        has_price = "price" in show_captions and is_price
        has_name = "name" in show_captions
        has_description = "description" in show_captions
        has_category = "category" in show_captions

        if not (has_price or has_name or has_description or has_category):
            return img

        width, height = img.size
        margin_x = self._text_margin_x
        caption_padding = 4
        base_font_size = (
            caption_style.font_size if caption_style and caption_style.font_size else 13
        )
        font_size = base_font_size + caption_padding

        total_caption_lines = sum(
            1
            for c in show_captions
            if (
                (c == "price" and is_price)
                or c == "name"
                or c == "description"
                or c == "category"
            )
        )
        caption_area_height = total_caption_lines * font_size + caption_padding * 2
        overlay_top = height - caption_area_height
        overlay_alpha = 255 * caption_opacity // 100

        bg_color_rgb = (255, 255, 255)
        if caption_style and caption_style.background:
            bg_color_rgb = parse_hex_color(caption_style.background)

        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_overlay.rectangle(
            [(0, overlay_top), (width, height)],
            fill=(*bg_color_rgb, overlay_alpha),
        )
        img_with_overlay = Image.alpha_composite(img.convert("RGBA"), overlay).convert(
            "RGB"
        )
        draw = ImageDraw.Draw(img_with_overlay)

        text_color = self._price_color
        if caption_style and caption_style.color:
            text_color = parse_hex_color(caption_style.color)

        try:
            font = ImageFont.truetype(self._font.get_font(), base_font_size)
        except Exception:
            font = ImageFont.load_default()

        text_y = overlay_top + caption_padding

        for idx, caption in enumerate(show_captions):
            match caption, is_price:
                case ("price", True):
                    text = f"{img_model.product.price} ₽"
                case ("name", _):
                    text = str(img_model.product.name)[:30]
                case ("description", _):
                    text = str(img_model.product.description)[:50]
                case ("category", _):
                    text = (
                        img_model.product.category_names[0]
                        if img_model.product.category_names
                        else ""
                    )
                case _:
                    continue

            if text:
                text_font = font
                if idx == 0:
                    try:
                        bold_font_path = self._font.get_font_bold()
                        if bold_font_path:
                            text_font = ImageFont.truetype(
                                bold_font_path, base_font_size
                            )
                    except Exception:
                        log.debug("Не удалось загрузить жирный шрифт")
                draw.text((margin_x, text_y), text, font=text_font, fill=text_color)
                text_y += font_size + caption_padding

        return img_with_overlay
