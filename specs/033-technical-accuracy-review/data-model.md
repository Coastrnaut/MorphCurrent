# Data model: F33

## Checklist item
`component_class`, `plausible_geometry`, `no_text`, `no_fake_symbols`, `era_materials` with a question each.

## Verdict (one JSON line in `outputs/reviews/<storyboard>.accuracy.jsonl`)
`t` (UTC), `storyboard`, `anchor`, `image_sha256` (64 hex), `verdict` accurate | reject | waive, `items` {key: "pass" | "fail"}, `note`, `reviewer`.

## Impact
`rejected` [anchor], `invalidated_anchors` [anchor] (plan order), `invalidated_bridges` [stage], `final` bool, `preserved` int, `regenerate` [{anchor, current_seed, new_seed, retry}].

## Status
`anchors` [{anchor, state accurate | waived | rejected | stale | pending, image_sha256, verdict_sha256}], `counts` {state: n}, `gate` bool.
