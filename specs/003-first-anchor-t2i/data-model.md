# Data model — F03

## AnchorRequest
`profile` (path), `method` ∈ {`text_to_image`, `independent_t2i`, `reference_edit`}, `positive_prompt` (required, non-empty), `negative_prompt` (optional), `seed` (int ≥ 0, required), `width`/`height` (optional), `reference_image` (path; required iff `reference_edit`, forbidden otherwise), `label` (optional anchor id).

## Anchor job record (`job.json`, shared schema with bridge)
`schema`, `job_id`, `kind: "anchor_image"`, `method`, `label`, `state` (planned → uploaded → validated → submitting → submitted → completed → downloaded → verified | failed | cancelled), `request`, `profile`, `capability`, `workflow`, `workflow_sha256`, `patched_graph_sha256`, `inputs` (reference role → path, sha256, upload_name), `values`, `models`, `model_sha256: "NOT RECORDED"`, `prompt_id`, `comfyui`, `outputs[]`, `image {local_path, sha256, bytes, format, width, height}`, `parent {sha256} | null`, `verification`, `error`, `events[]`.
