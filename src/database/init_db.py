import logging
from pathlib import Path
from typing import Set
from .connection import db


class InitDatabase:
    def __init__(self):
        self.sql_dir = Path(__file__).parent.parent / "database" / "sql"
        self.schema_file = self.sql_dir / "init.sql"

    async def get_existing_tables(self) -> Set[str]:
        pool = await db.get_pool()
        async with pool.acquire() as conn:
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            return {table["table_name"] for table in tables}

    async def check_tables(self) -> bool:
        existing_tables = await self.get_existing_tables()
        # Проверяем наличие хотя бы одной таблицы как индикатор инициализации
        return len(existing_tables) > 0

    async def create_schema(self):
        if not self.schema_file.exists():
            logging.error(f"Схема базы данных не найдена: {self.schema_file}")
            raise FileNotFoundError(f"Схема базы данных не найдена: {self.schema_file}")

        pool = await db.get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                try:
                    sql = self.schema_file.read_text()
                    await conn.execute(sql)
                    logging.info("Схема базы данных успешно создана")
                except Exception as e:
                    logging.error(f"Ошибка создания схемы базы данных: {e}")
                    raise

    async def initialize(self):
        try:
            if not await self.check_tables():
                logging.info(f"Инициализация схемы базы данных: {self.schema_file}")
                await self.create_schema()
            else:
                logging.info("Схема базы данных уже инициализирована")
        except Exception as e:
            logging.error(f"Ошибка инициализации схемы базы данных: {e}")
            raise
