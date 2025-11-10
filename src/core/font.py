import logging
from pathlib import Path

from PIL import ImageFont

log = logging.getLogger(__name__)


class Font:
    """Класс для поиска и хранения пути к шрифту с поддержкой кириллицы."""

    CYRILLIC_FONT_PATTERNS: list[str] = [  # noqa: RUF012
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
    ]
    FONT_EXTENSIONS: list[str] = ["ttf", "otf", "TTF", "OTF"]  # noqa: RUF012
    FONT_DIRS: list[Path] = [  # noqa: RUF012
        Path("/usr/share/fonts/truetype/"),
        Path("/usr/share/fonts/TTF/"),
        Path("/usr/share/fonts/opentype/"),
        Path("/usr/share/fonts/type1/"),
        Path("/usr/share/fonts/"),
    ]

    def __init__(self) -> None:
        self._font: str = self._find_font()

    def get_font(self) -> str:
        """Возвращает путь к найденному шрифту."""
        return self._font

    def _find_font(self) -> str:
        """Ищет первый подходящий шрифт с поддержкой кириллицы.

        Сначала ищет варианты с 'Regular' в имени файла.
        """
        for font_dir in self.FONT_DIRS:
            if not font_dir.exists():
                continue
            for pattern in self.CYRILLIC_FONT_PATTERNS:
                for ext in self.FONT_EXTENSIONS:
                    # Пример: *DejaVu*.ttf
                    glob_pattern = f"**/*{pattern}*.{ext}"
                    fonts = list(font_dir.glob(glob_pattern))
                    regular_fonts = [
                        str(f)
                        for f in fonts
                        if "Regular" in f.name or "regular" in f.name
                    ]
                    if regular_fonts:
                        font_path = regular_fonts[0]
                        log.info(
                            "Найден шрифт с поддержкой кириллицы: %s",
                            font_path,
                        )
                        return font_path
                    if fonts:
                        font_path = str(fonts[0])
                        log.info(
                            "Найден шрифт с поддержкой кириллицы: %s",
                            font_path,
                        )
                        return font_path
        log.critical(
            "Не найден шрифт с поддержкой кириллицы в /usr/share/fonts/, используется встроенный шрифт",
        )
        raise ValueError("Нужный шрифт не найден")

    def get_font_object(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        if self._font:
            try:
                if bold and self._font.endswith("-Regular.ttf"):
                    bold_font = self._font.replace("-Regular.ttf", "-Bold.ttf")
                    if Path(bold_font).exists():
                        return ImageFont.truetype(bold_font, size)
                return ImageFont.truetype(self._font, size)
            except Exception as e:
                log.warning("Ошибка загрузки шрифта: %s", e)
        raise ValueError("Не получилось загрузить шрифт")
