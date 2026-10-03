"""Tests for Sakhalin Kids rotation pivot normalization (SKIDS-013)."""

from __future__ import annotations

import unittest

from tools.character.sakhalin.rotation_pivot import apply_rotation_pivots

_PIVOTS = {
    "makar": {"head": (250, 270), "arm_right": (336, 290)},
    "leva": {"head": (250, 262)},
}

_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="500" height="700">'
    '<rect x="0" y="0" width="500" height="700" transform="rotate(15 250 350)"/>'
    '<g data-character-instance="makar" transform="translate(140 105)">'
    '<g data-part="head">'
    '<g data-motion-root="" transform="rotate(-5)"/>'
    "</g>"
    '<g data-part="arm_right">'
    '<g data-motion-root="" transform="rotate(-45)"/>'
    "</g>"
    '<g data-part="tail">'
    '<g data-motion-root="" transform="rotate(20 340 440)"/>'
    "</g>"
    '<g data-part="leg_left">'
    '<g data-motion-root=""/>'
    "</g>"
    "</g>"
    '<g data-character-instance="leva" transform="translate(740 105)">'
    '<g data-part="head">'
    '<g data-motion-root="" transform="rotate(-4)"/>'
    "</g>"
    '<g data-part="flipper_left">'
    '<g data-motion-root="" transform="rotate(-90)"/>'
    "</g>"
    "</g>"
    "</svg>"
)


class TRotationPivot(unittest.TestCase):
    def test_rewrites_bare_rotation_with_part_pivot(self) -> None:
        out = apply_rotation_pivots(_SVG, _PIVOTS)
        self.assertIn("rotate(-5 250 270)", out)
        self.assertIn("rotate(-45 336 290)", out)
        self.assertIn("rotate(-4 250 262)", out)
        self.assertNotIn('transform="rotate(-5)"', out)
        self.assertNotIn('transform="rotate(-45)"', out)

    def test_keeps_three_arg_rotation_untouched(self) -> None:
        out = apply_rotation_pivots(_SVG, _PIVOTS)
        self.assertIn("rotate(20 340 440)", out)
        self.assertIn("rotate(15 250 350)", out)

    def test_keeps_part_without_configured_pivot(self) -> None:
        out = apply_rotation_pivots(_SVG, _PIVOTS)
        self.assertIn('transform="rotate(-90)"', out)

    def test_none_pivots_returns_input_unchanged(self) -> None:
        self.assertEqual(apply_rotation_pivots(_SVG, None), _SVG)

    def test_empty_pivots_returns_input_unchanged(self) -> None:
        self.assertEqual(apply_rotation_pivots(_SVG, {}), _SVG)

    def test_missing_motion_root_transform_untouched(self) -> None:
        out = apply_rotation_pivots(_SVG, _PIVOTS)
        self.assertIn('data-motion-root=""', out)

    def test_deterministic(self) -> None:
        self.assertEqual(
            apply_rotation_pivots(_SVG, _PIVOTS),
            apply_rotation_pivots(_SVG, _PIVOTS),
        )

    def test_unknown_instance_untouched(self) -> None:
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<g data-character-instance="tikhon">'
            '<g data-part="head">'
            '<g data-motion-root="" transform="rotate(-7)"/>'
            "</g></g></svg>"
        )
        out = apply_rotation_pivots(svg, _PIVOTS)
        self.assertIn('transform="rotate(-7)"', out)


if __name__ == "__main__":
    unittest.main()
