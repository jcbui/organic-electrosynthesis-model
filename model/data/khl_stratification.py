"""Re-derive the 50-reaction set's class stratification under the KHL taxonomy.

    cd Section4_Model/data && python khl_stratification.py

WHY THIS EXISTS
---------------
SI S1.2 argues the 50-reaction set is stratified to match the corpus class distribution.
That argument was written against the retired structure-difference classification. The KHL
revision redraws the class boundaries -- cyclization becomes a class of its own and
outranks the bond-forming classes -- so the comparison has to be re-derived on both sides,
not merely renumbered.

The corpus side is read straight from Figure_1b_Kasie/polarity_redox.parquet.

The set side CANNOT be read the same way: reactions_50.csv carries no CAS reaction id and
no SMILES, only a reaction name and its page-verified conditions, so the KHL classifier
cannot be run on it. The 50 exemplars are instead assigned by APPLYING KHL's published
decision rules to the named transformation, one row at a time, in
reactions_50_khl_class.csv -- which records for every row the rule that was applied, a
confidence, and the code path in classify.py that decides it.

Every row is resolved against that CODE, not against the README's prose summary -- the
rows that once looked ambiguous were settled by reading it: kept_fragments() drops only
FULLY untracked fragments (so a methanol or water whose O is tracked into the product
stays a reactant), and nonHO_diff counts a lost halogen (so dehalogenation misses the
Oxidation/Reduction branch and falls through to FGI). No row now carries an alternative.

That makes the set side a state-B derivation from a named rule set, not a classifier
output, and it is labelled as such in the SI.

Isomerization is excluded from the comparison basis on both sides: KHL does not plot it in
Fig. 1b, so the corpus has no Isomerization bar and row 41 has no counterpart.
"""
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KHL = os.path.join(os.path.dirname(ROOT), "Figure_1b_Kasie", "polarity_redox.parquet")
RXN50 = os.path.join(HERE, "reactions_50.csv")

EXCLUDED = {"Isomerization", "Unclassified"}
# Isomerization: KHL does not plot it in Fig. 1b, so the corpus has no bar for it.
# (unclassified): classify_1_1 returns label None for that row, exactly as the pipeline
# leaves 925 corpus reactions unlabelled. Both are outside the comparison basis.


def corpus_shares():
    try:
        pol = pd.read_parquet(KHL, columns=["label"])
    except Exception:
        pol = pd.read_parquet(KHL, columns=["label"], engine="fastparquet")
    vc = pol.label.value_counts()
    return 100.0 * vc / len(pol), len(pol)


def set_shares(col=None):
    """Set-side shares, read from reactions_50.csv's own `cls` column.

    Since 2026-08-22 the 50-reaction set carries its KHL class directly (written by
    build_reactions50.py), so there is ONE source of truth rather than a parallel mapping
    file that could drift from it. reactions_50_khl_class.csv survives only as the audit
    trail recording which classify.py code path decided each row.
    """
    cls = pd.read_csv(RXN50)["cls"]
    cls = cls[~cls.isin(EXCLUDED)]
    return 100.0 * cls.value_counts() / len(cls), len(cls)


def table(corpus, cset, n_corpus, n_set):
    idx = sorted(set(corpus.index) | set(cset.index),
                 key=lambda k: -corpus.get(k, 0.0))
    rows = []
    for k in idx:
        c = corpus.get(k, 0.0)
        s = cset.get(k, 0.0)
        rows.append((k, s, c, s - c))
    return pd.DataFrame(rows, columns=["class", "set_pct", "corpus_pct", "diff"])


