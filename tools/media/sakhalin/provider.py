"""Provider-neutral media generation contracts for Sakhalin Kids."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Protocol, Sequence


class GenerationKind(str, Enum):
    """Supported paid-generation classes."""

    IMAGE = "image"
    VIDEO = "video"


class GenerationStatus(str, Enum):
    """Normalized provider request state."""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class GenerationRequest:
    """Provider-neutral generation request.

    Provider-specific arguments belong in `parameters`; callers must not rely on
    those fields outside the selected adapter.
    """

    request_key: str
    kind: GenerationKind
    prompt: str
    model: str
    max_cost_usd: float
    reference_urls: Sequence[str] = ()
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.request_key.strip():
            raise ValueError("request_key must not be empty")
        if not self.prompt.strip():
            raise ValueError("prompt must not be empty")
        if not self.model.strip():
            raise ValueError("model must not be empty")
        if self.max_cost_usd <= 0:
            raise ValueError("max_cost_usd must be positive")


@dataclass(frozen=True)
class GenerationResult:
    """Normalized result returned by a media provider."""

    provider: str
    request_id: str
    status: GenerationStatus
    asset_urls: Sequence[str] = ()
    raw_metadata: Mapping[str, Any] = field(default_factory=dict)


class MediaProvider(Protocol):
    """Minimal boundary for external generative-media providers."""

    @property
    def name(self) -> str:
        ...

    def submit(self, request: GenerationRequest) -> GenerationResult:
        ...

    def status(self, request_id: str) -> GenerationResult:
        ...

    def result(self, request_id: str) -> GenerationResult:
        ...

    def cancel(self, request_id: str) -> GenerationResult:
        ...
