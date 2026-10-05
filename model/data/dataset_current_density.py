#!/usr/bin/env python3
"""What the 25,941-reaction dataset can and cannot say about operating current density.

Jonas Rein asked the manuscript to put a number on "at low current density" and left a literal
placeholder, " (<XX mA cm-2)", in his redline.  This measures what the dataset can support.

It carries NO current-density column (rxn_id, n_react, n_prod, min_year, n_refs, all_years, yield,
reagents, solvents, catalysts, notes, n_react_parsed, n_prod_parsed, react_smiles, prod_smiles,
parse_ok) -- the same absence SI S4.1 already records for concentration.  What it has is a
free-text `notes` field, and three things are true of it:

  (i)  A current density appears in 657 records, in six unit forms (mA/cm2, mA cm-2, A/cm2, A/dm2
       and, with zero occurrences, mA/dm2 and uA/cm2).  A first version of this script required
       the "m" in mA and so MISSED A/cm2 and A/dm2 entirely, reporting 482; that is corrected.
  (ii) Those 657 records are NOT 657 observations.  They carry only 182 distinct note strings and
       38 distinct values, because CAS repeats one paper's conditions across every reaction it
       indexes from that paper -- one string recurs 30 times.  Any mean or median over the records
       is therefore weighted by how many reactions a paper happened to report, which is why this
       script reports the share below a threshold BOTH per record and per distinct value, and
       reports no median at all.
  (iii) The reason a density is so rarely recoverable is that papers report a CURRENT: 9,653
       records (37 % of the set) state one in mA, and NOT ONE of them also states an electrode
       area, so none can be converted.

Writes results/dataset_current_density.json.  `--check-si` is the gate (G-DSETJ-SI): it re-derives
every number here and requires the built SI's own sentence to print it, with its caveats.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PARQUET = os.path.join(os.path.dirname(ROOT), "Figure_1b_Kasie", "filtered_echem.parquet")
OUT = os.path.join(ROOT, "results", "dataset_current_density.json")

_N = r"(\d+(?:\.\d+)?)"
_A = r"(?:\s*[/ ]\s*|\s+per\s+)?"
# (label, pattern, factor to mA cm-2).  The negative lookbehind keeps "A" from matching the A of mA.
FORMS = [
    ("mA/cm2",  _N + r"\s*m\s?A" + _A + r"cm\s*(?:2|²|\^2)",                       1.0),
    ("mA cm-2", _N + r"\s*m\s?A\s*[ /]?\s*cm\s*(?:-|−|⁻)\s*(?:2|²)",      1.0),
    ("A/cm2",   _N + r"\s*(?<![mMµu])A" + _A + r"cm\s*(?:2|²|\^2)",         1000.0),
    ("A/dm2",   _N + r"\s*(?<![mMµu])A" + _A + r"dm\s*(?:2|²|\^2)",           10.0),
    ("mA/dm2",  _N + r"\s*m\s?A" + _A + r"dm\s*(?:2|²|\^2)",                        0.01),
    ("uA/cm2",  _N + r"\s*(?:u|µ)A" + _A + r"cm\s*(?:2|²|\^2)",                0.001),
]
RX = [(lab, re.compile(p, re.I), f) for lab, p, f in FORMS]
# a current with no area: "10 mA" but not "10 mA/cm2"
RX_CUR = re.compile(_N + r"\s*m\s?A\b(?!\s*[/ ]?\s*(?:c|d)m)", re.I)
RX_AREA = re.compile(r"\d\s*(?:c|d)m\s*(?:2|²|\^2)", re.I)

EXPECTED_COLS = {"rxn_id", "n_react", "n_prod", "min_year", "n_refs", "all_years", "yield",
                 "reagents", "solvents", "catalysts", "notes", "n_react_parsed", "n_prod_parsed",
                 "react_smiles", "prod_smiles", "parse_ok"}
THRESH = 25.0          # the threshold the manuscript and the survey both use


def measure():
    import numpy as np
    import pandas as pd
    d = pd.read_parquet(PARQUET)
    cols = set(d.columns)
    assert cols == EXPECTED_COLS, "parquet columns moved: %r" % (cols ^ EXPECTED_COLS)
    assert not (cols & {"current_density", "j", "mA_cm2", "current"}), \
        "the parquet now carries a current-density column; this script's premise is stale"
    notes = d["notes"].fillna("").astype(str)

    per_form, rec = {}, {}
    for lab, rx, f in RX:
        hits = 0
        for i, s in notes.items():
            v = [float(m.group(1)) * f for m in rx.finditer(s)]
            if v:
                hits += 1
                rec.setdefault(i, []).extend(v)
        per_form[lab] = hits
    vals = np.array([x for v in rec.values() for x in v], dtype=float)
    uniq = np.array(sorted({round(x, 4) for x in vals}), dtype=float)
    strings = notes[list(rec)]

    cur = notes.apply(lambda s: bool(RX_CUR.search(s)))
    cur_and_area = int((cur & notes.apply(lambda s: bool(RX_AREA.search(s)))).sum())
    dens = notes.index.isin(list(rec))
    n_both = int((cur & dens).sum())
    n_cur_only = int((cur & ~dens).sum())

    return dict(
        n_records=int(len(d)),
        n_with_notes=int((notes.str.strip() != "").sum()),
        n_stating_j=len(rec),
        share_stating_j_pct=round(100.0 * len(rec) / len(d), 1),
        per_form=per_form,
        n_distinct_notes=int(strings.nunique()),
        n_distinct_values=int(len(uniq)),
        max_note_repeats=int(strings.value_counts().iloc[0]),
        min_mAcm2=round(float(vals.min()), 2),
        max_mAcm2=round(float(vals.max()), 1),
        share_below_25_by_record_pct=int(round(100.0 * float((vals < THRESH).mean()))),
        share_below_25_by_value_pct=int(round(100.0 * float((uniq < THRESH).mean()))),
        n_stating_current_mA=int(cur.sum()),
        n_current_only=n_cur_only,
        n_both=n_both,
        share_current_only_pct=int(round(100.0 * n_cur_only / len(d))),
        share_stating_current_pct=int(round(100.0 * float(cur.mean()))),
        n_current_with_area=cur_and_area,
        threshold_mAcm2=THRESH,
        verdict="PASS",
    )


def main():
    r = measure()
    # the findings this exists to support, asserted rather than described
    assert r["share_stating_j_pct"] < 10.0, "the subsample is no longer a small minority (%.1f %%)" % r["share_stating_j_pct"]
    assert r["n_distinct_values"] < r["n_stating_j"] / 2, \
        "the records are no longer heavily duplicated (%d values over %d records); the caveat needs rewriting" \
        % (r["n_distinct_values"], r["n_stating_j"])
    assert r["n_current_with_area"] == 0, \
        "%d records now state both a current and an area, so some densities ARE recoverable" % r["n_current_with_area"]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(r, f, indent=2, sort_keys=True); f.write("\n")
    print("G-DSETJ: %d of %d records (%.1f %%) state a current density, in %d distinct note strings "
          "and %d distinct values (one string recurs %dx); %d %% of records and %d %% of distinct "
          "values are below %g mA cm-2; range %.2f-%.1f"
          % (r["n_stating_j"], r["n_records"], r["share_stating_j_pct"], r["n_distinct_notes"],
             r["n_distinct_values"], r["max_note_repeats"], r["share_below_25_by_record_pct"],
             r["share_below_25_by_value_pct"], r["threshold_mAcm2"], r["min_mAcm2"], r["max_mAcm2"]))
    print("G-DSETJ: %d records (%d %%) state a current in mA instead, %d of them with an electrode area"
          % (r["n_stating_current_mA"], r["share_stating_current_pct"], r["n_current_with_area"]))
    print("G-DSETJ: per unit form %s" % r["per_form"])
    print("G-DSETJ: PASS (wrote %s)" % os.path.relpath(OUT, ROOT))
    return 0


# ---------------------------------------------------------------- the gate
SI = os.path.join(ROOT, "SI_Section4_Transport_Model.docx")
LEAD = "Operating current density."


def check_si(negative=False):
    """Re-derive from the parquet and require the built SI's own sentence to match.

    This binds the DOCUMENT to the dataset, not the document to a JSON: a stale artifact and a
    stale sentence agreeing with each other is the failure a JSON comparison cannot see.
    """
    sys.path.insert(0, HERE)
    from docx_text import asserted_text
    r = measure()
    if negative:                                   # perturb the MODEL side, never the document
        r["n_stating_j"] += 200
        r["share_below_25_by_record_pct"] += 7

    txt = asserted_text(SI)
    i = txt.find(LEAD)
    if i < 0:
        print("G-DSETJ-SI: FAIL -- the SI carries no '%s' paragraph" % LEAD)
        return 1
    # read to the END of the paragraph, not a fixed window: a fixed one truncated the closing
    # clause the moment the paragraph grew past it, and reported the document as the defect.
    _end = txt.find("S4.2", i)
    sent = txt[i:_end if _end > i else i + 1500]
    fails = []

    def want(v, name):
        s = "%d" % v if isinstance(v, int) else "%g" % v
        probes = [s] + (["%s,%s" % (s[:-3], s[-3:])] if isinstance(v, int) and v >= 1000 else [])
        if not any(p in sent for p in probes):
            fails.append("%s: the SI does not print %s" % (name, s))

    for v, name in ((r["n_stating_j"], "records stating a density"),
                    (r["n_current_only"], "records stating only a current"),
                    (r["n_records"], "the set size"),
                    (r["n_distinct_notes"], "distinct note strings"),
                    (r["n_distinct_values"], "distinct values"),
                    (r["share_below_25_by_record_pct"], "share below 25 by record"),
                    (r["share_below_25_by_value_pct"], "share below 25 by value"),
                    (r["share_current_only_pct"], "share stating only a current")):
        want(v, name)
    if ("%.1f" % r["share_stating_j_pct"]) not in sent:
        fails.append("the SI does not print the %.1f %% share" % r["share_stating_j_pct"])

    # a number without its caveat is the overclaim this paragraph exists to avoid
    for claim, why in (("distinct", "the duplication caveat"),
                       ("with no electrode area", "the reason a density is not recoverable"),
                       ("too small", "the caveat that the subset cannot characterise the set"),
                       ("reports a threshold rather than an average",
                        "the statement that the main text reports a threshold, not an average"),
                       ("the number of records it is drawn from",
                        "the statement that the main text names the records behind the share")):
        if claim not in sent:
            fails.append("missing %s (%r)" % (why, claim))
    # and no median may be quoted: it would be weighted by how many reactions a paper reported
    if re.search(r"median[^.]{0,40}mA", sent):
        fails.append("the paragraph quotes a median over duplicated records")

    # the MANUSCRIPT sentence Jonas asked for, bound to the same re-derivation
    import glob
    # the highest-numbered JR build; "JRbase" has no digits, so filter BEFORE sorting
    ms = [f for f in glob.glob(os.path.join(os.path.dirname(ROOT), "MS Drafts",
                                            "RCE_Perspective_JR*.docx"))
          if re.search(r"JR(\d+)_", os.path.basename(f))]
    ms.sort(key=lambda f: int(re.search(r"JR(\d+)_", os.path.basename(f)).group(1)))
    if ms:
        mt = asserted_text(ms[-1])
        want_ms = ("at low current density (below {t:g} mA cm\u207b\u00b2 in {p} % of the {n} "
                    "records that report one)").format(t=r["threshold_mAcm2"],
                                                       p=r["share_below_25_by_record_pct"],
                                                       n=r["n_stating_j"])
        # asserted_text NFKC-normalises, so "cm\u207b\u00b2" reads back as "cm-2"; normalise the
        # expectation the same way, and compare on the digits rather than the space characters
        import unicodedata
        norm = lambda t: re.sub(r"[\s\u00a0]+", " ", unicodedata.normalize("NFKC", t))
        if norm(want_ms) not in norm(mt):
            fails.append("the manuscript's parenthetical does not read %r (checked %s)"
                         % (want_ms, os.path.basename(ms[-1])))
        else:
            print("   manuscript %s carries the parenthetical, bound to this re-derivation"
                  % os.path.basename(ms[-1]))
    else:
        fails.append("no JR-numbered manuscript found to check")

    for f in fails:
        print("   %s" % f)
    if negative:
        print("G-DSETJ-SI control: %s" % ("GOOD" if fails else "BAD -- test is inert"))
        return 0 if fails else 1
    print("G-DSETJ-SI: %s (%d of %d records, %d distinct values; %d %% of records below 25 mA cm-2; "
          "%d records state a current instead, %d with an area)"
          % ("PASS" if not fails else "FAIL", r["n_stating_j"], r["n_records"],
             r["n_distinct_values"], r["share_below_25_by_record_pct"],
             r["n_stating_current_mA"], r["n_current_with_area"]))
    return 1 if fails else 0


if __name__ == "__main__":
    if "--check-si" in sys.argv:
        sys.exit(check_si("--negative-control" in sys.argv))
    sys.exit(main())
