"""Pure/runtime helpers for the SKIDS-013 Character Runtime proof."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

from .character_loader import CharacterLoader
from .character_qa import CharacterQA
from .svg_scene_renderer import render_frame

DURATION_MS = 12_000
FPS = 24
WIDTH = 1280
HEIGHT = 720
VISEMES = ("REST", "A", "E", "O", "U", "MBP", "FV", "SH", "L", "S")


def load_yaml_dir(path: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in sorted(path.glob("*.yaml")):
        data = yaml.safe_load(item.read_text(encoding="utf-8"))
        result[data["id"]] = data
    if not result:
        raise RuntimeError(f"no YAML fixtures found: {path}")
    return result


def build_viseme_timeline(
    timeline_id: str,
    start_ms: int,
    speech_ms: int,
    sequence: tuple[str, ...],
) -> dict[str, Any]:
    if start_ms < 0 or speech_ms <= 0 or start_ms + speech_ms >= DURATION_MS:
        raise ValueError("speech placement does not fit proof duration")
    if not sequence or any(viseme not in VISEMES for viseme in sequence):
        raise ValueError("invalid fixture viseme sequence")

    cues: list[dict[str, Any]] = []
    if start_ms:
        cues.append({"start_ms": 0, "end_ms": start_ms, "viseme": "REST"})

    base, remainder = divmod(speech_ms, len(sequence))
    if base == 0:
        raise ValueError("speech duration is too short for fixture visemes")

    cursor = start_ms
    for index, viseme in enumerate(sequence):
        length = base + (1 if index < remainder else 0)
        end = cursor + length
        cues.append({"start_ms": cursor, "end_ms": end, "viseme": viseme})
        cursor = end

    if cursor < DURATION_MS:
        cues.append({"start_ms": cursor, "end_ms": DURATION_MS, "viseme": "REST"})

    return {
        "version": "1.0",
        "id": timeline_id,
        "duration_ms": DURATION_MS,
        "cues": cues,
    }


def build_scene_action(
    action_id: str,
    rig_profile: str,
    *,
    talk_start_ms: int,
    speech_ms: int,
    gesture_pose: str,
    talk_pose: str,
) -> dict[str, Any]:
    gesture_ms = 300
    pre_ms = talk_start_ms - gesture_ms
    settle_ms = DURATION_MS - talk_start_ms - speech_ms

    if pre_ms <= 0:
        raise ValueError("talk start must leave room for pre-roll")
    if settle_ms <= 0:
        raise ValueError("speech leaves no settle time")

    return {
        "version": "1.0",
        "id": action_id,
        "rig_profile": rig_profile,
        "phases": [
            {"name": "preroll", "duration_ms": pre_ms, "pose": "idle"},
            {"name": "gesture", "duration_ms": gesture_ms, "pose": gesture_pose},
            {"name": "dialogue", "duration_ms": speech_ms, "pose": talk_pose},
            {"name": "settle", "duration_ms": settle_ms, "pose": "idle"},
        ],
    }


def asset_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_frames(
    project_root: Path,
    build_root: Path,
    makar_timeline: dict[str, Any],
    leva_timeline: dict[str, Any],
    makar_poses: dict[str, dict[str, Any]],
    leva_poses: dict[str, dict[str, Any]],
) -> int:
    frames_dir = build_root / "frames"
    total_frames = DURATION_MS * FPS // 1000
    characters = [
        {
            "instance_id": "makar",
            "asset_path": "library/characters/makar/art/front.svg",
            "x": 420,
            "y": 445,
            "scale": 0.78,
            "timeline": makar_timeline,
            "poses_by_id": makar_poses,
        },
        {
            "instance_id": "leva",
            "asset_path": "library/characters/leva/art/front.svg",
            "x": 850,
            "y": 455,
            "scale": 0.84,
            "timeline": leva_timeline,
            "poses_by_id": leva_poses,
        },
    ]

    first_svg = None
    for frame in range(total_frames):
        timestamp_ms = min(DURATION_MS - 1, frame * 1000 // FPS)
        svg = render_frame(
            project_root,
            WIDTH,
            HEIGHT,
            timestamp_ms,
            characters,
            background_path="library/locations/runtime_proof_coast.svg",
        )
        if frame == 0:
            first_svg = svg
        (frames_dir / f"frame_{frame:04d}.svg").write_text(svg, encoding="utf-8")

    rerender = render_frame(
        project_root,
        WIDTH,
        HEIGHT,
        0,
        characters,
        background_path="library/locations/runtime_proof_coast.svg",
    )
    if rerender != first_svg:
        raise RuntimeError("deterministic rerender check failed")

    return total_frames


def build_character_qa(project_root: Path) -> dict[str, Any]:
    loader = CharacterLoader.from_project_root(project_root)
    qa = CharacterQA.from_project_root(project_root)
    reports: dict[str, Any] = {}

    configs = {
        "makar": (
            "fox_cartoon",
            "backpack",
            ["idle", "blink", "look", "point", "talk"],
        ),
        "leva": (
            "sea_lion_cartoon",
            "scarf",
            ["idle", "blink", "look", "think", "talk"],
        ),
    }

    for character_id, (rig_id, prop, actions) in configs.items():
        spec = loader.load_core(character_id)
        rig = yaml.safe_load(
            (project_root / "library" / "rig_profiles" / f"{rig_id}.yaml").read_text(
                encoding="utf-8"
            )
        )
        evidence = {
            "character_id": character_id,
            "parts": rig["parts"]["required"],
            "actions": actions,
            "props": [prop],
            "visemes": list(VISEMES),
        }
        reports[character_id] = qa.review(spec, rig, evidence)

    return reports
