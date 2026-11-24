# Research: F35

- **Decision**: Depth follows `conditioned_on_parent` edges only (same rule as F33 invalidation). **Rationale**: independent and text-to-image anchors are generated separately, so they restart drift.
- **Decision**: Greedy cutting every `limit` edits along a chain. **Rationale**: minimal number of extra keyframes that guarantees max depth ≤ limit; deterministic. **Alternatives**: cutting at section/energy events — possible later refinement with the sync plan.
- **Decision**: Drift relative to the act's reference (first anchor of the chapter). **Rationale**: the reference is the separately generated look anchor for the act (F32), so drift from it is what viewers notice within an act.
- **Decision**: Sharpness via the F16 subject sharpness (mask-edge gradient), ratio to the reference. **Rationale**: detects the detail loss reference-edit chains cause; reuses calibrated code.
- **Decision**: Shared-anchor check compares job-recorded upload hashes with manifest anchor hashes. **Rationale**: the job record stores the exact bytes uploaded to ComfyUI for each endpoint.
