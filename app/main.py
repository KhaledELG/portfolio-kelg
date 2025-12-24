"""FastAPI entrypoint for the portfolio site."""
from __future__ import annotations

import asyncio
import contextlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models.schemas import Certification, Experience, Project
from app.services.github_service import GitHubService, refresh_periodically

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@lru_cache
def load_experiences(locale: str | None = None) -> list[Experience]:
    lang = (locale or settings.default_locale).lower()
    raw_path = Path(f"app/data/experience_{lang}.json")
    if not raw_path.exists():
        raw_path = Path("app/data/experience.json")
    return [Experience.model_validate(exp) for exp in _load_json_list(raw_path)]


@lru_cache
def load_certifications(locale: str | None = None) -> list[Certification]:
    lang = (locale or settings.default_locale).lower()
    raw_path = Path(f"app/data/certifications_{lang}.json")
    if not raw_path.exists():
        raw_path = Path("app/data/certifications.json")
    return [Certification.model_validate(cert) for cert in _load_json_list(raw_path)]


def _load_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def load_tech_stack(locale: str | None = None, translations: dict[str, Any] | None = None) -> dict[str, list[str]]:
    """Return tech stack categories with optional localized category labels."""
    lang = (locale or settings.default_locale).lower()
    base = {
        "Cloud & Orchestration": ["AWS", "Kubernetes", "Docker", "Harbor", "EKS"],
        "Infrastructure as Code": ["Terraform", "Ansible", "Helm", "CloudFormation"],
        "CI/CD & GitOps": ["GitLab CI", "ArgoCD", "Jenkins", "GitHub Actions"],
        "Security": ["Trivy", "SonarQube", "Vault", "Grype", "DefectDojo", "Dependency Track"],
        "Networking & Service Mesh": ["Cilium", "Traefik", "MetalLB", "cert-manager"],
        "Observability": ["Prometheus", "Grafana", "Elastic", "Kibana"],
        "Databases & Storage": ["Ceph", "Rook", "PostgreSQL", "Aurora"],
        "Languages": ["Python", "Bash", "YAML"],
    }

    localized = (translations or {}).get("tech_categories") or load_locale(lang).get("tech_categories") or {}
    return {localized.get(k, k): v for k, v in base.items()}


def load_skills(locale: str | None = None, translations: dict[str, Any] | None = None) -> dict[str, list[str]]:
    """Return skills grouped by category, with optional localized category labels."""
    lang = (locale or settings.default_locale).lower()
    base = {
        "Cloud": ["AWS", "Azure", "GCP", "OVH"],
        "DevOps": ["Docker", "Kubernetes", "Terraform", "Ansible", "GitHub Actions"],
        "Security": ["Vault", "IAM", "Zero Trust"],
        "Monitoring": ["Prometheus", "Grafana", "ELK", "Loki"],
    }
    localized = (translations or {}).get("skills_categories") or load_locale(lang).get("skills_categories") or {}
    return {localized.get(k, k): v for k, v in base.items()}


@lru_cache
def load_locale(locale: str | None = None) -> dict[str, Any]:
    """Return translation dictionary, falling back to default locale when missing."""
    lang = (locale or settings.default_locale).lower()
    path = Path(f"app/locales/{lang}.json")
    if not path.exists():
        path = Path(f"app/locales/{settings.default_locale}.json")
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except json.JSONDecodeError:
        return {}


skills = {
    "Cloud": ["AWS", "Azure", "GCP", "OVH"],
    "DevOps": ["Docker", "Kubernetes", "Terraform", "Ansible", "GitHub Actions"],
    "Security": ["Vault", "IAM", "Zero Trust"],
    "Monitoring": ["Prometheus", "Grafana", "ELK", "Loki"],
}

github_service = GitHubService(
    username=settings.github_username,
    token=settings.github_token,
    cache_ttl_seconds=settings.cache_ttl_seconds,
)

refresh_task: asyncio.Task | None = None


@app.on_event("startup")
async def on_startup() -> None:
    global refresh_task
    await github_service.warm_cache()
    refresh_task = asyncio.create_task(
        refresh_periodically(github_service, interval_seconds=settings.cache_ttl_seconds)
    )



@app.on_event("shutdown")
async def on_shutdown() -> None:
    if refresh_task:
        refresh_task.cancel()
        with contextlib.suppress(Exception):
            await refresh_task



@app.get("/", response_class=HTMLResponse)
async def home(request: Request, lang: str | None = None) -> HTMLResponse:
    try:
        projects = await github_service.fetch_repos(limit=6)
    except httpx.HTTPError:
        projects = []

    t = load_locale(lang)
    tech_stack = load_tech_stack(lang, translations=t)
    localized_skills = load_skills(lang, translations=t)
    context = {
        "request": request,
        "settings": settings,
        "skills": localized_skills,
        "tech_stack": tech_stack,
        "experiences": load_experiences(lang),
        "certifications": load_certifications(lang),
        "projects": projects,
        "t": t,
        "lang": (lang or settings.default_locale),
    }
    return templates.TemplateResponse("index.html", context)


@app.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request, lang: str | None = None) -> HTMLResponse:
    try:
        projects = await github_service.fetch_repos(limit=20)
    except httpx.HTTPError:
        projects = []

    t = load_locale(lang)
    context = {
        "request": request,
        "settings": settings,
        "projects": projects,
        "t": t,
        "lang": (lang or settings.default_locale),
    }
    return templates.TemplateResponse("projects.html", context)


@app.get("/api/projects")
async def api_projects(topics: str | None = None) -> list[Project]:
    topics_filter = topics.split(",") if topics else None
    try:
        return await github_service.fetch_repos(topics_filter=topics_filter, limit=20)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="GitHub temporarily unavailable") from exc



@app.get("/resume")
async def download_resume() -> FileResponse:
    resume_path = Path("app/static/resume/resume.pdf")
    return FileResponse(resume_path, media_type="application/pdf", filename="resume.pdf")
