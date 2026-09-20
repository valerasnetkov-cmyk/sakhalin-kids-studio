"""Sakhalin Kids — SvgSceneRenderer domain service (SKIDS-008).

Deterministic, frame-oriented SVG scene renderer for character animation.
"""

from __future__ import annotations

import copy
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_SVG_BYTES = 2 * 1024 * 1024  # 2 MiB
_APPROVED_VISEMES = frozenset({
    "REST", "A", "E", "O", "U", "MBP", "FV", "SH", "L", "S",
})
_XMLNS = "http://www.w3.org/2000/svg"
_EVENT_RE = re.compile(r"^on\w+$", re.IGNORECASE)
_DANGEROUS_ATTRS = frozenset({"href", "xlink:href"})

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class SvgRenderError(Exception):
    """Raised when SVG rendering fails validation or structural checks."""


# ---------------------------------------------------------------------------
# Safe SVG loading
# ---------------------------------------------------------------------------


def _resolve_asset(asset_root: Path, rel_path: str) -> Path:
    if not isinstance(rel_path, str) or not rel_path:
        raise SvgRenderError("invalid asset path")
    if "/" in rel_path and rel_path.startswith(("/", "..")):
        raise SvgRenderError(f"unsafe asset path: {rel_path!r}")
    resolved = (asset_root / rel_path).resolve()
    if not str(resolved).startswith(str(asset_root.resolve())):
        raise SvgRenderError(f"asset escapes asset_root: {rel_path!r}")
    if not resolved.suffix.lower() == ".svg":
        raise SvgRenderError(f"non-SVG asset: {rel_path!r}")
    if not resolved.is_file():
        raise SvgRenderError(f"asset not found: {rel_path!r}")
    if resolved.stat().st_size > _MAX_SVG_BYTES:
        raise SvgRenderError(f"asset too large: {rel_path!r}")
    return resolved


def _load_svg(path: Path) -> ET.Element:
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise SvgRenderError(f"invalid SVG: {exc}") from exc
    root = tree.getroot()
    _sanitize_svg(root)
    return root


def _sanitize_svg(root: ET.Element) -> None:
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag in ("script", "foreignObject"):
            raise SvgRenderError(f"dangerous element: <{tag}>")
        for attr in list(elem.attrib):
            if _EVENT_RE.match(attr):
                raise SvgRenderError(f"event handler attribute: {attr}")
            local = attr.split("}")[-1] if "}" in attr else attr
            if local in _DANGEROUS_ATTRS:
                val = elem.attrib[attr]
                if not val.startswith("#"):
                    raise SvgRenderError(f"external href: {local}={val!r}")


# ---------------------------------------------------------------------------
# Merged timeline validation
# ---------------------------------------------------------------------------


def _validate_merged_timeline(timeline: dict, label: str) -> None:
    if not isinstance(timeline, dict):
        raise SvgRenderError(f"invalid merged timeline for {label}")
    dur = timeline.get("duration_ms", 0)
    if not isinstance(dur, int) or dur <= 0:
        raise SvgRenderError(f"invalid duration_ms for {label}")
    segs = timeline.get("segments", [])
    if not segs:
        raise SvgRenderError(f"empty segments for {label}")
    for i, seg in enumerate(segs):
        if not all(k in seg for k in ("start_ms", "end_ms", "pose", "viseme")):
            raise SvgRenderError(f"incomplete segment at {i} for {label}")
        if seg["start_ms"] >= seg["end_ms"]:
            raise SvgRenderError(f"invalid segment range at {i} for {label}")
        if seg["viseme"] not in _APPROVED_VISEMES:
            raise SvgRenderError(f"unknown viseme {seg['viseme']!r} at {i}")
    if segs[0]["start_ms"] != 0:
        raise SvgRenderError(f"first segment does not start at 0 for {label}")
    if segs[-1]["end_ms"] != dur:
        raise SvgRenderError(f"final segment end != duration for {label}")
    for i in range(1, len(segs)):
        if segs[i]["start_ms"] != segs[i - 1]["end_ms"]:
            raise SvgRenderError(
                f"non-contiguous segments at {i} for {label}"
            )


