#!/usr/bin/env python3
"""Does each row's reaction NAME describe chemistry its own exemplar paper actually reports?

Every existing gate checks NUMBERS -- G-COND co-locates the concentrations in the exemplar PDF,
G-DSUB binds diffusivities, G-SPECIES binds species. None checks that the reaction's NAME matches
the paper the conditions came from, which is how row 11 carried "Markovnikov hydroamination" for
four months while its own conditions were Gnaim's conditions C, an alkene REDUCTION.

Method: pull the distinctive transformation words out of each name and require each to appear in
that row's exemplar text cache. A miss is not automatically a defect -- a paper may use a synonym
-- so every miss is printed for a human to read, with the synonyms the cache does contain.
"""
import csv, os, re, sys

D = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
TXT = os.path.join(D, "results", "pdftext")
rows = list(csv.DictReader(open(os.path.join(D, "data", "reactions_50.csv"))))
pdfmap = {}
# the map's `row` column is ZERO-BASED: its row 0 is reaction 1. Keying it 1-based without the
# shift checks every reaction against the PREVIOUS row's paper, which is how the first run of this
# audit reported 44 of 63 terms missing.
for r in csv.DictReader(open(os.path.join(D, "data", "exemplar_pdf_map.csv"))):
    pdfmap[int(r["row"]) + 1] = r["pdf"].strip()

STOP = set("""catalyzed catalysed electrochemical electrocatalytic anodic cathodic mediated
paired direct the of and with via from under into onto reaction process alkyl aryl
selective type free based assisted driven promoted enabled""".split())

# transformation-naming morphology plus named reactions
NAMEY = re.compile(r"(ation|ylation|ination|isation|ization|coupling|cyclization|cyclisation|"
                   r"dimerization|dimerisation|genation|oxidation|reduction|exchange|cleavage|"
                   r"addition|substitution|rearrangement|elimination|opening|closure)$", re.I)
NAMED = ["wacker", "kolbe", "hofmann", "appel", "shono", "giese", "minisci", "ritter",
         "simmons", "heck", "suzuki", "negishi", "sandmeyer", "birch", "pinacol"]

def variants(w):
    w = w.lower()
    out = {w}
    if w.endswith("ization"): out.add(w[:-7] + "isation")
    if w.endswith("isation"): out.add(w[:-7] + "ization")
    if w.endswith("ized"):    out.add(w[:-4] + "ised")
    if w.endswith("ation"):   out.add(w[:-5] + "ate"); out.add(w[:-5] + "ated")
    return out


def cut_references(txt):
    """Drop the reference list.

    Nature-style extractions carry no "References" heading at all -- the list simply starts with
    numbered entries -- so the cut is found structurally: in the back half of the document, the
    first of a dense run of "<n>. <surname>," starts. Without this, a transformation named only in
    a CITED TITLE reads as the paper's own chemistry; that is precisely how "hydroamination"
    survived in the Gnaim row, from its ref 13 (Gui et al., olefin hydroamination with nitroarenes).
    """
    half = len(txt) // 2
    hits = [m.start() for m in re.finditer(r"\b\d{1,3}\. [a-z][a-z\-']+,", txt) if m.start() > half]
    if len(hits) >= 10:
        return txt[:hits[0]]
    for marker in (" references ", " bibliography "):
        k = txt.rfind(marker)
        if k > half:
            return txt[:k]
    return txt


print("ROW  REACTION                                             TERM            IN PAPER?")
print("-" * 104)
flagged, checked, nocache = [], 0, []
for i, r in enumerate(rows, 1):
    name = r["reaction"]
    pdf = pdfmap.get(i)
    cache = os.path.join(TXT, os.path.splitext(pdf)[0] + ".txt") if pdf else None
    if not cache or not os.path.exists(cache):
        nocache.append((i, name, pdf)); continue
    txt = open(cache, encoding="utf8", errors="replace").read().lower()
    txt = re.sub(r"\s+", " ", txt)
    # PDF text carries typographic ligatures: the Tajima title is "benzylic \ufb02uorination",
    # so a plain search for "fluorination" misses the paper's own title word.
    for lig, pair in (("\ufb00","ff"),("\ufb01","fi"),("\ufb02","fl"),("\ufb03","ffi"),("\ufb04","ffl")):
        txt = txt.replace(lig, pair)
    # CUT THE REFERENCE LIST. A cited title carries other people's chemistry: "hydroamination"
    # appears in the Gnaim paper exactly once, in its ref 13 (Gui et al., olefin hydroamination),
    # and searching the whole cache therefore passed the very mislabel this audit exists to catch.
    txt = cut_references(txt)
    words = re.findall(r"[A-Za-z][A-Za-z'\-]{3,}", name)
    terms = [w for w in words if w.lower() not in STOP and (NAMEY.search(w) or w.lower() in NAMED)]
    if not terms:
        terms = [w for w in words if w.lower() not in STOP and len(w) > 6]
    for t in terms:
        checked += 1
        hit = any(v in txt for v in variants(t))
        if not hit:
            flagged.append((i, name, t, txt))
            print("%3d  %-52s %-15s MISSING" % (i, name[:52], t))
print("-" * 104)
print("%d terms checked across %d rows with a cache; %d missing; %d rows have no cache"
      % (checked, len(rows) - len(nocache), len(flagged), len(nocache)))
if nocache:
    print("\nno text cache (cannot check):")
    for i, name, pdf in nocache:
        print("   %3d  %-50s %s" % (i, name[:50], pdf))
