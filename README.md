# Portfolio FastAPI + Tailwind

Portfolio professionnel (FastAPI + Jinja2 + Tailwind + Alpine.js) prêt pour déploiement cloud. Version POC avec configuration minimale.

## Stack
- FastAPI, uvicorn, Jinja2
- Tailwind CSS (CLI) + Alpine.js
- httpx (async) pour GitHub API + cache mémoire
- Pydantic v2 + pydantic-settings
- Packaging: Poetry

## Prérequis
- Python 3.11+
- Node 18+ / npm
- Poetry 1.8+

## Installation
```bash
poetry install
npm install
cp .env.example .env
```
Renseigner `GITHUB_USERNAME` et éventuellement `GITHUB_TOKEN` (pour lever les limites de rate).

## Développement
Dans deux terminaux:
```bash
npm run dev:css
poetry run uvicorn app.main:app --reload --port 8000
```
Ouvrir http://localhost:8000.

## Build CSS
```bash
npm run build:css
```

## Qualité & Tests
POC : aucune étape de lint ou de test n'est incluse.

## Structure
- app/main.py : routes, templates, statiques
- app/services/github_service.py : récupération + cache GitHub
- app/models/schemas.py : modèles Pydantic
- app/data/*.json : expériences et certifications
- app/locales/*.json : i18n fr / en
- app/static/css/tailwind.css : entrée Tailwind (output styles.css)
- app/templates/*.html : pages Jinja2

## Déploiement (ex. Render/Fly/Railway)
1. Construire CSS : `npm run build:css`
2. Démarrer via uvicorn : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Variables d'env : `GITHUB_USERNAME`, `GITHUB_TOKEN` (optionnel), `CACHE_TTL_SECONDS`, `DEFAULT_LOCALE`.

## Résumé & CV
Endpoint `/resume` renvoie le PDF dans `app/static/resume/resume.pdf` (remplacer par votre CV).

## CI
Workflow GitHub Actions réduit : build CSS uniquement (`.github/workflows/ci.yml`).

## Licence
MIT
