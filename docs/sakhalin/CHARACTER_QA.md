# Character QA (SKIDS-010)

Deterministic structural quality assurance for character bundles.

## Purpose

`CharacterReviewer` validates that character bundles satisfy Sakhalin Kids
Studio structural requirements before entering the Character Runtime Proof.
No AI, no computer vision, no artistic approval claims.

## Public API

```python
from tools.character.sakhalin.character_qa import (
    CharacterQAError,
    load_team_canon,
    review_character,
    to_openmontage_report,
)
```

### `review_character(...)`

```python
result = review_character(
    spec=character_spec_dict,
    rig_profile=rig_profile_dict,
    svg_path=Path("library/characters/makar.svg"),
    poses_by_id={"idle": pose_dict, ...},
    actions_by_id={"idle": action_dict, "blink": action_dict, ...},
    canon_path=Path("config/sakhalin/team_canon.json"),
)
```

Returns a result dict:

```json
{
  "status": "pass" | "revise" | "fail",
  "findings": [...],
  "checks": {...},
  "metadata": {...}
}
```

### `to_openmontage_report(result)`

Converts to pinned OpenMontage `character_qa_report` shape.

### `load_team_canon(path)`

Loads machine-readable team canon from JSON.

## Status semantics

| Status    | Meaning                                      |
|-----------|----------------------------------------------|
| `pass`    | No blocking findings, no warnings            |
| `revise`  | Warnings only (no blocking)                  |
| `fail`    | At least one blocking finding                |

## Finding severity

| Severity  | Meaning                                        |
|-----------|------------------------------------------------|
| `blocking`| Must fix before character enters production    |
| `warning` | Should fix; may proceed with caution           |
| `info`    | Informational only                             |

## Checks performed

1. **Schema validation** — spec and rig_profile against JSON Schema
2. **Team canon** — character ID, species, rig_profile match canon
3. **Continuity locks** — identity_locked, palette_locked, etc.
4. **SVG structure** — required parts, security (no scripts, no event handlers)
5. **Visemes** — all 10 approved visemes present, no duplicates, no unknown
6. **Gaze** — all 5 required gaze directions present
7. **Expressions** — required expressions present in SVG
8. **Blink** — blink semantics depend on `required_actions`:
   - capability=true + "blink" in required_actions + missing → **blocking** (fail)
   - capability=true + "blink" NOT in required_actions + missing → **warning** (revise)
   - capability=true + blink action present but invalid → **blocking** (fail)
9. **Pose validation** — schema, rig match, no unknown parts
10. **Action validation** — schema, rig match, all phases resolve to known poses
11. **Determinism** — results are deterministic, inputs not mutated

## Team canon

Machine-readable canon at `config/sakhalin/team_canon.json`:

```json
{
  "version": "1.0",
  "characters": {
    "makar": {"species": "fox", "rig_profile": "fox_cartoon"},
    "leva": {"species": "sea_lion", "rig_profile": "sea_lion_cartoon"},
    "tikhon": {"species": "bear", "rig_profile": null},
    "anna": {"species": "seal", "rig_profile": null},
    "antoshka": {"species": "human", "rig_profile": null}
  }
}
```

antoshka is a **human boy**. Any identity mismatch (seagull, sable, etc.) is blocking.

## OpenMontage report

`to_openmontage_report()` sets:

- `browser_preview_checked = false`
- `frame_samples_checked = false`
- `motion_detected = false`

These are never set to true without explicit evidence.

## Files

- `tools/character/sakhalin/character_qa.py` — implementation
- `tests/sakhalin/test_character_qa.py` — 48 tests
- `config/sakhalin/team_canon.json` — machine-readable canon
- `docs/sakhalin/CHARACTER_QA.md` — this file
