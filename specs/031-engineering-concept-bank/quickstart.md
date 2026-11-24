# Quickstart: F31

1. `.venv\Scripts\python.exe -m morph_studio.cli concepts-check` — expect `ok: true`, total 96, ten eras, status draft.
2. `.venv\Scripts\python.exe -m morph_studio.cli concepts-list` — 96 numbered lines for owner review.
3. With a sync plan: `concepts-check --plan <sync-plan.json>` — fails if the plan has more anchors than entries.
4. Owner approval: set `approval: {owner: <name>, date: YYYY-MM-DD}` and `status: approved`, then re-run the check.
