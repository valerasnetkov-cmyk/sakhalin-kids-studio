#!/usr/bin/env python3
"""Render the deterministic 12-second Makar + Leva Character Runtime proof."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILD_ROOT = PROJECT_ROOT / "build" / "skids-013"
DURATION_MS = 12_000
FPS = 24
WIDTH = 1280
HEIGHT = 720
VISEMES = ("REST", "A", "E", "O", "U", "MBP", "FV", "SH", "L", "S")

sys.path.insert(0, str(PROJECT_ROOT))

from tools.character.sakhalin.character_loader import CharacterLoader
from tools.character.sakhalin.character_qa import CharacterQA
from tools.character.sakhalin.svg_scene_renderer import render_frame
from tools.character.sakhalin.timeline_merger import merge_action_and_visemes


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _require_binary(*names: str) -> str:
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    raise RuntimeError(f"required executable missing: {' or '.join(names)}")


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


def _load_yaml_dir(path: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in sorted(path.glob("*.yaml")):
        data = yaml.safe_load(item.read_text(encoding="utf-8"))
        result[data["id"]] = data
    if not result:
        raise RuntimeError(f"no YAML fixtures found: {path}")
    return result


def _wav_duration_ms(path: Path) -> int:
    with wave.open(str(path), "rb") as handle:
        frames = handle.getnframes()
        rate = handle.getframerate()
    return max(1, round(frames * 1000 / rate))


def _synthesize_line(
    text: str,
    output_wav: Path,
    *,
    speed: int,
    pitch: int,
) -> None:
    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    ffmpeg = _require_binary("ffmpeg")

    if espeak:
        _run(
            [
                espeak,
                "-v",
                "ru",
                "-s",
                str(speed),
                "-p",
                str(pitch),
                "-w",
                str(output_wav),
                text,
            ]
        )
        return

    say = shutil.which("say")
    if say:
        temp_aiff = output_wav.with_suffix(".aiff")
        _run([say, "-r", str(speed), "-o", str(temp_aiff), text])
        _run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(temp_aiff),
                str(output_wav),
            ]
        )
        temp_aiff.unlink(missing_ok=True)
        return

    raise RuntimeError(
        "no local speech engine found; install espeak/espeak-ng or use macOS say"
    )


def _build_viseme_timeline(
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


def _build_scene_action(
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
    if pre_ms <= 0:
        raise ValueError("talk start must leave room for pre-roll")
    settle_ms = DURATION_MS - talk_start_ms - speech_ms
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


def _mix_audio(
    makar_wav: Path,
    leva_wav: Path,
    makar_start_ms: int,
    leva_start_ms: int,
    output_wav: Path,
) -> None:
    ffmpeg = _require_binary("ffmpeg")
    filter_graph = (
        f"[0:a]adelay={makar_start_ms}:all=1[a0];"
        f"[1:a]adelay={leva_start_ms}:all=1[a1];"
        "[a0][a1]amix=inputs=2:duration=longest:dropout_transition=0,"
        f"apad=pad_dur={DURATION_MS / 1000}[mix]"
    )
    _run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(makar_wav),
            "-i",
            str(leva_wav),
            "-filter_complex",
            filter_graph,
            "-map",
            "[mix]",
            "-t",
            f"{DURATION_MS / 1000:.3f}",
            str(output_wav),
        ]
    )


def _asset_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _render_frames(
    makar_timeline: dict[str, Any],
    leva_timeline: dict[str, Any],
    makar_poses: dict[str, dict[str, Any]],
    leva_poses: dict[str, dict[str, Any]],
) -> int:
    frames_dir = BUILD_ROOT / "frames"
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
            PROJECT_ROOT,
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
        PROJECT_ROOT,
        WIDTH,
        HEIGHT,
        0,
        characters,
        background_path="library/locations/runtime_proof_coast.svg",
    )
    if rerender != first_svg:
        raise RuntimeError("deterministic rerender check failed")

    return total_frames


def _encode_video(audio_mix: Path) -> Path:
    ffmpeg = _require_binary("ffmpeg")
    output = BUILD_ROOT / "skids-013-runtime-proof.mp4"
    _run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-framerate",
            str(FPS),
            "-i",
            str(BUILD_ROOT / "frames" / "frame_%04d.svg"),
            "-i",
            str(audio_mix),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-t",
            f"{DURATION_MS / 1000:.3f}",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    return output


def _make_samples(video: Path) -> list[str]:
    ffmpeg = _require_binary("ffmpeg")
    samples = [("opening", 0.5), ("middle", 6.0), ("end", 11.5)]
    paths = []
    for name, seconds in samples:
        output = BUILD_ROOT / "samples" / f"{name}.png"
        _run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                str(seconds),
                "-i",
                str(video),
                "-frames:v",
                "1",
                str(output),
            ]
        )
        paths.append(str(output.relative_to(PROJECT_ROOT)))
    return paths


def _probe(video: Path) -> dict[str, Any]:
    ffprobe = _require_binary("ffprobe")
    result = _run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(video),
        ]
    )
    return json.loads(result.stdout)


def _qa_report() -> dict[str, Any]:
    loader = CharacterLoader.from_project_root(PROJECT_ROOT)
    qa = CharacterQA.from_project_root(PROJECT_ROOT)
    reports = {}
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
            (
                PROJECT_ROOT / "library" / "rig_profiles" / f"{rig_id}.yaml"
            ).read_text(encoding="utf-8")
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


def main() -> int:
    _clean_build_root()
    _require_binary("ffmpeg")
    _require_binary("ffprobe")

    makar_wav = BUILD_ROOT / "audio" / "makar.wav"
    leva_wav = BUILD_ROOT / "audio" / "leva.wav"
    _synthesize_line(
        "Лёва, а почему море солёное?",
        makar_wav,
        speed=170,
        pitch=70,
    )
    _synthesize_line(
        "Хороший вопрос. Давайте разберёмся.",
        leva_wav,
        speed=145,
        pitch=42,
    )

    makar_speech_ms = _wav_duration_ms(makar_wav)
    leva_speech_ms = _wav_duration_ms(leva_wav)
    makar_start_ms = 1200
    leva_start_ms = 6200

    if makar_start_ms + makar_speech_ms >= leva_start_ms:
        raise RuntimeError("fixture dialogue overlaps; adjust local TTS timing")
    if leva_start_ms + leva_speech_ms >= DURATION_MS:
        raise RuntimeError("Leva fixture dialogue exceeds proof duration")

    makar_visemes = _build_viseme_timeline(
        "makar_proof_visemes",
        makar_start_ms,
        makar_speech_ms,
        ("L", "E", "FV", "A", "A", "S", "O", "L", "E", "S", "O", "L", "E"),
    )
    leva_visemes = _build_viseme_timeline(
        "leva_proof_visemes",
        leva_start_ms,
        leva_speech_ms,
        ("O", "L", "O", "SH", "E", "FV", "O", "S", "S", "A", "FV", "A"),
    )

    makar_poses = _load_yaml_dir(
        PROJECT_ROOT / "library" / "characters" / "makar" / "poses"
    )
    leva_poses = _load_yaml_dir(
        PROJECT_ROOT / "library" / "characters" / "leva" / "poses"
    )

    makar_action = _build_scene_action(
        "makar_proof_action",
        "fox_cartoon",
        talk_start_ms=makar_start_ms,
        speech_ms=makar_speech_ms,
        gesture_pose="point_right",
        talk_pose="talk_neutral",
    )
    leva_action = _build_scene_action(
        "leva_proof_action",
        "sea_lion_cartoon",
        talk_start_ms=leva_start_ms,
        speech_ms=leva_speech_ms,
        gesture_pose="think",
        talk_pose="talk_neutral",
    )

    makar_timeline = merge_action_and_visemes(
        makar_action, makar_poses, makar_visemes
    )
    leva_timeline = merge_action_and_visemes(leva_action, leva_poses, leva_visemes)

    audio_mix = BUILD_ROOT / "audio" / "dialogue_mix.wav"
    _mix_audio(makar_wav, leva_wav, makar_start_ms, leva_start_ms, audio_mix)

    frame_count = _render_frames(
        makar_timeline,
        leva_timeline,
        makar_poses,
        leva_poses,
    )
    video = _encode_video(audio_mix)
    samples = _make_samples(video)
    probe = _probe(video)
    qa = _qa_report()

    if any(report["blocking_count"] for report in qa.values()):
        raise RuntimeError("Character QA has blocking findings")

    assets = {
        "makar": (
            PROJECT_ROOT / "library" / "characters" / "makar" / "art" / "front.svg"
        ),
        "leva": (
            PROJECT_ROOT / "library" / "characters" / "leva" / "art" / "front.svg"
        ),
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
            name: _asset_sha256(path) for name, path in assets.items()
        },
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
