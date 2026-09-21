"""Tests for sakhalin character_qa.py - SKIDS-010."""

from __future__ import annotations
import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.character.sakhalin.character_qa import (
    CharacterQAError,
    load_team_canon,
    review_character,
    to_openmontage_report,
)

# ---------------------------------------------------------------------------
# SVG fixtures
# ---------------------------------------------------------------------------

def _svg(rig, parts_data, mouth=True, expressions=True, gaze=True):
    """Build a minimal valid SVG with all required elements."""
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 700" data-rig-profile="{rig}">'
    for part, inner in parts_data:
        svg += f'<g data-part="{part}">{inner}</g>'
    if expressions:
        for e in ["neutral","happy","curious","thinking","surprised","worried"]:
            svg += f'<g data-expression="{e}"><rect width="10" height="10"/></g>'
    if gaze:
        for g in ["left","center","right","up","down"]:
            svg += f'<g data-gaze="{g}"><circle r="2"/></g>'
    if mouth:
        svg += '<g data-part="mouth">'
        for v in ["REST","A","E","O","U","MBP","FV","SH","L","S"]:
            svg += f'<g data-viseme="{v}"><rect width="8" height="4"/></g>'
        svg += '</g>'
    svg += '</svg>'
    return svg


FOX_PARTS = [
    ("body", '<rect width="100" height="100"/>'),
    ("head", '<g data-motion-root=""><circle r="50"/></g>'),
    ("eye_left", '<g data-variant="open"><circle r="5"/></g><g data-variant="closed"><line x1="-5" y1="0" x2="5" y2="0"/></g>'),
    ("eye_right", '<g data-variant="open"><circle r="5"/></g><g data-variant="closed"><line x1="-5" y1="0" x2="5" y2="0"/></g>'),
    ("pupil_left", '<circle cx="0" cy="0" r="3"/>'),
    ("pupil_right", '<circle cx="0" cy="0" r="3"/>'),
    ("arm_left", '<rect width="20" height="60"/>'),
    ("arm_right", '<rect width="20" height="60"/>'),
    ("leg_left", '<rect width="15" height="50"/>'),
    ("leg_right", '<rect width="15" height="50"/>'),
    ("tail", '<ellipse rx="10" ry="30"/>'),
]

LION_PARTS = [
    ("body", '<rect width="80" height="80"/>'),
    ("head", '<g data-motion-root=""><circle r="40"/></g>'),
    ("eye_left", '<g data-variant="open"><circle r="5"/></g><g data-variant="closed"><line x1="-5" y1="0" x2="5" y2="0"/></g>'),
    ("eye_right", '<g data-variant="open"><circle r="5"/></g><g data-variant="closed"><line x1="-5" y1="0" x2="5" y2="0"/></g>'),
    ("pupil_left", '<circle cx="0" cy="0" r="3"/>'),
    ("pupil_right", '<circle cx="0" cy="0" r="3"/>'),
    ("flipper_left", '<rect width="30" height="50"/>'),
    ("flipper_right", '<rect width="30" height="50"/>'),
]

HUMAN_PARTS = [
    ("body", '<rect width="100" height="100"/>'),
    ("head", '<g data-motion-root=""><circle r="50"/></g>'),
    ("eye_left", '<g data-variant="open"><circle r="5"/></g>'),
    ("eye_right", '<g data-variant="open"><circle r="5"/></g>'),
    ("pupil_left", '<circle cx="0" cy="0" r="3"/>'),
    ("pupil_right", '<circle cx="0" cy="0" r="3"/>'),
    ("arm_left", '<rect width="20" height="60"/>'),
    ("arm_right", '<rect width="20" height="60"/>'),
    ("leg_left", '<rect width="15" height="50"/>'),
    ("leg_right", '<rect width="15" height="50"/>'),
]

_FOX_SVG = _svg("fox_cartoon", FOX_PARTS)
_LION_SVG = _svg("sea_lion_cartoon", LION_PARTS)
_HUMAN_SVG = _svg("human_child_cartoon", HUMAN_PARTS)

# NOMOUTH: no mouth part at all
_NOMOUTH_SVG = _svg("fox_cartoon", FOX_PARTS, mouth=False)

