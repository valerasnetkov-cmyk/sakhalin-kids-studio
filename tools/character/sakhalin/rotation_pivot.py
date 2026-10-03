"""Sakhalin Kids — rotation pivot normalization (SKIDS-013).

SvgSceneRenderer emits bare SVG `rotate(angle)` transforms, which rotate
around the canvas origin. Anatomical pivots (art coordinates) are applied
here, at the HTML embedding boundary: a bare rotation on a motion-root
inside a configured character part is rewritten to `rotate(angle cx cy)`.
Deterministic; parts without a configured pivot keep the renderer output.
"""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET
from typing import Dict, Optional, Tuple

_Pivots = Dict[str, Dict[str, Tuple[float, float]]]
_BARE_ROTATE_RE = re.compile(r"rotate\((-?\d+(?:\.\d+)?)\)")


def _find_pivot(
    elem: ET.Element,
    parents: Dict[ET.Element, ET.Element],
    pivots_by_instance: _Pivots,
) -> Optional[Tuple[float, float]]:
    """Resolve pivot via nearest data-part ancestor in a character instance."""
    part_id: Optional[str] = None
    instance_id: Optional[str] = None
    node = parents.get(elem)
    while node is not None:
        if part_id is None and "data-part" in node.attrib:
            part_id = node.get("data-part")
        if "data-character-instance" in node.attrib:
            instance_id = node.get("data-character-instance")
            break
        node = parents.get(node)
    if instance_id is None or part_id is None:
        return None
    return pivots_by_instance.get(instance_id, {}).get(part_id)


def apply_rotation_pivots(
    svg_str: str,
    pivots_by_instance: Optional[_Pivots],
) -> str:
    """Rewrite bare part rotations to pivot-relative rotations.

    `pivots_by_instance` maps instance_id -> data-part id -> (cx, cy) in
    character art coordinates. Only transforms exactly matching `rotate(angle)`
    on a motion-root whose part has a configured pivot are rewritten.
    """
    if not pivots_by_instance:
        return svg_str
    root = ET.fromstring(svg_str)
    parents = {child: parent for parent in root.iter() for child in parent}
    for elem in root.iter():
        if "data-motion-root" not in elem.attrib:
            continue
        match = _BARE_ROTATE_RE.fullmatch(elem.get("transform", ""))
        if match is None:
            continue
        pivot = _find_pivot(elem, parents, pivots_by_instance)
        if pivot is None:
            continue
        cx, cy = pivot
        elem.set("transform", f"rotate({match.group(1)} {cx:g} {cy:g})")
    return ET.tostring(root, encoding="unicode")
