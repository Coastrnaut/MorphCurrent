# Drafting sequences and prompts in Claude Desktop sessions

MorphCurrent does **not** run a language model for drafting (owner decision, 2026-11-24). All creative
text is pre-drafted in Claude Desktop sessions and then checked and planned locally. Claude sessions
see only text: never send generated images, videos or private media. All image and video inference
stays on the local ComfyUI.

## What a drafting session produces

| File | Contents | Next local step |
|---|---|---|
| `configs/briefs/<name>.yaml` | `title`, ordered `scenes` (`subject`, optional `details`, `morph` hint), `duration_s`, `bpm`, `style_pack`, `seed`, optional `drafted_by` | `draft-check`, then `brief-plan --out configs/sequences/<name>.yaml` |
| `configs/sequences/<name>.yaml` | a full storyboard (anchors with prompts, transitions with choreography) when the brief templates are not enough | `draft-check`, then `render --dry-run` |

Briefs are preferred: `brief-plan` computes valid Wan lengths (`L = 4n+1`), seeds, reference-edit
lineage and choreography, so the session only has to write good scene text.

## Rules for drafted text

- Describe **what is seen**: subject, material, form, lighting, framing. One subject per scene,
  centered, similar scale to its neighbours.
- Each `morph` hint describes a **physical, continuous** transformation from this scene's subject
  into the next (which part becomes which part), not a cut, fade or dissolve.
- Keep consecutive scenes compatible: same framing, background and scale, so the next anchor can be
  a reference edit of the previous one.
- Never name models, checkpoints, LoRAs, model files, ComfyUI nodes, samplers, CFG/denoise values
  or workflows, and never include URLs. `draft-check` rejects them. Model and workflow choices live
  in the hash-pinned profiles, not in creative text.
- Keep each prompt under about 600 characters; put style in a style pack (`configs/styles/`), not
  in every prompt.
- Engineering facts must be correct (F33). Keep artistic metaphor separate from factual claims.
- Record provenance with `drafted_by: "Claude Desktop session YYYY-MM-DD"` in briefs.

## Session prompt (paste into Claude Desktop)

> Draft a MorphCurrent brief at `configs/briefs/<name>.yaml` for: <idea, duration, tempo>.
> Use the `engineering-noir` style pack. Write N scenes, each with a concrete centered subject and a
> `morph` hint describing a continuous physical transformation into the next scene. Follow
> `docs/DRAFTING.md`: no model, node, workflow or URL text. Set `drafted_by`. Then run
> `draft-check` and `brief-plan` and show me the preview. Do not render.

## Validate, plan, approve

```powershell
.venv\Scripts\python.exe -m morph_studio.cli draft-check configs\briefs\engineering-pilot.yaml
.venv\Scripts\python.exe -m morph_studio.cli brief-plan configs\briefs\engineering-pilot.yaml --out configs\sequences\engineering-pilot.yaml
.venv\Scripts\python.exe -m morph_studio.cli draft-check configs\sequences\engineering-pilot.yaml
.venv\Scripts\python.exe -m morph_studio.cli render configs\sequences\engineering-pilot.yaml --dry-run
```

`draft-check` exits 0 when there are no errors (warnings, such as missing choreography
correspondences or an `independent_t2i` anchor, are advisory) and 3 when there are errors. The owner
reviews the drafted text and the dry-run before any `--confirm-gpu` render.
