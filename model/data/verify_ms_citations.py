"""Is every reference behind the Sections 3-4 model real, and correctly attributed?  (G-MSCITE)

    cd Section4_Model && python data/verify_ms_citations.py
    cd Section4_Model && python data/verify_ms_citations.py --negative-control

WHY
---
data/verify_citations.py (G-CITE) sweeps the 24 citations in the PARAMETER REGISTRY. It has never
looked at the manuscript. Sections 3 and 4 are where the transport and thermal model is stated and
defended, and their citations have never been resolved by anything.

TWO CHECKS, BOTH BY DOI
-----------------------
A. BIBLIOGRAPHY. Every numbered entry that carries a DOI is resolved against Crossref BY THAT DOI
   -- never by a bibliographic string search. That distinction is the whole design: a fuzzy
   `query.bibliographic` lookup returns "Love China, Love Hong Kong" for "Love/George, OPRD 2021",
   so a string-matching version of this gate reports failures that are artifacts of the matcher
   rather than defects in the paper. A DOI either resolves to the paper or it does not.

   The test is the CHIMERA test: the first author the manuscript prints must appear in the record
   the DOI resolves to. That failure mode has already occurred here once -- "Wallnofer-Ogris,
   Front. Chem. Eng. 2024, 6, 1384772" is really Eichner, Amiri, Burheim & Lamb, and the paper
   reports a value an order of magnitude below what was claimed of it.

B. IN-TEXT ATTRIBUTION. Every inline citation in Sections 3-4 and S8.2 names an author and a year.
   Each must correspond to a bibliography entry whose RESOLVED author list contains that surname.
   This is what catches an in-text attribution drifting off the reference it points to.

Year/journal/volume mismatches are reported as ADVISORY: Crossref's issued-date is the online
date for some publishers and page fields are uneven. Author mismatch is what fails the gate.
"""
import json
import os
import re
import subprocess
import sys
import unicodedata
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from docx_text import asserted_text                                      # noqa: E402

# A NEGATIVE CONTROL MUST NEVER WRITE THE ARTIFACT IT PERTURBS -- see the note in
# data/sensitivity_dma_viscosity.py. Controls write a _NEGCONTROL sibling instead.
def _out(path, neg):
    return path[:-5] + "_NEGCONTROL.json" if neg and path.endswith(".json") else path

from latest_ms import latest_ms   # shared resolver; the private copy here was pinned to a
# naming scheme the lineage left behind, so it gated a document 25 builds stale (2026-09-29)


MS = latest_ms()
OUT = os.path.join(ROOT, "results", "ms_citation_verification.json")
CACHE = os.path.join(ROOT, "results", "crossref_doi_cache.json")
SPANS = [(71, 112), (216, 222)]          # Section 3, Section 4, S8.2 -- from the numbered headings

JOURNAL_WORDS = {"science", "nature", "nat", "acs", "jacs", "chem", "joule", "pnas", "oprd",
                 "rce", "angew", "green", "adv", "front", "membranes", "annual", "journal"}


def deaccent(x):
    return "".join(c for c in unicodedata.normalize("NFKD", x or "") if not unicodedata.combining(c))


