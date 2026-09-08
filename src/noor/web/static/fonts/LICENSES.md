# Typefaces

All four faces are licensed under the **SIL Open Font License, Version 1.1**, which
permits bundling and self-hosting. They are committed here rather than fetched at
runtime because `docs/frontend_ssot.md` §12 forbids a CDN.

| File | Family | Weight | Subset | Upstream |
|---|---|---|---|---|
| `EBGaramond-Medium.woff2` | EB Garamond | 500 | latin | https://fonts.google.com/specimen/EB+Garamond |
| `DMSans-Regular.woff2` | DM Sans | 400 | latin | https://fonts.google.com/specimen/DM+Sans |
| `DMSans-SemiBold.woff2` | DM Sans | 600 | latin | https://fonts.google.com/specimen/DM+Sans |
| `NotoNaskhArabic-Regular.woff2` | Noto Naskh Arabic | 400 | arabic | https://fonts.google.com/noto/specimen/Noto+Naskh+Arabic |

Each file was downloaded from the `woff2` URL Google Fonts' `css2` endpoint returns for
that family and weight, already subset to the range in the table. The full licence text
travels with each family in its upstream repository under `OFL.txt`.

Replacing a file means replacing it here and running `pytest tests/web/` — nothing else
in the tree names these faces except `static/noor.css`.
