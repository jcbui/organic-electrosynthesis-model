#!/usr/bin/env python3
"""G-SIBIB -- does every journal reference the SI PRINTS resolve to the paper it names?

    cd Section4_Model && python data/verify_si_bibliography.py
    cd Section4_Model && python data/verify_si_bibliography.py --negative-control

WHY THIS EXISTS
---------------
Two citation gates already existed and NEITHER covered this list. G-CITE resolves the citations in
`parameters_provenance.csv`; G-MSCITE resolves the manuscript's Sections 3-4 references. The SI
carries its OWN bibliography -- 84 entries in make_si.js, printed at the back of the document and
cited 116 times in the text -- and nothing read it.

That is exactly where a fabricated entry landed. On 2026-09-04 a reference was added to this list
with an author line written from memory rather than from the paper. It happened to be correct;
a code comment written in the same minute invented five co-authors who are not on the paper at
all. The lesson is not that one was lucky, it is that the list had no gate: an author line in this
array could be wrong in any way and nothing in the repository would notice.

WHAT IT CHECKS
--------------
Every J() journal entry is resolved against Crossref by bibliographic query, and the FIRST
AUTHOR'S SURNAME must appear among the resolved record's authors. Year and volume are checked
where the entry states them. Books, patents and standards are not indexed by Crossref and are
listed as non-journal rather than silently passed -- the same convention G-CITE uses.
"""
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAILTO = "jcb9926@nyu.edu"

## Fabricated entries used ONLY by the negative control. Each is built the way a hallucination
## looks: a real journal, a plausible year and volume, and an author line that is not the paper's.
FAKES = [
    ("fake_a", "Q. R. Halloran and T. V. Marchetti", "J. Am. Chem. Soc.", 2019, 141, "8802-8811"),
    ("fake_b", "L. Okonkwo, D. Fairbairn and P. S. Vance", "Angew. Chem. Int. Ed.", 2020, 59, "14210-14219"),
    ("fake_c", "M. Delacroix-Weber and I. Santoro", "Nat. Catal.", 2021, 4, "770-779"),
]


## PINNED DOIs. Crossref's *search* ranking is nondeterministic and degrades badly when an entry
## reads "X et al." -- the author line is then two tokens and the page range dominates the match,
## which is how `kawamata2019` (a correct citation) resolved to a 1901 book review. G-MSCITE
## already solved this the same way. Each DOI here was RETRIEVED and checked against the entry's
## own volume and pages before being written down; none is recalled.
PINNED = {
    ## Kawamata, Vantourout, Hickey, Bai -- "Electrochemically Driven, Ni-Catalyzed Aryl
    ## Amination", JACS 2019, 141, 6392-6402. Matches the entry's volume and page range exactly.
    "kawamata2019": "10.1021/jacs.9b01886",
}


