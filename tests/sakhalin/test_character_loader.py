"""Tests for Sakhalin Kids CharacterLoader domain service (SKIDS-003)."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from tools.character.sakhalin.character_loader import (
    CharacterLoader,
    CharacterLoadError,
    CharacterManifestError,
    CharacterNotAllowedError,
    CharacterNotFoundError,
    CharacterValidationError,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "sakhalin" / "character_spec.schema.json"
ALLOWED_CAST_PATH = PROJECT_ROOT / "config" / "sakhalin" / "allowed_cast.json"


def _valid_manifest(**overrides) -> dict:
    spec = {
        "version": "1.0",
        "id": "makar",
        "display_name": "Makar",
        "species": "fox",
        "rig_profile": "fox_cartoon",
        "role": "lead_researcher",
        "story": {
            "primary_question": "Why?",
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
        "props": {"required": ["magnifying_glass"]},
        "voice": {"profile": "makar_voice"},
        "continuity": {
            "identity_locked": True,
            "redesign_requires_approval": True,
        },
    }
    spec.update(overrides)
    return spec


def _make_cast(data: dict) -> str:
    return json.dumps(data)


_VALID_CAST = _make_cast({
    "version": "1.0",
    "core_cast": ["makar", "leva", "tikhon", "anna", "antoshka"],
    "policy": {"core_cast_closed": True, "guest_characters_allowed": True,
               "guest_persistence": "episode_only",
               "new_core_character_requires": "explicit decision"},
})


class _LoaderTestBase(unittest.TestCase):
    """Base class providing temp directory setup for loader tests."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._root = Path(self._tmp.name)
        self._lib = self._root / "library" / "characters"
        self._lib.mkdir(parents=True)
        self._cast_path = self._root / "allowed_cast.json"
        self._cast_path.write_text(_VALID_CAST, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def _loader(self, cast_content: str | None = None) -> CharacterLoader:
        if cast_content is not None:
            self._cast_path.write_text(cast_content, encoding="utf-8")
        return CharacterLoader(
            library_root=self._lib,
            schema_path=SCHEMA_PATH,
            allowed_cast_path=self._cast_path,
        )

    def _write_manifest(self, character_id: str, content: str) -> Path:
        d = self._lib / character_id
        d.mkdir(parents=True, exist_ok=True)
        p = d / "character.yaml"
        p.write_text(content, encoding="utf-8")
        return p


class TestValidLoading(_LoaderTestBase):
    """Valid core character loads successfully."""

    def test_valid_core_character_loads(self):
        self._write_manifest("makar", json.dumps(_valid_manifest()))
        loader = self._loader()
        result = loader.load_core("makar")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], "makar")

    def test_returned_dict_passes_character_spec_schema(self):
        self._write_manifest("makar", json.dumps(_valid_manifest()))
        from jsonschema import Draft202012Validator
        loader = self._loader()
        result = loader.load_core("makar")
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(result)

    def test_valid_core_characters_all_five(self):
        for cid in ["makar", "leva", "tikhon", "anna", "antoshka"]:
            with self.subTest(character=cid):
                self._write_manifest(cid, json.dumps(_valid_manifest(id=cid)))
                loader = self._loader()
                result = loader.load_core(cid)
                self.assertEqual(result["id"], cid)


class TestCoreAdmission(_LoaderTestBase):
    """Non-core IDs rejected by core-cast policy."""

    def test_non_core_valid_id_rejected(self):
        self._write_manifest("boris", json.dumps(_valid_manifest(id="boris")))
        loader = self._loader()
        with self.assertRaises(CharacterNotAllowedError):
            loader.load_core("boris")

    def test_traversal_id_rejected_before_filesystem(self):
        loader = self._loader()
        with self.assertRaises(CharacterNotAllowedError):
            loader.load_core("makar/../../x")

    def test_non_core_guest_cannot_enter_persistent_library(self):
        loader = self._loader()
        with self.assertRaises(CharacterNotAllowedError):
            loader.load_core("guest_char")


