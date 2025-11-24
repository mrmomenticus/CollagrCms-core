import os
import pathlib
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
    return os.path.join(f"{pathlib.Path.cwd()}/files/{safe_tag}", filename)


async def created_file(image: UploadFile, file_path: str, tag: str):
    # Используем "default" если tag пустой или содержит только пробелы
    safe_tag = tag.strip() if tag and tag.strip() else "default"
    dir_path = f"files/{safe_tag}"
    if not pathlib.Path(dir_path).exists():
        pathlib.Path(dir_path).mkdir(parents=True)
    with pathlib.Path(file_path).open("wb") as buffer:
        while chunk := await image.read(1024 * 1024):  # Читаем по 1 МБ
            buffer.write(chunk)
    await image.close()


async def delete_file(file_path: str):
    if pathlib.Path(file_path).exists():
        pathlib.Path(file_path).unlink()
