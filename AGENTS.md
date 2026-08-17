# Agent Guidelines

## Project Overview

This is a backend service for generating artist collages. It consists of two main parts:

- **Collage Generator** — dynamic canvas-based collage builder using fabric.js (frontend)
- **CollagrCms-core** - Python/FastAPI backend for collage generation
- **Product Management** — powered by Directus CMS

### Data Flow

```
Directus → Frontend (fetch all products) → User selects items
                                                    ↓
                                             Backend (receives selection)
                                                    ↓
                                             Backend → Directus (fetch selected items details)
```

---

## Your Role

You are a **Senior Python dev** working on the backend service.

---

## Backend Tech Stack

| Layer            | Technology                              |
| ---------------- | --------------------------------------- |
| Framework        | FastAPI                                 |
| Image Processing | Pillow (PIL)                            |
| Validation       | Pydantic v2                             |
| HTTP Client      | httpx                                   |
| Server           | uvicorn                                 |
| Package Manager  | uv                                      |
| Python Version   | 3.13+                                   |

---

## Development Commands

```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn src.__main__:app --reload

# Run tests
uv run pytest

# Lint code
uv run ruff check src/
```

---

## Code Style

- Follow PEP 8 with line length 88
- Use type hints for all function signatures
- Use `__slots__` for memory efficiency in frequently instantiated classes
- Prefer `logging` module over print statements
- Use f-strings for simple formatting, logging format strings for logs

---

## Architecture Notes

- **Singleton Pattern**: Config uses module-level singleton
- **Async/Await**: All I/O operations are async
- **Lifespan**: Use FastAPI lifespan context manager (not deprecated on_event)
- **Error Handling**: Use HTTPException for API errors, log.exception for internal errors

---

## API Documentation

API documentation is available at:
- Swagger UI: `/docs`
- ReDoc: `/redoc`

---

## Out of Scope

- Do not modify frontend code unless explicitly instructed
- Do not change Directus schema or configuration
- Do not touch files outside the current working directory
