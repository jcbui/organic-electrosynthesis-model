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
                     ("THF-MeOH","THF"),("THF-EtOH","EtOH"),("THF","THF"),("EtOH-MeOH","EtOH"),
                     ("H2O-MeCN","H2O"),("tAmOH-H2O","tAmOH"),("AcOH-HCOOH","AcOH")]:
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

## Class defaults of the declared supporting-ion slots (registry rows 'Bu4N+/Q+ (organic)' and
## 'BF4-/generic A- (organic)').
CLASS_DEFAULT = {"cation": 1.0e-9, "anion": 1.5e-9}
## Declared slots that carry a value other than the class default: (ion, solvent key) -> (D in m2/s,
## the basis of that value). Each is a supporting ion in a medium for which no limiting conductance is
## tabulated; the basis says where the number comes from.
## Slots outside Krumgalz/CRC that a retrieved source does cover (2026-10-07): state B by Nernst-Einstein from a measured
## limiting conductance. Checked like DECLARED_VALUES: the table must carry exactly this value.
SOURCED_VALUES = {
    ("B(OH)4-", "aq"): (9.39e-10,
        "state B; Nernst-Einstein from lambda0(B(OH)4-) = 35.27 S cm2 mol-1 at 25 C (Corti, Crovetto & Fernandez-Prini, "
        "J. Solution Chem. 1980, 9, 617-625, Table III, p. 621)"),
}
DECLARED_VALUES = {
    ("K+", "tAmOH"): (1.957e-9,
        "value: the aqueous K+ diffusivity (CRC 97th ed., Vanysek, p. 5-75, D column) carried to tAmOH/H2O 3:1"),
    ("Br-", "THF"): (2.08e-9,
        "value: the aqueous Br- diffusivity (CRC 97th ed., Vanysek, p. 5-75, D column, 2.080e-9) carried to THF"),
    ("RCO2- (Et3NH+ carboxylate pair)", "MeOH"): (1.269e-9,
        "value: the carboxylate given the Wilke-Chang diffusivity in MeOH of its parent acid, this row's carrier "
        "(Table S2, 1.269e-5 cm2 s-1)"),
    ("ClO4-", "AcOH"): (1.7e-9,
        "value: the registry row 'ClO4- (MeCN, aq-like)' (Table S7d), 5% below the aqueous 1.792e-9 (CRC 97th ed., "
        "Vanysek, p. 5-75), carried to AcOH/HCOOH as in this row's EC' solve"),
    ("H+", "MeCN"): (3e-9,
        "value: the registry row 'H+ (MeCN/organic)' (Table S7d), about a third of the aqueous 9.311e-9 (CRC 97th "
        "ed., Vanysek, p. 5-75) because an aprotic medium supports no Grotthuss shuttle"),
}
declared_used = set()

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
            ## A slot with no tabulated limiting conductance keeps the D the table carries, and the label
            ## says which kind of declaration that D is: the class default (1.0e-9 for a cation, 1.5e-9
            ## for an anion), or a declared value of another origin, which must be one of DECLARED_VALUES
            ## and must carry exactly the value recorded there. Anything else stops the script, so a slot
            ## can never be labelled a class default while holding some other number.
            d_now = float(r[d_col])
            gap_txt = ("(supporting ion: it carries no flux, so its D does not enter i_lim; Table S7d) -- "
                       "no lambda0 for %s in %s in Krumgalz 1983 or CRC 97th ed. pp. 5-75 to 5-77" % (ion, sv))
            if (ion, sv) in SOURCED_VALUES:
                d_src, why = SOURCED_VALUES[(ion, sv)]
                if abs(d_now - d_src) > 1e-6 * d_src:
                    raise SystemExit("%s in %s carries D = %g, but SOURCED_VALUES records %g" % (ion, sv, d_now, d_src))
                r[basis_col] = why
                n_set += 1
                continue
            if abs(d_now - CLASS_DEFAULT[ion_col]) <= 1e-6 * CLASS_DEFAULT[ion_col]:
                r[basis_col] = "DECLARED CLASS DEFAULT " + gap_txt
            elif (ion, sv) in DECLARED_VALUES:
                d_decl, why = DECLARED_VALUES[(ion, sv)]
                if abs(d_now - d_decl) > 1e-6 * d_decl:
                    raise SystemExit("%s in %s (%s) carries D = %g, but DECLARED_VALUES records %g for it; "
                                     "fix the table or the record" % (ion, sv, r["reaction"], d_now, d_decl))
                r[basis_col] = "DECLARED VALUE " + gap_txt + "; " + why
                declared_used.add((ion, sv))
            else:
                raise SystemExit("%s in %s (%s) has no tabulated lambda0 and carries D = %g, which is neither the "
                                 "class default (%g) nor a value recorded in DECLARED_VALUES; record its basis "
                                 "there" % (ion, sv, r["reaction"], d_now, CLASS_DEFAULT[ion_col]))
            gaps[(ion, sv)] = gaps.get((ion, sv), 0) + 1
            n_gap += 1

unused = sorted(set(DECLARED_VALUES) - declared_used)
if unused:
    raise SystemExit("DECLARED_VALUES records %s, which no slot of the table uses; remove the record or restore "
                     "the slot" % unused)
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
