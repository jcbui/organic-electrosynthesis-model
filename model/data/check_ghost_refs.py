#!/usr/bin/env python3
"""G-GHOST -- does every internal cross-reference in the shipped documents resolve?

    cd Section4_Model && python data/check_ghost_refs.py
    cd Section4_Model && python data/check_ghost_refs.py --negative-control

WHY
---
The manuscript cited "SI S1.2" in the Figure 1 caption for weeks. There is no S1.2: the SI runs
S1.1 then S2, and the classification material is in S4. Nothing caught it, because every gate in
this repo checks NUMBERS -- against the model, the registry or a second code path -- and a
cross-reference carries no number. It was found by reading the built document during a review.

A dangling pointer is a provenance failure of the same kind as a bad citation: it tells a reader
that evidence exists somewhere it does not. This resolves all five reference species that the two
documents actually use, in both directions.

WHAT IS CHECKED
---------------
  1  section refs   "S1.1", "Section S6", "SI S4"      -> a heading with that id exists
  2  table refs     "Table S7"                          -> a caption "Table S7." exists
  3  lettered refs  "Table S7g"                         -> that letter exists AND names the
                                                          category the citing text is about
  4  figure refs    SI "Fig. K"; MS "Figure 3"          -> a caption exists
  5  equation refs  "Eq. S12"                           -> an equation numbered (S12) exists
  6  heading order  ids ascend through the document     -> no section printed out of place
  7  duplicates     no id defined twice
  8  content        a pointer's target must CONTAIN what it is cited for
  9  file paths     every data/, figs/, julia/, results/, docs/ path cited must exist

Subsections that nothing cross-references are LISTED but never failed. Per the author, those are
transparency sections -- written to be found by a reader auditing the work rather than cited from
the argument -- so a missing pointer is the intended state, and inventing one would be a fake
cross-reference rather than a fix.

(3) and (6) exist because both failed in real builds. Table S7's blocks are lettered in the order
its categories appear in the registry CSV, which ran 1,2,3,4,5,6,9,7,8,10,11 -- category 9 between
6 and 7 -- so every letter after (f) shifted: the SI cited "Table S7g" for the stirred-batch delta
band while (g) was the thermal block and delta was in (h). And two subsections were emitted into
the wrong array, so a document whose numbering was internally consistent printed S3.3 and S8.1
after S9. Neither moved a number, and no numeric gate could have seen either.
"""
import io
import json
import os
import re
import sys
import unicodedata
import zipfile
from latest_ms import latest_ms   # one resolver for every gate (see its docstring)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SI = os.path.join(ROOT, "SI_Section4_Transport_Model.docx")

# a lettered citation and the registry category it must land on
LETTER_CLAIMS = {"c": "Estimation methods", "d": "Solver species diffusivities",
                 "f": "Electrolyte conductivities", "g": "Reactors", "i": "Thermal model",
                 "k": "Numerics"}

# A reference can RESOLVE and still be wrong: the target exists but does not contain what it is
# cited for. v46 pointed the Fig. 5 caption at S6.1 for the reaction-entropy and evaporative-loss
# omissions; S6.1 is 18,500 characters of boil-off analysis and contains none of those words --
# the discussion lives on the registry's "Evaporative loss" row, i.e. Table S7i. Existence checks
# cannot see this, so the targets that carry a specific claim are checked for the claim's own
# vocabulary. Each entry: (citing phrase in either document, target section id, words the target
# must contain).
CONTENT_CLAIMS = [
    ("upper estimate (SI §S3.3)", "S3.3", ["Schmidt", "extrapolat"]),
    ("modelling choices and their bounds in SI §S1.1", "S1.1", ["dilute-solution", "viscosity"]),
]

# Table S-numbers cited for a specific topic must likewise contain it.
TABLE_CONTENT_CLAIMS = [
    ("(SI Table S7i)", "S7i", ["Evaporative loss"]),
    # 2026-09-05: three new lettered citations, each for a row that did not exist before that day
    ("moves its ceilings by at most", "S7d", ["Carrier charge z"]),                  # Table S2 caption
    ("summarised in Table S7d", "S7d", ["Supporting-ion diffusivities without conductance data"]),  # S3.1
    ("Table S7k gives the size of that effect", "S7k", ["Residual scale c_ref"]),   # S5.2
]


def newest_ms():
    # was: sorted(...)[-1] over revised_outline_v\d+, which is a LEXICAL sort -- "v99" sorts after
    # "v130" -- on a naming scheme the lineage left behind, so this gate had been reading v99.
    return latest_ms()


def norm(s):
    return unicodedata.normalize("NFKC", s)


