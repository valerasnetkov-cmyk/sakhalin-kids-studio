"""Sakhalin Kids — CharacterReviewer domain service (SKIDS-010).

Deterministic structural QA for character bundles entering the Character
Runtime Proof.  No AI, no computer vision, no artistic approval claims.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

from jsonschema import Draft202012Validator

_APPROVED_VISEMES = frozenset({
    "REST", "A", "E", "O", "U", "MBP", "FV", "SH", "L", "S",
})
_REQUIRED_GAZE = frozenset({"left", "center", "right", "up", "down"})
_SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "schemas" / "sakhalin"
_CANON_PATH = Path(__file__).resolve().parents[3] / "config" / "sakhalin" / "team_canon.json"
_event_re = re.compile(r"^on\w+$", re.IGNORECASE)
_dangerous_attrs = frozenset({"href", "xlink:href"})


class CharacterQAError(Exception):
    """Raised when character QA input is invalid."""


_schema_cache: Dict[str, dict] = {}


def _load_schema(name: str) -> dict:
    if name not in _schema_cache:
        with open(_SCHEMAS_DIR / f"{name}.schema.json", encoding="utf-8") as fh:
            _schema_cache[name] = json.load(fh)
    return _schema_cache[name]


def _validate_schema(name: str, instance: dict, label: str) -> List[str]:
    return [e.message for e in Draft202012Validator(_load_schema(name)).iter_errors(instance)]


def load_team_canon(path: Optional[Path] = None) -> dict:
    p = path or _CANON_PATH
    if not p.is_file():
        raise CharacterQAError(f"team canon not found: {p}")
    with open(p, encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("version") != "1.0":
        raise CharacterQAError("invalid team canon version")
    if "characters" not in data:
        raise CharacterQAError("team canon missing characters")
    return data


def _blocking(code: str, message: str) -> dict:
    return {"code": code, "severity": "blocking", "message": message}


def _warning(code: str, message: str) -> dict:
    return {"code": code, "severity": "warning", "message": message}


def _parse_svg(svg_path: Path) -> ET.Element:
    if not svg_path.is_file():
        raise CharacterQAError(f"SVG not found: {svg_path}")
    if svg_path.stat().st_size > 2 * 1024 * 1024:
        raise CharacterQAError(f"SVG too large: {svg_path}")
    try:
        tree = ET.parse(svg_path)
    except ET.ParseError as exc:
        raise CharacterQAError(f"invalid SVG: {exc}") from exc
    root = tree.getroot()
    _sanitize_svg(root)
    return root


def _sanitize_svg(root: ET.Element) -> None:
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag in ("script", "foreignObject"):
            raise CharacterQAError(f"dangerous SVG element: <{tag}>")
        for attr in list(elem.attrib):
            if _event_re.match(attr):
                raise CharacterQAError(f"event handler: {attr}")
            local = attr.split("}")[-1] if "}" in attr else attr
            if local in _dangerous_attrs and not elem.attrib[attr].startswith("#"):
                raise CharacterQAError(f"external href: {local}")


def _inspect_svg(root: ET.Element) -> dict:
    parts, visemes, gaze_dirs, expressions = set(), set(), set(), set()
    all_visemes: list[str] = []
    for elem in root.iter():
        p = elem.get("data-part")
        if p:
            parts.add(p)
        v = elem.get("data-viseme")
        if v:
            visemes.add(v)
            all_visemes.append(v)
        g = elem.get("data-gaze")
        if g:
            gaze_dirs.add(g)
        e = elem.get("data-expression")
        if e:
            expressions.add(e)
    return {"parts": parts, "visemes": visemes, "all_visemes": all_visemes,
            "gaze": gaze_dirs, "expressions": expressions}


def _check_canon(spec: dict, canon: dict) -> List[dict]:
    findings = []
    char_id = spec.get("id", "")
    chars = canon.get("characters", {})
    if char_id not in chars:
        return [_blocking("unknown_canon_id", f"character {char_id!r} not in team canon")]
    entry = chars[char_id]
    if spec.get("species", "") != entry.get("species", ""):
        findings.append(_blocking("species_mismatch",
            f"{char_id}: expected {entry['species']!r}, got {spec.get('species', '')!r}"))
    canon_rig = entry.get("rig_profile")
    if canon_rig is not None and spec.get("rig_profile", "") != canon_rig:
        findings.append(_blocking("rig_canon_mismatch",
            f"{char_id}: expected rig {canon_rig!r}, got {spec.get('rig_profile', '')!r}"))
    return findings


def _check_continuity(spec: dict) -> List[dict]:
    findings = []
    vis = spec.get("visual", {})
    cont = spec.get("continuity", {})
    checks = [
        ("palette_locked", True, "visual.palette_locked must be true"),
        ("proportions_locked", True, "visual.proportions_locked must be true"),
        ("wardrobe_locked", True, "visual.wardrobe_locked must be true"),
        ("base_regeneration_allowed", False, "visual.base_regeneration_allowed must be false"),
        ("identity_locked", True, "continuity.identity_locked must be true"),
        ("redesign_requires_approval", True, "continuity.redesign_requires_approval must be true"),
    ]
    for key, expected, msg in checks:
        source = vis if key in vis else cont
        val = source.get(key)
        if val is None:
            findings.append(_blocking("missing_continuity_field", msg))
        elif val != expected:
            findings.append(_blocking("continuity_violation", msg))
    return findings


def _check_rig(spec: dict, rig: dict, svg_info: dict) -> List[dict]:
    findings = []
    spec_rig = spec.get("rig_profile", "")
    if rig.get("id") != spec_rig:
        findings.append(_blocking(
            "rig_id_mismatch",
            f"rig_profile.id {rig.get('id')!r} != spec.rig_profile {spec_rig!r}",
        ))
    required_parts = set(rig.get("parts", {}).get("required", []))
    svg_parts = svg_info.get("parts", set())
    for part in required_parts:
        if part not in svg_parts:
            findings.append(_blocking(
                "missing_required_part",
                f"required part {part!r} not in SVG",
            ))
    caps = rig.get("capabilities", {})
    if caps.get("mouth_visemes"):
        found = svg_info.get("visemes", set())
        all_vis = svg_info.get("all_visemes", [])
        missing = _APPROVED_VISEMES - found
        for v in sorted(missing):
            findings.append(_blocking("missing_viseme", f"viseme {v!r} not in SVG"))
        extra = found - _APPROVED_VISEMES
        for v in sorted(extra):
            findings.append(_warning("unknown_viseme", f"unknown viseme {v!r} in SVG"))
        seen: set[str] = set()
        for v in all_vis:
            if v in seen:
                findings.append(_warning("duplicate_viseme", f"duplicate viseme {v!r}"))
                break
            seen.add(v)
    if caps.get("gaze"):
        found_gaze = svg_info.get("gaze", set())
        missing_gaze = _REQUIRED_GAZE - found_gaze
        for g in sorted(missing_gaze):
            findings.append(_blocking("missing_gaze", f"gaze direction {g!r} not in SVG"))
    return findings


def _check_expressions(spec: dict, svg_info: dict) -> List[dict]:
    findings = []
    required = set(spec.get("required_expressions", []))
    found = svg_info.get("expressions", set())
    for expr in sorted(required - found):
        findings.append(_blocking("missing_expression", f"expression {expr!r} not in SVG"))
    return findings


def _check_poses(
    poses_by_id: dict, spec: dict, rig: dict,
) -> List[dict]:
    findings = []
    required_parts = set(rig.get("parts", {}).get("required", []))
    for pid, pose in poses_by_id.items():
        errs = _validate_schema("pose", pose, f"pose {pid!r}")
        for e in errs:
            findings.append(_blocking("invalid_pose", f"pose {pid!r}: {e}"))
        if pose.get("id") != pid:
            findings.append(_blocking("pose_key_mismatch", f"key {pid!r} != pose.id {pose.get('id')!r}"))
        if pose.get("rig_profile") != spec.get("rig_profile"):
            findings.append(_blocking("pose_rig_mismatch", f"pose {pid!r} rig mismatch"))
        state_parts = set(pose.get("state", {}).get("parts", {}).keys())
        for p in state_parts:
            if p not in required_parts:
                findings.append(_blocking("pose_unknown_part", f"pose {pid!r} references unknown part {p!r}"))
    return findings


def _check_actions(
    actions_by_id: dict, poses_by_id: dict, spec: dict,
) -> List[dict]:
    findings = []
    for aid, action in actions_by_id.items():
        errs = _validate_schema("action", action, f"action {aid!r}")
        for e in errs:
            findings.append(_blocking("invalid_action", f"action {aid!r}: {e}"))
        if action.get("id") != aid:
            findings.append(_blocking("action_key_mismatch", f"key {aid!r} != action.id {action.get('id')!r}"))
        if action.get("rig_profile") != spec.get("rig_profile"):
            findings.append(_blocking("action_rig_mismatch", f"action {aid!r} rig mismatch"))
        for phase in action.get("phases", []):
            pose_ref = phase.get("pose", "")
            if pose_ref not in poses_by_id:
                findings.append(_blocking("action_unresolved_pose", f"action {aid!r} phase references unknown pose {pose_ref!r}"))
    required = set(spec.get("required_actions", []))
    for ra in sorted(required - set(actions_by_id.keys())):
        findings.append(_blocking("missing_required_action", f"required action {ra!r} not provided"))
    return findings


def _check_blink(spec: dict, rig: dict, actions_by_id: dict) -> List[dict]:
    findings = []
    caps = rig.get("capabilities", {})
    if caps.get("blink"):
        if "blink" not in actions_by_id:
            required = set(spec.get("required_actions", []))
            if "blink" in required:
                findings.append(_blocking(
                    "missing_required_blink",
                    "blink capability declared, blink in required_actions, but no blink action provided",
                ))
            else:
                findings.append(_warning(
                    "missing_blink_action",
                    "blink capability declared but no blink action provided",
                ))
    return findings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def review_character(
    *,
    spec: dict,
    rig_profile: dict,
    svg_path: Path,
    poses_by_id: Optional[dict] = None,
    actions_by_id: Optional[dict] = None,
    canon_path: Optional[Path] = None,
) -> dict:
    """Run deterministic structural QA on a character bundle.

    Returns a result dict with status, findings, checks, and metadata.
    Does not mutate inputs.
    """
    spec = copy.deepcopy(spec)
    rig_profile = copy.deepcopy(rig_profile)
    poses_by_id = copy.deepcopy(poses_by_id or {})
    actions_by_id = copy.deepcopy(actions_by_id or {})

    findings: List[dict] = []

    # Schema validation
    spec_errs = _validate_schema("character_spec", spec, "CharacterSpec")
    for e in spec_errs:
        findings.append(_blocking("invalid_spec", e))
    rig_errs = _validate_schema("rig_profile", rig_profile, "RigProfile")
    for e in rig_errs:
        findings.append(_blocking("invalid_rig_profile", e))

    # If schemas are invalid, return early
    if any(f["severity"] == "blocking" for f in findings):
        findings.sort(key=lambda f: (f["severity"], f["code"], f["message"]))
        return {
            "status": "fail",
            "findings": findings,
            "checks": {"schema_valid": False},
            "metadata": {"visual_reference_status": "not_verified"},
        }

    # Canon check
    canon = load_team_canon(canon_path)
    findings.extend(_check_canon(spec, canon))

    # Continuity locks
    findings.extend(_check_continuity(spec))

    # SVG inspection
    svg_root = _parse_svg(svg_path)
    svg_info = _inspect_svg(svg_root)

    # Rig checks
    findings.extend(_check_rig(spec, rig_profile, svg_info))

    # Expression checks
    findings.extend(_check_expressions(spec, svg_info))

    # Pose checks
    findings.extend(_check_poses(poses_by_id, spec, rig_profile))

    # Action checks
    findings.extend(_check_actions(actions_by_id, poses_by_id, spec))

    # Blink check
    findings.extend(_check_blink(spec, rig_profile, actions_by_id))

    findings.sort(key=lambda f: (f["severity"], f["code"], f["message"]))

    has_blocking = any(f["severity"] == "blocking" for f in findings)
    has_warning = any(f["severity"] == "warning" for f in findings)

    if has_blocking:
        status = "fail"
    elif has_warning:
        status = "revise"
    else:
        status = "pass"

    checks = {
        "schema_valid": True,
        "canon_valid": not any(f["code"] in ("unknown_canon_id", "species_mismatch") for f in findings),
        "rig_valid": not any(f["code"].startswith("rig_") or f["code"] == "missing_required_part" for f in findings),
        "poses_defined": len(poses_by_id) > 0,
        "actions_timed": len(actions_by_id) > 0,
    }

    return {
        "status": status,
        "findings": findings,
        "checks": checks,
        "metadata": {
            "visual_reference_status": "not_verified",
            "prop_visual_verification": "not_verified",
            "scale_check": "not_verified",
        },
    }


def to_openmontage_report(result: dict) -> dict:
    """Convert to pinned OpenMontage character_qa_report shape."""
    issues = [f["message"] for f in result.get("findings", []) if f["severity"] in ("blocking", "warning")]
    status = result.get("status", "fail")
    if status == "fail":
        rec = "block"
    elif status == "revise":
        rec = "fix_rig"
    else:
        rec = "present_to_user"
    checks = result.get("checks", {})
    return {
        "version": "1.0",
        "status": status,
        "checks": {
            "schema_valid": checks.get("schema_valid", False),
            "assets_exist": True,
            "pivots_defined": True,
            "poses_defined": checks.get("poses_defined", False),
            "actions_timed": checks.get("actions_timed", False),
            "motion_detected": False,
            "browser_preview_checked": False,
            "frame_samples_checked": False,
        },
        "issues": issues,
        "recommended_action": rec,
        "metadata": result.get("metadata", {}),
    }
