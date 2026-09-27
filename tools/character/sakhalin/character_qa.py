"""Structural Character QA for Sakhalin Kids (SKIDS-010).

The service validates identity and reusable-asset invariants without performing
perceptual image analysis. Visual reference checks are supplied as explicit
evidence and are never silently assumed to pass.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence


class CharacterQAError(ValueError):
    """Raised when QA inputs or policy are malformed."""


class CharacterQA:
    """Data-driven structural reviewer for persistent characters."""

    def __init__(self, policy: Mapping[str, Any]) -> None:
        self._policy = _validate_policy(policy)

    @classmethod
    def from_project_root(cls, project_root: Path) -> "CharacterQA":
        path = project_root / "config" / "sakhalin" / "character_qa_policy.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CharacterQAError(f"cannot load Character QA policy: {path}") from exc
        return cls(data)

    def review(
        self,
        character_spec: Mapping[str, Any],
        rig_profile: Mapping[str, Any],
        evidence: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Return deterministic pass/fail report with findings."""

        _require_mapping(character_spec, "character_spec")
        _require_mapping(rig_profile, "rig_profile")
        _require_mapping(evidence, "evidence")

        character_id = _require_text(character_spec.get("id"), "character_spec.id")
        canon = self._policy["characters"].get(character_id)

        findings: list[dict[str, str]] = []
        checks: list[dict[str, str]] = []

        if canon is None:
            _block(findings, "unknown_character", "character ID is not in Team Canon")
            return _report(character_id, findings, checks)

        _check_equal(
            checks,
            findings,
            "species_matches_canon",
            character_spec.get("species"),
            canon["species"],
            "character species/type differs from Team Canon",
        )

        expected_rig = canon.get("rig_profile")
        if expected_rig is not None:
            _check_equal(
                checks,
                findings,
                "rig_matches_canon",
                character_spec.get("rig_profile"),
                expected_rig,
                "character rig profile differs from current proof canon",
            )

        _check_equal(
            checks,
            findings,
            "rig_matches_character_spec",
            rig_profile.get("id"),
            character_spec.get("rig_profile"),
            "loaded rig profile does not match CharacterSpec",
        )

        evidence_id = evidence.get("character_id")
        _check_equal(
            checks,
            findings,
            "evidence_identity",
            evidence_id,
            character_id,
            "QA evidence belongs to a different character",
        )

        self._check_visual_locks(character_spec, findings, checks)
        self._check_continuity_locks(character_spec, findings, checks)
        self._check_required_assets(character_spec, rig_profile, evidence, findings, checks)
        self._check_reference_evidence(evidence, findings, checks)

        return _report(character_id, findings, checks)

    def _check_visual_locks(
        self,
        spec: Mapping[str, Any],
        findings: list[dict[str, str]],
        checks: list[dict[str, str]],
    ) -> None:
        visual = spec.get("visual")
        if not isinstance(visual, Mapping):
            _block(findings, "visual_lock_missing", "CharacterSpec.visual is missing")
            return

        required_true = ("palette_locked", "proportions_locked", "wardrobe_locked")
        for field in required_true:
            if visual.get(field) is True:
                _pass(checks, field)
            else:
                _block(findings, field, f"{field} must be true")

        if visual.get("base_regeneration_allowed") is False:
            _pass(checks, "base_regeneration_locked")
        else:
            _block(
                findings,
                "base_regeneration_allowed",
                "base character regeneration must remain disabled",
            )

    def _check_continuity_locks(
        self,
        spec: Mapping[str, Any],
        findings: list[dict[str, str]],
        checks: list[dict[str, str]],
    ) -> None:
        continuity = spec.get("continuity")
        if not isinstance(continuity, Mapping):
            _block(findings, "continuity_missing", "CharacterSpec.continuity is missing")
            return

        for field in ("identity_locked", "redesign_requires_approval"):
            if continuity.get(field) is True:
                _pass(checks, field)
            else:
                _block(findings, field, f"{field} must be true")

    def _check_required_assets(
        self,
        spec: Mapping[str, Any],
        rig: Mapping[str, Any],
        evidence: Mapping[str, Any],
        findings: list[dict[str, str]],
        checks: list[dict[str, str]],
    ) -> None:
        required_parts = _string_set(
            _nested(rig, "parts", "required"), "rig_profile.parts.required"
        )
        present_parts = _string_set(evidence.get("parts"), "evidence.parts")
        _check_subset(
            checks, findings, "required_parts", required_parts, present_parts
        )

        required_actions = _string_set(
            spec.get("required_actions"), "character_spec.required_actions"
        )
        present_actions = _string_set(evidence.get("actions"), "evidence.actions")
        _check_subset(
            checks, findings, "required_actions", required_actions, present_actions
        )

        required_props = _string_set(
            _nested(spec, "props", "required"), "character_spec.props.required"
        )
        present_props = _string_set(evidence.get("props"), "evidence.props")
        _check_subset(
            checks, findings, "required_props", required_props, present_props
        )

        mouth_required = bool(_nested(rig, "capabilities", "mouth_visemes"))
        if mouth_required:
            expected = set(self._policy["semantic_visemes"])
            actual = _string_set(evidence.get("visemes"), "evidence.visemes")
            _check_subset(checks, findings, "semantic_visemes", expected, actual)

    def _check_reference_evidence(
        self,
        evidence: Mapping[str, Any],
        findings: list[dict[str, str]],
        checks: list[dict[str, str]],
    ) -> None:
        reference = evidence.get("reference_checks")
        if reference is None:
            for code in (
                "palette_reference",
                "proportions_reference",
                "wardrobe_reference",
                "scale_reference",
                "identity_reference",
            ):
                _warn(
                    findings,
                    f"{code}_missing",
                    "reference comparison not supplied yet",
                )
            return
        if not isinstance(reference, Mapping):
            raise CharacterQAError("evidence.reference_checks must be a mapping")

        mapping = {
            "palette_matches": "palette_reference",
            "proportions_match": "proportions_reference",
            "wardrobe_matches": "wardrobe_reference",
            "scale_within_range": "scale_reference",
            "identity_matches": "identity_reference",
        }
        for field, code in mapping.items():
            value = reference.get(field)
            if value is True:
                _pass(checks, code)
            elif value is False:
                _block(findings, code, f"{field} failed against approved reference")
            else:
                _warn(findings, f"{code}_missing", "reference comparison not supplied yet")