def bibliography(text):
    tail = text[text.rfind("References"):]
    parts = re.split(r"\((\d{1,3})\)(?=[A-ZÀ-ÿ])", tail)
    out = []
    for i in range(1, len(parts) - 1, 2):
        n, e = parts[i], parts[i + 1]
        doi = re.search(r"doi\.org/(10\.\S+?)(?:\.\s|\.$|\s|$)", e)
        # [A-Za-zÀ-ÿ] stops at Latin Extended-A: "Petrović" parsed as "Petrovi", which then
        # failed the exact author match and reported a real citation as misattributed.
        first = re.match(r"\s*([A-ZÀ-ÿĀ-ſ][A-Za-zÀ-ÿĀ-ſ''\-]+)", e)
        # The publication year is the one followed by ", volume". Neither looser rule works:
        # taking the FIRST year-like token reads one out of the TITLE (Lehnherr's "Overview of
        # Recent Scale-Ups in Organic Electrosynthesis (2000-2023)" was reported for weeks as
        # "manuscript says 2000, Crossref says 2024" -- the item agreeing with Crossref and the
        # parser disagreeing with both), and taking the LAST reads a PAGE (Petrovic's 2081,
        # Heard's 2035, El-Nagar's 2062, Weng's 1968). In this bibliography the year is the only
        # year-like token followed by a comma and a space; a title range closes with ")" and a
        # page range with an en-dash or a full stop.
        _m = re.search(r"\b((?:19|20)\d{2}),\s", e)
        yr = _m if _m else re.search(r"\b((?:19|20)\d{2})\b", e)
        out.append(dict(n=int(n), doi=doi.group(1).rstrip(".") if doi else None,
                        first=first.group(1) if first else None,
                        year=yr.group(1) if yr else None, raw=e.strip()[:170]))
    return out


def inline(paras):
    body = " ".join(paras[i] for a, b in SPANS for i in range(a, b))
    out, seen = [], set()
    for m in re.finditer(r"\(([^()]{6,200}?(?:19|20)\d{2}[^()]{0,140}?)\)", body):
        for part in m.group(1).split(";"):
            part = part.strip()
            ys = re.findall(r"(?:19|20)\d{2}", part)
            if not ys:
                continue
            am = re.match(r"([A-ZÀ-ÿ][A-Za-zÀ-ÿ''\-]+)", part)
            sn = am.group(1) if am and am.group(1).lower() not in JOURNAL_WORDS else None
            if sn and part not in seen:
                seen.add(part)
                out.append(dict(surname=sn, year=ys[0], raw=part))
    return out


def crossref_doi(doi, cache):
    if doi in cache:
        return cache[doi]
    try:
        r = subprocess.run(["curl", "-s", "--max-time", "25", "-H",
                            "User-Agent: provenance-audit (mailto:jcb9926@nyu.edu)",
                            "https://api.crossref.org/works/" + doi],
                           capture_output=True, text=True, timeout=35)
        js = json.loads(r.stdout)
        msg = js.get("message") if isinstance(js, dict) else None
        if not isinstance(msg, dict):
            cache[doi] = None; return None
        rec = dict(
            title=(msg.get("title") or [""])[0],
            journal=(msg.get("container-title") or [""])[0],
            year=str(((msg.get("issued") or {}).get("date-parts") or [[None]])[0][0]),
            authors=[deaccent(a.get("family", "")) for a in (msg.get("author") or [])])
        cache[doi] = rec
        return rec
    except Exception:
        cache[doi] = None
        return None



