import logging
from pathlib import Path
from src.database.connection import DatabaseConnection


class BaseQueries:
    def __init__(self, db: DatabaseConnection):
        self.db = db
        self.sql_dir = Path(__file__).parent.parent / "sql"

    async def __call__(self, filename: str, *args, **kwargs):
        return await self.execute_sql_file(filename, *args, **kwargs)

    async def _read_sql_file(self, filename: str) -> str:
        file_path = self.sql_dir / filename
        logging.debug(f"Reading SQL file: {file_path}")
        if not file_path.exists():
            raise FileNotFoundError(f"SQL file not found: {filename}")
        return file_path.read_text()

    async def execute_sql_file(self, filename: str, *args, **kwargs) -> str:
        query = await self._read_sql_file(filename)
        return await self.db.execute_query(query, *args, **kwargs)