# NOGAZE: no gaze elements
_NOGAZE_SVG = _svg("fox_cartoon", FOX_PARTS, gaze=False)

# DUPE_SVG: duplicate REST viseme
def _dupe_svg():
    svg = _svg("fox_cartoon", FOX_PARTS)
    # Insert a duplicate REST viseme before closing mouth tag
    svg = svg.replace('</g></svg>', '<g data-viseme="REST"><rect width="8" height="4"/></g></g></svg>')
    return svg
_DUPE_SVG = _dupe_svg()

# NOEXPR: no expressions
_NOEXPR_SVG = _svg("fox_cartoon", FOX_PARTS, expressions=False)

# Missing REST viseme (only has A..S)
def _no_rest_svg():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 700" data-rig-profile="fox_cartoon">'
    for part, inner in FOX_PARTS:
        svg += f'<g data-part="{part}">{inner}</g>'
    for e in ["neutral","happy","curious","thinking","surprised","worried"]:
        svg += f'<g data-expression="{e}"><rect width="10" height="10"/></g>'
    for g in ["left","center","right","up","down"]:
        svg += f'<g data-gaze="{g}"><circle r="2"/></g>'
    svg += '<g data-part="mouth">'
    for v in ["A","E","O","U","MBP","FV","SH","L","S"]:
        svg += f'<g data-viseme="{v}"><rect width="8" height="4"/></g>'
    svg += '</g></svg>'
    return svg
_NO_REST_SVG = _no_rest_svg()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _canon_path(tmp):
    p = tmp / "canon.json"
    p.write_text(json.dumps({
        "version": "1.0",
        "characters": {
            "makar": {"species": "fox", "rig_profile": "fox_cartoon"},
            "leva": {"species": "sea_lion", "rig_profile": "sea_lion_cartoon"},
            "tikhon": {"species": "bear", "rig_profile": None},
            "anna": {"species": "seal", "rig_profile": None},
            "antoshka": {"species": "human", "rig_profile": None},
        }
    }), encoding="utf-8")
    return p


def _spec(cid="makar", species="fox", rig="fox_cartoon"):
    return {
        "version": "1.0", "id": cid, "display_name": cid.title(),
        "species": species, "rig_profile": rig, "role": "test",
        "story": {"primary_question": "?", "catchphrase": "!"},
        "visual": {"palette_locked": True, "proportions_locked": True,
                    "wardrobe_locked": True, "base_regeneration_allowed": False},
        "required_views": ["front"],
        "required_expressions": ["neutral"],
        "required_actions": ["idle"],
        "props": {"required": []},
        "voice": {"profile": cid},
        "continuity": {"identity_locked": True, "redesign_requires_approval": True},
    }


def _rig(rid="fox_cartoon", parts=None, caps=None):
    if parts is None:
        parts = ["body", "head", "eye_left", "eye_right", "pupil_left",
                  "pupil_right", "mouth", "arm_left", "arm_right",
                  "leg_left", "leg_right", "tail"]
    if caps is None:
        caps = {"blink": True, "gaze": True, "mouth_visemes": True,
                "head_turn": True, "arm_gestures": True, "tail_motion": True,
                "flipper_gestures": False, "wing_gestures": False}
    return {"version": "1.0", "id": rid, "parts": {"required": parts}, "capabilities": caps}


def _pose(pid="idle", rig="fox_cartoon"):
    return {"version": "1.0", "id": pid, "rig_profile": rig,
            "state": {"parts": {"head": {"rotation_deg": 0}}}}


def _action(aid="idle", rig="fox_cartoon", poses=None):
    if poses is None:
        poses = ["idle"]
    phases = [{"name": "p", "duration_ms": 100, "pose": p} for p in poses]
    return {"version": "1.0", "id": aid, "rig_profile": rig, "phases": phases}


def _write_svg(tmp, name, content):
    p = tmp / name
    p.write_text(content, encoding="utf-8")
    return p


