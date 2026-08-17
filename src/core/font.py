from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger(__name__)


class Font:
    """Класс для поиска и хранения пути к шрифту с поддержкой кириллицы."""

    CYRILLIC_FONT_PATTERNS: tuple[str, ...] = (
        "Roboto",
        "Liberation",
        "DejaVu",
        "Noto",
        "Ubuntu",
        "OpenSans",
        "PT",
        "Fira",
        "Source",
        "Droid",
        "Arial",
        "Helvetica",
    )
    FONT_EXTENSIONS: tuple[str, ...] = ("ttf", "otf")
    FONT_DIRS: tuple[Path, ...] = (
        Path("/usr/share/fonts/truetype/"),
        Path("/usr/share/fonts/TTF/"),
        Path("/usr/share/fonts/opentype/"),
        Path("/usr/share/fonts/type1/"),
        Path("/usr/share/fonts/"),
    )

    def __init__(self) -> None:
        self._font: str = self._find_font()

    def get_font(self) -> str:
        """Возвращает путь к найденному шрифту."""
        return self._font

    def get_font_bold(self) -> str | None:
        """Возвращает путь к жирному варианту шрифта или None."""
        if not self._font:
            return None

        font_path = Path(self._font)
        font_dir = font_path.parent
        font_name = font_path.stem

        bold_candidates = [
            font_dir / f"{font_name}-Bold.ttf",
            font_dir / f"{font_name}-Bold.otf",
            font_dir / f"{font_name}Bd.ttf",
            font_dir / f"{font_name}Bd.otf",
            font_dir / f"{font_name}_Bold.ttf",
        ]

        for candidate in bold_candidates:
            if candidate.exists():
                return str(candidate)

        for ext in self.FONT_EXTENSIONS:
            for pattern in self.CYRILLIC_FONT_PATTERNS:
                bold_fonts = list(font_dir.glob(f"**/*{pattern}*Bold*.{ext}"))
                if bold_fonts:
                    return str(bold_fonts[0])

        return None

    def _find_font(self) -> str:
        """Ищет первый подходящий шрифт с поддержкой кириллицы."""
        for font_dir in self.FONT_DIRS:
            if not font_dir.exists():
                continue
            for pattern in self.CYRILLIC_FONT_PATTERNS:
                for ext in self.FONT_EXTENSIONS:
                    fonts = list(font_dir.glob(f"**/*{pattern}*.{ext}"))
                    regular_fonts = [
                        str(f)
                        for f in fonts
                        if "Regular" in f.name or "regular" in f.name
                    ]
                    if regular_fonts:
                        log.info(
                            "Найден шрифт с поддержкой кириллицы: %s", regular_fonts[0]
                        )
                        return regular_fonts[0]
                    if fonts:
                        log.info("Найден шрифт с поддержкой кириллицы: %s", fonts[0])
                        return str(fonts[0])
        log.critical("Не найден шрифт с поддержкой кириллицы в /usr/share/fonts/")
        raise ValueError("Нужный шрифт не найден")
