# Handbook tooling

Generates the console mockups and the deployment-handbook PDFs from source, so the
collateral regenerates automatically when the agent profiles, template, CSS, or
figures change. Driven by the repo-root `Makefile`.

| File | Produces |
|---|---|
| `gen_console.py` | The 7 generic AWS-console mockups → `docs/assets/console/*.png` (+ SVG) |
| `agent_handbooks.py` | Per-agent figures → `docs/assets/console/<agent>/` and the 8 tailored PDFs → `deliverables/agent-handbooks/`. **Agent profiles live in the `PROFILES` list here.** |
| `build_master_pdf.py` | The suite master PDF → `HCLS-Deployment-Handbook.pdf` (from `docs/DEPLOYMENT-HANDBOOK.md`) |
| `handbook_template.md` | The agent-agnostic handbook body (placeholders filled per profile) |
| `handbook.css` | Shared print stylesheet (cover, header/footer, tables, figures) |

## Use

```bash
make install      # one-time: pip install the toolchain (needs libpango/cairo)
make handbooks    # regenerate figures + master PDF + all 8 agent PDFs
make figures      # just the console mockups
make master       # just the suite master handbook PDF
make agent-handbooks   # just the 8 per-agent PDFs
make deck         # export the executive deck PPTX -> PDF (needs LibreOffice)
make clean-handbooks
```

`make` tracks dependencies: edit an agent profile in `agent_handbooks.py` (or the
template/CSS) and `make handbooks` rebuilds only what changed. To add/adjust an
agent, edit the `PROFILES` list and re-run `make handbooks`.
