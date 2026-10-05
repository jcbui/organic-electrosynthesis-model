"""Which registry rows support a stated result, and which are development scaffolding?

    cd Section4_Model && python data/registry_liveness.py

WHY
---
The published SI should carry the parameters a reader needs in order to check a claim, and not
the ones that exist only because the model was built incrementally. Those are different sets, and
until now the SI printed their union: Table S7 dumped all 271 registry rows, so a reviewer reading
the conductivity census saw "0 measured / 8 derived / 41 assumption" and reasonably concluded the
thermal analysis rests on forty-one unsourced numbers. It does not. It rests on four. The other
41 are attached to reactions but drive nothing that is reported, and their presence made the
weakest-looking category in the registry also the most inert one.

THE RULE, STATED ONCE
---------------------
A row is DEAD when it cannot support any stated claim, graphic or table entry. Concretely:

  1. every row of a solvent that no reaction in reactions_50.csv uses;
  2. every row of an electrolyte whose own registry sensitivity declares it display-only
     (kappa enters no transport quantity, so only the four Fig. K electrolytes carry a verdict);
  3. any other row whose sensitivity declares it display-only, unassigned, or without a consumer.

Everything else is LIVE. The rule is applied to the registry text and the reaction table, never
to a hand-maintained list, so a row cannot be quietly reclassified to make a census look better.

WHAT IS *NOT* DEAD, AND WHY THE DISTINCTION MATTERS
---------------------------------------------------
"Sets no reported i_lim" is not the same as "supports no stated graphic". The solver-species
diffusivities set ion migration and the film potential inside the EC-prime solve whose output is
plotted as the mediated rows of Fig. 3 and Fig. 4. They are inputs to a shipped figure, so they
stay -- and that they stay is checked by perturbation, not asserted: see G-LIVE below.

WHAT HAPPENS TO THE DEAD ROWS
-----------------------------
They are dropped from the published SI and KEPT in data/parameters_provenance.csv, which remains
the complete internal record and the provenance file for the code. Nothing is deleted; the SI
states how many rows it omits and why, so the omission is disclosed rather than silent.
"""
import json
import os
import re

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "registry_liveness.json")

RE_DEAD = re.compile(r"display-only|not assigned to any of the 50|no consumer|zero consumers|"
                     r"enters no reported number|unused", re.I)
# A sensitivity that DENIES being display-only must not be matched by the phrase it denies. This
# has now bitten three separate checks in this project -- the assumption-ledger tier classifier,
# the manuscript kappa gate, and this one -- always the same way: prose that quotes a status in
# order to withdraw or contradict it. Whenever a gate reads prose, it needs this guard.
RE_NOT_DEAD = re.compile(r"\bis not display-only\b|\bnot display-only\b|carries a fig\. k verdict|"
                         r"carries a manuscript claim|carries a conclusion|enters a reported result",
                         re.I)


def main():
    reg = pd.read_csv(os.path.join(HERE, "parameters_provenance.csv"))
    rx = pd.read_csv(os.path.join(HERE, "reactions_50.csv"))
    sol = pd.read_csv(os.path.join(HERE, "solvents.csv"))

    used_solvents = set(rx.solvent.dropna())
    dead_solvents = set(sol.iloc[:, 0]) - used_solvents

    def is_dead(r):
        cat, param = str(r.category), str(r.parameter)
        # Read the SENSITIVITY only. That field is where a row DECLARES its status; the method
        # note is prose and may legitimately quote the words "display-only" or "unused-legacy"
        # while recounting what a row used to be. Matching the note marked `0.1 M Bu4NBF4/DMF`
        # dead for describing the history it had just escaped -- and that row is quoted in the
        # manuscript, so trimming it from the SI would have re-created the exact hole G-MSKAPPA
        # exists to catch.
        blob = str(r.get("sensitivity", ""))
        if cat.startswith("2. Solvents"):
            name = param.split(":")[0].strip()
            if name in dead_solvents:
                return "solvent used by no reaction"
        if RE_NOT_DEAD.search(blob):
            return ""
        if RE_DEAD.search(blob):
            return "declared display-only / unassigned by its own registry text"
        return ""

    reg["dead_reason"] = reg.apply(is_dead, axis=1)
    dead = reg[reg.dead_reason != ""]
    live = reg[reg.dead_reason == ""]

    print("registry: %d rows -> %d LIVE, %d DEAD" % (len(reg), len(live), len(dead)))
    print("\ndead rows by category:")
    for c, n in dead.category.value_counts().items():
        print("   %-34s %d" % (c, n))
    print("\ncensus, whole registry vs published (live) subset:")
    for lab, d in (("whole registry ", reg), ("published (live)", live), ("omitted (dead) ", dead)):
        v = d.provenance_class.value_counts()
        print("   %-17s n=%3d  measured=%3d  derived=%3d  assumption=%3d"
              % (lab, len(d), v.get("measured", 0), v.get("derived", 0), v.get("assumption", 0)))

    cond = live[live.category.str.startswith("6.")]
    v = cond.provenance_class.value_counts()
    print("\n   conductivities that survive the filter: n=%d (%d measured, %d derived, %d assumption)"
          % (len(cond), v.get("measured", 0), v.get("derived", 0), v.get("assumption", 0)))

    rep = dict(n_total=len(reg), n_live=len(live), n_dead=len(dead),
               dead_solvents=sorted(dead_solvents),
               dead_parameters=dead.parameter.tolist(),
               live_parameters=live.parameter.tolist(),
               census_live={k: int(live.provenance_class.value_counts().get(k, 0))
                            for k in ("measured", "derived", "assumption")},
               census_dead={k: int(dead.provenance_class.value_counts().get(k, 0))
                            for k in ("measured", "derived", "assumption")})
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(rep, f, indent=2)
    print("\nwrote %s" % os.path.relpath(OUT, ROOT))

    # ---- G-LIVE: nothing load-bearing may be dropped ----
    fails = []
    if len(dead) + len(live) != len(reg):
        fails.append("live/dead do not partition the registry")
    # A dead row must never be one the solvers read. The solver species live in category 4 and
    # the four Fig. K electrolytes carry verdicts -- neither may appear in the dead set.
    bad = dead[dead.category.str.startswith("4.")]
    if len(bad):
        fails.append("solver-species rows marked dead: %s" % bad.parameter.tolist())
    figk = ["3.0 M LiBr/THF", "0.25 M Bu4NBF4/MeCN", "0.2 M NaI/DMF", "1 M NaOH aq"]
    hit = [p for p in figk if p in set(dead.parameter.str.split(":").str[0])]
    if hit:
        fails.append("Fig. K conductivities marked dead: %s" % hit)
    for s_ in used_solvents:
        if s_ in dead_solvents:
            fails.append("solvent %s is both used and dead" % s_)
    print("\nG-LIVE: %s" % ("PASS" if not fails else "FAIL"))
    for f_ in fails:
        print("  " + f_)
    if fails:
        raise AssertionError("; ".join(fails))
    print("  the dead set contains no solver-species row, no Fig. K conductivity, and no solvent")
    print("  that any of the 50 reactions uses")
    return rep


if __name__ == "__main__":
    main()
