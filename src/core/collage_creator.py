import logging
import math

from PIL import Image, ImageDraw

from src.core.overlay import Overlay
from src.models.models import (
    CollageLayout,
    CollageSettings,
    ImageWithProduct,
)

log = logging.getLogger(__name__)


def _parse_hex_color(hex_color: str) -> tuple[int, int, int]:
    """Парсит hex цвет в RGB tuple.

    Args:
        hex_color: Hex цвет в формате '#RRGGBB'

    Returns:
        RGB tuple (R, G, B)


    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 6:
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return (53, 3, 61)


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
            image_models: Список изображений с продуктами (от 1 до 16)
            output_path: Путь для сохранения коллажа
            is_price: Флаг, указывающий, нужно ли добавлять цену на оверлей
        Returns:
            Путь к созданному коллажу

        """
        image_count = len(image_models)
        if image_count < 1 or image_count > 16:
            raise ValueError(
                f"Количество изображений должно быть от 1 до 16, получено: {image_count}",
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

    def create_with_layout(
        self,
        image_models: list[ImageWithProduct],
        layout: CollageLayout,
        settings: CollageSettings,
        output_path: str,
    ) -> str:
        """Создает коллаж с пользовательским макетом.

        Args:
            image_models: Список изображений с продуктами
            layout: Макет коллажа с ячейками
            settings: Настройки отображения
            output_path: Путь для сохранения коллажа

        Returns:
            Путь к созданному коллажу

        """
        image_count = len(image_models)
        if image_count < 1 or image_count > 16:
            raise ValueError(
                f"Количество изображений должно быть от 1 до 16, получено: {image_count}",
            )

        # Получаем размеры и цвет холста из макета
        canvas_width = layout.canvas.width
        canvas_height = layout.canvas.height
        bg_color = _parse_hex_color(layout.canvas.background)

        # Создаем изображение
        collage = Image.new(
            "RGB",
            (canvas_width, canvas_height),
            bg_color,
        )
        draw = ImageDraw.Draw(collage)

        # Рисуем рамку
        for i in range(self._border_thickness):
            draw.rectangle(
                [(i, i), (canvas_width - 1 - i, canvas_height - 1 - i)],
                outline=self._border_color,
            )

        # Создаем словарь изображений по ID для быстрого доступа
        images_by_id = {img.id: img for img in image_models}

        # Обрабатываем ячейки макета
        for cell in layout.cells:
            try:
                if cell.type == "image":
                    # Находим изображение по productId или по индексу ячейки
                    img_model = None
                    if cell.product_id:
                        # Ищем по productId
                        img_model = images_by_id.get(cell.product_id)
                    elif cell.index < len(image_models):
                        # Ищем по индексу
                        img_model = image_models[cell.index]

                    if img_model:
                        img = Image.open(img_model.path)

                        # Масштабируем изображение под размер ячейки
                        cell_width = int(cell.size.width)
                        cell_height = int(cell.size.height)
                        img = img.resize(
                            (cell_width, cell_height), Image.Resampling.LANCZOS
                        )

                        # Поворачиваем изображение
                        if cell.rotation != 0:
                            img = img.rotate(
                                cell.rotation,
                                expand=True,
                                resample=Image.Resampling.BICUBIC,
                            )

                        # Создаем оверлей для ячейки
                        overlay = Overlay(cell_width, cell_height)

                        # Получаем подписи из ячейки или используем дефолтные
                        captions = (
                            cell.captions if cell.captions is not None else ["price"]
                        )

                        # Пропускаем overlay если нет подписей
                        if captions:
                            caption_style = cell.caption_style
                            caption_opacity = settings.caption_opacity

                            img = overlay.add_text_overlay(
                                img,
                                img_model,
                                (0, 0, cell_width, cell_height),
                                settings.is_price,
                                captions,
                                caption_style,
                                caption_opacity,
                            )

                        # Вставляем изображение на холст
                        x = int(cell.position.x)
                        y = int(cell.position.y)
                        collage.paste(img, (x, y))

                elif cell.type == "text":
                    # Рисуем текстовую ячейку
                    if cell.text_config:
                        text_type = cell.text_config.type
                        font_size = cell.text_config.font_size
                        color = cell.text_config.color

                        # Получаем текст для отображения
                        text = ""
                        img_model = None
                        if cell.product_id:
                            # Ищем по productId
                            img_model = images_by_id.get(cell.product_id)
                        elif cell.index < len(image_models):
                            # Ищем по индексу
                            img_model = image_models[cell.index]

                        if img_model:
                            if text_type == "price" and settings.is_price:
                                text = f"{img_model.product.price} ₽"
                            elif text_type == "name" and settings.is_name:
                                text = img_model.product.name
                            elif text_type == "category" and settings.is_category:
                                text = ", ".join(img_model.product.category_names)
                            elif text_type == "description" and settings.is_description:
                                text = img_model.product.description

                        if text:
                            # Рисуем текст
                            from PIL import ImageFont

                            try:
                                font = ImageFont.truetype(
                                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                                    font_size,
                                )
                            except Exception:
                                font = ImageFont.load_default()

                            # Вычисляем размер текста для центрирования
                            bbox = draw.textbbox((0, 0), text, font=font)
                            text_width = bbox[2] - bbox[0]
                            text_height = bbox[3] - bbox[1]

                            # Центрируем текст в ячейке
                            x = (
                                int(cell.position.x)
                                + (int(cell.size.width) - text_width) // 2
                            )
                            y = (
                                int(cell.position.y)
                                + (int(cell.size.height) - text_height) // 2
                            )

                            draw.text(
                                (x, y),
                                text,
                                fill=color,
                                font=font,
                            )

            except Exception as e:
                log.exception(f"Ошибка при обработке ячейки {cell.id}: {e}")
                raise

        collage.save(output_path, "JPEG", quality=95)
        log.info(
            "Коллаж с макетом сохранён в %s (размер: %sx%s, ячеек: %s)",
            output_path,
            canvas_width,
            canvas_height,
            len(layout.cells),
        )
        return output_path
