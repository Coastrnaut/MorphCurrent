# Feature Specification: Seam-safe movie join and optional soundtrack

**Logical ledger ID**: F09 · **Feature Directory**: `specs/009-seam-safe-join` · **Created**: 2026-11-24 · **Status**: Draft

**Input**: "F09 Exact shared-anchor seam inspection, safe FFmpeg joining and optional owner-supplied soundtrack"

## Gap analysis
| Exists | Gap |
|---|---|
| `stitcher.build_join_command`: concat, drops first frame of later clips, requires a `verified_matching_endpoints` boolean, never overwrites, `-an` | Nothing actually verifies the seam; no output frame-count check; no audio path; no `.part` output |

## User Scenarios & Testing *(mandatory)*
### US1 - Verified seam join (P1)
**Acceptance**: for consecutive clips the last decoded frame of clip *i* is compared with the first decoded frame of clip *i+1* (and both with anchor B when given); only if they match within tolerance and fps/size agree, the duplicate is dropped and clips are concatenated without xfade; output frames = Σ L − (n−1) (65+65 → 129) at the generation fps; written via `.part` then renamed.
### US2 - Mismatch is blocked (P1)
**Acceptance**: a B→C clip whose first frame differs from A→B's last frame → join refused with the measured difference; nothing written.
### US3 - Optional licensed audio (P2)
**Acceptance**: without audio the MP4 has no audio stream; with an owner-supplied local file the audio is offset by `beat_offset_seconds`, cut to the video duration (`frames/fps`) and muxed as AAC; video frames unchanged. Remote URLs refused.

### Edge Cases
Clips with different fps or size → refused. Single clip → copied through verification only (no join). Audio shorter than video → reported; video length is authoritative.

## Requirements *(mandatory)*
- **FR-001** Seam check on decoded frames (64×36 gray mean abs diff ≤ 8 levels) for every boundary; recorded per seam.
- **FR-002** Join uses the existing concat/trim command; no `xfade`/blend filters.
- **FR-003** Output verified by ffprobe: frame count = Σ L − (n−1), fps, size.
- **FR-004** Audio is opt-in, must be a local existing file, `-t` = video duration, AAC.
- **FR-005** Output never overwrites; `.part` + rename.

## Success Criteria *(mandatory)*
- **SC-001** Synthetic 2-clip test yields exactly the expected unique frames with correct first/last frames.
- **SC-002** Mismatched seam refused in 100% of tests.
- **SC-003** Video-only and audio variants both tested.

## Assumptions
Tolerance 8 levels on 64×36 gray accounts for H.264 re-encoding of the same anchor in two clips; to be tightened after real Wan seams are measured (GPU-blocked).
