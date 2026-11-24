# Research: F34

- **Decision**: Per-act look via per-anchor `style_override` on top of one pack, not five packs. **Rationale**: the storyboard schema has one `style.pack`; overrides are already merged and hashed (`style_sha256`), so per-act identity is checkable. **Alternatives**: separate packs per act — rejected (schema change, duplicated base fields).
- **Decision**: Bridge camera via `choreography.camera`. **Rationale**: compiled into a fixed sentence (`CAMERA`), so enforcement is verifiable in the compiled prompt.
- **Decision**: Colour drift on the subject's mean colour from F12 `anchor_geometry` (Otsu mask on dark background). **Rationale**: the engineering-noir look uses dark backgrounds; subject colour is what the palette steers. Euclidean RGB distance; thresholds 60 / 70 are starting points to be calibrated by owner review.
- **Decision**: Two looks — warm→cool journey (default) vs steel base with accents. **Rationale**: tests whether a gradual hue journey or a constant base reads better as one film.
- **Decision**: A/B test = first five anchors of Spark with identical seeds and lengths. **Rationale**: small bounded GPU cost (5 anchors + 4 bridges per look).
