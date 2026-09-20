# Sakhalin Kids Studio — Asset Lifecycle

## Status

Approved architecture for production asset management.

Implementation beyond local fixtures is deferred until the first Character Runtime proof is accepted.

## Objective

Treat accepted media and character assets as versioned production objects rather than loose files.

The system must answer:

- what is this asset;
- which version is used;
- where it came from;
- who or what approved it;
- where it is used;
- whether it may be regenerated;
- whether a newer upstream dependency invalidates it.

## Asset identity

Every durable asset receives a stable `asset_id`.

Example:

```yaml
asset_id: character.makar.artwork
version: 3
content_sha256: "..."
status: approved
```

Paths are storage locations, not identity.

## Asset categories

At minimum:

- character artwork;
- rig parts;
- poses/actions;
- visemes;
- voice profiles;
- original Sakhalin photo/video;
- generated images/video;
- backgrounds;
- props;
- ambient/SFX/music;
- subtitles;
- episode scene renders;
- final renders;
- editable timeline packages.

## Versions

Never overwrite an approved production asset in place.

Use explicit versions:

```text
character.makar.artwork/v1
character.makar.artwork/v2

location.nevelsk.harbor/video/v3

episode.EP-004.scene-07/take-02
```

An episode revision pins exact asset versions.

"Latest" must not be used as a production reference after approval.

## Character locks

Core character assets are especially strict.

After approval, lock:

- palette;
- proportions;
- face/eyes;
- signature clothing;
- signature props;
- silhouette;
- canonical views.

Regeneration creates a candidate new version.

It never replaces the approved version automatically.

## Provenance

Durable assets should record:

```yaml
asset_id: location.okhotsk-sea.drone-001
version: 1

source:
  kind: original_footage
  owner: internal

rights:
  status: owned

technical:
  mime_type: video/mp4
  duration_seconds: 12.4
  width: 3840
  height: 2160

provenance:
  created_at: "..."
  project_revision: "..."
```

Generated assets additionally record:

- provider;
- model;
- workflow/model version where relevant;
- prompt reference;
- seed where meaningful;
- provider request/job identifier;
- generation cost;
- source/reference asset IDs.

Do not store provider secrets.

## Rights metadata

Every externally sourced or licensed asset must record rights information sufficient for publication review.

Suggested states:

```text
owned
generated
licensed
public_domain
permission_required
unknown
```

`unknown` blocks final publication until resolved.

## Storage tiers

Use three logical tiers.

### Git

For:

- code;
- schemas;
- manifests;
- small text metadata;
- small intentional test/reference fixtures.

Do not store normal generated video output in Git.

### Durable media storage

For:

- approved masters;
- original footage;
- audio masters;
- accepted generated assets;
- final renders;
- editable delivery packages.

The storage API should remain backend-agnostic.

S3-compatible object storage is a suitable future implementation.

### Workspace/cache

For:

- extracted frames;
- temporary transcodes;
- render caches;
- rejected generations;
- intermediate files that can be reproduced.

Cache retention may be shorter than master retention.

## Object storage

A future adapter may target an S3-compatible service such as Beget object storage.

Do not couple asset IDs to S3 object keys.

Use an abstraction such as:

```text
put_asset
get_asset
get_metadata
verify_checksum
delete_cache
```

Deletion of approved masters requires explicit policy.

## Dependency graph

Track dependencies between durable artifacts.

Example:

```text
script line
  -> dialogue audio
  -> alignment
  -> viseme timeline
  -> scene render
  -> edit timeline
  -> final video
```

If an upstream input changes, mark dependents stale.

Do not rerender unrelated scenes.

## Episode revisions

An episode revision freezes:

- script revision;
- storyboard revision;
- asset versions;
- character versions;
- voice profiles;
- production settings.

A new script revision does not inherit old approval automatically.

## Approval receipts

An approval must identify exactly what was approved.

Minimum data:

```yaml
episode_id: EP-004
stage: storyboard
revision: 3
artifact_hash: "..."
actor: user
approved_at: "..."
```

If the artifact hash changes, the approval is stale.

## ComfyUI workflows

ComfyUI is a planned production adapter, not a mandatory Milestone 01 dependency.

When used, store:

- workflow ID/version;
- workflow JSON or immutable reference;
- custom node versions;
- model/checkpoint identifiers;
- input asset IDs;
- seed and important parameters;
- output asset IDs.

Production agents may select approved workflows and bounded parameters.

They must not install arbitrary custom nodes during a production run.

## Original Sakhalin media

Original footage should preserve useful location metadata separately from public-facing descriptions.

Suggested organization:

```text
location
capture_date
capture_type
camera/drone
orientation
rights
quality_notes
tags
```

Do not rely on filename conventions as the only metadata store.

## Backup

Approved durable media and metadata need backup.

A tool such as restic is a suitable future candidate for backing up to S3-compatible or SFTP targets.

The required control is not "backup job succeeded".

The required control is a tested restore.

## Restore drill

Before production scale:

1. select one episode;
2. restore its metadata and required master assets;
3. verify checksums;
4. reconstruct the editable/final delivery package;
5. document gaps.

Repeat after material storage architecture changes.

## Checksums

Use content hashes for:

- corruption detection;
- approval binding;
- deduplication assistance;
- reproducibility records.

A checksum does not replace semantic versioning.

## Retention

Suggested classes:

- character masters: permanent;
- original footage: permanent unless policy changes;
- approved episode masters: permanent;
- rejected generations: short/medium retention;
- temporary frames/transcodes: disposable cache;
- provider logs: policy-defined and redacted.

Exact durations should be decided after real storage usage is measured.

## Acceptance criteria

Asset lifecycle architecture is ready when:

- approved assets are versioned;
- episode revisions pin exact versions;
- checksums are stored;
- provenance and rights are available;
- dependent outputs can be invalidated selectively;
- cache and master storage are separated;
- one episode can be restored from backup;
- character locks cannot be bypassed by normal regeneration.
