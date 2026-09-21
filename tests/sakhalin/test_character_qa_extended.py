"""Extended tests for sakhalin character_qa.py - SKIDS-010."""

from __future__ import annotations
import copy
import tempfile
import unittest
from pathlib import Path

from tools.character.sakhalin.character_qa import (
    load_team_canon,
    review_character,
    to_openmontage_report,
)

from tests.sakhalin.test_character_qa import (
    _FOX_SVG, _ok, _spec, _rig, _pose, _action, _canon_path, _write_svg,
)


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

class TSchemaValidation(unittest.TestCase):
    def test_malformed_spec(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td, spec={"bad": 1}))
            self.assertEqual(r["status"], "fail")
            self.assertTrue(any(f["code"] == "invalid_spec" for f in r["findings"]))

    def test_malformed_rig(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td, rig={"bad": 1}))
            self.assertEqual(r["status"], "fail")
            self.assertTrue(any(f["code"] == "invalid_rig_profile" for f in r["findings"]))


# ---------------------------------------------------------------------------
# Rig checks
# ---------------------------------------------------------------------------

class TRigChecks(unittest.TestCase):
    def test_missing_part(self):
        with tempfile.TemporaryDirectory() as td:
            parts = ["body", "head", "eye_left", "eye_right", "pupil_left",
                     "pupil_right", "mouth", "arm_left", "arm_right",
                     "leg_left", "leg_right", "tail", "wing_left"]
            r = review_character(**_ok(td, rig=_rig(parts=parts)))
            self.assertTrue(any(f["code"] == "missing_required_part" for f in r["findings"]))

    def test_rig_id_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td, rig=_rig("wrong_rig")))
            self.assertTrue(any(f["code"] == "rig_id_mismatch" for f in r["findings"]))


# ---------------------------------------------------------------------------
# Viseme checks
# ---------------------------------------------------------------------------

class TVisemeChecks(unittest.TestCase):
    def test_all_10_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td))
            vis_f = [f for f in r["findings"] if "viseme" in f["code"]]
            self.assertEqual(len(vis_f), 0)

    def test_missing_REST(self):
        with tempfile.TemporaryDirectory() as td:
            from tests.sakhalin.test_character_qa import _NOMOUTH_SVG
            r = review_character(**_ok(td, svg=_NOMOUTH_SVG))
            self.assertTrue(any(f["code"] == "missing_viseme" for f in r["findings"]))

    def test_missing_arbitrary_viseme(self):
        with tempfile.TemporaryDirectory() as td:
            from tests.sakhalin.test_character_qa import _NO_REST_SVG
            r = review_character(**_ok(td, svg=_NO_REST_SVG))
            self.assertTrue(any(
                f["code"] == "missing_viseme" and "REST" in f["message"]
                for f in r["findings"]
            ))

    def test_duplicate_viseme(self):
        with tempfile.TemporaryDirectory() as td:
            from tests.sakhalin.test_character_qa import _DUPE_SVG
            r = review_character(**_ok(td, svg=_DUPE_SVG))
            self.assertTrue(any(f["code"] == "duplicate_viseme" for f in r["findings"]))


# ---------------------------------------------------------------------------
# Gaze checks
# ---------------------------------------------------------------------------

class TGazeChecks(unittest.TestCase):
    def test_required_gaze_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td))
            gaze_f = [f for f in r["findings"] if "gaze" in f["code"]]
            self.assertEqual(len(gaze_f), 0)

    def test_missing_gaze_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            from tests.sakhalin.test_character_qa import _NOGAZE_SVG
            r = review_character(**_ok(td, svg=_NOGAZE_SVG))
            self.assertTrue(any(f["code"] == "missing_gaze" for f in r["findings"]))


# ---------------------------------------------------------------------------
# Blink
# ---------------------------------------------------------------------------

