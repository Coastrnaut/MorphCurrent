# Research: F33

- **Decision**: Propagate invalidation only along `conditioned_on_parent` edges (reference edits). **Rationale**: an independent/text-to-image anchor is generated separately, so a rejected ancestor does not change its pixels (the constitution's "separately generated reanchor"). **Alternatives**: follow every `depends_on` edge — rejected (over-invalidates independent anchors whose `reference` is only a continuity hint).
- **Decision**: Bridge text negatives through `choreography.negative`. **Rationale**: the existing prompt compiler merges defaults + negatives and the binding profile's `negative_prompt` role patches the graph; no new graph path. **Alternatives**: editing the Wan export's baked negative — rejected (graph contract, hash pinning).
- **Decision**: Append-only JSON Lines log with fsync. **Rationale**: crash-safe, diff-friendly, never rewritten; corrupted lines reported.
- **Decision**: Stale = latest verdict hash ≠ current image hash from the run manifest. **Rationale**: verdicts are about pixels; any re-render needs a new look.
- **Decision**: Regeneration seed via `derived_seed(master, "<task>:retry<n>")`. **Rationale**: deterministic and reproducible like all seeds.
