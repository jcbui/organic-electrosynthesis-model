#!/usr/bin/env python3
"""Diff a solver matrix against a backup, cell by cell.

    python data/diff_matrix.py julia/mediated_ec_matrix.csv julia/mediated_ec_matrix.csv.bak_preTrustRegion

Reports every cell whose current, flag, path or limiter CLASS changed, and summarises how many
were bit-identical. Written for the trust-region change (docs/CELL48_BROMINATION_UNSTIRRED.md),
where the expectation is specific and falsifiable: cells with no species below 1e-10 of bulk must
be bit-identical, and any cell that moves must move UP (the old step control stopped short of the
fold, it never overshot it).
"""
import csv, io, sys, os

def load(p, keycols, valcol):
    rows = {}
    with io.open(p, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[tuple(r[c] for c in keycols)] = r
    return rows

def limclass(s):
    s = (s or "").lower()
    for c in ("plateau", "collapse", "limit reached", "newton-wall", "unresolved", "delta-continued"):
        if c in s:
            return c
    return "other"

def main(new_p, old_p):
    hdr = csv.DictReader(io.open(new_p, encoding="utf-8")).fieldnames
    keycols = [c for c in ("reaction", "reactor") if c in hdr]
    valcol = next((c for c in ("i_ec_mAcm2", "i_np_mAcm2", "i_lim_mAcm2", "i_tier0_mAcm2")
                   if c in hdr), None)
    if valcol is None:
        raise SystemExit("no recognised current column in %s; header is %s" % (new_p, hdr))
    new, old = load(new_p, keycols, valcol), load(old_p, keycols, valcol)

    same = 0; moved = []; appeared = []; classchg = []
    for k, rn in new.items():
        ro = old.get(k)
        if ro is None:
            appeared.append((k, rn)); continue
        try:
            vn, vo = float(rn[valcol]), float(ro[valcol])
        except (ValueError, TypeError):
            continue
        if vn == vo:
            same += 1
        else:
            moved.append((k, vo, vn, 100.0*(vn-vo)/vo if vo else float("nan")))
        if "limiter" in rn and limclass(rn.get("limiter")) != limclass(ro.get("limiter")):
            classchg.append((k, limclass(ro.get("limiter")), limclass(rn.get("limiter"))))

    print(f"{len(new)} cells; {same} bit-identical, {len(moved)} moved, {len(appeared)} new")
    if moved:
        moved.sort(key=lambda t: -abs(t[3]))
        print(f"\n{'reaction':44s} {'reactor':22s} {'old':>10s} {'new':>10s} {'delta%':>9s}")
        for k, vo, vn, d in moved:
            print(f"{k[0][:44]:44s} {k[1][:22]:22s} {vo:10.4f} {vn:10.4f} {d:+9.4f}")
        down = [m for m in moved if m[2] < m[1]]
        print(f"\n{len(moved)} moved: {len(moved)-len(down)} up, {len(down)} DOWN")
        for k, vo, vn, d in down:
            print(f"  DOWN: {k[0][:40]} / {k[1]}  {vo:.4f} -> {vn:.4f} ({d:+.4f}%)")
    if classchg:
        print("\nlimiter class changes:")
        for k, a, b in classchg:
            print(f"  {k[0][:40]:40s} {k[1][:20]:20s} {a} -> {b}")
    for k, rn in appeared:
        print(f"  NEW CELL: {k}")
    ## flags
    if "flag" in hdr:
        bad_new = [k for k, r in new.items() if r.get("flag") != "ok"]
        bad_old = [k for k, r in old.items() if r.get("flag") != "ok"]
        print(f"\nnot flagged ok: {len(bad_old)} before -> {len(bad_new)} now")
        for k in bad_new:
            print(f"  still not ok: {k[0][:44]} / {k[1]}  flag={new[k]['flag']}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
