# Data model — F02

## CapabilityContract (constant `CAPABILITY_CONTRACTS`)
| capability | required roles | output kind |
|---|---|---|
| text_to_image | positive_prompt, seed | image |
| reference_edit | positive_prompt, seed, reference_image | image |
| wan_flf2v | start_image, end_image, positive_prompt, seed, length | video |

## InspectionReport (JSON)
- `ok` (no errors), `format: "api"`, `graph_sha256`, `node_count`
- `nodes[]`: `{id, class_type, cloud, output_node}`
- `cloud_nodes[]`
- `models[]`: `{node_id, class_type, input, value, installed: true|false|null}` (`null` when no object_info)
- `errors[]`, `warnings[]` (from `validate_graph` + model checks)
- `candidates[]`: `{role_hint, node_id, input, class_type, current, status: "candidate"}`
