# Feature Specification: Local Creative Review Experience (F18)

**Feature Branch**: `018-local-creative-review-ui` (work is committed on `main` per owner rule)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "F18: Interactive local review, timeline and preview experience. Make the pipeline usable without hand-editing YAML and manually locating every MP4. Strictly loopback local UI (design review required) showing runs, per-stage state, anchor/contact-sheet previews, bridge clips with QA flags, approve/reject/pending actions wired to the run manifest review.json with CLI parity, a read-only plan view (anchors, prompts, transition timeline, chapters, profile availability, GPU estimate). No hosted server, logins, tracking or cloud upload; no GPU/render actions from the UI; CLI remains authoritative. Tests: UI/CLI parity, storyboard injection, failed/missing media, Host/CSRF/Origin/traversal security, keyboard-accessible controls. Acceptance gate: operator can plan, inspect and approve an Orchid->Butterfly->Phoenix project locally without opening the ComfyUI graph; no involuntary rendering."

## Clarifications

### Session 2026-11-24

Resolved autonomously from ledger F18 and standing owner rules (CLAUDE.md: work autonomously; pause only for GPU scope, downloads, destructive actions or creative approvals):

- Q: Which storyboards appear in the plan view when none are named at startup? → A: All `*.yaml` in `configs/sequences/`, plus any named explicitly.
- Q: What happens if the page and the command line record a decision for the same clip at nearly the same time? → A: Each write is atomic; the last write wins and the page always re-reads the stored decisions.
- Q: Should the experience keep a request log? → A: No request logging to disk (privacy, local-only); errors are shown on the page.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inspect a render run in one place (Priority: P1)

After a render pauses for review, the operator opens a local review page and sees every run, and for a chosen run: its overall status, the state of each stage (anchors, bridges, final movie), the anchor images and contact sheet, each bridge clip playable in place with its automatic quality flags, any blocked-stage reasons, and the final movie when joined — without searching folders for files.

**Why this priority**: Locating and opening each clip by hand is the main friction in today's review gate; nothing else in this feature is useful without it.

**Independent Test**: Point the review experience at a completed Orchid→Butterfly→Phoenix run; all 3 anchors, the contact sheet, both clips with QA status and the final movie are visible and playable.

**Acceptance Scenarios**:

1. **Given** a run awaiting review, **When** the operator opens it, **Then** each stage's state, each anchor image, each bridge clip and its QA flags are shown.
2. **Given** a run whose clip file was deleted from disk, **When** the operator opens it, **Then** that clip is clearly marked "missing" and the rest of the page still works.
3. **Given** a run that stopped on a blocked stage, **When** opened, **Then** the blocking reason is shown.

---

### User Story 2 - Approve or reject clips from the page (Priority: P1)

For each bridge clip, the operator records approved, rejected or pending with an optional note. The decision is stored exactly as the existing command-line review command stores it, and the page reminds the operator that continuing (re-render or join) is done by re-running the same render command.

**Why this priority**: Recording decisions is the second half of the review gate; parity with the command line keeps the command line authoritative.

**Independent Test**: Record a decision through the page and through the command line for the same clip; the stored review records are equivalent and the render command reacts identically.

**Acceptance Scenarios**:

1. **Given** a clip awaiting review, **When** the operator approves it with a note, **Then** the stored decision and note match what the command-line review command would store.
2. **Given** a request naming an anchor, an unknown stage or an invalid decision, **When** submitted, **Then** it is refused and nothing is stored.
3. **Given** a decision request that does not originate from the review page itself, **When** submitted, **Then** it is refused.

---

### User Story 3 - Inspect a storyboard plan before rendering (Priority: P2)

The operator opens a read-only plan view of a storyboard: anchors with generation method, reference parent, chapter, start time and prompts; the transition timeline with frame counts, seconds and candidate counts; whether each required workflow profile is present; and the estimated GPU time from measured history.

**Why this priority**: Planning without reading YAML or a raw plan dump; read-only keeps editing in the existing files for now.

