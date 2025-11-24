import logging

from sqlalchemy import case, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from src.database.connection import db
from src.database.schema.images import ImagesDb
from src.database.schema.products import ProductDb

log = logging.getLogger(__name__)


class ImagesRepository:
    @staticmethod
    @db.with_session
    async def add(session, product_id: int, path: str) -> ImagesDb:
        """Добавляет новое изображение в базу данных.

        Args:
            session: Сессия базы данных
            product_id: ID продукта
            path: Путь к изображению

        Returns:
            Созданное изображение


        """
        log.debug(f"Добавление изображения в БД для продукта ID {product_id}: {path}")
        image = ImagesDb(path=path, product_id=product_id)
        try:
            session.add(image)
            await session.commit()
            log.info(f"Изображение успешно добавлено в БД: {path} (ID: {image.id})")
        except SQLAlchemyError as e:
            log.exception(f"Ошибка при добавлении изображения в БД: {e}")
            await session.rollback()
            raise e
        return image

    @staticmethod
    @db.with_session
    async def get_all(session) -> list[ImagesDb]:
        """Получает все изображения из базы данных.

        Args:
            session: Сессия базы данных

        Returns:
            Список всех изображений

        Raises:
            Exception: При ошибке получения изображений

        """
        log.info("Получение всех изображений из БД")
        try:
            result = await session.execute(select(ImagesDb))
            images = result.scalars().all()
            log.info(f"Получено изображений из БД: {len(images)}")
            return images
        except Exception as e:
            log.exception("Ошибка при получении изображений из БД: %s", e)
            raise e

    @staticmethod
    @db.with_session
    async def get_by_ids_with_products(
        session,
        list_id_images: list[int] | None = None,
        list_id_products: list[int] | None = None,
    ) -> list[ImagesDb] | None:
        """Получает изображения с продуктами по списку ID.

        Args:
            session: Сессия базы данных
            list_id_images: Список ID изображений
            list_id_products: Список ID продуктов

        Returns:
            Список изображений с продуктами или None

        Raises:
            Exception: При ошибке получения изображений

        """
        if list_id_images:
            log.info("Получение изображений из БД по ID: %s", list_id_images)
        elif list_id_products:
            log.info(
                "Получение изображений из БД по ID продуктов: %s",
                list_id_products,
            )
        else:
            log.info("Не переданы ID для поиска изображений в БД")
            return None

        try:
            if list_id_products:
                # Создаем case для сохранения порядка
                order_case = case(
                    {id_val: index for index, id_val in enumerate(list_id_products)},
                    value=ImagesDb.product_id,
                )
                result = await session.execute(
                    select(ImagesDb)
                    .options(
                        joinedload(ImagesDb.product).joinedload(ProductDb.categories),
                    )
                    .where(ImagesDb.product_id.in_(list_id_products))
                    .order_by(order_case),
                )
                images = result.unique().scalars().all()
                log.info(f"Найдено изображений по ID продуктов: {len(images)}")
                return images
            if list_id_images:
                # Создаем case для сохранения порядка
                order_case = case(
                    {id_val: index for index, id_val in enumerate(list_id_images)},
                    value=ImagesDb.id,
                )
                result = await session.execute(
                    select(ImagesDb)
                    .options(
                        joinedload(ImagesDb.product).joinedload(ProductDb.categories),
                    )
                    .where(ImagesDb.id.in_(list_id_images))
                    .order_by(order_case),
                )
                images = result.unique().scalars().all()
                log.info(f"Найдено изображений по ID: {len(images)}")
                return images
            # Если не переданы ID, возвращаем None
            return None
        except Exception as e:
            log.exception("Ошибка при получении изображений из БД: %s", e)
            raise e

    @staticmethod
    @db.with_session
    async def get_all_with_products(session) -> list[ImagesDb]:
        """Получает все изображения с информацией о продуктах из базы данных.

        Args:
            session: Сессия базы данных

        Returns:
            Список изображений с продуктами

        Raises:
            Exception: При ошибке получения изображений

        """
        try:
            result = await session.execute(
                select(ImagesDb).options(
                    joinedload(ImagesDb.product).joinedload(ProductDb.categories),
                ),
            )
            images = result.unique().scalars().all()
            log.debug(f"Получено изображений с продуктами из БД: {len(images)}")
            return images
        except Exception as e:
            log.exception("Ошибка при получении изображений с продуктами из БД: %s", e)
            raise e

    @staticmethod
    @db.with_session
    async def get_by_id(session, image_id: int) -> ImagesDb | None:
        """Получает изображение по ID из базы данных.

        Args:
            session: Сессия базы данных
            image_id: ID изображения

        Returns:
            Изображение или None если не найдено

        Raises:
            Exception: При ошибке получения изображения

        """
        log.info("Получение изображения из БД по ID: %s", image_id)
        try:
            result = await session.execute(
                select(ImagesDb)
                .options(joinedload(ImagesDb.product).joinedload(ProductDb.categories))
                .where(ImagesDb.id == image_id),
            )
            image = result.unique().scalars().first()
            if image:
                log.info(f"Изображение найдено в БД: {image.path}")
            else:
                log.info("Изображение с ID %s не найдено в БД", image_id)
            return image
        except Exception as e:
            log.exception(
                "Ошибка при получении изображения из БД по ID %s: %s",
                image_id,
                e,
            )
            raise

    @staticmethod
    @db.with_session
    async def update(session, image_id: int, path: str):
        """Обновляет изображение в базе данных.

        Args:
            session: Сессия базы данных
            image_id: ID изображения
            path: Новый путь к изображению

        Raises:
            ImageNotFoundError: Если изображение не найдено
            Exception: При ошибке обновления изображения

        """
        log.info("Обновление изображения в БД: ID %s, новый путь %s", image_id, path)
        try:
            result = await session.execute(
                select(ImagesDb).where(ImagesDb.id == image_id),
            )
            image = result.scalars().first()
            if not image:
                log.warning(
                    "Изображение с ID %s не найдено в БД для обновления",
                    image_id,
                )

            old_path = image.path
            image.path = path
            await session.commit()
            log.info("Изображение успешно обновлено в БД: %s -> %s", old_path, path)
        except SQLAlchemyError as e:
            log.exception("Ошибка при обновлении изображения в БД: %s", e)
            await session.rollback()
            raise ValueError from e
