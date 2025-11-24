# Используем официальный образ Python 3.13 slim
FROM python:3.13-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости
RUN pip install --no-cache-dir uv && uv pip install --system -e .

# Копируем весь код приложения
COPY . .
COPY --from=ghcr.io/astral-sh/uv:0.9.10 /uv /uvx /bin/

# Открываем порт 8000
EXPOSE 8000

# Запускаем приложение
CMD ["uv run", "-m", "src"]