# ---------------------------------------------------------------------------------------------
# C. THE SECTIONS 3-4 IN-TEXT CITATIONS, RESOLVED BY JOURNAL + VOLUME + FIRST PAGE.
#
# Sections 3-4 carry NO Zotero fields, no superscripts and no citation markers of any kind (0,
# against 51 in S2.2 and 69 in S5) -- their citations are hand-typed author-year parentheticals
# that correspond to no numbered reference. So they cannot be checked against the bibliography;
# they have to be resolved on their own.
#
# A bibliographic string search is useless here (it returns "Love China, Love Hong Kong" for
# "Love/George, OPRD 2021"). What IS precise: search, then accept only a record whose VOLUME and
# FIRST PAGE both equal what the manuscript printed. That turns a fuzzy search into an exact
# lookup, and the author test then means something.
INTEXT = [
    # surname printed, journal, year, volume, first page
    ("Atobe",       "Chem Rev",            "2018", "118", "4541"),
    ("Kappe",       "Org Process Res Dev", "2023", "27",  "2072"),
    ("Noel",        "Acc Chem Res",        "2019", "52",  "2858"),
    ("Bui",         "Chem Rev",            "2022", "122", "11022"),
    ("Stahl",       "J Am Chem Soc",       "2025", "147", "36053"),
    ("Modestino",   "PNAS",                "2019", "116", "17683"),
    ("Suryanto",    "Science",             "2021", "372", "1187"),
    ("Eichner",     "Front Chem Eng",      "2024", "6",   "1384772"),
    ("Yang",        "React Chem Eng",      "2025", "10",  "79"),
    ("Lehnherr",    "Org Process Res Dev", "2024", "28",  "338"),
    ("Bonciolini",  "J Am Chem Soc",       "2025", "147", "28523"),
    ("Heard",       "ACS Cent Sci",        "2024", "10",  "2028"),
    ("Berlinguette","Nat Catal",           "2018", "1",   "501"),
    # resolved 2026-08-23 from the project's own .bib, each verified against Crossref
    ("Bottecchia",  "Org Process Res Dev", "2022", "26",  "2423"),
    ("Love",        "Org Process Res Dev", "2022", "26",  "2674"),
    ("Ferretti",    "Org Process Res Dev", "2025", "29",  "322"),
    ("Manthiram",   "Science",             "2024", "383", "49"),
    ("Krempl",      "Science",             "2021", "374", "1593"),
]



# DOIs resolved by hand for locators whose Crossref SEARCH ranking is unreliable (an article
# number in the page field, or a very common surname). A DOI is a locator, not a guess: pinning
# it makes the check deterministic instead of dependent on how Crossref ranks a query today.
INTEXT_DOI = {
    ("Eichner",   "6",   "1384772"): "10.3389/fceng.2024.1384772",
    ("Suryanto",  "372", "1187"):    "10.1126/science.abg2371",
    ("Atobe",     "118", "4541"):    "10.1021/acs.chemrev.7b00353",
    ("Kappe",     "27",  "2072"):    "10.1021/acs.oprd.3c00255",
    ("Noel",      "52",  "2858"):    "10.1021/acs.accounts.9b00412",
    ("Bui",       "122", "11022"):   "10.1021/acs.chemrev.1c00901",
    ("Stahl",     "147", "36053"):   "10.1021/jacs.5c10599",
    ("Modestino", "116", "17683"):   "10.1073/pnas.1909985116",
    # Resolved 2026-08-23 from the project's own BibTeX export
    # ("Organic E Syn Perspective Zotero/Organic E Syn Perspective.bib", 88 entries), then each
    # verified against Crossref by DOI. Bottecchia's printed locator turned out to be correct all
    # along; Krempl's was not -- he is the 6th author of Science 2021, 374, 1593, and v33 moves
    # the locator there from Joule 2022, 6, 2083 (which is Li, Zhou, Li, Saccoccio & Sazinas).
    ("Bottecchia", "26",  "2423"):   "10.1021/acs.oprd.2c00111",
    ("Love",       "26",  "2674"):   "10.1021/acs.oprd.2c00108",
    ("Ferretti",   "29",  "322"):    "10.1021/acs.oprd.4c00353",
    ("Manthiram",  "383", "49"):     "10.1126/science.adh4355",
    ("Krempl",     "374", "1593"):   "10.1126/science.abl4300",
    # Resolved 2026-08-23 by author + journal + year, then pinned. These had no volume/page in the
    # manuscript, which is why the first pass could not check them at all.
    ("Lehnherr",    "28",  "338"):   "10.1021/acs.oprd.3c00340",
    ("Bonciolini",  "147", "28523"): "10.1021/jacs.5c10303",
    ("Heard",       "10",  "2028"):  "10.1021/acscentsci.4c00988",
    ("Berlinguette","1",   "501"):   "10.1038/s41929-018-0083-8",
    ("Yang",        "10",  "79"):    "10.1039/d4re00346b",
}


