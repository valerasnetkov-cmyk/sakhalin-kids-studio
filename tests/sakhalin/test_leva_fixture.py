"""SKIDS-012 — Leva fixture asset tests (proof fixture, not final art)."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

import yaml
from jsonschema import Draft202012Validator

from tools.character.sakhalin.character_qa import review_character
from tools.character.sakhalin.svg_scene_renderer import render_frame

_BUNDLE = Path(__file__).resolve().parents[2] / "library" / "characters" / "leva"
_ART = _BUNDLE / "art" / "front.svg"
_SPEC_PATH = _BUNDLE / "character.yaml"
_RIG_PATH = Path(__file__).resolve().parents[2] / "library" / "rig_profiles" / "sea_lion_cartoon.yaml"
_SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "schemas" / "sakhalin"

_REQUIRED_PARTS = frozenset({
    "body", "head", "eye_left", "eye_right", "pupil_left", "pupil_right",
    "mouth", "flipper_left", "flipper_right",
})
_REQUIRED_VISEMES = ["REST", "A", "E", "O", "U", "MBP", "FV", "SH", "L", "S"]
_REQUIRED_GAZE = frozenset({"left", "center", "right", "up", "down"})
_EXTERNAL_RE = re.compile(
    r"(https?://(?!www\.w3\.org)|ftp://|data:|<script|<foreignObject)", re.I,
)


def _spec():
    return yaml.safe_load(_SPEC_PATH.read_text(encoding="utf-8"))


def _rig():
    return yaml.safe_load(_RIG_PATH.read_text(encoding="utf-8"))


def _poses():
    d = {}
    for f in sorted((_BUNDLE / "poses").glob("*.yaml")):
        p = yaml.safe_load(f.read_text(encoding="utf-8"))
        d[p["id"]] = p
    return d


def _actions():
    d = {}
    for f in sorted((_BUNDLE / "actions").glob("*.yaml")):
        a = yaml.safe_load(f.read_text(encoding="utf-8"))
        d[a["id"]] = a
    return d


def _svg_info():
    root = ET.parse(_ART).getroot()
    parts, visemes, all_v, gaze, expr = set(), set(), [], set(), set()
    for e in root.iter():
        p = e.get("data-part")
        if p:
            parts.add(p)
        v = e.get("data-viseme")
        if v:
            visemes.add(v)
            all_v.append(v)
        g = e.get("data-gaze")
        if g:
            gaze.add(g)
        x = e.get("data-expression")
        if x:
            expr.add(x)
    return {"parts": parts, "visemes": visemes, "all_visemes": all_v,
            "gaze": gaze, "expressions": expr}


def _tl(rig="sea_lion_cartoon", dur=1000, segs=None):
    if segs is None:
        segs = [{"start_ms": 0, "end_ms": dur, "pose": "idle", "viseme": "REST"}]
    return {"version": "1.0", "rig_profile": rig, "duration_ms": dur, "segments": segs}


def _chars(tl, poses=None, inst="leva", x=250, y=600, scale=1.0):
    return [{"instance_id": inst, "asset_path": "art/front.svg",
             "x": x, "y": y, "scale": scale, "timeline": tl,
             "poses_by_id": poses or _poses()}]


class TSpec(unittest.TestCase):
    def test_01_yaml_validates(self):
        schema = json.loads((_SCHEMAS_DIR / "character_spec.schema.json").read_text())
        errs = list(Draft202012Validator(schema).iter_errors(_spec()))
        self.assertEqual(errs, [])

    def test_02_id_leva(self):
        self.assertEqual(_spec()["id"], "leva")

    def test_03_species_sea_lion(self):
        self.assertEqual(_spec()["species"], "sea_lion")

    def test_04_rig_sea_lion_cartoon(self):
        self.assertEqual(_spec()["rig_profile"], "sea_lion_cartoon")


class TArt(unittest.TestCase):
    def test_05_front_svg_exists(self):
        self.assertTrue(_ART.is_file())

    def test_06_root_rig_profile(self):
        self.assertEqual(ET.parse(_ART).getroot().get("data-rig-profile"), "sea_lion_cartoon")

    def test_07_all_parts_exist(self):
        info = _svg_info()
        missing = _REQUIRED_PARTS - info["parts"]
        self.assertEqual(missing, set())

    def test_08_all_10_visemes_exactly_once(self):
        info = _svg_info()
        self.assertEqual(info["visemes"], set(_REQUIRED_VISEMES))
        self.assertEqual(len(info["all_visemes"]), 10)

    def test_09_no_unknown_visemes(self):
        info = _svg_info()
        self.assertEqual(info["visemes"] - set(_REQUIRED_VISEMES), set())

    def test_10_all_5_gaze_directions(self):
        self.assertEqual(_svg_info()["gaze"], _REQUIRED_GAZE)

    def test_11_neutral_expression(self):
        self.assertIn("neutral", _svg_info()["expressions"])

    def test_12_thinking_expression(self):
        self.assertIn("thinking", _svg_info()["expressions"])


class TActionExistence(unittest.TestCase):
    def test_13_blink(self):
        self.assertIn("blink", _actions())

    def test_14_idle(self):
        self.assertIn("idle", _actions())

    def test_15_look(self):
        self.assertIn("look", _actions())

    def test_16_think(self):
        self.assertIn("think", _actions())

    def test_17_talk(self):
        self.assertIn("talk", _actions())


class TSchemaValidation(unittest.TestCase):
    def test_18_poses_validate(self):
        v = Draft202012Validator(json.loads((_SCHEMAS_DIR / "pose.schema.json").read_text()))
        for pid, pose in _poses().items():
            self.assertEqual(list(v.iter_errors(pose)), [], f"pose {pid!r}")

    def test_19_actions_validate(self):
        v = Draft202012Validator(json.loads((_SCHEMAS_DIR / "action.schema.json").read_text()))
        for aid, act in _actions().items():
            self.assertEqual(list(v.iter_errors(act)), [], f"action {aid!r}")

    def test_20_action_pose_refs_resolve(self):
        poses = _poses()
        for aid, act in _actions().items():
            for ph in act["phases"]:
                self.assertIn(ph["pose"], poses,
                              f"action {aid!r} phase {ph['name']!r} -> missing {ph['pose']!r}")

    def test_21_no_pose_controls_mouth(self):
        for pid, pose in _poses().items():
            self.assertNotIn("mouth", pose.get("state", {}).get("parts", {}),
                             f"pose {pid!r} controls mouth")


class TCharacterQA(unittest.TestCase):
    def test_22_reviewer_pass(self):
        r = review_character(
            spec=_spec(), rig_profile=_rig(), svg_path=_ART,
            poses_by_id=_poses(), actions_by_id=_actions(),
        )
        self.assertEqual(r["status"], "pass")
        blocking = [f for f in r["findings"] if f["severity"] == "blocking"]
        self.assertEqual(blocking, [])


class TRenderer(unittest.TestCase):
    def test_23_idle_render(self):
        svg = render_frame(_BUNDLE, 500, 700, 0, _chars(_tl()))
        self.assertIn("leva", svg)

    def test_24_blink_observable(self):
        p = _poses()
        segs = [
            {"start_ms": 0, "end_ms": 100, "pose": "idle", "viseme": "REST"},
            {"start_ms": 100, "end_ms": 180, "pose": "blink_closed", "viseme": "REST"},
            {"start_ms": 180, "end_ms": 300, "pose": "idle", "viseme": "REST"},
        ]
        a = render_frame(_BUNDLE, 500, 700, 0, _chars(_tl(dur=300, segs=segs), p))
        b = render_frame(_BUNDLE, 500, 700, 140, _chars(_tl(dur=300, segs=segs), p))
        self.assertNotEqual(a, b)

    def test_25_gaze_observable(self):
        segs = [
            {"start_ms": 0, "end_ms": 500, "pose": "idle", "viseme": "REST"},
            {"start_ms": 500, "end_ms": 1000, "pose": "look_left", "viseme": "REST"},
        ]
        a = render_frame(_BUNDLE, 500, 700, 0, _chars(_tl(segs=segs)))
        b = render_frame(_BUNDLE, 500, 700, 750, _chars(_tl(segs=segs)))
        self.assertNotEqual(a, b)

    def test_26_think_observable(self):
        segs = [
            {"start_ms": 0, "end_ms": 200, "pose": "idle", "viseme": "REST"},
            {"start_ms": 200, "end_ms": 1000, "pose": "think", "viseme": "REST"},
            {"start_ms": 1000, "end_ms": 1200, "pose": "idle", "viseme": "REST"},
        ]
        a = render_frame(_BUNDLE, 500, 700, 0, _chars(_tl(dur=1200, segs=segs)))
        b = render_frame(_BUNDLE, 500, 700, 600, _chars(_tl(dur=1200, segs=segs)))
        self.assertNotEqual(a, b)

    def test_27_viseme_observable(self):
        segs = [
            {"start_ms": 0, "end_ms": 500, "pose": "idle", "viseme": "REST"},
            {"start_ms": 500, "end_ms": 1000, "pose": "talk", "viseme": "A"},
        ]
        a = render_frame(_BUNDLE, 500, 700, 0, _chars(_tl(segs=segs)))
        b = render_frame(_BUNDLE, 500, 700, 750, _chars(_tl(segs=segs)))
        self.assertNotEqual(a, b)

    def test_28_deterministic(self):
        c = _chars(_tl())
        a = render_frame(_BUNDLE, 500, 700, 0, c)
        b = render_frame(_BUNDLE, 500, 700, 0, c)
        self.assertEqual(a, b)


class TSecurity(unittest.TestCase):
    def test_29_no_external_refs(self):
        for f in _BUNDLE.rglob("*"):
            if f.is_file() and f.suffix in (".yaml", ".svg", ".json"):
                content = f.read_text(encoding="utf-8")
                m = _EXTERNAL_RE.search(content)
                self.assertIsNone(m, f"{f.name}: {m.group() if m else ''}")

    def test_30_svg_under_2mb(self):
        self.assertLessEqual(_ART.stat().st_size, 2 * 1024 * 1024)
