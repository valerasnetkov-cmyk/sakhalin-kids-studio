"""Tests for sakhalin timeline_merger.py - SKIDS-007."""

from __future__ import annotations

import copy
import unittest

from tools.character.sakhalin.timeline_merger import (
    APPROVED_VISEMES,
    TimelineMergeError,
    merge_action_and_visemes,
)


def _fox_pose(pid: str) -> dict:
    return {
        "version": "1.0",
        "id": pid,
        "rig_profile": "fox_cartoon",
        "state": {"parts": {"head": {"rotation_deg": 0}}},
    }


def _action(**overrides) -> dict:
    base = {
        "version": "1.0",
        "id": "talk",
        "rig_profile": "fox_cartoon",
        "phases": [
            {"name": "enter", "duration_ms": 200, "pose": "talk_open"},
            {"name": "hold", "duration_ms": 500, "pose": "talk_neutral"},
            {"name": "settle", "duration_ms": 200, "pose": "idle"},
        ],
    }
    base.update(overrides)
    return base


def _viseme_timeline(**overrides) -> dict:
    base = {
        "version": "1.0",
        "id": "line_001",
        "duration_ms": 900,
        "cues": [
            {"start_ms": 0, "end_ms": 100, "viseme": "REST"},
            {"start_ms": 100, "end_ms": 300, "viseme": "L"},
            {"start_ms": 300, "end_ms": 600, "viseme": "E"},
            {"start_ms": 600, "end_ms": 900, "viseme": "S"},
        ],
    }
    base.update(overrides)
    return base


def _poses() -> dict:
    return {
        "talk_open": _fox_pose("talk_open"),
        "talk_neutral": _fox_pose("talk_neutral"),
        "idle": _fox_pose("idle"),
    }


class TestValidMerge(unittest.TestCase):

    def test_simple_merge(self) -> None:
        result = merge_action_and_visemes(
            _action(), _poses(), _viseme_timeline(),
        )
        self.assertEqual(result["version"], "1.0")
        self.assertEqual(result["rig_profile"], "fox_cartoon")
        self.assertEqual(result["duration_ms"], 900)
        self.assertGreater(len(result["segments"]), 0)

    def test_same_duration(self) -> None:
        act = _action()
        vt = _viseme_timeline()
        act_dur = sum(p["duration_ms"] for p in act["phases"])
        self.assertEqual(act_dur, vt["duration_ms"])
        result = merge_action_and_visemes(act, _poses(), vt)
        self.assertEqual(result["duration_ms"], 900)

    def test_shorter_action_holds_final_pose(self) -> None:
        act = _action(phases=[
            {"name": "enter", "duration_ms": 100, "pose": "talk_open"},
        ])
        vt = _viseme_timeline()
        result = merge_action_and_visemes(act, _poses(), vt)
        held = [s for s in result["segments"] if s["start_ms"] >= 100]
        for seg in held:
            self.assertEqual(seg["pose"], "talk_open")


class TestBoundaryUnion(unittest.TestCase):

    def test_boundaries_are_union(self) -> None:
        result = merge_action_and_visemes(
            _action(), _poses(), _viseme_timeline(),
        )
        boundaries = set()
        for seg in result["segments"]:
            boundaries.add(seg["start_ms"])
            boundaries.add(seg["end_ms"])
        self.assertIn(0, boundaries)
        self.assertIn(900, boundaries)
        self.assertIn(200, boundaries)
        self.assertIn(100, boundaries)

    def test_pose_unchanged_when_only_viseme_changes(self) -> None:
        result = merge_action_and_visemes(
            _action(), _poses(), _viseme_timeline(),
        )
        enter_segs = [s for s in result["segments"] if s["start_ms"] < 100]
        for seg in enter_segs:
            self.assertEqual(seg["pose"], "talk_open")

    def test_viseme_unchanged_when_only_pose_changes(self) -> None:
        result = merge_action_and_visemes(
            _action(), _poses(), _viseme_timeline(),
        )
        l_segs = [
            s for s in result["segments"]
            if s["start_ms"] >= 100 and s["end_ms"] <= 300
        ]
        for seg in l_segs:
            self.assertEqual(seg["viseme"], "L")