def crossref_search(qy, rows=8):
    try:
        r = subprocess.run(["curl", "-s", "--max-time", "25", "-H",
                            "User-Agent: provenance-audit (mailto:jcb9926@nyu.edu)",
                            "https://api.crossref.org/works?rows=%d&query.bibliographic=%s"
                            % (rows, re.sub(r"\s+", "+", qy))],
                           capture_output=True, text=True, timeout=35)
        js = json.loads(r.stdout)
        m = js.get("message") if isinstance(js, dict) else None
        return m.get("items", []) if isinstance(m, dict) else []
    except Exception:
        return []


# A misattribution may be EXEMPTED only while the manuscript carries a Word comment flagging it.
# The exemption is therefore not a suppression: delete the comment without fixing the citation and
# the gate fires again, because the exemption is conditional on the flag still being in the
# document a reader receives. Author decision recorded 2026-08-22: both need a replacement source
# that actually supports the claim, and guessing one would mean inventing a citation.
# keyed on (surname, journal token, first page) so the match does not depend on the comment
# happening to repeat the surname -- comment 82 names the journal and page but not "El Rayess".
# EMPTY as of 2026-08-23. Krempl's locator was corrected to Science 2021, 374, 1593 (he is its
# 6th author), and the four citations that could not be identified -- Garcia-Lopez, Heenan, Ayers
# and El Rayess -- were removed on author decision, the El Rayess CLAUSE with them because it was
# the sole support for its own sentence. Nothing is exempted any more.
FLAGGED_PENDING_SOURCE = {}


def comment_flags(ms_path):
    """Surnames that carry a 'FIND A BETTER PAPER' comment in the shipped .docx."""
    try:
        c = zipfile.ZipFile(ms_path).read("word/comments.xml").decode("utf8")
    except Exception:
        return set()
    import html as _h
    body = _h.unescape(re.sub("<[^>]+>", " ", c))
    if "FIND A BETTER PAPER" not in body:
        return set()
    out = set()
    for sn, (jr, pg) in FLAGGED_PENDING_SOURCE.items():
        if (sn in body) or (jr in body and pg in body):
            out.add(sn)
    return out


def check_intext():
    """Returns (confirmed, misattributed, unresolved, exempted)."""
    flagged = comment_flags(MS)
    good, bad, unk, exempt = [], [], [], []
    for sn, jr, yr, vol, pg in INTEXT:
        hit = None
        doi = INTEXT_DOI.get((sn, vol, pg))
        if doi:
            rec = crossref_doi(doi, {})
            if rec:
                hit = {"volume": vol, "page": pg, "title": [rec["title"]],
                       "author": [{"family": a} for a in rec["authors"]],
                       "container-title": [rec["journal"]]}
        items = [] if hit else crossref_search("%s %s %s %s %s" % (sn, jr, yr, vol, pg))
        for it in items:
            if (str(it.get("volume", "")).strip() == vol
                    and str(it.get("page", "")).split("-")[0].strip() == pg):
                hit = it; break
        raw = "%s, %s %s, %s, %s" % (sn, jr, yr, vol, pg)
        if hit is None:
            unk.append(raw); print("  %-9s %-46s DID NOT RESOLVE at that volume/page" % ("??", raw))
            continue
        au = [deaccent(a.get("family", "")).lower() for a in (hit.get("author") or [])]
        # The manuscript cites some papers by SENIOR author (Berlinguette on Nat. Catal. 2018,
        # Mo on RCE 2025). Membership in the author list is the right test, not first position.
        # A '?' inside a Crossref surname is MOJIBAKE, not a character: the record for
        # 10.1021/acs.accounts.9b00412 stores Timothy Noel's family name as 'Noe?l' with a
        # LITERAL ASCII QUESTION MARK (U+003F), so no normalisation can match it and the gate
        # reported a correct citation as misattributed. No real surname contains '?', so
        # treating it as a single-character wildcard is safe and cannot mask a real mismatch.
        def _mojibake_match(cited, family):
            if "?" not in family:
                return False
            # '?' stands for a COMBINING MARK that deaccent() would have stripped, so it is
            # optional, not one-for-one: Crossref's 'noe?l' (5 chars) must match 'noel' (4).
            return re.fullmatch(re.escape(family).replace(r"\?", ".?"), cited) is not None
        ok = (sn.split()[-1].lower() in au or deaccent(sn).lower() in au
              or any(_mojibake_match(sn.split()[-1].lower(), a_) for a_ in au)
              or any(_mojibake_match(deaccent(sn).lower(), a_) for a_ in au))
        real = ", ".join(deaccent(a.get("family", "")) for a in (hit.get("author") or [])[:5])
        if ok:
            good.append(raw); print("  %-9s %-46s %s" % ("ok", raw, real[:44]))
        elif sn in flagged:
            exempt.append("%s -> actually %s; FLAGGED in the .docx pending a replacement source"
                          % (raw, real))
            print("  %-9s %-46s flagged for replacement (actually %s)"
                  % ("FLAGGED", raw, real[:26]))
        else:
            bad.append("%s -> that volume/page is '%s' by %s; '%s' is not an author"
                       % (raw, (hit.get("title") or [""])[0][:52], real, sn))
            print("  %-9s %-46s IS ACTUALLY %s" % ("MISATTRIB", raw, real[:36]))
    return good, bad, unk, exempt


