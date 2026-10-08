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

# the repo ROOT, not this script's own directory: every path below is "<root>/data/..." or
# "<root>/results/...", and defaulting D to data/ made them "<root>/data/data/..."
NEGCTL = "--negative-control" in sys.argv
_pos = [a for a in sys.argv[1:] if not a.startswith("-")]
# the repo ROOT, not this script's own directory: every path below is "<root>/data/..." or
# "<root>/results/...". A flag must never be read as the root -- "--negative-control" was, and the
# control then died on '--negative-control/data/reactions_50.csv'.
D = _pos[0] if _pos else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TXT = os.path.join(D, "results", "pdftext")
rows = list(csv.DictReader(open(os.path.join(D, "data", "reactions_50.csv"))))
pdfmap = {}
# the map's `row` column is ZERO-BASED: its row 0 is reaction 1. Keying it 1-based without the
# shift checks every reaction against the PREVIOUS row's paper, which is how the first run of this
# audit reported 44 of 63 terms missing.
for r in csv.DictReader(open(os.path.join(D, "data", "exemplar_pdf_map.csv"))):
    n = int(r["row"]) + 1
    # The map carries the reaction NAME as well as the index, so the alignment is ASSERTED rather
    # than trusted. Keying it 1-based without the +1 shift checks every reaction against the
    # PREVIOUS row's paper, and the first run of this audit reported 44 of 63 terms missing for
    # exactly that reason -- a silent off-by-one that looks like a corpus of mislabels.
    if r.get("reaction", "").strip() and r["reaction"].strip() != rows[n - 1]["reaction"]:
        raise SystemExit("exemplar_pdf_map.csv row %s names %r where reactions_50.csv row %d is %r"
                         % (r["row"], r["reaction"].strip(), n, rows[n - 1]["reaction"]))
    pdfmap[n] = r["pdf"].strip()

if NEGCTL:
    # the control renames ONE row to a transformation its own paper does not report -- built the way
    # the two real defects were: a real word, a real reaction type, the wrong paper. The name chosen
    # is deliberately row 45's OWN name, so the string is real chemistry somewhere in this very set
    # and the only thing wrong with it is which paper it is attached to. It is applied in memory and
    # never written, so a control run cannot leave a perturbed name on disk.
    rows[0] = dict(rows[0], reaction="Anodic benzylic fluorination")
    print("NEGATIVE CONTROL: row 1 renamed to %r\n" % rows[0]["reaction"])

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


# ───────────────────────── terms read against their own paper and KEPT ─────────────────────────
# A miss is not automatically a defect: a paper may name the same transformation another way, and
# the tokeniser cannot see a hyphenated compound whose halves are both present. Every entry here was
# checked against the paper on 2026-10-05 and carries the reason. An entry that STOPS missing is a
# failure too, so the list cannot quietly go stale.
REVIEWED = {
    (4,  "annulation"):        "the paper is titled 'Electrochemical Synthesis of Benzimidazoles via "
                               "Dehydrogenative Cyclization of Amidines' -- annulation and cyclization "
                               "name the same ring-forming step ('cyclization' x21)",
    (7,  "pyridination"):      "the paper is titled 'Electrochemical C-H Amination ... via "
                               "N-Arylpyridinium Ions', but THIS ROW MODELS THE ANODIC STEP ALONE "
                               "(anisole + pyridine, divided cell, 2 e-), whose product is the "
                               "pyridinium ion; the alkylamine is added afterwards and is never in the "
                               "cell. The row's name is the more accurate one for what is solved. "
                               "DO NOT 'fix' this to amination.",
    (20, "homocoupling"):      "'biaryl' x12 and 'coupling' x12 -- Ni-mediated reductive coupling of two "
                               "ArX to the biaryl is a homocoupling",
    (30, "methoxylation"):     "the BASF patent says 'methoxy' and 'acetal' x40 (the product is the "
                               "dimethyl acetal); anodic methoxylation is the standard name for the step",
    (31, "alpha-methoxylation"): "'methoxylation' x1 and 'methoxy' x33; the hyphenated compound is not a "
                               "literal string in the paper",
    (32, "epoxidation"):       "'ethylene oxide' x40 and 'chlorohydrin' x9 -- ethylene to ethylene oxide "
                               "through the chlorohydrin IS the epoxidation",
    (35, "NHPI-mediated"):     "'NHPI' x28, 'allylic' x32, 'enone' x28; the hyphenated compound is the miss",
    (38, "Radical-cation"):    "'radical cation' x24, unhyphenated",
    (40, "alpha-methoxylation"): "'methoxylation' x13 and 'Non-Kolbe' x5; the hyphenated compound is the miss",
}


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

