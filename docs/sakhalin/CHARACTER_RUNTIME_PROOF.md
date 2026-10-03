# Sakhalin Kids — Character Runtime Proof (SKIDS-013)

Milestone 01 deliverable: a 12-second, 1280x720, 30fps MP4 with Makar and
Leva in one seashore scene — Russian dialogue, viseme lip-sync, acting beats,
owned background, and muxed fallback audio. Built entirely from local assets;
no paid providers, no AI video, no CDN.

## Scene

- Composition: `makar-leva-seashore-proof`, 12000 ms, 74 snapshot intervals
  (one per unique merged acting/viseme state boundary).
- Makar (`fox_cartoon`) at x=140, y=105; Leva (`sea_lion_cartoon`) at
  x=740, y=105; background `locations/seashore_proof.svg`.
- Fixtures: `library/scenes/makar_leva_seashore_proof/` (dialogue, actions,
  visemes) merged with `library/characters/{makar,leva}/poses/` via
  TimelineMerger.
- Speech/audio windows: makar 1700–4080 ms, leva 6300–9250 ms (distinct,
  non-overlapping; blink phases never intersect speech).

## Build and render

```text
python -m tools.character.sakhalin.character_runtime_proof
npx hyperframes lint
npx hyperframes validate
npx hyperframes render -o proof.mp4
ffmpeg -i workspace/skids-013/workspace/proof.mp4 -i workspace/skids-013/dialogue.wav -c:v copy -c:a aac -b:a 192k -shortest workspace/skids-013/proof-with-audio.mp4
```

Outputs live under `workspace/skids-013/` (gitignored): `workspace/`,
`dialogue.wav`, `proof-with-audio.mp4`.

## Render pipeline notes

- Snapshot SVGs are embedded inline; `hyperframes_handoff.py` normalizes
  namespace-prefixed tags for the HTML parser (`_svg_for_html`).
- SvgSceneRenderer emits bare `rotate(angle)` (origin-relative). Pivots are
  applied at the embedding boundary by `rotation_pivot.py` using
  `ROTATION_PIVOTS` in `character_runtime_proof.py` (makar head 250,270;
  makar arm_right 336,290; leva head 250,262). The renderer, fixtures, and
  CharacterReviewer are unchanged.

## Known limitations (accepted for Milestone 01 review)

- Audio is deterministic FFmpeg tones (LIPSYNC.md section 17); natural
  Russian TTS quality is NOT validated — Milestone 02 scope.
- Head tilts (−2…−4°) are subtle: eyes, mouth, and brows are separate
  top-level art layers and do not follow the head motion-root rotation.
- The point gesture uses the approved fixture value arm_right=−45°
  (diagonal outward), not a horizontal arm.

## Verification performed (SKIDS-013)

- Unit/contract tests: `test_character_runtime_proof` (17),
  `test_rotation_pivot` (8), `test_hyperframes_handoff` (29) — all pass.
- `hyperframes lint`: 0 errors, 2 warnings (file size / track density).
- `hyperframes validate`: no console errors.
- `hyperframes render`: 199.5 KB MP4, 12.0 s, 360 frames, screenshot capture.
- Frame samples at 1.04 / 2.5 / 3.6 / 5.8 / 7.5 s: blink, point, talk,
  gaze, think all readable; both characters fully in frame.
- `ffprobe` on `proof-with-audio.mp4`: h264 1280x720 30/1, 360 frames,
  aac 44.1 kHz mono, 12.000 s, 292615 bytes; audio non-silent
  (mean −36.3 dB).
- Determinism: workspace rebuild produced an identical composition SHA-256.

## Stop condition

After SKIDS-013, stop implementation and evaluate this proof visually before
expanding scope (plan.md).
