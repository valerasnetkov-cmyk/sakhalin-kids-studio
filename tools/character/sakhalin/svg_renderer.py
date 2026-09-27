"""Deterministic safe SVG scene renderer for Character Runtime proof (SKIDS-008).

The renderer accepts only a narrow declarative vector subset: path geometry,
solid hex fills, character placement, and scale. It never injects arbitrary SVG,
HTML, script, external references, CSS, or event-handler attributes.
"""

from __future__ import annotations

from html import escape
import math
import re
from typing import Any, Mapping, Sequence

_ID_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
_HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_PATH_RE = re.compile(r"^[MmLlHhVvCcSsQqTtAaZz0-9eE+.,\-\s]+$")
_MAX_CHARACTERS = 16
_MAX_PARTS_PER_CHARACTER = 128
_MAX_PATH_LENGTH = 20000


class SvgRenderError(ValueError):
    """Raised when scene data is invalid or outside the safe SVG subset."""


def render_svg_scene(scene: Mapping[str, Any]) -> str:
    """Render a validated scene into deterministic SVG text."""

    normalized = _validate_scene(scene)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{normalized["width"]}" '
        f'height="{normalized["height"]}" viewBox="0 0 {normalized["width"]} {normalized["height"]}">',
        f'  <rect width="100%" height="100%" fill="{normalized["background"]}"/>',
    ]

    for character in normalized["characters"]:
        transform = (
            f'translate({character["x"]:.3f} {character["y"]:.3f}) '
            f'scale({character["scale"]:.5f})'
        )
        lines.append(
            f'  <g id="character-{escape(character["character_id"])}" '
            f'transform="{transform}">'
        )
        for part in character["parts"]:
            lines.append(
                f'    <path id="{escape(part["id"])}" d="{escape(part["path"])}" '
                f'fill="{part["fill"]}"/>'
            )
        lines.append("  </g>")

    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _validate_scene(scene: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(scene, Mapping):
        raise SvgRenderError("scene must be a mapping")
    if set(scene) != {"width", "height", "background", "characters"}:
        raise SvgRenderError("scene contains unsupported fields")

    width = _bounded_int(scene.get("width"), "width", 1, 8192)
    height = _bounded_int(scene.get("height"), "height", 1, 8192)
    background = _color(scene.get("background"), "background")

    characters = scene.get("characters")
    if not isinstance(characters, Sequence) or isinstance(characters, (str, bytes)):
        raise SvgRenderError("characters must be a sequence")
    if len(characters) == 0:
        raise SvgRenderError("characters must not be empty")
    if len(characters) > _MAX_CHARACTERS:
        raise SvgRenderError("too many characters")

    normalized_characters = [
        _validate_character(character, index)
        for index, character in enumerate(characters)
    ]

    ids = [character["character_id"] for character in normalized_characters]
    if len(ids) != len(set(ids)):
        raise SvgRenderError("character IDs must be unique within a scene")

    return {
        "width": width,
        "height": height,
        "background": background,
        "characters": normalized_characters,
    }


def _validate_character(value: Any, index: int) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise SvgRenderError(f"character {index} must be a mapping")
    if set(value) != {"character_id", "x", "y", "scale", "parts"}:
        raise SvgRenderError(f"character {index} contains unsupported fields")

    character_id = _identifier(value.get("character_id"), f"character {index}.character_id")
    x = _finite_number(value.get("x"), f"character {index}.x", -16384, 16384)
    y = _finite_number(value.get("y"), f"character {index}.y", -16384, 16384)
    scale = _finite_number(value.get("scale"), f"character {index}.scale", 0.01, 20)

    parts = value.get("parts")
    if not isinstance(parts, Sequence) or isinstance(parts, (str, bytes)):
        raise SvgRenderError(f"character {index}.parts must be a sequence")
    if len(parts) == 0:
        raise SvgRenderError(f"character {index}.parts must not be empty")
    if len(parts) > _MAX_PARTS_PER_CHARACTER:
        raise SvgRenderError(f"character {index} has too many parts")

    normalized_parts = [
        _validate_part(part, index, part_index)
        for part_index, part in enumerate(parts)
    ]
    part_ids = [part["id"] for part in normalized_parts]
    if len(part_ids) != len(set(part_ids)):
        raise SvgRenderError(f"character {index} has duplicate part IDs")

    return {
        "character_id": character_id,
        "x": x,
        "y": y,
        "scale": scale,
        "parts": normalized_parts,
    }


def _validate_part(value: Any, character_index: int, part_index: int) -> dict[str, str]:
    label = f"character {character_index}.part {part_index}"
    if not isinstance(value, Mapping):
        raise SvgRenderError(f"{label} must be a mapping")
    if set(value) != {"id", "path", "fill"}:
        raise SvgRenderError(f"{label} contains unsupported fields")

    part_id = _identifier(value.get("id"), f"{label}.id")
    path = value.get("path")
    if not isinstance(path, str) or not path.strip():
        raise SvgRenderError(f"{label}.path must be non-empty")
    if len(path) > _MAX_PATH_LENGTH:
        raise SvgRenderError(f"{label}.path is too long")
    if not _PATH_RE.fullmatch(path):
        raise SvgRenderError(f"{label}.path contains unsupported characters")

    fill = _color(value.get("fill"), f"{label}.fill")
    return {"id": part_id, "path": path, "fill": fill}


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise SvgRenderError(f"{field} must be a stable identifier")
    return value


def _color(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _HEX_COLOR_RE.fullmatch(value):
        raise SvgRenderError(f"{field} must be a six-digit hex color")
    return value.upper()


def _bounded_int(value: Any, field: str, minimum: int, maximum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise SvgRenderError(f"{field} must be an integer")
    if value < minimum or value > maximum:
        raise SvgRenderError(f"{field} is outside allowed bounds")
    return value


def _finite_number(value: Any, field: str, minimum: float, maximum: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise SvgRenderError(f"{field} must be numeric")
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < minimum or numeric > maximum:
        raise SvgRenderError(f"{field} is outside allowed bounds")
    return numeric
