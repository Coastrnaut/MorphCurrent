# Research: F32

- **Decision**: Add `frames` to transitions rather than encoding exact lengths as fractional beats at a fake BPM. **Rationale**: exact, readable, no rounding; beats remain for BPM-grid storyboards. **Alternatives**: per-transition BPM — rejected (obscure, rounding).
- **Decision**: Keep the bridge task dict identical for the beat path (same keys and values) so existing plan hashes do not change. **Rationale**: Principle VII and F07 cache reuse.
- **Decision**: Fresh text-to-image anchor at each act start. **Rationale**: isolates acts for invalidation (FR-010) and caps reference-edit chains (≤ 28 with the current bank), mitigating lineage drift (F35); the boundary bridge still uses the same bytes of both neighbouring anchors (shared anchors).
- **Decision**: Act boundaries follow eras; boundary music events are reported (section / onset / energy peak / none). **Rationale**: subject order is the creative spine; moving boundaries to sections would reshuffle subjects — left to the owner.
- **Decision**: Commit the sync plan JSON (timing numbers only). **Rationale**: reproducibility of the film plan without the licensed audio file in the repository.
- **Decision**: GPU estimate via `perf.estimate(extrapolate=True)` aggregated per act. **Rationale**: reuses the F11 measured history and its labels.
