#!/usr/bin/env python3
"""G-ECBAND -- the EC' sensitivity bracket the SI prints, recomputed from the model.

    cd Section4_Model && python data/check_ecprime_band.py
    cd Section4_Model && python data/check_ecprime_band.py --negative-control

WHY THIS EXISTS
---------------
SI section S5.5 prints a bracket on the six >=25 mA cm-2 counts, and that bracket was a TYPED
LITERAL with nothing checking it. It had already drifted: when the MeCN viscosity moved to the
value CRC prints (0.343 -> 0.369 mPa s), delta_eff and the substrate-supply cap both moved with
it, and the RDE and RCE ends of the bracket went from 35 to 33 while the prose still said 35-36.
CLAUDE.md's own rule -- "never type a pinned expectation you could derive" -- covers exactly this.

WHAT THE BRACKET ACTUALLY IS, stated more carefully than the prose used to
-------------------------------------------------------------------------
The SI described the two directions as "raising every mediated cell to its physical cap
min(Savéant, substrate supply) and lowering every one to its Tier-0 floor". The second is right.
The first is NOT a raise: 20 of the 48 solves already sit ABOVE min(Savéant, substrate supply),
because the substrate cap n_S F D_S C_S / delta assumes the reaction front sits AT the electrode,
and when the substrate is exhausted the front detaches (docs/ECPRIME_WALL_FINDING.md). So that
direction moves some cells down and some up. It is still a legitimate perturbation -- it replaces
every solved value with the closed-form envelope -- but it is not an upper bound, and calling it
one was wrong. This script computes both directions and reports the union, without claiming
either endpoint bounds the truth.

HOW EACH VALUE WAS REACHED is reported too. Br-mediated Hofmann in an unstirred beaker
(delta = 300 um, delta/x_k = 128) used to stall at 0.74 mA cm-2 -- BELOW its own commuting bound,
so not a physical answer -- and was floored to Tier-0 (6.95), which sits under the 25 mA cm-2
threshold and was therefore setting a headline integer. It is now resolved by delta-continuation
at ~100-112 mA cm-2, and the unstirred counts are 12/50 and 9/50. That cell is the only one of 48
not reached by a direct current ramp, so this script prints which cells took the continuation path
and asserts the solver still records it. If a future change floors a cell again, the line
"cells still floored to Tier-0" reappears rather than the fact being buried in a CSV column.
"""
import os
import re
import sys
import unicodedata

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ARCH = ["natural", "stirred", "flow", "anec", "micro", "rde", "rce"]


def load():
    t = pd.read_csv(os.path.join(ROOT, "julia", "tier0_ec_matrix.csv")).set_index("reaction")
    m = pd.read_csv(os.path.join(ROOT, "julia", "mediated_ec_matrix.csv"))
    return t, m


def variants(t, m):
    """Shipped, all-mediated-at-Tier-0-floor, all-mediated-at-closed-form-envelope."""
    lo, hi = t.copy(), t.copy()
    for rx, g in m.groupby("reaction"):
        g = g.sort_values("delta_um", ascending=False).reset_index(drop=True)
        if len(g) != len(ARCH):
            sys.exit("%s has %d solves, expected %d" % (rx, len(g), len(ARCH)))
        for k, col in enumerate(ARCH):
            r = g.loc[k]
            lo.loc[rx, col] = r.i_tier0_mAcm2
            hi.loc[rx, col] = min(r.i_saveant_mAcm2, r.i_subcap_mAcm2)
    return {"shipped": t, "tier0 floor": lo, "closed-form envelope": hi}


def counts(d, thr):
    return [int((d[c] >= thr).sum()) for c in ARCH]


