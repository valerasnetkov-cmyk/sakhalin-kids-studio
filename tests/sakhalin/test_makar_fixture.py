"""Integration tests for Makar technical fixture (SKIDS-011)."""

from __future__ import annotations

import json
import pathlib
import unittest
from xml.etree import ElementTree as ET

import yaml
from jsonschema import Draft202012Validator

from tools.character.sakhalin.character_loader import CharacterLoader
from tools.character.sakhalin.character_qa import CharacterQA
from tools.character.sakhalin.svg_scene_renderer import render_frame

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
CHAR_DIR = PROJECT_ROOT / "library" / "characters" / "makar"
ART_DIR = CHAR_DIR / "art"
POSE_DIR = CHAR_DIR / "poses"
ACTION_DIR = CHAR_DIR / "actions"

POSE_SCHEMA = json.loads(
    (PROJECT_ROOT / "schemas" / "sakhalin" / "pose.schema.json").read_text(
        encoding="utf-8"
    )
)
ACTION_SCHEMA = json.loads(
    (PROJECT_ROOT / "schemas" / "sakhalin" / "action.schema.json").read_text(
        encoding="utf-8"
    )
)
RIG = yaml.safe_load(
    (PROJECT_ROOT / "library" / "rig_profiles" / "fox_cartoon.yaml").read_text(
        encoding="utf-8"
    )
)

POSE_VALIDATOR = Draft202012Validator(POSE_SCHEMA)
ACTION_VALIDATOR = Draft202012Validator(ACTION_SCHEMA)
SEMANTIC_VISEMES = {"REST", "A", "E", "O", "U", "MBP", "FV", "SH", "L", "S"}


def _load_yaml_dir(path: pathlib.Path) -> dict[str, dict]:
    result = {}
    for item in sorted(path.glob("*.yaml")):
        data = yaml.safe_load(item.read_text(encoding="utf-8"))
        result[data["id"]] = data
    return result


def _local_name(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


class TestMakarCharacterSpec(unittest.TestCase):
    def test_character_loader_accepts_makar_fixture(self):
        spec = CharacterLoader.from_project_root(PROJECT_ROOT).load_core("makar")
        self.assertEqual(spec["id"], "makar")
        self.assertEqual(spec["species"], "fox")
        self.assertEqual(spec["rig_profile"], "fox_cartoon")
        self.assertFalse(spec["visual"]["base_regeneration_allowed"])

    def test_fixture_scope_is_minimal_proof_scope(self):
        spec = CharacterLoader.from_project_root(PROJECT_ROOT).load_core("makar")
        self.assertEqual(spec["required_views"], ["front"])
        self.assertEqual(
            set(spec["required_actions"]),
            {"idle", "blink", "look", "point", "talk"},
        )


class TestMakarMotionLibrary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.poses = _load_yaml_dir(POSE_DIR)
        cls.actions = _load_yaml_dir(ACTION_DIR)

    def test_all_poses_validate(self):
        self.assertGreaterEqual(len(self.poses), 5)
        for pose_id, pose in self.poses.items():
            with self.subTest(pose=pose_id):
                POSE_VALIDATOR.validate(pose)
                self.assertEqual(pose["rig_profile"], "fox_cartoon")

    def test_all_actions_validate(self):
        self.assertEqual(set(self.actions), {"idle", "blink", "look", "point", "talk"})
        for action_id, action in self.actions.items():
            with self.subTest(action=action_id):
                ACTION_VALIDATOR.validate(action)
                self.assertEqual(action["rig_profile"], "fox_cartoon")

    def test_action_pose_references_resolve(self):
        for action_id, action in self.actions.items():
            for phase in action["phases"]:
                with self.subTest(action=action_id, pose=phase["pose"]):
                    self.assertIn(phase["pose"], self.poses)


class TestMakarSvgRig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.svg_path = ART_DIR / "front.svg"
        cls.root = ET.parse(cls.svg_path).getroot()

    def test_svg_rig_profile_matches(self):
        self.assertEqual(self.root.get("data-rig-profile"), "fox_cartoon")

    def test_all_required_rig_parts_exist_once(self):
        observed = {}
        for elem in self.root.iter():
            part = elem.get("data-part")
            if part:
                observed[part] = observed.get(part, 0) + 1

        for required in RIG["parts"]["required"]:
            with self.subTest(part=required):
                self.assertEqual(observed.get(required), 1)

    def test_all_semantic_visemes_exist_once(self):
        observed = {}
        for elem in self.root.iter():
            viseme = elem.get("data-viseme")
            if viseme:
                observed[viseme] = observed.get(viseme, 0) + 1
        self.assertEqual(set(observed), SEMANTIC_VISEMES)
        self.assertTrue(all(count == 1 for count in observed.values()))

    def test_no_script_or_external_href(self):
        for elem in self.root.iter():
            self.assertNotEqual(_local_name(elem.tag), "script")
            for attr, value in elem.attrib.items():
                local = _local_name(attr)
                if local == "href":
                    self.assertTrue(value.startswith("#"))


class TestMakarRuntimeProof(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.poses = _load_yaml_dir(POSE_DIR)

    def test_renderer_can_render_pointing_talking_frame(self):
        timeline = {
            "version": "1.0",
            "rig_profile": "fox_cartoon",
            "duration_ms": 1000,
            "segments": [
                {
                    "start_ms": 0,
                    "end_ms": 1000,
                    "pose": "point_right",
                    "viseme": "A",
                }
            ],
        }
        output = render_frame(
            ART_DIR,
            1280,
            720,
            500,
            [
                {
                    "instance_id": "makar",
                    "asset_path": "front.svg",
                    "x": 500,
                    "y": 430,
                    "scale": 0.85,
                    "timeline": timeline,
                    "poses_by_id": self.poses,
                }
            ],
        )
        self.assertIn('data-character-instance="makar"', output)
        self.assertIn("rotate(-58)", output)
        self.assertIn('data-viseme="A"', output)

    def test_character_qa_has_no_blocking_fixture_findings(self):
        spec = CharacterLoader.from_project_root(PROJECT_ROOT).load_core("makar")
        evidence = {
            "character_id": "makar",
            "parts": RIG["parts"]["required"],
            "actions": ["idle", "blink", "look", "point", "talk"],
            "props": ["backpack"],
            "visemes": sorted(SEMANTIC_VISEMES),
        }
        report = CharacterQA.from_project_root(PROJECT_ROOT).review(spec, RIG, evidence)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["blocking_count"], 0)
        self.assertEqual(report["warning_count"], 5)


if __name__ == "__main__":
    unittest.main()
