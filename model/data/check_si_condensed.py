#!/usr/bin/env python3
"""G-SICOND -- is the condensed (pre-review) SI a faithful subset of the detailed SI?

    cd Section4_Model && python data/check_si_condensed.py
    cd Section4_Model && python data/check_si_condensed.py --negative-control

WHY
---
On 2026-09-14 the author asked for a second, much shorter SI for submission: "the modeling details,
all of the parameters and their provenance, and how all the figures were made", with provenance
printed as "Source, Page Number, Table", keeping the detailed SI for reviewer questions. make_si.js
builds it (SI_MODE=condensed) from the detailed SI's own elements. A shorter document is only safe
if it cannot say anything the detailed one does not, cannot drop an equation or a parameter, and
cannot mis-number a citation while renumbering its reference list. This gate checks exactly that,
against the built .docx files rather than the generator.

CHECKS
------
 1 headings     the condensed SI carries the detailed SI's headings, same text, same order
 2 equations    every numbered equation of the detailed SI is present with identical content
 3 prose        every condensed sentence is either verbatim in the detailed SI or new; a new
                sentence may carry no number the detailed SI does not print
 4 citations    in every verbatim sentence the cited works are the works the detailed SI cites
                there (compared through each document's own reference list, not by number)
 5 Table S7     every detailed Table S7 row is present with identical parameter, value, units,
                state and equation; its short source names only a surname/work, year and
                page/table tokens that occur in that row's registry citation and locator
 6 Table S2     50 rows, the first twelve columns identical; each source cell cites the same
                exemplar work, and its page/table tokens occur in that row's concentration provenance
 7 tables       Tables S1, S3-S6, S8, S9 and the catalyst table carry the detailed numeric columns
 8 xrefs        every section, table and equation the condensed SI points to exists in it
 9 manuscript   every SI section and table the latest manuscript cites exists in the condensed SI
10 references   numbered 1..N, every entry cited, every entry text present in the detailed list
11 fresh        the condensed .docx is what make_si.js (SI_MODE=condensed) produces today
"""
import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import zipfile
from xml.etree import ElementTree as ET
from latest_ms import latest_ms as _shared_latest_ms   # aliased: a local def of the same
# name below would shadow the import and recurse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DET = os.path.join(ROOT, "SI_Section4_Transport_Model.docx")
CON = os.path.join(ROOT, "SI_Section4_Transport_Model_condensed.docx")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
SUP0, SUP1 = "\x01", "\x02"


# ---------------------------------------------------------------------------------------------
def read_docx(xml_bytes):
    """Body in order: paragraphs (with superscript runs wrapped in SUP0/SUP1, subscript runs as
    "_" + text, OMML as its text) and tables (rows of cell strings, same run convention)."""
    root = ET.fromstring(xml_bytes)
    body = root.find(W + "body")

    def runs_text(node):
        out = []
        for el in node.iter():
            if el.tag == W + "r":
                va = el.find(W + "rPr/" + W + "vertAlign")
                t = "".join(x.text or "" for x in el.findall(W + "t"))
                if not t:
                    continue
                v = va.get(W + "val") if va is not None else None
                out.append(SUP0 + t + SUP1 if v == "superscript" else ("_" + t if v == "subscript" else t))
            elif el.tag == M + "t" and el.text:
                out.append(el.text)
        return "".join(out)

    items = []
    for el in body:
        if el.tag == W + "p":
            st = el.find(W + "pPr/" + W + "pStyle")
            style = st.get(W + "val") if st is not None else ""
            is_eq = el.find(".//" + M + "oMath") is not None
            txt = runs_text(el)
            if txt.strip():
                items.append({"kind": "h" if style.startswith("Heading") else ("eq" if is_eq else "p"),
                              "text": txt})
        elif el.tag == W + "tbl":
            rows = []
            for tr in el.findall(W + "tr"):
                rows.append([runs_text(tc) for tc in tr.findall(W + "tc")])
            items.append({"kind": "table", "rows": rows})
    return items


