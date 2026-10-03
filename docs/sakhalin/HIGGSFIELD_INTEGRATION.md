# Higgsfield Integration

## Status

Approved future provider integration. Documentation-only in this change.

Implementation starts only after the Character Runtime proof `SKIDS-013` is visually accepted.

## Objective

Use Higgsfield as a bounded external visual-generation provider for scenes where generative video adds clear value, without changing ownership of production state or core-character identity.

Higgsfield is not the production orchestrator.

## Responsibility split

```text
OpenCode
  development

OpenMontage
  production workflow, checkpoints, artifacts, cost tracking

Sakhalin Kids
  scene routing, character continuity, editorial/QA contracts

Local Character Runtime
  core-character dialogue, acting, gaze, gestures, visemes, lip-sync

Higgsfield adapter
  storyboard experiments, AI cinematic inserts,
  historical/fantasy reconstruction, selected derivatives
```

## Non-goals

Do not use Higgsfield to:

- regenerate or replace locked core characters;
- own episode state;
- approve checkpoints;
- publish directly;
- bypass budget policy;
- silently replace real Sakhalin footage;
- become a second character runtime;
- become a second lip-sync system.

## Scene routing

Default routing remains unchanged.

| Scene type | Default path | Higgsfield role |
|---|---|---|
| character_dialogue | local Character Runtime | prohibited by default |
| character_action | local Character Runtime | prohibited by default |
| real_footage | owned media library | no replacement |
| location_establishing | owned media, then approved fallback | optional fallback |
| educational_graphic | HyperFrames/Remotion | optional concept reference only |
| map | HyperFrames/Remotion | no default role |
| ai_cinematic | OpenMontage video selector | eligible provider |
| historical_reconstruction | approved image/video selector | eligible provider |
| fantasy_imagination | image/video selector | eligible provider |
| transition | local composition runtime | optional only when approved |

Provider choice belongs to OpenMontage/Sakhalin routing and provider policy, not screenplay data.

## Character continuity boundary

Core characters remain immutable production assets.

Higgsfield may receive approved character reference renders only when a pilot explicitly tests a cinematic insert that contains a core character.

Even in that case:

- local character assets remain canonical;
- generated footage is non-canonical derivative output;
- generation must not update `library/characters/*`;
- generated appearance drift is a blocking QA issue;
- no generated frame becomes a new reference frame without explicit approval;
- local Character Runtime remains the default for recurring acting and dialogue.

## Provider adapter contract

Target future boundary:

```text
integrations/
  higgsfield/
    client.py
    contracts.py
    adapter.py
    validators.py
    cost.py
```

Exact paths may change to match the pinned OpenMontage provider conventions at implementation time.

The adapter receives schema-validated inputs only.

Candidate request envelope:

```yaml
job_id: video_job_001
episode_id: EP-001
scene_id: SC-007
scene_type: ai_cinematic

provider:
  id: higgsfield
  model: null

input:
  prompt: "..."
  aspect_ratio: "16:9"
  duration_seconds: 8
  references:
    - asset_id: "location_aniva_v3"
      role: location
    - asset_id: "makar_ref_three_quarter_v2"
      role: character_reference

policy:
  allow_core_character_generation: false
  max_attempts: 2
  max_cost_usd: 2.00
```

## Security

Treat provider output and metadata as untrusted.

Requirements:

- provider credentials stay outside Git and artifacts;
- URLs returned by the provider are validated before fetching;
- response schemas are validated;
- MIME type and media duration are checked;
- writes are constrained to the project workspace;
- no model/provider text is executed as shell or code;
- callback/webhook payloads, if later used, require authentication and replay protection;
- retries remain bounded;
- unknown provider state is represented explicitly.

## Cost and job execution

Every paid Higgsfield request follows the existing job contract:

```text
estimate
-> validate
-> budget policy
-> reserve
-> provider call
-> reconcile
```

Record:

- provider/model;
- request/job ID;
- prompt/config hash;
- input asset versions;
- duration/resolution;
- attempt number;
- reserved and actual cost;
- output checksum;
- provenance.

Do not retry automatically when external state is unknown.

## Storyboard use

Higgsfield may be evaluated as a storyboard/concept-generation aid, but storyboard approval remains attached to the Sakhalin `scene_plan`, not to provider-internal state.

Generated storyboard frames are disposable review artifacts until explicitly approved.

## Real Sakhalin media rule

For documentary or location-specific scenes:

1. owned Sakhalin footage;
2. approved stock where appropriate;
3. generated fallback only when the scene is clearly labeled internally as generated/reconstructed.

Do not depict a generated location as documentary evidence.

## Derivatives

Higgsfield may later be tested for:

- vertical 9:16 derivatives;
- teaser variants;
- cinematic hooks;
- short transition inserts.

All derivatives must remain traceable to one approved episode revision.

## Pilot: HIGGS-P01

Start only after `SKIDS-013` is visually accepted.

### Goal

Test one bounded Higgsfield insert without changing the local Character Runtime.

### Recommended pilot

A 10-20 second visual insert for a lighthouse episode:

- real or approved still/video reference of Sakhalin location;
- no character dialogue;
- no lip-sync;
- one cinematic move or historical/fantasy reconstruction;
- 16:9 master;
- optional 9:16 derivative.

### Acceptance

- provider adapter is isolated from episode state;
- job is budget-bounded and idempotent;
- provider request ID and provenance are recorded;
- output decodes and passes FFmpeg/ffprobe checks;
- no core-character asset is mutated;
- real/generated provenance is explicit;
- retry behavior is bounded;
- unknown external state does not trigger duplicate spend;
- visual result is judged useful versus the existing provider path;
- cost per usable second is recorded.

## Future optional pilot: HIGGS-P02

Only if HIGGS-P01 passes.

Test a non-dialogue core-character cinematic insert using locked references.

Acceptance adds:

- silhouette and palette continuity;
- wardrobe/prop continuity;
- no face/species drift;
- generated output remains non-canonical;
- local Character Runtime still owns recurring character performance.

## Decision rule

Adopt Higgsfield only for scene classes where it measurably improves quality, speed, or cost.

If the existing OpenMontage provider path is equivalent, keep the simpler path.
