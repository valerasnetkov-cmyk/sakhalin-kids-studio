"""Tests for safe deterministic SVG scene renderer (SKIDS-008)."""

import unittest

from tools.character.sakhalin.svg_renderer import SvgRenderError, render_svg_scene


def _scene(**overrides) -> dict:
    data = {
        "width": 1280,
        "height": 720,
        "background": "#DCEAF4",
        "characters": [
            {
                "character_id": "makar",
                "x": 320,
                "y": 580,
                "scale": 1.0,
                "parts": [
                    {"id": "body", "path": "M 0 0 L 80 0 L 80 120 L 0 120 Z", "fill": "#E77A22"},
                    {"id": "head", "path": "M 10 -70 C 20 -110 70 -110 80 -70 Z", "fill": "#F29236"},
                ],
            }
        ],
    }
    data.update(overrides)
    return data


class TestRendering(unittest.TestCase):
    def test_renders_deterministic_svg(self):
        first = render_svg_scene(_scene())
        second = render_svg_scene(_scene())
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("<svg "))
        self.assertIn('id="character-makar"', first)
        self.assertIn('id="body"', first)
        self.assertTrue(first.endswith("</svg>\n"))

    def test_normalizes_hex_colors(self):
        scene = _scene(background="#dceaf4")
        scene["characters"][0]["parts"][0]["fill"] = "#e77a22"
        output = render_svg_scene(scene)
        self.assertIn('fill="#DCEAF4"', output)
        self.assertIn('fill="#E77A22"', output)


class TestSceneValidation(unittest.TestCase):
    def test_unknown_scene_field_is_rejected(self):
        with self.assertRaises(SvgRenderError):
            render_svg_scene(_scene(script="<script/>"))

    def test_empty_characters_rejected(self):
        with self.assertRaises(SvgRenderError):
            render_svg_scene(_scene(characters=[]))

    def test_duplicate_character_ids_rejected(self):
        character = _scene()["characters"][0]
        with self.assertRaises(SvgRenderError):
            render_svg_scene(_scene(characters=[character, character]))

    def test_invalid_dimensions_rejected(self):
        for width in (0, 8193, 1280.5, True):
            with self.subTest(width=width):
                with self.assertRaises(SvgRenderError):
                    render_svg_scene(_scene(width=width))


class TestCharacterValidation(unittest.TestCase):
    def test_extra_character_field_rejected(self):
        scene = _scene()
        scene["characters"][0]["href"] = "https://example.com/x.svg"
        with self.assertRaises(SvgRenderError):
            render_svg_scene(scene)

    def test_non_finite_transform_rejected(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                scene = _scene()
                scene["characters"][0]["x"] = value
                with self.assertRaises(SvgRenderError):
                    render_svg_scene(scene)

    def test_scale_is_bounded(self):
        for value in (0, 20.1):
            with self.subTest(value=value):
                scene = _scene()
                scene["characters"][0]["scale"] = value
                with self.assertRaises(SvgRenderError):
                    render_svg_scene(scene)


class TestPartValidation(unittest.TestCase):
    def test_external_href_is_not_supported(self):
        scene = _scene()
        scene["characters"][0]["parts"][0]["href"] = "https://example.com/x.svg"
        with self.assertRaises(SvgRenderError):
            render_svg_scene(scene)

    def test_script_or_markup_in_path_is_rejected(self):
        bad_paths = [
            '<script>alert(1)</script>',
            'M 0 0 L 10 10" onload="alert(1)',
            "url(javascript:alert(1))",
        ]
        for path in bad_paths:
            with self.subTest(path=path):
                scene = _scene()
                scene["characters"][0]["parts"][0]["path"] = path
                with self.assertRaises(SvgRenderError):
                    render_svg_scene(scene)

    def test_css_color_syntax_is_rejected(self):
        for color in ("red", "rgb(1,2,3)", "url(#gradient)", "#FFF"):
            with self.subTest(color=color):
                scene = _scene()
                scene["characters"][0]["parts"][0]["fill"] = color
                with self.assertRaises(SvgRenderError):
                    render_svg_scene(scene)

    def test_duplicate_part_ids_rejected(self):
        scene = _scene()
        scene["characters"][0]["parts"].append(
            {"id": "body", "path": "M 0 0 L 1 1 Z", "fill": "#000000"}
        )
        with self.assertRaises(SvgRenderError):
            render_svg_scene(scene)


if __name__ == "__main__":
    unittest.main()
