#!/usr/bin/env python3
"""Render the deterministic 12-second Makar + Leva Character Runtime proof."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILD_ROOT = PROJECT_ROOT / "build" / "skids-013"
sys.path.insert(0, str(PROJECT_ROOT))

from tools.character.sakhalin.proof_media import (
    encode_svg_sequence,
    make_samples,
    mix_audio,
    probe_media,
    require_binary,
    synthesize_line,
    wav_duration_ms,
)
from tools.character.sakhalin.runtime_proof import (
    DURATION_MS,
    FPS,
    VISEMES,
    asset_sha256,
    build_character_qa,
    build_scene_action,
    build_viseme_timeline,
    load_yaml_dir,
    render_frames,
)
from tools.character.sakhalin.timeline_merger import merge_action_and_visemes


def _clean_build_root() -> None:
    resolved = BUILD_ROOT.resolve()
    allowed_parent = (PROJECT_ROOT / "build").resolve()
    if resolved.parent != allowed_parent or resolved.name != "skids-013":
        raise RuntimeError("refusing to clean unexpected build path")
    if BUILD_ROOT.exists():
        shutil.rmtree(BUILD_ROOT)
    (BUILD_ROOT / "frames").mkdir(parents=True)
    (BUILD_ROOT / "audio").mkdir()
    (BUILD_ROOT / "samples").mkdir()


def _prepare_dialogue() -> tuple[Path, Path, int, int, int, int]:
    makar_wav = BUILD_ROOT / "audio" / "makar.wav"
    leva_wav = BUILD_ROOT / "audio" / "leva.wav"

    synthesize_line(
        "Лёва, а почему море солёное?",
        makar_wav,
        speed=170,
        pitch=70,
    )
    synthesize_line(
        "Хороший вопрос. Давайте разберёмся.",
        leva_wav,
        speed=145,
        pitch=42,
    )

    makar_speech_ms = wav_duration_ms(makar_wav)
    leva_speech_ms = wav_duration_ms(leva_wav)
    makar_start_ms = 1200
    leva_start_ms = 6200

    if makar_start_ms + makar_speech_ms >= leva_start_ms:
        raise RuntimeError("fixture dialogue overlaps; adjust local TTS timing")
    if leva_start_ms + leva_speech_ms >= DURATION_MS:
        raise RuntimeError("Leva fixture dialogue exceeds proof duration")

    return (
        makar_wav,
        leva_wav,
        makar_start_ms,
        leva_start_ms,
        makar_speech_ms,
        leva_speech_ms,
    )


def _build_timelines(
    makar_start_ms: int,
    leva_start_ms: int,
    makar_speech_ms: int,
    leva_speech_ms: int,
) -> tuple[dict, dict, dict, dict]:
    makar_poses = load_yaml_dir(
        PROJECT_ROOT / "library" / "characters" / "makar" / "poses"
    )
    leva_poses = load_yaml_dir(
        PROJECT_ROOT / "library" / "characters" / "leva" / "poses"
    )

    makar_visemes = build_viseme_timeline(
        "makar_proof_visemes",
        makar_start_ms,
        makar_speech_ms,
        ("L", "E", "FV", "A", "A", "S", "O", "L", "E", "S", "O", "L", "E"),
    )
    leva_visemes = build_viseme_timeline(
        "leva_proof_visemes",
        leva_start_ms,
        leva_speech_ms,
        ("O", "L", "O", "SH", "E", "FV", "O", "S", "S", "A", "FV", "A"),
    )

    makar_action = build_scene_action(
        "makar_proof_action",
        "fox_cartoon",
        talk_start_ms=makar_start_ms,
        speech_ms=makar_speech_ms,
        gesture_pose="point_right",
        talk_pose="talk_neutral",
    )
    leva_action = build_scene_action(
        "leva_proof_action",
        "sea_lion_cartoon",
        talk_start_ms=leva_start_ms,
        speech_ms=leva_speech_ms,
        gesture_pose="think",
        talk_pose="talk_neutral",
    )

    return (
        merge_action_and_visemes(makar_action, makar_poses, makar_visemes),
        merge_action_and_visemes(leva_action, leva_poses, leva_visemes),
        makar_poses,
        leva_poses,
    )


def main() -> int:
    _clean_build_root()
    require_binary("ffmpeg")
    require_binary("ffprobe")

    (
        makar_wav,
        leva_wav,
        makar_start_ms,
        leva_start_ms,
        makar_speech_ms,
        leva_speech_ms,
    ) = _prepare_dialogue()

    (
        makar_timeline,
        leva_timeline,
        makar_poses,
        leva_poses,
    ) = _build_timelines(
        makar_start_ms,
        leva_start_ms,
        makar_speech_ms,
        leva_speech_ms,
    )

    audio_mix = BUILD_ROOT / "audio" / "dialogue_mix.wav"
    mix_audio(
        makar_wav,
        leva_wav,
        makar_start_ms,
        leva_start_ms,
        DURATION_MS,
        audio_mix,
    )

    frame_count = render_frames(
        PROJECT_ROOT,
        BUILD_ROOT,
        makar_timeline,
        leva_timeline,
        makar_poses,
        leva_poses,
    )

    video = BUILD_ROOT / "skids-013-runtime-proof.mp4"
    encode_svg_sequence(
        BUILD_ROOT / "frames" / "frame_%04d.svg",
        audio_mix,
        video,
        fps=FPS,
        duration_ms=DURATION_MS,
    )

    samples = [
        str(Path(path).relative_to(PROJECT_ROOT))
        for path in make_samples(video, BUILD_ROOT / "samples")
    ]
    probe = probe_media(video)
    qa = build_character_qa(PROJECT_ROOT)

    if any(report["blocking_count"] for report in qa.values()):
        raise RuntimeError("Character QA has blocking findings")

    assets = {
        "makar": PROJECT_ROOT / "library" / "characters" / "makar" / "art" / "front.svg",
        "leva": PROJECT_ROOT / "library" / "characters" / "leva" / "art" / "front.svg",
    }

    report = {
        "version": "1.0",
        "status": "pass",
        "duration_ms": DURATION_MS,
        "fps": FPS,
        "frame_count": frame_count,
        "dialogue": {
            "makar": {
                "text": "Лёва, а почему море солёное?",
                "start_ms": makar_start_ms,
                "audio_duration_ms": makar_speech_ms,
            },
            "leva": {
                "text": "Хороший вопрос. Давайте разберёмся.",
                "start_ms": leva_start_ms,
                "audio_duration_ms": leva_speech_ms,
            },
        },
        "character_asset_sha256": {
            name: asset_sha256(path) for name, path in assets.items()
        },
        "semantic_visemes": list(VISEMES),
        "character_qa": qa,
        "samples": samples,
        "video": str(video.relative_to(PROJECT_ROOT)),
        "ffprobe": probe,
    }
    (BUILD_ROOT / "render_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    print(video)
    print(BUILD_ROOT / "render_report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
