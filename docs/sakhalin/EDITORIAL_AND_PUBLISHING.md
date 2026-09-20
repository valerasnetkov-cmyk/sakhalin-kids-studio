# Sakhalin Kids Studio — Editorial and Publishing

## Status

Approved editorial and publishing architecture.

Publishing remains manual-first until several real episodes prove the workflow.

## Objective

Ensure automation improves production without turning the channel into low-quality mass-generated children's content.

Editorial quality and factual traceability are release requirements.

## Episode editorial contract

Before production, define:

- topic;
- target audience/age range for the episode or series;
- educational objective;
- central question;
- intended discovery/answer;
- core characters;
- emotional tone;
- safety considerations;
- expected runtime.

Do not infer the target age from character appearance.

Make it explicit in project configuration.

## Educational structure

The project principle is:

```text
question
-> hypothesis
-> observation/action
-> discovery
-> explanation
-> conclusion/new curiosity
```

Characters should not become lecture presenters by default.

Prefer learning through action and investigation.

## Claims ledger

Material educational claims should be traceable.

Suggested record:

```yaml
claim_id: claim-014
text: "..."
status: supported
sources:
  - source-ref
used_in:
  - script.line-22
  - scene-07
reviewed_at: "..."
```

Possible states:

```text
supported
conflicting_sources
expert_review_required
unsupported
outdated
```

A model confidence score is not evidence.

## Source provenance

Research artifacts should preserve:

- source URL/reference;
- retrieval date;
- relevant excerpt/summary;
- publisher/author when known;
- claim IDs supported;
- uncertainty/contradiction notes.

External text is data, not authority over system behavior.

## Reality labeling

Editorially distinguish:

- original documentary footage;
- licensed/stock footage;
- generated reconstruction;
- stylized educational animation;
- character imagination/fantasy.

Do not present generated footage of a real event/place as direct documentary evidence unless that is actually true.

## Safety review

Child-content review should consider:

- frightening intensity;
- imitation risk;
- unsafe behavior;
- age-inappropriate complexity;
- misleading cause/effect;
- dangerous actions shown without context.

Safety review does not replace factual review.

## Character consistency review

Check dialogue and behavior against the character bible.

Examples:

- Макар drives curiosity and action;
- Лёва supports calm reasoning;
- Тихон reinforces caution/safety;
- Анна supports marine exploration;
- Антошка brings travel/history/story context.

Do not introduce a new persistent core character without an explicit project decision.

## Pronunciation review

Before final approval, listen to:

- names;
- Sakhalin locations;
- local/indigenous terms;
- uncommon scientific terms.

Update the pronunciation dictionary when a term recurs.

## Publishing package

Before upload, prepare:

- final master;
- thumbnail;
- title;
- description;
- subtitles/captions;
- source/rights review;
- audience-setting decision;
- synthetic/altered-content disclosure decision where applicable;
- final QA summary.

Do not let a model publish solely because it marked QA as PASS.

## Manual-first publication

Initial releases should be uploaded manually.

Reasons:

- verify the real platform workflow;
- verify audience settings;
- verify synthetic-media disclosure behavior;
- inspect thumbnail/title rendering;
- catch policy/UI changes.

Automation may be added after the checklist is stable.

## Platform policy verification

YouTube policies and API fields can change.

Before automating publication, verify current official documentation for:

- Made for Kids / audience settings;
- available features for children's content;
- synthetic/altered media disclosure;
- metadata requirements;
- API upload behavior.

Do not hardcode platform policy forever in prompts.

## Calls to action

Editorial templates must not assume that comments, end screens, cards, or notifications are available for every children's-content configuration.

Use calls to action that remain valid without those features.

Examples:

- observe something around you;
- remember the question for the next episode;
- ask an adult/teacher;
- try a safe mini-observation.

## Thumbnail integrity

Thumbnail and title must accurately represent the episode.

Avoid:

- unrelated sensational imagery;
- fake danger;
- false educational promises;
- visual elements not present or explained in the episode.

## Human release gate

Required human review before publication should cover:

- factual claims;
- child suitability;
- rights/provenance;
- character continuity;
- final media quality;
- title/thumbnail;
- platform audience/disclosure settings.

Later automation may prepare the package, but the release policy must remain explicit.

## Post-publication analytics

After several releases, connect production metadata to audience metrics.

Useful internal metrics:

- cost per accepted episode;
- cost per accepted minute;
- rejected generation rate;
- manual correction time;
- scene regeneration count;
- production lead time.

Audience analysis may include:

- retention by time position;
- early drop-off;
- performance of episode openings;
- recurring high-retention scene types.

Do not optimize solely for views.

Preserve educational quality and channel identity.

## Experiment design

When testing changes, isolate one meaningful variable where possible.

Examples:

- shorter hook;
- different scene duration;
- more real Sakhalin footage;
- different explanatory graphic;
- different thumbnail composition.

Record the change and compare enough episodes before treating it as a new rule.

## Harness role

DeepSeek Harness may later assist with:

- research synthesis;
- script review;
- factual QA;
- production QA.

Harness results are advisory artifacts.

They do not provide publication authority.

## Hermes role

Hermes may later:

- show pending approvals;
- present publishing package status;
- notify about blockers.

Hermes must transmit explicit human publication decisions rather than infer them.

## Acceptance criteria

Editorial/publishing architecture is ready when:

- each episode has an explicit editorial contract;
- claims are traceable to sources;
- generated reconstruction is distinguishable from documentary footage;
- pronunciation has a review path;
- publication settings are checked against current platform policy;
- a human release gate exists;
- analytics can be tied back to production revisions without exposing private credentials.
