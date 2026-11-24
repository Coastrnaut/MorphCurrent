# Data model: F35

## Lineage config (`configs/film/lineage.yaml`)
`depth_limit` int; `drift` {colour_max, sharpness_min_ratio, centroid_max, scale_ratio [lo, hi]}.

## Lineage entry
`anchor`, `chapter`, `root`, `depth`, `chain` [root … anchor]. Report: `entries`, `per_act_max` {act: depth}, `max_depth`, `over_limit` [anchor], `limit`.

## Drift point
`anchor`, `act`, `reference`, `depth`, `colour_distance`, `sharpness_ratio`, `centroid_offset`, `scale_ratio`, `flags` [colour | sharpness | centroid | scale | unreliable]. Report: `points`, `missing`, `ok`.

## Proposal
`anchor`, `reasons` [depth | drift:<flags>], `invalidated_anchors`, `invalidated_bridges`; report `proposals`, `max_depth_after`, `out` (when written).

## Shared-anchor result
`bridge`, `endpoint` start | end, `expected`, `used`, `status` match | mismatch | unchecked.
