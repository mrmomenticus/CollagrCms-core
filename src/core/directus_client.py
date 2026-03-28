"""Клиент для работы с Directus API."""
import logging
from typing import Any

import httpx

from src.models.models import DirectusConfig

log = logging.getLogger(__name__)


class DirectusClient:
    """Клиент для работы с Directus API."""

    def __init__(self, config: DirectusConfig) -> None:
        """Инициализация клиента.

        Args:
            config: Конфигурация для подключения к Directus

        """
        self.config = config
        self.base_url = config.url.rstrip("/")
        self.headers: dict[str, str] = {}
        self._token: str | None = config.token

    async def authenticate(self) -> str:
        """Авторизация в Directus.

        Returns:
            Токен доступа

        Raises:
            Exception: Если ошибка авторизации

        """
        if self._token:
            self.headers["Authorization"] = f"Bearer {self._token}"
            return self._token

        if not self.config.email or not self.config.password:
            raise ValueError("Необходимо указать token или email/password")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/auth/login",
                    json={
                        "email": self.config.email,
                        "password": self.config.password,
                    },
                )
                response.raise_for_status()
                data = response.json()
                token = data["data"]["access_token"]
                self._token = token
                self.headers["Authorization"] = f"Bearer {token}"
                log.info("Успешная авторизация в Directus")
                return token

        except httpx.HTTPError as e:
            log.error("Ошибка авторизации в Directus: %s", e)
            raise

    async def get_products_with_images(
        self,
        product_ids: list[int] | None = None,
        category_ids: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        """Получает продукты с изображениями из Directus.

        Оптимизированный метод, который получает все данные за один запрос
        с использованием встроенных возможностей Directus (fields, filter).

        Args:
            product_ids: Опциональный список ID продуктов для фильтрации
            category_ids: Опциональный список ID категорий для фильтрации

        Returns:
            Список продуктов с изображениями

        Raises:
            Exception: Если ошибка получения данных

        """
        await self.authenticate()

        try:
            # Формируем параметры запроса
            params = {
                # Получаем все поля продукта и связанные данные
                "fields": ",".join([
                    "id",
                    "name",
                    "description",
                    "price",
                    "category_id.id",
                    "category_id.name",
                    "category_id.description",
                    "category_id.is_active",
                    # Получаем изображения через relation
                    "images.id",
                    "images.path",
                    "images.product_id",
                ]),
                # Фильтр только активных продуктов
                "filter[status][_eq]": "published",
            }

            # Добавляем фильтр по ID продуктов
            if product_ids:
                params["filter[id][_in]"] = ",".join(str(pid) for pid in product_ids)

            # Добавляем фильтр по категориям
            if category_ids:
                params["filter[category_id][_in]"] = ",".join(str(cid) for cid in category_ids)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/items/products",
                    params=params,
                    headers=self.headers,
                )
                response.raise_for_status()
                data = response.json()
                products = data.get("data", [])

                log.info("Получено %d продуктов из Directus", len(products))
                return products

        except httpx.HTTPError as e:
            log.error("Ошибка получения продуктов из Directus: %s", e)
            raise
