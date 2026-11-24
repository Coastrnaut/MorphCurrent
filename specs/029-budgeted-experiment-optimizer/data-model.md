# Data model: F29

## ExperimentDefinition (YAML)
`name` slug; `subject` {start_image, end_image, positive_prompt, negative_prompt?, profile = configs/profiles/wan22_flf2v.binding.json}; `controls` {setting: value}; `factors` {setting: [values] (≥1)}; `seeds` [int] | `seed_count` int + `master_seed` int; `budget` {max_runs?, max_gpu_s?, max_frames?}; `early_stop` {consecutive_flagged: int ≥ 1}?.
Allowed settings: seed, length, width, height, positive_prompt, negative_prompt, fps, profile. `seed` may not appear in controls/factors when a seed block is used (always is).

## Candidate
`id` (16 hex), `index`, `baseline` bool, `settings` (effective request fields), `levels` {factor: value}, `seed`, `frames` (effective length), `width`, `height`, `estimate_s` | null, `status` planned | deferred, `limit` (for deferred).

## Outcome (results.jsonl line)
`id`, `status` done | failed | validated | skipped, `job_dir`, `exec_s`, `peak_vram` | null, `frames_requested`, `frames_produced`, `bytes`, `flags` [str], `error`, `t`.

## Ratings (ratings.json)
`{id: {score 1..5, note, t}}`.

## Report
`experiment`, `controls`, `factors`, `seeds`, `budget`, `totals` {done, failed, exec_s}, `levels` {factor: {value: {n, rated, mean_rating, mean_exec_s, mean_bytes, mean_vram}}}, `mismatches` [id], `unrated` [id], `pareto` [id], `pareto_dimensions`, `caveat`.
