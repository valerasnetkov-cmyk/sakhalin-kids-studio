# AI generation reference extension

This file supplements `character.yaml`; it does not replace the canonical CharacterSpec.

## Canonical identity

- character_id: <id>
- canonical_asset_revision: <approved revision/hash>
- species: <species>
- silhouette: <short invariant description>
- palette: <locked palette reference>
- wardrobe: <locked wardrobe>
- signature_props: <locked props>

## Reference images

Use only approved files from:

`library/characters/<id>/reference_frames/`

Preferred references:

- front
- three-quarter
- side
- neutral
- curious
- talking

## Generation restrictions

- never change species;
- never change eye design;
- never change body proportions;
- never change wardrobe;
- never add/remove signature props;
- never convert the character to realistic human anatomy;
- never use generated output to overwrite canonical art;
- generated output is a derivative review artifact only.

## Provider prompt fragment

Describe appearance only from approved visual invariants. Do not add new design traits.

## Negative constraints

Record provider-specific negative prompt terms here only if the provider supports them.

## Approval

Any generated frame containing this core character must pass character continuity review before use.
