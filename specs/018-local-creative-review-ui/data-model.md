# Data model: F18

Derived views over existing files; only review entries are persisted.

## RunSummary (index row)
`run` (`run-<hex>`), `storyboard`, `status`, `created_at`, from `manifest.json`.

## RunView
`run`, `status`, `storyboard`, `plan_sha256`, `stages: [StageView]`, `contact_sheet: token|null`, `final: token|null`, `final_path`, `media: {token → absolute path}` (allowlist; never shown on the page).

## StageView
`task` (`anchor:<id>` | `bridge:<a>-><b>` | `final:movie`), `kind`, `state`, `qa`, `qa_flags[]`, `reason`, `media: token|null`, `media_missing: bool` (verified stage whose file is gone), `review: ReviewDecision|null`.

## ReviewDecision (in `review.json`, shared with the CLI)
`{task: {decision: approved|rejected|pending, note: str ≤ 500, t: ISO-8601 UTC}}`. Validation: task must be a bridge of the run; decision in the enum.

## PlanView
Storyboard name; anchors (id, chapter, start time, method, reference, positive/negative prompt); transitions (id, frames, span s, candidates, prompt); profile availability; F11 estimate (seconds + label, or NO DATA).

## Media token
First 24 hex of SHA-256 of the resolved absolute path; valid only if present in the current RunView allowlist.