**Independent Test**: Open the plan view of the sample storyboard; anchor times 0 s / 4 s / 8 s, two 65-frame transitions, profile presence and an estimate are shown.

**Acceptance Scenarios**:

1. **Given** a valid storyboard, **When** its plan view is opened, **Then** anchors, transitions, chapters, profile availability and the GPU estimate are displayed.
2. **Given** storyboard text containing markup or script-like content, **When** displayed, **Then** it is shown as inert text.

---

### Edge Cases

- Request arrives with a non-local host name (DNS rebinding attempt): refused.
- Operator tries to start the experience on a non-local network address: refused at startup.
- Requested file is outside the runs folder or not part of the run: not served.
- Manifest or review file is corrupt or absent: page reports the problem without crashing.
- Video seeking requests partial content: served correctly so clips can be scrubbed.
- No runs exist yet: empty-state message.
- Page and command line record a decision for the same clip concurrently: last atomic write wins; a refresh shows the stored state.
- No rendering, cancellation or ComfyUI action exists anywhere in the experience.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The experience MUST be reachable only from the operator's own machine (loopback addresses), refusing to start on any other address and refusing requests with non-local host names.
- **FR-002**: The experience MUST list all runs in the configured runs folder with storyboard name, status and creation time.
- **FR-003**: For a run, it MUST show overall status, each stage's state, anchor images, contact sheet, playable bridge clips with QA status/flags, review decisions and notes, blocked reasons, and the final movie if joined.
- **FR-004**: It MUST mark missing media explicitly while still rendering the rest of the run.
- **FR-005**: Operators MUST be able to record approved / rejected / pending with a note (≤ 500 characters) for bridge stages only; the stored record MUST be equivalent to the command-line review command's.
- **FR-006**: State-changing requests MUST be refused unless they carry the page's per-session form token and, when an origin is declared, a local origin.
- **FR-007**: Only media files referenced by the run's own records and located inside the runs folder MAY be served.
- **FR-008**: All displayed storyboard and manifest text MUST be escaped; pages MUST load no external resources and run no scripts.
- **FR-009**: It MUST provide a read-only plan view (anchors, prompts, chapters, timing, transitions, profile availability, GPU estimate) for every storyboard in the project's sequences folder and any storyboard named at startup.
- **FR-012**: Review writes MUST be atomic (last write wins) and every page view MUST re-read stored decisions, so page and command line never disagree after a refresh.
- **FR-013**: The experience MUST NOT write request logs to disk.
- **FR-010**: It MUST NOT offer any action that renders, cancels or otherwise contacts the local image/video generation service.
- **FR-011**: All controls MUST be operable by keyboard and carry accessible labels.

### Key Entities

- **Run**: one render attempt of a storyboard plan; status, stages, contact sheet, final movie.
- **Stage**: anchor, bridge or final; state, media file, QA status/flags, blocked reason.
- **Review decision**: per bridge stage — decision, note, timestamp; shared with the command line.
- **Plan view**: derived, read-only summary of a storyboard.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The operator can review and approve both clips of the Orchid→Butterfly→Phoenix run from one page in under 2 minutes, without opening a file browser or the generation service.
- **SC-002**: 100% of decisions recorded via the page are equivalent to the command-line review result in parity tests.
- **SC-003**: 100% of the listed hostile cases (foreign host, foreign origin, missing token, path traversal, markup injection, non-local start) are refused or neutralised in tests.
- **SC-004**: Zero generation requests are made by the experience in any test.
- **SC-005**: Pages for a 3-anchor run load in under 1 second locally.

## Assumptions

- A browser on the same machine is acceptable as the display surface (design review in plan.md); no new third-party packages.
- Storyboard and prompt editing stays in the existing YAML/brief files (F21/F22); in-page editing and side-by-side candidate comparison are deferred (F39).
- A single operator; no accounts or logins.
- Default local port 8765, configurable.
- Owner walkthrough of the acceptance gate is a separate owner step.
