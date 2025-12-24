"""Typed schemas used across the application."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, HttpUrl


class Experience(BaseModel):
    company: str
    role: str
    start: str
    end: str
    description: str
    technologies: list[str]


class Certification(BaseModel):
    name: str
    issuer: str
    date: str
    logo: str | None = None
    credential_url: HttpUrl | None = None


class Project(BaseModel):
    name: str
    description: str
    url: HttpUrl
    homepage: HttpUrl | None = None
    topics: list[str]
    language: str | None = None
    stars: int | None = None
    readme_preview: str | None = None
    updated_at: datetime | None = None


class CacheItem(BaseModel):
    value: Any
    expires_at: datetime
