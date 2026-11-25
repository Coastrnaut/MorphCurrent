# Research: F40 film delivery

## R1 Version choice
- Decision: non-preview uses the F39 decision `approved` on the current version; anything else is a blocker with a reason. Preview uses the current version of every bridge and lists the unapproved ones; missing bridges still refuse (nothing to join).

## R2 Join
- Decision: reuse `stitcher.join_verified` (seam check, `.part` + rename, frame-count verification, optional audio with offset, no crossfade). Anchor stills are passed when all are readable images, so each seam is also compared with its shared anchor; otherwise only clip boundaries are compared and the record says so.
- Coverage: planned total = last anchor frame + 1 from the frame-locked timeline (5,741 for the film = 358.8125 s at 16 fps); the join must equal it exactly.

## R3 Delivery
- Decision: `delivery.deliver` with default presets `landscape-1080p` and `vertical-1080x1920`; licensed audio passes through.

## R4 Provenance
- Decision: workflows from the three bindings (workflow path + `workflow_sha256`, models from `provenance.models_in_graph`); model sha256/licence from the catalogue; recorded weight hashes from `outputs/model_hashes.json`; approvals from the concept bank (`approval`), visual language (`selected`, status), `outputs/production/<film>.approvals.jsonl`, the F39 log. A catalogue licence starting "NOT RECORDED" counts as missing.
- GPU: measured = Σ job `timings.execution_seconds` of chosen versions (anchors and bridges); estimate = `production.budget(...)["totals"]["seconds"]`.

## R5 Gates
- Decision: `release.acceptance_matrix(through=40)` rows F31–F40; accepted blockers from `configs/film/accepted-blockers.yaml` (`- {feature, blocker, owner, date}`) mark a row resolved.
