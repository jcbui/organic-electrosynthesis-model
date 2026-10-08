"""Does every journal citation in the registry resolve to the paper it names?

    cd Section4_Model && python data/verify_citations.py            # live rows
    cd Section4_Model && python data/verify_citations.py --all      # every row
    cd Section4_Model && python data/verify_citations.py --negative-control

WHY
---
The failure mode this guards against is specific and has already happened in this repository. A
citation read "Wallnofer-Ogris, Front. Chem. Eng. 2024, 6, 1384772". That locator is real, but it
belongs to *Eichner, Amiri, Burheim & Lamb*, and the paper reports a value an order of magnitude
below what was claimed of it. A plausible author list had been attached to somebody else's
locator, and it survived multiple drafts in both the SI and the manuscript body.

That is a CHIMERA: the locator and the author list come from different papers. It is invisible to
every internal check, because nothing inside the project knows what the outside world published.
This script asks Crossref.

WHAT IT CHECKS, AND WHAT IT CANNOT
----------------------------------
For each citation carrying a journal locator it resolves the DOI (or, absent one, the closest
bibliographic match) and compares four things against what the registry claims: the first author's
surname, the journal, the year, and the volume. A first-author surname that does not appear in the
resolved author list is the chimera signature and is reported as FAIL.

It cannot check books and handbooks -- Poling, CRC, Incropera, Bard, Cussler -- because Crossref
does not index them by page. Those carry a different risk (a real book cited for a number nobody
looked up), which only opening the page settles; they are listed as UNVERIFIABLE rather than
silently passed, so the count of what remains unchecked is always visible.

It also cannot tell whether the NUMBER attributed to a correctly-identified paper is really in it.
That is what the retrieved-PDF checks are for.
"""
import json
import os
import re
import subprocess
import unicodedata
import sys
import time
import urllib.parse

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "citation_verification.json")

# Sources Crossref cannot adjudicate: books, handbooks, standards bodies, internal references.
NON_JOURNAL = re.compile(
    r"Handbook of Chemistry|Properties of Gases and Liquids|Fundamentals of Heat|"
    r"Electrochemical Methods|Diffusion: Mass Transfer|SI Brochure|NIST Chemistry WebBook|"
    r"this registry|Table S2 per-row|reactions_50\.csv|build_reactions50|declared |audited:|"
    r"no source supports|Organic Electrochemistry|dissertation|Foxboro|ASTM|"
    r"^--|no page-anchored|not page-verified|^NOT the|Table S\d+ per-row|per-row citations|"
    r"^\(|conventions$|^method:", re.I)

