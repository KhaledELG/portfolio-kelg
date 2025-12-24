# FastAPI Portfolio

Simple FastAPI + Jinja2 portfolio backed by Tailwind CSS and Alpine.js. The project ships with a minimal cloud-ready configuration.

## Tech Stack
- FastAPI, Uvicorn, Jinja2
- Tailwind CLI + Alpine.js
- httpx client with in-memory cache
- Pydantic v2 + pydantic-settings
- Poetry for packaging

## Requirements
- Python 3.11+
- Node 18+ with npm
- Poetry 1.8+

## Project Structure
- app/main.py – routes, templates, static files
- app/services/github_service.py – GitHub fetching + caching
- app/models/schemas.py – Pydantic models
- app/data/*.json – experience and certifications
- app/locales/*.json – i18n strings (fr/en)
- app/static/css/tailwind.css – Tailwind entry (outputs styles.css)
- app/templates/*.html – Jinja2 pages

## CI
Lightweight GitHub Actions workflow focuses on CSS build only (`.github/workflows/ci.yml`).
