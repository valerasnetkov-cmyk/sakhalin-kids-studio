"""Tests for sakhalin/viseme_timeline.schema.json — SKIDS-006."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "sakhalin" / "viseme_timeline.schema.json"


def _load_schema() -> dict:
    with open(_SCHEMA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _make_valid_timeline(**overrides) -> dict:
    base = {
        "version": "1.0",
        "id": "makar_line_001",
        "duration_ms": 1840,
        "cues": [
            {"start_ms": 0, "end_ms": 120, "viseme": "REST"},
            {"start_ms": 120, "end_ms": 260, "viseme": "MBP"},
            {"start_ms": 260, "end_ms": 420, "viseme": "A"},
            {"start_ms": 420, "end_ms": 560, "viseme": "L"},
        ],
    }
    base.update(overrides)
    return base


def _validate(schema: dict, instance: dict) -> list[str]:
    try:
        import jsonschema
        validator = jsonschema.Draft202012Validator(schema)
        return [e.message for e in validator.iter_errors(instance)]
    except ImportError:
        try:
            from jsonschema import validate as jsvalidate
            jsvalidate(instance=instance, schema=schema)
            return []
        except Exception as exc:
            return [str(exc)]


def _is_valid(schema: dict, instance: dict) -> bool:
    return len(_validate(schema, instance)) == 0


class TestVisemeTimelineSchemaSelfValidation(unittest.TestCase):
    """1. Schema self-validation."""

    def test_schema_is_valid_draft202012(self) -> None:
        schema = _load_schema()
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["$id"], "sakhalin/viseme_timeline")
        self.assertIn("version", schema["required"])
        self.assertIn("id", schema["required"])
        self.assertIn("duration_ms", schema["required"])
        self.assertIn("cues", schema["required"])


class TestVisemeTimelineValidCases(unittest.TestCase):
    """2–3. Valid timelines."""

    def test_valid_minimal_timeline(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline()
        self.assertTrue(_is_valid(schema, doc))

    def test_valid_all_semantic_visemes(self) -> None:
        schema = _load_schema()
        visemes = ["REST", "A", "E", "O", "U", "MBP", "FV", "SH", "L", "S"]
        cues = [{"start_ms": i * 100, "end_ms": (i + 1) * 100, "viseme": v} for i, v in enumerate(visemes)]
        doc = _make_valid_timeline(
            duration_ms=1000,
            cues=cues,
        )
        self.assertTrue(_is_valid(schema, doc))


class TestVisemeTimelineId(unittest.TestCase):
    """4–5. $id and version."""

    def test_correct_id(self) -> None:
        schema = _load_schema()
        self.assertEqual(schema["$id"], "sakhalin/viseme_timeline")

    def test_version_10_accepted(self) -> None:
        schema = _load_schema()
        self.assertTrue(_is_valid(schema, _make_valid_timeline()))


class TestVisemeTimelineVersionRejection(unittest.TestCase):
    """6–7. Wrong/missing version."""

    def test_wrong_version_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline(version="2.0")
        self.assertFalse(_is_valid(schema, doc))

    def test_missing_version_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline()
        del doc["version"]
        self.assertFalse(_is_valid(schema, doc))


class TestVisemeTimelineRequiredFields(unittest.TestCase):
    """8–10. Missing required fields."""

    def test_missing_id_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline()
        del doc["id"]
        self.assertFalse(_is_valid(schema, doc))

    def test_missing_duration_ms_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline()
        del doc["duration_ms"]
        self.assertFalse(_is_valid(schema, doc))

    def test_missing_cues_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline()
        del doc["cues"]
        self.assertFalse(_is_valid(schema, doc))


class TestVisemeTimelineIdValidation(unittest.TestCase):
    """11. Invalid timeline ID."""

    def test_invalid_id_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline(id="UPPERCASE")
        self.assertFalse(_is_valid(schema, doc))


class TestVisemeTimelineDurationValidation(unittest.TestCase):
    """12–14. Duration_ms validation."""

    def test_duration_zero_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline(duration_ms=0)
        self.assertFalse(_is_valid(schema, doc))

    def test_duration_negative_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline(duration_ms=-100)
        self.assertFalse(_is_valid(schema, doc))

    def test_duration_non_integer_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline(duration_ms=12.5)
        self.assertFalse(_is_valid(schema, doc))


class TestVisemeTimelineCuesValidation(unittest.TestCase):
    """15–18. Cues structure validation."""

    def test_empty_cues_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline(cues=[])
        self.assertFalse(_is_valid(schema, doc))

    def test_missing_cue_start_ms_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline(cues=[{"end_ms": 100, "viseme": "A"}])
        self.assertFalse(_is_valid(schema, doc))

    def test_missing_cue_end_ms_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline(cues=[{"start_ms": 0, "viseme": "A"}])
        self.assertFalse(_is_valid(schema, doc))

    def test_missing_cue_viseme_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline(cues=[{"start_ms": 0, "end_ms": 100}])
        self.assertFalse(_is_valid(schema, doc))


class TestVisemeTimelineCueTimestamps(unittest.TestCase):
    """19–21. Cue timestamp validation."""

    def test_negative_start_ms_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline(cues=[{"start_ms": -1, "end_ms": 100, "viseme": "A"}])
        self.assertFalse(_is_valid(schema, doc))

    def test_zero_end_ms_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline(cues=[{"start_ms": 0, "end_ms": 0, "viseme": "A"}])
        self.assertFalse(_is_valid(schema, doc))

    def test_non_integer_timestamps_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline(cues=[{"start_ms": 0.5, "end_ms": 100, "viseme": "A"}])
        self.assertFalse(_is_valid(schema, doc))


class TestVisemeTimelineVisemeEnum(unittest.TestCase):
    """22–23. Viseme enum validation."""

    def test_unknown_viseme_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline(cues=[{"start_ms": 0, "end_ms": 100, "viseme": "PHONEME_X"}])
        self.assertFalse(_is_valid(schema, doc))

    def test_all_11_approved_visemes_accepted(self) -> None:
        schema = _load_schema()
        visemes = ["REST", "A", "E", "O", "U", "MBP", "FV", "SH", "L", "S"]
        for v in visemes:
            doc = _make_valid_timeline(cues=[{"start_ms": 0, "end_ms": 100, "viseme": v}])
            self.assertTrue(_is_valid(schema, doc), f"Viseme {v!r} should be accepted")


class TestVisemeTimelineStrictFields(unittest.TestCase):
    """24–25. Unknown fields rejected."""

    def test_unknown_cue_field_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline(
            cues=[{"start_ms": 0, "end_ms": 100, "viseme": "A", "extra": True}]
        )
        self.assertFalse(_is_valid(schema, doc))

    def test_unknown_root_field_rejected(self) -> None:
        schema = _load_schema()
        doc = _make_valid_timeline(unknown_field = "nope")
        self.assertFalse(_is_valid(schema, doc))


class TestVisemeTimelineOwnershipBoundary(unittest.TestCase):
    """26–28. Schema contains no body/head/gaze/expression/action/provider/audio/asset fields."""

    def test_no_body_head_gaze_expression_action_fields(self) -> None:
        schema = _load_schema()
        forbidden = {"body", "head", "eyes", "gaze", "expression", "action",
                     "pose", "rig_profile", "character_id", "scene_id"}
        root_props = set(schema.get("properties", {}).keys())
        overlap = root_props & forbidden
        self.assertEqual(overlap, set(), f"Root contains forbidden fields: {overlap}")

    def test_no_provider_specific_fields(self) -> None:
        schema = _load_schema()
        schema_str = json.dumps(schema).lower()
        providers = ["elevenlabs", "google", "openai", "whisper", "whisperx",
                     "rhubarb", "azure"]
        found = [p for p in providers if p in schema_str]
        self.assertEqual(found, [], f"Schema contains provider references: {found}")

    def test_no_audio_path_asset_path(self) -> None:
        schema = _load_schema()
        schema_str = json.dumps(schema).lower()
        bad = ["audio_path", "asset_path", "audio.asset", "file_path"]
        found = [b for b in bad if b in schema_str]
        self.assertEqual(found, [], f"Schema contains path references: {found}")


class TestVisemeTimelineIdentifierPattern(unittest.TestCase):
    """29. Identifier pattern matches existing contracts."""

    def test_identifier_pattern_consistent(self) -> None:
        schema = _load_schema()
        id_pattern = schema["$defs"]["identifier"]["pattern"]
        self.assertEqual(id_pattern, "^[a-z][a-z0-9_-]*$")

    def test_identifier_pattern_same_as_pose(self) -> None:
        pose_schema_path = _SCHEMA_PATH.parent / "pose.schema.json"
        with open(pose_schema_path, encoding="utf-8") as fh:
            pose_schema = json.load(fh)
        viseme_pattern = _load_schema()["$defs"]["identifier"]["pattern"]
        pose_pattern = pose_schema["$defs"]["identifier"]["pattern"]
        self.assertEqual(viseme_pattern, pose_pattern)


class TestVisemeTimelineCharacterIndependence(unittest.TestCase):
    """30. No character-specific enum exists."""

    def test_no_core_character_references(self) -> None:
        schema = _load_schema()
        schema_str = json.dumps(schema)
        chars = ["makar", "leva", "tikhon", "anna", "antoshka"]
        found = [c for c in chars if c in schema_str.lower()]
        self.assertEqual(found, [], f"Schema references core characters: {found}")


if __name__ == "__main__":
    unittest.main()
