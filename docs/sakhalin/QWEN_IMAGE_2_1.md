# Qwen-Image-2.1 R&D Boundary

## Status

Experimental, research/evaluation only.

This document defines how Sakhalin Kids Studio may evaluate Qwen-Image-2.1 without changing the active Milestone 01 production architecture.

## Why it is relevant

Qwen-Image-2.1 combines text-to-image generation and image editing in one model. The official release documents:

- a 7B visual generation component;
- up to 10 reference images;
- native transparent RGBA output;
- local editing using annotations or masks;
- identity preservation for people and products;
- Diffusers and ComfyUI support.

These capabilities make it a candidate for controlled character-conditioned image work, especially pose variants, expressions, transparent assets, storyboards and multi-character keyframes.

## Current project decision

Qwen-Image-2.1 is **not** part of the active Character Runtime Proof.

Milestone 01 remains:

- Makar;
- Leva;
- one location;
- 10–15 seconds;
- reusable local character assets;
- deterministic re-render;
- no paid AI video;
- no production ComfyUI orchestration.

The model may be evaluated only as an optional R&D backend until SKIDS-013 is complete and visually accepted.

## Architecture boundary

Qwen must remain below the Sakhalin Kids asset and storyboard boundaries.

```text
approved character masters
        |
        v
Qwen experimental adapter
        |
        v
candidate variants / keyframes
        |
        v
human approval + character QA
        |
        v
approved asset manifest
```

Qwen must never become the source of truth for persistent character identity.

## Allowed uses

Research evaluation may generate:

- pose variants;
- expression variants;
- camera-angle variants;
- transparent character assets;
- multi-character compositions;
- interaction keyframes;
- storyboard frames;
- scene-specific visual experiments.

## Forbidden uses

Do not use Qwen to:

- redesign a core character;
- silently replace approved master art;
- change species;
- change locked palette;
- change signature clothing without approval;
- introduce permanent accessories without approval;
- bypass character QA;
- make production state transitions;
- publish directly.

## Character master contract

Every core character should eventually have an approved master set:

```text
library/characters/<id>/
  master/
    front.png
    three-quarter.png
    side.png
    back.png
    neutral.png
  expressions/
  poses/
  qwen/
    approved/
    rejected/
    tests/
```

Only manually approved images may enter `master/`.

Generated candidates remain outside the master set until explicitly approved.

## Reference strategy

For a single-character edit, prefer:

1. front or three-quarter master;
2. alternate approved angle;
3. approved expression or pose reference when needed.

For a multi-character shot, provide one or more approved references per character, plus an optional location/style reference, while staying within the model's documented 10-reference limit.

## Prompt assembly

Prompts should be assembled from explicit blocks rather than one free-form paragraph.

Recommended blocks:

1. identity lock;
2. character contract;
3. shot/action;
4. style;
5. forbidden changes.

Example identity lock:

```text
Preserve the exact identity, proportions, facial structure,
color pattern, clothing design and approved accessories
from the supplied character references.

Do not redesign the character.
```

## Benchmark before adoption

The first evaluation is a controlled Character Consistency Benchmark.

Each core character receives 10 tests:

1. front neutral;
2. three-quarter view;
3. side view;
4. happy;
5. surprised;
6. thinking;
7. walking;
8. running;
9. holding a character-specific object;
10. two-character interaction.

Five core characters produce 50 evaluation outputs.

A separate team-composition test should place all five approved characters in one scene and check:

- species correctness;
- identity stability;
- relative scale;
- palette;
- wardrobe;
- no merged characters;
- no duplicates;
- no extra limbs.

## Scoring

Suggested weighted score:

- identity: 30;
- proportions: 15;
- face: 15;
- palette: 10;
- clothing: 10;
- accessories: 5;
- style continuity: 10;
- anatomy: 5.

Thresholds:

- 90–100: PASS;
- 80–89: MANUAL REVIEW;
- below 80: REJECT.

Hard-failure conditions override the numeric score:

- wrong species;
- wrong core palette;
- wrong signature clothing;
- extra limbs;
- missing identity feature;
- obvious identity drift.

## Runtime adoption gate

Do not add Qwen tools to `pipeline_defs/sakhalin-kids.yaml` until all of these are true:

1. SKIDS-013 has passed and the Character Runtime Proof is visually accepted.
2. The 50-image benchmark has been reviewed.
3. The five-character composition test is acceptable.
4. Commercial licensing has been resolved for the intended use.
5. A narrow adapter contract is defined.
6. Provider/model outputs are schema validated and treated as untrusted data.
7. Budget, retry and provenance rules are implemented.
8. The fallback path remains the existing reusable character runtime.

## Licensing

The repository is published under the Qwen Research License Agreement.

The license grants non-commercial use for research or evaluation and requires a separate commercial license for commercial use.

Therefore:

- internal R&D/evaluation: allowed under the published research license;
- production commercial use: blocked until a separate commercial license is obtained and reviewed.

Commercial-license requests are directed by the license to:

`model-business@notice.qwencloud.com`

## Security and operations

If a runtime adapter is later implemented:

- never execute model output as code or shell;
- constrain filesystem output paths;
- validate response schemas;
- bound retries and cost;
- record model version, seed, references and output hash;
- store provenance;
- never let generated text authorize approval or publication.

## Decision

Qwen-Image-2.1 is accepted as a **candidate experimental visual backend**, not a production dependency.

The next valid action is benchmark preparation and local evaluation after or alongside completion of the Character Runtime Proof, without altering Milestone 01 scope.
