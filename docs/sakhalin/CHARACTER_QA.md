# Sakhalin Kids — Character QA

## Scope

SKIDS-010 provides structural Character QA for the persistent cast.

Identity source of truth remains `TEAM_CANON.md`. The machine-readable policy
in `config/sakhalin/character_qa_policy.json` mirrors only the fields needed by
the QA service and must be updated whenever the canon changes.

## Blocking checks

- known character ID;
- species/type matches canon;
- current proof rig matches canon where implemented;
- loaded RigProfile matches CharacterSpec;
- QA evidence belongs to the same character;
- palette/proportion/wardrobe locks remain enabled;
- base regeneration remains disabled;
- continuity identity lock remains enabled;
- redesign still requires approval;
- all RigProfile required parts exist;
- all CharacterSpec required actions exist;
- all CharacterSpec required props exist;
- complete semantic viseme set exists when the rig supports mouth visemes;
- explicit reference comparisons fail closed when they report a mismatch.

## Reference checks

Exact palette values, proportions, wardrobe comparison, scale bounds, and visual
identity similarity are not yet encoded in CharacterSpec. SKIDS-010 therefore
does not invent numeric thresholds.

The fixture/asset stages supply explicit evidence:

```text
palette_matches
proportions_match
wardrobe_matches
scale_within_range
identity_matches
```

A supplied `false` is blocking. A missing/unknown value produces a warning,
so the report never silently claims that an unavailable comparison passed.

SKIDS-011 and SKIDS-012 should provide approved reference evidence for Makar
and Leva before SKIDS-013 final proof acceptance.

## Report contract

The reviewer returns:

```json
{
  "version": "1.0",
  "character_id": "makar",
  "status": "pass",
  "blocking_count": 0,
  "warning_count": 0,
  "checks": [],
  "findings": []
}
```

Milestone 01 acceptance requires zero blocking findings.
