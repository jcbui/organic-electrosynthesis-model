"""Mediated vs direct electron transfer, on the KHL (Kasie) corpus.

Port of Figure1_reproducibility_package/polarity/mediated_split.py. The CAS
dictionaries, the bin priority and the anodic-mediator polarity gate are carried over
verbatim -- only the inputs move:

  reagents / catalysts  <- Figure_1b_Kasie/filtered_echem.parquet   (25,941 records)
  polarity label        <- Figure_1b_Kasie/polarity_redox.parquet   (site_label)

The old script read `unique_reactions.parquet` and `corpus_polarity_full.parquet` under
hardcoded /home/claude/rce paths, neither of which exists in this tree; this one resolves
everything relative to itself.

ONE BEHAVIOURAL DIFFERENCE, deliberate and reported at run time. The old corpus carried a
polarity label for every record, so the anodic-mediator gate could be applied to all of
them. Kasie's polarity is only scored for reactions that survive classification
(21,459 of 25,941), so ~4.5k records have no label. Those keep their raw bin -- the gate
is skipped rather than guessed. The count is printed and asserted below.

Bins (priority order -- a record takes the first bin that hits):
  catalyst : molecular metal catalyst present (metal salt/complex or dedicated ligand)
  mediator : unambiguous organic/inorganic redox shuttle
  halide   : alkali/ammonium halide or pseudohalide salt in the REAGENT field
  direct   : reagent data present, none of the above
  no_data  : no reagent/catalyst fields captured
Tetraalkylammonium halides are supporting electrolytes and do NOT count toward 'halide'.
"""
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
KHL = os.path.join(os.path.dirname(HERE), "Figure_1b_Kasie")
CORPUS = os.path.join(KHL, "filtered_echem.parquet")
POLARITY = os.path.join(KHL, "polarity_redox.parquet")
OUT = os.path.join(HERE, "electron_transfer_split.csv")

MEDIATOR = {
    "2564-83-2":  "TEMPO",
    "14691-89-5": "4-AcNH-TEMPO (ACT)",
    "2226-96-2":  "4-HO-TEMPO",
    "2896-70-0":  "4-oxo-TEMPO",
    "524-38-9":   "NHPI",
    "84-58-2":    "DDQ",
    "106-51-4":   "1,4-benzoquinone",
    "123-31-9":   "hydroquinone",
    "130-15-4":   "1,4-naphthoquinone",
    "102-54-5":   "ferrocene",
    "4316-58-9":  "tris(4-bromophenyl)amine",
    "603-34-9":   "triphenylamine",
    "7632-00-0":  "NaNO2 (NOx)",
    "591-50-4":   "iodobenzene (ArI/HVI)",
    "696-62-8":   "4-iodoanisole (ArI/HVI)",
}
HALIDE = {
    "7647-15-6": "NaBr", "7758-02-3": "KBr", "7550-35-8": "LiBr", "12124-97-9": "NH4Br",
    "7681-82-5": "NaI",  "7681-11-0": "KI",  "12027-06-4": "NH4I",
    "7647-14-5": "NaCl", "7447-40-7": "KCl", "7447-41-8": "LiCl", "12125-02-9": "NH4Cl",
    "7553-56-2": "I2",   "7726-95-6": "Br2",
    "540-72-7":  "NaSCN", "333-20-0": "KSCN", "1762-95-4": "NH4SCN",
}
R4NX_ELECTROLYTE = {  # counted as electrolyte, never mediator
    "1643-19-2": "Bu4NBr", "311-28-4": "Bu4NI", "1112-67-0": "Bu4NCl",
    "71-91-0": "Et4NBr", "68-05-3": "Et4NI",
}
CATALYST = {
    "7718-54-9": "NiCl2", "13462-88-9": "NiBr2", "3264-82-2": "Ni(acac)2",
    "29046-78-4": "NiCl2·glyme", "7791-20-0": "NiCl2·6H2O",
    "7646-79-9": "CoCl2", "71-48-7": "Co(OAc)2",
    "7773-01-5": "MnCl2", "638-38-0": "Mn(OAc)2",
    "7681-65-4": "CuI", "7787-70-4": "CuBr", "7758-89-6": "CuCl",
    "142-71-2": "Cu(OAc)2", "13395-16-9": "Cu(acac)2",
    "7705-08-0": "FeCl3", "7758-94-3": "FeCl2", "14024-18-1": "Fe(acac)3",
    "3375-31-3": "Pd(OAc)2", "7647-10-1": "PdCl2",
    "10049-07-7": "RhCl3", "12354-85-8": "[Cp*RhCl2]2",
    "366-18-7": "2,2'-bipyridine (ligand)", "66-71-7": "1,10-phenanthroline (ligand)",
    "1148-79-4": "terpyridine (ligand)",
}