def plain(s):
    return re.sub(SUP0 + ".*?" + SUP1, "", s)


def sups(s):
    return re.findall(SUP0 + "(.*?)" + SUP1, s)


def norm(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s)).strip()


ABBR = set("e.g i.e al Fig Figs Eq Eqs ref Ref refs vs ca cf p pp No vol Vol ed Ch Sect cyl prio approx".split())


def sentences(s):
    """Split at ., ! or ? followed by space and a sentence start, not after an abbreviation,
    an initial or a decimal; superscript citations after the stop stay with their sentence."""
    out, start = [], 0
    for m in re.finditer(r"([.!?])((?:" + SUP0 + r"[^" + SUP1 + r"]*" + SUP1 + r")?[\"”’»)]*)\s+(?=[A-Z(«\"“0-9§*ΛλκδσμΔτ])", s):
        before = s[start:m.start()]
        last = (re.search(r"([A-Za-z]+)$", before) or [None, ""])[1] if re.search(r"([A-Za-z]+)$", before) else ""
        if m.group(1) == "." and (last in ABBR or re.search(r"(^|[\s(])[A-Z]$", before)):
            continue
        out.append(s[start:m.end(2)])
        start = m.end()
    if start < len(s):
        out.append(s[start:])
    return [x.strip() for x in out if x.strip()]


def references(items):
    """{number: entry text} from the paragraphs after the References heading."""
    refs, on = {}, False
    for it in items:
        if it["kind"] == "h":
            on = norm(it["text"]) == "References"
            continue
        if on and it["kind"] == "p":
            m = re.match(r"^(\d+)\s+(.*)$", norm(it["text"]))
            if m:
                refs[int(m.group(1))] = m.group(2)
    return refs


def cite_works(groups, refs):
    works = []
    for g in groups:
        for n in re.split(r"[,–-]", g):
            n = n.strip()
            if n.isdigit():
                works.append(refs.get(int(n), "<missing %s>" % n))
    return works


def tables_by_header(items):
    out = {}
    for it in items:
        if it["kind"] == "table":
            out.setdefault(norm(plain(" | ".join(it["rows"][0]))), []).append(it["rows"])
    return out


LOCTOK = re.compile(r"(?<![A-Za-z])(?:SI |SM |Supplementary )?(?:Tables? |Figs?\. |Figure |Eqs?\. |Sect\. |Ch\. |entry |entries |pp?\. )"
                    r"(?:SI )?[A-Z]{0,2}\d+[A-Za-z]?(?:[-–.]\d+[A-Za-z]?)*(?:[–-][A-Z]?\d+(?:[-–.]\d+)*)?")


def squash(s):
    return re.sub(r"[\s.–\-]", "", norm(s).replace(" to ", "–")).lower()


