# Research: F38 titles and overlays

## R1 Text escaping in FFmpeg drawtext
- Decision: write each overlay's text to `tNN.txt` and the font to `font.ttf` in a temp dir; run FFmpeg with that dir as working directory; the filter uses `textfile=tNN.txt:expansion=none` and `fontfile=font.ttf`.
- Rationale: avoids filtergraph quoting of colons, quotes, percent signs, backslashes and Windows drive letters; the filter string is identical across runs, so it can be part of the recipe checksum.
- Alternatives: inline `text=` with multi-level escaping (fragile); absolute temp paths (non-deterministic filter).

## R2 Fades
- Decision: `alpha` expression `if(lt(t,S),0,if(lt(t,S+F),(t-S)/F,if(lt(t,E-F),1,if(lt(t,E),(E-t)/F,0))))` with `enable=between(t,S,E)`; times printed with 3 decimals.
- Alternatives: a fade filter on a separate overlay stream (more complex graph).

## R3 Timing reference
- Decision: anchor time = anchor frame / generation fps (anchor frames from the frame-locked timeline); an act title uses the first anchor whose chapter equals the act id; act titles that would start inside the opening card are deferred to the card's end (the film's first act starts at 0 s).
- End card: `duration − d`; duration probed from the movie at render time, or `(last anchor frame + 1) / fps` when only checking.

## R4 Width estimate and safe areas
- Decision: width ≈ 0.55 × size × characters; 16:9 title-safe = central 90 % of width and height; 9:16 crop width = round(H·9/16), safe = central 90 % of the crop; shrink the size to the largest fitting value ≥ 0.035·H, else flag.

## R5 Encoding
- Decision: `libx264 -crf 18 -preset medium -pix_fmt yuv420p`, map video and optional audio, audio copied, input frame timing kept (`-fps_mode passthrough`). Frame count and duration verified with `media.probe_video` (duration within one frame).

## R6 Boundary proposals
- Decision: boundaries are the first anchors of acts 2..n; section starts are sync-plan anchors with `event == "section"`; nearest within ±window (ties → earlier); proposal only.