# Citations Crossref cannot adjudicate but that were verified by OPENING THE PDF. Each entry
# names the file in the repository and what was checked in it, so the exemption carries its own
# evidence instead of merely suppressing a warning. Crossref indexes neither ISCA's Research
# Journal of Chemical Sciences nor Indian J. Chem. Section A, so its bibliographic matcher lands
# on an unrelated paper and reports a first-author mismatch that is an indexing gap, not a chimera.
LOCALLY_VERIFIED = {
    "Noel, Cao & Laudadio": (
        "papers for model/acs.accounts.9b00412.pdf",
        "Crossref's OWN RECORD IS CORRUPT for this DOI: it stores the first author's family "
        "name as 'Noe?l' with a LITERAL ASCII QUESTION MARK (U+003F, codepoints 4e 6f 65 3f 6c), "
        "not an o-diaeresis, so no amount of Unicode normalisation can match it and deaccent() "
        "correctly cannot either. Everything else in the record resolves: Accounts of Chemical "
        "Research, 2019, volume 52. The retrieved PDF's title page reads 'The Fundamentals Behind "
        "the Use of Flow Reactors in Electrochemistry', Accounts of Chemical Research special "
        "issue 'Electrifying Synthesis', by Timothy Noel, Yiran Cao and Gabriele Laudadio "
        "(Eindhoven University of Technology). Author order and journal match the citation "
        "exactly; this is an index defect, not a chimera."),
    "Ansari & Singh": (
        "papers for model/ansari_singh_2022_RJCS_12_67-69_acetonitrile_water_viscosity_density.pdf",
        "Retrieved 2026-08-22 from isca.in. Masthead confirms Res. J. Chem. Sci. Vol. 12(1), "
        "67-69, February 2022, 'Viscosities and Densities of Acetonitrile-water systems at 25 C', "
        "Mahzbeen Ansari and Shatrughan Prasad Singh. All four values the registry attributes to "
        "Table-1 p. 68 are present in the text: 0.973, 0.9588, 0.910, 0.9380. The paper's own "
        "neat-MeCN values (0.7767 g cm-3, 0.346 cP) agree with solvents.csv (0.776, 0.343)."),
    "Gopal & Jha": (
        "papers for model/gopal_jha_1977_IndianJChem_15A_80-83_ionic_conductivities_DMF_PC.pdf",
        "Retrieved 2026-08-22 from the NIScPR open repository. Masthead confirms Indian J. Chem. "
        "Vol. 15A, February 1977, pp. 80-83, 'Cationic Transport Numbers of Potassium Iodide & "
        "Solvation of Ions in N,N'-Dimethylformamide & Propylene Carbonate', Ram Gopal & J. S. "
        "Jha, Lucknow University. Table 2 ('IONIC CONDUCTIVITIES IN DMF AND PC AT VARIOUS "
        "TEMPERATURES') DMF 25 C column carries Et4N+ 35.39, Na+ 29.81, I- 52.11 and ClO4- 52.67 "
        "-- every value the registry attributes to it. The OCR prints decimal points as middle "
        "dots, which is why a literal string search for '29.81' fails on the extracted text."),
    "Bhat, Mohan & Susha": (
        "papers for model/bhat_mohan_susha_1996_IndianJChem_35A_825-831_perchlorate_solvation_DMF.pdf",
        "Retrieved 2026-08-22 from the NIScPR open repository. Masthead confirms Indian J. Chem. "
        "Vol. 35A, October 1996, pp. 825-831, 'Solvation behaviour of HClO4, NaClO4 and KClO4 "
        "species under varying conditions', J Ishwara Bhat, T P Mohan & C B Susha, Mangalore "
        "University. Table I p. 827 (not 826 -- see below) gives NaClO4 in the DMF column as "
        "80/76/80/78 at 293 K across the four conductance models (mean 78.5) and 89/86/89/88 at "
        "303 K (mean 88.0); interpolating to 298 K gives 83.25, reproducing the 83.3 the registry "
        "cross-validates against. NOTE: the registry's locator says p. 826; the table prints on "
        "p. 827 in the repository scan. The value is right, the page is off by one."),
}

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
# "Author..., Journal Year, Vol, pages"
CIT_RE = re.compile(r"^(?P<auth>.+?),\s*(?P<jour>[A-Z][^,]*?)\s*(?P<year>(?:19|20)\d{2}),\s*"
                    r"(?P<vol>\d+)")


# A NEGATIVE CONTROL MUST NEVER WRITE THE ARTIFACT IT PERTURBS -- see the note in
# data/sensitivity_dma_viscosity.py. Controls write a _NEGCONTROL sibling instead.
def _out(path, neg):
    return path[:-5] + "_NEGCONTROL.json" if neg and path.endswith(".json") else path

def deaccent(x):
    """Noel vs Noel: Crossref returns the accented form and the registry the ASCII one. A
    diacritic is not a chimera, and treating it as one buries the real signal in noise."""
    return "".join(c for c in unicodedata.normalize("NFKD", x or "")
                   if not unicodedata.combining(c))


def crossref(url):
    try:
        r = subprocess.run(["curl", "-s", "--max-time", "20", "-H",
                            "User-Agent: provenance-audit (mailto:jcb9926@nyu.edu)", url],
                           capture_output=True, text=True, timeout=30)
        return json.loads(r.stdout)
    except Exception:
        return None


def resolve(cit):
    m = DOI_RE.search(cit)
    if m:
        doi = m.group(0).rstrip(".,;)")
        d = crossref("https://api.crossref.org/works/" + urllib.parse.quote(doi))
        if d and d.get("status") == "ok":
            return d["message"], "doi"
    # strip parenthetical asides: they are our commentary, not part of the bibliographic record,
    # and they push Crossref's matcher onto the wrong paper.
    clean = re.sub(r"\([^)]*\)", " ", cit)
    clean = re.sub(r"\s{2,}", " ", clean).strip()
    q = urllib.parse.quote(clean[:250])
    d = crossref("https://api.crossref.org/works?rows=1&query.bibliographic=" + q)
    if d and d.get("status") == "ok" and d["message"]["items"]:
        return d["message"]["items"][0], "search"
    return None, None


