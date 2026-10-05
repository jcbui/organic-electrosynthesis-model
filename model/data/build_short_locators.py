"""Short provenance locators for the condensed SI (Source, page, table).

The detailed SI prints each registry row's full citation and locator, and each Table S2 row's full
concentration provenance. The condensed SI prints only "Source, page/table". This script derives the
short form mechanically from those same strings and writes results/si_short_locators.json, which
make_si.js reads in SI_MODE=condensed.

Nothing here is typed per row. A short source is either a named override for a reference work
(matched on a prefix of the citation) or the first author and year read out of the citation; a
locator token is a page/table/figure/equation/section token copied out of the citation or locator
text. data/check_si_condensed.py (G-SICOND) re-checks that every surname, year and locator token
in the short form occurs verbatim in the full record, so a short form cannot say anything the
detailed SI does not.
"""
import csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Reference works: (prefix of the citation, short name). Matched with startswith on the stripped part.
WORKS = [
    ("CRC Handbook of Chemistry and Physics", "CRC Handbook, 97th ed."),
    ("Reid, Prausnitz & Poling", "Reid, Prausnitz & Poling, 4th ed."),
    ("Incropera, DeWitt, Bergman & Lavine", "Incropera et al., 6th ed."),
    ("BIPM, The International System of Units", "SI Brochure, 9th ed."),
    ("NIST Chemistry WebBook", "NIST Chemistry WebBook"),
    ("Cussler, Diffusion", "Cussler, Diffusion, 3rd ed."),
    ("Bard & Faulkner", "Bard & Faulkner, 2nd ed."),
    ("Newman & Thomas-Alyea", "Newman & Thomas-Alyea, 3rd ed."),
    ("Sigma-Aldrich product specification", "Sigma-Aldrich specification"),
    ("Prohaska et al., 'Standard atomic weights", "Prohaska et al. 2022"),
    ("Sander, 'Compilation of Henry's law constants", "Sander 2023"),
    ("Table S2", "Table S2"),
    ("Table S6", "Table S6"),
    ("the median over the solved 50-reaction transport matrix", "Table S5"),
    ("the balanced half-reaction of each exemplar", "Table S2"),
    ("Leveque entrance solution (Pickett & Ong", "Pickett & Ong 1974"),
]
# Short names printed without locator tokens: pointers inside this SI, or a method whose locator
# text describes this SI's own tables rather than the cited work.
BARE = {"Table S2", "Table S5", "Table S6", "Pickett & Ong 1974"}
# Citations that name no external source.
INTERNAL = [
    (re.compile(r"^(this registry|rows? '|rows '|declared basis: the value of row)", re.I), "This table"),
    (re.compile(r"^elementary geometry of the declared vessel", re.I), "Vessel geometry"),
    (re.compile(r"^--\s*\(", re.I), "No source"),
    (re.compile(r"^declared", re.I), "Declared"),
]

TOK = re.compile(
    r"(?:(?:SI|SM|Supporting Information|Supplementary Materials?|supporting information|Supplementary)\s+)?"
    r"(?<![A-Za-z])(?:Tables?[- ]|Fig(?:ure|s)?\.?\s|Eqs?\.\s|Sect\.\s|Ch\.\s|entry\s|entries\s|pp?\.?\s)"
    r"\s*(?:SI\s+)?[A-Z]{0,2}\d+[A-Za-z]?(?:[-–.]\d+[A-Za-z]?)*"
    r"(?:\s*(?:to|–|-)\s*[A-Z]?\d+(?:[-–.]\d+)*)?")


def norm_tok(t):
    t = re.sub(r"\s+", " ", t.strip())
    t = re.sub(r"(?<![A-Za-z])(pp?)\.?\s*(?=[A-Z]?\d)", r"\1. ", t)   # "p 2186" -> "p. 2186"
    t = re.sub(r"(?<![A-Za-z])(Figs?)\.?\s+(?=[A-Z]?\d)", r"\1. ", t)
    t = re.sub(r"^Table-", "Table ", t)
    t = t.replace(" to ", "–")
    return t


def tokens(text):
    out = []
    for m in TOK.finditer(text or ""):
        t = norm_tok(m.group(0))
        # "Ch. 11-12" after "Ch. 11": a range restating tokens already kept adds nothing
        if "-" in t and any(o == t.split("-")[0] for o in out):
            continue
        if t not in out:
            out.append(t)
    return out


# Names of works that a locator may mention without the row citing them ("as restated at Reid 4th
# ed. p. 599"); a token that follows such a mention belongs to that work, not to the row's source.
FOREIGN = re.compile(r"\b(Reid|Poling|CRC|Amatore|Krumgalz|Dorn|Gong|Casteel|Kalugin|Izutsu|Barthel|Das|Lee|Zhang|Cussler|Incropera|Newman|Bard|IUPAC|Watkins|Mo|Jang|Eisenberg|Wilke)\b")
YEAR = re.compile(r"\b(19[4-9]\d|20[0-3]\d)\b")