def main():
    corpus, n_corpus = corpus_shares()
    corpus = corpus[~corpus.index.isin(EXCLUDED)]

    prim, n_set = set_shares()


    print("corpus basis n = %d (Fig. 1b, KHL); set basis n = %d of 50 -- row 41 "
          "(Isomerization, not plotted in Fig. 1b) and row 33 (unclassified, as the "
          "pipeline leaves it) are outside the basis\n" % (n_corpus, n_set))

    t = table(corpus, prim, n_corpus, n_set)
    # Write the per-class shares so the SI can interpolate them instead of carrying eleven typed
    # pairs. They had gone stale once already: correcting row 11's class (C-N formation -> Reduction,
    # 2026-10-05) moved two of them, and G-STRAT did not fire because it gates the five CLAIMS the
    # paragraph makes, not the share list itself -- a gate covering part of a claim passing for the
    # whole of it.
    import json as _json
    _out = {"n_corpus": int(n_corpus), "n_set": int(n_set),
            "shares": [{"cls": r["class"], "set_pct": round(float(r.set_pct), 1),
                        "corpus_pct": round(float(r.corpus_pct), 1),
                        "diff": round(float(r["diff"]), 1)} for _, r in t.iterrows()]}
    # The classification record's oxygen-donor convention (a reagent that adds only oxygen -- water or a peroxide -- is not a
    # reactant, methanol is) follows how the dataset draws its records; the SI states it with these counts.
    _fe = os.path.join(os.path.dirname(ROOT), "Figure_1b_Kasie", "filtered_echem.parquet")
    _frag = pd.read_parquet(_fe, columns=["react_smiles"]).react_smiles.fillna("").map(lambda s: set(s.split(".")))
    _out["drawn_as_reactant"] = {"n_records": int(len(_frag)),
                                 "water": int(_frag.map(lambda f: bool(f & {"O", "[OH2]"})).sum()),
                                 "hydrogen_peroxide": int(_frag.map(lambda f: "OO" in f).sum()),
                                 "methanol": int(_frag.map(lambda f: bool(f & {"CO", "OC"})).sum())}
    _p = os.path.join(ROOT, "results", "khl_stratification.json")
    with open(_p, "w") as _f:
        _json.dump(_out, _f, indent=1)
    print("wrote results/khl_stratification.json (%d classes)" % len(_out["shares"]))

    print("=== primary assignment ===")
    print(t.to_string(index=False, float_format=lambda v: "%6.1f" % v))
    worst = t["diff"].abs().max()
    row = t.loc[t["diff"].abs().idxmax()]
    print("\nlargest gap: %s, set %.1f%% vs corpus %.1f%% (%+.1f points)"
          % (row["class"], row.set_pct, row.corpus_pct, row["diff"]))
    print("every populated class matches within %.1f points -> quote %d points"
          % (worst, -(-worst // 1)))

    unrep = t[(t.set_pct == 0) & (t.corpus_pct > 0)]
    for _, r in unrep.iterrows():
        print("NO EXEMPLAR: %s (%.1f%% of corpus)" % (r["class"], r.corpus_pct))

    return t


def check_si(perturb=False):
    """Assert every set-vs-corpus pair the SI prose quotes matches this computation.

    Falsifiable by construction: the pairs are rebuilt from the parquet and the mapping
    CSV, then required to appear verbatim in the built SI. --negative-control perturbs the
    computed table and confirms the gate fires.
    """
    import re
    # The BUILT SI, not make_si.js: since chemistry audit pass 4 the bound word is computed in the generator, so the
    # phrase exists only in the document (a check that greps a generator stops passing the moment its text is computed).
    import sys
    sys.path.insert(0, HERE)
    import docx_text
    src = docx_text.asserted_text(os.path.join(ROOT, "SI_Section4_Transport_Model.docx"))
    corpus, n_corpus = corpus_shares()
    corpus = corpus[~corpus.index.isin(EXCLUDED)]
    prim, n_basis = set_shares()
    t = table(corpus, prim, 0, 0)
    if perturb:
        # Perturb the CORPUS side. The earlier control nudged set_pct by 0.4, which moved
        # no claim at all -- the bound word did not change, and multicomponent's share went
        # 0.0 -> 0.4 so the no-exemplar claim simply stopped being emitted instead of
        # failing. A gate that quietly drops a check is not a gate. Shifting the corpus
        # side by 3 points moves both the bound and the quoted no-exemplar share.
        t["corpus_pct"] = t["corpus_pct"] + 3.0
        t["diff"] = t["set_pct"] - t["corpus_pct"]

    # The SI no longer prints a per-class table; it makes three quantified claims.
    # Rebuild each from the parquet + mapping CSV and require it verbatim.
    worst = t["diff"].abs().max()
    import math
    bound_word = {5:"five",6:"six",7:"seven",8:"eight",9:"nine",10:"ten"}[int(math.ceil(worst))]
    unrep = t[(t.set_pct == 0) & (t.corpus_pct > 0)]

    claims = [
        ("bound", "matches within %s percentage points" % bound_word),
        ("basis", "across the %d entries the classifier places" % n_basis),
        # the SI names this set the "dataset" since the 2026-09-14 voice pass; the claim it
        # gates is the scored subset the classifier actually places, not the wording.
        ("scored-n", "%s carry the polarity scores Fig. 1b plots" % format(int(n_corpus), ",")),
        ("representative", "is approximately representative of the dataset"),
    ]
    # Multicomponent coupling had NO exemplar until 2026-08-22; two page-verified
    # three-component entries were added and the alkoxysulfonylation row reclassified, so
    # the claim to gate is now the match itself, not the absence.
    mcc = t[t["class"] == "Multicomponent coupling"]
    if len(mcc):
        r = mcc.iloc[0]
        claims.append(("mcc-match", "%.1f%% of the set against %.1f%% of the dataset"
                       % (r.set_pct, r.corpus_pct)))
    for _, r in unrep.iterrows():
        claims.append(("no-exemplar", "%s has no exemplar" % r["class"]))

    fails = []
    for label, want in claims:
        ok = want in src
        print("  %-5s %-14s %s" % ("PASS" if ok else "FAIL", label, want))
        if not ok:
            fails.append(want)

    print("\n%d FAIL" % len(fails))
    if perturb:
        # DERIVED from the claims actually emitted, never typed. This set was pinned as
        # {"bound", "no-exemplar"} and went stale the moment multicomponent coupling gained
        # exemplars: `unrep` became empty, so no "no-exemplar" claim is emitted at all, and
        # the share-dependent claim for that class became "mcc-match". The control then
        # reported BAD for a gate that was working correctly -- a pinned expectation that
        # can drift out from under the thing it pins is the same failure class as a typed
        # number that goes stale.
        SHARE_DEPENDENT = ("bound", "mcc-match", "no-exemplar")
        expected = {lab for lab, _ in claims if lab in SHARE_DEPENDENT}
        fired = {lab for lab, want in claims if want in fails}
        print("negative control: perturbing the corpus side should fire exactly %s"
              % sorted(expected))
        if fired == expected:
            print("  OK -- every share-dependent claim fired; the three that do not "
                  "depend on shares correctly held")
            return 0
        print("  BAD -- missed %s ; spurious %s"
              % (sorted(expected - fired), sorted(fired - expected)))
        return 1
    return 1 if fails else 0


if __name__ == "__main__":
    import sys
    if "--check-si" in sys.argv:
        sys.exit(check_si(perturb="--negative-control" in sys.argv))
    main()
