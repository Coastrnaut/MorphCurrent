# Research: F23

## R1 Camera control in the installed workflow
- **Finding**: `workflows/03_wan22_flf2v.json` contains UNETLoader ×2, CLIPLoader, VAELoader, LoadImage ×2, CLIPTextEncode ×2, ModelSamplingSD3 ×2, WanFirstLastFrameToVideo, KSamplerAdvanced ×2, VAEDecode, CreateVideo, SaveVideo — no camera-control node or input.
- **Decision**: camera moves are prompt text only, labelled "prompt-only approximation"; `control: graph` is refused when no node whose class name contains "Camera" exists in the pinned graph.
- **Alternatives**: camera LoRAs / Uni3C / camera embedding nodes — need new model installs and owner consent (F27).

## R2 Satisfiability metric
- **Decision**: F12 `image_geometry` centroid/extent; r = mean(end.extent / start.extent); thresholds per spec Clarifications; unreliable masks (`mask_unreliable`, `subject_too_small`) → "unknown — review".
- **Rationale**: FLF2V fixes both endpoints, so any camera motion the model invents must reconcile with them; geometry is already measured for anchors.

## R3 Amount wording
- **Decision**: amount < 0.10 "slightly", < 0.25 "moderately", else "strongly", plus "about N% of the frame"; deterministic.

## R4 Crops
- **Decision**: 16:9 = full frame; 9:16 = full-height centre crop of width H·9/16; safe area = crop inset 5% each side; subject box = centroid ± extent/2.
