# Quickstart: validate F18

Prerequisites: controller `.venv`; an existing run (e.g. `outputs/runs/run-ba2d9dbedb6189be`) or the test suite's synthetic run.

1. Offline tests: `.venv\Scripts\python.exe -m pytest tests/test_review_ui.py -q` → all pass (parity, security, missing media, live server).
2. Start: `.venv\Scripts\python.exe -m morph_studio.cli review-ui` → prints `http://127.0.0.1:8765/`.
3. Open the URL: the runs index lists `run-ba2d9dbe…`; plan links list `organic-machines`.
4. Run page: 3 anchors, contact sheet, 2 playable clips with QA `no_flags`, final movie.
5. Approve a clip with a note → banner "Recorded approved…"; `morphcurrent render --status RUN` shows the same review.
6. Refusal: `morphcurrent review-ui --host 0.0.0.0` → error, exit 2.
7. ComfyUI `/queue` unchanged before and after (no prompts submitted).

Status codes: [contracts/http-routes.md](contracts/http-routes.md).
