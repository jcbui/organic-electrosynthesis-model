# Citation audit — every cited work in the manuscript and the SI (2026-09-13)

Author instruction: "run an audit on both SI and MS for appropriateness of references and rigor
there", escalated to "every single cited work needs to be checked", confirmed as "both".

Internal work product. Nothing here ships in either document.

## Scope and method

| | manuscript (v97) | SI (current build) |
|---|---|---|
| citation fields / sites | 104 | 121 |
| distinct works | 123 | 87 |
| with a DOI | 122 (Newman's book has none) | 0 — the SI prints locators, not DOIs |
| full text readable | 83 of 122 | via G-COND for every Table S2 row |

Three layers were run, not one:

1. **Resolution** — does the locator name a real record carrying the first author claimed?
   MS: all 122 DOIs resolve, 0 author mismatches, 0 title disagreements, 0 year gaps >= 2.
   SI: **G-SIBIB PASS** — 76 journal entries resolve with the first author matching, 11
   non-journal (books, patents) retrieved and recorded.
2. **Numeric** — is the value the sentence states actually present in the work it cites?
3. **Appropriateness** — does the work support the particular claim it is attached to?
   All 104 MS fields and all 121 SI sites were read one by one against the work's title and,
   where readable, its text.

### Two method corrections, both of which had produced a false finding first

**(i) A marker attaches to the END of its clause, not to its sentence.** The manuscript writes
`...confined below 20 mA cm-2.54`, so a sentence-scoped window binds the value to the marker that
OPENS the sentence — which belongs to the previous clause. Under that wrong rule the Deberghes
65% / 100 mA cm-2 appeared misattributed to ref 53 (Deberghes 2023). Read from the raw run order,
the clause ends with ref 54 = Deberghes **2024**, "Chlorine-Mediated Electrooxidation of
Cyclohexene at High Current Density", which prints verbatim "at 100 mA/cm2, the reactor maintains
a Faradaic efficiency of ~65%" and "limited to steady state operation below 20 mA/cm2".
**The document is correct; my attribution rule was not.** The probe now binds a value to the NEXT
marker after it. *This is trap 25 in a new coat: proximity is not evidence.*

**(ii) `<w:t[^>]*>` also matches `<w:tbl>`.** Trap 13, one element along from the recorded
`<w:tab/>` case. It swallowed raw XML into the flattened text and manufactured three "unmatched"
values out of style attributes. The boundary is `<w:t(?:\s[^>]*)?>` now, and the flattener asserts
no `<w:` survives in its output.

A third false alarm, retired before it was written up: **the SI's citation marker has two forms**,
`«key»` (superscript) and `⟦key⟧` (table cells). A regex reading only the first found 56 of 121
sites and reported **39 SI references as uncited**. Counting both forms, and logging every site
from the builder itself rather than from the source, gives **87 of 87 entries cited, 0 uncited,
0 cited-but-unlisted**.

## Numeric layer — result

MS: 34 numeric claims bind to a citation field; 33 have at least one readable cited work;
**0 genuine mismatches**. Three apparent misses were artifacts: `~10³ h` and `10⁴ h` are literal
superscripts that NFKC folds to "103"/"104", and "10-100 g" is the readiness table's own stage
range, not a claim about Rafiee.

Spot-verified against the papers' own text, all present: 200 °C, 1 A cm-2, 97%, 99%, 80%
(epoxidation group); 100 mA cm-2, 20 wt%, 30 wt% (H2O2 group); 1.6 V, 0.4 V (Wang); 2.2%, 98%,
89%, 92% (Rein); 92% (Cardinale); 73% (Zhang).
**98.1% is Zhou 2025's** ("97.8% and 98.1% selectivity, respectively") and **5,735 is Chen 2023's**
("turnover number for hydrazine formation of 5,735 within 24 h"); the field carrying that clause
cites both. Ferretti's counts all check: "None of the surveyed companies reported having
commercialized electrochemical processes", 14/15, 11/15, 6/15, 5/15.

SI: the Table S2 numeric layer is gated by **G-COND, re-run 2026-09-13: PASS**, 50 rows,
33 ANCHORED / 17 HAND-VERIFIED / 0 SI-ONLY / 0 MIXED-EXPERIMENT / 0 unusable.

## Findings

### M1 — the readiness table calls Ferretti's respondents "fine-chemical companies"; they are pharmaceutical, and the body says so

The manuscript states the same survey two ways:
- body: "among 17 **pharmaceutical** companies surveyed, none reported a commercialized
  electrochemical process"
- readiness table: "current frontier: 0 of 17 **fine-chemical** companies surveyed"

Ferretti et al., *Org. Process Res. Dev.* 2025, **29**, 322–332 is "a comprehensive survey on the
adoption of electrochemistry among 17 major **pharmaceutical** companies"; the strings
"fine chemical" and "fine-chemical" appear in it **zero** times. An internal contradiction and a
mislabel of the cited population. Fix: one word in the table cell.

### S1 — Table S2's benzimidazole row cites the wrong Zhao paper

The row "Oxidative benzimidazole annulation (C-H/N-H)" carries reference key `zhao2017` =
Zhao, Hou, Liu, Zhou, Song & Xu, *Angew. Chem. Int. Ed.* 2017, **56**, 587–590, "Amidinyl Radical
Formation through Anodic N-H Bond Cleavage and Its Application in Aromatic C-H Bond
Functionalization" (10.1002/anie.201610715).

Every number in the row is read from a different paper — Zhao, Zhuang & Xu, *ChemSusChem* 2021,
**14**, 1692–1695, "Electrochemical Synthesis of Benzimidazoles via Dehydrogenative Cyclization of
Amidines" (10.1002/cssc.202100254): the standard conditions ('amidine (0.3 mmol), Et4NPF6
(0.3 mmol), THF/MeOH (5:1, 9 mL), reflux'), the derived 0.033 M, and the optimisation entry
(52% against 65%). `data/reactions_50.csv` names that paper in its own source column.

**The ChemSusChem paper is not in the SI reference list at all.** The cell prints its full locator
in running prose, so the source is findable — but the numbered citation resolves to a related
paper by the same group that does not contain the conditions. Same class as the Krempl
attribution and the mis-lettered Table S7g.

Fix: add the ChemSusChem 2021 entry and point the row at it. That renumbers the reference list,
so it needs the SI rebuilt and G-SIBIB, G-GHOST and G-SIFRESH re-run.

### S2 (minor) — one SI source is cited inline instead of in the reference list

The state-B conductivity floor of 0.206 mS cm-1 is attributed to "Lee et al., *Org. Process Res.
Dev.* 2022, **26**, 2674–2684" in running text. The locator is complete and the claim is sound
(the `peters2019` marker beside it is correctly cited for the 3.0 M composition, and the sentence
says outright that Peters does not give κ). But it is the only work the SI cites outside its own
numbered list, and the same paper IS a numbered reference in the manuscript.

### S3 (minor) — "the ETC industry survey"

`ETC` occurs once in the SI, beside Ferretti, and is never defined. The survey's own population is
pharmaceutical companies. The three numbers around it are correct: 17 surveyed, 14 reporting
scale-up current densities, 10 below 25 / three 25–50 / one above 50 mA cm-2.

### M2 (minor) — a three-mode sentence carrying one citation

"Electrodes are consumed or damaged outright as well, by anode thinning, by Pd dissolution at high
current density, or by graphite spallation under strongly reductive conditions.73" Ref 73 is Moon
2020, "Layer-engineered large-area exfoliation of graphene", which supports the third mode only.
Anode thinning is covered by the next sentence's Kelly zinc projection; **Pd dissolution is
uncited**.

## What came back clean

- Every one of the 87 SI references is cited; every one of the 123 MS references is cited.
- No fabricated locator, no chimera, in either document.
- The SI's Table S2 rows quote the exemplar's own words with page and table locators, and flag
  their own deviations ("the paper runs at reflux against this model's isothermal 25 C — a
  declared deviation"; "MeOH 10 equiv is a REAGENT, not solvent").
- The S5.7 kinetics table cites primary kinetics literature per constant with explicit measured
  brackets (Ting 3.4–56, Kawamata >= 10², Till < 10⁴, Boucher 7 x 10², Cai <= 4 x 10¹).
- Where a source does NOT contain something, the SI says so and cites it for that absence
  (Bard "contains no numerical δ for natural convection"; Lobaccaro's σ = 74.3 "is not adopted:
  one exemplar body is not the archetype").

## Gate status at close

G-SIBIB PASS (76 + 11), G-COND PASS (33/17/0/0/0), G-MSCITE PASS, G-GHOST PASS.
The three G-SIBIB entries that read "unresolved" on 2026-09-12 were **HTTP 429** from four
concurrent Crossref clients, not citation defects; run serially the gate is clean. *That gate
cannot distinguish a network failure from a fabricated reference — read its log, not its count.*

---

# Resolution (2026-09-14, author instruction: "fix everything then I'll do the Zotero refresh on V98")

| # | finding | status |
|---|---|---|
| M1 | readiness table called Ferretti's respondents "fine-chemical companies" | **fixed in v98** |
| M2 | three-mode electrode sentence carried one citation covering one mode | **fixed in v98** |
| S1 | benzimidazole row cited the wrong Zhao paper | **fixed, SI rebuilt** |
| S3 | undefined "ETC industry survey" | **fixed, SI rebuilt** |
| S2 | Lee 2022 cited inline rather than in the numbered list | **WITHDRAWN — not a defect** |

## S2 is withdrawn, and the reason is the finding worth keeping

Before converting Lee to a numbered reference I counted how many works the built SI names inline
with a full locator. **It is 56** — Das, Dorn, Gong, Krumgalz, Casteel & Amis, Churchill & Chu,
Amatore, Shinkle, Williams, Wilke & Chang, Prue & Sherrington, Pickett & Ong and 44 more. The
numbered list carries the works the ARGUMENT cites; a provenance note names its own source in
running text with author, journal, year, volume and page. Lee is one of 56, not an exception.

Converting Lee alone would have made it inconsistent with 55 others, and converting all 56 would
be a restructuring nobody asked for. **The "defect" was me reading a deliberate convention as an
omission because I met one instance of it before I had counted the rest.** *Count how many times
the thing you are about to fix already happens.*

## S1 — what was actually wrong, and what was not

`ROWKEYS[3]` mapped the benzimidazole row to `zhao2017`. Both Zhao papers are amidine
electrochemistry from the same group, which is why this survived: the 2017 Angew paper makes
**tetracyclic** benzimidazoles by cyclising an amidinyl radical onto an arene, while the row is the
2021 ChemSusChem dehydrogenative cyclisation of amidines, and every number in the row — 'amidine
(0.3 mmol), Et4NPF6 (0.3 mmol), THF/MeOH (5:1, 9 mL), reflux', the derived 0.033 M, the 52%/65%
optimisation entry — is the 2021 paper's. `data/reactions_50.csv` named the right paper in its own
source column the whole time; only the SI's key map was wrong.

Fixed by swapping the REFS entry **in place**, so reference 30 stays reference 30 and **nothing
renumbers**: 87 references before and after, first-appearance order OK, G-SIBIB PASS.
`zhao2017` is cited nowhere else and is gone from the list.

## M2 — the claim was sourced; it was attached to the wrong group

"...by anode thinning, by Pd dissolution at high current density, or by graphite spallation under
strongly reductive conditions.73" cited only Moon (graphene exfoliation), which covers the third
clause. The first two are supported by works **this manuscript already cites**, so nothing was
invented and no new library item was needed:

- **Leow et al., Science 2020**, verbatim: *"Operating at this high current density resulted in
  dissolution of the Pd anode, as can be observed from the rapidly increasing potential with
  time (fig. S2C)."* — at 300 mA cm⁻².
- **Kelly et al., Org. Process Res. Dev. 2026**: *"...is less than 2.5 mm per 50 kg batch ... This
  small change in anode thickness significantly reduces the risk of leaking from anode
  dissolution."*

Both are MERGED into the existing field, never placed beside it (two adjacent fields render as
run-on digits; one claim carries one group). The marker is now **3,18,73**, and those numbers are
DERIVED, not typed: the builder maps every field's rendered numbers positionally onto its own
citationItems across the whole document and reads Kelly = 3 and Leow = 18 back out of v97.

**The first draft of this fix was going to DELETE the palladium clause** under "if something isn't
defensible we throw it out", because no cited work appeared to support it. That would have removed
a true, sourced statement. What changed the outcome was checking the other members of the claim's
own neighbourhood before concluding it was unsourced — the same move the v82 hydrazine entry
already records. *Look for the source before removing the sentence.*

## One build note

The reject-all invariant failed by exactly 5 characters, and the honest fix was to make it exact
rather than relax it (the v80 precedent). A field RESULT is Zotero's output, not authored prose,
so the merged rendering survives a reject-all — and it survives **on the pre-v81 sentence**, since
v81 rewrote that sentence as a tracked change. The replay anchor is therefore "consumed.73", not
the live wording, and `verify_v98` asserts that anchor is unique before replaying it so the replay
cannot silently match nothing.