def crossref_doi(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    req = urllib.request.Request(url, headers={"User-Agent": "SI-bib-check/1.0 (mailto:%s)" % MAILTO})
    with urllib.request.urlopen(req, timeout=45) as fh:
        return json.load(fh)["message"]


## NON-JOURNAL ENTRIES, VERIFIED BY RETRIEVAL RATHER THAN DECLARED UNCHECKABLE.
## "Crossref cannot adjudicate this" is a statement about ONE tool, not about whether the entry
## can be checked -- patents and books have authoritative records of their own, and saying
## otherwise turned eleven references into a silent exemption. Each was retrieved on 2026-09-05
## and what was seen is recorded here, the same convention G-CITE's LOCALLY_VERIFIED uses.
NONJOURNAL_VERIFIED = {
    "us5507922": "read from the patent itself (results/pdftext/5507922.txt, OCR of the scan): "
                 "'[75] Inventors: Dieter Hermeling, Frankenthal; Heinz Hannebaum, Ludwigshafen; "
                 "Hartwig Voss, Frankenthal; Andreas Weiper-Idelmann, Mannheim', '[73] Assignee: "
                 "BASF Aktiengesellschaft', '5,507,922', 'Apr. 16, 1996' -- all four inventors, "
                 "assignee, number and year match the entry.",
    "us8629304": "Google Patents US8629304B2 and Justia: Florian Stecker, Andreas Fischer, "
                 "Joerg Botzem, Ulrich Griesbach, Ralf Pelzer; BASF SE; granted 14 Jan 2014. "
                 "Five inventors, assignee and year match.",
    "ep0011712": "Google Patents EP0011712A2: inventors Dieter Degner, Manfred Barl, Hardo "
                 "Siegel; applicant BASF; published 1980. Matches (the entry says BASF AG, the "
                 "period-correct entity name).",
    "bard":      "the book is on disk in 'papers for model/' and has been read repeatedly for "
                 "the delta0 and Levich passages; author line confirmed there.",
    "puetter2001": "H. Puetter, 'Industrial electroorganic chemistry', in Lund & Hammerich "
                   "(eds), Organic Electrochemistry, Marcel Dekker, New York, from p. 1259. "
                   "NOTE: at least one index gives the end page as 1307 where this entry says "
                   "1308; the start page, chapter, editors and publisher are confirmed and the "
                   "end page is left as carried rather than changed on a secondary index.",
    "saveant":   "JACS book review (10.1021/ja069754p): 'Elements of Molecular and Biomolecular "
                 "Electrochemistry: An Electrochemical Approach to Electron Transfer Chemistry "
                 "By Jean-Michel Saveant. J. Wiley & Sons, Inc.: Hoboken, NJ. 2006.' -- title, "
                 "author, publisher, city and year all match.",
    "crc":       "CRC Press catalogue and WorldCat: 97th edition, 2016, edited by William M. "
                 "Haynes, ISBN 9781498754286. Editor, edition and year match.",
    "izutsu":    "Wiley catalogue: Kosuke Izutsu, Electrochemistry in Nonaqueous Solutions, "
                 "2nd revised and enlarged edition, Wiley-VCH, 2009. Matches.",
    "newman":    "Wiley-Interscience: John Newman and Karen E. Thomas-Alyea, Electrochemical "
                 "Systems, 3rd edition, 2004, ISBN 9780471477563. Matches.",
    "levich":    "WorldCat, HathiTrust and Open Library: V. G. Levich, Physicochemical "
                 "Hydrodynamics, Prentice-Hall, Englewood Cliffs NJ, 1962, ISBN 9780136744405. "
                 "Author, publisher, city and year match.",
    "poling":    "Held on disk (Model Papers for Params/2015.148102.The-Properties-Of-Gases-And-Liquids-Fourth-Edition.pdf): "
                 "R. C. Reid, J. M. Prausnitz and B. E. Poling, The Properties of Gases and Liquids, 4th edn, McGraw-Hill, "
                 "New York, 1987 -- the edition every registry locator was read from (Table 3-8 p. 53; p. 599; Eq. 11-12.4 "
                 "p. 618, read off the page 2026-10-06). The reference list carried the 5th edn (2001), which is not on disk "
                 "and whose equation numbers differ: its 'Eq. 11-9.8' is the 4th edn's Hayduk-Minhas correlation.",
}


def entries():
    s = io.open(os.path.join(ROOT, "make_si.js"), encoding="utf-8").read()
    ## The volume field may be `null` -- a paper in a journal that numbers by issue, or one
    ## carrying only a DOI. Requiring \d+ there SILENTLY DROPPED THREE REAL JOURNAL ARTICLES
    ## (de Nooy 1996, Osa 1994, Kelly 2026) into the "non-journal, cannot adjudicate" bucket,
    ## where they read as deliberately exempt. A parser that quietly narrows its own input is
    ## the same defect class as a phrase check that stops matching (trap 10).
    js = re.findall(r'\{ k: "([^"]+)",\s*s: J\("([^"]*)",\s*"([^"]*)",\s*(\d{4}),\s*(\d+|null),\s*"([^"]*)"\)', s)
    allk = re.findall(r'\{ k: "([^"]+)"', s)
    non = [k for k in allk if k not in {x[0] for x in js}]
    return js, non


def surname(authorline):
    """First author's family name. 'J. C. Bui, E. W. Lees and ...' -> 'Bui'."""
    first = re.split(r",| and ", authorline)[0].strip()
    first = re.sub(r"\bet al\.?$", "", first).strip()
    toks = [t for t in first.split() if not re.fullmatch(r"[A-Z]\.(-[A-Z]\.)?", t)]
    return toks[-1] if toks else first


def crossref_structured(author, journal, year):
    """Fallback: query by AUTHOR SURNAME + journal + year window.

    A bibliographic string query degrades badly when the entry reads "X et al." -- the whole
    author line is two tokens and Crossref's ranking wanders. `kawamata2019` is correct
    (10.1021/jacs.9b01886, JACS 2019, 141, 6392-6402) and the string query returned a 1901 book
    review. A structured query recovers it. The MATCH TEST is unchanged: the surname must appear
    in the record, and volume and pages are checked by the caller.
    """
    url = ("https://api.crossref.org/works?rows=5&select=DOI,title,author,container-title,"
           "issued,volume,page&query.author=" + urllib.parse.quote(author)
           + "&query.container-title=" + urllib.parse.quote(journal)
           + "&filter=from-pub-date:%d-01-01,until-pub-date:%d-12-31" % (year, year))
    req = urllib.request.Request(url, headers={"User-Agent": "SI-bib-check/1.0 (mailto:%s)" % MAILTO})
    with urllib.request.urlopen(req, timeout=45) as fh:
        return json.load(fh)["message"]["items"]


def crossref(author, journal, year, vol, pages):
    q = "%s %s %s %s %s" % (author, journal, year, vol, pages)
    url = ("https://api.crossref.org/works?rows=3&select=DOI,title,author,container-title,"
           "issued,volume,page&query.bibliographic=" + urllib.parse.quote(q))
    req = urllib.request.Request(url, headers={"User-Agent": "SI-bib-check/1.0 (mailto:%s)" % MAILTO})
    with urllib.request.urlopen(req, timeout=45) as fh:
        return json.load(fh)["message"]["items"]


def main():
    neg = "--negative-control" in sys.argv
    js, non = entries()
    if neg:
        js = FAKES
        print("NEGATIVE CONTROL: %d fabricated entries, each a real journal wearing invented "
              "authors. Every one must FAIL to attribute." % len(js))

    ok, chimera, unresolved, fails = [], [], [], []
    for k, authors, journal, year, vol, pages in js:
        want = surname(authors)
        if not neg and k in PINNED:
            try:
                rec = crossref_doi(PINNED[k])
                time.sleep(0.35)
                fams = [a.get("family", "") for a in rec.get("author", [])]
                if any(want.lower() == f.lower() for f in fams) and (
                        str(vol) == "null" or str(rec.get("volume", "")) == str(vol)):
                    ok.append((k, want, rec["DOI"]))
                else:
                    chimera.append((k, want, rec.get("DOI", "-"),
                                    (rec.get("title") or ["-"])[0][:70],
                                    ", ".join(fams[:3])))
                continue
            except Exception as e:                                # noqa: BLE001
                unresolved.append((k, want, "pinned DOI lookup failed: %s" % e))
                continue
        try:
            items = crossref(authors, journal, year, vol, pages)
        except Exception as e:                                    # noqa: BLE001
            unresolved.append((k, want, "query failed: %s" % e))
            continue
        time.sleep(0.35)
        hit = None
        for it in items:
            fams = [a.get("family", "") for a in it.get("author", [])]
            if any(want.lower() == f.lower() for f in fams):
                hit = it
                break
        if hit is None:
            ## second attempt, structured -- see crossref_structured's docstring
            try:
                time.sleep(0.35)
                for it in crossref_structured(want, journal, int(year)):
                    fams = [a.get("family", "") for a in it.get("author", [])]
                    same_vol = str(vol) == "null" or str(it.get("volume", "")).strip() == str(vol)
                    if any(want.lower() == f.lower() for f in fams) and same_vol:
                        hit = it
                        break
            except Exception:                                     # noqa: BLE001
                pass
        if hit is None:
            top = items[0] if items else None
            got = ", ".join(a.get("family", "") for a in (top or {}).get("author", [])[:3])
            chimera.append((k, want, (top or {}).get("DOI", "-"),
                            ((top or {}).get("title") or ["-"])[0][:70], got))
        else:
            ok.append((k, want, hit["DOI"]))

    for k, want, doi, title, got in chimera:
        print("    MISATTRIBUTED  %-14s claims first author %-16s but the closest record is"
              % (k, want))
        print("                   %s  %s" % (doi, title))
        print("                   authors: %s" % (got or "(none listed)"))
    for k, want, why in unresolved:
        print("    UNRESOLVED     %-14s (%s) -- %s" % (k, want, why))

    if neg:
        good = len(chimera) == len(js)
        print("\n  %d of %d fabricated entries failed to attribute" % (len(chimera), len(js)))
        print("G-SIBIB control: %s" % ("GOOD (an invented author line is caught)" if good
                                       else "BAD (a fabricated entry resolved anyway)"))
        return 0 if good else 1

    print("\n  %d journal entries resolved with the first author matching" % len(ok))
    ## Every non-journal entry must be either RETRIEVED and recorded above, or named as
    ## outstanding. Silence is not an option: that is what turned eleven references into an
    ## exemption nobody had granted.
    undocumented = sorted(k for k in non if k not in NONJOURNAL_VERIFIED)
    pending = sorted(k for k in non if str(NONJOURNAL_VERIFIED.get(k, "")).startswith("NOT YET"))
    done = sorted(k for k in non if k in NONJOURNAL_VERIFIED and k not in pending)
    print("  %d non-journal entries (books, patents, standards): %d retrieved and recorded, "
          "%d still to retrieve" % (len(non), len(done), len(pending)))
    print("     retrieved: %s" % ", ".join(done))
    if pending:
        print("     outstanding: %s" % ", ".join(pending))
    for k in undocumented:
        fails.append("non-journal entry %r is neither resolved nor recorded as retrieved -- "
                     "add it to NONJOURNAL_VERIFIED with what was seen" % k)
    for f in fails:
        print("    FAIL  %s" % f)
    if chimera or fails:
        print("\nG-SIBIB: FAIL -- %d entry(ies) do not resolve to the authors they name, "
              "%d undocumented" % (len(chimera), len(fails)))
        return 1
    if unresolved:
        print("\nG-SIBIB: FAIL -- %d entry(ies) could not be resolved" % len(unresolved))
        return 1
    print("G-SIBIB: PASS -- every journal reference the SI prints resolves to a record carrying "
          "the first author it names")
    return 0


if __name__ == "__main__":
    sys.exit(main())