# ---------------------------------------------------------------------------------------------
def run_checks(det_xml, con_xml, ms_items=None):
    D, C = read_docx(det_xml), read_docx(con_xml)
    fails, notes = [], {}
    dref, cref = references(D), references(C)

    # the title page ends at the first heading; it is not prose under test
    def body(items):
        i = next(k for k, it in enumerate(items) if it["kind"] == "h")
        return items[i:]
    Db, Cb = body(D), body(C)

    # 1 headings
    dh = [norm(it["text"]) for it in Db if it["kind"] == "h"]
    ch = [norm(it["text"]) for it in Cb if it["kind"] == "h"]
    if dh != ch:
        fails.append("headings: condensed %s against detailed %s" % (
            [h for h in ch if h not in dh], [h for h in dh if h not in ch]) + ("" if set(dh) != set(ch) else " (order differs)"))
    notes["headings"] = len(ch)

    # 2 equations
    def eqs(items):
        out = {}
        for it in items:
            if it["kind"] == "eq":
                m = re.search(r"\((S\d+)\)\s*$", norm(plain(it["text"])))
                if m:
                    out[m.group(1)] = norm(plain(it["text"]))
        return out
    de, ce = eqs(Db), eqs(Cb)
    miss = sorted(set(de) - set(ce), key=lambda x: int(x[1:]))
    diff = sorted([k for k in de if k in ce and de[k] != ce[k]], key=lambda x: int(x[1:]))
    if miss:
        fails.append("equations missing from the condensed SI: " + ", ".join(miss))
    if diff:
        fails.append("equations whose content differs: " + ", ".join(diff))
    notes["equations"] = "%d of %d" % (len(set(de) & set(ce)), len(de))

    # 3 + 4 prose and citations (paragraphs outside tables, headings, equations and references)
    def prose(items):
        out = []
        for it in items:
            if it["kind"] == "h" and norm(it["text"]) == "References":
                break
            if it["kind"] == "p":
                out.extend(sentences(it["text"]))
        return out
    dsent = {}
    for s in prose(Db):
        dsent.setdefault(norm(plain(s)), []).append(cite_works(sups(s), dref))
    dtext = norm(plain(" ".join(it["text"] if it["kind"] != "table" else " ".join(" ".join(r) for r in it["rows"]) for it in D)))
    dnums = set(re.findall(r"\d+(?:[.,]\d+)*", dtext))
    verbatim, new, badnum, badcite = 0, [], [], []
    for s in prose(Cb):
        key = norm(plain(s))
        if key in dsent:
            verbatim += 1
            works = cite_works(sups(s), cref)
            if works not in dsent[key]:
                badcite.append((key[:90], works, dsent[key][0]))
        elif key in dtext:
            verbatim += 1          # a sentence the detailed SI carries inside a longer one
        else:
            new.append(key)
            for n in re.findall(r"\d+(?:[.,]\d+)*", key):
                if n not in dnums:
                    badnum.append((n, key[:100]))
    for n, k in badnum:
        fails.append("new sentence prints a number the detailed SI does not (%s): %s" % (n, k))
    for k, got, want in badcite:
        fails.append("citation mismatch in «%s»: condensed cites %s, detailed %s" % (k, got, want))
    notes["prose"] = "%d verbatim sentences, %d new" % (verbatim, len(new))
    notes["new_sentences"] = new

    # 5 Table S7
    dt, ct = tables_by_header(D), tables_by_header(C)
    s7d = [r for rows in dt.get("Parameter | Value | Units | State | Eq. | Citation with locator | Sensitivity / exposure", []) for r in rows[1:]]
    s7c = [r for rows in ct.get("Parameter | Value | Units | State | Eq. | Source", []) for r in rows[1:]]
    reg = {r["parameter"]: r for r in csv.DictReader(open(os.path.join(HERE, "parameters_provenance.csv")))}
    if [[norm(x) for x in r[:5]] for r in s7d] != [[norm(x) for x in r[:5]] for r in s7c]:
        fails.append("Table S7: condensed rows differ from the detailed rows (%d against %d)" % (len(s7c), len(s7d)))
    bad7 = []
    works = {"CRC Handbook": "CRC Handbook", "Reid, Prausnitz & Poling": "Reid, Prausnitz & Poling",
             "Incropera et al.": "Incropera", "SI Brochure": "International System of Units",
             "NIST Chemistry WebBook": "NIST Chemistry WebBook", "Cussler, Diffusion": "Cussler",
             "Bard & Faulkner": "Bard & Faulkner", "Newman & Thomas-Alyea": "Newman & Thomas-Alyea",
             "Sigma-Aldrich specification": "Sigma-Aldrich"}
    internal = {"Declared", "No source", "This table", "Vessel geometry", "Table S2", "Table S5", "Table S6"}
    for r in s7c:
        name, src = norm(plain(r[0])), norm(plain(r[5]))
        row = reg.get(name) or reg.get(r[0])
        if row is None:
            bad7.append("no registry row for '%s'" % name)
            continue
        full = row["citation"] + " " + row["locator"]
        body_ = re.sub(r"^Declared; basis: ", "", src)
        if src.startswith("Declared; basis: ") and row["provenance_class"] != "assumption":
            bad7.append("'%s' is %s but its source reads as declared" % (name, row["provenance_class"]))
        if body_ in internal:
            continue
        for part in body_.split("; "):
            wk = next((v for k, v in works.items() if part.startswith(k)), None)
            if wk:
                if wk.lower() not in full.lower():
                    bad7.append("'%s': %s not in its citation" % (name, wk))
            else:
                m = re.match(r"^([A-Z][\w'\-]+).*?\b((?:19|20)\d\d)\b", part)
                if not m or m.group(1).lower() not in full.lower() or m.group(2) not in full:
                    bad7.append("'%s': source '%s' not derivable from its citation" % (name, part[:60]))
            for t in LOCTOK.findall(part):
                if squash(t) not in squash(full):
                    bad7.append("'%s': locator token '%s' not in its citation or locator" % (name, t))
    fails.extend("Table S7: " + b for b in bad7)
    notes["table_s7_rows"] = len(s7c)

    # 6 Table S2
    s2d = next((rows for h, rr in dt.items() if h.startswith("# | Class | Reaction") for rows in rr), None)
    s2c = next((rows for h, rr in ct.items() if h.startswith("# | Class | Reaction") for rows in rr), None)
    rx = list(csv.DictReader(open(os.path.join(HERE, "reactions_50.csv"))))
    if not s2d or not s2c or len(s2c) != 51:
        fails.append("Table S2: expected 50 data rows in the condensed SI")
    else:
        for i, (a, b) in enumerate(zip(s2d[1:], s2c[1:])):
            if [norm(x) for x in a[:12]] != [norm(x) for x in b[:12]]:
                fails.append("Table S2 row %d: the first twelve columns differ" % (i + 1))
            na = re.match(r"^\[([\d,]+)\]", norm(a[12])); nb = re.match(r"^\[([\d,]+)\]", norm(b[12]))
            if not na or not nb or cite_works([na.group(1)], dref) != cite_works([nb.group(1)], cref):
                fails.append("Table S2 row %d: the source cell cites a different work" % (i + 1))
            for t in LOCTOK.findall(norm(b[12])):
                if squash(t) not in squash(rx[i]["conc_provenance"]):
                    fails.append("Table S2 row %d: locator token '%s' not in its concentration provenance" % (i + 1, t))

    # 7 the other tables
    def same_cols(dh_, ch_, cols, label):
        a = next((r for h, rr in dt.items() if h.startswith(dh_) for r in rr), None)
        b = next((r for h, rr in ct.items() if h.startswith(ch_) for r in rr), None)
        if a is None or b is None:
            fails.append("%s: table missing" % label)
            return
        if [[norm(plain(x[c])) for c in cols] for x in a[1:]] != [[norm(plain(x[c])) for c in cols] for x in b[1:]]:
            fails.append("%s: columns %s differ from the detailed table" % (label, cols))
    same_cols("Archetype | Model", "Archetype | Model", [0, 1, 2, 3], "Table S1")
    same_cols("Solvent | M", "Solvent | M", [0, 1, 2, 3, 4, 5], "Table S3")
    same_cols("Electrolyte | κ", "Electrolyte | κ", [0, 1, 2], "Table S4")
    same_cols("Reactor archetype | median", "Reactor archetype | median", [0, 1, 2, 3], "Table S5")
    same_cols("Mediated system", "Mediated system", [0, 1, 3, 4, 5, 6], "Table S6")
    same_cols("Catalyst-carried entry", "Catalyst-carried entry", [0, 1, 2, 3, 4], "catalyst table")
    for k, (hd, lab) in enumerate([("Reported quantity", "Table S8"), ("Reported quantity", "Table S9")]):
        a = [rr for h, rr in dt.items() if h.startswith(hd)]
        b = [rr for h, rr in ct.items() if h.startswith(hd)]
        if not a or not b or a[0] != b[0]:
            fails.append("Tables S8/S9 differ from the detailed tables")
            break
    s6d = next(rr for h, r0 in dt.items() if h.startswith("Mediated system") for rr in r0)
    s6c = next(rr for h, r0 in ct.items() if h.startswith("Mediated system") for rr in r0)
    for a, b in zip(s6d[1:], s6c[1:]):
        wd = sorted(set(cite_works(sups(a[2]), dref)))
        wc = sorted(set(cite_works([norm(b[2])], cref)))
        if wd != wc:
            fails.append("Table S6 '%s': k sources cite different works" % norm(a[0])[:40])

    # 8 internal cross-references
    ctext = norm(plain(" ".join(it["text"] if it["kind"] != "table" else " ".join(" ".join(r) for r in it["rows"]) for it in Cb)))
    secs = set(re.findall(r"^(S\d+(?:\.\d+)?)\.? ", "\n".join(ch), re.M))
    tabs = {m.group(1) for it in Cb if it["kind"] == "p"
            for m in [re.match(r"^Table (S\d+[a-k]?)[.\s(]", norm(plain(it["text"])))] if m}
    eqtags = set(ce)
    dang = []
    for m in re.finditer(r"§§?\s*(S\d+(?:\.\d+)?)(?:\s*(?:–|-|and)\s*§?(S\d+(?:\.\d+)?))?|Section (S\d+(?:\.\d+)?)", ctext):
        for g in (m.group(1), m.group(2), m.group(3)):
            if g and g not in secs:
                dang.append("§" + g)
    for m in re.finditer(r"\bTables? (S\d+[a-k]?(?:(?:, | and |, and |–|-)S\d+[a-k]?)*)", ctext):
        for g in re.findall(r"S\d+[a-k]?", m.group(1)):
            if g not in tabs and not (re.match(r"S7$", g) and any(t.startswith("S7") for t in tabs)):
                dang.append("Table " + g)
    for m in re.finditer(r"\bEqs?\. (S\d+)(?:\s*(?:–|-|and)\s*(S\d+))?", ctext):
        for g in (m.group(1), m.group(2)):
            if g and g not in eqtags:
                dang.append("Eq. " + g)
    for d in sorted(set(dang)):
        fails.append("dangling cross-reference in the condensed SI: " + d)

    # 9 manuscript targets
    if ms_items is not None:
        mtext = norm(plain(" ".join(it["text"] if it["kind"] != "table" else " ".join(" ".join(r) for r in it["rows"]) for it in ms_items)))
        want = set()
        for m in re.finditer(r"SI (?:§§?\s*|Sections? )?(S\d+(?:\.\d+)?)(?:\s*[–-]\s*S?(\d+(?:\.\d+)?))?(?:\s+and\s+S?(\d+(?:\.\d+)?))?", mtext):
            a, b, c = m.group(1), m.group(2), m.group(3)
            want.add(("sec", a))
            if c:
                want.add(("sec", "S" + c))
            if b:
                if "." in a:
                    maj, lo = a[1:].split("."); hi = b.split(".")[-1]
                    want.update(("sec", "S%s.%d" % (maj, j)) for j in range(int(lo), int(hi) + 1))
                else:
                    want.update(("sec", "S%d" % j) for j in range(int(a[1:]), int(b.split(".")[0]) + 1))
        for m in re.finditer(r"Tables? (S\d+[a-k]?(?:(?:, | and |, and )S\d+[a-k]?)*(?:\s*[–-]\s*S\d+)?)", mtext):
            grp = m.group(1)
            rng = re.search(r"S(\d+)\s*[–-]\s*S(\d+)", grp)
            if rng:
                want.update(("tab", "S%d" % j) for j in range(int(rng.group(1)), int(rng.group(2)) + 1))
            want.update(("tab", g) for g in re.findall(r"S\d+[a-k]?", grp))
        for kind, g in sorted(want):
            ok = g in secs if kind == "sec" else (g in tabs or (g == "S7" and any(t.startswith("S7") for t in tabs)))
            if not ok:
                fails.append("the manuscript cites SI %s %s, which the condensed SI does not carry" % ("section" if kind == "sec" else "Table", g))
        notes["manuscript_targets"] = len(want)

    # 10 references
    nums = sorted(cref)
    if nums != list(range(1, len(nums) + 1)):
        fails.append("reference list is not numbered 1..N")
    cited = set()
    for it in Cb:
        if it["kind"] == "h" and norm(it["text"]) == "References":
            break
        src = [it["text"]] if it["kind"] != "table" else [c for r in it["rows"] for c in r]
        for s in src:
            for g in sups(s):
                cited.update(int(x) for x in re.findall(r"\d+", g))
            if it["kind"] != "table":
                cited.update(int(x) for x in re.findall(r"\b[Rr]ef\. (\d+)", plain(s)))
    # table-cell citations are plain numbers: take them from the columns that carry them
    for h, rr in ct.items():
        for rows in rr:
            if h.startswith("# | Class | Reaction"):
                for r in rows[1:]:
                    mm = re.match(r"^\[([\d,]+)\]", norm(r[12]))
                    if mm:
                        cited.update(int(x) for x in mm.group(1).split(","))
            if h.startswith("Mediated system"):
                for r in rows[1:]:
                    cited.update(int(x) for x in re.findall(r"\d+", norm(r[2])))
            if h.startswith("Archetype | Model"):
                for r in rows[1:]:
                    cited.update(int(x) for x in re.findall(r"\((\d+)[,)]", norm(r[4])))
    for n in nums:
        if n not in cited:
            fails.append("reference %d is listed but never cited" % n)
        if cref[n] not in dref.values():
            fails.append("reference %d is not an entry of the detailed reference list" % n)
    if "?" in "".join(g for it in Cb if it["kind"] != "table" for g in sups(it["text"])):
        fails.append("an unresolved citation marker ('?') is printed")
    notes["references"] = len(nums)
    return fails, notes


