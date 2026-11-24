# Data model: F31

## ConceptBank (`configs/concepts/engineering-film.yaml`)
`version` int ≥ 1; `status` draft | approved; `approval` null | {owner: non-empty, date: YYYY-MM-DD}; `drafted_by` text; `eras` [ten names in order]; `entries` [ConceptEntry] (≥ 96).

## ConceptEntry
`id` slug (unique); `era` one of `eras`; `follows` id of previous entry (omitted for the first); `subject`; `description`; `shapes` [≥1]; `materials` [≥1]; `scale` (e.g. "hand-held", "room", "chip"); `morph_to_next` (required except the last); `accuracy_note`; `sources`; `accuracy` unverified | reviewed.

## CheckReport
`ok`, `total`, `target`, `status`, `counts` {era: n}, `problems` [{id, field, message}].
