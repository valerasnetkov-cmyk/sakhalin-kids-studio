# Sakhalin Kids Studio — Media Delivery

## Status

Approved delivery and media-QA architecture.

The first Character Runtime proof only needs a technically valid MP4 plus review frames/audio.

Full editable delivery is required before routine full-episode production.

## Delivery outputs

A production episode should eventually produce three classes of output.

### Review output

Optimized for quick human review.

Examples:

- review MP4;
- storyboard/contact sheet;
- QA report.

### Final master

The approved release-quality video.

### Editable package

A package suitable for manual finishing without regenerating the episode.

Target contents:

- edit timeline;
- scene renders;
- dialogue stems;
- music stem;
- SFX/ambient stems where practical;
- subtitle/caption files;
- graphics/assets required by the edit;
- metadata manifest.

## OpenTimelineIO

OpenTimelineIO is the preferred future interchange model for editorial timing and clip references.

Use it for:

- clip order;
- source references;
- in/out timing;
- track structure;
- basic editorial metadata.

Do not assume every transition, effect, title, or color operation will round-trip through every NLE.

Compatibility with the actual editing application must be tested.

## Media package example

```text
delivery/
  master/
    episode.mp4
  review/
    review.mp4
    contact-sheet.jpg
  timeline/
    episode.otio
  video/
    scene-001.mp4
    scene-002.mp4
  audio/
    dialogue/
    music/
    sfx/
    ambient/
  subtitles/
    episode.srt
  metadata/
    delivery.json
    qa.json
```

Exact structure may evolve after testing with the preferred NLE.

## Render profiles

Define named render profiles rather than hardcoding random settings in prompts.

Initial profile examples:

```text
proof
review
youtube-master
vertical-short
```

Each profile should define:

- resolution;
- frame rate;
- codec/container;
- audio sample rate;
- loudness target;
- subtitle behavior.

Do not invent final platform settings until the real delivery workflow is tested.

## FFmpeg technical QA

Use deterministic checks where possible.

Candidate checks:

- `ffprobe` parses the result;
- expected video/audio streams exist;
- duration is within tolerance;
- resolution/frame rate match profile;
- no unexpected long black segments;
- no unexpected long silence;
- audio is not clipped;
- loudness is measured against the chosen profile;
- opening/middle/end frames can be sampled.

Automated black/silence detection must compare against creative intent.

A deliberate fade or pause is not automatically a defect.

## Audio structure

Keep dialogue separate from music/SFX as long as practical.

Benefits:

- easier lip-sync debugging;
- pronunciation fixes without full regeneration;
- manual mix adjustments;
- editable delivery.

Do not run speech alignment on the final mixed soundtrack when clean dialogue stems are available.

## Russian alignment

The project keeps alignment behind an adapter.

Possible order:

1. provider timing metadata, if trustworthy and sufficiently precise;
2. dedicated forced/alignment tool;
3. manually supplied fixture timings for technical tests.

WhisperX is an approved candidate to evaluate for Russian alignment after the Character Runtime proof.

It is not a required Milestone 01 dependency.

## Pronunciation dictionary

Create a project pronunciation dictionary for:

- character names;
- Sakhalin place names;
- indigenous/local terms;
- recurring scientific vocabulary.

Each entry may include:

- display form;
- spoken form;
- phonetic hint/provider override;
- review status.

Pronunciation must be checked by listening.

A successful TTS request is not proof of correct pronunciation.

## Lip-sync deliverables

For each dialogue line retain:

- source text;
- audio asset ID/version;
- timing/alignment artifact;
- viseme timeline;
- voice profile version.

This permits rebuilding mouth animation without paying for TTS again.

## ComfyUI production adapter

ComfyUI is a future media-generation/processing worker.

Approved use cases may include:

- backgrounds;
- props;
- controlled image variants;
- image-to-video inserts;
- selected restoration/processing tasks.

Use curated versioned workflows.

Do not allow a production agent to install arbitrary nodes or execute unreviewed workflows.

## Visual provenance

Generated visuals must remain linked to:

- source/reference assets;
- workflow/model;
- provider;
- prompt reference;
- seed/settings;
- episode/scene.

A generated representation of a real location must not automatically be labeled documentary footage.

## Scene replacement

A new take creates a new asset version.

The editor/pipeline chooses which take is active.

Do not overwrite a previously approved take.

## Subtitles

Maintain subtitles as a first-class artifact.

At minimum retain:

- text;
- timing;
- language;
- revision;
- source dialogue references.

Subtitles should be regenerated when dialogue timing changes.

## Technical QA vs creative QA

Technical QA checks measurable properties.

Creative QA checks:

- pacing;
- composition;
- acting;
- readability;
- emotional tone;
- character continuity.

A technical PASS does not imply creative approval.

## Manual finishing

Manual finishing is allowed and expected where it produces a better result.

If the final master differs from the automated render, record:

- source automated render;
- editing package revision;
- manual edit version;
- final master hash.

The system should support professional editorial work rather than forcing full automation.

## Delivery gate

Before a full episode is ready for publishing review:

- master file exists;
- technical QA passes;
- creative review passes;
- required approvals are current;
- subtitles exist where required;
- rights/provenance checks are complete;
- editable package can be reconstructed;
- costs are reconciled.

## Acceptance criteria

Media delivery architecture is ready when:

- renders use named profiles;
- audio stems are retained;
- subtitles are versioned;
- final technical QA is reproducible;
- edit timing can be exported in an editable form;
- a manual finishing pass does not destroy provenance;
- replaced scene takes remain recoverable.