def author_year(part):
    """'Watkins, Schiffer, ... & Gregoire, ACS Energy Lett. 2023, ...' -> 'Watkins et al. 2023'."""
    y = re.search(r"\b(19[4-9]\d|20[0-3]\d)\b(?=,\s*\d)", part) or YEAR.search(part)
    if not y:
        return None
    head = part[:y.start()]
    acs = re.match(r"^([A-Z][\w'\-]+), [A-Z]\.", part)      # 'Ting, S. I.; Williams, W. L.; ...'
    if acs:
        n = len(re.findall(r"[A-Z][\w'\-]+, [A-Z]\.", head))
        return acs.group(1) + (" et al. " if n > 2 or "et al" in head else " " ) + y.group(1) if n != 2 else \
            acs.group(1) + " & " + re.findall(r"([A-Z][\w'\-]+), [A-Z]\.", head)[1] + " " + y.group(1)
    first = re.match(r"^([A-Z][\w'\-]+(?: [A-Z][\w'\-]+)?)(?=,| &| et al)", part)
    if not first:
        return None
    s = first.group(1)
    names = head.split(", ")
    if "et al" in head[:60]:
        return s + " et al. " + y.group(1)
    m2 = re.match(r"^([A-Z][\w'\-]+) & ([A-Z][\w'\-]+),", part)
    if m2:
        return m2.group(1) + " & " + m2.group(2) + " " + y.group(1)
    return s + " et al. " + y.group(1)


def split_sources(cit):
    parts, cur = [], ""
    for seg in re.split(r";\s+", cit):
        if cur and not YEAR.search(cur) and re.match(r"^[A-Z][\w'\-]+, [A-Z]\.", seg):   # ACS author list
            cur += "; " + seg
        else:
            if cur:
                parts.append(cur)
            cur = seg
    if cur:
        parts.append(cur)
    return [re.sub(r"^(?:method:|cross-checked against|restated as)\s*", "", p).strip() for p in parts]


def short_source(part):
    for pre, name in WORKS:
        if part.startswith(pre):
            return name
    for rx, name in INTERNAL:
        if rx.search(part):
            return name
    return author_year(part)


def surname_of(short):
    return (short or "").split(",")[0].split(" ")[0]


def registry_short(cit, loc, cls="measured"):
    cit = (cit or "").strip()
    loc = (loc or "").strip()
    srcs = split_sources(cit)
    shorts = []
    for s in srcs:
        n = short_source(s)
        if n and n not in [x[0] for x in shorts]:
            shorts.append((n, s))
    if not shorts:
        return "—"
    if shorts[0][0] in ("Declared", "No source", "This table", "Vessel geometry"):
        return shorts[0][0]
    # An assumption row may cite a work that supports its context (a composition, a range) but not
    # the value; the condensed table must not read as if that work measured it.
    prefix = "Declared; basis: " if cls == "assumption" else ""
    toks = {n: ([] if n in BARE else [t for t in tokens(s) if t != n]) for n, s in shorts}
    names = {n: surname_of(n) for n, _ in shorts}
    for seg in (re.split(r";\s+", loc) if loc else []):
        owner = shorts[0][0]
        for n, sn in names.items():
            if len(sn) > 2 and sn.lower() in seg[:25].lower():
                owner = n
                break
        else:
            if FOREIGN.search(seg[:25]):
                continue
        cut = len(seg)
        for m in FOREIGN.finditer(seg):
            if m.start() > 25 and m.group(0).lower() != names[owner].lower():
                cut = min(cut, m.start())
        for n, sn in names.items():
            if n != owner and len(sn) > 2:
                i = seg.lower().find(sn.lower(), 25)
                if i >= 0:
                    cut = min(cut, i)
        for t in ([] if owner in BARE else tokens(seg[:cut])):
            if t not in toks[owner] and t != owner:
                toks[owner].append(t)
    cells = []
    for n, _ in shorts:
        cells.append(", ".join([n] + toks[n][:3]))
    return prefix + "; ".join(cells)


def s2_short(conc):
    m = re.findall(r"\(([^()]*?(?:p{1,2}\.?\s*[A-Z]?\d|Table|SI|SM|Fig)[^()]*)\)", conc or "")
    toks = []
    for grp in (m or [conc or ""]):
        for t in tokens(grp):
            if t not in toks:
                toks.append(t)
    toks = [t for t in toks if t.startswith(("p.", "pp.", "SI", "SM", "Table", "Fig", "Supplementary"))]
    cell = ", ".join(toks[:4])
    if re.match(r"^\s*Declared", conc or ""):
        cell = "declared" + ("; " + cell if cell else "")
    return cell


def main():
    live = set(json.load(open(os.path.join(ROOT, "results", "registry_liveness.json")))["live_parameters"])
    reg = {}
    with open(os.path.join(HERE, "parameters_provenance.csv"), newline="") as f:
        for r in csv.DictReader(f):
            if r["parameter"] in live:
                reg[r["parameter"]] = registry_short(r["citation"], r["locator"], r["provenance_class"])
    with open(os.path.join(HERE, "reactions_50.csv"), newline="") as f:
        s2 = [s2_short(r["conc_provenance"]) for r in csv.DictReader(f)]
    out = {"registry": reg, "table_s2": s2}
    p = os.path.join(ROOT, "results", "si_short_locators.json")
    with open(p, "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    print("wrote %s: %d registry rows, %d Table S2 rows" % (os.path.relpath(p, ROOT), len(reg), len(s2)))


if __name__ == "__main__":
    main()