# ───────────────────── second check: is the CARRIER named in the exemplar? ─────────────────────
# The name check above reads transformation words. It cannot see a row whose transformation is
# right and whose MOLECULE is not: "Shono oxidation" carried N-Boc-pyrrolidine against a 1975 paper
# that never mentions Boc; "imide reduction" carried N-methylphthalimide against a heteroarene
# paper; "aryl chloride dehalogenation" carried 4-chloroanisole where the model substrate is
# 4-phenoxybromobenzene. Each row lists the strings by which its exemplar names the species the
# row calls its carrier; at least one must occur in that paper's text (reference list cut).
CARRIER = {
 1: ["bpy", "bipyridine"], 2: ["bipyridine", "bpy"], 3: ["carbomethoxypyrrolidine"], 4: ["amidine"],
 5: ["mnbr2", "manganese"], 6: ["nabr"], 7: ["anisole"], 8: ["nabr"], 9: ["salen"], 10: ["adamantane"],
 11: ["cobr2"], 12: ["undecenoic"], 13: ["dtbbpy", "bipyridine"], 14: ["nicl2"], 15: ["guaiacol"],
 16: ["dicyanobenzene"], 17: ["molecular oxygen"], 18: ["cp*rh", "[cp*rhcl2]2"], 19: ["cu(acac)2"],
 20: ["nibr2bpy"], 21: ["naphthol"], 22: ["acrylonitrile"], 23: ["naphthalene"],
 24: ["nitrobenzotrifluoride"], 25: ["thiophenecar"], 26: ["4-fluorothiophenol"],
 27: ["phenoxylbromobenzene", "phenoxybromobenzene"], 28: ["benzaldehyde"], 29: ["act"],
 30: ["butyltoluene"], 31: ["benzamide"], 32: ["chloride"], 33: ["carbonate"], 34: ["chloride"],
 35: ["cl4nhpi"], 36: ["cinnam"], 37: ["act"], 38: ["anethol"], 39: ["hydroquinone", "benzoquinone"],
 40: ["alanine"], 41: ["salen"], 42: ["n(pmp)3"], 43: ["tet a"], 44: ["biphenylcarboxylic"],
 45: ["ethylbenzene"], 46: ["nabr"], 47: ["methyl styrene", "methylstyrene"], 48: ["nh4scn"],
 49: ["mesitylene"], 50: ["dianilide", "malon"],
}
REVIEWED_CARRIER = {
 13: "the main text writes 'Ni catalyst' and draws the ligand; the SI names it "
     "('4,4'-di-tert-butyl-2,2'-bipyridine', reagent table) and the aryl bromide ('5-bromo-3-isopropyl-1H-indole')",
 15: "the main text writes 'phenol 1a and arene 1b' and draws them; the SI names the product "
     "'2-Hydroxy-2',3,4',5'-tetramethoxy-5-methylbiphenyl (1ab)', which fixes 1a as 4-methylguaiacol",
 31: "the exemplar writes 'Dimethylacetamide-d9 (14)' and draws 13, its protio isotopologue, as "
     "N,N-dimethylacetamide (p. 4266); the row carries the 1:1 mixture the p. 4268 experiment oxidizes",
}
if NEGCTL:
    CARRIER[3] = ["n-boc-pyrrolidine"]      # the label this row carried until 2026-10-05
cflag = []
for i, r in enumerate(rows, 1):
    pdf = pdfmap.get(i); cache = os.path.join(TXT, os.path.splitext(pdf)[0] + ".txt") if pdf else None
    if not cache or not os.path.exists(cache):
        continue
    txt = re.sub(r"\s+", " ", open(cache, encoding="utf8", errors="replace").read().lower())
    for lig, pair in (("\ufb00","ff"),("\ufb01","fi"),("\ufb02","fl"),("\ufb03","ffi"),("\ufb04","ffl")):
        txt = txt.replace(lig, pair)
    txt = cut_references(txt)
    dehyph = txt.replace("- ", "").replace("-", "")
    if not any(a in txt or a.replace("-", "") in dehyph for a in CARRIER[i]):
        cflag.append(i)
        print("%3d  %-52s carrier %-28s NOT NAMED (%s)" % (i, r["reaction"][:52], r["carrier_species"][:28], "/".join(CARRIER[i])))
c_undeclared = sorted(i for i in cflag if i not in REVIEWED_CARRIER)
c_stale = sorted(i for i in REVIEWED_CARRIER if i not in cflag)
print("carrier check: %d of %d rows name their carrier in the exemplar text; %d reviewed exceptions"
      % (len(rows) - len(cflag), len(rows), len(REVIEWED_CARRIER)))
if c_undeclared:
    print("\nUNDECLARED -- a row's carrier species is not named in its own exemplar: rows %s" % c_undeclared)
if c_stale:
    print("\nSTALE CARRIER EXEMPTION -- now named, so remove: rows %s" % c_stale)

# ───────────────────────────────── verdict ─────────────────────────────────
# Printing a list and exiting 0 is what this gate did on the day it was written, and run_gates.sh
# reported PASS over eleven unexamined misses. A gate that cannot fail is not a gate.
missed = {(i, t) for i, _, t, _ in flagged}
undeclared = sorted(m for m in missed if m not in REVIEWED)
stale = sorted(k for k in REVIEWED if k not in missed)
if undeclared:
    print("\nUNDECLARED -- a reaction names chemistry its own exemplar does not report:")
    for i, t in undeclared:
        print("   row %-3d %-24s in %s" % (i, t, pdfmap.get(i)))
if stale:
    print("\nSTALE EXEMPTION -- these no longer miss, so the reason is obsolete; remove them:")
    for i, t in stale:
        print("   row %-3d %s" % (i, t))
if nocache:
    print("\n%d row(s) have no text cache and were not checked" % len(nocache))

ok = not undeclared and not stale and not nocache and not c_undeclared and not c_stale
if NEGCTL:
    both = bool(undeclared) and (3 in c_undeclared)
    print("\nG-NAMES control: %s -- the injected name %s; the retired carrier label %s"
          % ("GOOD" if both else "BAD, the gate did not fire on both",
             "was rejected" if undeclared else "passed unnoticed",
             "was rejected" if 3 in c_undeclared else "passed unnoticed"))
    sys.exit(0)
print("\nG-NAMES: %s" % ("PASS -- every reaction name describes chemistry its own exemplar reports, "
                          "and every exemption still applies" if ok else "FAIL"))
sys.exit(0 if ok else 1)
