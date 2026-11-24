# Quickstart: validate F23

1. `.venv\Scripts\python.exe -m pytest tests/test_camera.py -q` → all pass.
2. `.venv\Scripts\python.exe -m morph_studio.cli camera-check configs\sequences\organic-machines.yaml` → no camera moves set: transitions report static/choreography only, verdict pending anchors.
3. `... camera-check configs\sequences\organic-machines.yaml --run outputs\runs\run-ba2d9dbedb6189be` → per-transition satisfiability for the real anchors and per-anchor framing.
4. Add `camera: {move: push_in, amount: 0.15}` to a transition in a copy; `render --dry-run` shows the compiled clause and "prompt-only approximation"; `control: graph` is refused.
