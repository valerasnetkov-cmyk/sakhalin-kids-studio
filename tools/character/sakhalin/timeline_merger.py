"""Sakhalin Kids — TimelineMerger domain service (SKIDS-007).

Deterministic merger of Action + Pose references + VisemeTimeline
into renderer-ready combined character timeline.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from jsonschema import Draft202012Validator

# ---------------------------------------------------------------------------
# Schema paths
# ---------------------------------------------------------------------------

_SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "schemas" / "sakhalin"

_ACTION_SCHEMA_PATH = _SCHEMAS_DIR / "action.schema.json"
_POSE_SCHEMA_PATH = _SCHEMAS_DIR / "pose.schema.json"
_VISEME_SCHEMA_PATH = _SCHEMAS_DIR / "viseme_timeline.schema.json"

# ---------------------------------------------------------------------------
# Approved viseme set
# ---------------------------------------------------------------------------

APPROVED_VISEMES: frozenset[str] = frozenset({
    "REST", "A", "E", "O", "U", "MBP", "FV", "SH", "L", "S",
})

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class TimelineMergeError(Exception):
    """Raised when timeline merge fails validation or structural checks."""


# ---------------------------------------------------------------------------
# Schema loaders (cached per process)
# ---------------------------------------------------------------------------

_schema_cache: Dict[str, dict] = {}


def _load_schema(name: str, path: Path) -> dict:
    if name not in _schema_cache:
        with open(path, encoding="utf-8") as fh:
            _schema_cache[name] = json.load(fh)
    return _schema_cache[name]


def _validate_schema(name: str, path: Path, instance: dict, label: str) -> None:
    schema = _load_schema(name, path)
    validator = Draft202012Validator(schema)
    errors = [e.message for e in validator.iter_errors(instance)]
    if errors:
        joined = "; ".join(errors[:5])
        raise TimelineMergeError(f"invalid {label}: {joined}")


# ---------------------------------------------------------------------------
# Action -> absolute phase ranges
# ---------------------------------------------------------------------------


def _action_phase_ranges(
    action: dict,
) -> List[Tuple[int, int, str]]:
    """Convert action phases to [(start_ms, end_ms, pose_id), ...]."""
    ranges: List[Tuple[int, int, str]] = []
    cursor = 0
    for phase in action["phases"]:
        start = cursor
        end = cursor + phase["duration_ms"]
        ranges.append((start, end, phase["pose"]))
        cursor = end
    return ranges


def _action_duration_ms(action: dict) -> int:
    return sum(p["duration_ms"] for p in action["phases"])


# ---------------------------------------------------------------------------
# Pose resolution
# ---------------------------------------------------------------------------


def _resolve_poses(
    action: dict,
    poses_by_id: Dict[str, dict],
) -> Dict[str, dict]:
    """Validate and resolve all action phase pose references."""
    resolved: Dict[str, dict] = {}
    for phase in action["phases"]:
        pose_id = phase["pose"]
        if pose_id not in poses_by_id:
            raise TimelineMergeError(
                f"unresolved pose reference: {pose_id!r}"
            )
        pose = poses_by_id[pose_id]
        if pose["id"] != pose_id:
            raise TimelineMergeError(
                f"pose mapping key {pose_id!r} != pose.id {pose['id']!r}"
            )
        if pose["rig_profile"] != action["rig_profile"]:
            raise TimelineMergeError(
                f"rig_profile mismatch: action {action['rig_profile']!r} "
                f"!= pose {pose_id!r} rig_profile {pose['rig_profile']!r}"
            )
        resolved[pose_id] = pose
    return resolved


# ---------------------------------------------------------------------------
# Viseme temporal validation
# ---------------------------------------------------------------------------


def _validate_viseme_temporal(
    viseme_timeline: dict,
) -> None:
    """Validate viseme cue temporal semantics."""
    cues = viseme_timeline["cues"]
    duration_ms = viseme_timeline["duration_ms"]

    for i, cue in enumerate(cues):
        if cue["start_ms"] >= cue["end_ms"]:
            raise TimelineMergeError(
                f"invalid cue range: start_ms {cue['start_ms']} "
                f">= end_ms {cue['end_ms']} at index {i}"
            )

    for i in range(1, len(cues)):
        if cues[i]["start_ms"] < cues[i - 1]["start_ms"]:
            raise TimelineMergeError("unsorted cues")

    for i in range(1, len(cues)):
        if cues[i]["start_ms"] < cues[i - 1]["end_ms"]:
            raise TimelineMergeError(
                f"overlapping cues at index {i}"
            )

    for i in range(1, len(cues)):
        if cues[i]["start_ms"] > cues[i - 1]["end_ms"]:
            raise TimelineMergeError(
                f"timeline gap between index {i - 1} and {i}"
            )

    if cues[0]["start_ms"] != 0:
        raise TimelineMergeError("first cue does not start at 0")

    if cues[-1]["end_ms"] != duration_ms:
        raise TimelineMergeError(
            f"final cue end_ms {cues[-1]['end_ms']} "
            f"!= duration_ms {duration_ms}"
        )


# ---------------------------------------------------------------------------
# Boundary union merge
# ---------------------------------------------------------------------------


def _merge_boundaries(
    acting_ranges: List[Tuple[int, int, str]],
    cues: List[dict],
    duration_ms: int,
) -> List[dict]:
    """Merge acting and viseme boundaries into combined segments."""
    boundaries = set()
    for start, end, _pose in acting_ranges:
        boundaries.add(start)
        boundaries.add(end)
    for cue in cues:
        boundaries.add(cue["start_ms"])
        boundaries.add(cue["end_ms"])
    boundaries.add(0)
    boundaries.add(duration_ms)
    sorted_bounds = sorted(boundaries)

    def _find_pose(t: int) -> str:
        for start, end, pose in acting_ranges:
            if start <= t < end:
                return pose
        return acting_ranges[-1][2]

    def _find_viseme(t: int) -> str:
        for cue in cues:
            if cue["start_ms"] <= t < cue["end_ms"]:
                return cue["viseme"]
        return cues[-1]["viseme"]

    segments = []
    for i in range(len(sorted_bounds) - 1):
        start = sorted_bounds[i]
        end = sorted_bounds[i + 1]
        segments.append({
            "start_ms": start,
            "end_ms": end,
            "pose": _find_pose(start),
            "viseme": _find_viseme(start),
        })
    return segments


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def merge_action_and_visemes(
    action: dict,
    poses_by_id: Dict[str, dict],
    viseme_timeline: dict,
) -> dict:
    """Merge Action + Pose references + VisemeTimeline into combined timeline.

    Returns a deterministic renderer-ready segment list.
    Does not mutate inputs.
    """
    action = copy.deepcopy(action)
    poses_by_id = copy.deepcopy(poses_by_id)
    viseme_timeline = copy.deepcopy(viseme_timeline)

    _validate_schema("action", _ACTION_SCHEMA_PATH, action, "action")
    for pid, pose in poses_by_id.items():
        _validate_schema("pose", _POSE_SCHEMA_PATH, pose, f"pose {pid!r}")
    _validate_schema(
        "viseme_timeline", _VISEME_SCHEMA_PATH,
        viseme_timeline, "viseme_timeline",
    )

    _resolve_poses(action, poses_by_id)
    _validate_viseme_temporal(viseme_timeline)

    action_dur = _action_duration_ms(action)
    viseme_dur = viseme_timeline["duration_ms"]

    if action_dur > viseme_dur:
        raise TimelineMergeError(
            f"action duration {action_dur}ms "
            f"> viseme duration {viseme_dur}ms"
        )

    acting_ranges = _action_phase_ranges(action)

    if action_dur < viseme_dur:
        last_pose = acting_ranges[-1][2]
        acting_ranges.append((action_dur, viseme_dur, last_pose))

    segments = _merge_boundaries(
        acting_ranges, viseme_timeline["cues"], viseme_dur,
    )

    return {
        "version": "1.0",
        "rig_profile": action["rig_profile"],
        "duration_ms": viseme_dur,
        "segments": segments,
    }
