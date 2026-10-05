#!/usr/bin/env python3
"""G-VOICE -- the shipped documents must carry no trace of the editing or auditing process.

CLAUDE.md makes this a standing requirement, and a one-off sweep on 2026-08-25 took the SI
from 152 process phrases to 2. Nothing has enforced it since, so the requirement decayed the
only way an ungated one can: the stirred-film row's sensitivity was written as edit history
("Adopting it moved the stirred >=25 count 17 -> 14 of 50 ... the stirred median 17.1 -> 9.1"),
shipped verbatim into Table S7, and passed every one of the 87 registered gates -- including
G-SIPROSE, which reads SI numbers, because each of those numbers was individually true.

The failure mode is not a wrong number. It is a number narrated as a CHANGE to a previous draft,
which tells a referee that a draft existed and says nothing about the physics.

What this gate does NOT do: forbid transitions. A sensitivity legitimately states one -- the
kappa(T) bracket moves the MeCN microfluidic ceiling 438 -> 560, and that is physics. It targets
the VOCABULARY of editing instead: words that can only refer to the document's own history.

Every exemption is verbatim and reasoned; a bare suppression is never used (see the standard).
"""
import io, os, re, sys, unicodedata

SEC4 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SEC4, "data"))
from docx_text import asserted_text  # noqa: E402
from latest_ms import latest_ms

## Vocabulary that can only be about this document's own history. Each entry is a regex over
## the normalised text; the comment says what shape of defect it catches.
PROCESS = [
    (r"adopting it moved",            "narrates the effect of an edit rather than a sensitivity"),
    ## 2026-09-05: the unstirred-film row shipped "Adopting 228 um in place of the retired 300 um
    ## raises the unstirred median from 6.11 to 8.01" into Table S7 behind a green G-VOICE -- the
    ## same class as "adopting it moved", in different words. A sensitivity states what the value
    ## does across its band; it never names the value it replaced as "retired".
    (r"in place of the retired",       "narrates a replacement rather than a sensitivity"),
    (r"\bthe retired \d",              "cites a superseded value of itself as retired"),
    (r"\breplacing a declared\b",      "narrates a replacement"),
    (r"(this row|it) previously (carried|read|said)", "cites a superseded value of itself"),
    (r"earlier (versions?|drafts?) of this", "cites a superseded draft"),
    (r"\bthe inherited\b",            "cites where the text came from"),
    (r"defect (found|fixed)",         "audit finding left in shipped prose"),
    (r"needs? re-?verification",      "audit to-do left in shipped prose"),
    (r"previously unregistered",      "registry bookkeeping"),
    (r"\bstale\b",                    "audit vocabulary"),
    (r"negative[- ]control",          "gate vocabulary"),
    (r"\bthe gate\b|\bgated by\b|\bgate (fires|passes|fails)", "gate vocabulary"),
    (r"\bCLAUDE\.md\b|apply_v\d+|verify_v\d+", "internal file reference"),
    ## AUTHOR INSTRUCTION 2026-09-01: the verification apparatus is internal work product and
    ## must not appear in a public-facing document. Gate identifiers and repository paths were
    ## removed from both documents; these patterns keep them out. (G-GHOST enforces the paths
    ## too, from the cross-reference side; this is the voice side of the same rule.)
    (r"\bG-[A-Z][A-Z-]+\b|\bgates? G\d{1,2}[ab]?\b|\(G\d{1,2}[ab]?\)", "gate identifier"),
    (r"\baudit(ed|s|ing)?\b", "verification-apparatus vocabulary"),
    (r"\b(?:data|figs|julia|results|docs|scripts)/[A-Za-z0-9_./-]+", "repository path"),
    (r"\b[A-Za-z0-9_]+\.(?:py|jl|js|csv|json)\b", "source or artifact filename"),
    (r"\bre-?run (the|this)\b",       "instruction to the author, not to the reader"),
    (r"\bwe corrected\b|\bwas wrong\b|\bhad drifted\b", "narrates a correction"),
    (r"\bin an earlier pass\b|\bon (a|the) (first|second|third) pass\b", "narrates a pass"),
    (r"\bTHAT PARAGRAPH IS HISTORY\b", "editing marker"),
]