class TBlinkCheck(unittest.TestCase):
    def test_blink_supported(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td))
            blink_f = [f for f in r["findings"] if "blink" in f["code"]]
            self.assertEqual(len(blink_f), 0)

    def test_missing_blink_warning(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td, actions={"idle": _action()}))
            self.assertTrue(any(f["code"] == "missing_blink_action" for f in r["findings"]))
            self.assertEqual(r["status"], "revise")

    def test_required_blink_missing_fails(self):
        with tempfile.TemporaryDirectory() as td:
            s = _spec()
            s["required_actions"] = ["idle", "blink"]
            r = review_character(**_ok(td, spec=s, actions={"idle": _action()}))
            self.assertTrue(any(f["code"] == "missing_required_blink" for f in r["findings"]))
            self.assertEqual(r["status"], "fail")

    def test_required_valid_blink_passes(self):
        with tempfile.TemporaryDirectory() as td:
            s = _spec()
            s["required_actions"] = ["idle", "blink"]
            r = review_character(**_ok(td, spec=s))
            blink_f = [f for f in r["findings"] if "blink" in f["code"]]
            self.assertEqual(len(blink_f), 0)
            self.assertEqual(r["status"], "pass")


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------

class TExpressionCheck(unittest.TestCase):
    def test_required_expression_passes(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td))
            expr_f = [f for f in r["findings"] if "expression" in f["code"]]
            self.assertEqual(len(expr_f), 0)

    def test_missing_expression_fails(self):
        with tempfile.TemporaryDirectory() as td:
            from tests.sakhalin.test_character_qa import _NOEXPR_SVG
            s = _spec()
            s["required_expressions"].append("nonexistent")
            r = review_character(**_ok(td, spec=s, svg=_NOEXPR_SVG))
            self.assertTrue(any(f["code"] == "missing_expression" for f in r["findings"]))


# ---------------------------------------------------------------------------
# Pose validation
# ---------------------------------------------------------------------------

class TPoseValidation(unittest.TestCase):
    def test_valid_poses(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td, poses={"idle": _pose(), "talk": _pose("talk")}))
            self.assertTrue(r["checks"]["poses_defined"])

    def test_invalid_pose(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td, poses={"idle": {"bad": 1}}))
            self.assertTrue(any(f["code"] == "invalid_pose" for f in r["findings"]))

    def test_pose_rig_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td, poses={"idle": _pose("idle", "sea_lion_cartoon")}))
            self.assertTrue(any(f["code"] == "pose_rig_mismatch" for f in r["findings"]))

    def test_pose_unknown_part(self):
        with tempfile.TemporaryDirectory() as td:
            p = _pose()
            p["state"]["parts"]["wing_left"] = {"rotation_deg": 0}
            r = review_character(**_ok(td, poses={"idle": p}))
            self.assertTrue(any(f["code"] == "pose_unknown_part" for f in r["findings"]))


# ---------------------------------------------------------------------------
# Action validation
# ---------------------------------------------------------------------------

class TActionValidation(unittest.TestCase):
    def test_valid_actions(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td))
            self.assertTrue(r["checks"]["actions_timed"])

    def test_invalid_action(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td, actions={"idle": {"bad": 1}}))
            self.assertTrue(any(f["code"] == "invalid_action" for f in r["findings"]))

    def test_missing_required_action(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td, actions={"blink": _action("blink")}))
            self.assertTrue(any(f["code"] == "missing_required_action" for f in r["findings"]))

    def test_action_rig_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td, actions={"idle": _action("idle", "sea_lion_cartoon"),
                                                     "blink": _action("blink")}))
            self.assertTrue(any(f["code"] == "action_rig_mismatch" for f in r["findings"]))

    def test_action_unresolved_pose(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td, actions={"idle": _action(poses=["nonexistent"]),
                                                     "blink": _action("blink")}))
            self.assertTrue(any(f["code"] == "action_unresolved_pose" for f in r["findings"]))


