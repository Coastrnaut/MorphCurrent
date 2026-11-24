# Data model — F11

## vram_samples.json
`{schema: 1, label, interval_s, gpu_index, total_mib, samples: [[utc_epoch_s, used_mib], ...]}`

## Sample analysis
`{status: MEASURED|NOT MEASURED, samples, interval_s, max_gap_s, gaps: [[start, end]], coverage_pct, external_baseline_mib, peak_mib, peak_rise_mib, label}`

## Stage row
`{task, kind, method?, width, height, frames?, state, reused: bool, wall_s, exec_s, overhead_s, vram_window_peak_mib?, vram_window_rise_mib?, labels: {time: MEASURED|NOT MEASURED, vram: MEASURED (whole GPU)|NOT MEASURED}}`

## Report
`{schema: 1, run_dir, plan_sha256, stages[], totals {gpu_exec_s, wall_s, reused_stages}, vram {analysis}, provenance {gpu, driver, comfyui, pytorch, models: {file: sha|NOT MEASURED}}, caveats[]}`

## History entry (configs/perf_history.json)
`{run, kind: anchor|bridge, method?, width, height, frames?, exec_s, source}`
