# Sakhalin Kids — HyperFrames Runtime Handoff

SKIDS-009: Deterministic handoff from SvgSceneRenderer to HyperFrames workspace.

## Purpose

Generate a self-contained, offline HyperFrames workspace from merged character timelines. One SVG snapshot per unique state interval — no JavaScript animation, no CDN, no remote URLs.

## Architecture

```
TimelineMerger
    ↓
SvgSceneRenderer(timestamp_ms)
    ↓
deterministic SVG interval snapshots
    ↓
HyperFrames authored workspace
    ↓
OpenMontage hyperframes_compose.render_existing
```

## Public API

```python
def build_hyperframes_workspace(
    asset_root: Path,
    output_dir: Path,
    width: int,
    height: int,
    characters: list[dict],
    composition_id: str = "sakhalin-scene",
) -> dict:
```

Returns a manifest dict with workspace metadata.

### Parameters

- `asset_root` — directory containing SVG character assets
- `output_dir` — target workspace directory (created if missing)
- `width`, `height` — output dimensions
- `characters` — list of character dicts (same format as `SvgSceneRenderer.render_frame`)
- `composition_id` — unique composition identifier

### Return value

```python
{
    "workspace_path": str,
    "composition_path": str,
    "duration_s": float,
    "duration_ms": int,
    "snapshot_count": int,
    "interval_count": int,
    "composition_id": str,
}
```

## Workspace structure

```
output_dir/
├── index.html                    # HyperFrames entry point
├── styles.css                    # offline CSS (no CDN)
├── hyperframes.json              # workspace manifest (no remote registry)
├── DESIGN.md                     # human-readable design notes
├── compositions/
│   └── {composition_id}.html     # template with inline SVG snapshots
└── assets/                       # static assets directory
```

## Timeline boundary union

For multiple characters:

1. Collect all segment boundaries from all character timelines
2. Verify all characters have the same `duration_ms` (fail closed on mismatch)
3. Sort unique boundaries → non-overlapping intervals
4. Render one SVG frame at `timestamp_ms=start` for each interval
5. Embed each SVG inline in the composition HTML

## Constraints

- Deterministic: same inputs → identical workspace
- Offline/self-contained: no CDN, no remote URLs
- No custom animation JS: SVG snapshots only
- Compatible with pinned OpenMontage `render_existing` flow
- All authored files ≤400 lines

## Invariants

- No gaps between intervals
- No overlapping intervals
- Final interval ends at `duration_ms`
- First interval starts at 0
- `sum(interval_durations) == duration_s`
- Input dicts not mutated
- Asset paths contained within `asset_root`
- No `<script>`, `<foreignObject>`, event handlers, or external hrefs

## Tests

23 tests in `tests/sakhalin/test_hyperframes_handoff.py` covering:

- Global boundary union (single/multi character, duration mismatch, empty, invalid)
- Interval generation (no gaps, no overlaps, final equals duration)
- Milliseconds → seconds conversion
- Deterministic output
- Input immutability
- Path safety (nonexistent root, no external URLs in HTML)
- Workspace structure (files created, valid hyperframes.json, snapshot count)
- SvgSceneRenderer integration (SVG data attributes in composition, two characters)