def latest_ms():
    import glob
    d = os.path.join(os.path.dirname(ROOT), "MS Drafts")
    # shared resolver -- the glob here was pinned to a retired naming scheme (2026-09-29)
    return _shared_latest_ms(verbose=False)


def ms_items(path):
    xml = zipfile.ZipFile(path).read("word/document.xml")
    xml = re.sub(rb"<w:del\s[^>]*[^/]>.*?</w:del>", b"", xml, flags=re.S)   # struck text asserts nothing
    return read_docx(xml)


def parts(path):
    z = zipfile.ZipFile(path)
    return {n: z.read(n) for n in z.namelist()}


def fresh():
    snap = os.path.join(ROOT, "results", "_si_condensed_snapshot.docx")
    shutil.copy2(CON, snap)
    before = parts(snap)
    env = dict(os.environ, SI_MODE="condensed")
    r = subprocess.run(["node", os.path.join(ROOT, "make_si.js")], cwd=HERE, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copy2(snap, CON); os.remove(snap)
        return ["fresh: make_si.js (condensed) did not run: " + r.stderr.strip()[-300:]]
    after = parts(CON)
    diff = sorted(n for n in set(before) | set(after) if n != "docProps/core.xml" and before.get(n) != after.get(n))
    if diff:
        os.remove(snap)
        return ["fresh: the condensed SI was not what make_si.js produces (%s); it has been rebuilt" % ", ".join(diff)]
    shutil.copy2(snap, CON); os.remove(snap)
    return []


def main(neg=False):
    for p in (DET, CON):
        if not os.path.exists(p):
            print("G-SICOND: FAIL -- missing %s" % os.path.basename(p))
            return 1
    det_xml = zipfile.ZipFile(DET).read("word/document.xml")
    con_xml = zipfile.ZipFile(CON).read("word/document.xml")
    msp = latest_ms()
    mi = ms_items(msp) if msp else None
    if not neg:
        fails = fresh()
        con_xml = zipfile.ZipFile(CON).read("word/document.xml")
        f2, notes = run_checks(det_xml, con_xml, mi)
        fails += f2
        print("manuscript under test: %s" % (os.path.basename(msp) if msp else "none"))
        for k in ("headings", "equations", "prose", "table_s7_rows", "references", "manuscript_targets"):
            print("  %-20s %s" % (k, notes.get(k)))
        print("  new sentences (not verbatim in the detailed SI):")
        for s in notes["new_sentences"]:
            print("    - " + s[:150])
        json.dump({"fails": fails, "notes": notes}, io.open(os.path.join(ROOT, "results", "si_condensed.json"), "w", encoding="utf8"), indent=1, ensure_ascii=False)
        for f in fails:
            print("  FAIL " + f)
        print("G-SICOND: %s" % ("PASS -- the condensed SI is a faithful subset of the detailed SI: every equation, every Table S7 row, "
                                "verbatim prose with the same cited works, derivable short locators, and every manuscript target"
                                if not fails else "FAIL (%d)" % len(fails)))
        return 0 if not fails else 1

    # NEGATIVE CONTROL: perturb copies of the condensed XML in memory, one defect class at a time,
    # and require the check written for that class to fire. Nothing on disk is modified.
    base_fails, _ = run_checks(det_xml, con_xml, mi)
    if base_fails:
        print("G-SICOND control: INCONCLUSIVE -- the unperturbed condensed SI already fails (%d)" % len(base_fails))
        return 1
    txt = con_xml.decode("utf8")
    probes = []

    def probe(label, old, new, expect):
        if old not in txt:
            probes.append((label, False, "probe string absent -- repoint the control"))
            return
        f, _ = run_checks(det_xml, txt.replace(old, new, 1).encode("utf8"), mi)
        probes.append((label, any(expect in x for x in f), "; ".join(f)[:160]))
    probe("number changed in a verbatim sentence", "reproduced to 0.5% and 0.26%", "reproduced to 0.5% and 0.27%", "new sentence prints a number")
    probe("equation S16 dropped", "\t(S16)</w:t>", "\t(S99)</w:t>", "equations")
    probe("Table S7 value altered", ">1.380649e-23<", ">1.380649e-22<", "Table S7")
    m = re.search(r'<w:t xml:space="preserve">(\d+)</w:t>(?:(?!<w:t[ >]).){0,800}<w:t xml:space="preserve">\] Table 4, p\. 6399', txt, re.S)
    if m:
        probe("Table S2 source cites another work", m.group(0), m.group(0).replace(">%s</w:t>" % m.group(1), ">%d</w:t>" % (int(m.group(1)) + 1), 1), "Table S2")
    else:
        probes.append(("Table S2 source cites another work", False, "probe string absent -- repoint the control"))
    m = re.search(r'(correlation,</w:t>(?:(?!<w:t[ >]).){0,800}<w:t xml:space="preserve">)(\d+)(</w:t>)', txt, re.S)
    if m:
        probe("citation renumbered to another work", m.group(0), m.group(1) + str(int(m.group(2)) + 1) + m.group(3), "citation mismatch")
    else:
        probes.append(("citation renumbered to another work", False, "probe string absent -- repoint the control"))
    probe("heading renamed", ">S6.2 Cooling duty<", ">S6.2 Cooling requirement<", "headings")
    probe("dangling cross-reference", "Values and locators: Table S7g.", "Values and locators: Table S12.", "dangling cross-reference")
    for label, ok, detail in probes:
        print("  %-5s %-42s %s" % ("fired" if ok else "MISSED", label, "" if ok else detail))
    good = all(ok for _, ok, _ in probes)
    print("G-SICOND control: %s" % ("GOOD -- every perturbation fired its check" if good else "BAD -- at least one perturbation went undetected"))
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main("--negative-control" in sys.argv))
