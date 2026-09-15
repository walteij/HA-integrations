from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, TypeAlias
from urllib.parse import urlsplit

import aiohttp
from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)


class ArrApiError(Exception):
    """Base error for ARR API issues."""


class ArrAuthenticationError(ArrApiError):
    """Raised when the API key or authentication fails."""


class ArrConnectionError(ArrApiError):
    """Raised when the API cannot be reached."""


class ArrTimeoutError(ArrApiError):
    """Raised when the API request times out."""


class ArrSslError(ArrApiError):
    """Raised when SSL certificate verification fails."""


class ArrInvalidResponseError(ArrApiError):
    """Raised when the API returns malformed or unexpected data."""


class ArrNotFoundError(ArrApiError):
    """Raised when a resource is not found."""


class ArrConflictError(ArrApiError):
    """Raised when an operation conflicts with an existing resource."""


class ArrUnsupportedOperationError(ArrApiError):
    """Raised when a requested operation is not supported by the target application."""


JsonValue: TypeAlias = dict[str, Any] | list[Any] | str | int | float | bool | None


@dataclass(slots=True)
class SystemStatus:
    app_name: str
    version: str
    instance_id: str | None = None
    is_proper_plan: bool | None = None
    raw: dict[str, Any] | None = None


@dataclass(slots=True)
class QueueSummary:
    count: int = 0
    total_records: int = 0
    items: list[dict[str, Any]] | None = None


@dataclass(slots=True)
class HealthIssue:
    source: str | None = None
    type: str | None = None
    message: str | None = None
    wiki_url: str | None = None


@dataclass(slots=True)
class DiskSpace:
    path: str | None = None
    total: float | None = None
    free: float | None = None
    used_percentage: float | None = None


@dataclass(slots=True)
class RootFolder:
    id: int | str | None = None
    path: str | None = None
    name: str | None = None
    accessible: bool | None = None


@dataclass(slots=True)
class QualityProfile:
    id: int | str | None = None
    name: str | None = None
    language: str | None = None


@dataclass(slots=True)
class LookupResult:
    id: str | int | None = None
    title: str | None = None
    year: int | None = None
    media_type: str | None = None
    foreign_id: str | None = None
    overview: str | None = None
    poster_url: str | None = None
    existing: bool = False
    application_id: str | int | None = None
    raw: dict[str, Any] | None = None


@dataclass(slots=True)
class AddMediaRequest:
    title: str | None = None
    root_folder_path: str | None = None
    quality_profile_id: int | str | None = None
    monitor: str | None = None
    search_after_add: bool = False
    foreign_id: str | None = None
    year: int | None = None
    media_type: str | None = None


@dataclass(slots=True)
class AddMediaResult:
    success: bool = False
    id: str | int | None = None
    title: str | None = None
    message: str | None = None
    raw: dict[str, Any] | None = None


@dataclass(slots=True)
class CommandResult:
    success: bool = False
    id: str | int | None = None
    message: str | None = None
    raw: dict[str, Any] | None = None


def redact_url(url: str) -> str:
    """Return a URL without credentials or secrets."""
    parsed = urlsplit(url)
    if parsed.username or parsed.password:
        netloc = parsed.hostname or ""
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        return parsed._replace(netloc=netloc).geturl()
    return url


def _json_loads(raw: str | bytes | None) -> Any:
    if raw in (None, ""):
        raise ArrInvalidResponseError("Empty response")
    try:
        return json.loads(raw)
    except (TypeError, ValueError) as err:
        raise ArrInvalidResponseError("Malformed JSON response") from err


