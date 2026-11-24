# Data model: F28

## project.json (format 1)
- `format` 1, `kind` "morphcurrent_project", `created_at` (UTC), `morphcurrent_version`
- `storyboard` {name, path (repo-relative), sha256}, `plan_sha256`
- `profiles` [{capability, path, profile, workflow, workflow_sha256, status}]
- `style_packs` [{id, path, sha256}]
- `models` [{folder, file, role, licence, sha256, bundled: false}]
- `run` (optional) {name, plan_sha256, plan_matches_storyboard, stages: {stage_id: {state, output_sha256}}, final: {sha256 | null}, redactions}
- `media` {included: bool, audio_included: bool, files: [{path (package or original name), sha256 | "not found", kind: image | video | audio, included}]}
- `anchors` [id], `stage_ids` [id] (used for duplicate checks)
- `migrated_from` (only on migrated descriptions)

## SHA256SUMS.json
`{member: sha256}` for every member except itself.

## Inspection report
`{ok, format, kind, problems: [str], summary: {members, expanded_bytes, media_included, storyboard, plan_sha256}}`

## Readiness report
`{dest, restored_files, plan_sha256_recorded, plan_sha256_recompiled, plan_matches, profiles: [{path, status}], missing_models: [str], note}`
