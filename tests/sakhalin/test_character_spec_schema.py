"""Tests for Sakhalin Kids CharacterSpec schema (SKIDS-002)."""

import json
import pathlib
import unittest

from jsonschema import Draft202012Validator, ValidationError

SCHEMA_PATH = pathlib.Path(__file__).resolve().parents[2] / "schemas" / "sakhalin" / "character_spec.schema.json"
ALLOWED_CAST_PATH = pathlib.Path(__file__).resolve().parents[2] / "config" / "sakhalin" / "allowed_cast.json"

with open(SCHEMA_PATH, "r", encoding="utf-8") as _f:
    SCHEMA = json.load(_f)

with open(ALLOWED_CAST_PATH, "r", encoding="utf-8") as _f:
    ALLOWED_CAST = json.load(_f)

_validator = Draft202012Validator(SCHEMA)


def _valid_spec(**overrides):
    """Return a minimal valid CharacterSpec, optionally overridden."""
    spec = {
        "version": "1.0",
        "id": "makar",
        "display_name": "Makar",
        "species": "fox",
        "rig_profile": "fox_cartoon",
        "role": "lead_researcher",
        "story": {
            "primary_question": "Why is the sea salty?",
            "catchphrase": "Let's find out!",
        },
        "visual": {
            "palette_locked": True,
            "proportions_locked": True,
            "wardrobe_locked": True,
            "base_regeneration_allowed": False,
        },
        "required_views": ["front", "three_quarter"],
        "required_expressions": ["neutral", "curious"],
        "required_actions": ["idle", "blink"],
        "props": {
            "required": ["magnifying_glass"],
            "optional": ["backpack"],
        },
        "voice": {
            "profile": "makar_voice",
        },
        "continuity": {
            "identity_locked": True,
            "redesign_requires_approval": True,
        },
    }
    spec.update(overrides)
    return spec


class TestSchemaSelfValidation(unittest.TestCase):
    """Check that the schema itself is valid Draft 2020-12."""

    def test_schema_is_valid_draft202012(self):
        Draft202012Validator.check_schema(SCHEMA)

    def test_schema_uses_draft202012(self):
        self.assertEqual(SCHEMA.get("$schema"), "https://json-schema.org/draft/2020-12/schema")

    def test_schema_has_id(self):
        self.assertIn("$id", SCHEMA)


class TestValidSpec(unittest.TestCase):
    """Valid spec passes validation."""

    def test_valid_spec_passes(self):
        _validator.validate(_valid_spec())

    def test_valid_spec_without_optional_props(self):
        spec = _valid_spec()
        del spec["props"]["optional"]
        _validator.validate(spec)

    def test_valid_spec_empty_required_props(self):
        spec = _valid_spec(props={"required": []})
        _validator.validate(spec)


class TestRequiredFields(unittest.TestCase):
    """Missing required fields must fail."""

    TOP_LEVEL_KEYS = [
        "version", "id", "display_name", "species", "rig_profile", "role",
        "story", "visual", "required_views", "required_expressions",
        "required_actions", "props", "voice", "continuity",
    ]

    def test_missing_required_top_level_field(self):
        for key in self.TOP_LEVEL_KEYS:
            with self.subTest(field=key):
                spec = _valid_spec()
                del spec[key]
                with self.assertRaises(ValidationError):
                    _validator.validate(spec)

    def test_missing_required_nested_story_field(self):
        for key in ("primary_question", "catchphrase"):
            with self.subTest(field=key):
                spec = _valid_spec()
                del spec["story"][key]
                with self.assertRaises(ValidationError):
                    _validator.validate(spec)

    def test_missing_required_nested_visual_field(self):
        for key in ("palette_locked", "proportions_locked", "wardrobe_locked", "base_regeneration_allowed"):
            with self.subTest(field=key):
                spec = _valid_spec()
                del spec["visual"][key]
                with self.assertRaises(ValidationError):
                    _validator.validate(spec)

    def test_missing_required_nested_continuity_field(self):
        for key in ("identity_locked", "redesign_requires_approval"):
            with self.subTest(field=key):
                spec = _valid_spec()
                del spec["continuity"][key]
                with self.assertRaises(ValidationError):
                    _validator.validate(spec)

    def test_missing_required_voice_profile(self):
        spec = _valid_spec()
        del spec["voice"]["profile"]
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_missing_props_required(self):
        spec = _valid_spec()
        del spec["props"]["required"]
        with self.assertRaises(ValidationError):
            _validator.validate(spec)