def main(negative_control=False):
    t, m = load()
    if negative_control:
        # Perturb the MODEL, not the prose: push every RDE solve up so the bracket's RDE end
        # must move. A control that edited the sentence would only prove the regex works.
        t = t.copy(); t["rde"] = t["rde"] * 3.0
    V = variants(t, m)

    band25, band50 = {}, {}
    for c in ARCH:
        v25 = [counts(d, 25)[ARCH.index(c)] for d in V.values()]
        v50 = [counts(d, 50)[ARCH.index(c)] for d in V.values()]
        band25[c] = (min(v25), max(v25))
        band50[c] = (min(v50), max(v50))

    print("recomputed from julia/tier0_ec_matrix.csv + julia/mediated_ec_matrix.csv\n")
    print("%-24s %-26s %s" % ("variant", ">=25 mA cm-2", ">=50 mA cm-2"))
    for k, d in V.items():
        print("  %-22s %-26s %s" % (k, counts(d, 25), counts(d, 50)))
    print("\n  %-22s %-26s %s"
          % ("BAND >=25", [band25[c] for c in ARCH], [band50[c] for c in ARCH]))

    # ---- the sentence the SI prints -------------------------------------------------------
    # THE SHIPPED DOCUMENT, not make_si.js. Reading the generator asks "was this sentence
    # authored?" when the question is "does the .docx a referee opens carry it?" -- and it goes
    # structurally blind the moment a passage becomes computed rather than typed, which is
    # exactly how the Table S5 and S6 checks broke on 2026-08-25.
    import sys as _sys
    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from docx_text import asserted_text as _asserted
    si = unicodedata.normalize(
        "NFKC", _asserted(os.path.join(ROOT, "SI_Section4_Transport_Model.docx")))
    mm = re.search(r"brackets the reported counts at .{0,40}? between\s+(.+?)\s+of 50", si)
    fails = []
    if not mm:
        fails.append("the SI no longer contains the bracket sentence at all -- a vanished claim "
                     "is a FAIL, not a skip (CLAUDE.md trap 10)")
        printed = []
    else:
        printed = re.findall(r"(\d+)\s*[–−-]\s*(\d+)", mm.group(1))
        printed = [(int(a), int(b)) for a, b in printed]
        if len(printed) != len(ARCH):
            fails.append("the SI prints %d ranges, the model has %d architectures"
                         % (len(printed), len(ARCH)))
        else:
            for c, p in zip(ARCH, printed):
                if p != band25[c]:
                    fails.append("%s: SI prints %d-%d, model gives %d-%d"
                                 % (c, p[0], p[1], band25[c][0], band25[c][1]))
    if printed:
        print("\n  SI prints            %s" % printed)

    # ---- cells whose value came from delta-continuation rather than a direct ramp ---------
    # RETIRED 2026-08-23: this block used to assert that Br-mediated Hofmann x unstirred was
    # still a stall, and report what the counts would be if it were resolved. It IS resolved
    # now (delta-continuation, ~100-112 mA cm-2 against a floor of 6.95), so that assertion
    # would be checking for a condition that no longer exists -- the gate's own message said to
    # retire it rather than leave it standing, and this is that retirement.
    #
    # What replaces it is the thing now worth watching: which cells do NOT come from a direct
    # current ramp. A delta-continued value is legitimate but is reached by a different path,
    # and the count belongs in front of a reader rather than buried in a CSV column.
    if "path" not in m.columns:
        fails.append("mediated_ec_matrix.csv has no `path` column -- run_mediated.jl must record "
                     "how each value was reached")
    else:
        ## THE FILTER USED TO BE `m.path != "direct"`, AND `"direct"` IS NOT A VALUE THAT COLUMN
        ## EVER TAKES. run_mediated.jl writes "direct-ramp", "c-control", "delta-continued",
        ## "delta-continued + c-control", "k-continuation" or "k-limit-tracked" -- never "direct".
        ## So the test was true for every row and the gate reported "48 of 48 reached by
        ## delta-continuation" no matter what the matrix said. It was printing that while the
        ## matrix held 46 c-control + 2 direct-ramp and NOT ONE continuation. That is the
        ## value-matching trap in CLAUDE.md, inside a gate: a comparison against a string that
        ## never occurs cannot fail and cannot inform.
        ## Name the ordinary paths and treat everything else as a continuation, and assert the
        ## column only ever holds paths we know about -- so a new path name in run_mediated.jl
        ## makes this gate fire rather than silently misreport.
        DIRECT = {"direct-ramp", "c-control"}
        KNOWN  = DIRECT | {"delta-continued", "delta-continued + c-control",
                           "k-continuation", "k-limit-tracked"}
        unknown = sorted(set(m.path) - KNOWN)
        if unknown:
            fails.append("mediated_ec_matrix.csv has unrecognised path value(s) %s -- update "
                         "check_ecprime_band.py's DIRECT/KNOWN sets deliberately, do not let a "
                         "new path be silently counted as a continuation" % unknown)
        ## THE SI PUBLISHES A CENSUS OF HOW THESE CELLS TERMINATE, AND NOTHING CHECKED IT.
        ## It read "44 of the 48 solves end on a Newton failure and only four reach the collapse
        ## criterion" for nine days after concentration control made that 48 of 48 -- a factor of
        ## twenty-two, behind a fully green suite, because every gate here watched the NUMBERS
        ## and none watched the sentence describing how they were obtained. Bind it.
        import re as _re
        ## pass 15 (2026-10-07): a cell whose concentration-control walk was REJECTED (it did not rise above the k = 0
        ## floor) keeps the ramp's value and the path "direct-ramp", while its limiter still carries the rejected
        ## "plateau (c-control ...)" label. Counting that label as a plateau put ten floor-valued cells into the census;
        ## the census is over the cells whose published value IS the concentration-control result.
        _cc = m[m.path == "c-control"]
        _reach = sum(1 for x in _cc.limiter.astype(str)
                     if "plateau (c-control" in x or x.startswith("collapse"))
        ## A cell whose limiter is "collapse (c-control)" crossed the 1e-3 criterion exactly and
        ## records no plateau value; it sits AT the criterion, so it enters the census at 1e-3.
        ## (Until 2026-09-05 such cells were skipped, so the share "at or below 0.28%" undercounted
        ## them -- 35 where the honest figure is 39.)
        _fr = [float(_re.search(r"c_red/cb ([0-9.eE+-]+)", str(x)).group(1)) if "c_red/cb" in str(x)
               else 1e-3 for x in _cc.limiter if "c_red/cb" in str(x) or str(x).startswith("collapse")]
        if len(_fr) != len(_cc):
            fails.append("%d of %d concentration-control cells carry neither a plateau value nor a collapse "
                         "label" % (len(_cc) - len(_fr), len(_cc)))
        _ncoll = sum(1 for x in _cc.limiter if str(x).startswith("collapse"))
        if _reach != len(_cc):
            fails.append("%d of %d concentration-control cells reach the criterion" % (_reach, len(_cc)))
        # the rest are published at their k = 0 floor: checked against the Stage-1 layer, a second artifact
        _np = pd.read_csv(os.path.join(ROOT, "julia", "all50_np_matrix.csv")).set_index(["reaction", "reactor"])
        if negative_control:     # move one floor cell 1 % off its k = 0 value: the floor check must name it
            m = m.copy(); _i0 = m.index[m.path != "c-control"][0]; m.loc[_i0, "i_ec_mAcm2"] *= 1.01
        for _r in m[m.path != "c-control"].itertuples():
            _k0 = float(_np.loc[(_r.reaction, _r.reactor), "i_np_mAcm2"])
            if abs(_r.i_ec_mAcm2 / _k0 - 1) > 1e-4:
                fails.append("%s / %s keeps its ramp value but is not at its k = 0 floor (%.4f vs %.4f); the SI says it is"
                             % (_r.reaction, _r.reactor, _r.i_ec_mAcm2, _k0))
        _claims = [
            ("cells ending on a concentration-control plateau",
             "Of the %d mediated cells, %d end on a plateau of this walk" % (len(m), len(_cc))),
            ("the others published at their k = 0 floor", "so the value published is that floor"),
            ("plateau depletion range",
             "the reduced mediator there sits between %.2f%% and %.1f%% of its bulk value"
             % (100*min(_fr), 100*max(_fr))),
            ("cells at the criterion exactly",
             "%d of them reaching the 10\u22123 criterion exactly" % _ncoll),
            ("share at or below 0.28%%",
             "%d of the %d at or below 0.28%%" % (sum(1 for v in _fr if 100*v <= 0.28), len(_cc))),
        ]
        # the wall sentence names the cells; both the count and the archetype list are read from the
        # matrix here exactly as make_si.js computes them (it was a typed "Two cells" until 2026-09-07)
        _wall = m[m.limiter.astype(str).str.startswith("newton-wall")]
        _WN = {"Unstirred batch": "unstirred-batch", "Stirred batch": "stirred-batch",
               "Recirculating flow cell": "recirculating-flow", "ANEC flow cell": "ANEC",
               "Microfluidic cell (25 um gap)": "microfluidic", "RDE 1600 rpm": "rotating-disk",
               "Rotating cylinder 3000 rpm": "rotating-cylinder"}
        _NW = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve"]
        # 2026-10-05: the wall cells can span two systems (the triarylamine row, a mediator solved at k = 0, walls in every
        # architecture); the sentence names each system, every architecture or a list, exactly as make_si.js builds it
        _SYS = [("Cl-mediated ethylene", "the Cl\u207b/ethylene system"),
                ("Oxazole synthesis", "the triarylamine-mediated oxazole synthesis, solved at k = 0")]
        _and = lambda xs: xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]
        _parts = []
        for _key, _label in _SYS:
            _w = _wall[_wall.reaction.str.contains(_key, regex=False)]
            if len(_w):
                _parts.append(("every architecture" if len(_w) == 7 else "the %s architectures" % _and([_WN[r] for r in _w.reactor]))
                              + " of " + _label)
        _unnamed = [r for r in _wall.reaction.unique() if not any(k in r for k, _ in _SYS)]
        if _unnamed:
            fails.append("wall cells of %r have no name in the SI's wall sentence" % _unnamed)
        elif len(_wall):
            _claims.append(("cells recording a ramp wall first", "%s cells \u2014 %s \u2014" % (_NW[len(_wall)], _and(_parts))))
        for _lbl, _ph in _claims:
            if unicodedata.normalize("NFKC", _ph) not in si:
                fails.append("SI census claim %r is absent or reworded -- expected %r"
                             % (_lbl, _ph[:80]))

        print("\n  path taken by each of the %d mediated cells:" % len(m))
        for name, n in m.path.value_counts().items():
            print("    %-32s %d" % (name, n))
        cont = m[~m.path.isin(DIRECT)]
        print("  cells needing a CONTINUATION rather than the ordinary ramp/c-control: %d of %d"
              % (len(cont), len(m)))
        for r in cont.itertuples():
            print("    %s x %s: i_ec %.1f (Tier-0 floor %.2f, substrate-supply scale %.1f)"
                  % (r.reaction, r.reactor, r.i_ec_mAcm2, r.i_tier0_mAcm2, r.i_subcap_mAcm2))
        stalled = m[m.flag != "ok"]
        if len(stalled):
            print("  cells still floored to Tier-0 (ramp died below the commuting bound): %d"
                  % len(stalled))
            for r in stalled.itertuples():
                print("    %s x %s" % (r.reaction, r.reactor))
        else:
            print("  no cell is floored to Tier-0 any more: every one of the %d clears its own "
                  "commuting bound" % len(m))

    print("\nG-ECBAND: %s" % ("PASS" if not fails else "FAIL"))
    for f in fails:
        print("  " + f)
    if negative_control:
        fired = any("rde" in f for f in fails) and any("not at its k = 0 floor" in f for f in fails)
        print("\nnegative control: tripled every RDE solve, so the RDE end of the bracket must "
              "move, and moved one floor cell 1 % off its k = 0 value, which the floor check must name")
        print("  %s" % ("OK -- the gate fired on rde" if fired
                        else "BAD -- the gate did not notice"))
        sys.exit(0 if fired else 1)
    if fails:
        raise AssertionError("; ".join(fails))


if __name__ == "__main__":
    main(negative_control="--negative-control" in sys.argv)
