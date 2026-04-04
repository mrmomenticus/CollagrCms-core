# CollagrCms-core - Backend для генерации коллажей

Backend сервис для генерации коллажей из изображений с использованием Pillow.

## Описание

Сервис принимает запросы с изображениями и метаданными композиции, выполняет серверную обработку изображений и возвращает готовый коллаж.

## Технологии

- **FastAPI** - HTTP API
- **Pillow (PIL)** - обработка изображений
- **Pydantic v2** - валидация данных
- **httpx** - HTTP клиент для скачивания изображений
- **uvicorn** - ASGI сервер

## Требования

- Python 3.13+
- uv (менеджер пакетов)

## Установка и запуск

```bash
# Установка зависимостей
uv sync

# Установка с dev зависимостями
uv sync --extra dev

# Запуск в режиме разработки
uv run uvicorn src.__main__:app --host 0.0.0.0 --port 8000 --reload

# Запуск в продакшене
uv run uvicorn src.__main__:app --host 0.0.0.0 --port 8000 --workers 4
```

## Конфигурация

Создайте файл `.env` на основе `cfg/example.env`:

```bash
cp cfg/example.env cfg/.env
```

Основные параметры:
- `SERVER_HOST` - хост сервера (по умолчанию: 0.0.0.0)
- `SERVER_PORT` - порт сервера (по умолчанию: 8000)
- `DEBUG` - режим отладки (по умолчанию: False)
- `DIRECTUS_URL` - URL Directus API (по умолчанию: http://localhost:8055)
- `COLLAGE_OUTPUT_DIR` - директория для сохранения коллажей (по умолчанию: ./output)

## Структура проекта

```
src/
├── __main__.py          # Точка входа FastAPI приложения
├── core/
│   ├── collage_creator.py  # Создание коллажей с Pillow
│   ├── collages.py         # Сервис для работы с коллажами
│   ├── directus_client.py  # Клиент для Directus API
│   ├── font.py             # Работа со шрифтами
│   └── overlay.py          # Наложение текста на изображения
├── models/
│   └── models.py           # Pydantic модели
├── routers/
│   └── collages.py         # Эндпоинты для коллажей
└── utils/
    ├── config.py           # Конфигурация приложения
    └── logs.py             # Настройка логирования
```

## API Endpoints

### Коллажи

- `POST /v1/collage/generate` - Генерация коллажа из переданных данных об изображениях
- `POST /v1/collage/generate/with-layout` - Генерация коллажа с пользовательским макетом
- `POST /v1/collage/generate/from-directus` - Генерация коллажа из Directus
- `POST /v1/collage/generate/batch` - Пакетная генерация коллажей
- `POST /v1/collage/generate/batch-auto` - Автоматическая пакетная генерация

## Тестирование

```bash
# Запуск тестов
uv run pytest

# Запуск тестов с покрытием
uv run pytest --cov=src
```

## Линтинг

```bash
# Проверка кода
uv run ruff check src/

# Автоисправление
uv run ruff check --fix src/
```
