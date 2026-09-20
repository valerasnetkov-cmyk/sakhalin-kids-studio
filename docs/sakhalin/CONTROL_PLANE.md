# Sakhalin Kids Studio — Control Plane

## Status

Approved future architecture.

Implementation is deferred until the Character Runtime Proof `SKIDS-001 -> SKIDS-013` is complete and visually accepted.

## Objective

Provide a safe operator layer for Sakhalin Kids Studio without moving production ownership out of OpenMontage.

Target responsibility split:

```text
OpenCode
  = development

Hermes
  = operator / Telegram control plane

OpenMontage
  = production workflow and episode-state owner

DeepSeek Harness
  = cognitive research/review/QA layer
```

## Core invariant

There must be exactly one authoritative owner of production state.

That owner is Sakhalin Kids Studio / OpenMontage.

Hermes may request actions and approve checkpoints.

DeepSeek Harness may analyze and return structured results.

Neither Hermes nor Harness may independently maintain a competing episode state machine.

## Target topology

```text
                     USER
                      |
             Telegram / Web
                      |
                      v
                  HERMES
              operator layer
                      |
                 MCP / API
                      |
                      v
          Sakhalin Kids Control API
                      |
        +-------------+-------------+
        |                           |
        v                           v
   OpenMontage                 read/status
 production state               services
        |
   +----+-------------------------+
   |              |              |
   v              v              v
Character      Media tools    DeepSeek
Runtime                      Harness
                               |
                      research/review/QA
```

## Hermes role

Hermes is an operator interface.

Expected responsibilities:

- create episode requests;
- inspect episode status;
- show storyboard/proposal state;
- request preview renders;
- submit explicit approval/rejection;
- request scene retry;
- read cost reports;
- read QA reports;
- cancel queued/running jobs where supported;
- notify the user about blocked stages or failures.

Hermes is not the production workflow engine.

## Control API

Introduce a narrow control service after the first Character Runtime proof.

Target module boundary:

```text
services/
  control/
    episode_service.py
    job_service.py
    approval_service.py
    budget_service.py
    artifact_service.py

mcp/
  sakhalin_kids/
    server.py
    tools/
      episodes.py
      approvals.py
      renders.py
      status.py
```

Exact paths may adapt to the final OpenMontage integration pattern.

Do not create these modules before the implementation phase that requires them.

## MCP contract

Prefer narrow domain operations over arbitrary execution.

Candidate tools:

```text
create_episode
get_episode
get_episode_status

get_storyboard
approve_stage
reject_stage

render_preview
render_episode
retry_scene

get_cost_report
get_qa_report

cancel_job
```

Avoid generic tools such as:

```text
run_shell
execute_python
write_any_file
fetch_any_url
run_any_command
```

## Example episode creation request

Hermes may convert natural language:

> Сделаем выпуск о сивучах Невельска. Макар и Лёва, около четырёх минут.

into validated structured input:

```json
{
  "topic": "Сивучи Невельска",
  "target_duration_sec": 240,
  "characters": ["makar", "leva"]
}
```

The structured payload must pass deterministic schema validation before creating the episode.

## Approval model

Human approval remains authoritative.

Minimum expected approval gates:

1. proposal;
2. script;
3. storyboard;
4. paid/generated asset plan;
5. publish package.

Hermes may submit the user's explicit approval to the control API.

Hermes must not infer approval from silence or model judgment.

## Example flow

```text
User
  |
  | "Create an episode about sea lions"
  v
Hermes
  |
  | create_episode(...)
  v
OpenMontage
  |
research
  |
proposal
  |
script
  |
storyboard
  |
  +---- PAUSE ----+
                  |
                  v
               Hermes
                  |
           user approval
                  |
                  v
            approve_stage
                  |
                  v
OpenMontage continues
```

## Production ownership

OpenMontage is responsible for:

- workflow state;
- stage transitions;
- artifacts;
- checkpoints;
- cost accounting;
- render decisions;
- production logs;
- final render status.

Hermes must read these states instead of duplicating them.

## Hermes profile

When integration begins, create a dedicated Hermes profile:

```text
sakhalin-kids
```

It should use isolated:

- memory;
- sessions;
- skills;
- cron jobs;
- working context;
- MCP access.

Project-specific memory must not become executable policy.

Repository instructions and deterministic application rules remain authoritative.

## Suggested Hermes skills

Future operator skills may include:

```text
sakhalin-new-episode
sakhalin-episode-status
sakhalin-review-storyboard
sakhalin-review-render
sakhalin-cost-report
sakhalin-retry-scene
```

Skills should call the control API/MCP rather than directly mutate project files or databases.

## Scheduled operations

Cron may later support:

- production queue health checks;
- failed-render alerts;
- cost threshold alerts;
- weekly topic proposal generation;
- pending-approval reminders.

Scheduled jobs must not auto-approve editorial or paid production gates.

## Security invariants

Hermes MAY:

- create bounded episode requests;
- read authorized project state;
- request approved render operations;
- submit explicit user approval/rejection.

Hermes MUST NOT:

- execute arbitrary shell commands in production;
- directly edit the production database;
- override hard budget limits;
- bypass human checkpoints;
- unlock or redesign core characters;
- change provider credentials;
- publish solely because a model recommends it.

All MCP arguments must be validated independently from the model.

## Authentication and authorization

The control plane must enforce authorization at the server boundary.

Do not treat Telegram identity, UI visibility, or Hermes prompts as sufficient authorization by themselves.

High-impact operations should have:

- authenticated actor identity;
- explicit operation;
- validated target episode;
- audit record;
- approval state;
- idempotency where relevant.

## Audit log

High-impact actions should record:

```text
actor
operation
episode_id
stage
timestamp
approval source
result
safe/redacted arguments
```

Never log secrets or raw provider credentials.

## Budget boundary

Hermes can display and query budgets.

It cannot override a hard budget limit.

Paid operations remain governed by:

```text
estimate
-> validate
-> budget policy
-> reserve
-> provider call
-> reconcile
```

## Failure behavior

Control-plane failures must fail closed.

Examples:

- missing approval -> do not continue;
- invalid episode ID -> reject;
- unknown character ID -> reject;
- budget state unavailable -> do not start paid generation;
- malformed MCP arguments -> reject;
- ambiguous high-impact request -> require explicit user action.

## Implementation timing

Do not implement Hermes integration during Milestone 01.

Recommended order:

1. complete `SKIDS-001 -> SKIDS-013`;
2. accept the visual proof;
3. stabilize episode state/artifact contracts;
4. implement Control API;
5. expose narrow MCP tools;
6. connect dedicated Hermes profile;
7. add cron/notifications only after normal control flow is stable.

## Acceptance criteria for future Hermes integration

- OpenMontage remains the single production-state owner;
- Hermes can create/read/approve through narrow interfaces;
- no arbitrary production shell tool is exposed;
- approvals are auditable;
- duplicate commands are idempotent where needed;
- budget limits cannot be bypassed through Hermes;
- core character locks remain enforced;
- a failed Hermes session cannot corrupt episode state.