def classify_records(corpus=CORPUS):
    u = pd.read_parquet(corpus, columns=["rxn_id", "reagents", "catalysts"])
    rg = (u.reagents.fillna("") + ";" + u.catalysts.fillna("")).str.strip(";")
    has_data = rg.str.len() > 2

    def hit(dic):
        s = pd.Series(False, index=u.index)
        counts = {}
        for cas, name in dic.items():
            h = rg.str.contains(cas, regex=False)
            counts[name] = int(h.sum())
            s |= h
        return s, counts

    cat, cat_counts = hit(CATALYST)
    med, med_counts = hit(MEDIATOR)
    hal, hal_counts = hit(HALIDE)
    r4n, _ = hit(R4NX_ELECTROLYTE)

    bin_ = pd.Series("no_data", index=u.index)
    bin_[has_data] = "direct"
    bin_[has_data & hal] = "halide"
    bin_[has_data & med] = "mediator"
    bin_[has_data & cat] = "catalyst"
    out = pd.DataFrame({"rxn_id": u.rxn_id, "et_bin": bin_, "r4nx_present": r4n})
    return out, cat_counts, med_counts, hal_counts


def build(corpus=CORPUS, polarity=POLARITY, out=OUT):
    df, cc, mc, hc = classify_records(corpus)
    n_corpus = len(df)

    pol = pd.read_parquet(polarity, columns=["rxn_id", "site_label"])
    df = df.merge(pol, on="rxn_id", how="left")
    df["et_bin_raw"] = df.et_bin

    # polarity gate: every shuttle in the dictionary is an ANODIC mediator (nitroxyls,
    # NHPI, quinones, amines, NOx, ArI, halides). In a net-cathodic record these are
    # additives / electrolytes / proton sources, not the current carrier -> direct.
    # Catalysts are not gated.
    gate = df.et_bin.isin(["mediator", "halide"]) & (df.site_label == "Reductive")
    df.loc[gate, "et_bin"] = "direct"

    n_unscored = df.site_label.isna().sum()
    ungated = df.et_bin.isin(["mediator", "halide"]) & df.site_label.isna()
    print("corpus %d records; %d have no polarity call (%.1f%%), of which %d sit in a "
          "gateable bin and keep their raw label"
          % (n_corpus, n_unscored, 100 * n_unscored / n_corpus, ungated.sum()))
    print("polarity gate reclassified %d mediator/halide records -> direct" % gate.sum())

    df.to_csv(out, index=False)
    print("\n=== corpus electron-transfer bins ===")
    print(df.et_bin.value_counts().to_string())
    n = (df.et_bin != "no_data").sum()
    print("\nof records with reagent data (n=%d):" % n)
    for b in ["direct", "catalyst", "mediator", "halide"]:
        v = (df.et_bin == b).sum()
        print("  %-9s %6d  %.1f%%" % (b, v, 100 * v / n))
    print("\ntop mediator hits:", sorted(mc.items(), key=lambda x: -x[1])[:6])
    print("top halide hits:  ", sorted(hc.items(), key=lambda x: -x[1])[:6])
    print("top catalyst hits:", sorted(cc.items(), key=lambda x: -x[1])[:6])
    print("\nsaved -> %s" % out)
    return df


if __name__ == "__main__":
    build()
