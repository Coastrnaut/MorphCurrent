# Data model: F39

## Stage state
`stage` (`anchor:<id>` | `bridge:<a>-><b>`), `kind`, `act`, `index` (storyboard order), `state` (missing | rendered | verified), `qa` (status), `qa_flags`, `score` (int ≥ 0), `versions` [Version], `current` (media hash | null), `decision` (Review entry | null), `stale` (bool).

## Version
`sha256`, `job_id`, `run`, `t` (manifest created_at), `media` (path | null).

## Review entry (log line)
`t` (UTC ISO seconds), `stage`, `decision` ∈ {approved, rejected, pending}, `note` (≤ 500 chars), `reviewer` (non-empty), `version` (sha256), `source` (film-log | run-review).

## Rerender queue
`stages` [{stage, reason (rejected | depends on <anchor> | touches <anchor>), est_s, label}], `total_s`, `labels`.

## Act sheet record
`act`, `rows` [{stage, version, frames [0, mid, last]}], `missing` [stage], `out`.
