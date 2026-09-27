"""Tests for structural Character QA (SKIDS-010)."""

import pathlib
import unittest

from tools.character.sakhalin.character_qa import CharacterQA, CharacterQAError

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _spec(**overrides) -> dict:
    data = {
        "id": "makar",
        "species": "fox",
        "rig_profile": "fox_cartoon",
        "visual": {
            "palette_locked": True,
            "proportions_locked": True,
            "wardrobe_locked": True,
            "base_regeneration_allowed": False,
        },
        "required_actions": ["idle", "blink", "look", "point", "talk"],
        "props": {"required": ["backpack"]},
        "continuity": {
            "identity_locked": True,
            "redesign_requires_approval": True,
        },
    }
    data.update(overrides)
    return data


def _rig(**overrides) -> dict:
    data = {
        "id": "fox_cartoon",
        "parts": {
            "required": [
                "body", "head", "eye_left", "eye_right",
                "pupil_left", "pupil_right", "mouth",
                "arm_left", "arm_right", "leg_left", "leg_right", "tail",
            ]
        },
        "capabilities": {"mouth_visemes": True},
    }
    data.update(overrides)
    return data


def _evidence(**overrides) -> dict:
    data = {
        "character_id": "makar",
        "parts": _rig()["parts"]["required"],
        "actions": ["idle", "blink", "look", "point", "talk"],
        "props": ["backpack"],
        "visemes": ["REST", "A", "E", "O", "U", "MBP", "FV", "SH", "L", "S"],
        "reference_checks": {
            "palette_matches": True,
            "proportions_match": True,
            "wardrobe_matches": True,
            "scale_within_range": True,
            "identity_matches": True,
        },
    }
    data.update(overrides)
    return data


class TestHappyPath(unittest.TestCase):
    def setUp(self):
        self.qa = CharacterQA.from_project_root(PROJECT_ROOT)

    def test_makar_passes_with_complete_evidence(self):
        report = self.qa.review(_spec(), _rig(), _evidence())
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["blocking_count"], 0)
        self.assertEqual(report["warning_count"], 0)

    def test_missing_reference_checks_are_warnings_not_fake_passes(self):
        evidence = _evidence()
        del evidence["reference_checks"]
        report = self.qa.review(_spec(), _rig(), evidence)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["blocking_count"], 0)
        self.assertEqual(report["warning_count"], 5)


class TestIdentity(unittest.TestCase):
    def setUp(self):
        self.qa = CharacterQA.from_project_root(PROJECT_ROOT)

    def test_unknown_character_is_blocking(self):
        spec = _spec(id="sima")
        report = self.qa.review(spec, _rig(), _evidence(character_id="sima"))
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any(x["code"] == "unknown_character" for x in report["findings"]))

    def test_species_mismatch_is_blocking(self):
        report = self.qa.review(_spec(species="seagull"), _rig(), _evidence())
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any(x["code"] == "species_matches_canon" for x in report["findings"]))

    def test_rig_mismatch_is_blocking(self):
        report = self.qa.review(_spec(rig_profile="sea_lion_cartoon"), _rig(), _evidence())
        self.assertEqual(report["status"], "fail")

    def test_evidence_for_other_character_is_blocking(self):
        report = self.qa.review(_spec(), _rig(), _evidence(character_id="leva"))
        self.assertEqual(report["status"], "fail")


class TestLocks(unittest.TestCase):
    def setUp(self):
        self.qa = CharacterQA.from_project_root(PROJECT_ROOT)

    def test_visual_unlock_is_blocking(self):
        visual = dict(_spec()["visual"])
        visual["palette_locked"] = False
        report = self.qa.review(_spec(visual=visual), _rig(), _evidence())
        self.assertEqual(report["status"], "fail")

    def test_base_regeneration_is_blocking(self):
        visual = dict(_spec()["visual"])
        visual["base_regeneration_allowed"] = True
        report = self.qa.review(_spec(visual=visual), _rig(), _evidence())
        self.assertEqual(report["status"], "fail")

    def test_identity_unlock_is_blocking(self):
        continuity = dict(_spec()["continuity"])
        continuity["identity_locked"] = False
        report = self.qa.review(_spec(continuity=continuity), _rig(), _evidence())
        self.assertEqual(report["status"], "fail")


class TestAssets(unittest.TestCase):
    def setUp(self):
        self.qa = CharacterQA.from_project_root(PROJECT_ROOT)

    def test_missing_required_part_is_blocking(self):
        parts = list(_evidence()["parts"])
        parts.remove("tail")
        report = self.qa.review(_spec(), _rig(), _evidence(parts=parts))
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any(x["code"] == "required_parts" for x in report["findings"]))

    def test_missing_required_action_is_blocking(self):
        report = self.qa.review(
            _spec(), _rig(), _evidence(actions=["idle", "blink", "look", "talk"])
        )
        self.assertEqual(report["status"], "fail")

    def test_missing_required_prop_is_blocking(self):
        report = self.qa.review(_spec(), _rig(), _evidence(props=[]))
        self.assertEqual(report["status"], "fail")

    def test_missing_viseme_is_blocking(self):
        visemes = list(_evidence()["visemes"])
        visemes.remove("MBP")
        report = self.qa.review(_spec(), _rig(), _evidence(visemes=visemes))
        self.assertEqual(report["status"], "fail")


class TestReferenceChecks(unittest.TestCase):
    def setUp(self):
        self.qa = CharacterQA.from_project_root(PROJECT_ROOT)

    def test_failed_identity_reference_is_blocking(self):
        checks = dict(_evidence()["reference_checks"])
        checks["identity_matches"] = False
        report = self.qa.review(_spec(), _rig(), _evidence(reference_checks=checks))
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any(x["code"] == "identity_reference" for x in report["findings"]))

    def test_unknown_reference_value_becomes_warning(self):
        checks = dict(_evidence()["reference_checks"])
        checks["palette_matches"] = None
        report = self.qa.review(_spec(), _rig(), _evidence(reference_checks=checks))
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["warning_count"], 1)


class TestPolicy(unittest.TestCase):
    def test_invalid_policy_version_rejected(self):
        with self.assertRaises(CharacterQAError):
            CharacterQA({
                "version": "2.0",
                "semantic_visemes": ["REST"],
                "characters": {"makar": {"species": "fox", "rig_profile": "fox_cartoon"}},
            })


if __name__ == "__main__":
    unittest.main()
