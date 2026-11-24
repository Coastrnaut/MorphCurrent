# Feature Specification: Local style packs and asset collections

**Logical ledger ID**: F21 · **Feature Directory**: `specs/021-style-packs-asset-library` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F21 Local style packs and private asset collections: reusable palette, lighting, lens, composition, materials, prompt and negative presets with content hashes, applied deterministically to storyboards"

## Gap analysis
| Exists | Gap |
|---|---|
| `style.description` string appended to every anchor prompt; per-anchor `negative_prompt`; plan hash | No reusable, versioned look across storyboards; no inheritance or per-scene override; no negatives shared by a look; no record of reference assets and their licences; changing a look does not show up as a distinct identity |

## User Scenarios & Testing *(mandatory)*
### US1 - Versioned style packs with inheritance (P1)
A style pack (`configs/styles/<id>.yaml`): `id`, `version`, optional `extends`, `description`, `palette`, `lighting`, `lens`, `composition`, `materials`, `negative` list, optional `size` and `reference_assets`. Resolution applies parents first; scalar fields override; `negative` merges without duplicates; `palette` replaces. Each resolved pack has a SHA-256 over its canonical content.
**Acceptance**: child overrides lighting, inherits lens; negatives merged in order; cycle → error; unknown parent → error; id must be a safe slug.

### US2 - Storyboards use a pack with per-scene overrides (P1)
`style.pack: <id>` applies the resolved pack to every anchor prompt (deterministic text) and negative prompt; `anchors[].style_override` changes fields for one scene only. The resolved pack hash enters the plan hash only when a pack is used; storyboards without a pack keep their plan hash. Artist prompts are never rewritten — style text is appended.
**Acceptance**: three linked scenes share the pack; the overridden scene differs only in the overridden field; changing the pack file changes the plan hash; the sample storyboard's hash is unchanged.

### US3 - Private asset references (P2)
`reference_assets` entries name files *relative to a local, gitignored library root* (`library/` by default) with SHA-256 and a licence note. `style-check` reports missing, changed (hash mismatch) or unsafe (absolute / `..`) paths. Assets are never copied into Git.

### Edge Cases
Override of a field the pack does not define → allowed (adds it). Empty negatives → no negative added. Pack `size` is advisory (reported, never silently changes render size).

## Requirements *(mandatory)*
- **FR-001** Pack schema strict; id pattern `^[a-z0-9][a-z0-9-]{0,62}$`.
- **FR-002** Deterministic composition: `prompt + " " + description + " Palette: …; lighting: …; lens: …; composition: …; materials: …."` (fields present only).
- **FR-003** Plan task records `style_pack` and `style_sha256` when a pack is used.
- **FR-004** Asset checks are read-only and path-safe.
- **FR-005** CLI: `style-list`, `style-show ID`, `style-check [ID]`.

## Success Criteria *(mandatory)*
- **SC-001** Three-scene fixture shares a pack with one override; deterministic prompts and hash invalidation proven by tests.
- **SC-002** Sample storyboard plan hash unchanged.

## Assumptions
Reference images are provenance only until a workflow exposes a style-reference input (F27).
