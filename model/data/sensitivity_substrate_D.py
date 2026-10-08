#!/usr/bin/env python3
"""G-DSUBSENS -- bound what the 8 hand-typed mediated substrate diffusivities cost.

    cd Section4_Model && python data/sensitivity_substrate_D.py 0.7 1.3

WHY THIS EXISTS
---------------
The registry publishes "8 mediated-spec substrate D values" as class `derived`, method
"Wilke-Chang on named surrogate structures". The method and the structures are NAMED, but NOTHING
reproduces the arithmetic: OERxn carries no substrate-D field, build_reactions50.py computes none,
and the eight numbers are typed by hand into run_mediated.jl. That fails the state-B test in
PROVENANCE_STANDARD.md ("the arithmetic reproducible from the registry alone"), and unlike a
spectator diffusivity these are MATERIAL -- D_S sets i_subcap and enters the EC' source.

Until the surrogate structures are pinned down (three of the eight names are ambiguous), the
honest move is the one G-DSENS already makes for the unsourced ion diffusivities: not to invent a
number, but to BOUND WHAT NOT KNOWING IT COSTS. This perturbs all eight together and reports
whether the published counts move.

It never touches the production solver. It writes a patched COPY of run_mediated.jl with the
substrate D values scaled and the output redirected, so `mediated_ec_matrix.csv` is untouched.
"""
import os, re, subprocess, sys, csv, io

HERE = os.path.dirname(os.path.abspath(__file__)); SEC4 = os.path.dirname(HERE)
JL = os.path.join(SEC4, "julia")
SRC = os.path.join(JL, "run_mediated.jl")


REGISTRY_SUFFIX = "mediated-spec substrate D values"     # the row is named with its own count
MAX_DECLARED_MOVE = 1          # entries; a larger movement is a finding, not a disclosure


def movements(d):
    """Every (scale, architecture, threshold, before, after) the sweep moved."""
    base, out = d["base_counts"], []
    for scale, per_arch in sorted(d["counts"].items(), key=lambda kv: float(kv[0])):
        for arch, c in per_arch.items():
            for i, thr in enumerate((25, 50)):
                if c[i] != base[arch][i]:
                    out.append((float(scale), arch, thr, base[arch][i], c[i]))
    return out


def registry_sensitivity():
    path = os.path.join(SEC4, "data", "parameters_provenance.csv")
    hits = [r for r in csv.DictReader(io.open(path, encoding="utf-8"))
            if (r.get("parameter") or "").strip().endswith(REGISTRY_SUFFIX)]
    return (hits[0].get("sensitivity") or "") if len(hits) == 1 else None


def verdict(d, quiet=False):
    """PASS/FAIL on the DISCLOSED claim.

    A movement is not itself a failure -- the sweep exists to measure one. What fails is a
    movement the published row does not declare, or one bigger than the row's stated bound. This
    mirrors G-SCRANGE, which had to stop failing on the mere EXISTENCE of a Schmidt inversion once
    a real correlation produced one, and test disclosure instead: a check that can only be silenced
    by deleting the comparison is not a check.
    """
    moves = movements(d)
    fails = []
    if not moves:
        if not quiet:
            print("G-DSUBSENS: PASS -- no >=25 or >=50 count moves across x%.2f-%.2f on all the mediated "
                  "substrate diffusivities" % (min(d["scales"]), max(d["scales"])))
        return 0
    worst = max(abs(a - b) for _, _, _, b, a in moves)
    sens = registry_sensitivity()
    if sens is None:
        fails.append("no single registry row ends in %r, so the movement is published nowhere" % REGISTRY_SUFFIX)
        sens = ""
    if worst > MAX_DECLARED_MOVE:
        fails.append("a count moves by %d entries, beyond the declared bound of %d -- that is "
                     "a finding to report, not a sensitivity to restate" % (worst, MAX_DECLARED_MOVE))
    for _, arch, thr, b, a in moves:
        if arch not in sens or (">=%d" % thr) not in sens.replace("\u2265", ">="):
            fails.append("the registry row does not declare that the >=%d count of the %s moves "
                         "%d -> %d" % (thr, arch, b, a))
    if not quiet:
        print("substrate-D sweep moved %d count(s), worst %d entr%s:"
              % (len(moves), worst, "y" if worst == 1 else "ies"))
        for sc, arch, thr, b, a in moves:
            print("    x%.2f  %-32s >=%d  %d -> %d" % (sc, arch, thr, b, a))
        for f in fails:
            print("    FAIL  %s" % f)
    if fails:
        if not quiet:
            print("G-DSUBSENS: FAIL -- the sweep and the published row disagree")
        return 1
    if not quiet:
        print("G-DSUBSENS: PASS -- every count movement is within +/-%d and is declared "
              "verbatim in the registry row that publishes this sweep" % MAX_DECLARED_MOVE)
    return 0


