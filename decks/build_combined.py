#!/usr/bin/env python3
"""Merge all per-deck PDFs into one combined leave-behind (overview → 01..09 → CIO)."""
import os, glob
from pypdf import PdfWriter, PdfReader
HERE = os.path.dirname(__file__)
order = ["HCLS-Agentic-AI-Suite-Executive-Overview.pdf"] + \
        sorted(glob.glob(os.path.join(HERE, "HCLS-0*-*.pdf"))) + \
        ["HCLS-CIO-Adoption-Review.pdf"]
# normalize to basenames in HERE, de-dup, keep order
seen=set(); files=[]
for f in order:
    b=os.path.basename(f)
    if b not in seen and os.path.exists(os.path.join(HERE,b)): files.append(b); seen.add(b)
w=PdfWriter(); n=0
for b in files:
    for pg in PdfReader(os.path.join(HERE,b)).pages: w.add_page(pg); n+=1
os.makedirs(os.path.join(HERE,"leave-behinds"), exist_ok=True)
out=os.path.join(HERE,"leave-behinds","HCLS-AI-Agent-Suite-COMBINED.pdf")
with open(out,"wb") as fh: w.write(fh)
print(f"wrote {out} ({n} pages, {len(files)} decks)")
