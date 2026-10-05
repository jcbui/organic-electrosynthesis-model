#!/usr/bin/env python3
"""G-SIFRESH -- is the shipped SI what make_si.js produces today?

    cd Section4_Model && python data/check_si_fresh.py
    cd Section4_Model && python data/check_si_fresh.py --negative-control

WHY
---
Three gates cover staleness and none covered this one. G-REGEN checks generated DATA artifacts
against their generators (build_reactions50.py, build_param_tables.py). G-FIGRUN runs the eight
figure generators and requires byte-identical output. verify_v*.py G1 checks that the artwork
embedded in the manuscript equals the on-disk render. **Nothing asked whether the built SI is
current**, and on 2026-08-31 it was not: the EC-prime viscosities were made derived, the RCE
median moved in its fourth significant figure, and S3.3 kept printing 126.3 where the model gives
126.2 because the SI had been rebuilt BEFORE the re-solve. Every other gate passed.

The same pass showed the failure is not one step deep. A derived-value change propagates
solve -> build_merged_matrix.py -> build_param_tables.py -> make_si.js, and rebuilding the SI
without the registry left G-REGEN failing on one line while rebuilding the registry without the
SI left S3.3 wrong. This gate closes the last link.

HOW, AND WHY IT REBUILDS IN PLACE
---------------------------------
make_si.js hardcodes its output path, and it reads fonts, figures, three CSVs and a dozen
results/*.json from the repo root, so the scratch-tree approach G-REGEN uses does not transplant.
The SI is snapshotted, rebuilt in place, and compared part-by-part. **docProps/core.xml is
excluded**: it carries the build timestamp, so two builds of identical content always differ there
and a whole-file hash reports a clean build as a change (CLAUDE.md records that trap).
If the content matches, the snapshot is restored so the file does not churn. If it differs, the
FRESH build is kept -- that is the correct artifact -- and the gate fails, naming the parts.
"""
import filecmp
import io
import json
import os
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SI = os.path.join(ROOT, "SI_Section4_Transport_Model.docx")
SNAP = os.path.join(ROOT, "results", "_si_snapshot.docx")
TIMESTAMP_PART = "docProps/core.xml"


def parts(path):
    z = zipfile.ZipFile(path)
    return {n: z.read(n) for n in z.namelist()}


def main(neg=False):
    if not os.path.exists(SI):
        print("G-SIFRESH: FAIL -- no built SI at %s" % SI)
        return 1
    shutil.copy2(SI, SNAP)
    before = parts(SNAP)
    if neg:
        # Perturb the SNAPSHOT, not the source: pretend the shipped SI had been built from an
        # older state. Nothing in the repo is modified, and the rebuild below must detect it.
        before = dict(before)
        ## THE PERTURBATION STRING MUST STILL BE IN THE DOCUMENT. This control used to swap
        ## 126.2 -> 126.3, the exact staleness that shipped in 2026-08-31. That number left the
        ## SI when S3.3's sensitivity was rebuilt on a second fitted correlation, so the swap
        ## became a no-op and the control reported itself INERT -- correctly, and that is the
        ## only reason it was noticed. A control pinned to a literal the document may stop
        ## carrying is trap 10 aimed at the control instead of the gate, so assert the string is
        ## present rather than trusting it.
        _probe, _alt = b"228", b"229"
        if _probe not in before["word/document.xml"]:
            print("G-SIFRESH control: BAD -- the probe string %r is no longer in the SI; "
                  "repoint it at a value the document actually carries" % _probe.decode())
            shutil.copy2(SNAP, SI)
            os.remove(SNAP)
            return 1
        before["word/document.xml"] = before["word/document.xml"].replace(_probe, _alt, 1)

    r = subprocess.run(["node", os.path.join(ROOT, "make_si.js")],
                       cwd=os.path.join(ROOT, "data"), capture_output=True, text=True)
    if r.returncode != 0:
        print("G-SIFRESH: FAIL -- make_si.js did not run:\n%s" % r.stderr.strip()[-400:])
        shutil.copy2(SNAP, SI)
        return 1
    after = parts(SI)

    diff = sorted(n for n in set(before) | set(after)
                  if n != TIMESTAMP_PART and before.get(n) != after.get(n))
    print("  parts compared: %d (%s excluded: it carries the build timestamp)"
          % (len(set(before) | set(after)) - 1, TIMESTAMP_PART))
    for n in diff:
        b, a = before.get(n), after.get(n)
        print("    DIFFERS  %-28s %s -> %s bytes"
              % (n, "absent" if b is None else len(b), "absent" if a is None else len(a)))

    json.dump({"differing_parts": diff, "n_parts": len(after)},
              io.open(os.path.join(ROOT, "results", "si_fresh%s.json"
                                   % ("_NEGCONTROL" if neg else "")), "w", encoding="utf8"),
              indent=1)

    if neg:
        shutil.copy2(SNAP, SI)          # leave the real artifact exactly as found
        os.remove(SNAP)
        ok = "word/document.xml" in diff
        print("\nNEGATIVE CONTROL: the SNAPSHOT was altered (228 -> 229, the derived unstirred film) "
              "that shipped), so the rebuild must differ from it.")
        print("G-SIFRESH control: %s" % ("GOOD (the stale body was detected)" if ok
                                         else "BAD -- test is inert"))
        return 0 if ok else 1

    if diff:
        os.remove(SNAP)                 # keep the FRESH build; it is the correct artifact
        print("\nG-SIFRESH: FAIL -- the shipped SI was NOT what make_si.js produces. It has been "
              "rebuilt; re-run the gates and re-check anything that quotes the SI.")
        return 1
    shutil.copy2(SNAP, SI)              # identical content: restore to avoid needless churn
    os.remove(SNAP)
    print("\nG-SIFRESH: PASS -- the shipped SI is byte-identical to a fresh build in every part "
          "but its timestamp")
    return 0


if __name__ == "__main__":
    sys.exit(main(neg="--negative-control" in sys.argv))
