"""Sakhalin Kids — Character Runtime Proof builder (SKIDS-013).

Loads the seashore proof scene fixtures, merges acting + Russian viseme
timelines via TimelineMerger, generates the Milestone 01 fallback dialogue
audio with FFmpeg (deterministic tones — natural TTS quality is NOT
validated), and builds the offline HyperFrames workspace with the seaside
background.

Usage (from repository root):
    python -m tools.character.sakhalin.character_runtime_proof
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Tuple

import yaml

from tools.character.sakhalin.hyperframes_handoff import (
    HyperFramesHandoffError,
    build_hyperframes_workspace,
)
from tools.character.sakhalin.timeline_merger import (
    TimelineMergeError,
    merge_action_and_visemes,
)

# ---------------------------------------------------------------------------
# Scene constants
# ---------------------------------------------------------------------------

WIDTH = 1280
HEIGHT = 720
DURATION_MS = 12000
COMPOSITION_ID = "makar-leva-seashore-proof"

REPO_ROOT = Path(__file__).resolve().parents[3]
SCENE_DIR = REPO_ROOT / "library" / "scenes" / "makar_leva_seashore_proof"
LIBRARY_DIR = REPO_ROOT / "library"
BACKGROUND_PATH = "locations/seashore_proof.svg"

# Scene placement on the 1280x720 seashore canvas (feet on the sand band).
PLACEMENT: Dict[str, dict] = {
    "makar": {"asset_path": "characters/makar/art/front.svg", "x": 140, "y": 105},
    "leva": {"asset_path": "characters/leva/art/front.svg", "x": 740, "y": 105},
}

# Milestone 01 fallback audio windows in scene ms — hand-authored, aligned
# with the viseme speech windows and the FFmpeg tone fixture.
AUDIO_WINDOWS_MS: Dict[str, Tuple[int, int]] = {
    "makar": (1700, 4080),
    "leva": (6300, 9250),
}

_AUDIO_TONES = {"makar": 380, "leva": 220}

# Anatomical rotation pivots in character art coordinates for the parts that
# the approved fixture poses rotate (SvgSceneRenderer emits origin-relative
# rotate(); the handoff rewrites these at the HTML embedding boundary).
ROTATION_PIVOTS: Dict[str, Dict[str, Tuple[float, float]]] = {
    "makar": {"head": (250, 270), "arm_right": (336, 290)},
    "leva": {"head": (250, 262)},
}


class ProofError(Exception):
    """Raised when proof construction fails."""


# ---------------------------------------------------------------------------
# Fixture loading
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict:
    if not path.is_file():
        raise ProofError(f"missing fixture: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ProofError(f"fixture is not a mapping: {path}")
    return data


def load_poses(character_id: str) -> Dict[str, dict]:
    """Load all fixture poses for a character keyed by pose id."""
    poses_dir = LIBRARY_DIR / "characters" / character_id / "poses"
    if not poses_dir.is_dir():
        raise ProofError(f"missing poses directory: {poses_dir}")
    poses: Dict[str, dict] = {}
    for path in sorted(poses_dir.glob("*.yaml")):
        pose = _load_yaml(path)
        pid = pose.get("id")
        if not isinstance(pid, str):
            raise ProofError(f"pose without id: {path}")
        poses[pid] = pose
    return poses


def load_dialogue() -> dict:
    return _load_yaml(SCENE_DIR / "dialogue.yaml")


def load_scene_fixtures(character_id: str) -> Tuple[dict, dict, Dict[str, dict]]:
    """Return (action, viseme_timeline, poses_by_id) for a character."""
    action = _load_yaml(SCENE_DIR / "actions" / f"{character_id}_proof.yaml")
    visemes = _load_yaml(SCENE_DIR / "visemes" / f"{character_id}_proof.yaml")
    poses = load_poses(character_id)
    return action, visemes, poses


def merge_character(character_id: str) -> Tuple[dict, Dict[str, dict]]:
    """Merge action + visemes into a renderer-ready timeline for one character."""
    action, visemes, poses = load_scene_fixtures(character_id)
    timeline = merge_action_and_visemes(action, poses, visemes)
    return timeline, poses


# ---------------------------------------------------------------------------
# Milestone 01 fallback audio (FFmpeg tones — not natural speech)
# ---------------------------------------------------------------------------


def generate_dialogue_audio(wav_path: Path) -> Path:
    """Create the 12s mono fallback dialogue track with FFmpeg.

    Two distinct pulsed tones mark the speaker windows; this proves audio
    presence/mux/sync plumbing only. Natural Russian TTS is deferred to
    Milestone 02 (docs/sakhalin/LIPSYNC.md section 17).
    """
    if shutil.which("ffmpeg") is None:
        raise ProofError("ffmpeg not found on PATH (required for audio fixture)")
    if not wav_path.is_absolute():
        raise ProofError(f"audio path must be absolute: {wav_path}")
    wav_path.parent.mkdir(parents=True, exist_ok=True)

    makar_start, makar_end = AUDIO_WINDOWS_MS["makar"]
    leva_start, leva_end = AUDIO_WINDOWS_MS["leva"]
    makar_dur = (makar_end - makar_start) / 1000.0
    leva_dur = (leva_end - leva_start) / 1000.0
    total_s = DURATION_MS / 1000.0

    filter_graph = (
        f"[0:a]tremolo=f=6:d=0.85,volume=0.4,adelay={makar_start}:all=1[a0];"
        f"[1:a]tremolo=f=4.5:d=0.85,volume=0.4,adelay={leva_start}:all=1[a1];"
        "[a0][a1]amix=inputs=2:normalize=0,apad"
    )
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", f"sine=frequency={_AUDIO_TONES['makar']}:duration={makar_dur:.3f}",
        "-f", "lavfi", "-i", f"sine=frequency={_AUDIO_TONES['leva']}:duration={leva_dur:.3f}",
        "-filter_complex", filter_graph,
        "-t", f"{total_s:.3f}", "-ac", "1", "-ar", "44100",
        str(wav_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not wav_path.is_file():
        raise ProofError(f"ffmpeg audio generation failed: {proc.stderr.strip()}")
    return wav_path


# ---------------------------------------------------------------------------
# Proof build
# ---------------------------------------------------------------------------


def build_proof(
    output_dir: Path,
    *,
    generate_audio: bool = True,
) -> dict:
    """Build the SKIDS-013 proof: merged timelines, audio, workspace."""
    output_dir = Path(output_dir).resolve()

    characters = []
    timelines: Dict[str, dict] = {}
    for character_id in ("makar", "leva"):
        timeline, poses = merge_character(character_id)
        timelines[character_id] = timeline
        placement = PLACEMENT[character_id]
        characters.append({
            "instance_id": character_id,
            "asset_path": placement["asset_path"],
            "x": placement["x"],
            "y": placement["y"],
            "scale": 1.0,
            "timeline": timeline,
            "poses_by_id": poses,
        })

    output_dir.mkdir(parents=True, exist_ok=True)
    audio_path = output_dir / "dialogue.wav"
    if generate_audio:
        generate_dialogue_audio(audio_path)

    workspace = build_hyperframes_workspace(
        LIBRARY_DIR,
        output_dir / "workspace",
        WIDTH,
        HEIGHT,
        characters,
        composition_id=COMPOSITION_ID,
        background_path=BACKGROUND_PATH,
        rotation_pivots=ROTATION_PIVOTS,
    )
    return {
        "output_dir": str(output_dir),
        "workspace": workspace,
        "audio_path": str(audio_path) if generate_audio else None,
        "duration_ms": DURATION_MS,
        "audio_windows_ms": {k: list(v) for k, v in AUDIO_WINDOWS_MS.items()},
        "timelines": timelines,
    }


def _ensure_within(root: Path, target: Path) -> Path:
    root_r, target_r = root.resolve(), target.resolve()
    try:
        target_r.relative_to(root_r)
    except ValueError as exc:
        raise ProofError(f"output path escapes workspace: {target}") from exc
    return target_r


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build SKIDS-013 runtime proof")
    parser.add_argument(
        "--output", default="workspace/skids-013",
        help="output directory, relative to repository root",
    )
    parser.add_argument(
        "--skip-audio", action="store_true",
        help="skip FFmpeg fallback audio generation",
    )
    args = parser.parse_args(argv)

    out_arg = Path(args.output)
    out = out_arg if out_arg.is_absolute() else REPO_ROOT / out_arg
    try:
        out = _ensure_within(REPO_ROOT, out)
        manifest = build_proof(out, generate_audio=not args.skip_audio)
    except (ProofError, HyperFramesHandoffError, TimelineMergeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    summary = {k: v for k, v in manifest.items() if k != "timelines"}
    summary["snapshot_count"] = manifest["workspace"]["snapshot_count"]
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