# ---------------------------------------------------------------------------
# Continuity
# ---------------------------------------------------------------------------

class TContinuityChecks(unittest.TestCase):
    def test_identity_lock_false(self):
        with tempfile.TemporaryDirectory() as td:
            s = _spec()
            s["continuity"]["identity_locked"] = False
            r = review_character(**_ok(td, spec=s))
            self.assertTrue(any(f["code"] == "continuity_violation" for f in r["findings"]))

    def test_base_regeneration_true(self):
        with tempfile.TemporaryDirectory() as td:
            s = _spec()
            s["visual"]["base_regeneration_allowed"] = True
            r = review_character(**_ok(td, spec=s))
            self.assertTrue(any(f["code"] == "continuity_violation" for f in r["findings"]))

    def test_wardrobe_lock_false(self):
        with tempfile.TemporaryDirectory() as td:
            s = _spec()
            s["visual"]["wardrobe_locked"] = False
            r = review_character(**_ok(td, spec=s))
            self.assertTrue(any(f["code"] == "continuity_violation" for f in r["findings"]))


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

class TDeterminism(unittest.TestCase):
    def test_result_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            kw = _ok(td)
            r1 = review_character(**kw)
            r2 = review_character(**copy.deepcopy(kw))
            self.assertEqual(r1, r2)

    def test_inputs_not_mutated(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            s = _spec()
            r = _rig()
            p = {"idle": _pose()}
            a = {"idle": _action(), "blink": _action("blink")}
            sc, rc, pc, ac = copy.deepcopy(s), copy.deepcopy(r), copy.deepcopy(p), copy.deepcopy(a)
            _write_svg(t, "f.svg", _FOX_SVG)
            review_character(spec=s, rig_profile=r, svg_path=t / "f.svg",
                             poses_by_id=p, actions_by_id=a,
                             canon_path=_canon_path(t))
            self.assertEqual(s, sc)
            self.assertEqual(r, rc)
            self.assertEqual(p, pc)
            self.assertEqual(a, ac)


# ---------------------------------------------------------------------------
# OpenMontage report
# ---------------------------------------------------------------------------

class TOpenMontageReport(unittest.TestCase):
    def test_report_structure(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td))
            rpt = to_openmontage_report(r)
            self.assertEqual(rpt["version"], "1.0")
            self.assertIn(rpt["status"], ["pass", "revise", "fail"])
            self.assertIn("schema_valid", rpt["checks"])
            self.assertFalse(rpt["checks"]["browser_preview_checked"])
            self.assertFalse(rpt["checks"]["frame_samples_checked"])
            self.assertFalse(rpt["checks"]["motion_detected"])


# ---------------------------------------------------------------------------
# Visual boundary
# ---------------------------------------------------------------------------

class TVisualBoundary(unittest.TestCase):
    def test_visual_not_falsely_verified(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td))
            self.assertEqual(r["metadata"]["visual_reference_status"], "not_verified")
            self.assertEqual(r["metadata"]["prop_visual_verification"], "not_verified")
            self.assertEqual(r["metadata"]["scale_check"], "not_verified")


# ---------------------------------------------------------------------------
# Findings ordering
# ---------------------------------------------------------------------------

class TFindingsOrder(unittest.TestCase):
    def test_findings_sorted(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td))
            sevs = [f["severity"] for f in r["findings"]]
            order = {"blocking": 0, "warning": 1, "info": 2}
            self.assertEqual(sevs, sorted(sevs, key=lambda s: order.get(s, 3)))


# ---------------------------------------------------------------------------
# SVG safety
# ---------------------------------------------------------------------------

class TSVGSafety(unittest.TestCase):
    def test_no_raw_manifest_in_errors(self):
        with tempfile.TemporaryDirectory() as td:
            r = review_character(**_ok(td))
            for f in r["findings"]:
                self.assertLess(len(f["message"]), 500)


if __name__ == "__main__":
    unittest.main()
