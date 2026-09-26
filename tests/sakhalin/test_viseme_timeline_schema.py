"""Tests for Sakhalin Kids semantic viseme contract (SKIDS-006)."""

import json
import pathlib
import unittest

from jsonschema import Draft202012Validator, ValidationError

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "sakhalin" / "viseme_timeline.schema.json"
CHAR_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "sakhalin" / "character_spec.schema.json"

SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
CHAR_SCHEMA = json.loads(CHAR_SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)

SEMANTIC_VISEMES = ["REST", "A", "E", "O", "U", "MBP", "FV", "SH", "L", "S"]


def _timeline(**overrides) -> dict:
    data = {
        "version": "1.0",
        "character_id": "makar",
        "audio_asset_id": "dialogue_scene_01_makar",
        "start_seconds": 0.0,
        "events": [
            {"t": 0.00, "viseme": "A"},
            {"t": 0.10, "viseme": "S"},
            {"t": 0.19, "viseme": "E"},
            {"t": 0.31, "viseme": "REST"},
        ],
    }
    data.update(overrides)
    return data


class TestSchema(unittest.TestCase):
    def test_schema_is_valid_draft202012(self):
        Draft202012Validator.check_schema(SCHEMA)

    def test_identifier_pattern_matches_character_contract(self):
        self.assertEqual(
            SCHEMA["$defs"]["identifier"]["pattern"],
            CHAR_SCHEMA["$defs"]["identifier"]["pattern"],
        )

    def test_viseme_enum_matches_documented_mvp_set(self):
        self.assertEqual(SCHEMA["$defs"]["viseme"]["enum"], SEMANTIC_VISEMES)


class TestValidTimeline(unittest.TestCase):
    def test_documented_example_is_valid(self):
        VALIDATOR.validate(_timeline())

    def test_every_semantic_viseme_is_accepted(self):
        events = [
            {"t": index * 0.1, "viseme": viseme}
            for index, viseme in enumerate(SEMANTIC_VISEMES)
        ]
        VALIDATOR.validate(_timeline(events=events))


class TestRequiredFields(unittest.TestCase):
    def test_required_fields_cannot_be_removed(self):
        for field in (
            "version",
            "character_id",
            "audio_asset_id",
            "start_seconds",
            "events",
        ):
            with self.subTest(field=field):
                data = _timeline()
                del data[field]
                with self.assertRaises(ValidationError):
                    VALIDATOR.validate(data)


class TestClosedContract(unittest.TestCase):
    def test_unknown_viseme_is_rejected(self):
        data = _timeline(events=[{"t": 0.0, "viseme": "TH"}])
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(data)

    def test_lowercase_viseme_is_rejected(self):
        data = _timeline(events=[{"t": 0.0, "viseme": "rest"}])
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(data)

    def test_unknown_root_field_is_rejected(self):
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(_timeline(provider="example"))

    def test_unknown_event_field_is_rejected(self):
        data = _timeline(events=[{"t": 0.0, "viseme": "REST", "duration": 0.1}])
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(data)


class TestTimeBounds(unittest.TestCase):
    def test_negative_start_is_rejected(self):
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(_timeline(start_seconds=-0.01))

    def test_negative_event_time_is_rejected(self):
        data = _timeline(events=[{"t": -0.01, "viseme": "REST"}])
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(data)

    def test_extreme_event_time_is_rejected(self):
        data = _timeline(events=[{"t": 3600.01, "viseme": "REST"}])
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(data)


class TestEventBounds(unittest.TestCase):
    def test_events_cannot_be_empty(self):
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(_timeline(events=[]))

    def test_event_count_is_bounded(self):
        events = [{"t": 0.0, "viseme": "REST"} for _ in range(5001)]
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(_timeline(events=events))


class TestIdentityFields(unittest.TestCase):
    def test_character_id_is_stable_identifier(self):
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(_timeline(character_id="Макар"))

    def test_audio_asset_id_is_stable_identifier(self):
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(_timeline(audio_asset_id="../audio.wav"))

    def test_version_is_locked(self):
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(_timeline(version="2.0"))


if __name__ == "__main__":
    unittest.main()
