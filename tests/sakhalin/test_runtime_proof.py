"""Unit tests for SKIDS-013 proof timing helpers."""

import unittest

from tools.character.sakhalin.runtime_proof import (
    DURATION_MS,
    VISEMES,
    build_scene_action,
    build_viseme_timeline,
)


class TestVisemeTimelineBuilder(unittest.TestCase):
    def test_timeline_is_contiguous_and_full_length(self):
        timeline = build_viseme_timeline(
            "fixture",
            1200,
            2400,
            ("A", "E", "O", "U"),
        )
        cues = timeline["cues"]
        self.assertEqual(cues[0]["start_ms"], 0)
        self.assertEqual(cues[-1]["end_ms"], DURATION_MS)

        for left, right in zip(cues, cues[1:]):
            self.assertEqual(left["end_ms"], right["start_ms"])

    def test_timeline_uses_only_semantic_visemes(self):
        timeline = build_viseme_timeline(
            "fixture",
            900,
            1800,
            ("REST", "MBP", "FV", "SH", "L", "S"),
        )
        allowed = set(VISEMES)
        self.assertTrue(all(cue["viseme"] in allowed for cue in timeline["cues"]))

    def test_invalid_viseme_is_rejected(self):
        with self.assertRaises(ValueError):
            build_viseme_timeline("fixture", 900, 1800, ("TH",))

    def test_dialogue_must_fit_proof_duration(self):
        with self.assertRaises(ValueError):
            build_viseme_timeline(
                "fixture",
                DURATION_MS - 100,
                500,
                ("A",),
            )


class TestSceneActionBuilder(unittest.TestCase):
    def test_action_spans_full_proof_duration(self):
        action = build_scene_action(
            "makar_proof_action",
            "fox_cartoon",
            talk_start_ms=1200,
            speech_ms=2400,
            gesture_pose="point_right",
            talk_pose="talk_neutral",
        )
        total = sum(phase["duration_ms"] for phase in action["phases"])
        self.assertEqual(total, DURATION_MS)
        self.assertEqual(action["phases"][1]["pose"], "point_right")
        self.assertEqual(action["phases"][2]["pose"], "talk_neutral")

    def test_no_settle_time_is_rejected(self):
        with self.assertRaises(ValueError):
            build_scene_action(
                "bad",
                "fox_cartoon",
                talk_start_ms=11_000,
                speech_ms=1_500,
                gesture_pose="point_right",
                talk_pose="talk_neutral",
            )


if __name__ == "__main__":
    unittest.main()