class ArrApiClient:
    """Async API client for Sonarr, Radarr, and Lidarr."""

    def __init__(
        self,
        session: ClientSession,
        base_url: str,
        api_key: str,
        *,
        verify_ssl: bool = True,
        timeout: int = 30,
    ) -> None:
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.timeout = timeout

    @property
    def api_base(self) -> str:
        return self.base_url

    def _merge_url(self, endpoint: str) -> str:
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        return f"{self.base_url}{endpoint if endpoint.startswith('/') else '/' + endpoint}"

    async def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        timeout: int | None = None,
    ) -> Any:
        """Perform an API request and normalize exceptions."""
        method_name = method.upper()
        url = self._merge_url(endpoint)
        headers = {
            "X-Api-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        request_timeout = aiohttp.ClientTimeout(total=timeout or self.timeout)
        _LOGGER.debug("Request %s %s", method_name, redact_url(url))
        try:
            async with self.session.request(
                method_name,
                url,
                params=params,
                json=json_body,
                headers=headers,
                ssl=self.verify_ssl,
                timeout=request_timeout,
            ) as response:
                status = response.status
                if status in (200, 201, 202, 204):
                    if status == 204:
                        return None
                    text = await response.text()
                    if not text:
                        return None
                    try:
                        return json.loads(text)
                    except ValueError as err:
                        raise ArrInvalidResponseError(f"Unexpected non-JSON response: {status}") from err

                body_text = await response.text()
                try:
                    payload = json.loads(body_text) if body_text else {}
                except ValueError:
                    payload = {"message": body_text[:200] or "No response body"}

                if status == 401:
                    raise ArrAuthenticationError("Authentication failed")
                if status == 403:
                    raise ArrAuthenticationError("Access denied")
                if status == 404:
                    raise ArrNotFoundError(str(payload.get("message") or "Resource not found"))
                if status == 409:
                    raise ArrConflictError(str(payload.get("message") or "Conflict"))
                if status == 400 and isinstance(payload, dict) and payload.get("error") == "notSupported":
                    raise ArrUnsupportedOperationError("Requested operation is not supported")
                if status >= 500:
                    raise ArrConnectionError("Server error from ARR instance")
                raise ArrInvalidResponseError(str(payload.get("message") or f"Unexpected status code {status}"))
        except TimeoutError as err:
            raise ArrTimeoutError("Request to ARR instance timed out") from err
        except aiohttp.ClientConnectorSSLError as err:
            raise ArrSslError("SSL certificate validation failed") from err
        except aiohttp.ClientConnectorError as err:
            raise ArrConnectionError("Unable to connect to ARR instance") from err
        except (aiohttp.ClientError, ValueError) as err:
            raise ArrConnectionError("Request failed") from err

    async def get(self, endpoint: str, *, params: Mapping[str, Any] | None = None) -> Any:
        return await self.request("GET", endpoint, params=params)

    async def post(self, endpoint: str, *, json_body: Any = None, params: Mapping[str, Any] | None = None) -> Any:
        return await self.request("POST", endpoint, json_body=json_body, params=params)

    async def put(self, endpoint: str, *, json_body: Any = None) -> Any:
        return await self.request("PUT", endpoint, json_body=json_body)

    async def delete(self, endpoint: str, *, json_body: Any = None) -> Any:
        return await self.request("DELETE", endpoint, json_body=json_body)


def normalize_system_status(data: dict[str, Any]) -> SystemStatus:
    version = str(data.get("version") or data.get("appVersion") or "unknown")
    app_name = str(data.get("appName") or data.get("application") or "unknown")
    instance_id = data.get("instanceId")
    if instance_id is None:
        instance_id = data.get("instanceName")
    return SystemStatus(
        app_name=app_name,
        version=version,
        instance_id=str(instance_id) if instance_id is not None else None,
        is_proper_plan=data.get("isProperPlan"),
        raw=data,
    )


def normalize_queue(data: dict[str, Any] | list[Any] | None) -> QueueSummary:
    if isinstance(data, dict):
        items = data.get("records") or data.get("queue") or []
        count = int(data.get("totalCount") or data.get("count") or 0)
        return QueueSummary(count=count, total_records=len(items if isinstance(items, list) else []), items=list(items) if isinstance(items, list) else [])
    if isinstance(data, list):
        return QueueSummary(count=len(data), total_records=len(data), items=data)
    return QueueSummary()


def normalize_health(data: list[dict[str, Any]] | None) -> list[HealthIssue]:
    if not isinstance(data, list):
        return []
    issues: list[HealthIssue] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        issues.append(
            HealthIssue(
                source=item.get("source"),
                type=item.get("type"),
                message=item.get("message"),
                wiki_url=item.get("wikiUrl"),
            )
        )
    return issues


def normalize_disk_space(data: dict[str, Any] | None) -> list[DiskSpace]:
    if not isinstance(data, list):
        if isinstance(data, dict):
            data = [data]
        else:
            return []
    disks: list[DiskSpace] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        total = float(item.get("total") or 0)
        free = float(item.get("free") or 0)
        used_percentage = (1 - (free / total)) * 100 if total else 0
        disks.append(
            DiskSpace(
                path=item.get("path"),
                total=total,
                free=free,
                used_percentage=used_percentage,
            )
        )
    return disks


def normalize_root_folders(data: list[dict[str, Any]] | None) -> list[RootFolder]:
    if not isinstance(data, list):
        return []
    result: list[RootFolder] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        result.append(
            RootFolder(
                id=item.get("id"),
                path=item.get("path"),
                name=item.get("name") or item.get("path"),
                accessible=item.get("accessible"),
            )
        )
    return result


def normalize_quality_profiles(data: list[dict[str, Any]] | None) -> list[QualityProfile]:
    if not isinstance(data, list):
        return []
    result: list[QualityProfile] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        result.append(
            QualityProfile(
                id=item.get("id"),
                name=item.get("name"),
                language=item.get("language"),
            )
        )
    return result


def normalize_lookup_result(data: dict[str, Any] | None) -> LookupResult | None:
    if not isinstance(data, dict):
        return None
    return LookupResult(
        id=data.get("id") or data.get("tmdbId") or data.get("foreignId"),
        title=data.get("title") or data.get("name"),
        year=data.get("year"),
        media_type=data.get("mediaType") or data.get("type"),
        foreign_id=data.get("foreignId") or data.get("tvdbId") or data.get("imdbId"),
        overview=data.get("overview"),
        poster_url=data.get("remotePoster") or data.get("posterUrl"),
        existing=bool(data.get("existing")),
        application_id=data.get("id"),
        raw=data,
    )
