import logging

from sqlalchemy import select
from src.database.schema.images import ImagesDb
from src.database.schema.products import ProductDb
from src.database.connection import db
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import joinedload


class ImagesRepository:
    @staticmethod
    @db.with_session
    async def add(session, product_id: int, path: str) -> ImagesDb:
        """
        Добавляет новое изображение в базу данных

        Args:
            session: Сессия базы данных
            product_id: ID продукта
            path: Путь к изображению

        Returns:
            Созданное изображение

        Raises:
            Exception: При ошибке создания изображения
        """
        logging.info(
            f"Добавление изображения в БД для продукта ID {product_id}: {path}"
        )
        image = ImagesDb()
        image.path = path
        image.product_id = product_id
        try:
            session.add(image)
            await session.commit()
            logging.info(f"Изображение успешно добавлено в БД: {path} (ID: {image.id})")
        except Exception as e:
            logging.error(f"Ошибка при добавлении изображения в БД: {e}")
            await session.rollback()
            raise e
        return image

    @staticmethod
    @db.with_session
    async def get_all(session) -> list[ImagesDb]:
        """
        Получает все изображения из базы данных

        Args:
            session: Сессия базы данных

        Returns:
            Список всех изображений

        Raises:
            Exception: При ошибке получения изображений
        """
        logging.info("Получение всех изображений из БД")
        try:
            result = await session.execute(select(ImagesDb))
            images = result.scalars().all()
            logging.info(f"Получено изображений из БД: {len(images)}")
            return images
        except Exception as e:
            logging.error(f"Ошибка при получении изображений из БД: {e}")
            raise e

    @staticmethod
    @db.with_session
    async def get_by_ids_with_products(
        session,
        list_id_images: list[int] | None = None,
        list_id_products: list[int] | None = None,
    ) -> list[ImagesDb] | None:
        """
        Получает изображения с продуктами по списку ID

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
            logging.info(f"Получение изображений из БД по ID: {list_id_images}")
        elif list_id_products:
            logging.info(
                f"Получение изображений из БД по ID продуктов: {list_id_products}"
            )
        else:
            logging.info("Не переданы ID для поиска изображений в БД")
            return None

        try:
            if list_id_products:
                result = await session.execute(
                    select(ImagesDb)
                    .options(
                        joinedload(ImagesDb.product).joinedload(ProductDb.category)
                    )
                    .where(ImagesDb.product_id.in_(list_id_products))
                )
                images = result.scalars().all()
                logging.info(f"Найдено изображений по ID продуктов: {len(images)}")
                return images
            if list_id_images:
                result = await session.execute(
                    select(ImagesDb)
                    .options(
                        joinedload(ImagesDb.product).joinedload(ProductDb.category)
                    )
                    .where(ImagesDb.id.in_(list_id_images))
                )
                images = result.scalars().all()
                logging.info(f"Найдено изображений по ID: {len(images)}")
                return images
            # Если не переданы ID, возвращаем None
            return None
        except Exception as e:
            logging.error(f"Ошибка при получении изображений из БД: {e}")
            raise e

    @staticmethod
    @db.with_session
    async def get_all_with_products(session) -> list[ImagesDb]:
        """
        Получает все изображения с информацией о продуктах из базы данных

        Args:
            session: Сессия базы данных

        Returns:
            Список изображений с продуктами

        Raises:
            Exception: При ошибке получения изображений
        """
        logging.info("Получение всех изображений с продуктами из БД")
        try:
            result = await session.execute(
                select(ImagesDb).options(
                    joinedload(ImagesDb.product).joinedload(ProductDb.category)
                )
            )
            images = result.scalars().all()
            logging.info(f"Получено изображений с продуктами из БД: {len(images)}")
            return images
        except Exception as e:
            logging.error(f"Ошибка при получении изображений с продуктами из БД: {e}")
            raise

    @staticmethod
    @db.with_session
    async def get_by_id(session, image_id: int) -> ImagesDb | None:
        """
        Получает изображение по ID из базы данных

        Args:
            session: Сессия базы данных
            image_id: ID изображения

        Returns:
            Изображение или None если не найдено

        Raises:
            Exception: При ошибке получения изображения
        """
        logging.info(f"Получение изображения из БД по ID: {image_id}")
        try:
            result = await session.execute(
                select(ImagesDb)
                .options(joinedload(ImagesDb.product).joinedload(ProductDb.category))
                .where(ImagesDb.id == image_id)
            )
            image = result.scalars().first()
            if image:
                logging.info(f"Изображение найдено в БД: {image.path}")
            else:
                logging.info(f"Изображение с ID {image_id} не найдено в БД")
            return image
        except Exception as e:
            logging.error(
                f"Ошибка при получении изображения из БД по ID {image_id}: {e}"
            )
            raise

    @staticmethod
    @db.with_session
    async def update(session, image_id: int, path: str):
        """
        Обновляет изображение в базе данных

        Args:
            session: Сессия базы данных
            image_id: ID изображения
            path: Новый путь к изображению

        Raises:
            ImageNotFoundError: Если изображение не найдено
            Exception: При ошибке обновления изображения
        """
        logging.info(f"Обновление изображения в БД: ID {image_id}, новый путь {path}")
        try:
            result = await session.execute(
                select(ImagesDb).where(ImagesDb.id == image_id)
            )
            image = result.scalars().first()
            if not image:
                logging.warning(
                    f"Изображение с ID {image_id} не найдено в БД для обновления"
                )
                raise NoResultFound(f"Image with ID {image_id} not found")

            old_path = image.path
            image.path = path
            await session.commit()
            logging.info(f"Изображение успешно обновлено в БД: {old_path} -> {path}")
        except NoResultFound:
            raise
        except Exception as e:
            logging.error(f"Ошибка при обновлении изображения в БД: {e}")
            await session.rollback()
            raise
