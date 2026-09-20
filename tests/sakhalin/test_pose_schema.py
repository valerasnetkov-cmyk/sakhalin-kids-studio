"""Tests for Sakhalin Kids Pose schema (SKIDS-005)."""

import json
import pathlib
import unittest

from jsonschema import Draft202012Validator, ValidationError

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
POSE_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "sakhalin" / "pose.schema.json"
CHAR_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "sakhalin" / "character_spec.schema.json"
RIG_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "sakhalin" / "rig_profile.schema.json"

POSE_SCHEMA = json.loads(POSE_SCHEMA_PATH.read_text(encoding="utf-8"))
CHAR_SCHEMA = json.loads(CHAR_SCHEMA_PATH.read_text(encoding="utf-8"))
RIG_SCHEMA = json.loads(RIG_SCHEMA_PATH.read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(POSE_SCHEMA)


def _valid_pose(**overrides) -> dict:
    pose = {
        "version": "1.0",
        "id": "idle",
        "rig_profile": "fox_cartoon",
        "state": {
            "parts": {
                "head": {"rotation_deg": 0},
            }
        },
    }
    pose.update(overrides)
    return pose


class TestPoseSchema(unittest.TestCase):
    def test_01_schema_self_validation(self):
        Draft202012Validator.check_schema(POSE_SCHEMA)

    def test_02_valid_fox_idle_like_pose(self):
        VALIDATOR.validate(_valid_pose())

    def test_03_valid_fox_point_right_pose(self):
        pose = _valid_pose(
            id="point_right",
            state={
                "parts": {
                    "arm_right": {"rotation_deg": -42},
                    "head": {"rotation_deg": 6},
                },
                "expression": "curious",
                "gaze": {"direction": "right"},
            },
        )
        VALIDATOR.validate(pose)

    def test_04_valid_sea_lion_think_like_pose(self):
        pose = _valid_pose(
            id="think",
            rig_profile="sea_lion_cartoon",
            state={
                "parts": {
                    "flipper_right": {"variant": "raised_soft"},
                    "head": {"rotation_deg": -5},
                },
                "expression": "thinking",
                "gaze": {"direction": "up"},
            },
        )
        VALIDATOR.validate(pose)

    def test_05_missing_required_root_field_fails(self):
        for field in ("version", "id", "rig_profile", "state"):
            with self.subTest(field=field):
                pose = _valid_pose()
                del pose[field]
                with self.assertRaises(ValidationError):
                    VALIDATOR.validate(pose)

    def test_06_invalid_pose_id_fails(self):
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(_valid_pose(id="Point Right"))

    def test_07_invalid_rig_profile_id_fails(self):
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(_valid_pose(rig_profile="Fox.Cartoon"))

    def test_08_unknown_root_field_fails(self):
        pose = _valid_pose(debug=True)
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(pose)

    def test_09_empty_state_fails(self):
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(_valid_pose(state={}))

    def test_10_unknown_state_field_fails(self):
        pose = _valid_pose(state={"speed": 1.0})
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(pose)

    def test_11_invalid_part_identifier_fails(self):
        pose = _valid_pose(state={"parts": {"Arm Right": {"rotation_deg": 1}}})
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(pose)

    def test_12_empty_part_state_fails(self):
        pose = _valid_pose(state={"parts": {"head": {}}})
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(pose)

    def test_13_unknown_part_state_field_fails(self):
        forbidden = {
            "x": 1,
            "svg_path": "M0,0",
            "transform": "rotate(3)",
            "scale": 1.2,
            "opacity": 0.5,
            "layer": 2,
            "asset_path": "parts/head.svg",
        }
        for key, value in forbidden.items():
            with self.subTest(field=key):
                pose = _valid_pose(state={"parts": {"head": {key: value}}})
                with self.assertRaises(ValidationError):
                    VALIDATOR.validate(pose)

    def test_14_rotation_deg_must_be_numeric(self):
        pose = _valid_pose(state={"parts": {"head": {"rotation_deg": "six"}}})
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(pose)

    def test_15_variant_must_be_identifier(self):
        pose = _valid_pose(state={"parts": {"eye_left": {"variant": "Closed Soft"}}})
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(pose)

    def test_16_mouth_part_state_rejected(self):
        pose = _valid_pose(state={"parts": {"mouth": {"variant": "rest"}}})
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(pose)

    def test_17_expression_identifier_validation(self):
        valid = _valid_pose(state={"expression": "raised_soft"})
        VALIDATOR.validate(valid)
        invalid = _valid_pose(state={"expression": "Raised Soft"})
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(invalid)

    def test_18_valid_gaze_directions_pass(self):
        for direction in ("left", "center", "right", "up", "down"):
            with self.subTest(direction=direction):
                pose = _valid_pose(state={"gaze": {"direction": direction}})
                VALIDATOR.validate(pose)

    def test_19_unknown_gaze_direction_fails(self):
        pose = _valid_pose(state={"gaze": {"direction": "upper_right"}})
        with self.assertRaises(ValidationError):
            VALIDATOR.validate(pose)

    def test_20_identifier_pattern_matches_character_and_rig_profile(self):
        pose_pattern = POSE_SCHEMA["$defs"]["identifier"]["pattern"]
        char_pattern = CHAR_SCHEMA["$defs"]["identifier"]["pattern"]
        rig_pattern = RIG_SCHEMA["$defs"]["identifier"]["pattern"]
        self.assertEqual(pose_pattern, char_pattern)
        self.assertEqual(pose_pattern, rig_pattern)


if __name__ == "__main__":
    unittest.main()
