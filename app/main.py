"""FastAPI entrypoint for the portfolio site."""
from __future__ import annotations

import asyncio
import contextlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
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
def load_experiences() -> list[Experience]:
    raw_path = Path("app/data/experience.json")
    return [Experience.model_validate(exp) for exp in _load_json_list(raw_path)]


@lru_cache
def load_certifications() -> list[Certification]:
    raw_path = Path("app/data/certifications.json")
    return [Certification.model_validate(cert) for cert in _load_json_list(raw_path)]


def _load_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


skills = {
    "Cloud": ["AWS", "Azure", "GCP", "OVH"],
    "DevOps": ["Docker", "Kubernetes", "Terraform", "Ansible", "GitHub Actions"],
    "Security": ["Vault", "IAM", "Zero Trust"],
    "Monitoring": ["Prometheus", "Grafana", "ELK", "Loki"],
}

tech_stack = {
    "Cloud & Orchestration": ["AWS", "Kubernetes", "Docker", "Harbor", "EKS"],
    "Infrastructure as Code": ["Terraform", "Ansible", "Helm", "CloudFormation"],
    "CI/CD & GitOps": ["GitLab CI", "ArgoCD", "Jenkins", "GitHub Actions"],
    "Security": ["Trivy", "SonarQube", "Vault", "Grype", "DefectDojo", "Dependency Track"],
    "Networking & Service Mesh": ["Cilium", "Traefik", "MetalLB", "cert-manager"],
    "Observability": ["Prometheus", "Grafana", "Elastic", "Kibana"],
    "Databases & Storage": ["Ceph", "Rook", "PostgreSQL", "Aurora"],
    "Languages": ["Python", "Bash", "YAML"],
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
async def home(request: Request) -> HTMLResponse:
    projects = await github_service.fetch_repos(limit=6)
    context = {
        "request": request,
        "settings": settings,
        "skills": skills,
        "tech_stack": tech_stack,
        "experiences": load_experiences(),
        "certifications": load_certifications(),
        "projects": projects,
    }
    return templates.TemplateResponse("index.html", context)



@app.get("/api/projects")
async def api_projects(topics: str | None = None) -> list[Project]:
    topics_filter = topics.split(",") if topics else None
    return await github_service.fetch_repos(topics_filter=topics_filter, limit=20)



@app.get("/resume")
async def download_resume() -> FileResponse:
    resume_path = Path("app/static/resume/resume.pdf")
    return FileResponse(resume_path, media_type="application/pdf", filename="resume.pdf")
