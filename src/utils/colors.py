"""Color utilities."""

from __future__ import annotations


def parse_hex_color(hex_color: str) -> tuple[int, int, int]:
    """Парсит hex цвет в RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 6:
        return (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16),
        )
    return (53, 3, 61)