def _validate_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    _require_mapping(policy, "policy")
    if policy.get("version") != "1.0":
        raise CharacterQAError("policy.version must be '1.0'")
    characters = policy.get("characters")
    if not isinstance(characters, Mapping) or not characters:
        raise CharacterQAError("policy.characters must be a non-empty mapping")
    visemes = _string_set(policy.get("semantic_visemes"), "policy.semantic_visemes")
    if "REST" not in visemes:
        raise CharacterQAError("policy.semantic_visemes must include REST")

    normalized_characters: dict[str, dict[str, Any]] = {}
    for character_id, value in characters.items():
        if not isinstance(character_id, str) or not isinstance(value, Mapping):
            raise CharacterQAError("invalid policy character entry")
        species = _require_text(value.get("species"), f"characters.{character_id}.species")
        rig = value.get("rig_profile")
        if rig is not None:
            rig = _require_text(rig, f"characters.{character_id}.rig_profile")
        normalized_characters[character_id] = {
            "species": species,
            "rig_profile": rig,
            "proof_scope": value.get("proof_scope") is True,
        }

    return {
        "version": "1.0",
        "semantic_visemes": tuple(sorted(visemes)),
        "characters": normalized_characters,
    }


def _nested(value: Mapping[str, Any], first: str, second: str) -> Any:
    node = value.get(first)
    if not isinstance(node, Mapping):
        raise CharacterQAError(f"{first} must be a mapping")
    return node.get(second)


def _string_set(value: Any, label: str) -> set[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise CharacterQAError(f"{label} must be a sequence")
    result = set()
    for item in value:
        if not isinstance(item, str) or not item:
            raise CharacterQAError(f"{label} must contain non-empty strings")
        result.add(item)
    return result


def _require_mapping(value: Any, label: str) -> None:
    if not isinstance(value, Mapping):
        raise CharacterQAError(f"{label} must be a mapping")


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise CharacterQAError(f"{label} must be a non-empty string")
    return value


def _check_equal(
    checks: list[dict[str, str]],
    findings: list[dict[str, str]],
    code: str,
    actual: Any,
    expected: Any,
    message: str,
) -> None:
    if actual == expected:
        _pass(checks, code)
    else:
        _block(findings, code, message)


def _check_subset(
    checks: list[dict[str, str]],
    findings: list[dict[str, str]],
    code: str,
    required: set[str],
    actual: set[str],
) -> None:
    missing = sorted(required - actual)
    if missing:
        _block(findings, code, f"missing: {', '.join(missing)}")
    else:
        _pass(checks, code)


def _pass(checks: list[dict[str, str]], code: str) -> None:
    checks.append({"code": code, "status": "pass"})


def _block(findings: list[dict[str, str]], code: str, message: str) -> None:
    findings.append({"severity": "blocking", "code": code, "message": message})


def _warn(findings: list[dict[str, str]], code: str, message: str) -> None:
    findings.append({"severity": "warning", "code": code, "message": message})


def _report(
    character_id: str,
    findings: list[dict[str, str]],
    checks: list[dict[str, str]],
) -> dict[str, Any]:
    blocking = sum(1 for item in findings if item["severity"] == "blocking")
    warnings = sum(1 for item in findings if item["severity"] == "warning")
    return {
        "version": "1.0",
        "character_id": character_id,
        "status": "fail" if blocking else "pass",
        "blocking_count": blocking,
        "warning_count": warnings,
        "checks": checks,
        "findings": findings,
    }
