"""One canonical way to read the ASSERTED text out of a tracked-changes .docx.

    from docx_text import asserted_text
    t = asserted_text("...docx")          # NFKC-normalised, tracked deletions removed

WHY THIS MODULE EXISTS
----------------------
Three gates each rolled their own regex for stripping <w:del> blocks, and two of them got it
wrong in the same way. `<w:del\\b` matches a SELF-CLOSING `<w:del .../>` -- which is how Word
marks a tracked-deleted PARAGRAPH MARK inside w:pPr/w:rPr -- and the lazy `.*?</w:del>` then
swallows every run up to the first real </w:del>. On the v28 manuscript that hid 1,849 characters
of asserted text from `check_ms_numbers.py` and `check_ms_derived.py`, including the ENTIRE
Figure 2 caption. Both gates advertised whole-document coverage and reported PASS.

Rather than fix the regex in three places and hope, this module parses the XML STRUCTURALLY with
ElementTree -- which cannot confuse a self-closing element with an open tag, because the parser
knows the difference -- and then cross-checks that result against the corrected regex. If the two
disagree the module RAISES, because a disagreement means one of them is wrong and neither gate
has any business reporting PASS until it is known which.
"""
import html
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
RE_DEL_CORRECT = re.compile(r"<w:del (?:[^>]*[^/])?>.*?</w:del>", re.S)
# `<w:t[^>]*>` also matches <w:tab .../>, <w:tabs>, <w:tblPr> ... -- the same sloppy-tag-
# boundary mistake as the <w:del> bug, one element along. Require whitespace or ">" after w:t.
RE_WT = r"<w:t(?:\s[^>]*)?>(.*?)</w:t>"


def _is_sub(run):
    va = run.find(W + "rPr/" + W + "vertAlign")
    return va is not None and va.get(W + "val") == "subscript"


def _by_tree(xml_bytes):
    """Structural walk: drop every real <w:del> ELEMENT, concatenate the remaining <w:t>.

    2026-09-11: a run formatted as a SUBSCRIPT reads back as "_" + its text (i + subscript "lim" -> "i_lim"), the spelling
    every gate phrase and data/ms_phrases.py use; the writers (apply_v81_fixes.py, make_si.js) render that spelling as a
    subscript run through data/subscripts.py, so reader and writers are inverses (see subscript_tokens.json)."""
    root = ET.fromstring(xml_bytes)
    for parent in root.iter():
        for child in list(parent):
            if child.tag == W + "del":
                parent.remove(child)          # a self-closing <w:del/> has no <w:t> to lose
    out = []
    for run in root.iter(W + "r"):
        pre = "_" if _is_sub(run) else ""
        for e in run.findall(W + "t"):
            out.append(pre + (e.text or ""))
    return "".join(out)


def _by_regex(xml_text):
    """Same extraction by regex: drop <w:del> blocks, then take <w:t> CONTENT only.

    Taking <w:t> content specifically -- rather than stripping all tags -- is what makes this
    comparable to the structural walk. Stripping every tag also sweeps up w:instrText, field
    codes and Zotero JSON, which the tree path never sees; and the raw XML carries escaped
    entities (&amp;) that ElementTree has already resolved.
    """
    body = RE_DEL_CORRECT.sub("", xml_text)
    out = []
    for run in re.finditer(r"<w:r(?:\s[^>]*)?>.*?</w:r>", body, re.S):
        pre = "_" if re.search(r'<w:vertAlign w:val="subscript"/>', run.group(0)) else ""
        for m in re.findall(RE_WT, run.group(0), re.S):
            out.append(pre + html.unescape(m))
    return "".join(out)


RE_SUB_RUN = re.compile(r'(<w:r(?:\s[^>]*)?>(?:(?!</w:r>).)*?<w:vertAlign w:val="subscript"/>(?:(?!</w:r>).)*?<w:t(?:\s[^>]*)?>)', re.S)


def mark_subscripts(xml_text):
    """For a gate that strips tags itself (re.sub("<[^>]+>", "", xml)): insert "_" at the start of every subscript run's text
    FIRST, so the stripped text carries the same "_" + text spelling asserted_text returns (2026-09-11 convention)."""
    return RE_SUB_RUN.sub(r"\1_", xml_text)


def asserted_text(path, part="word/document.xml", _check=True):
    raw = zipfile.ZipFile(path).read(part)
    tree = _by_tree(raw)
    if _check:
        rx = _by_regex(raw.decode("utf8"))
        # Compare on non-whitespace only: the regex path also picks up text from parts of the
        # XML that carry no <w:t> semantics, and whitespace runs differ harmlessly.
        a = re.sub(r"\s+", "", tree)
        b = re.sub(r"\s+", "", rx)
        if a != b:
            n = min(len(a), len(b))
            i = next((k for k in range(n) if a[k] != b[k]), n)
            raise AssertionError(
                "docx_text: the structural walk and the corrected regex DISAGREE at offset %d "
                "(tree %d chars, regex %d chars). One of them is wrong; no gate reading this "
                "document should report PASS until it is known which.\n  tree : ...%r...\n"
                "  regex: ...%r..." % (i, len(a), len(b), a[max(0, i - 60):i + 60],
                                       b[max(0, i - 60):i + 60]))
    return unicodedata.normalize("NFKC", tree)


def naive_would_lose(path, part="word/document.xml"):
    """How much asserted text the BUGGY `<w:del\\b...` regex hides. 0 on a clean document."""
    x = zipfile.ZipFile(path).read(part).decode("utf8")
    body = re.sub(r"<w:del\b.*?</w:del>", "", x, flags=re.S)
    naive = "".join(html.unescape(m) for m in re.findall(RE_WT, body, re.S))
    return len(_by_regex(x)) - len(naive)


if __name__ == "__main__":
    import os
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    import glob
    d = os.path.join(os.path.dirname(os.path.dirname(here)), "MS Drafts")
    cands = glob.glob(os.path.join(d, "revised_outline_v*_RCE_Perspective_JCB_tracked.docx"))
    ms = max(cands, key=lambda p: int(re.search(r"_v(\d+)_", os.path.basename(p)).group(1)))
    print("self-test on %s" % os.path.basename(ms))
    t = asserted_text(ms)
    print("asserted text: %d chars (structural walk, cross-checked against the regex)" % len(t))
    print("the buggy regex would hide: %d characters" % naive_would_lose(ms))
    probe = "Reactor architecture organized by diffusion-layer thickness"
    print("Figure 2 caption visible: %s" % (probe in t))
    sys.exit(0 if probe in t else 1)
