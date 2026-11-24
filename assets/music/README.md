# Music assets

Only owner-approved, **public-domain or CC0** recordings are committed here, each with a JSON provenance record (source URLs, licence of the recording *and* the composition, original file hash, processing command, approval). Everything else stays out of Git.

| File | Work | Performer | Licence | Length | Provenance |
|---|---|---|---|---|---|
| `mozart-symphony-40-i-molto-allegro-musopen.opus` | Mozart, Symphony No. 40 in G minor, K. 550 — I. Molto allegro | Musopen Symphony (2012) | Public domain (recording PD-author, composition PD-old) | 5:58.8 | [`mozart-symphony-40-i-molto-allegro-musopen.json`](mozart-symphony-40-i-molto-allegro-musopen.json) |

No attribution is legally required for public-domain recordings; a courtesy credit is suggested in each provenance file.

Use in a storyboard:

```yaml
audio:
  file: assets/music/mozart-symphony-40-i-molto-allegro-musopen.opus
  licensed: true
```

Verify a file against its record: `certutil -hashfile <file> SHA256` (Windows) and compare with `sha256` in the JSON.
