"""Tests for Sakhalin Kids RigProfile schema (SKIDS-004)."""

import json
import pathlib
import unittest

import yaml
from jsonschema import Draft202012Validator, ValidationError

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
RIG_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "sakhalin" / "rig_profile.schema.json"
CHAR_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "sakhalin" / "character_spec.schema.json"
FOX_PATH = PROJECT_ROOT / "library" / "rig_profiles" / "fox_cartoon.yaml"
SEA_LION_PATH = PROJECT_ROOT / "library" / "rig_profiles" / "sea_lion_cartoon.yaml"

with open(RIG_SCHEMA_PATH, "r", encoding="utf-8") as _f:
    RIG_SCHEMA = json.load(_f)

with open(FOX_PATH, "r", encoding="utf-8") as _f:
    FOX_PROFILE = yaml.safe_load(_f)

with open(SEA_LION_PATH, "r", encoding="utf-8") as _f:
    SEA_LION_PROFILE = yaml.safe_load(_f)

_validator = Draft202012Validator(RIG_SCHEMA)

ALL_CAPS = [
    "blink", "gaze", "mouth_visemes", "head_turn",
    "arm_gestures", "tail_motion", "flipper_gestures", "wing_gestures",
]


def _valid_profile(**overrides) -> dict:
    p = {
        "version": "1.0",
        "id": "fox_cartoon",
        "parts": {
            "required": ["body", "head", "mouth"],
        },
        "capabilities": {c: True for c in ALL_CAPS},
    }
    p.update(overrides)
    return p


class TestSchemaSelfValidation(unittest.TestCase):

    def test_schema_is_valid_draft202012(self):
        Draft202012Validator.check_schema(RIG_SCHEMA)

    def test_schema_uses_draft202012(self):
        self.assertEqual(RIG_SCHEMA.get("$schema"), "https://json-schema.org/draft/2020-12/schema")


class TestCanonicalProfiles(unittest.TestCase):

    def test_fox_cartoon_valid(self):
        _validator.validate(FOX_PROFILE)

    def test_sea_lion_cartoon_valid(self):
        _validator.validate(SEA_LION_PROFILE)

    def test_fox_id_matches_filename(self):
        self.assertEqual(FOX_PROFILE["id"], "fox_cartoon")

    def test_sea_lion_id_matches_filename(self):
        self.assertEqual(SEA_LION_PROFILE["id"], "sea_lion_cartoon")


class TestRequiredFields(unittest.TestCase):

    def test_missing_version(self):
        p = _valid_profile()
        del p["version"]
        with self.assertRaises(ValidationError):
            _validator.validate(p)

    def test_missing_id(self):
        p = _valid_profile()
        del p["id"]
        with self.assertRaises(ValidationError):
            _validator.validate(p)

    def test_missing_parts(self):
        p = _valid_profile()
        del p["parts"]
        with self.assertRaises(ValidationError):
            _validator.validate(p)

    def test_missing_capabilities(self):
        p = _valid_profile()
        del p["capabilities"]
        with self.assertRaises(ValidationError):
            _validator.validate(p)


class TestIdentifierPattern(unittest.TestCase):

    def test_invalid_id(self):
        for bad in ["Fox", "123abc", "a b", "", "A_B"]:
            with self.subTest(id=bad):
                p = _valid_profile(id=bad)
                with self.assertRaises(ValidationError):
                    _validator.validate(p)

    def test_valid_ids(self):
        for good in ["fox_cartoon", "sea-lion", "a1", "my_rig"]:
            with self.subTest(id=good):
                p = _valid_profile(id=good)
                _validator.validate(p)


class TestAdditionalProperties(unittest.TestCase):

    def test_unknown_root_field(self):
        p = _valid_profile(unknown=True)
        with self.assertRaises(ValidationError):
            _validator.validate(p)

    def test_unknown_parts_field(self):
        p = _valid_profile()
        p["parts"]["unknown"] = []
        with self.assertRaises(ValidationError):
            _validator.validate(p)

    def test_unknown_capability(self):
        p = _valid_profile()
        p["capabilities"]["laser_eyes"] = True
        with self.assertRaises(ValidationError):
            _validator.validate(p)


class TestPartsContract(unittest.TestCase):

    def test_required_parts_empty(self):
        p = _valid_profile(parts={"required": []})
        with self.assertRaises(ValidationError):
            _validator.validate(p)

    def test_duplicate_required_parts(self):
        p = _valid_profile(parts={"required": ["body", "body"]})
        with self.assertRaises(ValidationError):
            _validator.validate(p)

    def test_duplicate_optional_parts(self):
        p = _valid_profile(parts={"required": ["body"], "optional": ["hat", "hat"]})
        with self.assertRaises(ValidationError):
            _validator.validate(p)

    def test_invalid_part_identifier(self):
        p = _valid_profile(parts={"required": ["Body"]})
        with self.assertRaises(ValidationError):
            _validator.validate(p)

    def test_optional_parts_not_required(self):
        p = _valid_profile(parts={"required": ["body"]})
        _validator.validate(p)