def patch(scale, tag):
    s = io.open(SRC, encoding="utf-8").read()
    n = 0
    ## the 9th MedSpec field is D_S
    def med(m):
        nonlocal n; n += 1
        return "%s%.6g" % (m.group(1), float(m.group(2)) * scale)
    s = re.sub(r'(MedSpec\("[^"]+",\s*[\d.e+-]+,\s*[\d.e+-]+,\s*[\d.e+-]+,\s*\d+,\s*\d+,\s*[\d.]+,\s*[\d.]+,\s*)([\d.e+-]+)',
               med, s)
    ## and the Sub species' own D
    def sub(m):
        nonlocal n; n += 1
        return '%s%.6g' % (m.group(1), float(m.group(2)) * scale)
    s = re.sub(r'(S\("Sub",\s*[\d.]+,\s*)([\d.e+-]+)', sub, s)
    out = "mediated_ec_matrix_%s.csv" % tag
    s = s.replace('open(joinpath(@__DIR__, "mediated_ec_matrix.csv"), "w")',
                  'open(joinpath(@__DIR__, "%s"), "w")' % out)
    p = os.path.join(JL, "_dsub_%s.jl" % tag)
    nspec = len(re.findall(r'MedSpec\("', s))
    if n != 2 * nspec:
        raise SystemExit("patched %d substrate-D literals for %d MedSpecs; expected two each (the MedSpec "
                         "field and the Sub species) -- the regex has drifted from the solver" % (n, nspec))
    io.open(p, "w", encoding="utf-8").write(s)
    return p, out, n

