# SKIDS-013 Character Runtime Proof

## Target

A deterministic 12-second local proof with Makar and Leva.

The proof includes two different rig profiles, Russian fixture dialogue, local
SVG character rendering, viseme-driven mouths, a deterministic Sakhalin-style
background, H.264/AAC MP4 output, opening/middle/end PNG samples, ffprobe JSON,
Character QA reports and SHA-256 hashes of the two source character assets.

Dialogue:

Макар: «Лёва, а почему море солёное?»
Лёва: «Хороший вопрос. Давайте разберёмся.»

## Run

From repository root:

    python scripts/render-skids-013.py

Required local executables:

    ffmpeg
    ffprobe
    espeak or espeak-ng

On macOS, the system say command is accepted as a local speech fallback when
eSpeak is absent.

No cloud provider or paid AI-video call is used.

## Output

Generated files are written only under build/skids-013/.

Expected outputs:

    skids-013-runtime-proof.mp4
    render_report.json
    audio/
    frames/
    samples/opening.png
    samples/middle.png
    samples/end.png

Generated build media should not be committed unless intentionally selected as
a small regression fixture.

## Visual status

Makar and Leva assets in SKIDS-011/012 are technical proof fixtures. They prove
runtime structure and deterministic reuse but do not replace final approved
production art.

Character QA must have zero blocking findings. Missing production visual
reference comparisons may remain warnings until approved model sheets and
reference frames are attached.
