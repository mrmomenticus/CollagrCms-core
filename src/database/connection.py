import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from typing import Optional, AsyncGenerator, Callable, TypeVar, Awaitable
from contextlib import asynccontextmanager
from functools import wraps


from src.database.schema.base import Base

T = TypeVar("T")


class DatabaseConnection:
    _instance: Optional["DatabaseConnection"] = None
    _engine = None
    _async_session = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self, dsn: str):
        if self._engine is None:
            self._engine = create_async_engine(
                dsn,
                poolclass=AsyncAdaptedQueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
            )
            self._async_session = async_sessionmaker(
                self._engine, class_=AsyncSession, expire_on_commit=False
            )

    async def close(self):
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._async_session = None

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        if not self._async_session:
            raise RuntimeError("База данных не подключена")

        async with self._async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e

    def with_session(
        self, func: Callable[..., Awaitable[T]]
    ) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with self.get_session() as session:
                return await func(session, *args, **kwargs)

        return wrapper

    async def init_database(self) -> None:
        if not self._engine:
            raise RuntimeError("База данных не подключена")
        async with self._engine.begin() as conn:
            logging.info("Создание базы данных")
            await conn.run_sync(Base.metadata.create_all)


# Синглтон
db = DatabaseConnection()
