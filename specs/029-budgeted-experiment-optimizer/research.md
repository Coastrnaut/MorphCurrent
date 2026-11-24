# Research: F29

- **Decision**: Reuse `run_bridge` per candidate rather than a new dispatcher. **Rationale**: it already enforces idle queue, `--confirm-gpu`, crash-safe prompt IDs, content-addressed reuse and output verification (Principles II, IV). **Alternatives**: batch submission — rejected (queue saturation forbidden).
- **Decision**: Candidate identity = hash of effective settings including the subject image SHA-256s and profile path. **Rationale**: identical requests map to identical bridge jobs, so the cache reuse and the experiment identity agree.
- **Decision**: Estimates use the median of exact matches (kind, width, height, frames) from `configs/perf_history.json`; no extrapolation by default. **Rationale**: Principle I (NO DATA beats guesses). GPU budget deferral only uses known estimates; at run time the measured total is authoritative.
- **Decision**: Pareto over dimensions measured for every rated candidate (memory is "NOT MEASURED" on ComfyUI 0.46, so it drops out with a note). **Rationale**: avoids comparing unknowns.
- **Decision**: Report language: counts per level, means, "observational; n per level is small; differences may be seed noise". **Rationale**: acceptance gate forbids false certainty.
- **Decision**: Early stop counts consecutive flagged outcomes per (factor, level) pair over executed candidates in order.
