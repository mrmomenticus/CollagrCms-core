import logging
from pathlib import Path
from typing import List

from src.utils.exeptions import (
    NotFound
)


class Font:
    """
    Класс для поиска и хранения пути к шрифту с поддержкой кириллицы.
    """

    CYRILLIC_FONT_PATTERNS: List[str] = [
        "Liberation",
        "DejaVu",
        "Noto",
        "Ubuntu",
        "Roboto",
        "OpenSans",
        "PT",
        "Fira",
        "Source",
        "Droid",
        "Arial",
        "Helvetica",
    ]
    FONT_EXTENSIONS: List[str] = ["ttf", "otf", "TTF", "OTF"]
    FONT_DIRS: List[Path] = [
        Path("/usr/share/fonts/truetype/"),
        Path("/usr/share/fonts/TTF/"),
        Path("/usr/share/fonts/opentype/"),
        Path("/usr/share/fonts/type1/"),
        Path("/usr/share/fonts/"),
    ]

    def __init__(self) -> None:
        self._font: str = self._find_font()

    def get_font(self) -> str:
        """
        Возвращает путь к найденному шрифту.
        """
        return self._font

    def _find_font(self) -> str:
        """
        Ищет первый подходящий шрифт с поддержкой кириллицы.
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
                        logging.info(
                            f"Найден шрифт с поддержкой кириллицы: {font_path}"
                        )
                        return font_path
                    elif fonts:
                        font_path = str(fonts[0])
                        logging.info(
                            f"Найден шрифт с поддержкой кириллицы: {font_path}"
                        )
                        return font_path
        logging.critical(
            "Не найден шрифт с поддержкой кириллицы в /usr/share/fonts/, используется встроенный шрифт"
        )
        raise NotFound("Font with Cyrillic support not found.")