class TestFilesystemSecurity(_LoaderTestBase):
    """Filesystem containment checks."""

    def test_missing_manifest(self):
        loader = self._loader()
        with self.assertRaises(CharacterNotFoundError):
            loader.load_core("makar")

    def test_symlink_manifest_escape(self):
        if not hasattr(os, "symlink"):
            self.skipTest("os.symlink not available")
        target = self._root / "outside" / "escaped.yaml"
        target.parent.mkdir()
        target.write_text("not yaml", encoding="utf-8")
        d = self._lib / "makar"
        d.mkdir()
        try:
            os.symlink(str(target), str(d / "character.yaml"))
        except OSError:
            self.skipTest("symlink requires elevated privileges on this platform")
        loader = self._loader()
        with self.assertRaises(CharacterNotAllowedError):
            loader.load_core("makar")

    def test_symlink_directory_escape(self):
        if not hasattr(os, "symlink"):
            self.skipTest("os.symlink not available")
        target = self._root / "outside_lib"
        target.mkdir()
        d = self._lib / "leva"
        try:
            os.symlink(str(target), str(d))
        except OSError:
            self.skipTest("symlink requires elevated privileges on this platform")
        loader = self._loader()
        with self.assertRaises(CharacterNotAllowedError):
            loader.load_core("leva")


class TestYAMLParsing(_LoaderTestBase):
    """YAML parsing safety checks."""

    def test_malformed_yaml(self):
        self._write_manifest("makar", "{{invalid yaml}}")
        loader = self._loader()
        with self.assertRaises(CharacterManifestError):
            loader.load_core("makar")

    def test_yaml_list_root(self):
        self._write_manifest("makar", "- item1\n- item2\n")
        loader = self._loader()
        with self.assertRaises(CharacterManifestError):
            loader.load_core("makar")

    def test_yaml_scalar_root(self):
        self._write_manifest("makar", "just a string\n")
        loader = self._loader()
        with self.assertRaises(CharacterManifestError):
            loader.load_core("makar")

    def test_python_object_yaml_tag(self):
        content = "!!python/object/apply:os.path.join ['a', 'b']\n"
        self._write_manifest("makar", content)
        loader = self._loader()
        with self.assertRaises(CharacterManifestError):
            loader.load_core("makar")


class TestSchemaValidation(_LoaderTestBase):
    """Schema and identity validation."""

    def test_schema_invalid_manifest(self):
        bad = _valid_manifest()
        del bad["visual"]
        self._write_manifest("makar", json.dumps(bad))
        loader = self._loader()
        with self.assertRaises(CharacterValidationError):
            loader.load_core("makar")

    def test_manifest_id_mismatch(self):
        self._write_manifest("makar", json.dumps(_valid_manifest(id="leva")))
        loader = self._loader()
        with self.assertRaises(CharacterValidationError):
            loader.load_core("makar")


class TestOversizedManifest(_LoaderTestBase):
    """Size limit enforcement."""

    def test_oversized_manifest(self):
        big = "x" * (128 * 1024 + 1)
        self._write_manifest("makar", big)
        loader = self._loader()
        with self.assertRaises(CharacterManifestError):
            loader.load_core("makar")


class TestEncoding(_LoaderTestBase):
    """Encoding checks."""

    def test_invalid_utf8(self):
        d = self._lib / "makar"
        d.mkdir()
        p = d / "character.yaml"
        p.write_bytes(b"\x80\x81\x82")
        loader = self._loader()
        with self.assertRaises(CharacterManifestError):
            loader.load_core("makar")