# ---------------------------------------------------------------------------
# Pose resolution
# ---------------------------------------------------------------------------


def _resolve_segment_pose(
    segment: dict,
    poses_by_id: Dict[str, dict],
    rig_profile: str,
) -> dict:
    pose_id = segment["pose"]
    if pose_id not in poses_by_id:
        raise SvgRenderError(f"missing pose: {pose_id!r}")
    pose = poses_by_id[pose_id]
    if pose.get("id") != pose_id:
        raise SvgRenderError(
            f"pose key {pose_id!r} != pose.id {pose.get('id')!r}"
        )
    if pose.get("rig_profile") != rig_profile:
        raise SvgRenderError(
            f"pose rig mismatch: {pose_id!r} "
            f"has {pose.get('rig_profile')!r}, expected {rig_profile!r}"
        )
    return pose


def _find_active_segment(
    timeline: dict, timestamp_ms: int,
) -> dict:
    for seg in timeline["segments"]:
        if seg["start_ms"] <= timestamp_ms < seg["end_ms"]:
            return seg
    raise SvgRenderError(
        f"timestamp {timestamp_ms}ms outside timeline range"
    )


# ---------------------------------------------------------------------------
# SVG rendering helpers
# ---------------------------------------------------------------------------


def _get_rig_profile(root: ET.Element) -> str:
    rp = root.get("data-rig-profile", "")
    if not rp:
        raise SvgRenderError("SVG missing data-rig-profile")
    return rp


def _apply_pose_to_svg(
    svg_root: ET.Element, pose: dict,
) -> None:
    state = pose.get("state", {})
    parts = state.get("parts", {})
    for part_id, part_state in parts.items():
        elems = svg_root.findall(f".//*[@data-part='{part_id}']")
        if not elems:
            raise SvgRenderError(f"missing SVG part: {part_id!r}")
        if len(elems) > 1:
            raise SvgRenderError(f"duplicate data-part: {part_id!r}")
        elem = elems[0]
        if "rotation_deg" in part_state:
            roots = elem.findall(".//*[@data-motion-root]")
            if not roots:
                raise SvgRenderError(
                    f"no motion root for part: {part_id!r}"
                )
            if len(roots) > 1:
                raise SvgRenderError(
                    f"duplicate motion root in part: {part_id!r}"
                )
            roots[0].set("transform", f"rotate({part_state['rotation_deg']})")
        if "variant" in part_state:
            variant = part_state["variant"]
            found = False
            for vg in elem.findall(".//*[@data-variant]"):
                if vg.get("data-variant") == variant:
                    vg.attrib.pop("display", None)
                    found = True
                else:
                    vg.set("display", "none")
            if not found:
                raise SvgRenderError(
                    f"missing variant {variant!r} in part {part_id!r}"
                )
        elif elem.get("data-default-variant"):
            for vg in elem.findall(".//*[@data-variant]"):
                if vg.get("data-variant") == elem.get("data-default-variant"):
                    vg.attrib.pop("display", None)
                else:
                    vg.set("display", "none")


def _apply_expression(svg_root: ET.Element, pose: dict) -> None:
    state = pose.get("state", {})
    expr = state.get("expression")
    if not expr:
        return
    elems = svg_root.findall(".//*[@data-expression]")
    if not elems:
        raise SvgRenderError("no expression layers in SVG")
    found = False
    for e in elems:
        if e.get("data-expression") == expr:
            e.attrib.pop("display", None)
            found = True
        else:
            e.set("display", "none")
    if not found:
        raise SvgRenderError(f"missing expression: {expr!r}")


def _apply_gaze(svg_root: ET.Element, pose: dict) -> None:
    state = pose.get("state", {})
    gaze = state.get("gaze", {})
    direction = gaze.get("direction") if isinstance(gaze, dict) else None
    if not direction:
        return
    elems = svg_root.findall(".//*[@data-gaze]")
    if not elems:
        raise SvgRenderError("no gaze layers in SVG")
    found = False
    for e in elems:
        if e.get("data-gaze") == direction:
            e.attrib.pop("display", None)
            found = True
        else:
            e.set("display", "none")
    if not found:
        raise SvgRenderError(f"missing gaze direction: {direction!r}")


