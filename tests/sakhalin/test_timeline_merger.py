"""Tests for acting + mouth timeline merge (SKIDS-007)."""

from __future__ import annotations

import copy
import unittest

from tools.character.sakhalin.timeline_merger import (
    TimelineMergeError,
    merge_character_timelines,
)


def _acting(**overrides) -> dict:
    data = {
        "version": "1.0",
        "character_id": "makar",
        "events": [
            {"t": 0.0, "channel": "action", "value": "idle"},
            {"t": 0.4, "channel": "gaze", "value": "leva"},
            {"t": 0.8, "channel": "gesture", "value": "point"},
        ],
    }
    data.update(overrides)
    return data


def _mouth(**overrides) -> dict:
    data = {
        "version": "1.0",
        "character_id": "makar",
        "audio_asset_id": "dialogue_scene_01_makar",
        "start_seconds": 0.5,
        "events": [
            {"t": 0.0, "viseme": "REST"},
            {"t": 0.1, "viseme": "A"},
            {"t": 0.2, "viseme": "S"},
        ],
    }
    data.update(overrides)
    return data


class TestMerge(unittest.TestCase):
    def test_merges_into_independent_tracks(self):
        merged = merge_character_timelines(_acting(), _mouth())
        self.assertEqual(merged["character_id"], "makar")
        self.assertEqual(merged["audio_asset_id"], "dialogue_scene_01_makar")
        self.assertEqual(
            merged["tracks"]["acting"][1],
            {"t": 0.4, "channel": "gaze", "value": "leva"},
        )
        self.assertEqual(
            merged["tracks"]["mouth"][1],
            {"t": 0.6, "viseme": "A"},
        )

    def test_applies_mouth_start_offset(self):
        merged = merge_character_timelines(_acting(), _mouth(start_seconds=2.0))
        self.assertEqual(merged["tracks"]["mouth"][0]["t"], 2.0)
        self.assertEqual(merged["tracks"]["mouth"][2]["t"], 2.2)

    def test_does_not_mutate_inputs(self):
        acting = _acting()
        mouth = _mouth()
        acting_before = copy.deepcopy(acting)
        mouth_before = copy.deepcopy(mouth)
        merge_character_timelines(acting, mouth)
        self.assertEqual(acting, acting_before)
        self.assertEqual(mouth, mouth_before)

    def test_same_timestamp_is_allowed(self):
        acting = _acting(events=[
            {"t": 0.0, "channel": "action", "value": "idle"},
            {"t": 0.0, "channel": "gaze", "value": "leva"},
        ])
        merged = merge_character_timelines(acting, _mouth())
        self.assertEqual(len(merged["tracks"]["acting"]), 2)


class TestRootValidation(unittest.TestCase):
    def test_extra_acting_root_field_is_rejected(self):
        with self.assertRaises(TimelineMergeError):
            merge_character_timelines(_acting(provider="example"), _mouth())

    def test_extra_mouth_root_field_is_rejected(self):
        with self.assertRaises(TimelineMergeError):
            merge_character_timelines(_acting(), _mouth(provider="example"))


class TestIdentity(unittest.TestCase):
    def test_character_mismatch_is_rejected(self):
        with self.assertRaises(TimelineMergeError):
            merge_character_timelines(_acting(), _mouth(character_id="leva"))

    def test_invalid_character_identifier_is_rejected(self):
        with self.assertRaises(TimelineMergeError):
            merge_character_timelines(_acting(character_id="Макар"), _mouth())

    def test_invalid_audio_asset_identifier_is_rejected(self):
        with self.assertRaises(TimelineMergeError):
            merge_character_timelines(_acting(), _mouth(audio_asset_id="../audio.wav"))

    def test_unicode_identifier_is_rejected(self):
        with self.assertRaises(TimelineMergeError):
            merge_character_timelines(_acting(character_id="éclair"), _mouth())


class TestActingIsolation(unittest.TestCase):
    def test_acting_cannot_control_mouth(self):
        for channel in ("mouth", "viseme", "lip_sync"):
            with self.subTest(channel=channel):
                bad = _acting(events=[
                    {"t": 0.0, "channel": channel, "value": "A"},
                ])
                with self.assertRaises(TimelineMergeError):
                    merge_character_timelines(bad, _mouth())

    def test_unknown_acting_channel_is_rejected(self):
        bad = _acting(events=[
            {"t": 0.0, "channel": "renderer", "value": "remotion"},
        ])
        with self.assertRaises(TimelineMergeError):
            merge_character_timelines(bad, _mouth())

    def test_extra_acting_fields_are_rejected(self):
        bad = _acting(events=[
            {
                "t": 0.0,
                "channel": "head",
                "value": "look_right",
                "script": "doSomething()",
            }
        ])
        with self.assertRaises(TimelineMergeError):
            merge_character_timelines(bad, _mouth())


class TestTimelineValidation(unittest.TestCase):
    def test_unsorted_acting_events_are_rejected(self):
        bad = _acting(events=[
            {"t": 1.0, "channel": "action", "value": "idle"},
            {"t": 0.5, "channel": "gaze", "value": "leva"},
        ])
        with self.assertRaises(TimelineMergeError):
            merge_character_timelines(bad, _mouth())

    def test_unsorted_mouth_events_are_rejected(self):
        bad = _mouth(events=[
            {"t": 0.2, "viseme": "A"},
            {"t": 0.1, "viseme": "REST"},
        ])
        with self.assertRaises(TimelineMergeError):
            merge_character_timelines(_acting(), bad)

    def test_negative_times_are_rejected(self):
        cases = [
            (_acting(events=[{"t": -0.1, "channel": "action", "value": "idle"}]), _mouth()),
            (_acting(), _mouth(events=[{"t": -0.1, "viseme": "REST"}])),
            (_acting(), _mouth(start_seconds=-0.1)),
        ]
        for acting, mouth in cases:
            with self.subTest(acting=acting, mouth=mouth):
                with self.assertRaises(TimelineMergeError):
                    merge_character_timelines(acting, mouth)

    def test_unknown_viseme_is_rejected(self):
        bad = _mouth(events=[{"t": 0.0, "viseme": "TH"}])
        with self.assertRaises(TimelineMergeError):
            merge_character_timelines(_acting(), bad)

    def test_extra_mouth_fields_are_rejected(self):
        bad = _mouth(events=[
            {"t": 0.0, "viseme": "REST", "head_rotation": 10}
        ])
        with self.assertRaises(TimelineMergeError):
            merge_character_timelines(_acting(), bad)

    def test_empty_event_tracks_are_rejected(self):
        with self.assertRaises(TimelineMergeError):
            merge_character_timelines(_acting(events=[]), _mouth())
        with self.assertRaises(TimelineMergeError):
            merge_character_timelines(_acting(), _mouth(events=[]))

    def test_event_count_is_bounded(self):
        acting_events = [
            {"t": 0.0, "channel": "action", "value": "idle"}
            for _ in range(5001)
        ]
        with self.assertRaises(TimelineMergeError):
            merge_character_timelines(_acting(events=acting_events), _mouth())

        mouth_events = [{"t": 0.0, "viseme": "REST"} for _ in range(5001)]
        with self.assertRaises(TimelineMergeError):
            merge_character_timelines(_acting(), _mouth(events=mouth_events))


if __name__ == "__main__":
    unittest.main()