def counts(path):
    rows = list(csv.DictReader(io.open(path, encoding="utf-8")))
    by = {}
    for r in rows:
        by.setdefault(r["reactor"], []).append(float(r["i_ec_mAcm2"]))
    return {k: (sum(v >= 25 for v in vs), sum(v >= 50 for v in vs), sorted(vs)[len(vs)//2])
            for k, vs in by.items()}

def main(scales):
    base = counts(os.path.join(JL, "mediated_ec_matrix.csv"))
    results = {}
    ## the scales write to different files, so they are solved side by side
    from concurrent.futures import ThreadPoolExecutor
    def one(sc):
        tag = ("%g" % sc).replace(".", "p")
        p, out, n = patch(sc, tag)
        print("scale %.2f: patched %d substrate-D literals -> %s" % (sc, n, os.path.basename(p)))
        sys.stdout.flush()
        r = subprocess.run(["julia", os.path.basename(p)], cwd=JL, capture_output=True, text=True)
        os.remove(p)
        if r.returncode != 0:
            print("   solver failed:", r.stderr[-400:]); return sc, None
        return sc, counts(os.path.join(JL, out))
    if "--from-files" in sys.argv:
        ## Re-derive the summary from the scaled matrices already on disk, without solving: used when single rows of
        ## them were re-solved in isolation (2026-10-05, two rows whose rate constant changed) and spliced in. Each
        ## file must hold seven cells for every MedSpec of the live solver, or it is not this sweep's matrix.
        want = set(re.findall(r'MedSpec\("([^"]+)"', io.open(SRC, encoding="utf-8").read()))
        for sc in scales:
            f = os.path.join(JL, "mediated_ec_matrix_%s.csv" % ("%g" % sc).replace(".", "p"))
            rows = list(csv.DictReader(io.open(f, encoding="utf-8")))
            have = {}
            for r in rows:
                have[r["reaction"]] = have.get(r["reaction"], 0) + 1
            if set(have) != want or any(v != 7 for v in have.values()):
                raise SystemExit("--from-files: %s does not hold seven cells for every MedSpec" % os.path.basename(f))
            results[sc] = counts(f)
        print("re-deriving the summary from the scaled matrices on disk (no solve)")
    else:
      with ThreadPoolExecutor(max_workers=len(scales)) as ex:
        for sc, c in ex.map(one, scales):
            if c is not None:
                results[sc] = c
    if len(results) != len(scales):
        raise SystemExit("a scaled solve failed; no artifact written")
    print("\n%-28s %-16s %s" % ("reactor", "baseline (25/50)", "  ".join("x%.2f" % s for s in scales)))
    moved = False
    for k in sorted(base):
        row = "%-28s %2d/%2d            " % (k[:28], base[k][0], base[k][1])
        for sc in scales:
            if sc not in results: continue
            c = results[sc][k]
            row += " %2d/%2d" % (c[0], c[1])
            if c[:2] != base[k][:2]: moved = True
        print(row)
    print()
    ## Until 2026-09-05 this gate printed a sentence with no PASS/FAIL and exited 0 either way, so the
    ## runner could not see it fail; and the registry row it backs quoted a typed result from an
    ## earlier matrix ("Br- oxidation x unstirred reads 25.34 ... 12/50 -> 11/50 once D_S is 7.6 %
    ## low") that the unstirred-film change had made false (the cell reads 33.3 now). The sweep
    ## writes its result and the registry interpolates it; the verdict is PASS when no count moves
    ## and FAIL when one does, so a movement has to be declared, not discovered by hand.
    import json as _json
    base_rows = list(csv.DictReader(io.open(os.path.join(JL, "mediated_ec_matrix.csv"), encoding="utf-8")))
    margins = sorted(((abs(float(r["i_ec_mAcm2"]) - 25.0) / 25.0, r["reaction"], r["reactor"], float(r["i_ec_mAcm2"]))
                      for r in base_rows), key=lambda t: t[0])
    closest = {"reaction": margins[0][1], "reactor": margins[0][2], "i_mAcm2": margins[0][3],
               "margin_pct_to_25": 100.0 * margins[0][0]}
    out = {"note": "G-DSUBSENS: all mediated substrate diffusivities scaled together, mediated matrix "
                   "re-solved per scale; counts over the mediated rows per architecture. Written by "
                   "data/sensitivity_substrate_D.py",
           "scales": scales, "base_counts": {k: list(v[:2]) for k, v in base.items()},
           "counts": {("%g" % sc): {k: list(v[:2]) for k, v in results[sc].items()} for sc in scales if sc in results},
           "counts_moved": moved, "closest_cell_to_25": closest}
    out["verdict"] = "PASS" if verdict(out, quiet=True) == 0 else "FAIL"
    with open(os.path.join(os.path.dirname(JL), "results", "substrate_D_sensitivity.json"), "w", encoding="utf-8") as fh:
        _json.dump(out, fh, indent=2)
    print("wrote results/substrate_D_sensitivity.json")
    print("closest mediated cell to 25 mA cm-2 is %s / %s at %.2f (%.1f%% away)"
          % (closest["reaction"][:30], closest["reactor"], closest["i_mAcm2"], closest["margin_pct_to_25"]))
    raise SystemExit(verdict(out))

def check_registry(neg=False):
    """Fast tier (G-DSUBSENS-REG): re-check the DISCLOSURE against the stored sweep, no re-solve."""
    import json as _json
    with io.open(os.path.join(SEC4, "results", "substrate_D_sensitivity.json"), encoding="utf-8") as fh:
        d = _json.load(fh)
    if neg:
        # perturb the MODEL side, never the document: invent a movement twice the declared bound
        arch = sorted(d["base_counts"])[0]
        sc = sorted(d["counts"])[0]
        d["counts"][sc][arch] = [d["base_counts"][arch][0] - 3, d["base_counts"][arch][1]]
        rc = verdict(d)
        good = rc != 0
        print("\nNEGATIVE CONTROL: an undeclared 3-entry movement injected into the sweep result.")
        print("G-DSUBSENS-REG control: %s" % ("GOOD" if good else "BAD -- test is inert"))
        return 0 if good else 1
    return verdict(d)


if __name__ == "__main__":
    if "--check-registry" in sys.argv:
        sys.exit(check_registry(neg="--negative-control" in sys.argv))
    main([float(x) for x in ([a for a in sys.argv[1:] if not a.startswith("-")] or ["0.7", "1.3"])])
