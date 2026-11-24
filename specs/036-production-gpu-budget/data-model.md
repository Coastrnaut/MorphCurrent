# Data model: F36

## Cost entry (`configs/perf_history.json` → `entries`)
`run` (source label), `kind` anchor | bridge, `width`, `height`, `frames` (bridges) | `method` (anchors), `exec_s`, `job` (16 hex), optional `task`.

## Stage estimate
`stage`, `act`, `kind`, `seconds`, `label` ESTIMATED | INTERPOLATED | EXTRAPOLATED | NO DATA.

## Budget
`acts` [{id, anchors, bridges, seconds, hours, labels {label: n}, batches [{index, stages, seconds, eta_s, oversized}]}], `totals` {stages, seconds, hours, batches, cold_s}, `storage_bytes`, `caps`.

## Approval (`outputs/production/<storyboard>.approvals.jsonl`)
`t`, `storyboard`, `act`, `note`, `owner`, `decision` approved | revoked.

## Status
`finished`, `remaining`, `remaining_seconds`, `eta_hours`, `ratios` [{stage, actual, estimate, ratio, flag}], `duplicates` [{prompt_id, jobs}], `ok`.
