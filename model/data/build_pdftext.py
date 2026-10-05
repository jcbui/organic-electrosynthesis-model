#!/usr/bin/env python3
"""Build results/pdftext/*.txt -- the text caches G-COND reads instead of the PDFs.

    cd Section4_Model && python data/build_pdftext.py            # build what is missing/stale
    cd Section4_Model && python data/build_pdftext.py --check    # report only, write nothing

WHY THIS EXISTS
---------------
The caches were hand-made and NOTHING produced them. That is how the BASF patent
(`5507922.pdf`) came to sit at 5 bytes while its own conc_provenance DESCRIBED a 300 dpi tesseract
pass: the pass had been run once, by hand, and its output was never written anywhere. From
G-COND's side an unwritten cache and a genuine scan look identical -- both are "no text" -- so the
row was reported as unreadable when the text was merely absent from disk.

A cache with no generator is a hand-made artifact that cannot be checked, which is exactly the
category G-REGEN exists to close. This makes it reproducible.

TWO KINDS OF PDF
----------------
Most carry a text layer and PyMuPDF extracts it directly. A scan carries none, and is OCRed:
rendered page by page at 300 dpi and read with tesseract. OCR output is marked with a header
saying so, because a transcription is not the document -- and digits are what OCR gets wrong.
That warning is not decorative: the patent's flow rate was carried as 900 L/h and reads 200.
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TXT = os.path.join(ROOT, "results", "pdftext")
PDFD = os.path.join(os.path.dirname(ROOT), "papers for model", "concentrations")
DPI = 300
OCR_HEADER = (
    "[OCR TEXT LAYER. The source PDF is a scan and carries no text layer, so this file was produced\n"
    "by rendering every page with PyMuPDF and running tesseract on each. It is a transcription aid,\n"
    "not a substitute for reading the document. Digits in a scan are exactly what OCR gets wrong\n"
    "most often, so any number taken from here must be confirmed against the page image before it\n"
    "is carried. Rebuild with data/build_pdftext.py.]\n\n")
MIN_TEXT = 500          # below this a PDF is treated as a scan


def extract(pdf_path):
    """(text, was_ocred). Direct extraction where there is a text layer, OCR where there is not."""
    import pymupdf
    d = pymupdf.open(pdf_path)
    direct = "".join(d[i].get_text() for i in range(len(d)))
    if len(direct) >= MIN_TEXT:
        return direct, False
    if not shutil.which("tesseract"):
        return None, False
    tmp = tempfile.mkdtemp(prefix="pdftext_")
    try:
        parts = []
        for i in range(len(d)):
            png = os.path.join(tmp, "p%03d.png" % i)
            d[i].get_pixmap(dpi=DPI).save(png)
            out = os.path.join(tmp, "p%03d" % i)
            subprocess.run(["tesseract", png, out, "--psm", "3", "-l", "eng"],
                           capture_output=True)
            f = out + ".txt"
            if os.path.exists(f):
                parts.append(io.open(f, encoding="utf-8", errors="replace").read())
        return OCR_HEADER + "".join(parts), True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(check=False):
    if not os.path.isdir(PDFD):
        sys.exit("no %s" % PDFD)
    os.makedirs(TXT, exist_ok=True)
    built = stale = ok = failed = 0
    for f in sorted(os.listdir(PDFD)):
        if not f.lower().endswith(".pdf"):
            continue
        dest = os.path.join(TXT, os.path.splitext(f)[0] + ".txt")
        have = io.open(dest, encoding="utf-8", errors="replace").read() if os.path.exists(dest) else ""
        text, ocred = extract(os.path.join(PDFD, f))
        if text is None:
            print("  %-42s NEEDS OCR but tesseract is not installed" % f[:42]); failed += 1; continue
        # OCR is deterministic for a given input, so a rebuilt cache should match byte for byte.
        if have.strip() == text.strip():
            ok += 1; continue
        tag = "OCR" if ocred else "text layer"
        if check:
            print("  %-42s STALE (%s, %d chars on disk -> %d)" % (f[:42], tag, len(have), len(text)))
            stale += 1; continue
        io.open(dest, "w", encoding="utf-8").write(text)
        print("  %-42s built (%s, %d chars)" % (f[:42], tag, len(text)))
        built += 1
    print("\n  %d already correct, %d %s, %d could not be built"
          % (ok, stale if check else built, "stale" if check else "written", failed))
    if check:
        # G-PDFTEXT. A cache that no longer matches its PDF is not cosmetic: G-COND reads the
        # cache, not the document, so a lossy or unbuilt one silently downgrades a row -- and on
        # 2026-08-31 a dropped sentence caused a correct concentration to be overwritten with a
        # wrong one. Rebuild rather than reason about it.
        if stale or failed:
            print("\nG-PDFTEXT: FAIL -- %d cache(s) no longer match their PDF and %d could not be "
                  "built. G-COND reads these, not the PDFs, so a stale cache changes what the "
                  "provenance gate can see. Run this script without --check." % (stale, failed))
            return 1
        print("\nG-PDFTEXT: PASS -- every text cache matches what its PDF yields today")
        return 0
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(check="--check" in sys.argv))
