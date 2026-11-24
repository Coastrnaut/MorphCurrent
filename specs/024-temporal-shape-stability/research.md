# Research: F24

## R1 One mask threshold per clip
- **Decision**: threshold = max(24, mean of the first and last frames' Otsu thresholds), applied to every frame.
- **Rationale**: per-frame Otsu (F16) re-adapts to each frame, hiding substitutions and making masks incomparable; a clip-level threshold keeps overlap and part counts meaningful.

## R2 Connected parts
- **Decision**: 4-connected components on the 128×74 mask via iterative flood fill; ignore components < 0.5% of the frame (≈ 47 px) to suppress glints.

## R3 Relative thresholds for motion
- **Decision**: motion/colour/background steps compared with max(absolute floor, 4 × the clip's median step) so steady fast motion is tolerated; thresholds as in spec Clarifications.

## R4 No optical-flow claims
- **Decision**: mask overlap and colour paths are proxies; reports say "heuristic" and never claim physical identity (ledger F24 build note).

## R5 Repair refinements per kind
- substitution → "the subject transforms continuously part by part; no part is replaced or swapped"
- topology → "all parts stay attached and visible throughout; nothing disappears or splits off"
- background → "the background stays dark and unchanged throughout"
- motion jump → "the subject moves smoothly with no jumps, staying centred"
- colour jump → "materials change gradually; no sudden colour or material switch"
- F16 kinds (collapse / drift / blur) map to "the subject keeps its full size", "stays centred", "stays sharp and in focus".
