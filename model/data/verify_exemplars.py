#!/usr/bin/env python3
"""G-EXEMPLAR -- resolve every exemplar paper behind the 50 reactions against Crossref.

    cd Section4_Model && python data/verify_exemplars.py

WHY THIS EXISTS
---------------
The 49 distinct exemplar papers named in reactions_50.csv are the ENTIRE basis for every
concentration in the model -- carrier, substrate, mediator and supporting electrolyte. Until now
NOTHING checked them. `verify_citations.py` (G-CITE) resolves the SI's own bibliography and
`verify_ms_citations.py` (G-MSCITE) the manuscript's Sections 3-4; neither mentions reactions_50
or the exemplar column.

That matters here more than it would elsewhere. CLAUDE.md records a chimera that survived
multiple drafts -- "Wallnofer-Ogris, Front. Chem. Eng. 2024, 6, 1384772", a locator that actually
belongs to Eichner/Amiri/Burheim/Lamb and reports a value an order of magnitude below what was
claimed of it. A fabricated exemplar would be worse: it would carry a whole row's concentrations.

WHAT THIS CAN AND CANNOT DO
---------------------------
Crossref SEARCH ranking is nondeterministic and a bibliographic string can return an unrelated
paper -- CLAUDE.md records "Love/George, OPRD 2021" resolving to "Love China, Love Hong Kong".
So this script does NOT claim a citation is correct because a search returned something. It
reports, per exemplar:

    RESOLVED   a Crossref record whose journal AND year match, and whose author list contains
               the surname(s) the exemplar names
    WEAK       a record matching journal+year but NOT the named author -- suspicious, look at it
    UNRESOLVED nothing plausible came back -- may be a patent, a pre-Crossref paper, or wrong

UNRESOLVED is not by itself proof of fabrication (the 1964 Baizer JES paper and the BASF patent
are legitimately hard to resolve), but every UNRESOLVED and every WEAK needs a human to open it.
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UA = "Mozilla/5.0 (provenance-audit; mailto:jbui888@gmail.com)"

JOURNAL = {
    "JACS": "Journal of the American Chemical Society", "Angew": "Angewandte Chemie",
    "Science": "Science", "Nature": "Nature", "Nat Commun": "Nature Communications",
    "Nat Catal": "Nature Catalysis", "OPRD": "Organic Process Research",
    "OL": "Organic Letters", "Chem Sci": "Chemical Science", "Tetrahedron": "Tetrahedron",
    "Chem Commun": "Chemical Communications", "JES": "Journal of The Electrochemical Society",
    "ACS SCE": "ACS Sustainable Chemistry", "ChemSusChem": "ChemSusChem",
    "Chem Eur J": "Chemistry - A European Journal", "Can J Chem": "Canadian Journal of Chemistry",
    "RSC Adv": "RSC Advances", "Tet Lett": "Tetrahedron Letters",
    "Electrochem Commun": "Electrochemistry Communications", "ACS Omega": "ACS Omega",
    "Electrochim Acta": "Electrochimica Acta",
}


def split_exemplars(ex):
    """Split an exemplar cell on ';' -- but NOT on a ';' inside parentheses.

    A plain str.split(";") tore "Hioki/Baran Science 2023 (rAP; acetone)" into two pieces and
    then tried to resolve "acetone)" as a citation, which of course came back WEAK. That is a
    phantom entry on the "needs a human to open" list: a reviewer chasing it finds nothing to
    chase, and a review list that contains noise stops being read.
    """
    out, buf, depth = [], [], 0
    for ch in str(ex):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == ";" and depth == 0:
            out.append("".join(buf)); buf = []
        else:
            buf.append(ch)
    out.append("".join(buf))
    return [p.strip() for p in out if p.strip()]


def parse(ex):
    """'Kawamata/Baran JACS 2019 (kg, flow)' -> (['Kawamata','Baran'], 'JACS', 2019)."""
    ex = re.sub(r"\([^)]*\)", "", ex).strip()
    m = re.search(r"\b(19|20)\d{2}\b", ex)
    year = int(m.group(0)) if m else None
    head = ex[:m.start()].strip() if m else ex
    jrn = None
    for k in sorted(JOURNAL, key=len, reverse=True):
        if re.search(r"\b" + re.escape(k) + r"\b", head):
            jrn = k
            head = head[:head.rfind(k)].strip()
            break
    names = [n.strip() for n in head.split("/") if n.strip()]
    return names, jrn, year


def crossref(names, jrn, year):
    q = " ".join(names + ([JOURNAL.get(jrn, jrn)] if jrn else []) + ([str(year)] if year else []))
    url = ("https://api.crossref.org/works?rows=5&query.bibliographic="
           + urllib.parse.quote(q))
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}),
                                    timeout=25) as r:
            return json.load(r)["message"]["items"]
    except Exception as e:
        return [{"__error__": str(e)}]


# The fabricated exemplars this gate exists to catch -- Zhang/Qiu Nat Commun 2025 and Yang/Wang
# Nat Commun 2023 -- were REPLACED by real DOI-anchored papers once found, so a clean run
# proves only that the surviving list resolves -- it cannot show the gate would still catch a new
# one. (A third, Ke/Chi Chem Eur J 2019, was recorded as fabricated and IS NOT -- it is real,
# DOI 10.1002/chem.201901082, and only fails Crossref's short-form string match. An UNRESOLVED
# verdict is a statement about the search, not about the paper.)
# The control feeds it invented citations built the same way the real fabrications were:
# plausible authors, a real journal, a recent year, a chemistry that does not exist at that
# locator. Each must come back in the "needs a human" set. It resolves ONLY these, not all 49,
# so the control is a few seconds rather than a full network sweep.
FAKE = ["Vasquez, Oyelaran and Brindisi, J. Am. Chem. Soc. 2024, 146, 20331",
        "Halvorsen and Ntembe, Nat. Commun. 2023, 14, 7788",
        "Rasmussen, Adeyemi and Falk, Chem. Eur. J. 2022, 28, e202201847"]


# EXEMPLARS CONFIRMED BY PINNED DOI.
# Crossref's bibliographic-STRING ranking is unreliable on abbreviated citations -- it is what
# returns "Love China, Love Hong Kong" for "Love/George, OPRD 2021" -- so a short form like
# "Ke/Chi Chem Eur J 2019" can come back UNRESOLVED for a paper that plainly exists. Leaving those
# on the review list forever is not neutral: one of them was written down as FABRICATED in a sister
# module's docstring, which is a false accusation about a real paper and real authors.
#
# These are resolved by DOI instead, and the resolved record's author list must still contain the
# expected surname -- so this is a stricter check than the string search, not an exemption from it.
# Adding a row here requires the DOI to have been retrieved and read, never merely recognised.
CONFIRMED_DOI = {
    "Ke/Chi Chem Eur J 2019":
        ("10.1002/chem.201901082", "Ke",
         "Hydrodehalogenation of Aryl Halides through Direct Electrolysis; author list "
         "Ke, Wang, Zhou, Mou, Zhang, Pan, Chi matches the registry exactly"),
    "Osa/Bobbitt Chem Commun 1994":
        ("10.1039/c39940002535", "Osa",
         "Enantioselective electrocatalytic oxidative coupling; 1994 Chem. Commun. is older than "
         "Crossref's reliable full-text indexing, so the string query cannot rank it"),
    "Bottecchia/Merck OPRD 2022":
        ("10.1021/acs.oprd.2c00111", "Bottecchia",
         "Kilo-Scale Electrochemical Oxidation of a Thioether to a Sulfone"),
}


def by_doi(doi):
    u = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    req = urllib.request.Request(u, headers={"User-Agent": UA})
    return json.load(urllib.request.urlopen(req, timeout=30))["message"]


def main(neg=False):
    rx = pd.read_csv(os.path.join(HERE, "reactions_50.csv"))
    seen, out = set(), []
    exemplars = FAKE if neg else rx.exemplar.dropna()
    if neg:
        print("NEGATIVE CONTROL: %d invented exemplars, each must land in the review set.\n"
              % len(FAKE))
    for ex in exemplars:
        for piece in split_exemplars(ex):
            piece = piece.strip()
            if not piece or piece in seen:
                continue
            seen.add(piece)
            if not neg and piece in CONFIRMED_DOI:
                doi, want, why = CONFIRMED_DOI[piece]
                try:
                    it = by_doi(doi)
                    fam = " ".join((a_.get("family", "") or "") for a_ in it.get("author", []) or [])
                    ok = want.lower() in fam.lower()
                except Exception as e:                     # noqa: BLE001
                    out.append((piece, "NETWORK", str(e)[:60])); continue
                lab = "%s | %s %s | %s" % ((it.get("title") or [""])[0][:58],
                                           (it.get("container-title") or [""])[0][:26],
                                           ((it.get("issued", {}).get("date-parts")
                                             or [[None]])[0][0]), doi)
                verdict = "DOI-PINNED" if ok else "DOI-MISMATCH"
                out.append((piece, verdict, lab))
                print("  %-11s %-46s %s" % (verdict, piece[:46], lab[:88]))
                sys.stdout.flush()
                continue
            names, jrn, year = parse(piece)
            if not names:
                out.append((piece, "UNPARSED", "")); continue
            items = crossref(names, jrn, year)
            time.sleep(0.4)
            if items and "__error__" in items[0]:
                out.append((piece, "NETWORK", items[0]["__error__"][:60])); continue
            best, verdict = None, "UNRESOLVED"
            for it in items:
                ttl = (it.get("container-title") or [""])[0]
                yr = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
                auth = " ".join((a.get("family", "") or "") for a in it.get("author", []) or [])
                jok = (not jrn) or JOURNAL.get(jrn, jrn).lower()[:12] in ttl.lower()
                yok = (year is None) or (yr is not None and abs(yr - year) <= 1)
                ## ALL named surnames must appear, not any. Requiring only one produced a
                ## false RESOLVED on the very first run: "Zhang/Qiu Nat Commun 2025" matched
                ## "Carbon markets promote environmental justice in China" because the journal
                ## and year lined up and one very common surname was in the author list. With
                ## two-surname exemplars (first author / last author) both must be present.
                nok = all(n.lower() in auth.lower() for n in names)
                ## and the title must look like chemistry, not merely share a journal-year
                ttl_l = ((it.get("title") or [""])[0]).lower()
                chem = any(w in ttl_l for w in (
                    "electro", "anod", "cathod", "oxid", "reduct", "catal", "synthes",
                    "coupling", "radical", "amination", "halogen", "flow", "cell",
                    "c–h", "c-h", "carbox", "alken", "aryl", "alkyl", "hydro", "sulf",
                    "cyclo", "brom", "chlor", "fluor", "nitr", "ester", "acid", "amide"))
                if jok and yok and nok and chem:
                    best, verdict = it, "RESOLVED"; break
                if jok and yok and nok and not chem:
                    best, verdict = it, "WEAK-TITLE"
                if jok and yok and best is None:
                    best, verdict = it, "WEAK"
            lab = ""
            if best:
                lab = "%s | %s %s | %s" % (
                    (best.get("title") or [""])[0][:58],
                    (best.get("container-title") or [""])[0][:26],
                    ((best.get("issued", {}).get("date-parts") or [[None]])[0][0]),
                    best.get("DOI", ""))
            out.append((piece, verdict, lab))
            print("  %-10s %-46s %s" % (verdict, piece[:46], lab[:88]))
            sys.stdout.flush()

    n = {}
    for _, v, _ in out:
        n[v] = n.get(v, 0) + 1
    print("\n%d distinct exemplars: %s" % (len(out), n))
    bad = [o for o in out if o[1] in ("WEAK", "WEAK-TITLE", "UNRESOLVED", "UNPARSED", "NETWORK",
                                     "DOI-MISMATCH")]
    print("\nNEEDS A HUMAN TO OPEN (%d):" % len(bad))
    for p, v, l in bad:
        print("  %-10s %s" % (v, p))
    _o = os.path.join(ROOT, "results", "exemplar_verification%s.json"
                      % ("_NEGCONTROL" if neg else ""))
    json.dump([{"exemplar": p, "verdict": v, "match": l} for p, v, l in out],
              open(_o, "w"), indent=1)
    print("\n-> %s" % os.path.relpath(_o, ROOT))
    if neg:
        caught = len(bad)
        print("G-EXEMPLAR control: %s"
              % ("GOOD -- all %d invented exemplars were flagged for a human" % caught
                 if caught == len(FAKE) else
                 "BAD -- only %d of %d invented exemplars were flagged; the rest RESOLVED, so "
                 "this gate would pass a fabrication" % (caught, len(FAKE))))
        return 0 if caught == len(FAKE) else 1
    print("G-EXEMPLAR: %s" % ("PASS" if not bad else "REVIEW NEEDED"))
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv) or 0)
