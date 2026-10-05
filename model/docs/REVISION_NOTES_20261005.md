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
