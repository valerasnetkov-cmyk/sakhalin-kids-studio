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


def _local_tag(elem):
    return elem.tag.split("}")[-1]


def _parse_frame(svg_text):
    return ET.fromstring(svg_text)


def _active_variant(root, part_id):
    parts = [e for e in root.iter() if e.get("data-part") == part_id]
    if len(parts) != 1:
        raise AssertionError(f"expected 1 part {part_id!r}, found {len(parts)}")
    return [v.get("data-variant") for v in parts[0].iter()
            if v.get("data-variant") is not None and v.get("display") != "none"]


def _active_layer(root, attr):
    return [e.get(attr) for e in root.iter()
            if e.get(attr) is not None and e.get("display") != "none"]


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

    def test_31_eye_open_variant_has_no_drawn_pupil(self):
        root = ET.parse(_ART).getroot()
        for eye in ("eye_left", "eye_right"):
            part = next(e for e in root.iter() if e.get("data-part") == eye)
            open_v = next(e for e in part.iter() if e.get("data-variant") == "open")
            tags = [_local_tag(e) for e in open_v.iter()]
            self.assertIn("ellipse", tags,
                          f"{eye}: open variant must draw the eye sclera")
            self.assertNotIn("circle", tags,
                             f"{eye}: open variant must not draw a pupil")

    def test_32_pupils_have_hidden_variant(self):
        root = ET.parse(_ART).getroot()
        for side in ("pupil_left", "pupil_right"):
            part = next(e for e in root.iter() if e.get("data-part") == side)
            variants = [e.get("data-variant") for e in part.iter()
                        if e.get("data-variant")]
            self.assertIn("hidden", variants,
                          f"{side}: missing hidden variant")


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

    def test_33_gaze_pupil_variants_synced(self):
        for pid, pose in _poses().items():
            gaze = pose.get("state", {}).get("gaze", {})
            direction = gaze.get("direction") if isinstance(gaze, dict) else None
            if direction is None:
                continue
            parts = pose.get("state", {}).get("parts", {})
            for side in ("pupil_left", "pupil_right"):
                variant = parts.get(side, {}).get("variant")
                self.assertEqual(
                    variant, direction,
                    f"pose {pid!r}: gaze {direction!r} but {side}={variant!r}")


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
    def _assert_variant(self, root, part_id, expected):
        act = _active_variant(root, part_id)
        self.assertEqual(act, [expected], f"part {part_id!r}")

    def _assert_layer(self, root, attr, expected):
        act = _active_layer(root, attr)
        self.assertEqual(act, [expected], f"attr {attr!r}")

    def test_23_idle_render(self):
        root = _parse_frame(render_frame(_BUNDLE, 500, 700, 0, _chars(_tl())))
        inst = [e for e in root.iter()
                if e.get("data-character-instance") == "leva"]
        self.assertEqual(len(inst), 1)
        self._assert_variant(root, "eye_left", "open")
        self._assert_variant(root, "eye_right", "open")
        self._assert_variant(root, "pupil_left", "center")
        self._assert_variant(root, "pupil_right", "center")
        self._assert_layer(root, "data-expression", "neutral")
        self._assert_layer(root, "data-gaze", "center")
        self._assert_layer(root, "data-viseme", "REST")

    def test_24_blink_closed_state(self):
        p = _poses()
        segs = [
            {"start_ms": 0, "end_ms": 100, "pose": "idle", "viseme": "REST"},
            {"start_ms": 100, "end_ms": 180, "pose": "blink_closed", "viseme": "REST"},
            {"start_ms": 180, "end_ms": 300, "pose": "idle", "viseme": "REST"},
        ]
        tl = _tl(dur=300, segs=segs)
        open_r = _parse_frame(render_frame(_BUNDLE, 500, 700, 0, _chars(tl, p)))
        closed_r = _parse_frame(render_frame(_BUNDLE, 500, 700, 140, _chars(tl, p)))
        self._assert_variant(open_r, "eye_left", "open")
        self._assert_variant(open_r, "pupil_left", "center")
        self._assert_variant(closed_r, "eye_left", "closed")
        self._assert_variant(closed_r, "eye_right", "closed")
        self._assert_variant(closed_r, "pupil_left", "hidden")
        self._assert_variant(closed_r, "pupil_right", "hidden")
        self._assert_layer(closed_r, "data-viseme", "REST")

    def test_25_gaze_pupil_sync(self):
        segs = [
            {"start_ms": 0, "end_ms": 500, "pose": "idle", "viseme": "REST"},
            {"start_ms": 500, "end_ms": 1000, "pose": "look_left", "viseme": "REST"},
        ]
        tl = _tl(segs=segs)
        idle_r = _parse_frame(render_frame(_BUNDLE, 500, 700, 0, _chars(tl)))
        left_r = _parse_frame(render_frame(_BUNDLE, 500, 700, 750, _chars(tl)))
        self._assert_layer(idle_r, "data-gaze", "center")
        self._assert_variant(idle_r, "pupil_left", "center")
        self._assert_variant(idle_r, "pupil_right", "center")
        self._assert_layer(left_r, "data-gaze", "left")
        self._assert_variant(left_r, "pupil_left", "left")
        self._assert_variant(left_r, "pupil_right", "left")

    def test_26_think_state(self):
        segs = [
            {"start_ms": 0, "end_ms": 200, "pose": "idle", "viseme": "REST"},
            {"start_ms": 200, "end_ms": 1000, "pose": "think", "viseme": "REST"},
            {"start_ms": 1000, "end_ms": 1200, "pose": "idle", "viseme": "REST"},
        ]
        tl = _tl(dur=1200, segs=segs)
        think_r = _parse_frame(render_frame(_BUNDLE, 500, 700, 600, _chars(tl)))
        self._assert_layer(think_r, "data-expression", "thinking")
        self._assert_layer(think_r, "data-gaze", "up")
        self._assert_variant(think_r, "pupil_left", "up")
        self._assert_variant(think_r, "pupil_right", "up")
        head = [e for e in think_r.iter() if e.get("data-part") == "head"]
        roots = [e for e in head[0].iter() if e.get("data-motion-root") is not None]
        self.assertEqual(roots[0].get("transform"), "rotate(-4)")

    def test_27_viseme_state(self):
        segs = [
            {"start_ms": 0, "end_ms": 500, "pose": "idle", "viseme": "REST"},
            {"start_ms": 500, "end_ms": 1000, "pose": "talk", "viseme": "A"},
        ]
        tl = _tl(segs=segs)
        rest_r = _parse_frame(render_frame(_BUNDLE, 500, 700, 0, _chars(tl)))
        a_r = _parse_frame(render_frame(_BUNDLE, 500, 700, 750, _chars(tl)))
        self._assert_layer(rest_r, "data-viseme", "REST")
        self._assert_layer(a_r, "data-viseme", "A")

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
