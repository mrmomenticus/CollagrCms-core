import os
import uuid

from fastapi import UploadFile


async def create_uuid(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    if not ext:
        ext = ".jpg"
    return f"{uuid.uuid4()}{ext}"


async def create_path(filename: str, tag: str) -> str:
    # Используем "default" если tag пустой или содержит только пробелы
    safe_tag = tag.strip() if tag and tag.strip() else "default"
    return os.path.join(f"{os.getcwd()}/files/{safe_tag}", filename)


async def created_file(image: UploadFile, file_path: str, tag: str):
    # Используем "default" если tag пустой или содержит только пробелы
    safe_tag = tag.strip() if tag and tag.strip() else "default"
    dir_path = f"files/{safe_tag}"
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    with open(file_path, "wb") as buffer:
        while chunk := await image.read(1024 * 1024):  # Читаем по 1 МБ
            buffer.write(chunk)
    await image.close()
    return


async def delete_file(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)
