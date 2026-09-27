"""Merge acting and mouth timelines without cross-track authority.

SKIDS-007 keeps lip-sync isolated from body/head acting. The merger validates
both inputs, applies the mouth timeline offset, and returns renderer-neutral
tracks. It does not interpret actions or render assets.
"""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Mapping, Sequence

SEMANTIC_VISEMES = frozenset(
    {"REST", "A", "E", "O", "U", "MBP", "FV", "SH", "L", "S"}
)

_ALLOWED_ACTING_CHANNELS = frozenset(
    {
        "action",
        "body",
        "head",
        "eyes",
        "eyebrows",
        "arms",
        "tail_wings",
        "expression",
        "gaze",
        "gesture",
    }
)

_FORBIDDEN_MOUTH_AUTHORITY = frozenset({"mouth", "viseme", "lip_sync"})
_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
_MAX_EVENTS = 5000


class TimelineMergeError(ValueError):
    """Raised when acting/mouth timelines cannot be safely merged."""


def merge_character_timelines(
    acting_timeline: Mapping[str, Any],
    mouth_timeline: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and merge acting plus mouth tracks.

    Mouth events are shifted by start_seconds but remain a separate track.
    Acting data is never rewritten from viseme data.
    """

    acting = _validate_acting_timeline(acting_timeline)
    mouth = _validate_mouth_timeline(mouth_timeline)

    if acting["character_id"] != mouth["character_id"]:
        raise TimelineMergeError("acting and mouth character_id must match")

    shifted_mouth = [
        {"t": mouth["start_seconds"] + event["t"], "viseme": event["viseme"]}
        for event in mouth["events"]
    ]

    return {
        "version": "1.0",
        "character_id": acting["character_id"],
        "audio_asset_id": mouth["audio_asset_id"],
        "tracks": {
            "acting": deepcopy(acting["events"]),
            "mouth": shifted_mouth,
        },
    }


def _validate_acting_timeline(timeline: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(timeline, Mapping):
        raise TimelineMergeError("acting timeline must be a mapping")
    if set(timeline) != {"version", "character_id", "events"}:
        raise TimelineMergeError("acting timeline contains unsupported fields")
    if timeline.get("version") != "1.0":
        raise TimelineMergeError("acting timeline version must be '1.0'")

    character_id = _require_identifier(timeline.get("character_id"), "character_id")
    events = timeline.get("events")
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes)):
        raise TimelineMergeError("acting events must be a sequence")
    if len(events) == 0:
        raise TimelineMergeError("acting events must not be empty")
    if len(events) > _MAX_EVENTS:
        raise TimelineMergeError("acting events exceed allowed limit")

    normalized: list[dict[str, Any]] = []
    previous_t = -1.0
    for index, raw_event in enumerate(events):
        if not isinstance(raw_event, Mapping):
            raise TimelineMergeError(f"acting event {index} must be a mapping")
        if set(raw_event) != {"t", "channel", "value"}:
            raise TimelineMergeError(f"acting event {index} contains unsupported fields")

        t = _require_time(raw_event.get("t"), f"acting event {index}.t")
        if t < previous_t:
            raise TimelineMergeError("acting events must be sorted by time")
        previous_t = t

        channel = raw_event.get("channel")
        if channel in _FORBIDDEN_MOUTH_AUTHORITY:
            raise TimelineMergeError("acting timeline cannot control mouth or viseme state")
        if channel not in _ALLOWED_ACTING_CHANNELS:
            raise TimelineMergeError(f"acting event {index} has unsupported channel")

        value = raw_event.get("value")
        if not isinstance(value, str) or not value.strip():
            raise TimelineMergeError(
                f"acting event {index}.value must be a non-empty string"
            )

        normalized.append({"t": t, "channel": channel, "value": value})

    return {"version": "1.0", "character_id": character_id, "events": normalized}


def _validate_mouth_timeline(timeline: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(timeline, Mapping):
        raise TimelineMergeError("mouth timeline must be a mapping")
    if set(timeline) != {
        "version",
        "character_id",
        "audio_asset_id",
        "start_seconds",
        "events",
    }:
        raise TimelineMergeError("mouth timeline contains unsupported fields")
    if timeline.get("version") != "1.0":
        raise TimelineMergeError("mouth timeline version must be '1.0'")

    character_id = _require_identifier(timeline.get("character_id"), "character_id")
    audio_asset_id = _require_identifier(
        timeline.get("audio_asset_id"), "audio_asset_id"
    )
    start_seconds = _require_time(timeline.get("start_seconds"), "start_seconds")

    events = timeline.get("events")
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes)):
        raise TimelineMergeError("mouth events must be a sequence")
    if len(events) == 0:
        raise TimelineMergeError("mouth events must not be empty")
    if len(events) > _MAX_EVENTS:
        raise TimelineMergeError("mouth events exceed allowed limit")

    normalized: list[dict[str, Any]] = []
    previous_t = -1.0
    for index, raw_event in enumerate(events):
        if not isinstance(raw_event, Mapping):
            raise TimelineMergeError(f"mouth event {index} must be a mapping")
        if set(raw_event) != {"t", "viseme"}:
            raise TimelineMergeError(f"mouth event {index} contains unsupported fields")

        t = _require_time(raw_event.get("t"), f"mouth event {index}.t")
        if t < previous_t:
            raise TimelineMergeError("mouth events must be sorted by time")
        previous_t = t

        viseme = raw_event.get("viseme")
        if viseme not in SEMANTIC_VISEMES:
            raise TimelineMergeError(f"mouth event {index} has unknown viseme")

        normalized.append({"t": t, "viseme": viseme})

    return {
        "version": "1.0",
        "character_id": character_id,
        "audio_asset_id": audio_asset_id,
        "start_seconds": start_seconds,
        "events": normalized,
    }


def _require_identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER_RE.fullmatch(value):
        raise TimelineMergeError(f"{field} must be a stable identifier")
    return value


def _require_time(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TimelineMergeError(f"{field} must be numeric")
    numeric = float(value)
    if numeric < 0 or numeric > 3600:
        raise TimelineMergeError(f"{field} is outside allowed bounds")
    return numeric
