# Leave-behinds

Single-file PDF exports for emailing without PowerPoint.

- **`HCLS-AI-Agent-Suite-COMBINED.pdf`** — every deck in one file: the executive overview, all nine
  per-agent decks (01–09), and the CIO/CISO adoption-review board deck. The complete suite story in
  one attachment.

Per-deck PDFs live in `decks/` alongside the editable `.pptx` sources. Regenerate with
`make decks` (sources) and `make decks-pdf` (PDFs); the combined file rebuilds from those.
