---
name: debug-node
description: Diagnose ComfyUI API graph binding failures and unavailable nodes without inventing node IDs.
---
# Debug node

1. Capture non-secret API error payload and `/object_info` for the relevant class.
2. Compare actual API-exported graph `class_type` and input names with `configs/profiles` bindings.
3. Identify missing models, custom nodes, version changes or filename mismatches.
4. Re-export working graph from local ComfyUI if necessary; never fabricate a graph.
5. Add a regression test for the failure and document verification in `PROGRESS.md`.

Windows-only: invoke existing Python .py helpers in scripts/windows/; do not use WSL, .ps1 or .sh. Keep ComfyUI's Python separate from the controller venv. Spec Kit generated scripts must use --script py.
