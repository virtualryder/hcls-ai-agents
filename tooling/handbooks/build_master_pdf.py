import re, datetime, markdown
from pathlib import Path
from weasyprint import HTML

DOCS = Path(__file__).resolve().parents[2] / "docs"
md_path = DOCS / "DEPLOYMENT-HANDBOOK.md"
raw = md_path.read_text(encoding="utf-8")

# Drop the H1 (we render a cover instead); keep from first blockquote/intro on.
lines = raw.split("\n")
# remove leading H1 + its '###' subtitle line if present
body_md = []
skip_title = True
for ln in lines:
    if skip_title and (ln.startswith("# ") or ln.startswith("### Deploying")):
        continue
    skip_title = False
    body_md.append(ln)
md_text = "\n".join(body_md)

# checklist glyphs
md_text = re.sub(r"(?m)^- \[ \] ", "- ☐ ", md_text)
md_text = re.sub(r"(?m)^- \[x\] ", "- ☑ ", md_text)

html_body = markdown.markdown(md_text, extensions=["tables","fenced_code","toc","attr_list","sane_lists"])

today = datetime.date.today().strftime("%B %Y")
CSS = """
@page {
  size: Letter; margin: 22mm 18mm 20mm 18mm;
  @bottom-left { content: "HCLS Agentic AI Suite — Deployment Handbook"; font-size: 8pt; color: #8893a5; }
  @bottom-right { content: "Page " counter(page) " of " counter(pages); font-size: 8pt; color: #8893a5; }
  @top-right { content: "Illustrative reference — validate for your environment"; font-size: 7.5pt; color: #b6bfce; }
}
@page :first { margin: 0; @bottom-left { content: ""; } @bottom-right { content: ""; } @top-right { content: ""; } }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; color: #1b2430; font-size: 10.5pt; line-height: 1.5; }
.cover { background: #0E1B33; color: #fff; height: 100vh; padding: 28mm 22mm; page-break-after: always; position: relative; }
.cover .bar { position:absolute; top:0; left:0; right:0; height:10mm; background:#14B8A6; }
.cover .barb { position:absolute; bottom:0; left:0; right:0; height:8mm; background:#0E7C86; }
.cover .eyebrow { color:#14B8A6; font-weight:700; letter-spacing:3px; font-size:11pt; margin-top:34mm; }
.cover h1 { font-family: Georgia, "Times New Roman", serif; font-size: 34pt; line-height:1.15; margin: 8mm 0 0 0; color:#fff; }
.cover .sub { color:#D7E3F4; font-size:13pt; margin-top:8mm; max-width: 150mm; }
.cover .rule { width: 60mm; height: 2px; background:#0E7C86; margin: 12mm 0 8mm; }
.cover .meta { color:#9FB3D1; font-size:10.5pt; }
.cover .tag { position:absolute; bottom:18mm; left:22mm; color:#6f86ab; font-size:9.5pt; font-style:italic; }
h1 { font-family: Georgia, serif; font-size: 19pt; color:#0E1B33; border-bottom: 2px solid #14B8A6; padding-bottom:3pt; margin: 16pt 0 8pt; page-break-after: avoid; }
h2 { font-family: Georgia, serif; font-size: 15pt; color:#0E7C86; margin: 16pt 0 6pt; page-break-before: always; page-break-after: avoid; }
h2:first-of-type { page-break-before: avoid; }
h3 { font-size: 12pt; color:#16294B; margin: 12pt 0 4pt; page-break-after: avoid; }
p, li { font-size: 10.5pt; }
a { color:#0E7C86; text-decoration: none; }
code { font-family: "SFMono-Regular", Consolas, monospace; background:#eef2f7; padding:1px 4px; border-radius:3px; font-size:9pt; color:#0E1B33; }
pre { background:#0E1B33; color:#e7eefc; padding:9pt 11pt; border-radius:6px; font-size:8.6pt; line-height:1.45; overflow-wrap:anywhere; white-space:pre-wrap; page-break-inside: avoid; }
pre code { background:transparent; color:#e7eefc; padding:0; }
table { border-collapse: collapse; width:100%; margin:8pt 0; font-size:9.2pt; page-break-inside: avoid; }
th { background:#0E1B33; color:#fff; text-align:left; padding:5pt 7pt; font-size:9pt; }
td { border:1px solid #d8dee8; padding:5pt 7pt; vertical-align:top; }
tr:nth-child(even) td { background:#f6f8fb; }
blockquote { background:#F1FAFF; border-left:4px solid #14B8A6; margin:8pt 0; padding:6pt 12pt; color:#16294B; font-size:9.8pt; page-break-inside: avoid; }
blockquote p { margin:3pt 0; }
img { max-width:100%; height:auto; display:block; margin:8pt auto 2pt; border:1px solid #d8dee8; border-radius:5px; page-break-inside: avoid; }
em { color:#5B6B82; font-size:8.6pt; }
ul, ol { margin:5pt 0 5pt 0; padding-left: 16pt; }
li { margin:2pt 0; }
hr { border:none; border-top:1px solid #dce2ea; margin:12pt 0; }
"""

cover = f"""
<div class="cover">
  <div class="bar"></div><div class="barb"></div>
  <div class="eyebrow">DEPLOYMENT HANDBOOK</div>
  <h1>HCLS Agentic AI Suite<br/>Deploying an Agent on AWS</h1>
  <div class="sub">Step-by-step, console and CLI — from an empty AWS account to a running,
  governed, human-gated agent. Worked example: Agent 02 — Pharmacovigilance, with a per-agent appendix for all eight.</div>
  <div class="rule"></div>
  <div class="meta">Systems-Integrator field &amp; delivery reference &nbsp;·&nbsp; {today}</div>
  <div class="tag">Illustrative reference — figures are mockups, not actual AWS screenshots. Validate for your environment.</div>
</div>
"""

doc = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{cover}{html_body}</body></html>"
out = Path(__file__).resolve().parents[2] / "HCLS-Deployment-Handbook.pdf"
HTML(string=doc, base_url=str(DOCS)).write_pdf(str(out))
print("WROTE", out, out.stat().st_size, "bytes")