class TestOutputInvariants(unittest.TestCase):

    def test_first_segment_starts_at_zero(self) -> None:
        result = merge_action_and_visemes(
            _action(), _poses(), _viseme_timeline(),
        )
        self.assertEqual(result["segments"][0]["start_ms"], 0)

    def test_final_segment_ends_at_duration(self) -> None:
        result = merge_action_and_visemes(
            _action(), _poses(), _viseme_timeline(),
        )
        self.assertEqual(result["segments"][-1]["end_ms"], 900)

    def test_no_zero_duration_segments(self) -> None:
        result = merge_action_and_visemes(
            _action(), _poses(), _viseme_timeline(),
        )
        for seg in result["segments"]:
            self.assertLess(seg["start_ms"], seg["end_ms"])

    def test_segments_are_contiguous(self) -> None:
        result = merge_action_and_visemes(
            _action(), _poses(), _viseme_timeline(),
        )
        for i in range(1, len(result["segments"])):
            prev_end = result["segments"][i - 1]["end_ms"]
            curr_start = result["segments"][i]["start_ms"]
            self.assertEqual(prev_end, curr_start)

    def test_segments_are_ordered(self) -> None:
        result = merge_action_and_visemes(
            _action(), _poses(), _viseme_timeline(),
        )
        for i in range(1, len(result["segments"])):
            self.assertLess(
                result["segments"][i - 1]["start_ms"],
                result["segments"][i]["start_ms"],
            )


class TestPoseResolution(unittest.TestCase):

    def test_missing_pose_reference_fails(self) -> None:
        poses = {"talk_open": _fox_pose("talk_open")}
        with self.assertRaises(TimelineMergeError):
            merge_action_and_visemes(_action(), poses, _viseme_timeline())

    def test_pose_mapping_key_mismatch(self) -> None:
        poses = _poses()
        poses["talk_open"]["id"] = "wrong_id"
        with self.assertRaises(TimelineMergeError):
            merge_action_and_visemes(_action(), poses, _viseme_timeline())

    def test_rig_profile_mismatch(self) -> None:
        poses = _poses()
        poses["talk_open"]["rig_profile"] = "sea_lion_cartoon"
        with self.assertRaises(TimelineMergeError):
            merge_action_and_visemes(_action(), poses, _viseme_timeline())


class TestSchemaValidation(unittest.TestCase):

    def test_invalid_action_schema(self) -> None:
        bad = _action()
        del bad["phases"]
        with self.assertRaises(TimelineMergeError):
            merge_action_and_visemes(bad, _poses(), _viseme_timeline())

    def test_invalid_pose_schema(self) -> None:
        poses = _poses()
        poses["talk_open"]["state"]["parts"]["mouth"] = {}
        with self.assertRaises(TimelineMergeError):
            merge_action_and_visemes(_action(), poses, _viseme_timeline())

    def test_invalid_viseme_timeline_schema(self) -> None:
        bad = _viseme_timeline()
        del bad["cues"]
        with self.assertRaises(TimelineMergeError):
            merge_action_and_visemes(_action(), _poses(), bad)


class TestVisemeTemporal(unittest.TestCase):

    def test_cue_start_equals_end_fails(self) -> None:
        bad = _viseme_timeline(cues=[
            {"start_ms": 0, "end_ms": 0, "viseme": "REST"},
        ])
        bad["duration_ms"] = 0
        with self.assertRaises(TimelineMergeError):
            merge_action_and_visemes(_action(), _poses(), bad)

    def test_cue_start_greater_than_end_fails(self) -> None:
        bad = _viseme_timeline(cues=[
            {"start_ms": 100, "end_ms": 50, "viseme": "REST"},
        ])
        bad["duration_ms"] = 100
        with self.assertRaises(TimelineMergeError):
            merge_action_and_visemes(_action(), _poses(), bad)

    def test_unsorted_cues_fail(self) -> None:
        bad = _viseme_timeline(cues=[
            {"start_ms": 300, "end_ms": 600, "viseme": "E"},
            {"start_ms": 0, "end_ms": 300, "viseme": "L"},
        ])
        bad["duration_ms"] = 600
        with self.assertRaises(TimelineMergeError):
            merge_action_and_visemes(_action(), _poses(), bad)

    def test_overlapping_cues_fail(self) -> None:
        bad = _viseme_timeline(cues=[
            {"start_ms": 0, "end_ms": 200, "viseme": "REST"},
            {"start_ms": 150, "end_ms": 400, "viseme": "L"},
        ])
        bad["duration_ms"] = 400
        with self.assertRaises(TimelineMergeError):
            merge_action_and_visemes(_action(), _poses(), bad)

    def test_gap_between_cues_fails(self) -> None:
        bad = _viseme_timeline(cues=[
            {"start_ms": 0, "end_ms": 200, "viseme": "REST"},
            {"start_ms": 250, "end_ms": 400, "viseme": "L"},
        ])
        bad["duration_ms"] = 400
        with self.assertRaises(TimelineMergeError):
            merge_action_and_visemes(_action(), _poses(), bad)

    def test_first_cue_not_at_zero_fails(self) -> None:
        bad = _viseme_timeline(cues=[
            {"start_ms": 50, "end_ms": 300, "viseme": "REST"},
        ])
        bad["duration_ms"] = 300
        with self.assertRaises(TimelineMergeError):
            merge_action_and_visemes(_action(), _poses(), bad)

    def test_final_cue_not_reaching_duration_fails(self) -> None:
        bad = _viseme_timeline(cues=[
            {"start_ms": 0, "end_ms": 400, "viseme": "REST"},
        ])
        bad["duration_ms"] = 900
        with self.assertRaises(TimelineMergeError):
            merge_action_and_visemes(_action(), _poses(), bad)