def main(negative_control=False):
    text = asserted_text(MS)
    paras_raw = text  # noqa
    import zipfile, html
    x = zipfile.ZipFile(MS).read("word/document.xml").decode("utf8")
    RE_DEL = re.compile(r"<w:del (?:[^>]*[^/])?>.*?</w:del>", re.S)
    paras = [html.unescape("".join(re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>",
                                              RE_DEL.sub("", p), re.S)))
             for p in re.findall(r"<w:p[ >].*?</w:p>|<w:p/>", x, re.S)]

    bib = bibliography(text)
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    if negative_control:
        bib.append(dict(n=999, doi="10.3389/fceng.2024.1384772", first="Wallnofer",
                        year="2024", raw="Wallnofer-Ogris et al., Front. Chem. Eng. 2024"))

    print("A. BIBLIOGRAPHY -- %d entries, %d with a DOI\n"
          % (len(bib), sum(1 for b in bib if b["doi"])))
    fails, advisory, nodoi, unresolved = [], [], [], []
    for b in bib:
        if not b["doi"]:
            nodoi.append(b); continue
        rec = crossref_doi(b["doi"], cache)
        if rec is None:
            unresolved.append(b)
            print("  %-4s %-30s DOI DID NOT RESOLVE" % (b["n"], (b["first"] or "?")[:30]))
            continue
        auth = {a.lower() for a in rec["authors"] if a}
        ok = bool(b["first"]) and deaccent(b["first"]).lower() in auth
        if not ok:
            fails.append("ref (%s): the manuscript prints first author '%s', but DOI %s resolves "
                         "to '%s' (%s %s) by %s"
                         % (b["n"], b["first"], b["doi"], rec["title"][:58], rec["journal"][:26],
                            rec["year"], ", ".join(rec["authors"][:5]) or "(no authors listed)"))
        if b["year"] and rec["year"] and b["year"] != rec["year"]:
            advisory.append("ref (%s) %s: manuscript says %s, Crossref says %s"
                            % (b["n"], b["first"], b["year"], rec["year"]))
        print("  %-4s %-30s %-34s %s" % (b["n"], (b["first"] or "?")[:30],
                                         rec["journal"][:34], "ok" if ok else "AUTHOR MISMATCH"))
    json.dump(cache, open(CACHE, "w"), indent=1)

    resolved_authors = {}
    for b in bib:
        rec = cache.get(b["doi"]) if b["doi"] else None
        if rec:
            # EXACT family names, not a joined string. Substring matching makes "Li" match inside
            # "Lin", "Liu" and "Li u"-style lists, so an in-text attribution to Li resolved to four
            # unrelated references. The code audit flagged the same weakness in G-CITE.
            resolved_authors[b["n"]] = {a.lower() for a in rec["authors"] if a}

    inl = inline(paras)
    print("\nB. IN-TEXT ATTRIBUTIONS in Sections 3-4 and S8.2 -- %d\n" % len(inl))
    orphans = []
    for c in inl:
        sn = deaccent(c["surname"]).lower()
        # Surname AND year. Surname alone is a coincidence detector: "Li et al., Science 2021,
        # 372, 1187" matched four references that merely happen to have a Li among their authors
        # and are not that paper. An in-text attribution corresponds to a reference only if both
        # agree.
        byn = {b["n"]: b for b in bib}
        def _yr_ok(n):
            rec = cache.get(byn[n]["doi"]) if byn[n].get("doi") else None
            years = {byn[n].get("year"), rec["year"] if rec else None}
            return c["year"] in {y for y in years if y}
        hit = [n for n, a in resolved_authors.items() if sn in a and _yr_ok(n)]
        raw_hit = [b["n"] for b in bib
                   if b["first"] and deaccent(b["first"]).lower() == sn and b.get("year") == c["year"]]
        where = sorted(set(hit) | set(raw_hit))
        if not where:
            orphans.append(c["raw"])
        print("  %-6s %-52s %s" % ("ok" if where else "ORPHAN", c["raw"][:52],
                                   ("-> ref " + ", ".join(map(str, where[:4]))) if where
                                   else "no bibliography entry has this author"))

    print("\nC. SECTIONS 3-4 IN-TEXT CITATIONS resolved by journal + volume + first page\n")
    ok_c, bad_c, unk_c, exempt_c = check_intext()
    fails.extend(bad_c)
    if exempt_c:
        print("\n  exempted while flagged in the manuscript (%d) -- the exemption lapses if the "
              "comment is removed:" % len(exempt_c))
        for e in exempt_c:
            print("    " + e)

    json.dump(dict(bibliography=bib, failures=fails, advisory=advisory,
                   intext_confirmed=ok_c, intext_misattributed=bad_c, intext_unresolved=unk_c,
                   intext_flagged=exempt_c,
                   no_doi=[b["n"] for b in nodoi], unresolved=[b["n"] for b in unresolved],
                   inline=inl, orphans=orphans),
              open(_out(OUT, negative_control), "w"), indent=2, default=str)
    print("\nwrote %s" % os.path.relpath(OUT, ROOT))

    print("\nG-MSCITE: %s" % ("PASS" if not fails else "FAIL"))
    for f in fails:
        print("  " + f)
    if advisory:
        print("\n  advisory (year differs from Crossref's issued date -- often the online year):")
        for a in advisory:
            print("    " + a)
    if nodoi:
        print("\n  no DOI, not machine-checkable (%d): refs %s"
              % (len(nodoi), ", ".join(str(b["n"]) for b in nodoi)))
    if unresolved:
        print("  DOI did not resolve (%d): refs %s"
              % (len(unresolved), ", ".join(str(b["n"]) for b in unresolved)))
    if orphans:
        print("\n  in-text attributions with no matching bibliography entry (%d):" % len(orphans))
        for o in orphans:
            print("    " + o)

    if negative_control:
        fired = any("999" in f for f in fails)
        print("\nnegative control: injected the known chimera 'Wallnofer-Ogris' on the REAL DOI "
              "10.3389/fceng.2024.1384772 (actually Eichner, Amiri, Burheim & Lamb)")
        print("  gate fired on it: %s" % fired)
        if not fired:
            raise AssertionError("negative control did not fire; this gate cannot detect a real "
                                 "locator wearing a fabricated first author")
        return
    if fails:
        raise AssertionError("%d bibliography entries are misattributed" % len(fails))


if __name__ == "__main__":
    main(negative_control="--negative-control" in sys.argv)
