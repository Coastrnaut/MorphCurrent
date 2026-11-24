# Data model: F23

- **CameraMove** (`transitions[].camera`): `move` ∈ {static, push_in, pull_out, pan_left, pan_right, tilt_up, tilt_down, orbit_left, orbit_right, rise}; `amount` 0–0.5 (default 0.1); `control` ∈ {prompt, graph} (default prompt; graph refused). Conflicts with a non-static `choreography.camera` → validation error.
- **FramingTarget** (`anchors[].framing`): `center` [x, y] in 0–1 (default [0.5, 0.5]); `tolerance` 0–0.5 (default 0.08); `size` [min, max] of mean subject extent (default [0.2, 0.8]).
- **delivery_crops** (`render.delivery_crops`): list of "16:9", "9:16" (default empty).
- **Bridge task record** (only when camera set): `camera: {move, amount, clause, label: "prompt-only approximation"}`.
- **Satisfiability**: `{transition, move, amount, verdict: satisfiable|unsatisfiable|unknown|not_verifiable|pending_anchors, extent_ratio, dx, dy, reason}`.
- **Framing/crop result**: `{anchor, on_target, center, size, crops: {name: inside|outside}}`.
