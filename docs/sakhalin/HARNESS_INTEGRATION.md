# Sakhalin Kids Studio — DeepSeek Harness Integration

## Status

Approved future architecture.

Implementation is deferred until:

1. `SKIDS-001 -> SKIDS-013` is complete;
2. at least one reproducible character-video proof exists;
3. core OpenMontage production state and artifact contracts are stable.

## Objective

Use DeepSeek Harness as a specialized cognitive execution layer for tasks that benefit from parallel reasoning, independent review, or structured synthesis.

DeepSeek Harness is not the main production orchestrator.

## Responsibility split

```text
OpenCode
  development

Hermes
  operator / control plane

OpenMontage
  production workflow and state owner

DeepSeek Harness
  research / review / QA intelligence
```

## Core architectural rule

Do not build this chain:

```text
Hermes Agent
  -> Harness Agent
  -> OpenMontage Agent
  -> Character Agent
  -> Provider Agent
```

That creates ambiguous ownership, nested retries, cost amplification, and hard-to-debug state.

Use:

```text
                     OpenMontage
                         |
             +-----------+-----------+
             |                       |
             v                       v
      deterministic             cognitive
       production                 tasks
             |                       |
             v                       v
      Character Runtime       DeepSeek Harness
      Render / Audio          Research / Review
      Media / Compose         Structured QA
```

## Harness role

Harness may:

- research a topic from multiple perspectives;
- synthesize sourced research;
- review scripts;
- review character consistency at the semantic level;
- review educational clarity;
- review factual claims;
- review final production artifacts;
- return structured findings and suggestions.

Harness must not:

- own episode workflow state;
- approve checkpoints;
- publish;
- bypass budgets;
- alter locked character identity;
- directly perform unlimited paid generation;
- treat one agent's recommendation as authorization for another privileged action.

## Initial workflows

The first approved Harness workflows are documented separately in:

`docs/sakhalin/HARNESS_WORKFLOWS.md`

Scope:

- research;
- script review;
- factual QA;
- production QA.

These workflows are advisory/cognitive layers and must not own production state.

## Structured interface

Harness input/output must use schemas.

Avoid passing free-form agent text directly into:

- shell;
- filesystem paths;
- provider calls;
- state transitions;
- publish actions.

Candidate job envelope:

```json
{
  "job_id": "hjob_001",
  "episode_id": "EP-012",
  "workflow": "script_review",
  "input_artifacts": [
    "script",
    "research_brief",
    "scene_plan"
  ],
  "budget": {
    "max_steps": 12,
    "max_parallel_agents": 4
  }
}
```

## Harness adapter boundary

Target future structure:

```text
integrations/
  harness/
    client.py
    contracts.py
    jobs.py
    validators.py

workflows/
  harness/
    research.yaml
    script_review.yaml
    factual_qa.yaml
    production_qa.yaml
```

Exact file layout should follow the actual OpenMontage integration conventions at implementation time.

## State ownership

Harness may receive:

- immutable artifact references;
- scoped job metadata;
- bounded task instructions.

Harness returns:

- result artifact;
- provenance;
- cost/usage metadata;
- warnings;
- status.

It must not directly transition the OpenMontage episode state machine.

OpenMontage consumes the validated result and decides the next allowed transition.

## Security invariants

Treat all agent messages and external research as untrusted data.

Requirements:

- authenticate agent-to-service calls where applicable;
- validate job schema before execution;
- validate result schema before ingestion;
- limit tools available to each workflow;
- separate read and write capabilities;
- cap recursion/subagent depth;
- cap parallel agents;
- cap steps;
- cap provider spend;
- cap wall-clock time;
- preserve provenance;
- redact secrets from prompts and logs.

A subagent may not gain privilege because it claims a role such as "reviewer" or "admin".

## Prompt injection boundary

External pages, documents, transcripts, metadata, and tool outputs may contain hostile instructions.

Harness workflows must treat them as content, not authority.

A retrieved instruction must not be able to:

- approve a stage;
- invoke a privileged tool;
- expand MCP permissions;
- change budget limits;
- change core character locks;
- write durable policy.

## Cost containment

Every Harness workflow should define:

```text
max_steps
max_parallel_agents
max_retries
max_wall_time
max_provider_cost
```

If limits are reached, return a bounded incomplete result instead of recursively expanding work.

## Failure behavior

Examples:

- malformed result -> reject result;
- partial subagent failure -> record partial status;
- provider unavailable -> return degraded/failed status;
- budget unavailable -> do not start paid workflow;
- provenance missing for factual QA -> mark unsupported;
- conflicting agents -> preserve disagreement for synthesis/human review.

## First implementation scope

When Harness integration is eventually started, implement only:

```text
research
script_review
factual_qa
production_qa
```

Do not initially use Harness for:

- render orchestration;
- provider generation loops;
- episode state transitions;
- publishing;
- character asset mutation.

## Recommended rollout

### Phase H0

No Harness.

Complete Character Runtime Proof.

### Phase H1

Research workflow only.

Validate:

- schemas;
- provenance;
- bounded fan-out;
- cost;
- usefulness versus a single model call.

### Phase H2

Add script review and factual QA.

Measure whether findings improve actual episodes.

### Phase H3

Add production QA after real rendered episodes exist.

### Phase H4

Only after evidence of value, consider additional specialized workflows.

## Acceptance criteria

Harness integration is acceptable when:

- OpenMontage remains the only production-state owner;
- every job is bounded;
- inputs/outputs are schema validated;
- factual outputs retain provenance;
- agent output cannot authorize privileged actions;
- one failed subagent cannot corrupt episode state;
- cost is measurable;
- multi-agent workflows outperform simpler single-agent calls on chosen tasks.

## Decision rule

Use Harness only where multi-agent decomposition produces measurable value.

If one reliable model call gives equivalent output, prefer the simpler path.