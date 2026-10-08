# Revision notes — Jonas Rein, 2026-10-05

## Raised, and resolved in the data this session

**Ref 25 (condensed SI) = Gnaim et al., Nature 2022, 605, 687 is not a hydroamination.** Confirmed
from the paper: "hydroamination" occurs in it exactly ONCE, inside its own reference 13 (Gui et al.,
someone else's work); "Markovnikov" and "MHAT" occur zero times. Its three condition sets are

  A  CoBr2(glyme)/4,4'-MeO-bpy, MeCN, Zn/Sn, 2.5 mA        monosubstituted alkene ISOMERIZATION
  B  Co(salen)-1/HFIP, acetone, Zn/Ni, 5 mA                disubstituted isomerization, cycloisomerization
  C  CoBr2glyme/6,6'-Me-bpy, HFIP 9 equiv, THF, Mg/C       Z-selective alkyne reduction and
                                                           monosubstituted alkene REDUCTION

Row 11's own conditions (THF, HFIP 9 equiv, Mg/C, 0.2 mmol/2.5 mL) are unambiguously **conditions C**,
so Jonas is right on both counts: the conditions are correct and the name was not.
  * `reaction` "Co-H Markovnikov hydroamination (e-HAT)" -> "Co-H alkene reduction (e-HAT)"
  * `cls` "C-N formation" -> "Reduction". A reduction forms no C-N bond; the KHL justification even
    read "new C-N bond", which was wrong. **Jonas did not flag this; the class error was underneath
    the name error.**

**No computed number moves.** `cls` and `reaction` are carried as labels only -- `run_tier0.jl` and
`run_section4.jl` do `row = Any[rx.cls, rx.name, rx.carrier]` -- so no ceiling, median or threshold
count changes. The one published claim that moves is the SI S4.2 class stratification: the largest
gap shifts from Cyclization -6.3 to Reduction +6.5 points, and the published "within seven points"
**still holds**.

**His faradaic-efficiency concern lands on a different row than he thought.** Conditions A and B run
at 0.5-3 F/mol (catalytic isomerization, so FE is not well defined and can read >>100%); conditions C
runs at 3-5 F/mol and is a genuine 2-electron reduction. Row 11 is conditions C, so it is the *best*
of the three for this model. The row where the concern actually bites is **row 41**, the conditions-B
isomerization -- and that row already carries `n_substrate = 0.2`, i.e. the sub-stoichiometric charge
is already encoded. Worth saying explicitly in the SI rather than leaving implicit.

## Found by the audit this prompted, not raised by Jonas

**Row 40 was also misnamed.** "Anodic decarboxylative elimination" cites Walecka-Kurczyk, RSC Adv.
2022, whose title is *"Non-Kolbe electrolysis of N-protected-a-amino acids: a standardized method for
the synthesis of N-protected (1-methoxyalkyl)amines"* and whose abstract says "decarboxylative
a-methoxylation". "elimination", "alkene" and "olefin" occur **zero** times; "methoxy" occurs 47
times. The row's own inputs corroborate the correction: solvent MeOH (the nucleophile) at 2.1 F/mol,
n = 2. Renamed to "Non-Kolbe decarboxylative alpha-methoxylation"; no number moves.
  * OPEN: its `cls` is "Functional group intraconversion". Under KHL's own rule (a methanol whose O
    is tracked into the product stays a reactant -> C-O formation) this is arguably C-O formation.
    Not changed, because it would move the stratification a second time and the row-by-row KHL
    assignment was made against classify.py's code paths; it needs the same treatment.

## Deferred to the next revision, at his request

**Section 7.4 — give credit where it is due.** Where these sections propose diagnostic and
stability-measurement practice, say not only that the methods are standard in the energy space but
that they have already been implemented in electrosynthesis, and cite good published examples of each
failure mode being measured, diagnosed and reported. He can name several. This is a citation and
credit question, not a correction.

## Still to do from his note

* He redrew the Figure 6 structures; `Figures/Reaction equations.cdxml` (2026-10-05) is his file and
  has not yet been merged into `figs/make_fig6_schemes_cdxml.py`.
* SI reference formatting: the condensed SI's Kelly 2026 entry prints "2026, DOI: 10.1021/..." with
  no volume or pages, where every other entry carries them.

---

## Implemented, 2026-10-05 (author: "let's just go ahead and implement all of Jonas' changes")

### (1) The redrawn structures are in the figure

Jonas's `Reaction equations.cdxml` is installed as `Figures/Fig6_schemes_JR_20261005.cdxml` and read at
build time by `figs/make_fig6_schemes_cdxml.py`. **His document style is identical to ours** — measured,
not assumed: BondLength 14.40, LineWidth 1.13, BoldWidth 2.27, HashSpacing 2.49, Arial 9.9 pt labels,
and his 56 bonds have a median length of 14.40 — so his drawings need translation only, never scaling,
and the generator refuses to run if that ever stops being true.