class TestActionDuration(unittest.TestCase):

    def test_action_longer_than_viseme_fails(self) -> None:
        act = _action(phases=[
            {"name": "a", "duration_ms": 500, "pose": "talk_open"},
            {"name": "b", "duration_ms": 500, "pose": "talk_neutral"},
        ])
        vt = _viseme_timeline()
        with self.assertRaises(TimelineMergeError):
            merge_action_and_visemes(act, _poses(), vt)

    def test_action_duration_exact_equal_passes(self) -> None:
        act = _action()
        vt = _viseme_timeline()
        result = merge_action_and_visemes(act, _poses(), vt)
        self.assertEqual(result["duration_ms"], 900)


class TestVisemeSemantics(unittest.TestCase):

    def test_adjacent_identical_visemes_accepted(self) -> None:
        vt = _viseme_timeline(cues=[
            {"start_ms": 0, "end_ms": 450, "viseme": "REST"},
            {"start_ms": 450, "end_ms": 900, "viseme": "REST"},
        ])
        result = merge_action_and_visemes(_action(), _poses(), vt)
        self.assertEqual(result["duration_ms"], 900)

    def test_rest_is_accepted_normally(self) -> None:
        vt = _viseme_timeline(cues=[
            {"start_ms": 0, "end_ms": 900, "viseme": "REST"},
        ])
        result = merge_action_and_visemes(_action(), _poses(), vt)
        for seg in result["segments"]:
            self.assertEqual(seg["viseme"], "REST")

    def test_all_10_visemes_can_participate(self) -> None:
        visemes = ["REST", "A", "E", "O", "U", "MBP", "FV", "SH", "L", "S"]
        dur = len(visemes) * 100
        vt = _viseme_timeline(
            duration_ms=dur,
            cues=[
                {"start_ms": i * 100, "end_ms": (i + 1) * 100, "viseme": v}
                for i, v in enumerate(visemes)
            ],
        )
        act = _action(phases=[
            {"name": "a", "duration_ms": dur, "pose": "talk_open"},
        ])
        result = merge_action_and_visemes(act, _poses(), vt)
        self.assertEqual(result["duration_ms"], dur)
        visemes_in_output = {s["viseme"] for s in result["segments"]}
        self.assertTrue(visemes_in_output.issubset(APPROVED_VISEMES))


class TestImmutability(unittest.TestCase):

    def test_inputs_not_mutated(self) -> None:
        act = _action()
        poses = _poses()
        vt = _viseme_timeline()
        act_copy = copy.deepcopy(act)
        poses_copy = copy.deepcopy(poses)
        vt_copy = copy.deepcopy(vt)
        merge_action_and_visemes(act, poses, vt)
        self.assertEqual(act, act_copy)
        self.assertEqual(poses, poses_copy)
        self.assertEqual(vt, vt_copy)

    def test_same_input_produces_identical_output(self) -> None:
        act = _action()
        poses = _poses()
        vt = _viseme_timeline()
        r1 = merge_action_and_visemes(act, poses, vt)
        r2 = merge_action_and_visemes(act, poses, vt)
        self.assertEqual(r1, r2)


class TestOwnershipBoundary(unittest.TestCase):

    def test_no_metadata_in_output(self) -> None:
        result = merge_action_and_visemes(
            _action(), _poses(), _viseme_timeline(),
        )
        forbidden = {
            "character_id", "scene_id", "episode_id",
            "audio_asset_id", "audio_path", "provider", "renderer", "fps",
        }
        self.assertTrue(forbidden.isdisjoint(result.keys()))

    def test_no_mouth_in_pose_state(self) -> None:
        result = merge_action_and_visemes(
            _action(), _poses(), _viseme_timeline(),
        )
        for seg in result["segments"]:
            self.assertIn("pose", seg)
            self.assertIn("viseme", seg)
            self.assertNotIn("state", seg)

    def test_output_segments_have_exactly_pose_and_viseme(self) -> None:
        result = merge_action_and_visemes(
            _action(), _poses(), _viseme_timeline(),
        )
        for seg in result["segments"]:
            keys = set(seg.keys())
            self.assertEqual(keys, {"start_ms", "end_ms", "pose", "viseme"})


if __name__ == "__main__":
    unittest.main()