def main(scope_all=False, negative_control=False):
    reg = pd.read_csv(os.path.join(HERE, "parameters_provenance.csv"))
    with open(os.path.join(ROOT, "results", "registry_liveness.json")) as f:
        dead = set(json.load(f)["dead_parameters"])
    rows = reg if scope_all else reg[~reg.parameter.isin(dead)]

    # A DECLARED BASIS IS NOT A CITATION. Rows with no external source used to print
    # "-- (no source supports this value)"; they now state what the value actually rests on, and
    # those sentences MENTION real papers ("Krumgalz 1983, Table 4, p. 579 prints a dash for
    # ClO4-") without claiming them as the source of the number. Resolving such a sentence as a
    # bibliographic entry and failing its author match would be a false chimera report.
    # The loophole is closed by construction: only an ASSUMPTION-class row may carry a declared
    # basis, so a measured or derived row can never hide behind the marker, and the papers those
    # sentences mention all carry their own primary citations on other rows anyway.
    DECLARED = re.compile(r"^(Declared\b|-- \()")
    # A citation that is only a pointer to another table of this SI ("Table S2", "Table S6 and Table S11",
    # "Table S2 per-row citations") is not a bibliographic entry: the rows it points to carry their own
    # citations. Sent to Crossref's bibliographic search it resolves to whatever paper ranks first and reads
    # as a chimera on one run and not the next (2026-10-05). Skip it by shape, for every class.
    INTERNAL = re.compile(r"^Table S\d+( and Table S\d+)*( per-row citations)?$")
    cits, declared_rows, internal_rows = {}, [], []
    for _, x in rows.iterrows():
        cit = str(x.citation).strip()
        if INTERNAL.match(cit):
            internal_rows.append(x.parameter)
            continue
        if DECLARED.match(cit):
            if str(x.provenance_class).strip() != "assumption":
                raise SystemExit("%s is class '%s' but carries a DECLARED basis instead of a "
                                 "citation; only assumption-class rows may do that"
                                 % (x.parameter, x.provenance_class))
            declared_rows.append(x.parameter)
            continue
        for part in re.split(r";\s*(?=[A-Z])", cit):
            part = part.strip()
            if len(part) > 20 and not NON_JOURNAL.search(part):
                cits.setdefault(part, []).append(x.parameter)

    if negative_control:
        # A CHIMERA is an author list bolted onto somebody else's locator, so the control must
        # use a locator that RESOLVES -- otherwise it exercises the "unresolved" path and never
        # reaches the author check. The first attempt injected the real Wallnofer-Ogris locator,
        # whose Crossref bibliographic match is a junk record ("Inside front cover") with no
        # author list, so it was filed as unresolvable and the control silently passed nothing.
        # This one is the exact shape of the failure: a real, resolvable DOI wearing the wrong
        # authors.
        cits["Wallnofer-Ogris & Fabricated, Beilstein J. Org. Chem. 2011, 7, 1108-1114, "
             "DOI 10.3762/bjoc.7.127"] = ["<injected chimera>"]

    print("journal-style citations to check: %d  (scope: %s)"
          % (len(cits), "all rows" if scope_all else "live rows only"))
    ok, fail, unres = [], [], []
    for cit, params in sorted(cits.items()):
        m = CIT_RE.match(cit)
        surname = re.split(r"[ ,&]", cit.strip())[0].strip()
        surname = re.sub(r"[^A-Za-z\-]", "", surname)
        meta, how = resolve(cit)
        time.sleep(0.2)
        if meta is None:
            unres.append((cit, params, "", ""))
            print("  [?]  %s\n         -> NOT RESOLVED by Crossref" % cit[:110])
            continue
        authors = " ".join((a.get("family", "") or "") for a in meta.get("author", []) or [])
        authors_n = deaccent(authors)
        title = (meta.get("title") or [""])[0]
        jour = (meta.get("container-title") or [""])[0]
        yr = str((meta.get("issued", {}).get("date-parts") or [[None]])[0][0])
        vol = str(meta.get("volume", ""))
        # the chimera signature: the surname the citation leads with is not an author of the
        # paper the locator resolves to
        base = deaccent(surname).split("-")[0]
        # An empty Crossref author list means the record is incomplete, NOT that the paper is a
        # chimera. Kharkiv Univ. Bull. is indexed by DOI with no contributor metadata at all;
        # calling that a fabricated citation would be a false accusation.
        if not authors.strip():
            unres.append((cit, params, meta.get("DOI", ""), (meta.get("title") or [""])[0]))
            print("  [?]  %s\n         -> resolved (%s) but Crossref carries NO author list: %s"
                  % (cit[:104], how, (meta.get("title") or [""])[0][:70]))
            continue
        hit = bool(base) and (base.lower() in authors_n.lower())
        cy = m.group("year") if m else None
        cv = m.group("vol") if m else None
        bad = []
        local = next((k for k in LOCALLY_VERIFIED if cit.startswith(k)), None)
        if not hit and local:
            path, note = LOCALLY_VERIFIED[local]
            print("  [pdf] %s" % cit[:104])
            print("         -> Crossref mismatch OVERRIDDEN by the retrieved PDF: %s" % path)
            ok.append(dict(citation=cit, resolved_authors="(verified from local PDF)",
                           title=note, journal="", year="", volume="", doi="",
                           issues=["crossref-index-gap"], how="local-pdf", params=params))
            continue
        if not hit:
            bad.append("first author %r absent from %r" % (surname, authors[:90]))
        if cy and yr and yr != "None" and cy != yr:
            bad.append("year %s vs %s" % (cy, yr))
        if cv and vol and cv != vol:
            bad.append("volume %s vs %s" % (cv, vol))
        tag = "FAIL" if not hit else ("warn" if bad else "ok  ")
        print("  [%s] %s" % (tag, cit[:104]))
        print("         -> %s, %s %s, %s" % (authors[:70] or "(no authors)", jour[:44], yr, vol))
        if bad:
            print("         !! " + "; ".join(bad))
        (fail if not hit else ok).append(dict(citation=cit, resolved_authors=authors,
                                              title=title, journal=jour, year=yr, volume=vol,
                                              doi=meta.get("DOI", ""),
                                              issues=bad, how=how, params=params))

    print("\ninternal table pointer, not a citation: %d" % len(internal_rows))
    print("declared basis, not a citation    : %d (assumption-class only, asserted)"
          % len(declared_rows))
    print("resolved and first author matches : %d" % len(ok))
    print("CHIMERA SUSPECTS (author mismatch) : %d" % len(fail))
    print("not resolvable by Crossref         : %d" % len(unres))
    non_journal = sorted({p.strip() for _, x in rows.iterrows()
                          for p in re.split(r";\s*(?=[A-Z])", str(x.citation))
                          if len(p.strip()) > 20 and NON_JOURNAL.search(p)})
    print("books/handbooks Crossref cannot adjudicate: %d (listed in the JSON)" % len(non_journal))

    rep = dict(n_checked=len(cits), ok=ok, chimera_suspects=fail,
               unresolved=[dict(citation=c, params=p_, doi=d_, title=t_)
                           for c, p_, d_, t_ in unres], non_journal=non_journal)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    _o = _out(OUT, negative_control)
    with open(_o, "w") as f:
        json.dump(rep, f, indent=2)
    print("wrote %s" % os.path.relpath(_o, ROOT))

    if negative_control:
        fired = any("Wallnofer" in f_["citation"] for f_ in fail)
        print("\nnegative control: injected the known chimera locator")
        print("  gate fired on it: %s" % fired)
        if not fired:
            raise AssertionError("negative control did not fire")
        return rep
    print("\nG-CITE: %s" % ("PASS" if not fail else "FAIL"))
    if fail:
        raise AssertionError("chimera suspects: %s" % [f_["citation"][:60] for f_ in fail])
    return rep


if __name__ == "__main__":
    main(scope_all="--all" in sys.argv, negative_control="--negative-control" in sys.argv)
