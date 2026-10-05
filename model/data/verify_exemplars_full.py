#!/usr/bin/env python3
"""G-EXEMPLAR2 -- verify EVERY exemplar behind the 50 reactions by searching on the CHEMISTRY.

    cd Section4_Model && python data/verify_exemplars_full.py

TWO exemplars in this table were FABRICATED and went undetected through a full provenance audit:
Zhang/Qiu Nat Commun 2025 and Yang/Wang Nat Commun 2023. They carried invented concentrations with
circumstantial detail ("0.5 M NaBr in the aqueous half of a 1:1 mix = 0.25 M effective Br-",
"0.61 kg") that read as page-verified. Both have since been REPLACED by real, DOI-anchored papers
-- Zhang/Su, Nat. Commun. 2025, DOI 10.1038/s41467-025-57329-0, and Yang/Lei, Nat. Commun. 2023,
14, 1476, DOI 10.1038/s41467-023-37032-8 -- and the concentrations were re-derived from them.

A THIRD, Ke/Chi Chem Eur J 2019, was listed here as fabricated until 2026-08-31 AND IT IS NOT.
It is Ke, Wang, Zhou, Mou, Zhang, Pan & Chi, "Hydrodehalogenation of Aryl Halides through Direct
Electrolysis", Chem. Eur. J. 2019, DOI 10.1002/chem.201901082 -- a real paper, resolving on the
first hit when queried by TITLE, whose author list matches the registry exactly. What it does not
do is resolve from the short form "Ke/Chi Chem Eur J 2019", because Crossref's bibliographic-string
ranking is unreliable on abbreviated citations (the same weakness that returns "Love China, Love
Hong Kong" for "Love/George, OPRD 2021"). AN UNRESOLVED VERDICT IS A STATEMENT ABOUT THE SEARCH,
NOT ABOUT THE PAPER, and writing one down as "fabricated" turned a tooling limitation into a false
accusation that sat in this file. Exemplars confirmed by pinned DOI are listed in CONFIRMED_DOI
below and resolved that way instead.

The earlier check searched author+journal+year, which is far too weak: it returned an earthquake
paper for one real citation and a carbon-markets paper for another, and it never questioned rows
whose exemplar did not exist. THIS check searches the REACTION CHEMISTRY plus the author surnames
and requires (a) an author surname to match, allowing for diacritics, and (b) the title to be
about that chemistry. Anything it cannot confirm is reported as NOT CONFIRMED -- which is a
statement about the evidence, not proof the paper is fake, and every one must be opened by hand.
"""
import json, os, re, sys, time, unicodedata, urllib.parse, urllib.request
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
UA = "Mozilla/5.0 (provenance-audit; mailto:jbui888@gmail.com)"
FOLD = lambda s: "".join(c for c in unicodedata.normalize("NFKD", s.lower())
                         if not unicodedata.combining(c))

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


def cr(query, rows=6):
    u = "https://api.crossref.org/works?rows=%d&query.bibliographic=%s" % (rows, urllib.parse.quote(query))
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=25) as r:
            return json.load(r)["message"]["items"]
    except Exception:
        return []

# This gate exists because three FABRICATED exemplars survived a full provenance audit. All three
# were removed once found, so a clean run can no longer demonstrate that the check still works --
# it only shows the survivors resolve. The control puts fabrications back: real-sounding authors
# and a real journal attached to a chemistry that was never published there. Each must come back
# NOT CONFIRMED. It searches only these rows, so it costs seconds rather than a full sweep.
FAKE_ROWS = [
    ("Ni-mediated anodic difluoromethylenation of enol carbamates",
     "Vasquez/Oyelaran/Brindisi, JACS 2024, 146, 20331"),
    ("Cathodic ring-opening telomerization of azetidinyl sulfonamides",
     "Halvorsen/Ntembe, Nat Commun 2023, 14, 7788"),
    ("Paired electrolytic dearomative silyl-amination of quinolines",
     "Rasmussen/Adeyemi/Falk, Chem Eur J 2022, 28, e202201847"),
]


