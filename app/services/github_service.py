"""GitHub service to fetch repositories with lightweight caching."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Iterable

import httpx
from pydantic import ValidationError

from app.models.schemas import CacheItem, Project


class GitHubService:
    """Service responsible for querying GitHub and caching responses."""

    def __init__(
        self, username: str, token: str | None, cache_ttl_seconds: int = 900
    ) -> None:
        self.username = username
        self.token = token
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: CacheItem | None = None

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _is_cache_valid(self) -> bool:
        return bool(self._cache and self._cache.expires_at > datetime.now(timezone.utc))

    def _set_cache(self, projects: list[Project]) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.cache_ttl_seconds)
        self._cache = CacheItem(value=projects, expires_at=expires_at)

    def _get_cache(self) -> list[Project] | None:
        if self._is_cache_valid():
            return list(self._cache.value)
        return None

    async def _fetch_readme_preview(self, client: httpx.AsyncClient, repo_name: str) -> str | None:
        url = f"https://api.github.com/repos/{self.username}/{repo_name}/readme"
        try:
            headers = {**self._headers(), "Accept": "application/vnd.github.raw"}
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                return None
            # GitHub raw content when using the default JSON accept header returns base64 content;
            # requesting vnd.github.raw gives text directly.
            return response.text[:400]
        except httpx.HTTPError:
            return None

    def _filter_by_topics(
        self, projects: Iterable[Project], topics_filter: Iterable[str] | None
    ) -> list[Project]:
        if not topics_filter:
            return list(projects)
        topic_set = {topic.lower() for topic in topics_filter}
        filtered = [
            project
            for project in projects
            if topic_set.intersection({topic.lower() for topic in project.topics})
        ]
        return filtered

    async def fetch_repos(
        self, topics_filter: list[str] | None = None, limit: int = 6
    ) -> list[Project]:
        """Return repositories for the configured user, optionally filtered by topics."""
        cached = self._get_cache()
        if cached is not None:
            return self._filter_by_topics(cached, topics_filter)[:limit]

        url = f"https://api.github.com/users/{self.username}/repos?per_page=100&sort=updated"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=self._headers())
            response.raise_for_status()
            repos = response.json()

            projects: list[Project] = []
            for repo in repos:
                topics = repo.get("topics") or []
                preview = await self._fetch_readme_preview(client, repo["name"])
                homepage = repo.get("homepage") or None  # GitHub may return empty strings
                try:
                    project = Project(
                        name=repo["name"],
                        description=repo.get("description") or "",
                        url=repo["html_url"],
                        homepage=homepage,
                        topics=topics,
                        language=repo.get("language"),
                        stars=repo.get("stargazers_count"),
                        readme_preview=preview,
                        updated_at=datetime.fromisoformat(
                            repo["updated_at"].replace("Z", "+00:00")
                        ),
                    )
                except ValidationError:
                    # Skip repositories with malformed data instead of failing startup
                    continue

                projects.append(project)

        self._set_cache(projects)
        return self._filter_by_topics(projects, topics_filter)[:limit]

    async def warm_cache(self) -> None:
        """Warm cache in the background without blocking startup."""
        try:
            await self.fetch_repos()
        except httpx.HTTPError:
            # We keep startup resilient if GitHub is temporarily unreachable.
            return

    async def clear_cache(self) -> None:
        """Clear the in-memory cache."""
        self._cache = None



async def refresh_periodically(service: GitHubService, interval_seconds: int) -> None:
    """Background task to refresh cache periodically."""
    while True:
        await asyncio.sleep(interval_seconds)
        await service.clear_cache()
        await service.warm_cache()