def _apply_viseme(svg_root: ET.Element, viseme: str) -> None:
    mouth = svg_root.findall(".//*[@data-part='mouth']")
    if not mouth:
        raise SvgRenderError("no mouth part in SVG")
    mouth_elem = mouth[0]
    found = False
    for v in mouth_elem.findall(".//*[@data-viseme]"):
        if v.get("data-viseme") == viseme:
            v.attrib.pop("display", None)
            found = True
        else:
            v.set("display", "none")
    if not found:
        raise SvgRenderError(f"missing viseme: {viseme!r}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_frame(
    asset_root: Path,
    width: int,
    height: int,
    timestamp_ms: int,
    characters: List[dict],
    background_path: Optional[str] = None,
) -> str:
    """Render a single deterministic SVG frame.

    Parameters
    ----------
    asset_root:
        Directory containing SVG character assets.
    width, height:
        Output SVG dimensions.
    timestamp_ms:
        Frame timestamp.
    characters:
        List of character instance dicts with keys:
        instance_id, asset_path, x, y, scale, timeline, poses_by_id.
    background_path:
        Optional relative path to background SVG.

    Returns
    -------
    Complete SVG document string.
    """
    asset_root = Path(asset_root)
    canvas = ET.Element("svg")
    canvas.set("xmlns", _XMLNS)
    canvas.set("width", str(width))
    canvas.set("height", str(height))
    canvas.set("viewBox", f"0 0 {width} {height}")

    if background_path:
        bg_path = _resolve_asset(asset_root, background_path)
        bg_root = _load_svg(bg_path)
        for child in bg_root:
            canvas.append(child)

    for char in characters:
        inst_id = char.get("instance_id", "")
        asset_path = char.get("asset_path", "")
        x = char.get("x", 0)
        y = char.get("y", 0)
        scale = char.get("scale", 1.0)
        timeline = char.get("timeline", {})
        poses_by_id = char.get("poses_by_id", {})

        if not isinstance(x, (int, float)) or not math.isfinite(x):
            raise SvgRenderError(f"invalid x for {inst_id!r}")
        if not isinstance(y, (int, float)) or not math.isfinite(y):
            raise SvgRenderError(f"invalid y for {inst_id!r}")
        if not isinstance(scale, (int, float)) or not math.isfinite(scale) or scale <= 0:
            raise SvgRenderError(f"invalid scale for {inst_id!r}")

        _validate_merged_timeline(timeline, inst_id)

        if timestamp_ms < 0 or timestamp_ms >= timeline["duration_ms"]:
            raise SvgRenderError(
                f"timestamp {timestamp_ms}ms out of range for {inst_id!r}"
            )

        segment = _find_active_segment(timeline, timestamp_ms)
        pose = _resolve_segment_pose(segment, poses_by_id, timeline["rig_profile"])

        svg_path = _resolve_asset(asset_root, asset_path)
        svg_root = _load_svg(svg_path)

        svg_rig = _get_rig_profile(svg_root)
        if svg_rig != timeline["rig_profile"]:
            raise SvgRenderError(
                f"rig mismatch for {inst_id!r}: "
                f"SVG has {svg_rig!r}, timeline has {timeline['rig_profile']!r}"
            )

        _apply_pose_to_svg(svg_root, pose)
        _apply_expression(svg_root, pose)
        _apply_gaze(svg_root, pose)
        _apply_viseme(svg_root, segment["viseme"])

        char_group = ET.Element("g")
        char_group.set("data-character-instance", inst_id)
        char_group.set("transform", f"translate({x} {y}) scale({scale})")
        for child in svg_root:
            char_group.append(child)
        canvas.append(char_group)

    ET.indent(canvas, space="  ")
    return ET.tostring(canvas, encoding="unicode", xml_declaration=False)
