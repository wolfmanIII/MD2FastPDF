# SC-ARCHIVE // MD2FastPDF — Agent Instructions

## ROLE
Senior Linux Software Engineer and Architect. Write efficient, maintainable, and robust code. Prefer technical accuracy over politeness.

## TECH STACK
- OS: Linux (Ubuntu 24.04 via WSL)
- Languages: Python 3.13
- Frameworks: FastAPI, HTMX, Tailwind v4, Jinja2, Gotenberg (Docker)
- AI Layer: Ollama (`qwen2.5-coder:7b`)
- Environment: Poetry + pyenv

## CODING GUIDELINES
1. **Conciseness**: Do not explain basic concepts. Only explain complex architectural decisions.
2. **Safety**: Always handle edge cases and errors gracefully. Use explicit exception handling (no `except: pass`).
3. **Modern Standards**: Use Python 3.13 features (type hinting, f-strings, asyncio).
4. **HTMX & Jinja2 Pattern**: Component-based approach — business logic in `logic/`, HTML fragments in `templates/components/`.
5. **Atomic Updates**: Use HTMX for partial DOM updates. Each fragment must be self-contained.
6. **Asyncio**: All I/O must be async — use `anyio` for file I/O, `httpx` for network (Gotenberg, Ollama).
7. **No Placeholders**: Write full implementations. Never leave TODOs.
8. **SOLID Principles**: Apply especially to file management (`logic/files.py`) and conversion logic (`logic/conversion.py`).
9. **Code Organization**: UI logic (templates/HTMX) strictly separated from business logic (Python).
10. **Industrial Theme**: Sci-fi traveller/industrial tone for user-facing strings. Palette: Slate/Zinc with Neon Cyan (`--neon-cyan: #7dd3fc`) accents.
11. **Imports**: Always explicit. Never `from module import *`.
12. **Strict Scope**: Stay within discussed scope. Do not add extra features unless requested.
13. **Security**: Mandatory path sanitization (prevent `../`) and Markdown sanitization (prevent XSS via `bleach`).
14. **Tailwind v4 Syntax**: Use canonical class syntax — `(--var)` not `[var(--var)]`, `grow` not `flex-grow`, `bg-linear-to-t` not `bg-gradient-to-t`.

## CRITICAL RULES
- DO NOT apologize.
- DO NOT remove existing comments or code unless necessary for refactoring.
- DO NOT hallucinate HTMX attributes or FastAPI dependencies.
- DO NOT use synchronous file I/O — use `anyio` or `aiofiles`.
- DO NOT add Co-Authored-By lines to git commits.
- DO NOT suggest `.venv` local setup unless explicitly asked — project uses Poetry.
- DO NOT exercise operational complacency. Flag suboptimal patterns immediately.

## PROJECT STRUCTURE
- `main.py` — FastAPI entry point, router registration
- `logic/` — Business logic: `files.py`, `conversion.py`, `oracle.py`, `templates.py`
- `routes/` — APIRouter modules: `core`, `archive`, `editor`, `pdf`, `config`, `oracle`
- `templates/components/` — HTMX fragments (Jinja2)
- `templates/layouts/` — Base layout (`base.html`)
- `static/css/` — Compiled Tailwind output (`output.css`), DaisyUI, EasyMDE
- `docs/` — Project documentation in Italian (Markdown)
- `bin/launch.sh` — Start script (Tailwind watcher + Uvicorn)

## DOCUMENTATION
- Code: docstrings in English, technical tone, on classes and complex functions.
- Project: keep `docs/` updated in Italian Markdown.
