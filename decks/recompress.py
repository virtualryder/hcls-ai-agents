#!/usr/bin/env python3
"""Deflate-recompress generated decks (pptxgenjs writes uncompressed STORED ZIPs)."""
import glob, os, zipfile

here = os.path.dirname(__file__)
for f in glob.glob(os.path.join(here, "HCLS-*.pptx")):
    tmp = f + ".tmp"
    with zipfile.ZipFile(f) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
        for item in zin.infolist():
            zout.writestr(item, zin.read(item.filename))
    os.replace(tmp, f)
    print("recompressed", os.path.basename(f))
