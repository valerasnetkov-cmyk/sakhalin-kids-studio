# Sakhalin Kids — Team Canon

## 1. Status

This document is the canonical identity reference for the persistent cast of
«Исследуем Сахалин вместе».

Character IDs are stable. Visual identity, species/type, role, and signature
details must not be silently reinterpreted by code, prompts, fixtures, or
generation workflows.

The persistent cast is closed:

```text
makar
leva
tikhon
anna
antoshka
```

`sima` is excluded from the team and must not be used unless explicitly
restored by a separate project decision.

## 2. Canonical cast

| character_id | Name | Species / type | Narrative role | Rig notes |
|---|---|---|---|---|
| `makar` | Макар | fox cub | active researcher, initiator of discoveries | `fox_cartoon`; tail, ears, arms, expressive face, mouth visemes |
| `leva` | Лёва | sea lion | calm reasoning partner, sea and coast topics | `sea_lion_cartoon`; flippers, head, gaze, expressive face, mouth visemes |
| `tikhon` | Тихон | bear cub | reliable expedition partner, forest and safety | future `bear_cartoon`; arms, head, gaze, binocular/expedition poses |
| `anna` | Анна | seal | sea, ecology, observation, emotional warmth | future `seal_cartoon`; head, gaze, expression layers, flipper gestures |
| `antoshka` | Антошка | human boy, about 8–9 by character design | traveler, storyteller, young guide through Sakhalin | future `human_child_cartoon`; arms, legs, hands, face, props, mouth visemes |

## 3. Antoshka canonical correction

`antoshka` is a small human boy.

He is **not**:

- a seagull;
- a sable;
- an animal mascot.

Canonical role:

```text
traveler + storyteller + young Sakhalin researcher
```

Canonical visual markers:

- cap with patch;
- blue expedition jacket;
- warm yellow neck accent/scarf;
- travel backpack;
- camera;
- Sakhalin map;
- compass;
- notebook.

Typical actions:

- studies a map;
- takes photos;
- looks at the horizon;
- tells a story;
- writes notes;
- talks with local residents;
- points out a route or discovery.

Any old documentation that describes Antoshka as `seagull` or uses
`seagull_cartoon` for him is stale and must be corrected.

## 4. Character identity summary

### Makar

- ID: `makar`
- Type: fox cub
- Role: active researcher
- Story function: asks questions, proposes experiments, notices discoveries
- Signature details: orange fur, expedition clothing, backpack/notebook
- Motion emphasis: head, gaze, ears, tail, pointing, talking

### Leva

- ID: `leva`
- Type: sea lion
- Role: calm reasoning partner
- Story function: explains, observes, balances Makar's energy
- Signature details: marine visual language, scarf/accessory set
- Motion emphasis: head, gaze, flippers, thinking, talking

### Tikhon

- ID: `tikhon`
- Type: bear cub
- Role: reliable expedition partner
- Story function: forest, safety, practical support
- Signature details: expedition vest/equipment, binoculars or useful gear
- Motion emphasis: head, arms, binocular poses, helping gestures

### Anna

- ID: `anna`
- Type: seal
- Role: nature and sea observer
- Story function: ecology, marine world, emotional warmth
- Signature details: light coat, blue neck accessory, marine accents
- Motion emphasis: gaze, head tilt, expressions, simple flipper gestures

### Antoshka

- ID: `antoshka`
- Type: human boy
- Role: traveler and storyteller
- Story function: route guide, history collector, audience-facing explorer
- Signature details: cap, blue jacket, backpack, camera, map, compass, notebook
- Motion emphasis: full human upper-body gestures, hands with props, talking

## 5. Visual language

The approved direction is a detailed, friendly, 3D-stylized children's
adventure look.

Required qualities:

- warm, readable faces;
- strong silhouettes;
- rich clothing and prop detail;
- tactile fur/fabric/material feel;
- Sakhalin expedition context;
- consistent proportions across views;
- recognizable identity across poses and expressions.

Do not silently simplify approved characters into generic flat mascots merely
because flat vector art is easier to animate.

Technical proof assets may be simpler than final production art, but must be
clearly identified as proof fixtures and must not redefine the character canon.

## 6. Renderer / asset implications

The current SKIDS-008 renderer expects structured SVG hooks such as:

```text
data-rig-profile
data-part
data-motion-root
data-variant
data-expression
data-gaze
data-viseme
```

A single traced illustration flattened into one SVG group is not sufficient for
the reusable character runtime.

