# Sakhalin Kids Studio — DeepSeek Harness Workflows

## Status

Companion document to `HARNESS_INTEGRATION.md`.

These workflows are approved as future integration targets and are deferred until the Character Runtime Proof and core production contracts are stable.

## First workflow: Research

Example topic:

```text
Почему на Сахалине бывают землетрясения?
```

Possible fan-out:

```text
Research Lead
   |
   +-- geology researcher
   +-- Sakhalin context researcher
   +-- child explanation reviewer
   +-- visual storytelling reviewer
   |
   v
fact check / synthesis
   |
   v
research_brief.json
```

Output should be structured rather than free-form narrative.

Example:

```json
{
  "topic": "sakhalin_earthquakes",
  "claims": [
    {
      "claim": "Example claim",
      "confidence": 0.92,
      "sources": ["source-ref"]
    }
  ],
  "kid_explanations": [],
  "visual_ideas": [],
  "uncertainties": []
}
```

## Second workflow: Script review

The primary script remains an OpenMontage production artifact.

Harness reviews it through focused roles:

```text
script
  |
  +-- child-language-review
  +-- character-consistency-review
  +-- education-review
  +-- visual-storytelling-review
  |
  v
script_review.json
```

Example finding:

```json
{
  "scene_id": "scene_04",
  "issues": [
    {
      "type": "lecture_language",
      "severity": "medium",
      "suggestion": "Turn the explanation into a question-and-discovery beat."
    }
  ]
}
```

Harness suggests.

The production pipeline or human editor decides how to apply the finding.

## Third workflow: Factual QA

Input:

- research brief;
- approved script;
- factual claims extracted from the script;
- final narration text where applicable.

Output:

```text
factual_qa.json
```

Each important educational claim should have:

- claim ID;
- support status;
- source references;
- uncertainty;
- contradiction notes;
- severity if unsupported.

Harness output must not silently replace source provenance.

## Fourth workflow: Production QA

Possible review areas:

- dialogue clarity;
- character behavior;
- visual continuity observations;
- educational pacing;
- mismatch between approved storyboard and final render;
- suspicious factual wording;
- age-appropriateness.

Example flow:

```text
final.mp4
 + script
 + storyboard
 + character manifests
 + research brief
       |
       v
DeepSeek Harness
       |
       +-- visual review
       +-- character review
       +-- factual review
       +-- child-content review
       |
       v
production_qa.json
```

LLM review is advisory evidence, not the sole release gate.

## Deterministic vs cognitive QA

Use deterministic checks for:

- file existence;
- schema validity;
- duration;
- codec;
- audio stream presence;
- frame dimensions;
- character asset IDs;
- budget;
- stage state;
- required approvals.

Use Harness for:

- semantic review;
- explanation quality;
- factual review assistance;
- narrative consistency;
- visual/storytelling observations.

Final release requires deterministic checks plus human approval where defined.

## Integration rule

All workflows return structured artifacts to the Sakhalin Kids/OpenMontage layer.

They do not directly:

- transition episode state;
- approve checkpoints;
- publish;
- mutate locked character assets;
- bypass budgets.

For security boundaries, schemas, state ownership, cost limits, and rollout policy, see `HARNESS_INTEGRATION.md`.
