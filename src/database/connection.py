import asyncpg
from typing import Optional


class Database:
    _instance: Optional["Database"] = None
    _pool: Optional[asyncpg.Pool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self, dsn: str):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(dsn)

    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def get_pool(self) -> asyncpg.Pool:
        if not self._pool:
            raise RuntimeError("Database connection not initialized")
        return self._pool


db = Database()
