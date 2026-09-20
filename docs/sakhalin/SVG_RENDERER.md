# Sakhalin Kids — SVG Scene Renderer

SKIDS-008: Deterministic, frame-oriented SVG scene renderer for character animation.

## Purpose

Render a single SVG frame from a composed scene description. No animation runtime, no video output, no HyperFrames/Remotion.

## Public API

```python
def render_frame(
    asset_root: Path,
    width: int,
    height: int,
    timestamp_ms: int,
    characters: list[dict],
) -> str:
```

Returns an SVG string. Raises `SvgRenderError` on validation failure.

### Parameters

- `asset_root` — directory containing SVG character assets
- `width`, `height` — viewport dimensions
- `timestamp_ms` — current time (0 <= ts < duration_ms)
- `characters` — list of character dicts (see below)

### Character dict shape

```python
{
    "instance_id": str,          # unique within scene
    "asset_path": str,           # relative path under asset_root
    "x": int | float,            # placement position
    "y": int | float,
    "scale": float,              # optional, default 1.0, must be > 0
    "timeline": merged_timeline, # output of TimelineMerger
    "poses_by_id": {pose_id: pose_dict},
}
```

## Validation

- Asset paths are resolved under `asset_root` (no traversal, no absolute paths)
- Only `.svg` files accepted
- Max 2 MiB per SVG
- Rejects `<script>`, `<foreignObject>`, event handlers, external `href`
- Rig profile must match between SVG `data-rig-profile` and timeline
- Timestamp must be in range `[0, duration_ms)`

## SVG data attributes

| Attribute | Purpose |
|---|---|
| `data-rig-profile` | rig profile ID on `<svg>` root |
| `data-part` | body part identifier |
| `data-motion-root` | element to receive rotation transform |
| `data-variant` | variant group member |
| `data-default-variant` | default variant to activate |
| `data-expression` | expression layer identifier |
| `data-gaze` | gaze direction layer |
| `data-viseme` | viseme layer within mouth part |

## Output contract

- Single `<svg>` root element
- `viewBox` set to `0 0 {width} {height}`
- Each character wrapped in `<g data-character-instance="{id}">` with translate/scale
- Original SVG elements not mutated (deep copy)
- Deterministic: same inputs produce identical output

## Tests

33 tests in `tests/sakhalin/test_svg_scene_renderer.py` covering:

- Single/two character composition
- Deterministic output
- Timestamp boundary (start, boundary, negative, overflow)
- Pose resolution (missing pose, key mismatch, rig mismatch)
- SVG rig mismatch detection
- Motion root rotation
- Variant activation and default variants
- Expression layer activation and rejection
- Gaze direction activation and rejection
- Viseme layer activation (all 10 approved visemes)
- Placement and z-order
- Path safety (traversal, absolute, non-SVG, script injection, event handlers, href injection)
- Immutability (input dicts not mutated)
