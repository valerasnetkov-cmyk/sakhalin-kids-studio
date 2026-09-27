"""Local media helpers for the SKIDS-013 proof.

All subprocess calls use fixed argument vectors. No shell execution is used.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import wave
from pathlib import Path
from typing import Any


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def require_binary(*names: str) -> str:
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    raise RuntimeError(f"required executable missing: {' or '.join(names)}")


def wav_duration_ms(path: Path) -> int:
    with wave.open(str(path), "rb") as handle:
        frames = handle.getnframes()
        rate = handle.getframerate()
    return max(1, round(frames * 1000 / rate))


def synthesize_line(
    text: str,
    output_wav: Path,
    *,
    speed: int,
    pitch: int,
) -> None:
    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    ffmpeg = require_binary("ffmpeg")

    if espeak:
        run_command(
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
        run_command([say, "-r", str(speed), "-o", str(temp_aiff), text])
        run_command(
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


def mix_audio(
    makar_wav: Path,
    leva_wav: Path,
    makar_start_ms: int,
    leva_start_ms: int,
    duration_ms: int,
    output_wav: Path,
) -> None:
    ffmpeg = require_binary("ffmpeg")
    filter_graph = (
        f"[0:a]adelay={makar_start_ms}:all=1[a0];"
        f"[1:a]adelay={leva_start_ms}:all=1[a1];"
        "[a0][a1]amix=inputs=2:duration=longest:dropout_transition=0,"
        f"apad=pad_dur={duration_ms / 1000}[mix]"
    )
    run_command(
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
            f"{duration_ms / 1000:.3f}",
            str(output_wav),
        ]
    )


def encode_svg_sequence(
    frames_pattern: Path,
    audio_mix: Path,
    output_video: Path,
    *,
    fps: int,
    duration_ms: int,
) -> None:
    ffmpeg = require_binary("ffmpeg")
    run_command(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-framerate",
            str(fps),
            "-i",
            str(frames_pattern),
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
            f"{duration_ms / 1000:.3f}",
            "-movflags",
            "+faststart",
            str(output_video),
        ]
    )


def make_samples(video: Path, samples_dir: Path) -> list[str]:
    ffmpeg = require_binary("ffmpeg")
    samples = [("opening", 0.5), ("middle", 6.0), ("end", 11.5)]
    paths: list[str] = []

    for name, seconds in samples:
        output = samples_dir / f"{name}.png"
        run_command(
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
        paths.append(str(output))

    return paths


def probe_media(video: Path) -> dict[str, Any]:
    ffprobe = require_binary("ffprobe")
    result = run_command(
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
