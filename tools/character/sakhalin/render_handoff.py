"""Validated handoff manifest for Remotion/HyperFrames (SKIDS-009).

The handoff transfers approved render artifacts and timing only. It does not
allow downstream composition to mutate character identity, poses, visemes,
or production-state decisions.
"""

from __future__ import annotations

import math
import re
from typing import Any, Mapping, Sequence

_ID_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
_RENDERERS = frozenset({"remotion", "hyperframes"})
_MAX_DURATION_SECONDS = 600.0
_MAX_FRAMES = 36000


class RenderHandoffError(ValueError):
    """Raised when renderer handoff data is invalid."""


def build_render_handoff(spec: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize renderer handoff metadata."""

    if not isinstance(spec, Mapping):
        raise RenderHandoffError("handoff spec must be a mapping")
    expected = {
        "scene_id",
        "renderer",
        "fps",
        "duration_seconds",
        "frame_assets",
        "audio_asset_id",
    }
    if set(spec) != expected:
        raise RenderHandoffError("handoff spec contains unsupported fields")

    scene_id = _identifier(spec.get("scene_id"), "scene_id")
    renderer = spec.get("renderer")
    if renderer not in _RENDERERS:
        raise RenderHandoffError("renderer is not approved")

    fps = spec.get("fps")
    if not isinstance(fps, int) or isinstance(fps, bool) or fps < 1 or fps > 120:
        raise RenderHandoffError("fps is outside allowed bounds")

    duration = _finite_number(
        spec.get("duration_seconds"), "duration_seconds", 0.001, _MAX_DURATION_SECONDS
    )
    audio_asset_id = _identifier(spec.get("audio_asset_id"), "audio_asset_id")

    frame_assets = spec.get("frame_assets")
    if not isinstance(frame_assets, Sequence) or isinstance(frame_assets, (str, bytes)):
        raise RenderHandoffError("frame_assets must be a sequence")
    if len(frame_assets) == 0:
        raise RenderHandoffError("frame_assets must not be empty")
    if len(frame_assets) > _MAX_FRAMES:
        raise RenderHandoffError("frame_assets exceed allowed limit")

    normalized_frames: list[dict[str, Any]] = []
    previous_frame = -1
    max_frame = max(0, math.ceil(duration * fps) - 1)
    seen_assets: set[str] = set()

    for index, item in enumerate(frame_assets):
        if not isinstance(item, Mapping):
            raise RenderHandoffError(f"frame asset {index} must be a mapping")
        if set(item) != {"frame", "svg_asset_id"}:
            raise RenderHandoffError(f"frame asset {index} contains unsupported fields")

        frame = item.get("frame")
        if not isinstance(frame, int) or isinstance(frame, bool) or frame < 0:
            raise RenderHandoffError(f"frame asset {index}.frame must be non-negative integer")
        if frame < previous_frame:
            raise RenderHandoffError("frame_assets must be sorted by frame")
        if frame > max_frame:
            raise RenderHandoffError("frame asset lies outside scene duration")
        previous_frame = frame

        asset_id = _identifier(item.get("svg_asset_id"), f"frame asset {index}.svg_asset_id")
        if asset_id in seen_assets:
            raise RenderHandoffError("svg_asset_id values must be unique")
        seen_assets.add(asset_id)
        normalized_frames.append({"frame": frame, "svg_asset_id": asset_id})

    return {
        "version": "1.0",
        "scene_id": scene_id,
        "renderer": renderer,
        "fps": fps,
        "duration_seconds": duration,
        "frame_assets": normalized_frames,
        "audio_asset_id": audio_asset_id,
        "character_mutation_allowed": False,
    }


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise RenderHandoffError(f"{field} must be a stable identifier")
    return value


def _finite_number(value: Any, field: str, minimum: float, maximum: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise RenderHandoffError(f"{field} must be numeric")
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < minimum or numeric > maximum:
        raise RenderHandoffError(f"{field} is outside allowed bounds")
    return numeric