class TestHardening(_LoaderTestBase):
    """Regression tests for SKIDS-003 hardening pass."""

    def test_identifier_pattern_from_schema(self):
        loader = self._loader()
        import re
        self.assertIsInstance(loader._identifier_re, re.Pattern)
        self.assertEqual(loader._identifier_re.pattern, "^[a-z][a-z0-9_-]*$")

    def test_malformed_schema_identifier_fails_construction(self):
        import json as _json
        bad_schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        del bad_schema["$defs"]["identifier"]["pattern"]
        tmp = self._root / "bad_schema.json"
        tmp.write_text(_json.dumps(bad_schema), encoding="utf-8")
        with self.assertRaises(CharacterLoadError):
            CharacterLoader(
                library_root=self._lib,
                schema_path=tmp,
                allowed_cast_path=self._cast_path,
            )

    def test_missing_schema_defs_fails_construction(self):
        import json as _json
        bad_schema = {"type": "object"}
        tmp = self._root / "bad_schema.json"
        tmp.write_text(_json.dumps(bad_schema), encoding="utf-8")
        with self.assertRaises(CharacterLoadError):
            CharacterLoader(
                library_root=self._lib,
                schema_path=tmp,
                allowed_cast_path=self._cast_path,
            )

    def test_schema_validation_error_does_not_echo_manifest_value(self):
        bad = _valid_manifest()
        bad["visual"]["palette_locked"] = "not_a_boolean"
        self._write_manifest("makar", json.dumps(bad))
        loader = self._loader()
        with self.assertRaises(CharacterValidationError) as ctx:
            loader.load_core("makar")
        msg = str(ctx.exception)
        self.assertNotIn("not_a_boolean", msg)
        self.assertIn("palette_locked", msg)

    def test_resolved_path_is_same_for_reading(self):
        self._write_manifest("makar", json.dumps(_valid_manifest()))
        loader = self._loader()
        path = loader._resolve_contained_manifest_path("makar")
        self.assertTrue(path.is_file())

    def test_containment_outside_library_root(self):
        from tools.character.sakhalin.character_loader import CharacterLoader as CL
        outside = self._root / "outside_chars"
        outside.mkdir()
        loader = CL(
            library_root=outside,
            schema_path=SCHEMA_PATH,
            allowed_cast_path=self._cast_path,
        )
        with self.assertRaises(CharacterNotAllowedError):
            loader._resolve_contained_manifest_path("../sneaky")


class TestPolicyValidation(_LoaderTestBase):
    """allowed_cast.json structural validation."""

    def test_malformed_json(self):
        with self.assertRaises(CharacterLoadError):
            self._loader("{not json")

    def test_root_wrong_type(self):
        with self.assertRaises(CharacterLoadError):
            self._loader(_make_cast(["makar"]))

    def test_core_cast_wrong_type(self):
        with self.assertRaises(CharacterLoadError):
            self._loader(_make_cast({
                "version": "1.0", "core_cast": "makar",
                "policy": {"core_cast_closed": True},
            }))

    def test_duplicate_core_ids(self):
        with self.assertRaises(CharacterLoadError):
            self._loader(_make_cast({
                "version": "1.0",
                "core_cast": ["makar", "makar", "leva", "tikhon", "anna", "antoshka"],
                "policy": {"core_cast_closed": True},
            }))

    def test_invalid_identifier_in_core_cast(self):
        with self.assertRaises(CharacterLoadError):
            self._loader(_make_cast({
                "version": "1.0",
                "core_cast": ["makar", "../leva", "tikhon", "anna", "antoshka"],
                "policy": {"core_cast_closed": True},
            }))

    def test_missing_policy_object(self):
        with self.assertRaises(CharacterLoadError):
            self._loader(_make_cast({
                "version": "1.0",
                "core_cast": ["makar", "leva", "tikhon", "anna", "antoshka"],
            }))

    def test_policy_core_cast_closed_false(self):
        with self.assertRaises(CharacterLoadError):
            self._loader(_make_cast({
                "version": "1.0",
                "core_cast": ["makar", "leva", "tikhon", "anna", "antoshka"],
                "policy": {"core_cast_closed": False},
            }))

    def test_wrong_version(self):
        with self.assertRaises(CharacterLoadError):
            self._loader(_make_cast({
                "version": "2.0",
                "core_cast": ["makar", "leva", "tikhon", "anna", "antoshka"],
                "policy": {"core_cast_closed": True},
            }))

    def test_empty_core_cast(self):
        with self.assertRaises(CharacterLoadError):
            self._loader(_make_cast({
                "version": "1.0", "core_cast": [],
                "policy": {"core_cast_closed": True},
            }))


if __name__ == "__main__":
    unittest.main()