class TestCapabilitiesContract(unittest.TestCase):

    def test_capability_must_be_boolean(self):
        for cap in ALL_CAPS:
            with self.subTest(cap=cap):
                p = _valid_profile()
                p["capabilities"][cap] = "yes"
                with self.assertRaises(ValidationError):
                    _validator.validate(p)

    def test_all_known_capabilities_required(self):
        p = _valid_profile()
        for cap in ALL_CAPS:
            with self.subTest(cap=cap):
                del p["capabilities"][cap]
                with self.assertRaises(ValidationError):
                    _validator.validate(p)
                p["capabilities"][cap] = True

    def test_missing_capability_fails(self):
        p = _valid_profile()
        del p["capabilities"]["blink"]
        with self.assertRaises(ValidationError):
            _validator.validate(p)


class TestVersion(unittest.TestCase):

    def test_version_10_passes(self):
        _validator.validate(_valid_profile())

    def test_wrong_version_fails(self):
        for v in ["2.0", "0.9", "latest"]:
            with self.subTest(version=v):
                p = _valid_profile(version=v)
                with self.assertRaises(ValidationError):
                    _validator.validate(p)


class TestSchemaBoundary(unittest.TestCase):

    def test_no_character_id_in_schema(self):
        self.assertNotIn("character_id", RIG_SCHEMA.get("properties", {}))

    def test_no_asset_path_in_parts_schema(self):
        parts_props = RIG_SCHEMA["$defs"]["parts"]["properties"]
        for key in ("asset_path", "joints", "pivots", "layers"):
            self.assertNotIn(key, parts_props)


class TestIdentifierPatternConsistency(unittest.TestCase):

    def test_rig_and_character_identifier_patterns_match(self):
        rig_pattern = RIG_SCHEMA["$defs"]["identifier"]["pattern"]
        char_pattern = json.loads(CHAR_SCHEMA_PATH.read_text(encoding="utf-8"))["$defs"]["identifier"]["pattern"]
        self.assertEqual(rig_pattern, char_pattern)


class TestCanonicalProfileIntegrity(unittest.TestCase):

    def test_fox_required_optional_disjoint(self):
        req = set(FOX_PROFILE["parts"]["required"])
        opt = set(FOX_PROFILE["parts"].get("optional", []))
        self.assertEqual(req & opt, set())

    def test_sea_lion_required_optional_disjoint(self):
        req = set(SEA_LION_PROFILE["parts"]["required"])
        opt = set(SEA_LION_PROFILE["parts"].get("optional", []))
        self.assertEqual(req & opt, set())

    def test_fox_capabilities_match_proof(self):
        caps = FOX_PROFILE["capabilities"]
        self.assertTrue(caps["blink"])
        self.assertTrue(caps["gaze"])
        self.assertTrue(caps["mouth_visemes"])
        self.assertTrue(caps["head_turn"])
        self.assertTrue(caps["arm_gestures"])
        self.assertTrue(caps["tail_motion"])
        self.assertFalse(caps["flipper_gestures"])
        self.assertFalse(caps["wing_gestures"])

    def test_sea_lion_capabilities_match_proof(self):
        caps = SEA_LION_PROFILE["capabilities"]
        self.assertTrue(caps["blink"])
        self.assertTrue(caps["gaze"])
        self.assertTrue(caps["mouth_visemes"])
        self.assertTrue(caps["head_turn"])
        self.assertFalse(caps["arm_gestures"])
        self.assertFalse(caps["tail_motion"])
        self.assertTrue(caps["flipper_gestures"])
        self.assertFalse(caps["wing_gestures"])

    def test_fox_tail_motion_implies_tail_part(self):
        self.assertIn("tail", FOX_PROFILE["parts"]["required"])

    def test_fox_arm_gestures_implies_arm_parts(self):
        req = set(FOX_PROFILE["parts"]["required"])
        self.assertIn("arm_left", req)
        self.assertIn("arm_right", req)

    def test_sea_lion_flipper_gestures_implies_flipper_parts(self):
        req = set(SEA_LION_PROFILE["parts"]["required"])
        self.assertIn("flipper_left", req)
        self.assertIn("flipper_right", req)


if __name__ == "__main__":
    unittest.main()
