# Data model: F40

## Assembly record (`<master>.assembly.json`)
`film`, `storyboard`, `plan_sha256`, `preview` (bool), `chosen` [{stage, version, job_id, run, media, decision}], `anchors` [{stage, version, media}], `unapproved` [stage], `master`, `frames`, `planned_frames`, `fps`, `duration_s`, `planned_s`, `seams`, `seam_mode` (anchor+boundary | boundary), `audio`, `audio_licensed`, `created_at`.

## Blocker
`stage`, `reason` ∈ {missing, unreviewed, pending, rejected, stale}.

## Delivery record (`<master>.delivery.json`)
`master`, `preview`, `presets`, `results`, `errors`.

## Provenance report
`film`, `plan_sha256`, `storyboard_sha256`, `preview`, `stages` [{stage, version, job_id, seed, run}], `workflows` [{profile, workflow, workflow_sha256, models}], `models` [{file, sha256, licence, recorded_sha256}], `approvals` {concept_bank, visual_language, acts, review_decisions}, `gpu` {measured_s, estimated_s, ratio, jobs_timed}, `missing` [str], `complete` (bool).

## Gate row
`feature`, `status`, `evidenced`, `gate`, `accepted` ({blocker, owner, date} | null), `resolved`.

## Accepted blockers (`configs/film/accepted-blockers.yaml`)
`version: 1`, `accepted: [{feature: "F3x", blocker, owner, date: YYYY-MM-DD}]`.
