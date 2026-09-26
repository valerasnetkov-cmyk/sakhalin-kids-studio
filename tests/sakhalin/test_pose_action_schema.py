"""Tests for Sakhalin Kids Pose/Action contracts (SKIDS-005)."""

import json
import pathlib
import unittest

from jsonschema import Draft202012Validator, ValidationError

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
POSE_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "sakhalin" / "pose.schema.json"
ACTION_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "sakhalin" / "action.schema.json"
RIG_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "sakhalin" / "rig_profile.schema.json"
CHAR_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "sakhalin" / "character_spec.schema.json"

POSE_SCHEMA = json.loads(POSE_SCHEMA_PATH.read_text(encoding="utf-8"))
ACTION_SCHEMA = json.loads(ACTION_SCHEMA_PATH.read_text(encoding="utf-8"))
RIG_SCHEMA = json.loads(RIG_SCHEMA_PATH.read_text(encoding="utf-8"))
CHAR_SCHEMA = json.loads(CHAR_SCHEMA_PATH.read_text(encoding="utf-8"))

_pose_validator = Draft202012Validator(POSE_SCHEMA)
_action_validator = Draft202012Validator(ACTION_SCHEMA)


def _pose(**overrides) -> dict:
    data = {
        "version": "1.0",
        "id": "point_right",
        "duration_hint_ms": 650,
        "parts": {
            "arm_right": {"rotation": -42},
            "head": {"rotation": 6},
        },
        "gaze": {"direction": "right"},
    }
    data.update(overrides)
    return data


def _action(**overrides) -> dict:
    data = {
        "version": "1.0",
        "id": "point",
        "phases": [
            {"name": "anticipation", "duration_ms": 180, "pose": "idle"},
            {"name": "move", "duration_ms": 320, "pose": "point_right"},
            {"name": "hold", "duration_ms": 500, "pose": "point_right"},
            {"name": "settle", "duration_ms": 260, "pose": "idle"},
        ],
    }
    data.update(overrides)
    return data


class TestSchemas(unittest.TestCase):
    def test_pose_schema_is_valid(self):
        Draft202012Validator.check_schema(POSE_SCHEMA)

    def test_action_schema_is_valid(self):
        Draft202012Validator.check_schema(ACTION_SCHEMA)

    def test_identifier_patterns_match_existing_contracts(self):
        expected = CHAR_SCHEMA["$defs"]["identifier"]["pattern"]
        self.assertEqual(POSE_SCHEMA["$defs"]["identifier"]["pattern"], expected)
        self.assertEqual(ACTION_SCHEMA["$defs"]["identifier"]["pattern"], expected)
        self.assertEqual(RIG_SCHEMA["$defs"]["identifier"]["pattern"], expected)


class TestPoseContract(unittest.TestCase):
    def test_valid_pose(self):
        _pose_validator.validate(_pose())

    def test_version_is_required_and_locked(self):
        bad = _pose()
        del bad["version"]
        with self.assertRaises(ValidationError):
            _pose_validator.validate(bad)
        with self.assertRaises(ValidationError):
            _pose_validator.validate(_pose(version="2.0"))

    def test_pose_requires_at_least_one_part(self):
        with self.assertRaises(ValidationError):
            _pose_validator.validate(_pose(parts={}))

    def test_unknown_root_property_rejected(self):
        with self.assertRaises(ValidationError):
            _pose_validator.validate(_pose(renderer="remotion"))

    def test_arbitrary_code_or_asset_path_not_allowed(self):
        bad = _pose()
        bad["parts"]["head"]["script"] = "doSomething()"
        with self.assertRaises(ValidationError):
            _pose_validator.validate(bad)
        bad = _pose()
        bad["parts"]["head"]["asset_path"] = "/tmp/head.svg"
        with self.assertRaises(ValidationError):
            _pose_validator.validate(bad)

    def test_rotation_is_bounded(self):
        for value in (-181, 181):
            with self.subTest(value=value):
                bad = _pose()
                bad["parts"]["head"]["rotation"] = value
                with self.assertRaises(ValidationError):
                    _pose_validator.validate(bad)

    def test_scale_must_be_positive(self):
        bad = _pose()
        bad["parts"]["head"] = {"scale": 0}
        with self.assertRaises(ValidationError):
            _pose_validator.validate(bad)

    def test_opacity_is_normalized(self):
        for value in (-0.01, 1.01):
            with self.subTest(value=value):
                bad = _pose()
                bad["parts"]["head"] = {"opacity": value}
                with self.assertRaises(ValidationError):
                    _pose_validator.validate(bad)

    def test_gaze_direction_is_closed_enum(self):
        with self.assertRaises(ValidationError):
            _pose_validator.validate(_pose(gaze={"direction": "leva"}))

    def test_duration_hint_is_optional(self):
        data = _pose()
        del data["duration_hint_ms"]
        _pose_validator.validate(data)


class TestActionContract(unittest.TestCase):
    def test_valid_action(self):
        _action_validator.validate(_action())

    def test_action_requires_phase(self):
        with self.assertRaises(ValidationError):
            _action_validator.validate(_action(phases=[]))

    def test_phase_duration_must_be_positive(self):
        bad = _action()
        bad["phases"][0]["duration_ms"] = 0
        with self.assertRaises(ValidationError):
            _action_validator.validate(bad)

    def test_phase_requires_pose_reference(self):
        bad = _action()
        del bad["phases"][0]["pose"]
        with self.assertRaises(ValidationError):
            _action_validator.validate(bad)

    def test_unknown_phase_property_rejected(self):
        bad = _action()
        bad["phases"][0]["easing_js"] = "() => 1"
        with self.assertRaises(ValidationError):
            _action_validator.validate(bad)

    def test_action_does_not_embed_renderer_or_character(self):
        for key in ("renderer", "character_id", "asset_path"):
            with self.subTest(key=key):
                with self.assertRaises(ValidationError):
                    _action_validator.validate(_action(**{key: "x"}))

    def test_action_phase_count_is_bounded(self):
        phases = [
            {"name": f"phase_{i}", "duration_ms": 10, "pose": "idle"}
            for i in range(33)
        ]
        with self.assertRaises(ValidationError):
            _action_validator.validate(_action(phases=phases))

    def test_identifiers_are_lowercase_stable_ids(self):
        bad = _action(id="Point")
        with self.assertRaises(ValidationError):
            _action_validator.validate(bad)


if __name__ == "__main__":
    unittest.main()
