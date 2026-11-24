# CLI contract — `morphcurrent workflow-inspect`

```
python -m morph_studio.cli workflow-inspect EXPORT.json [--url URL | --object-info FILE | --offline]
```
- Stdout: InspectionReport JSON. Exit 0 when `ok`, 4 when errors, 2 on unreadable/non-API input.
- Network: at most `GET /object_info` (none with `--object-info` or `--offline`). Writes no files.
- `--offline`: structural report only; model `installed: null`.
