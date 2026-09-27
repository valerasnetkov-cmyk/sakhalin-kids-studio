"""Tests for renderer handoff manifest (SKIDS-009)."""

import unittest

from tools.character.sakhalin.render_handoff import (
    RenderHandoffError,
    build_render_handoff,
)


def _spec(**overrides) -> dict:
    data = {
        "scene_id": "scene_01",
        "renderer": "remotion",
        "fps": 30,
        "duration_seconds": 2.0,
        "frame_assets": [
            {"frame": 0, "svg_asset_id": "scene_01_frame_0000"},
            {"frame": 30, "svg_asset_id": "scene_01_frame_0030"},
            {"frame": 59, "svg_asset_id": "scene_01_frame_0059"},
        ],
        "audio_asset_id": "dialogue_scene_01_mix",
    }
    data.update(overrides)
    return data


class TestHandoff(unittest.TestCase):
    def test_builds_locked_handoff(self):
        result = build_render_handoff(_spec())
        self.assertEqual(result["version"], "1.0")
        self.assertEqual(result["renderer"], "remotion")
        self.assertFalse(result["character_mutation_allowed"])

    def test_hyperframes_is_allowed(self):
        result = build_render_handoff(_spec(renderer="hyperframes"))
        self.assertEqual(result["renderer"], "hyperframes")


class TestRendererBoundary(unittest.TestCase):
    def test_unknown_renderer_is_rejected(self):
        with self.assertRaises(RenderHandoffError):
            build_render_handoff(_spec(renderer="after-effects"))

    def test_paths_and_urls_are_not_valid_asset_ids(self):
        for bad in ("../frame.svg", "https://example.com/frame.svg", "/tmp/frame.svg"):
            with self.subTest(bad=bad):
                spec = _spec(frame_assets=[{"frame": 0, "svg_asset_id": bad}])
                with self.assertRaises(RenderHandoffError):
                    build_render_handoff(spec)

    def test_unknown_root_field_rejected(self):
        with self.assertRaises(RenderHandoffError):
            build_render_handoff(_spec(prompt="change makar design"))

    def test_unknown_frame_field_rejected(self):
        spec = _spec(frame_assets=[
            {"frame": 0, "svg_asset_id": "frame_0", "href": "https://example.com"}
        ])
        with self.assertRaises(RenderHandoffError):
            build_render_handoff(spec)


class TestTimingValidation(unittest.TestCase):
    def test_invalid_fps_rejected(self):
        for fps in (0, 121, 29.97, True):
            with self.subTest(fps=fps):
                with self.assertRaises(RenderHandoffError):
                    build_render_handoff(_spec(fps=fps))

    def test_non_finite_duration_rejected(self):
        for value in (float("nan"), float("inf"), 0):
            with self.subTest(value=value):
                with self.assertRaises(RenderHandoffError):
                    build_render_handoff(_spec(duration_seconds=value))

    def test_unsorted_frames_rejected(self):
        spec = _spec(frame_assets=[
            {"frame": 10, "svg_asset_id": "frame_10"},
            {"frame": 5, "svg_asset_id": "frame_05"},
        ])
        with self.assertRaises(RenderHandoffError):
            build_render_handoff(spec)

    def test_frame_outside_duration_rejected(self):
        spec = _spec(
            duration_seconds=1.0,
            frame_assets=[{"frame": 30, "svg_asset_id": "frame_30"}],
        )
        with self.assertRaises(RenderHandoffError):
            build_render_handoff(spec)

    def test_duplicate_asset_ids_rejected(self):
        spec = _spec(frame_assets=[
            {"frame": 0, "svg_asset_id": "frame_same"},
            {"frame": 1, "svg_asset_id": "frame_same"},
        ])
        with self.assertRaises(RenderHandoffError):
            build_render_handoff(spec)


class TestIdentityValidation(unittest.TestCase):
    def test_scene_id_must_be_stable(self):
        with self.assertRaises(RenderHandoffError):
            build_render_handoff(_spec(scene_id="../scene"))

    def test_audio_asset_id_must_be_stable(self):
        with self.assertRaises(RenderHandoffError):
            build_render_handoff(_spec(audio_asset_id="audio.wav"))


if __name__ == "__main__":
    unittest.main()
