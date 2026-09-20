# Sakhalin Kids — Timeline Merge

## 1. Purpose

SKIDS-007 implements the deterministic merger of:

- Action (timed pose sequence)
- Resolved Pose references
- VisemeTimeline (mouth viseme sequence)

into one renderer-ready character timeline.

Service:

```text
tools/character/sakhalin/timeline_merger.py
```

## 2. Inputs

```python
merge_action_and_visemes(
    action,        # validated Sakhalin Action object
    poses_by_id,   # mapping: pose_id -> validated Pose object
    viseme_timeline,  # validated Sakhalin VisemeTimeline object
)
```

## 3. Semantic Validation

Before merge, the service validates:

- Action against action.schema.json
- Every referenced Pose against pose.schema.json
- VisemeTimeline against viseme_timeline.schema.json
- Every Action phase.pose exists in poses_by_id
- Pose mapping key matches Pose.id
- Action.rig_profile matches every referenced Pose.rig_profile
- Viseme cues are sorted by start_ms
- No overlapping cues
- No gaps between cues
- First cue starts at 0
- Final cue ends at duration_ms
- start_ms < end_ms for every cue

## 4. Duration Policy

VisemeTimeline.duration_ms is authoritative.

- Action duration == Viseme duration: normal merge
- Action duration < Viseme duration: hold final Action pose
- Action duration > Viseme duration: FAIL CLOSED

No time-stretching, rescaling, looping, or silent truncation.

## 5. Merge Algorithm

1. Convert Action phases to absolute ranges [(start, end, pose_id), ...]
2. If action is shorter, append hold range for final pose
3. Collect all boundary points from acting ranges + viseme cues
4. For each resulting interval, determine active pose + active viseme
5. Return deterministic segment list

## 6. Output Contract

```json
{
  "version": "1.0",
  "rig_profile": "fox_cartoon",
  "duration_ms": 1200,
  "segments": [
    {"start_ms": 0, "end_ms": 100, "pose": "talk_open", "viseme": "REST"}
  ]
}
```

No character_id, scene_id, audio_path, provider, renderer, fps, or asset paths.

## 7. Ownership Boundary

- Pose/Action own body/head/gaze/expression/gesture
- VisemeTimeline owns mouth only
- Merged segments reference pose + viseme separately
- No mixed mutable state is created

## 8. Determinism

Given identical inputs, output is identical. No current time, randomness, input mutation, or dict ordering dependence.

## 9. Exclusions

- No renderer, SVG, GSAP, Remotion
- No TTS, phonemizer, aligner, WhisperX
- No provider calls
- No interpolation or easing
- No multi-character or episode timeline
- No OpenMontage adapter/compiler
