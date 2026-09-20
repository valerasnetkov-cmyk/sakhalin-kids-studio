# Sakhalin Kids Studio — Job Execution

## Status

Approved post-proof execution architecture.

Milestone 01 may remain single-process and sequential.

Do not introduce distributed infrastructure before the Character Runtime proof demonstrates a real need.

## Objective

Make long-running and paid production operations resumable, idempotent, auditable, and bounded.

## Core entities

### Episode revision

Immutable production input snapshot.

Contains references to approved:

- script;
- storyboard;
- asset versions;
- character versions;
- runtime settings.

### Job

A unit of requested work.

Examples:

- synthesize one dialogue line;
- align one audio file;
- render one scene;
- generate one approved AI-video insert;
- compose an episode.

### Attempt

One execution attempt of a job.

A job may have multiple attempts under bounded retry rules.

### Artifact version

Durable output produced by a successful job.

### Approval receipt

Proof that a human approved a particular artifact revision.

### Cost entry

Reservation or reconciled provider cost attributable to a job/attempt.

## Job states

Use explicit states such as:

```text
queued
running
succeeded
failed
cancel_requested
cancelled
unknown_external_state
blocked
```

`unknown_external_state` is important for external providers when a request may have succeeded but the local connection failed.

Do not automatically retry an operation whose external state is unknown.

## Idempotency

Every expensive or irreversible job needs a stable idempotency key.

Example inputs:

```text
episode revision
scene ID
operation
input artifact hashes
provider/model
important settings
```

If the same job is requested again, the system should reuse the valid existing result where policy allows.

## Provider request tracking

For external providers record:

- internal job ID;
- provider request/job ID;
- request timestamp;
- provider/model;
- reserved cost;
- current external state;
- output asset IDs.

After a timeout, query provider status before resubmitting when the provider supports it.

## Retry policy

Retries are explicit and bounded.

Default planning values:

- image: max 3;
- video: max 2;
- voice: max 2.

A retry must create a new attempt while preserving previous attempt history.

Do not recursively delegate retries to agents without a hard bound.

## Cost handling

Paid work follows:

```text
estimate
-> validate
-> budget policy
-> reserve
-> execute
-> reconcile
```

Track cost per:

- episode;
- scene;
- job;
- provider;
- attempt.

The pipeline `budget_default_usd` is a default planning value, not proven production cost.

## Hard budget

When a hard budget would be exceeded:

```text
block job
-> report reason
-> require explicit budget decision
```

Hermes, Harness, or a Production Director cannot silently override the limit.

## Resume

A process restart must not require restarting the entire episode.

Resume from durable:

- episode revision;
- checkpoints;
- jobs/attempts;
- artifact versions;
- approval receipts;
- provider request IDs.

## Dependency handling

Jobs can depend on other jobs.

Example:

```text
tts_line_04
  -> align_line_04
  -> viseme_line_04

scene_07_assets
  + viseme_line_04
  -> render_scene_07

all approved scenes
  -> compose_episode
```

A changed upstream artifact invalidates only affected descendants.

## Worker model

Milestone 01:

```text
one operator
one process
sequential jobs
```

Later:

```text
Control API
  |
job store
  |
+------------------+
|                  |
VPS worker      local GPU worker
                 ComfyUI/render
```

A local GPU worker should preferably pull authorized jobs.

Do not expose a raw local ComfyUI interface publicly solely for orchestration.

## Durable job store

Do not add a database only for architectural symmetry.

When multi-worker execution, Hermes control, or reliable resume requires it, PostgreSQL is the preferred initial durable job/state store.

Use database transactions/locking to prevent two workers from claiming the same job.

Implementation details must be proven with concurrency tests.

## No competing state machines

The durable job store supports execution.

It must not create a second independent creative production workflow.

OpenMontage stage/checkpoint semantics remain authoritative until an explicit migration changes that ownership.

## Cancellation

Cancellation is cooperative where external providers cannot guarantee immediate stop.

On cancellation:

- stop starting dependent work;
- attempt provider cancellation if supported;
- preserve completed artifacts;
- reconcile costs;
- record the final state.

Do not delete production history to simulate cancellation.

## Approval binding

Approvals bind to a revision/hash.

Example:

```text
storyboard revision 3 approved
storyboard revision 4 created
=> revision 4 is NOT approved
```

A production stage must fail closed if required approval is stale or missing.

## Duplicate operator commands

Commands such as:

```text
render scene 7
approve storyboard
create episode
```

must be designed for duplicate delivery.

For one-time operations use idempotency and uniqueness constraints.

## Audit data

Record high-impact execution events with:

- actor;
- episode ID;
- job ID;
- operation;
- attempt;
- timestamp;
- result;
- cost impact;
- approval reference.

Redact secrets.

## Failure policy

Examples:

### Worker crash

Job lease expires or is reconciled, then safely retried if state is known.

### Provider timeout

Move to `unknown_external_state` until queried/reconciled.

### Invalid provider response

Fail the attempt; do not pass malformed output downstream.

### Artifact checksum mismatch

Block dependent jobs.

### Budget service unavailable

Block new paid jobs.

### Approval service unavailable

Block approval-gated transitions.

## Tests required before multi-worker production

At minimum test:

- duplicate job submission;
- duplicate approval;
- concurrent claim;
- worker crash/restart;
- external timeout;
- stale approval;
- hard-budget rejection;
- cancelled dependent chain;
- malformed provider output;
- filesystem write outside workspace rejection.

## Relationship to Hermes

Hermes will call narrow control operations.

Hermes does not manipulate job records directly.

See `CONTROL_PLANE.md`.

## Relationship to Harness

Harness jobs are bounded cognitive jobs with their own limits.

Their outputs are validated artifacts.

Harness agents do not transition production state directly.

See `HARNESS_INTEGRATION.md`.

## Acceptance criteria

Job execution is production-ready for the reviewed scope when:

- paid jobs are idempotent;
- retries are bounded;
- external unknown state is represented explicitly;
- restart/resume works;
- approvals bind to revisions;
- costs reconcile per attempt;
- duplicate commands do not duplicate side effects;
- workers cannot exceed scoped permissions.
