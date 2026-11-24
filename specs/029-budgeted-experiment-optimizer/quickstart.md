# Quickstart: F29

1. Plan the example — expect the baseline plus 2 lengths × 2 seeds, estimates from MC-RUN history (65 frames at 832×480 measured; 81 frames NO DATA) and nothing deferred under the example budget:
   `.venv\Scripts\python.exe -m morph_studio.cli experiment-plan configs\experiments\orchid-length-seed.yaml`
2. Validate only (ComfyUI running, no GPU work): `experiment-run configs\experiments\orchid-length-seed.yaml`
3. Bounded GPU comparison (owner-approved scope): add `--confirm-gpu`; one candidate at a time; stops at the budget.
4. Rate: `experiment-rate configs\experiments\orchid-length-seed.yaml <candidate> 4 --note "clean wing fold"`
5. Report: `experiment-report configs\experiments\orchid-length-seed.yaml` → `outputs\experiments\...\report.md`.
