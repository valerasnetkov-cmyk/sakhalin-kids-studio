"""Higgsfield MediaProvider adapter.

The SDK import is lazy so repository tooling and the active Character Runtime
proof do not require higgsfield-client to be installed.
"""

from __future__ import annotations

from typing import Any

from .higgsfield_config import HiggsfieldConfig
from .provider import (
    GenerationRequest,
    GenerationResult,
    GenerationStatus,
)


class HiggsfieldDisabledError(RuntimeError):
    """Raised when a paid call is attempted while the provider is disabled."""


class HiggsfieldDependencyError(RuntimeError):
    """Raised when the optional Higgsfield SDK is unavailable."""


class HiggsfieldProvider:
    """Guarded adapter over the official Higgsfield Python client."""

    name = "higgsfield"

    def __init__(self, config: HiggsfieldConfig) -> None:
        self._config = config

    def submit(self, request: GenerationRequest) -> GenerationResult:
        self._require_enabled()
        client = self._load_client()

        controller = client.submit(
            request.model,
            arguments=dict(request.parameters, prompt=request.prompt),
        )
        request_id = _extract_request_id(controller)

        return GenerationResult(
            provider=self.name,
            request_id=request_id,
            status=GenerationStatus.QUEUED,
        )

    def status(self, request_id: str) -> GenerationResult:
        self._require_enabled()
        client = self._load_client()
        raw_status = client.status(request_id=request_id)

        return GenerationResult(
            provider=self.name,
            request_id=request_id,
            status=_normalize_status(raw_status),
            raw_metadata={"status_type": type(raw_status).__name__},
        )

    def result(self, request_id: str) -> GenerationResult:
        self._require_enabled()
        client = self._load_client()
        payload = client.result(request_id=request_id)

        return GenerationResult(
            provider=self.name,
            request_id=request_id,
            status=GenerationStatus.COMPLETED,
            asset_urls=_extract_asset_urls(payload),
        )

    def cancel(self, request_id: str) -> GenerationResult:
        self._require_enabled()
        client = self._load_client()
        client.cancel(request_id=request_id)

        return GenerationResult(
            provider=self.name,
            request_id=request_id,
            status=GenerationStatus.CANCELLED,
        )

    def _require_enabled(self) -> None:
        if not self._config.enabled:
            raise HiggsfieldDisabledError(
                "Higgsfield generation is disabled by configuration"
            )

    def _load_client(self) -> Any:
        try:
            import higgsfield_client
        except ImportError as exc:
            raise HiggsfieldDependencyError(
                "Install higgsfield-client before enabling Higgsfield"
            ) from exc

        return higgsfield_client


def _extract_request_id(controller: Any) -> str:
    for attribute in ("request_id", "id"):
        value = getattr(controller, attribute, None)
        if isinstance(value, str) and value:
            return value
    raise RuntimeError("Higgsfield submit response did not expose a request ID")


def _normalize_status(raw_status: Any) -> GenerationStatus:
    name = type(raw_status).__name__.lower()
    mapping = {
        "queued": GenerationStatus.QUEUED,
        "inprogress": GenerationStatus.IN_PROGRESS,
        "completed": GenerationStatus.COMPLETED,
        "failed": GenerationStatus.FAILED,
        "nsfw": GenerationStatus.BLOCKED,
        "cancelled": GenerationStatus.CANCELLED,
    }
    return mapping.get(name, GenerationStatus.FAILED)


def _extract_asset_urls(payload: Any) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        return ()

    urls: list[str] = []
    for collection_key in ("images", "videos", "assets"):
        items = payload.get(collection_key)
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                url = item.get("url")
                if isinstance(url, str) and url.startswith(("https://", "http://")):
                    urls.append(url)

    direct_url = payload.get("url")
    if isinstance(direct_url, str) and direct_url.startswith(("https://", "http://")):
        urls.append(direct_url)

    return tuple(dict.fromkeys(urls))