def _ok(tmp, **kw):
    t = Path(tmp)
    svg = kw.pop("svg", _FOX_SVG)
    svg_path = _write_svg(t, "f.svg", svg)
    spec = kw.pop("spec", _spec())
    rig = kw.pop("rig", _rig())
    poses = kw.pop("poses", {"idle": _pose()})
    actions = kw.pop("actions", {"idle": _action(), "blink": _action("blink")})
    return dict(spec=spec, rig_profile=rig, svg_path=svg_path,
                poses_by_id=poses, actions_by_id=actions, canon_path=_canon_path(t))


# ---------------------------------------------------------------------------
# Team canon
# ---------------------------------------------------------------------------

class TCanon(unittest.TestCase):
    def test_canon_loads(self):
        with tempfile.TemporaryDirectory() as td:
            c = load_team_canon(_canon_path(Path(td)))
            self.assertEqual(set(c["characters"].keys()),
                             {"makar", "leva", "tikhon", "anna", "antoshka"})

    def test_makar_fox(self):
        with tempfile.TemporaryDirectory() as td:
            c = load_team_canon(_canon_path(Path(td)))
            self.assertEqual(c["characters"]["makar"]["species"], "fox")

    def test_leva_sea_lion(self):
        with tempfile.TemporaryDirectory() as td:
            c = load_team_canon(_canon_path(Path(td)))
            self.assertEqual(c["characters"]["leva"]["species"], "sea_lion")

    def test_antoshka_human(self):
        with tempfile.TemporaryDirectory() as td:
            c = load_team_canon(_canon_path(Path(td)))
            self.assertEqual(c["characters"]["antoshka"]["species"], "human")
            self.assertIsNone(c["characters"]["antoshka"]["rig_profile"])

    def test_sima_excluded(self):
        with tempfile.TemporaryDirectory() as td:
            c = load_team_canon(_canon_path(Path(td)))
            self.assertNotIn("sima", c["characters"])

    def test_canon_missing_file(self):
        with self.assertRaises(CharacterQAError):
            load_team_canon(Path("/nonexistent/canon.json"))


# ---------------------------------------------------------------------------
# Valid bundles
# ---------------------------------------------------------------------------

