"""Tests for Sakhalin Kids Action schema (SKIDS-005)."""

import json
import pathlib
import unittest

from jsonschema import Draft202012Validator, ValidationError

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
ACTION_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "sakhalin" / "action.schema.json"
POSE_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "sakhalin" / "pose.schema.json"

ACTION_SCHEMA = json.loads(ACTION_SCHEMA_PATH.read_text(encoding="utf-8"))
POSE_SCHEMA = json.loads(POSE_SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(ACTION_SCHEMA)
POSE_VALIDATOR = Draft202012Validator(POSE_SCHEMA)


def _valid_action(**overrides) -> dict:
    action = {
        "version": "1.0",
        "id": "point",
        "rig_profile": "fox_cartoon",
        "phases": [
            {"name": "move", "duration_ms": 320, "pose": "point_right"},
        ],
    }
    action.update(overrides)
    return action


def _schema_property_names(schema: object) -> set[str]:
    names: set[str] = set()
    if isinstance(schema, dict):
        properties = schema.get("properties")
        if isinstance(properties, dict):
            names.update(properties)
        for value in schema.values():
            names.update(_schema_property_names(value))
    elif isinstance(schema, list):
        for value in schema:
            names.update(_schema_property_names(value))
    return names


class TestActionSchema(unittest.TestCase):
    def test_01_schema_self_validation(self):
        Draft202012Validator.check_schema(ACTION_SCHEMA)

    def test_02_valid_point_action(self):
        action = _valid_action(
            phases=[
                {"name": "anticipation", "duration_ms": 180, "pose": "idle"},
                {"name": "move", "duration_ms": 320, "pose": "point_right"},
                {"name": "hold", "duration_ms": 500, "pose": "point_right"},
                {"name": "settle", "duration_ms": 260, "pose": "idle"},
            ]
        )
        VALIDATOR.validate(action)

    def test_03_valid_blink_action(self):
        action = _valid_action(
            id="blink",
            phases=[
                {"name": "close", "duration_ms": 90, "pose": "blink_closed"},
                {"name": "open", "duration_ms": 110, "pose": "idle"},
            ],
        )
        VALIDATOR.validate(action)

    def test_04_valid_think_action(self):
        action = _valid_action(
            id="think",
            rig_profile="sea_lion_cartoon",
            phases=[
                {"name": "raise", "duration_ms": 240, "pose": "think"},
                {"name": "hold", "duration_ms": 650, "pose": "think"},
                {"name": "settle", "duration_ms": 220, "pose": "idle"},
            ],
        )
        VALIDATOR.validate(action)

    def test_05_valid_talk_body_action_without_mouth_data(self):
        action = _valid_action(
            id="talk",
            phases=[
                {"name": "enter", "duration_ms": 160, "pose": "talk_body_open"},
                {"name": "hold", "duration_ms": 500, "pose": "talk_body_neutral"},
                {"name": "settle", "duration_ms": 180, "pose": "idle"},
            ],
        )
        VALIDATOR.validate(action)
        self.assertNotIn("mouth", json.dumps(action))

    def test_06_missing_required_root_field_fails(self):
        for field in ("version", "id", "rig_profile", "phases"):
            with self.subTest(field=field):
                action = _valid_action()
                del action[field]
                with self.assertRaises(ValidationError):
                    VALIDATOR.validate(action)

    def test_07_invalid_action_id_fails(self):
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(_valid_action(id="Point Action"))

    def test_08_invalid_rig_profile_id_fails(self):
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(_valid_action(rig_profile="Sea Lion"))

    def test_09_empty_phases_fails(self):
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(_valid_action(phases=[]))

    def test_10_missing_phase_field_fails(self):
        for field in ("name", "duration_ms", "pose"):
            with self.subTest(field=field):
                phase = {"name": "move", "duration_ms": 100, "pose": "idle"}
                del phase[field]
                with self.assertRaises(ValidationError):
                    VALIDATOR.validate(_valid_action(phases=[phase]))

    def test_11_duration_ms_zero_fails(self):
        action = _valid_action(phases=[{"name": "hold", "duration_ms": 0, "pose": "idle"}])
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(action)

    def test_12_duration_ms_negative_fails(self):
        action = _valid_action(phases=[{"name": "hold", "duration_ms": -1, "pose": "idle"}])
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(action)

    def test_13_duration_ms_non_integer_fails(self):
        action = _valid_action(phases=[{"name": "hold", "duration_ms": 120.5, "pose": "idle"}])
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(action)

    def test_14_invalid_pose_reference_fails(self):
        action = _valid_action(phases=[{"name": "move", "duration_ms": 100, "pose": "Point Right"}])
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(action)

    def test_15_unknown_phase_field_fails(self):
        phase = {"name": "move", "duration_ms": 100, "pose": "idle", "easing": "linear"}
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(_valid_action(phases=[phase]))

    def test_16_unknown_root_field_fails(self):
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(_valid_action(character_id="makar"))

    def test_17_schema_contains_no_mouth_viseme_or_audio_fields(self):
        names = _schema_property_names(ACTION_SCHEMA)
        for field in ("mouth", "viseme", "visemes", "audio", "audio_path"):
            with self.subTest(field=field):
                self.assertNotIn(field, names)

    def test_18_schema_contains_no_character_or_scene_timestamps(self):
        names = _schema_property_names(ACTION_SCHEMA)
        for field in ("character_id", "scene_id", "start_ms", "end_ms", "timestamp_ms"):
            with self.subTest(field=field):
                self.assertNotIn(field, names)

    def test_19_action_and_pose_identifier_patterns_match(self):
        self.assertEqual(
            ACTION_SCHEMA["$defs"]["identifier"]["pattern"],
            POSE_SCHEMA["$defs"]["identifier"]["pattern"],
        )

    def test_20_fixture_pose_rig_profile_matches_action_rig_profile(self):
        pose = {
            "version": "1.0",
            "id": "point_right",
            "rig_profile": "fox_cartoon",
            "state": {"parts": {"arm_right": {"rotation_deg": -42}}},
        }
        action = _valid_action(rig_profile="fox_cartoon")
        POSE_VALIDATOR.validate(pose)
        VALIDATOR.validate(action)
        self.assertEqual(pose["rig_profile"], action["rig_profile"])


if __name__ == "__main__":
    unittest.main()
