# Feature Specification: Structured Local A/B Experiments and Quality-vs-Cost Optimization (F29)

**Feature Branch**: `029-budgeted-experiment-optimizer` (work committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "F29 Structured local A/B experiments and quality-vs-cost optimization — offline slice plus GPU-gated runner: experiment definition for one bridge with controls, factors limited to real bridge inputs and validated against workflow constraints, a seed block and a budget; deterministic factorial design with baseline first, content-hashed candidates, estimated GPU time and deferred candidates; one-at-a-time resumable runner through the existing bridge jobs with --confirm-gpu, budget stop and early-stop; owner ratings, per-level summaries, mismatch flags, Pareto frontier and an honest report. CLI experiment-plan, experiment-run, experiment-rate, experiment-report."

## Clarifications

### Session 2026-11-24

Resolved autonomously from the ledger and owner rules:

- Q: Where do an experiment's log, ratings and report live? → A: `outputs/experiments/<name>-<definition hash 8>/` (the hash covers name, subject, controls, factors and seeds, not the budget, so raising a budget resumes the same experiment; `results.jsonl`, `ratings.json`, `report.md`, `report.json`); bridge jobs stay in the normal content-addressed runs folder so identical candidates are reused.
- Q: What exactly is the baseline? → A: The subject with only the controls applied (every other input keeps the workflow's exported value) and the first seed of the seed block.
- Q: In what order are candidates listed? → A: Baseline first, then factors sorted by name with their values in the order written, seeds varying fastest.
- Q: How is the seed block written? → A: Either an explicit `seeds` list or a `seed_count` derived deterministically from a master seed and the experiment name.
- Q: What counts as "flagged" for early stopping? → A: A candidate whose existing per-clip quality check reports any flag, or whose job failed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Design a bounded comparison (Priority: P1)

The owner writes a small experiment file naming one bridge (its two anchor images and prompt), the settings held fixed, the settings to vary (for example two clip lengths and two seeds), and a budget. The tool checks that every varied setting is something the video workflow really accepts and within its real limits, then lists every candidate in a fixed order with the baseline first, each with a stable identifier and an estimated GPU time from past measurements. Candidates that would exceed the budget are listed as deferred.

**Why this priority**: Systematic comparison replaces guessing, and the budget keeps GPU use bounded before anything runs.

**Independent Test**: A definition with 2 lengths × 2 prompts × 3 seeds produces 13 candidates (baseline + 12) in the same order on every run, each with the same identifier; a budget of 5 runs marks 8 as deferred.

**Acceptance Scenarios**:

1. **Given** a valid definition, **When** planned, **Then** the baseline (controls only) is first, followed by every factor combination × seed in a deterministic order, each with a content identifier and estimated GPU seconds or "NO DATA".
2. **Given** a setting listed both as fixed and as varied, **When** planned, **Then** the definition is refused for control leakage.
3. **Given** a varied setting the workflow does not accept (for example "steps" or "cfg"), **When** planned, **Then** it is refused naming the allowed settings.
4. **Given** a clip length that is not 4n+1, or a size not a multiple of 16, **When** planned, **Then** it is refused naming the rule.
5. **Given** a budget smaller than the design, **When** planned, **Then** the candidates over the budget (runs, estimated GPU seconds or frames) are listed as deferred with the limit that deferred them.

---

### User Story 2 - Run it safely, one candidate at a time (Priority: P1)

The owner runs the experiment. Without explicit GPU confirmation each candidate is only validated against the live workflow. With confirmation, candidates render one at a time through the normal bridge jobs (which refuse a busy queue), each result is appended to a results log, candidates already rendered are reused, and the run stops as soon as the measured GPU time or run count reaches the budget. Interrupting and re-running continues where it stopped.

**Why this priority**: GPU discipline (one job, idle queue, explicit consent) and reproducibility must hold for experiments as for renders.

**Independent Test**: With a stand-in executor, a 6-candidate experiment with a 100-second budget and 40 s per candidate stops after 3 candidates; re-running after an interruption does not repeat finished candidates.

**Acceptance Scenarios**:

1. **Given** no GPU confirmation, **When** run, **Then** candidates are only validated and nothing is rendered.
2. **Given** confirmation, **When** run, **Then** candidates execute strictly one at a time in design order and each outcome (candidate, job, measured GPU seconds, peak memory if recorded, frames, size, quality flags) is appended to the log.
3. **Given** measured GPU time reaching the budget, **When** the next candidate would start, **Then** the run stops and reports "budget exhausted".
4. **Given** a results log with finished candidates, **When** run again, **Then** those candidates are skipped and reported as reused.
5. **Given** an early-stop rule of N, **When** N consecutive candidates sharing a factor level are flagged by quality checks, **Then** the remaining candidates of that level are skipped and reported.

---

### User Story 3 - Rate, compare and choose (Priority: P2)

The owner rates each rendered candidate from 1 to 5 with a note. A report then summarizes each factor level (mean rating, runtime, memory, file size, sample count), flags candidates whose output length differs from what was requested, lists the Pareto-optimal candidates (no other candidate is at least as good on rating, runtime, memory and size and better on one), and states plainly that the results are observational with the given sample sizes.

**Why this priority**: The acceptance gate is a human-readable report with explicit variables, timings, notes and Pareto choices, without false certainty.

**Independent Test**: Given a results log with ratings, the Pareto set matches a hand-computed set, per-level means are correct, a length mismatch is flagged and the report contains the sample-size caveat.

**Acceptance Scenarios**:

1. **Given** a rated candidate, **When** rating outside 1–5 or for an unknown candidate, **Then** it is refused.
2. **Given** ratings, **When** reported, **Then** per-level summaries and the Pareto set are shown; unrated candidates are excluded from the Pareto set and listed as unrated.
3. **Given** a candidate whose output frames differ from the requested length, **When** reported, **Then** it is flagged.
4. **Given** any report, **Then** it lists the controls, factors, seeds, budget, measured totals and the observational caveat.

### Edge Cases

- A factor with one value is treated as a control (warned) to avoid a meaningless comparison.
- An experiment whose baseline equals one factor combination is not duplicated (same identifier → one candidate).
- No measured history: estimates are "NO DATA", and only the run and frame budgets apply until measurements exist.
- A candidate job that fails is logged as failed (with its error) and counts toward the run budget but not the GPU-time budget unless time was measured.
- Ratings are stored separately from the results log so re-runs never lose them.
- Anchor images given must exist; missing files refuse the plan.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: An experiment definition MUST name a subject bridge (start image, end image, prompt, profile), controls, factors, a seed block (explicit list or count derived from a master seed) and a budget (max runs, max GPU seconds, max frames; each optional).
- **FR-002**: Factors MUST be limited to the bridge's bindable inputs (seed, length, width, height, positive prompt, negative prompt, fps, profile); any other setting MUST be refused naming the allowed ones.
- **FR-003**: Values MUST be validated against the workflow's real rules: length 4n+1 within the workflow's limits, width/height multiples of 16, fps positive, profile must be a known binding profile for the first/last-frame capability.
- **FR-004**: A setting appearing in both controls and factors MUST be refused (control leakage); seed MUST come only from the seed block when seeds vary.
- **FR-005**: The design MUST be the baseline followed by the full factorial of factor values × seeds in a deterministic order, with each candidate identified by a content hash of its effective settings and duplicates removed.
- **FR-006**: Each candidate MUST carry an estimated GPU time from measured history matching its size and length, or "NO DATA".
- **FR-007**: Candidates beyond any budget limit (in design order) MUST be marked deferred with the limit responsible; nothing is silently dropped.
- **FR-008**: The runner MUST execute at most one candidate at a time, in design order, through the existing bridge job machinery; without GPU confirmation it MUST only validate.
- **FR-009**: Each outcome MUST be appended to a results log keyed by candidate identifier; re-running MUST skip candidates with a finished outcome.
- **FR-010**: The runner MUST stop before starting a candidate when measured GPU seconds or completed runs have reached the budget, and report why it stopped.
- **FR-011**: An optional early-stop rule MUST skip the remaining candidates of a factor level after N consecutive flagged candidates at that level.
- **FR-012**: Owner ratings (integer 1–5, optional note) MUST be stored in a separate ratings file keyed by candidate identifier; unknown candidates or out-of-range ratings MUST be refused.
- **FR-013**: The report MUST include controls, factors, seeds, budget, per-level summaries (count, mean rating, mean runtime, mean memory, mean size), length mismatches, unrated candidates, the Pareto set over rating (max) and runtime, memory, size (min), measured totals, and an observational caveat with sample sizes.
- **FR-014**: The experiment tools MUST NOT modify existing approved outputs or run folders and MUST write only the experiment's own log, ratings and report files.
- **FR-015**: Command-line access MUST provide experiment-plan, experiment-run (with GPU confirmation flag), experiment-rate and experiment-report, with ASCII-safe output and exit codes 0 success, 2 refusal.
- **FR-016**: Experiment files MUST be written under `outputs/experiments/<name>-<definition hash 8>/`; the baseline and ordering MUST follow the Clarifications.

### Key Entities

- **Experiment definition**: subject, controls, factors, seeds, budget, early-stop.
- **Candidate**: identifier, effective settings, factor levels, seed, estimate, status (planned / deferred / validated / done / failed / skipped).
- **Outcome**: candidate, job reference, measured GPU seconds, peak memory, frames requested and produced, size, flags, error.
- **Rating**: candidate, score 1–5, note, time.
- **Report**: summaries, Pareto set, mismatches, caveat.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The same definition always yields the same candidate list and identifiers (100% across repeated plans).
- **SC-002**: In tests, the runner never exceeds the run budget and never starts a candidate after the GPU-time budget is reached.
- **SC-003**: Re-running after an interruption repeats zero finished candidates.
- **SC-004**: The Pareto set and per-level means match hand-computed values in 100% of test cases.
- **SC-005**: Planning a 13-candidate experiment completes in under 1 second offline.

## Assumptions

- The subject is a single bridge; anchor experiments can follow the same pattern later.
- Measured history is the existing performance history file used by `estimate`.
- Real GPU runs are a bounded owner-approved comparison (standing local-render consent covers one-at-a-time renders on an idle queue); the acceptance gate's owner review of the report is owner-gated.
- Quality flags come from the existing per-clip quality checks when available.
