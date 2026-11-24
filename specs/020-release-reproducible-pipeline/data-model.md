# Data model: F20

## RunComparison
`a`, `b` (run dirs), `same_plan: bool`, `stages: [StageComparison]`, `verdict: reproduced | differs | incomplete`, `counts`.

## StageComparison
`task`, `status: identical | different | missing_a | missing_b | not_verified`, `sha_a`, `sha_b`, optional `frames: {count_a, count_b, max_mean_abs_diff, visually_equivalent}`.

## AuditReport
`checks: [{check, status: ok|error|warning, detail}]`, `errors`, `warnings`, `models: [{folder, file, sha256}]`.

## RunArchive
zip with `run/<run>/**`, `jobs/<job>/**`, `SHA256SUMS.json` = `{member: sha256}`; backup result `{archive, files, bytes, missing_jobs}`.

## AcceptanceRow
`feature`, `status` (ledger text), `evidenced: bool`, `gate` (pending text or null); matrix `{rows, evidenced, unresolved, release_ready}`.