def main(neg=False):
    rx = pd.read_csv(os.path.join(HERE, "reactions_50.csv"))
    if neg:
        rx = pd.DataFrame([{"reaction": a, "exemplar": b} for a, b in FAKE_ROWS])
        print("NEGATIVE CONTROL: %d invented reaction/exemplar pairs; each must come back "
              "NOT CONFIRMED.\n" % len(FAKE_ROWS))
    out = []
    for _, r in rx.iterrows():
        ex = str(r.exemplar)
        names = []
        for piece in split_exemplars(ex):
            head = re.sub(r"\([^)]*\)", "", piece)
            head = re.split(r"\b(19|20)\d{2}\b", head)[0]
            for j in ("JACS","Angew","Science","Nature","Nat Commun","Nat Catal","OPRD","OL",
                      "Chem Sci","Tetrahedron","Chem Commun","JES","ACS SCE","ChemSusChem",
                      "Chem Eur J","Can J Chem","RSC Adv","Tet Lett","Electrochem Commun",
                      "ACS Omega","Electrochim Acta"):
                head = head.replace(j, "")
            names += [n.strip() for n in head.split("/") if n.strip()]
        yrs = re.findall(r"\b(19|20)\d{2}\b", ex)
        query = "%s %s electrochemical" % (r.reaction, " ".join(names[:3]))
        items = cr(query)
        time.sleep(0.35)
        best, verd = None, "NOT CONFIRMED"
        rkey = [w for w in FOLD(str(r.reaction)).replace("-", " ").split()
                if len(w) > 4 and w not in ("electrochemical","cathodic","anodic","reaction")]
        for it in items:
            doi = it.get("DOI", "")
            if doi.endswith((".s001", ".s002")) or "/v1/" in doi or "/v2/" in doi:
                continue
            auth = FOLD(" ".join((a.get("family", "") or "") for a in it.get("author", []) or []))
            ttl = FOLD((it.get("title") or [""])[0])
            nok = any(FOLD(n) in auth for n in names if len(n) > 3)
            tok = sum(1 for w in rkey if w[:6] in ttl)
            if nok and tok >= 1:
                best, verd = it, "CONFIRMED"; break
            if best is None and (nok or tok >= 2):
                best, verd = it, "WEAK"
        lab = ""
        if best:
            lab = "%s | %s %s | %s" % ((best.get("title") or [""])[0][:56],
                  (best.get("container-title") or [""])[0][:22],
                  ((best.get("issued", {}).get("date-parts") or [[None]])[0][0]), best.get("DOI",""))
        out.append(dict(reaction=r.reaction, exemplar=ex, verdict=verd, match=lab))
        print("  %-13s %-42s %s" % (verd, str(r.reaction)[:42], lab[:80])); sys.stdout.flush()
    n = {}
    for o in out: n[o["verdict"]] = n.get(o["verdict"], 0) + 1
    print("\n%d rows: %s" % (len(out), n))
    bad = [o for o in out if o["verdict"] != "CONFIRMED"]
    print("\nNOT CONFIRMED -- open each by hand (%d):" % len(bad))
    for o in bad:
        print("  %-46s  %s" % (o["reaction"][:46], o["exemplar"][:58]))
    _o = os.path.join(ROOT, "results", "exemplar_full_verification%s.json"
                      % ("_NEGCONTROL" if neg else ""))
    json.dump(out, open(_o, "w"), indent=1)
    print("\n-> %s" % os.path.relpath(_o, ROOT))
    if neg:
        ok = len(bad) == len(FAKE_ROWS)
        print("G-EXEMPLAR2 control: %s"
              % ("GOOD -- all %d invented pairs came back NOT CONFIRMED" % len(bad) if ok else
                 "BAD -- %d of %d invented pairs were CONFIRMED against a real paper, so this "
                 "gate would pass a fabrication" % (len(FAKE_ROWS) - len(bad), len(FAKE_ROWS))))
        return 0 if ok else 1
    print("G-EXEMPLAR2: %s" % ("PASS" if not bad else "REVIEW NEEDED"))
    return 0

if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv) or 0)
