"""Tests for the SKIDS-013 Character Runtime Proof scene and outputs."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.character.sakhalin import character_runtime_proof as proof
from tools.character.sakhalin.character_runtime_proof import (
    AUDIO_WINDOWS_MS,
    COMPOSITION_ID,
    DURATION_MS,
    HEIGHT,
    PLACEMENT,
    WIDTH,
    build_proof,
    load_dialogue,
    load_scene_fixtures,
    merge_character,
)

_APPROVED_VISEMES = frozenset({
    "REST", "A", "E", "O", "U", "MBP", "FV", "SH", "L", "S",
})
_REMOTE_RE = ('href="http', 'src="http', "url(http", "<script")


def _phase_ranges(action: dict) -> list[tuple[str, int, int]]:
    """Return (pose, start_ms, end_ms) for every action phase."""
    out = []
    cursor = 0
    for phase in action.get("phases", []):
        start = cursor
        cursor += int(phase["duration_ms"])
        out.append((phase["pose"], start, cursor))
    return out


class TSceneFixtures(unittest.TestCase):
    """Offline fixture checks: dialogue, actions, visemes, lip-sync."""

    def test_dialogue_texts_exact(self) -> None:
        lines = load_dialogue()["lines"]
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0]["character_id"], "makar")
        self.assertEqual(lines[0]["text"], "Лёва, а почему море солёное?")
        self.assertEqual(lines[1]["character_id"], "leva")
        self.assertEqual(lines[1]["text"], "Хороший вопрос. Давайте разберёмся.")

    def test_action_durations_sum_to_scene(self) -> None:
        for character_id in ("makar", "leva"):
            action, _, _ = load_scene_fixtures(character_id)
            total = sum(int(p["duration_ms"]) for p in action["phases"])
            self.assertEqual(total, DURATION_MS, character_id)

    def test_required_beats_present(self) -> None:
        action, _, _ = load_scene_fixtures("makar")
        poses = [p["pose"] for p in action["phases"]]
        for beat in ("blink_closed", "look_right", "point", "talk"):
            self.assertIn(beat, poses, "makar")
        action, _, _ = load_scene_fixtures("leva")
        poses = [p["pose"] for p in action["phases"]]
        for beat in ("blink_closed", "look_left", "think", "talk"):
            self.assertIn(beat, poses, "leva")

    def test_viseme_timeline_contract(self) -> None:
        for character_id in ("makar", "leva"):
            _, visemes, _ = load_scene_fixtures(character_id)
            cues = visemes["cues"]
            self.assertEqual(cues[0]["start_ms"], 0, character_id)
            self.assertEqual(
                cues[-1]["end_ms"], visemes["duration_ms"], character_id,
            )
            for i, cue in enumerate(cues):
                self.assertIn(cue["viseme"], _APPROVED_VISEMES)
                self.assertLess(cue["start_ms"], cue["end_ms"])
                if i:
                    self.assertEqual(cue["start_ms"], cues[i - 1]["end_ms"])

    def test_speech_span_matches_audio_windows(self) -> None:
        for character_id in ("makar", "leva"):
            timeline, _ = merge_character(character_id)
            spoken = [s for s in timeline["segments"] if s["viseme"] != "REST"]
            self.assertTrue(spoken, character_id)
            span = (spoken[0]["start_ms"], spoken[-1]["end_ms"])
            self.assertEqual(span, AUDIO_WINDOWS_MS[character_id])

    def test_speech_within_talk_span(self) -> None:
        for character_id in ("makar", "leva"):
            action, _, _ = load_scene_fixtures(character_id)
            talk = [r for r in _phase_ranges(action) if r[0] == "talk"]
            self.assertTrue(talk, character_id)
            speech_start, speech_end = AUDIO_WINDOWS_MS[character_id]
            self.assertEqual(speech_start, talk[0][1], character_id)
            self.assertLessEqual(speech_end, talk[-1][2], character_id)

    def test_blink_never_during_speech(self) -> None:
        for character_id in ("makar", "leva"):
            action, _, _ = load_scene_fixtures(character_id)
            speech_start, speech_end = AUDIO_WINDOWS_MS[character_id]
            for pose, start, end in _phase_ranges(action):
                if pose == "blink_closed":
                    self.assertFalse(
                        start < speech_end and end > speech_start, character_id,
                    )

    def test_audio_windows_distinct_and_ordered(self) -> None:
        makar_start, makar_end = AUDIO_WINDOWS_MS["makar"]
        leva_start, leva_end = AUDIO_WINDOWS_MS["leva"]
        self.assertLess(makar_end, leva_start)
        self.assertLess(makar_start, makar_end)
        self.assertLess(leva_start, leva_end)
        self.assertNotEqual(proof._AUDIO_TONES["makar"], proof._AUDIO_TONES["leva"])

    def test_merged_timeline_deterministic(self) -> None:
        first, _ = merge_character("makar")
        second, _ = merge_character("makar")
        self.assertEqual(first, second)

    def test_library_character_assets_reused(self) -> None:
        for character_id, placement in PLACEMENT.items():
            asset = proof.LIBRARY_DIR / placement["asset_path"]
            self.assertTrue(asset.is_file(), character_id)
            self.assertIn(f"characters/{character_id}/", placement["asset_path"])


class TWorkspaceBuild(unittest.TestCase):
    """Build the proof workspace once and inspect the composition."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.manifest = build_proof(
            Path(cls._tmp.name), generate_audio=False,
        )
        comp_path = Path(cls.manifest["workspace"]["composition_path"])
        cls.composition = comp_path.read_text(encoding="utf-8")
        cls.index = (comp_path.parent.parent / "index.html").read_text(
            encoding="utf-8",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_manifest_shape(self) -> None:
        ws = self.manifest["workspace"]
        self.assertEqual(self.manifest["duration_ms"], DURATION_MS)
        self.assertEqual(ws["duration_s"], 12.0)
        self.assertEqual(ws["composition_id"], COMPOSITION_ID)
        self.assertGreater(ws["snapshot_count"], 0)

    def test_both_characters_in_composition(self) -> None:
        self.assertIn('data-character-instance="makar"', self.composition)
        self.assertIn('data-character-instance="leva"', self.composition)

    def test_rig_profiles_in_timelines(self) -> None:
        timelines = self.manifest["timelines"]
        self.assertEqual(timelines["makar"]["rig_profile"], "fox_cartoon")
        self.assertEqual(timelines["leva"]["rig_profile"], "sea_lion_cartoon")

    def test_frame_geometry(self) -> None:
        self.assertEqual(WIDTH, 1280)
        self.assertEqual(HEIGHT, 720)
        self.assertIn(f'data-width="{WIDTH}"', self.index)
        self.assertIn(f'data-height="{HEIGHT}"', self.index)

    def test_rotation_pivots_applied(self) -> None:
        self.assertIn("rotate(-45 336 290)", self.composition)
        self.assertIn("rotate(-3 250 270)", self.composition)
        self.assertIn("rotate(-4 250 262)", self.composition)
        self.assertNotIn('transform="rotate(-45)"', self.composition)

    def test_workspace_is_offline(self) -> None:
        for text in (self.composition, self.index):
            for marker in _REMOTE_RE:
                self.assertNotIn(marker, text)


class TFinalMedia(unittest.TestCase):
    """Probe the rendered MP4 when it has been produced (workspace output)."""

    MP4 = proof.REPO_ROOT / "workspace" / "skids-013" / "proof-with-audio.mp4"

    def test_mp4_probe(self) -> None:
        if shutil.which("ffprobe") is None or not self.MP4.is_file():
            self.skipTest("proof-with-audio.mp4 not rendered in this checkout")
        proc = subprocess.run(
            [
                "ffprobe", "-v", "error", "-print_format", "json",
                "-show_format", "-show_streams", str(self.MP4),
            ],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        streams = {s["codec_type"]: s for s in data["streams"]}
        self.assertIn("video", streams)
        self.assertIn("audio", streams)
        video = streams["video"]
        self.assertEqual(video["width"], WIDTH)
        self.assertEqual(video["height"], HEIGHT)
        self.assertEqual(video["r_frame_rate"], "30/1")
        self.assertEqual(streams["audio"]["codec_name"], "aac")
        duration = float(data["format"]["duration"])
        self.assertAlmostEqual(duration, DURATION_MS / 1000.0, delta=0.1)


if __name__ == "__main__":
    unittest.main()
