# Implementation Plan: Style packs and asset collections

**Branch**: none (`main`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary
New `styles.py` (`StylePack` model, `load_pack`, `resolve_pack`, `pack_sha256`, `style_text`, `apply_override`, `check_assets`); schema: `Style.pack`, `Anchor.style_override`; `dag.compile_plan` uses packs when set; CLI `style-list/show/check`. Example packs: `configs/styles/engineering-noir.yaml` (+ `engineering-noir-power.yaml` extending it) for the F31–F40 film.

## Constitution Check
I (no silent prompt rewriting; advisory size) PASS · II (assets local, gitignored library) PASS · IV (pack hash in plan identity) PASS · VII (no-pack storyboards unchanged) PASS.

## Complexity Tracking
None.
