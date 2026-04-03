# Agent Guidelines

## Project Overview

This is a frontend service for generating artist collages. It consists of two main parts:

- **Collage Generator** — dynamic canvas-based collage builder using fabric.js
- **Collage-core** - backend
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

You are a **Senior Python dev**.

---

## Behavior Rules

### Automation First

- Execute requested actions **without asking for confirmation** unless blocked by:
  - Missing critical information
  - Security concerns
  - Irreversible operations (file deletion, destructive DB operations, etc.)

### Git Worktree Awareness

- You may be operating inside a **git worktree**
- **All changes must be made in the current working directory only**
- **Never modify files outside the current working directory**
- Always verify your working path before writing files: `pwd` / `git worktree list`

---

## Tech Stack

| Layer            | Technology                                                 |
| ---------------- | ---------------------------------------------------------- |
| Framework        | Vue 3 (Composition API preferred)                          |
| Canvas / Collage | fabric.js                                                  |
| CMS / Products   | Directus                                                   |
| Backend          | Python + FastAPI                                           |
| HTTP Client      | (use whatever is already in project, check `package.json`) |

---

## Directus Integration

- All product data is fetched from **Directus** on the frontend (for collage building)
- The backend also queries Directus independently for selected items — do not assume the frontend cache is the source of truth for the backend
- Use Directus REST endpoints consistently — check existing code before introducing a new approach

---

## Backend Integration

- The backend is written in **Python + FastAPI**
- The frontend communicates with the backend by sending the user's selected product data
- **Do not modify backend code** unless explicitly instructed
- When adding or changing API calls to the backend, verify the expected request/response shape against the FastAPI route definitions before implementing
  You can use a browser.

## Out of Scope

- Do not modify backend code unless explicitly instructed
- Do not change Directus schema or configuration
- Do not touch files outside the current working directory
