"""Sakhalin Kids — CharacterLoader domain service (SKIDS-003).

Safe loader for persistent core character manifests.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict

import yaml
from jsonschema import Draft202012Validator

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class CharacterLoadError(Exception):
    """Base error for character loading failures."""


class CharacterNotAllowedError(CharacterLoadError):
    """Requested character ID is not in the core cast policy."""


class CharacterNotFoundError(CharacterLoadError):
    """Character directory or manifest does not exist."""


class CharacterManifestError(CharacterLoadError):
    """Manifest is malformed, oversized, or unreadable."""


class CharacterValidationError(CharacterLoadError):
    """Manifest does not conform to CharacterSpec schema or identity check."""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MANIFEST_NAME = "character.yaml"
_MAX_MANIFEST_BYTES = 128 * 1024  # 128 KiB
_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")

# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


class CharacterLoader:
    """Domain service that loads and validates core character manifests.

    This is NOT an OpenMontage tool adapter.  It is a standalone domain
    service with no upstream coupling.
    """

    def __init__(
        self,
        library_root: Path,
        schema_path: Path,
        allowed_cast_path: Path,
    ) -> None:
        self._library_root = library_root.resolve()
        self._schema_path = schema_path.resolve()
        self._allowed_cast_path = allowed_cast_path.resolve()

        self._schema = self._load_schema()
        self._identifier_re = _IDENTIFIER_PATTERN
        self._core_ids = self._load_and_validate_policy()

    # -- public API --------------------------------------------------------

    @classmethod
    def from_project_root(cls, project_root: Path) -> "CharacterLoader":
        """Convenience constructor from project root directory."""
        return cls(
            library_root=project_root / "library" / "characters",
            schema_path=project_root / "schemas" / "sakhalin" / "character_spec.schema.json",
            allowed_cast_path=project_root / "config" / "sakhalin" / "allowed_cast.json",
        )

    def load_core(self, character_id: str) -> Dict[str, Any]:
        """Load and validate a core character manifest.

        Returns a validated dict.  Raises on any policy, filesystem,
        parsing, or schema violation.
        """
        self._check_id_pattern(character_id)
        self._check_core_admission(character_id)
        self._check_filesystem_containment(character_id)

        manifest_path = self._resolve_manifest_path(character_id)
        self._check_manifest_exists(manifest_path, character_id)
        raw = self._read_manifest(manifest_path, character_id)
        manifest = self._parse_yaml(raw, character_id)
        self._validate_schema(manifest, character_id)
        self._validate_identity(manifest, character_id)

        return manifest

    # -- schema loading ----------------------------------------------------

    def _load_schema(self) -> Dict[str, Any]:
        try:
            raw = self._schema_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise CharacterLoadError(
                f"Cannot read schema: {self._schema_path}"
            ) from exc

        try:
            schema = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CharacterLoadError(
                f"Schema is not valid JSON: {self._schema_path}"
            ) from exc

        Draft202012Validator.check_schema(schema)
        return schema

    # -- policy loading ----------------------------------------------------

    def _load_and_validate_policy(self) -> frozenset[str]:
        try:
            raw = self._allowed_cast_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise CharacterLoadError(
                f"Cannot read allowed cast config: {self._allowed_cast_path}"
            ) from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CharacterLoadError(
                "allowed_cast.json is not valid JSON"
            ) from exc

        if not isinstance(data, dict):
            raise CharacterLoadError("allowed_cast.json root must be an object")

        if data.get("version") != "1.0":
            raise CharacterLoadError(
                f"allowed_cast.json version must be '1.0', got {data.get('version')!r}"
            )

        core_cast = data.get("core_cast")
        if not isinstance(core_cast, list) or len(core_cast) == 0:
            raise CharacterLoadError("core_cast must be a non-empty list")

        for item in core_cast:
            if not isinstance(item, str):
                raise CharacterLoadError(
                    f"core_cast entry must be string, got {type(item).__name__}"
                )
            if not self._identifier_re.match(item):
                raise CharacterLoadError(
                    f"core_cast contains invalid identifier: {item!r}"
                )

        if len(core_cast) != len(set(core_cast)):
            raise CharacterLoadError("core_cast contains duplicate IDs")

        policy = data.get("policy")
        if not isinstance(policy, dict):
            raise CharacterLoadError("policy must be an object")

        if policy.get("core_cast_closed") is not True:
            raise CharacterLoadError(
                "policy.core_cast_closed must be true for closed core cast"
            )

        return frozenset(core_cast)

    # -- identity checks ---------------------------------------------------

    def _check_id_pattern(self, character_id: str) -> None:
        if not isinstance(character_id, str) or not self._identifier_re.match(
            character_id
        ):
            raise CharacterNotAllowedError(
                f"Invalid character identifier: {character_id!r}"
            )

    def _check_core_admission(self, character_id: str) -> None:
        if character_id not in self._core_ids:
            raise CharacterNotAllowedError(
                f"Character {character_id!r} is not in the core cast"
            )

    # -- filesystem containment ---------------------------------------------

    def _check_filesystem_containment(self, character_id: str) -> None:
        resolved = (self._library_root / character_id / _MANIFEST_NAME).resolve()
        try:
            resolved.relative_to(self._library_root)
        except ValueError:
            raise CharacterNotAllowedError(
                f"Path traversal detected for character: {character_id!r}"
            )

    def _resolve_manifest_path(self, character_id: str) -> Path:
        return (self._library_root / character_id / _MANIFEST_NAME).resolve()

    # -- manifest reading --------------------------------------------------

    def _check_manifest_exists(self, path: Path, character_id: str) -> None:
        if not path.is_file():
            raise CharacterNotFoundError(
                f"Manifest not found for character: {character_id!r}"
            )

    def _read_manifest(self, path: Path, character_id: str) -> bytes:
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise CharacterManifestError(
                f"Cannot read manifest for {character_id!r}"
            ) from exc

        if len(raw) > _MAX_MANIFEST_BYTES:
            raise CharacterManifestError(
                f"Manifest for {character_id!r} exceeds {_MAX_MANIFEST_BYTES} bytes"
            )

        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CharacterManifestError(
                f"Manifest for {character_id!r} is not valid UTF-8"
            ) from exc

    # -- YAML parsing ------------------------------------------------------

    def _parse_yaml(self, raw: str, character_id: str) -> Dict[str, Any]:
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            raise CharacterManifestError(
                f"YAML parse error for {character_id!r}"
            ) from exc

        if not isinstance(data, dict):
            raise CharacterManifestError(
                f"Manifest root must be a mapping, got {type(data).__name__}"
            )

        return data

    # -- schema validation -------------------------------------------------

    def _validate_schema(self, manifest: Dict[str, Any], character_id: str) -> None:
        validator = Draft202012Validator(self._schema)
        errors = list(validator.iter_errors(manifest))
        if errors:
            messages = [f"  - {e.message}" for e in errors[:5]]
            raise CharacterValidationError(
                f"CharacterSpec validation failed for {character_id!r}:\n"
                + "\n".join(messages)
            )

    def _validate_identity(self, manifest: Dict[str, Any], character_id: str) -> None:
        manifest_id = manifest.get("id")
        if manifest_id != character_id:
            raise CharacterValidationError(
                f"Identity mismatch: requested {character_id!r}, "
                f"manifest contains {manifest_id!r}"
            )