He redrew **five** of the six: Hofmann (amide → methyl carbamate), Ni-XEC (Ar–Br + Alkyl–Br → Ar–Alkyl),
ACT (primary alcohol → acid), aza-Wacker (N-tethered alkene closes, X = NH, O, CH₂) and NHPI
(cyclohexene → cyclohex-2-enone). The sixth, the cobalt row, he did not redraw — he flagged it as the
wrong reaction instead, which is item (3).

Each group is located by **signature** — its fragment count plus the multiset of its atom labels — never
by position in his file, so re-saving his document in ChemDraw cannot silently swap two schemes. Each
signature must match exactly one group or the build stops.

He generalised the NHPI scheme: the exemplar is valencene → nootkatone, and a sesquiterpene skeleton is
unreadable at the size that scheme is placed. The manuscript caption names the transformation, not the
substrate, so it still describes the drawing.

**A latent layout defect came out of it.** The bands had a fixed 82 pt pitch, which worked only because
every scheme happened to be shorter than that. His aza-Wacker drawing is 83.2 pt tall, and each band is
cropped with a ±20 pt margin before being trimmed to its own ink, so the tightest gap was 42.8 pt against
the 40 pt two neighbouring crops consume — 2.8 pt of slack, and a band could have pulled its neighbour's
ink into its crop. `build()` now lays the bands out from their own measured heights with a declared
clearance, asserts every gap exceeds what the crops consume, and asserts the page still fits ChemDraw's
legal-landscape sheet (545 pt of 576). Past that sheet ChemDraw refuses the document outright.

### (2) SI reference 13 — already fixed, and this is what it was

The condensed SI he read printed

    13  M. Kelly, L. Cardinale, ... and M. Schreier, Org. Process Res. Dev., 2026, DOI: 10.1021/acs.oprd.6c00110.

— a DOI where all 80-odd other entries print volume and pages, because the Zotero record had no volume
when the entry was written. It now reads `2026, 30, 1926–1936`. Nothing else in the list uses that form.

(The seven `et al.` entries are not a defect: all seven are many-author papers — Kawamata, Gnaim, Peters,
Leow, Bottecchia, Zhang, Górski — which is ordinary RSC practice.)

### (3) The cobalt row: the name, the class, the scheme, the prose

Settled from the paper, not from recognition. Gnaim et al. Nature 2022 captions Fig. 3 **"Scope of e-HAT
reduction"** (p. 689) and writes "the selective reduction of monosubstituted alkenes was similarly
achieved by relying on e-HAT (conditions C)" (p. 690). Conditions C is printed in full on the figure:
CoBr₂·glyme (10 mol%) / 6,6′-Me-bpy (15 mol%) / HFIP (9 equiv.) / Et₃NHBF₄ (3 equiv.) / THF (2.5 ml) /
Mg(+)C(−), 5 mA, 3–5 F mol⁻¹ — which is this row's own recorded condition set. **"Hydroamination" occurs
in that paper exactly once, in its own reference 13** (Gui et al., olefin hydroamination with
nitroarenes): a cited title, not its chemistry.

Carried through:

| where | was | is |
|---|---|---|
| `data/reactions_50.csv`, `reactions_50_khl_class.csv` | Co-H Markovnikov hydroamination (e-HAT), C-N formation | Co-H alkene reduction (e-HAT), Reduction |
| `data/build_reactions50.py` | `("C-N formation", ...)` | `("Reduction", ...)` |
| `julia/reactions_table.jl`, `julia/tier0_matrix.csv`, `julia/tier0_ec_matrix.csv` | regenerated | regenerated |
| `figs/make_fig6_schemes_cdxml.py` `sch_coh` | R–CH=CH₂ + HNR₂ → R–CH(NR₂)–CH₃ | R–CH=CH₂ → R–CH₂–CH₃ |
| `data/ms_phrases.py` (Fig 6h caption, §4 body) | cobalt-hydride Markovnikov hydroamination / hydroamination | cobalt-hydride alkene reduction |
| `make_si.js`, `data/build_param_tables.py` | "(hydroamination, isomerization)" | "(alkene reduction, isomerization)" |
| the manuscript | both phrases | both phrases, as tracked changes |

**The class fix had to reach the generator, and G-REGEN is what caught that it had not.** The class was
corrected in `reactions_50.csv` and not in `build_reactions50.py`, so regenerating would have reverted it.
The control on the propagation is that **every architecture value in `tier0_matrix.csv` and
`tier0_ec_matrix.csv` is unchanged and exactly one cell moved in each — the class string.** No ceiling,
median or threshold count moves, because `cls` and `reaction` are carried as labels.

The published SI claim that does move is the §S4.2 class stratification: the largest class gap is now
**Reduction, 10.4 % of the set against 3.9 % of the corpus, +6.5 points**, and the published "within
seven points" still holds. Those eleven pairs are now computed from `results/khl_stratification.json`
rather than typed.

### A second mislabel, found by the gate written for the first

`data/check_reaction_names.py` (G-NAMES) requires each row's transformation words to appear in its own
exemplar's text, **with the reference list cut off**, because a cited title carries other people's
chemistry. Row 49 read **"Anodic C-H phosphonylation of azoles"**. Long, Huang, … & H.-C. Xu,
*Nat. Commun.* 2021 is titled *"Electrochemical C–H phosphorylation of arenes in continuous flow"*, and:

* its own word is **phosphorylation** (title, abstract and body); "phosphonylation" appears three times
  and all three are in cited titles — Niu, Shaikh and Yuan — the identical shape as the Gnaim error;
* its substrate is **arenes**, not azoles. "Azole" appears five times: once in the sentence saying that
  *previous* radical methods "are generally limited to electron-rich arenes or azoles", and four times in
  reference titles. The row's own data had it right all along — `conc_provenance` reads "arene 0.05 M
  limiting" and `carrier_species` reads "triethyl phosphite (arene-limited basis)".

Corrected to **"Anodic C-H phosphorylation of arenes"**. `cls` stays "Other bond formation" (a C–P bond).

### The other nine flags, read and kept

Each was checked against its own paper and is a synonym or a tokenisation artifact, not a mislabel:

| row | name | why the term is not in the paper |
|---|---|---|
| 4 | Oxidative benzimidazole annulation | the paper says "dehydrogenative **cyclization**" of amidines; annulation is the same ring-forming step |
| 7 | Arene C-H pyridination | the paper is titled "Electrochemical C−H **Amination** … via N-Arylpyridinium Ions", but the row models the ANODIC step alone — anisole + pyridine in a divided cell, 2 e⁻ — whose product is the pyridinium ion. The amine is added afterwards and is never in the cell, so "pyridination" is the more accurate name for what is solved |
| 16 | Decarboxylative Minisci alkylation | "Minisci" ×4 and "alkyl radical" ×7; a Minisci reaction is an alkylation |
| 20 | Cathodic Ni aryl-aryl homocoupling | "biaryl" ×12, "coupling" ×12 |
| 30 | Anodic methoxylation of 4-tBu-toluene | the patent says "methoxy" and "acetal" (the product is the dimethyl acetal) |
| 31 | Shono alpha-methoxylation | "methoxylation" ×1, "methoxy" ×33 — the hyphenated compound is not a literal string |
| 32 | Cl-mediated ethylene epoxidation | "ethylene oxide" ×40, "chlorohydrin" ×9 |
| 35 | NHPI-mediated allylic C-H → enone | "NHPI" ×28, "allylic" ×32, "enone" ×28 — the hyphenated compound is the miss |
| 38 | Radical-cation Diels-Alder | "radical cation" ×24, unhyphenated |
| 40 | Non-Kolbe decarboxylative alpha-methoxylation | "Non-Kolbe" ×5, "methoxylation" ×13 |

These are recorded in the gate itself, so it reports a verdict instead of a list to re-read.

### Code availability

The manuscript's Data availability paragraph now carries the repository the model was published to:
<https://github.com/jcbui/organic-electrosynthesis-model>. It holds the solvers, the fifty-reaction set,
the provenance registry and every figure generator; the CAS-derived per-record dataset is withheld under
the data use agreement, which the paragraph already states and the repository's `EXCLUDED.md` repeats.

### Deferred by the author, for the next revision

Jonas, on §7.4: where the text proposes a method standard in the energy space, point out that it has
*also* been implemented in electrosynthesis and cite good examples there — "give credit where credit is
due". Not addressed this round, by his own instruction.

## Late night: the chemistry audit's second pass, and Figure 6h's third row

Implemented (author: "Go for it"): Wacker at the palladium-limited k = 0.06 M⁻¹ s⁻¹; both nickel aminations and the
Co(salen) allylic C–H amination (formerly "aza-Wacker") at k = 0; the NH₃ amination at n = 2; Kolbe neutral; the Giese
reduced species HO₂•; the triarylamine oxazole reclassified as a mediator. Medians 8.1 / 9.2 / 17.2 / 42.4 / 103 / 104 /
117 mA cm⁻²; clearing 25: 12/14/19/29/34/34/34; clearing 50: 9/11/13/23/32/32/32.

Figure 6h then drew the allylic amination as a straight k = 0 line. No measured constant exists for it or for the Ni(tet a)
cyclization (Ozaki 1993 and Olivero 1998 read in full), so the third row is the **Ni aryl–aryl homocoupling** at the nickel
constant: the only catalyst row to clear 25 mA cm⁻², substrate-limited in the batch cells, kinetic ceiling 83 mA cm⁻².
Section 4, the Figure 6 caption and SI §S5.7 say so; the manuscript embeds an interim Figure 6 until (h) is re-placed.

**Draft reply to Jonas** (for the author to adapt):

> Thanks again for the Co–H catch — it led to a full read of all fifty rows against their papers. Two rate constants came
> out wrong (NHPI and the bromination, now at measured values), the Wacker row is now limited by its palladium turnover,
> and the Co(salen) row turned out to be an allylic C–H amination with no measured rate constant, so it no longer appears
> in Figure 6h; the third catalyst there is now the Ni homocoupling. Your redrawn structures are in the figure as you drew
> them, plus one new scheme built from your Ni–XEC drawing. SI Tables S10 and S11 now give every balanced reaction and,
> for every rate constant, the system it was measured on.
