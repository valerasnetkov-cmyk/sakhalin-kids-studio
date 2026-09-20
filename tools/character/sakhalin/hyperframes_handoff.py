"""Sakhalin Kids — HyperFrames Runtime Handoff (SKIDS-009).

Deterministic handoff from SvgSceneRenderer to HyperFrames workspace.
Generates one SVG snapshot per unique state interval (no JS animation).
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from tools.character.sakhalin.svg_scene_renderer import (
    SvgRenderError,
    render_frame,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HF_MANIFEST_VERSION = "1.0"
_SVG_INLINE_RE = re.compile(r"<svg\b[^>]*>.*?</svg>", re.DOTALL)
_DANGEROUS_CONTENT = re.compile(
    r"<script[\s>]|<foreignObject[\s>]|javascript:|data:text/html",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class HyperFramesHandoffError(Exception):
    """Raised when HyperFrames handoff fails validation or structural checks."""


# ---------------------------------------------------------------------------
# Timeline boundary union
# ---------------------------------------------------------------------------


def _collect_boundaries(characters: List[dict]) -> Tuple[List[int], int]:
    """Collect sorted unique boundary timestamps from all character timelines.

    Returns (sorted_boundaries, duration_ms).
    Raises HyperFramesHandoffError on duration mismatch or empty input.
    """
    if not characters:
        raise HyperFramesHandoffError("no characters provided")

    durations = set()
    boundaries: set[int] = {0}
    for char in characters:
        tl = char.get("timeline", {})
        dur = tl.get("duration_ms", 0)
        if not isinstance(dur, int) or dur <= 0:
            raise HyperFramesHandoffError(
                f"invalid duration_ms for {char.get('instance_id', '?')!r}"
            )
        durations.add(dur)
        for seg in tl.get("segments", []):
            boundaries.add(seg["start_ms"])
            boundaries.add(seg["end_ms"])

    if len(durations) > 1:
        raise HyperFramesHandoffError(
            f"duration mismatch across characters: {sorted(durations)}ms"
        )

    duration_ms = durations.pop()
    boundaries.add(duration_ms)
    sorted_bounds = sorted(boundaries)
    return sorted_bounds, duration_ms


def _intervals_from_bounds(
    bounds: List[int], duration_ms: int,
) -> List[Tuple[int, int]]:
    """Convert sorted boundaries to non-overlapping intervals.

    Each interval is (start_ms, end_ms) with no gaps.
    """
    intervals = []
    for i in range(len(bounds) - 1):
        start = bounds[i]
        end = bounds[i + 1]
        if start < end:
            intervals.append((start, end))
    if not intervals:
        raise HyperFramesHandoffError("no intervals generated from boundaries")
    if intervals[-1][1] != duration_ms:
        raise HyperFramesHandoffError(
            f"final interval end {intervals[-1][1]} != duration {duration_ms}"
        )
    return intervals


# ---------------------------------------------------------------------------
# SVG snapshot generation
# ---------------------------------------------------------------------------


def _render_snapshots(
    asset_root: Path,
    width: int,
    height: int,
    intervals: List[Tuple[int, int]],
    characters: List[dict],
) -> List[dict]:
    """Render one SVG frame per interval start timestamp.

    Returns list of {"start_ms", "end_ms", "duration_s", "svg"} dicts.
    """
    snapshots = []
    for start_ms, end_ms in intervals:
        svg_str = render_frame(asset_root, width, height, start_ms, characters)
        snapshots.append({
            "start_ms": start_ms,
            "end_ms": end_ms,
            "duration_s": round((end_ms - start_ms) / 1000.0, 6),
            "svg": svg_str,
        })
    return snapshots


# ---------------------------------------------------------------------------
# HyperFrames workspace generation
# ---------------------------------------------------------------------------


def _build_index_html(
    width: int,
    height: int,
    duration_s: float,
    composition_id: str,
    css_rel_path: str,
    composition_rel_path: str,
) -> str:
    """Build the HyperFrames index.html entry point.

    No <script> tags — offline/self-contained, no CDN, no custom JS.
    HyperFrames runtime loads compositions from the manifest.
    """
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8" />\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1" />\n'
        "  <title>Sakhalin Kids — Character Scene</title>\n"
        f'  <link rel="stylesheet" href="{css_rel_path}" />\n'
        f'  <meta name="hf-composition" content="{composition_rel_path}" />\n'
        f'  <meta name="hf-duration" content="{duration_s:.3f}" />\n'
        "</head>\n"
        "<body>\n"
        '  <div id="hf-root"></div>\n'
        "</body>\n"
        "</html>\n"
    )


def _build_styles_css() -> str:
    """Build the HyperFrames styles.css (offline, no CDN)."""
    return (
        "/* Sakhalin Kids — HyperFrames styles (SKIDS-009) */\n"
        ":root {\n"
        "  --color-bg: #9bd7ff;\n"
        "  --color-ground: #75c878;\n"
        "  --color-outline: #202632;\n"
        "}\n"
        "\n"
        "body {\n"
        "  margin: 0;\n"
        "  overflow: hidden;\n"
        "  background: var(--color-bg);\n"
        "  font-family: system-ui, sans-serif;\n"
        "}\n"
        "\n"
        "[data-composition-id] {\n"
        "  position: relative;\n"
        "  width: 100vw;\n"
        "  height: 100vh;\n"
        "  overflow: hidden;\n"
        "  background: linear-gradient(var(--color-bg) 0 65%, var(--color-ground) 65%);\n"
        "}\n"
        "\n"
        "[data-composition-id] svg {\n"
        "  width: 100%;\n"
        "  height: 100%;\n"
        "}\n"
    )


def _build_composition_html(
    width: int,
    height: int,
    duration_s: float,
    composition_id: str,
    snapshots: List[dict],
) -> str:
    """Build the HyperFrames composition HTML with inline SVGs.

    Each snapshot is rendered as a <div> with data-start/data-duration
    attributes. No JS animation — HyperFrames handles display timing.
    """
    parts = [
        f'<template id="{composition_id}">',
        f'  <div data-composition-id="{composition_id}" '
        f'data-start="0" data-duration="{duration_s:.3f}" '
        f'data-width="{width}" data-height="{height}">',
        "    <style>",
        f'      [data-composition-id="{composition_id}"] {{',
        "        position: relative;",
        f"        width: {width}px;",
        f"        height: {height}px;",
        "        overflow: hidden;",
        "        background: linear-gradient(var(--color-bg) 0 65%, var(--color-ground) 65%);",
        "      }",
        f'      [data-composition-id="{composition_id}"] svg {{',
        "        width: 100%;",
        "        height: 100%;",
        "      }",
        "    </style>",
    ]
    for snap in snapshots:
        start_s = round(snap["start_ms"] / 1000.0, 6)
        dur_s = snap["duration_s"]
        svg_str = snap["svg"]
        parts.append(
            f'    <div data-start="{start_s:.3f}" data-duration="{dur_s:.3f}">'
        )
        parts.append(f"      {svg_str}")
        parts.append("    </div>")
    parts.append("  </div>")
    parts.append("</template>")
    return "\n".join(parts) + "\n"


def _build_hyperframes_json(workspace_rel: str) -> dict:
    """Build the hyperframes.json manifest (no remote registry)."""
    return {
        "version": _HF_MANIFEST_VERSION,
        "paths": {
            "blocks": "compositions",
            "components": "compositions/components",
            "assets": "assets",
        },
    }


def _build_design_md() -> str:
    """Build DESIGN.md for the workspace."""
    return (
        "# DESIGN — Sakhalin Kids Character Scene\n"
        "\n"
        "> Generated by Sakhalin Kids HyperFrames handoff (SKIDS-009).\n"
        "\n"
        "## Colors\n"
        "\n"
        "- Background sky: `#9bd7ff`\n"
        "- Ground: `#75c878`\n"
        "- Outline: `#202632`\n"
        "\n"
        "## Notes\n"
        "\n"
        "- No CDN, no remote URLs\n"
        "- No custom animation JS\n"
        "- One SVG snapshot per unique state interval\n"
        "- Deterministic output from SvgSceneRenderer\n"
    )


def _validate_no_external_content(html: str, label: str) -> None:
    """Reject HTML containing dangerous content."""
    if _DANGEROUS_CONTENT.search(html):
        raise HyperFramesHandoffError(
            f"dangerous content detected in {label}"
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_hyperframes_workspace(
    asset_root: Path,
    output_dir: Path,
    width: int,
    height: int,
    characters: List[dict],
    composition_id: str = "sakhalin-scene",
) -> dict:
    """Build a deterministic, offline HyperFrames workspace.

    Parameters
    ----------
    asset_root:
        Directory containing SVG character assets.
    output_dir:
        Target workspace directory (created if missing).
    width, height:
        Output dimensions.
    characters:
        List of character dicts (same format as SvgSceneRenderer.render_frame).
    composition_id:
        Unique composition identifier.

    Returns
    -------
    Manifest dict with workspace_path, composition_path, duration_s, etc.
    """
    asset_root = Path(asset_root)
    output_dir = Path(output_dir)

    if not asset_root.is_dir():
        raise HyperFramesHandoffError(f"asset_root not a directory: {asset_root}")

    chars = copy.deepcopy(characters)
    bounds, duration_ms = _collect_boundaries(chars)
    intervals = _intervals_from_bounds(bounds, duration_ms)
    duration_s = round(duration_ms / 1000.0, 6)

    snapshots = _render_snapshots(asset_root, width, height, intervals, chars)

    comp_dir = output_dir / "compositions"
    assets_dir = output_dir / "assets"
    comp_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    composition_html = _build_composition_html(
        width, height, duration_s, composition_id, snapshots,
    )
    _validate_no_external_content(composition_html, "composition")

    index_html = _build_index_html(
        width, height, duration_s, composition_id,
        "styles.css", f"compositions/{composition_id}.html",
    )
    _validate_no_external_content(index_html, "index")

    styles_css = _build_styles_css()
    hf_json = _build_hyperframes_json(".")
    design_md = _build_design_md()

    (output_dir / "index.html").write_text(index_html, encoding="utf-8")
    (comp_dir / f"{composition_id}.html").write_text(
        composition_html, encoding="utf-8",
    )
    (output_dir / "styles.css").write_text(styles_css, encoding="utf-8")
    (output_dir / "hyperframes.json").write_text(
        json.dumps(hf_json, indent=2, sort_keys=True), encoding="utf-8",
    )
    (output_dir / "DESIGN.md").write_text(design_md, encoding="utf-8")

    return {
        "workspace_path": str(output_dir),
        "composition_path": str(comp_dir / f"{composition_id}.html"),
        "duration_s": duration_s,
        "duration_ms": duration_ms,
        "snapshot_count": len(snapshots),
        "interval_count": len(intervals),
        "composition_id": composition_id,
    }
