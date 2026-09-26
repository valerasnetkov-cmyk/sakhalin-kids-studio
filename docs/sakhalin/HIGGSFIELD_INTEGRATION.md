# Higgsfield Integration

## Status

Approved integration direction. The implementation is intentionally staged so the active Character Runtime proof remains deterministic and no paid generation is triggered accidentally.

Higgsfield is an external generative-media provider behind a project-owned `MediaProvider` boundary. It is not the owner of episode state, character identity, approvals, or budget policy.

## Goals

- provide a single adapter for Higgsfield image/video generation;
- keep model/vendor choice out of screenplay and character data;
- preserve approved core-character identity;
- require deterministic budget checks before every paid request;
- keep credentials server-side and outside prompts/artifacts;
- allow later providers without changing episode contracts.

## Non-goals

- replacing the local Character Runtime;
- silently regenerating core characters;
- making Higgsfield the production-state owner;
- enabling paid calls during the current Character Runtime proof by default;
- storing provider URLs as permanent media storage.

## Boundary

```text
Episode / Scene
      |
Scene Router
      |
MediaProvider
      |
HiggsfieldProvider
      |
Higgsfield API
```

The project contract is `MediaProvider`. Higgsfield-specific model identifiers, credentials, polling behavior, and response details stay inside the adapter.

## Routing policy

Default routing:

- `character_dialogue` -> local Character Runtime;
- `character_action` -> local Character Runtime;
- `educational_graphic` -> HyperFrames / Remotion;
- `map` -> HyperFrames / Remotion;
- `real_footage` -> owned media library;
- `location_establishing` -> owned media first, then approved generative fallback;
- `historical_reconstruction` -> approved generative path;
- `ai_cinematic` -> provider selector;
- core-character image-to-video -> only with approved reference assets and continuity lock.

## Character continuity

For `makar`, `leva`, `tikhon`, `anna`, and `antoshka`:

- approved base assets are the source of truth;
- palette, proportions, signature clothing, and props remain locked;
- provider calls involving a core character require approved reference assets;
- a provider result is a derived artifact, not a new canonical character asset;
- provider failure must not silently fall back to text-only character regeneration.

## Security invariants

- `HF_KEY`, `HF_API_KEY`, and `HF_API_SECRET` are never committed.
- Provider credentials are read only in the server-side adapter.
- Model output and provider responses are untrusted data.
- External result URLs are not executed or treated as trusted filesystem paths.
- Paid calls fail closed unless generation is explicitly enabled.
- Every paid request requires a positive budget allowance before submission.
- Retry counts, duration, and concurrency are bounded.
- Webhook support, when implemented, must authenticate the callback according to the provider's documented mechanism before changing production state.
- Provider request IDs are persisted for idempotency/reconciliation before production rollout.

## Budget flow

```text
estimate
  -> validate request
  -> budget policy
  -> reserve
  -> provider call
  -> reconcile actual cost
  -> persist result/provenance
```

Hard budget limits fail closed.

Default retry limits remain:

- image: 3 attempts;
- video: 2 attempts;
- voice: 2 attempts.

## Environment

The repository contains only placeholders:

```text
HIGGSFIELD_ENABLED=false
HF_KEY=
HF_API_KEY=
HF_API_SECRET=
```

`HIGGSFIELD_ENABLED=false` is the safe default.

Credentials can use either the combined key or the API key + secret pair. Do not configure both forms at once.

## First implementation slice

The foundation consists of:

1. `MediaProvider` request/result/status contract;
2. fail-closed Higgsfield configuration;
3. Higgsfield adapter with lazy SDK import;
4. no automatic provider invocation from the active Character Runtime milestone;
5. tests for disabled mode and invalid credential configuration.

The first paid smoke test must happen only after explicit operator approval and a configured hard budget.

## Planned production slice

After visual acceptance of SKIDS-013:

1. add estimate/reservation integration;
2. add upload of approved reference assets;
3. add submit/status/result/cancel persistence;
4. add bounded polling and/or authenticated webhook handling;
5. download successful outputs into project-controlled durable storage;
6. attach provenance, model, request ID, reference hashes, and cost;
7. test a location establishing shot without core characters;
8. test one controlled image-to-video shot with an approved character reference;
9. evaluate continuity before allowing character shots in normal production.

## Provider portability

Do not expose Higgsfield SDK objects outside the adapter. Future implementations may include:

- `RunwayProvider`;
- `OpenAIProvider`;
- `LocalComfyUIProvider`.

Episode manifests should describe intent and constraints, not vendor-specific APIs.