Characters must be decomposed into independently controllable parts.

Minimum reusable rig concepts:

```text
head
eyes
pupils / gaze
expression layers
mouth visemes
body
gesture limbs
signature props
```

Human Antoshka additionally requires:

```text
arm_left
arm_right
hand_left
hand_right
leg_left
leg_right
```

as appropriate to the final rig design.

## 7. Detailed-art asset decision

The current SVG renderer is suitable for structured vector assets.

The approved visual direction is more detailed than a typical flat SVG mascot,
so before production-quality fixture authoring the project must explicitly
confirm one of these asset strategies:

1. fully structured vector SVG;
2. structured SVG rig with approved local raster detail layers;
3. another deterministic local layered format with an adapter to the existing
   renderer contract.

Current SKIDS-008 safety rules reject arbitrary external SVG references.
Therefore local PNG/WebP layer support must not be assumed to exist.

Do not weaken SVG safety or add external resource loading implicitly.

If raster-backed layers are adopted, they require a separate bounded local
asset-path contract and tests.

## 8. SKIDS-010 priorities — Character QA

Character QA should treat this document as identity source of truth.

Minimum checks:

- character ID is known;
- species/type matches canon;
- rig profile is compatible with the character;
- required parts exist;
- required viseme set exists;
- palette and proportions match approved references;
- signature clothing/props are preserved;
- scale is within approved range;
- expected actions/poses exist;
- no silent character redesign occurred.

Specific Antoshka guard:

```text
antoshka -> human boy
```

A seagull, sable, or generic animal representation for `antoshka` must be a
blocking identity failure unless a later explicit canon change exists.

## 9. SKIDS-011 priorities — Makar fixture

SKIDS-011 remains limited to Makar.

Required proof scope:

- `fox_cartoon` compatibility;
- stable front/working view sufficient for the proof;
- structured head/eyes/gaze;
- blink;
- readable point/gesture;
- talk pose;
- all semantic mouth visemes;
- deterministic reuse of the same base art;
- reference frame(s) for QA.

Do not use SKIDS-011 to implement all five characters.

Do not redesign Makar to accommodate renderer shortcuts.

## 10. SKIDS-012 priorities — Leva fixture

SKIDS-012 remains limited to Leva.

Required proof scope:

- `sea_lion_cartoon` compatibility;
- stable front/working view sufficient for the proof;
- structured head/eyes/gaze;
- blink;
- readable think/gesture;
- talk pose;
- all semantic mouth visemes;
- deterministic reuse of the same base art;
- reference frame(s) for QA.

Makar and Leva must remain visually distinct and use different rig profiles.

## 11. Post-proof characters

Tikhon, Anna, and Antoshka are canonical core characters, but their production
rigs are not part of the current Makar + Leva Character Runtime Proof.

Do not implement their complete production rigs before SKIDS-013 visual review
unless the project scope is explicitly changed.

Future candidate profiles:

```text
tikhon   -> bear_cartoon
anna     -> seal_cartoon
antoshka -> human_child_cartoon
```

These profile names are architectural candidates, not implemented RigProfile
contracts yet.

## 12. Machine-readable canon

The canonical identity data is also available as machine-readable JSON:

```text
config/sakhalin/team_canon.json
```

This file is the source of truth for `CharacterReviewer` (SKIDS-010) and any
code that needs to validate character identity programmatically.

Load it with:

```python
from tools.character.sakhalin.character_qa import load_team_canon
canon = load_team_canon()
```

The JSON structure:

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

`rig_profile: null` means the character does not yet have an implemented
production rig profile.

Do not edit this file without also updating this document and running the
character QA test suite.

## 13. Change control

Changing any of the following is a canon change and requires explicit approval:

- character ID;
- species/type;
- core narrative role;
- signature visual identity;
- signature clothing/props;
- replacement of the base approved character design.

Runtime implementation details may evolve without changing canon, provided
character identity and approved visual references remain intact.


## Narrative character profiles

Detailed narrative/behavior canon for each core character is stored in:

```text
docs/sakhalin/characters/
  makar.md
  leva.md
  tikhon.md
  anna.md
  antoshka.md
```

These profiles are the project source of truth for personality, thinking pattern,
team relationships, recurring phrases, strengths/weaknesses, and story function.

Identity/type conflicts still resolve through this document plus
`config/sakhalin/team_canon.json`; do not silently reinterpret a character.

Sima remains excluded from the persistent cast.