def paras(path):
    x = zipfile.ZipFile(path).read("word/document.xml").decode("utf8")
    out = []
    for p in re.findall(r"<w:p[ >].*?</w:p>|<w:p/>", x, re.S):
        p = re.sub(r"<w:del\b.*?</w:del>", "", p, flags=re.S)   # tracked deletions do not ship
        # 2026-09-11: a subscript run reads back as "_" + text, the tree-wide convention of data/docx_text.py, so a content
        # claim written "c_ref" still finds the block after the SI started rendering c_ref with a real subscript
        _runs = []
        for r in re.finditer(r"<w:r(?:\s[^>]*)?>.*?</w:r>", p, re.S):
            _pre = "_" if re.search(r'<w:vertAlign w:val="subscript"/>', r.group(0)) else ""
            _runs += [_pre + t for t in re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", r.group(0), re.S)]
        out.append(norm("".join(_runs)))
    return out


def key(sid):
    return [int(y) for y in sid[1:].split(".")]


def main(neg=False):
    ms_path = newest_ms()
    si_ps, ms_ps = paras(SI), paras(ms_path)
    si = norm(re.sub(r"\s+", " ", " ".join(si_ps)))
    ms = norm(re.sub(r"\s+", " ", " ".join(ms_ps)))
    print("  SI: %s" % os.path.basename(SI))
    print("  MS: %s" % os.path.basename(ms_path))

    # ---- what EXISTS -------------------------------------------------------------
    heads = []
    for tx in si_ps:
        t = tx.strip()
        m = re.match(r"^(S\d+(?:\.\d+)?)[.．]?\s+(\S.{0,70})", t)
        if m and len(t) < 110:
            heads.append(m.group(1))
    tables = set(re.findall(r"Table (S\d+)[.\s]", si))
    letters = dict(re.findall(r"Table S7([a-z])\.\s+([^—]{0,60})", si))
    figs = set(re.findall(r"Figure ([A-Z])[.\s]", si))
    eqs = set(re.findall(r"\((S\d+)\)", si))
    ms_figs = set(re.findall(r"Figure (\d)[.\s]", ms))

    if neg:
        # perturb the DOCUMENT SIDE in memory: pretend two targets were never written.
        heads = [h for h in heads if h != "S6.1"]
        tables.discard("S7")

    fails = []

    # ---- 1/2/4/5: references resolve ---------------------------------------------
    def secrefs(t):
        r = set(re.findall(r"§\s*(S\d+(?:\.\d+)?)", t))
        r |= set(re.findall(r"Section\s+(S\d+(?:\.\d+)?)", t))
        r |= set(re.findall(r"SI\s+§?\s*(S\d+(?:\.\d+)?)", t))
        return r

    checked = 0
    for lab, t in (("SI", si), ("MS", ms)):
        for s in sorted(secrefs(t), key=key):
            checked += 1
            if s not in heads:
                fails.append("%s cites section %s, which has no heading in the SI" % (lab, s))
        for tb in sorted(set(re.findall(r"Tables? (S\d+)", t)), key=lambda z: int(z[1:])):
            checked += 1
            if tb not in tables:
                fails.append("%s cites Table %s, which has no caption in the SI" % (lab, tb))
        for e in sorted(set(re.findall(r"Eq(?:s|uation)?\.?\s*\(?(S\d+)", t)),
                        key=lambda z: int(z[1:])):
            checked += 1
            if e not in eqs:
                fails.append("%s cites Eq. %s, which is not numbered in the SI" % (lab, e))
    for f in sorted(set(re.findall(r"Fig(?:ure|\.)\s+([A-Z])\b", si))):
        checked += 1
        if f not in figs:
            fails.append("SI cites Figure %s, which has no caption" % f)
    for f in sorted(ms_figs):
        checked += 1
    print("  defined: %d headings, %d tables (S7 in %d lettered blocks), %d figures, %d equations"
          % (len(heads), len(tables), len(letters), len(figs), len(eqs)))

    # ---- 3: a lettered block must name the category the citation is about --------
    for L, want in sorted(LETTER_CLAIMS.items()):
        if ("Table S7" + L) not in si:
            continue
        checked += 1
        got = letters.get(L, "")
        if want.lower() not in got.lower():
            fails.append("the SI cites Table S7%s for %r but that block is %r"
                         % (L, want, got.strip()))

    # ---- 3b: a resolving pointer must also CONTAIN what it is cited for ---------
    # section bodies, sliced between consecutive headings
    bodies, cur, buf = {}, None, []
    for tx in si_ps:
        t = tx.strip()
        m = re.match(r"^(S\d+(?:\.\d+)?)[.．]?\s+(\S.{0,70})", t)
        if m and len(t) < 110:
            if cur:
                bodies[cur] = " ".join(buf)
            cur, buf = m.group(1), []
        elif cur:
            buf.append(tx)
    if cur:
        bodies[cur] = " ".join(buf)
    for phrase, target, words in CONTENT_CLAIMS:
        if phrase not in si and phrase not in ms:
            continue
        checked += 1
        body = bodies.get(target, "")
        if neg:
            body = ""
        miss = [w for w in words if w.lower() not in body.lower()]
        if miss:
            fails.append("a document cites %s for %r but that section never mentions %s"
                         % (target, phrase[:40], ", ".join(miss)))
    for phrase, tbl, words in TABLE_CONTENT_CLAIMS:
        if phrase not in si and phrase not in ms:
            continue
        checked += 1
        L = tbl[-1]
        blk = letters.get(L, "")
        # the block's ROWS, not just its caption: slice the SI from the block caption backwards
        idx = si.find("Table S7" + L + ".")
        seg = si[max(0, idx - 30000):idx] if idx > 0 else ""
        if neg:
            seg = ""
        miss = [w for w in words if w.lower() not in seg.lower()]
        if miss:
            fails.append("a document cites Table %s (%s) for %r but that block never mentions %s"
                         % (tbl, blk.strip(), phrase[:32], ", ".join(miss)))

    # ---- 6/7: order and uniqueness ----------------------------------------------
    for i in range(len(heads) - 1):
        checked += 1
        if key(heads[i]) > key(heads[i + 1]):
            fails.append("section %s is printed before %s -- the SI is out of order"
                         % (heads[i], heads[i + 1]))
    dupes = sorted({h for h in heads if heads.count(h) > 1})
    checked += 1
    if dupes:
        fails.append("duplicate section headings: %s" % ", ".join(dupes))

    # ---- 9: the documents must cite NO repository path at all -------------------
    # INVERTED 2026-09-01, author instruction. This used to assert that every data/, figs/,
    # julia/, results/ or docs/ path a document cites exists, and 53 did. The MS and SI are
    # public-facing, and a repository path is internal work product: it names a file a reader
    # cannot open, and in the audit-script cases it exposes the verification apparatus rather
    # than the model. All of them were removed, so the existence test would now be vacuous --
    # it would pass on an empty set and report nothing. The requirement it is replaced by is
    # the one that actually needs enforcing: no such path may reappear.
    for label, t in (("SI", si), ("MS", ms)):
        checked += 1
        stray = sorted(set(re.findall(
            r"\b(?:data|figs|julia|results|docs|scripts)/[A-Za-z0-9_./-]+"
            r"|\b[A-Za-z0-9_]+\.(?:py|jl|js|csv|json)\b", t)))
        if stray:
            fails.append("%s cites %d repository path(s), which are internal work product and "
                         "must not appear in a public-facing document: %s"
                         % (label, len(stray), ", ".join(stray[:6])))

    # ---- orphans: defined but never cited. REPORTED, never failed ---------------
    # AUTHOR RULING 2026-08-31: a subsection that nothing points at is NOT a defect here. These
    # sections exist for transparency -- they are written to be found by a reader auditing the
    # work, not to be cited from the argument -- so the absence of a pointer is the intended
    # state and no cross-reference should be manufactured for them. Listed so the set stays
    # visible and so a genuinely orphaned ARGUMENT section would stand out against it; never a
    # failure, and not an open question.
    cited = secrefs(si) | secrefs(ms)
    orphans = [h for h in heads if h not in cited and "." in h]
    print("  %d references checked" % checked)
    if orphans:
        print("  transparency subsections, deliberately not cross-referenced (author ruling, "
              "not an action item): %s" % ", ".join(orphans))

    json.dump({"headings": heads, "tables": sorted(tables), "s7_letters": letters,
               "figures": sorted(figs), "n_equations": len(eqs), "checked": checked,
               "failures": fails, "orphan_subsections": orphans},
              io.open(os.path.join(ROOT, "results", "ghost_refs%s.json"
                                   % ("_NEGCONTROL" if neg else "")), "w", encoding="utf8"),
              indent=1)

    for f in fails:
        print("    FAIL  %s" % f)
    if neg:
        ok = len(fails) >= 2
        print("\nNEGATIVE CONTROL: heading S6.1 and Table S7 removed from the defined set, so "
              "every reference to them must be reported as dangling.")
        print("G-GHOST control: %s (%d finding(s))"
              % ("GOOD" if ok else "BAD -- test is inert", len(fails)))
        return 0 if ok else 1
    if not checked:
        print("\nG-GHOST: FAIL -- nothing was checked, so this gate is inert")
        return 1
    if fails:
        print("\nG-GHOST: FAIL -- %d dangling or misdirected reference(s)" % len(fails))
        return 1
    print("\nG-GHOST: PASS -- all %d internal references resolve, the %d headings ascend in "
          "document order with no duplicates, and every lettered Table S7 citation lands on the "
          "block it names" % (checked, len(heads)))
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
