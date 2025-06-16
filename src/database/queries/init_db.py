import logging
from typing import Set

from src.database.queries.base import BaseQueries


class InitDatabase(BaseQueries):
    def __init__(self):
        super().__init__()  # Инициализируем BaseQueries
        self.schema_filename = "init.sql"  # Имя файла в sql_dir

    async def get_existing_tables(self):
        """Получение списка существующих таблиц через методы BaseQueries"""
        result = await self.execute_query(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            """,
        )
        return {row[0] for row in result}

    async def check_tables(self) -> bool:
        """Проверка существования таблиц без прямого доступа к подключению"""
        existing_tables = await self.get_existing_tables()
        return len(existing_tables) > 0

    async def create_schema(self):
        """Создание схемы БД с использованием методов BaseQueries"""
        try:
            # Используем существующий метод для выполнения SQL из файла
            await self.execute_sql_file(self.schema_filename, fetch=False)
            logging.info("Схема базы данных успешно создана")
        except FileNotFoundError as e:
            logging.error(f"Схема базы данных не найдена: {self.schema_filename}")
            raise
        except Exception as e:
            logging.error(f"Ошибка создания схемы базы данных: {e}")
            raise

    async def initialize(self):
        """Инициализация схемы БД через публичный API BaseQueries"""
        try:
            if not await self.check_tables():
                logging.info(f"Инициализация схемы базы данных: {self.schema_filename}")
                await self.create_schema()
            else:
                logging.info("Схема базы данных уже инициализирована")
        except Exception as e:
            logging.error(f"Ошибка инициализации схемы базы данных: {e}")
            raise
