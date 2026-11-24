# Contract: loopback HTTP routes (F18)

All responses carry `Content-Security-Policy: default-src 'self'; img-src 'self'; media-src 'self'; style-src 'unsafe-inline'; form-action 'self'`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`. Any request with a non-loopback `Host` → 403.

| Method | Path | Result |
|---|---|---|
| GET | `/` | 200 runs index + storyboard plan links |
| GET | `/run/<run-name>[?msg=]` | 200 run page; 404 unknown/malformed run |
| GET | `/plan?i=<n>` | 200 read-only plan; 404 bad index; 422 invalid storyboard |
| GET/HEAD | `/media/<run-name>/<token>` | 200/206 with Range support; 404 not in allowlist; 416 bad range |
| POST | `/run/<run-name>/review` (form `csrf, task, decision, note`) | 303 → `/run/<run>?msg=…`; 403 bad token / foreign Origin; 400 non-bridge task or bad decision; 413 > 10 kB |

No other routes. No route renders, cancels or calls ComfyUI.