class TValidBundles(unittest.TestCase):
    def test_makar_passes(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td))
            self.assertEqual(r["status"], "pass")
            self.assertFalse(any(f["severity"] == "blocking" for f in r["findings"]))

    def test_leva_passes(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            parts = ["body", "head", "eye_left", "eye_right", "pupil_left",
                     "pupil_right", "mouth", "flipper_left", "flipper_right"]
            caps = {"blink": True, "gaze": True, "mouth_visemes": True,
                    "head_turn": True, "arm_gestures": False, "tail_motion": False,
                    "flipper_gestures": True, "wing_gestures": False}
            lp = {"version": "1.0", "id": "idle", "rig_profile": "sea_lion_cartoon",
                  "state": {"parts": {"head": {"rotation_deg": 0}}}}
            la = {"version": "1.0", "id": "idle", "rig_profile": "sea_lion_cartoon",
                  "phases": [{"name": "p", "duration_ms": 100, "pose": "idle"}]}
            lb = {"version": "1.0", "id": "blink", "rig_profile": "sea_lion_cartoon",
                  "phases": [{"name": "p", "duration_ms": 100, "pose": "idle"}]}
            r = review_character(
                spec=_spec("leva", "sea_lion", "sea_lion_cartoon"),
                rig_profile=_rig("sea_lion_cartoon", parts, caps),
                svg_path=_write_svg(t, "f.svg", _LION_SVG),
                poses_by_id={"idle": lp},
                actions_by_id={"idle": la, "blink": lb},
                canon_path=_canon_path(t),
            )
            self.assertEqual(r["status"], "pass")


# ---------------------------------------------------------------------------
# Canon failures
# ---------------------------------------------------------------------------

class TCanonFailures(unittest.TestCase):
    def test_unknown_id(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td, spec=_spec("sima")))
            self.assertEqual(r["status"], "fail")
            self.assertTrue(any(f["code"] == "unknown_canon_id" for f in r["findings"]))

    def test_makar_wrong_species(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td, spec=_spec("makar", "seal")))
            self.assertEqual(r["status"], "fail")
            self.assertTrue(any(f["code"] == "species_mismatch" for f in r["findings"]))

    def test_leva_wrong_species(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            parts = ["body", "head", "eye_left", "eye_right", "pupil_left",
                     "pupil_right", "mouth", "flipper_left", "flipper_right"]
            caps = {"blink": True, "gaze": True, "mouth_visemes": True,
                    "head_turn": True, "arm_gestures": False, "tail_motion": False,
                    "flipper_gestures": True, "wing_gestures": False}
            r = review_character(
                spec=_spec("leva", "fox", "sea_lion_cartoon"),
                rig_profile=_rig("sea_lion_cartoon", parts, caps),
                svg_path=_write_svg(t, "f.svg", _LION_SVG),
                poses_by_id={"idle": _pose("idle", "sea_lion_cartoon")},
                actions_by_id={"idle": _action("idle", "sea_lion_cartoon")},
                canon_path=_canon_path(t),
            )
            self.assertEqual(r["status"], "fail")
            self.assertTrue(any(f["code"] == "species_mismatch" for f in r["findings"]))

    def test_antoshka_human_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            parts = ["body", "head", "eye_left", "eye_right", "pupil_left",
                     "pupil_right", "mouth", "arm_left", "arm_right",
                     "leg_left", "leg_right"]
            caps = {"blink": True, "gaze": True, "mouth_visemes": True,
                    "head_turn": True, "arm_gestures": True, "tail_motion": False,
                    "flipper_gestures": False, "wing_gestures": False}
            hp = {"version": "1.0", "id": "idle", "rig_profile": "human_child_cartoon",
                  "state": {"parts": {"head": {"rotation_deg": 0}}}}
            ha = {"version": "1.0", "id": "idle", "rig_profile": "human_child_cartoon",
                  "phases": [{"name": "p", "duration_ms": 100, "pose": "idle"}]}
            hb = {"version": "1.0", "id": "blink", "rig_profile": "human_child_cartoon",
                  "phases": [{"name": "p", "duration_ms": 100, "pose": "idle"}]}
            r = review_character(
                spec=_spec("antoshka", "human", "human_child_cartoon"),
                rig_profile=_rig("human_child_cartoon", parts, caps),
                svg_path=_write_svg(t, "f.svg", _HUMAN_SVG),
                poses_by_id={"idle": hp},
                actions_by_id={"idle": ha, "blink": hb},
                canon_path=_canon_path(t),
            )
            self.assertNotEqual(r["status"], "fail")
            self.assertFalse(any(f["code"] == "species_mismatch" for f in r["findings"]))

    def test_antoshka_seagull_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td, spec=_spec("antoshka", "seagull")))
            self.assertEqual(r["status"], "fail")
            self.assertTrue(any(f["code"] == "species_mismatch" for f in r["findings"]))

    def test_antoshka_sable_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td, spec=_spec("antoshka", "sable")))
            self.assertEqual(r["status"], "fail")
            self.assertTrue(any(f["code"] == "species_mismatch" for f in r["findings"]))

    def test_makar_wrong_rig(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td, spec=_spec("makar", "fox", "sea_lion_cartoon")))
            self.assertEqual(r["status"], "fail")
            self.assertTrue(any(f["code"] == "rig_canon_mismatch" for f in r["findings"]))

    def test_leva_wrong_rig(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            parts = ["body", "head", "eye_left", "eye_right", "pupil_left",
                     "pupil_right", "mouth", "flipper_left", "flipper_right"]
            caps = {"blink": True, "gaze": True, "mouth_visemes": True,
                    "head_turn": True, "arm_gestures": False, "tail_motion": False,
                    "flipper_gestures": True, "wing_gestures": False}
            r = review_character(
                spec=_spec("leva", "sea_lion", "fox_cartoon"),
                rig_profile=_rig("fox_cartoon", parts, caps),
                svg_path=_write_svg(t, "f.svg", _LION_SVG),
                poses_by_id={"idle": _pose("idle", "fox_cartoon")},
                actions_by_id={"idle": _action("idle", "fox_cartoon")},
                canon_path=_canon_path(t),
            )
            self.assertEqual(r["status"], "fail")
            self.assertTrue(any(f["code"] == "rig_canon_mismatch" for f in r["findings"]))


if __name__ == "__main__":
    unittest.main()