## Verbatim exemptions. Each states WHY the phrase is legitimate where it stands, and each is
## matched as a literal substring so it cannot broaden.
EXEMPT = [
    ("withdraws more rejecting surface",
     "physical: sigma ~ 0.8 withdraws surface, not a claim being withdrawn"),
    ("softened or withdrawn",
     "the four-state rule's own text: a conclusion is softened or withdrawn, never the provenance faked"),
    ("a declared omission rather than a conservative one",
     "declares a modelling omission, not an edit"),
    ("gated by photon absorption",
     "physical: the excited-state population is limited by photon flux, not by any check of ours"),
]


def scan(label, path):
    raw = asserted_text(path)
    txt = unicodedata.normalize("NFKC", re.sub(r"\s+", " ", raw))
    low = txt.lower()
    hits = []
    for pat, why in PROCESS:
        for m in re.finditer(pat, low, re.I):
            ctx = txt[max(0, m.start() - 90):m.end() + 90]
            if any(e.lower() in ctx.lower() for e, _ in EXEMPT):
                continue
            hits.append((label, txt[m.start():m.end()], why, ctx))
    return txt, hits


def main():
    control = "--negative-control" in sys.argv
    docs = [("SI", os.path.join(SEC4, "SI_Section4_Transport_Model.docx"))]
    msd = os.path.join(SEC4, os.pardir, "MS Drafts")
    # shared resolver -- the pattern here was pinned to a retired naming scheme (2026-09-29)
    _ms = latest_ms()
    docs.append(("MS " + os.path.basename(_ms).replace(".docx", ""), _ms))

    all_hits, total = [], 0
    for label, path in docs:
        txt, hits = scan(label, path)
        total += len(txt)
        all_hits += hits
        print("  %-10s %7d chars   %d process phrase(s)" % (label, len(txt), len(hits)))

    if control:
        ## Perturb the CLAIM, not the checker: feed a sentence written the way the real defect
        ## was written and require it to be caught. A control that edits the pattern list would
        ## only prove the list can be edited.
        fake = ("The measurement is a proxy. Adopting it moved the stirred count 17 -> 14 of 50, "
                "and this row previously carried 100 um.")
        low = fake.lower()
        caught = [why for pat, why in PROCESS if re.search(pat, low, re.I)]
        ## the second control is the sentence that shipped on 2026-09-05 behind a green gate
        fake2 = ("Adopting 228 um in place of the retired 300 um raises the unstirred median "
                 "from 6.11 to 8.01 mA cm-2 and moves no count.")
        caught2 = [why for pat, why in PROCESS if re.search(pat, fake2.lower(), re.I)]
        print("  second control sentence caught by %d pattern(s): %s" % (len(caught2), "; ".join(caught2)))
        ok = len(caught) >= 2 and len(caught2) >= 1
        print("\n  control sentence caught by %d pattern(s): %s" % (len(caught), "; ".join(caught)))
        print("G-VOICE control: %s" % ("GOOD (a process narrative is detected)" if ok
                                       else "BAD (the narrative was not detected)"))
        return 0 if ok else 1

    for label, phrase, why, ctx in all_hits:
        print("\n  %s: %r -- %s\n     ...%s..." % (label, phrase, why, ctx))

    if all_hits:
        print("\nG-VOICE: FAIL -- %d process phrase(s) in shipped text" % len(all_hits))
        return 1
    print("\n  %d exemption(s), each verbatim and reasoned" % len(EXEMPT))
    print("G-VOICE: PASS -- neither document narrates its own editing or auditing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