class TestIdentifierPattern(unittest.TestCase):
    """Invalid identifiers must fail."""

    def test_invalid_id_values(self):
        bad_ids = ["Makar", "123abc", "a b", "", "MAKAR", "a.b", "a_b_c!"]
        for bad_id in bad_ids:
            with self.subTest(id=bad_id):
                spec = _valid_spec(id=bad_id)
                with self.assertRaises(ValidationError):
                    _validator.validate(spec)

    def test_valid_id_values(self):
        good_ids = ["makar", "leva", "a", "a1", "my_char", "char-2"]
        for good_id in good_ids:
            with self.subTest(id=good_id):
                spec = _valid_spec(id=good_id)
                _validator.validate(spec)

    def test_invalid_rig_profile(self):
        spec = _valid_spec(rig_profile="FOX_CARTOON")
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_invalid_voice_profile(self):
        spec = _valid_spec()
        spec["voice"]["profile"] = "Makar Voice"
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_invalid_view_identifier(self):
        spec = _valid_spec(required_views=["Front View"])
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_invalid_expression_identifier(self):
        spec = _valid_spec(required_expressions=["Neutral!"])
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_invalid_action_identifier(self):
        spec = _valid_spec(required_actions=["idle "])
        with self.assertRaises(ValidationError):
            _validator.validate(spec)


class TestAdditionalProperties(unittest.TestCase):
    """Unknown fields must be rejected."""

    def test_unknown_root_field(self):
        spec = _valid_spec(unknown_field = "nope")
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_unknown_nested_visual_field(self):
        spec = _valid_spec()
        spec["visual"]["unknown"] = True
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_unknown_nested_story_field(self):
        spec = _valid_spec()
        spec["story"]["extra"] = "nope"
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_unknown_nested_continuity_field(self):
        spec = _valid_spec()
        spec["continuity"]["extra"] = False
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_unknown_nested_voice_field(self):
        spec = _valid_spec()
        spec["voice"]["extra"] = "x"
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_unknown_nested_props_field(self):
        spec = _valid_spec()
        spec["props"]["extra"] = []
        with self.assertRaises(ValidationError):
            _validator.validate(spec)


class TestVisualLockBooleans(unittest.TestCase):
    """Visual lock fields must be boolean."""

    def test_visual_lock_rejects_non_boolean(self):
        for val in ["true", 1, 0, "yes", None]:
            for field in ("palette_locked", "proportions_locked", "wardrobe_locked", "base_regeneration_allowed"):
                with self.subTest(field=field, value=val):
                    spec = _valid_spec()
                    spec["visual"][field] = val
                    with self.assertRaises(ValidationError):
                        _validator.validate(spec)


class TestArrayTypes(unittest.TestCase):
    """Array fields must contain strings and have correct shape."""

    def test_required_views_rejects_non_strings(self):
        spec = _valid_spec(required_views=[123])
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_required_expressions_rejects_non_strings(self):
        spec = _valid_spec(required_expressions=[True])
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_required_actions_rejects_non_strings(self):
        spec = _valid_spec(required_actions=[None])
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_required_views_empty_rejected(self):
        spec = _valid_spec(required_views=[])
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_required_expressions_empty_rejected(self):
        spec = _valid_spec(required_expressions=[])
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_required_actions_empty_rejected(self):
        spec = _valid_spec(required_actions=[])
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_props_required_allows_empty(self):
        spec = _valid_spec(props={"required": []})
        _validator.validate(spec)


class TestUniqueItems(unittest.TestCase):
    """Duplicate items in arrays must fail."""

    def test_duplicate_required_views(self):
        spec = _valid_spec(required_views=["front", "front"])
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_duplicate_required_expressions(self):
        spec = _valid_spec(required_expressions=["neutral", "neutral"])
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_duplicate_required_actions(self):
        spec = _valid_spec(required_actions=["idle", "idle"])
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_duplicate_props_required(self):
        spec = _valid_spec(props={"required": ["hat", "hat"]})
        with self.assertRaises(ValidationError):
            _validator.validate(spec)

    def test_duplicate_props_optional(self):
        spec = _valid_spec(props={"required": [], "optional": ["scarf", "scarf"]})
        with self.assertRaises(ValidationError):
            _validator.validate(spec)


class TestVersion(unittest.TestCase):
    """Version must be exactly '1.0'."""

    def test_version_10_passes(self):
        _validator.validate(_valid_spec())

    def test_unsupported_version_fails(self):
        for v in ["2.0", "0.9", "1.1", "latest"]:
            with self.subTest(version=v):
                spec = _valid_spec(version=v)
                with self.assertRaises(ValidationError):
                    _validator.validate(spec)


class TestNonCoreIdPassesSchema(unittest.TestCase):
    """Schema-valid non-core ID passes at schema level."""

    def test_non_core_id_boris_passes(self):
        spec = _valid_spec(id="boris")
        _validator.validate(spec)

    def test_non_core_id_zhmyh_passes(self):
        spec = _valid_spec(id="zhmyh")
        _validator.validate(spec)


class TestAllowedCastUnchanged(unittest.TestCase):
    """allowed_cast.json must remain exactly 5 core IDs."""

    def test_allowed_cast_has_exactly_five(self):
        self.assertEqual(len(ALLOWED_CAST["core_cast"]), 5)

    def test_allowed_cast_core_ids(self):
        expected = {"makar", "leva", "tikhon", "anna", "antoshka"}
        self.assertEqual(set(ALLOWED_CAST["core_cast"]), expected)


if __name__ == "__main__":
    unittest.main()
