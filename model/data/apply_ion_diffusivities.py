#!/usr/bin/env python3
"""Replace the DEFAULT ion diffusivities in electrolyte_ions.csv with the sourced ones.

    cd Section4_Model && python data/apply_ion_diffusivities.py --dry-run
    cd Section4_Model && python data/apply_ion_diffusivities.py

`electrolyte_ions.csv` carried `1e-09` for 32 different cations and `1.5e-09` for 24 different
anions -- defaults, not data, feeding the migration term. `build_ion_diffusivities.py` derives real
values from Krumgalz 1983 via Nernst-Einstein (validated to <0.05% against four independently-known
aqueous D). This script substitutes them and, critically, LEAVES A MARK on every row it cannot
source, so the remaining gap stays countable instead of disappearing into a plausible number.
"""
import csv, io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DRY = "--dry-run" in sys.argv

# solvent-string -> the key used in ion_diffusivities.csv. Mixtures resolve to their MAJOR
# component by volume; that is an approximation and is recorded in the note, not hidden.
def solvent_key(elec):
    s = elec.split("/")[-1] if "/" in elec else "aq"
    for pre, key in [("MeCN-H2O","MeCN"),("MeCN-HCl","MeCN"),("MeCN","MeCN"),
                     ("MeOH-H2O","MeOH"),("MeOH","MeOH"),("acetone","acetone"),
                     ("DMA","DMA"),("DMF","DMF"),("DMSO","DMSO"),("MeNO2","MeNO2"),
                     ("HFIP-MeOH","HFIP"),("HFIP","HFIP"),("THF-HFIP","THF"),
                     ("THF-MeOH","THF"),("THF","THF"),("EtOH-MeOH","EtOH"),
                     ("H2O-MeCN","H2O"),("tAmOH-H2O","H2O"),("AcOH-HCOOH","AcOH")]:
        if s.startswith(pre):
            return key
    return "aq"

D = {}
for r in csv.DictReader(open(os.path.join(HERE, "ion_diffusivities.csv"))):
    D[(r["ion"], r["solvent"])] = (float(r["D_m2s"]), r["basis"], r["state"])

def load(path):
    """Read the table, refusing anything malformed instead of silently mangling it.

    THIS GUARD EXISTS BECAUSE THIS SCRIPT DESTROYED THE FILE ONCE. Two rows of
    electrolyte_ions.csv had been written earlier the same day with an UNQUOTED COMMA inside their
    `note` text ("...; estimate, not measured (...)"), giving them 12 fields against an 11-column
    header. csv.DictReader files that overflow under the key None; csv.DictWriter then raises
    ValueError on the first such row. The original version wrote straight over its own input, so
    the exception left a 3-row file where 50 had been, and the only reason nothing was lost is that
    a .bak had been taken a minute earlier. Never write in place, and never trust a row count.
    """
    rows = list(csv.DictReader(open(path)))
    bad = [i for i, r in enumerate(rows) if None in r]
    if bad:
        raise SystemExit(
            "electrolyte_ions.csv rows %s have more fields than the header -- almost certainly an "
            "unquoted comma inside a note or basis string. Fix the quoting; do not let this script "
            "rewrite the file in that state." % bad)
    return rows


def save(path, fields, rows):
    """Write via a temp file, round-trip it, and only then replace the original."""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, quoting=csv.QUOTE_MINIMAL)
    w.writeheader(); w.writerows(rows)
    txt = buf.getvalue()
    back = list(csv.DictReader(io.StringIO(txt)))
    if len(back) != len(rows):
        raise SystemExit("refusing to write: round trip gave %d rows, expected %d"
                         % (len(back), len(rows)))
    if any(None in r for r in back):
        raise SystemExit("refusing to write: round trip produced overflow fields")
    tmp = path + ".tmp"
    io.open(tmp, "w", encoding="utf8", newline="").write(txt)
    os.replace(tmp, path)
    return len(back)


rows = load(os.path.join(HERE, "electrolyte_ions.csv"))
fields = [k for k in rows[0].keys() if k is not None]
for extra in ("D_cat_basis", "D_an_basis"):
    if extra not in fields:
        fields.append(extra)

n_set = n_gap = 0
gaps = {}
for r in rows:
    sv = solvent_key(r["electrolyte"])
    for ion_col, d_col, basis_col in (("cation","D_cat","D_cat_basis"),
                                      ("anion","D_an","D_an_basis")):
        ion = r[ion_col]
        hit = D.get((ion, sv))
        if hit:
            val, basis, state = hit
            r[d_col] = "%.4g" % val
            note = "state %s; %s" % (state, basis)
            raw_solv = r["electrolyte"].split("/")[-1] if "/" in r["electrolyte"] else "aq"
            if sv != raw_solv:
                note += "; solvent taken as major component %s of '%s'" % (sv, raw_solv)
            r[basis_col] = note
            n_set += 1
        else:
            r[basis_col] = ("DECLARED CLASS DEFAULT (supporting ion: it carries no flux, so its D "
                            "does not enter i_lim; Table S7d) -- no lambda0 for %s in %s in "
                            "Krumgalz 1983 or CRC 5-75/5-76" % (ion, sv))
            gaps[(ion, sv)] = gaps.get((ion, sv), 0) + 1
            n_gap += 1

print("sourced   : %d of %d (ion, row) slots" % (n_set, 2 * len(rows)))
print("unsourced : %d slots, %d distinct (ion, solvent) pairs" % (n_gap, len(gaps)))
print("\nremaining gaps, by frequency:")
for (ion, sv), c in sorted(gaps.items(), key=lambda x: (-x[1], x[0])):
    print("   %-9s in %-8s  %d rows" % (ion, sv, c))
if DRY:
    print("\n--dry-run: nothing written")
    raise SystemExit(0)
n = save(os.path.join(HERE, "electrolyte_ions.csv"), fields, rows)
print("\nwrote data/electrolyte_ions.csv (%d rows, round-trip verified)" % n)
