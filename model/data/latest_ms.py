"""Resolve the LIVE manuscript, once, for every gate that reads it.

Six gates each carried their own copy of this, and on 2026-09-29 all six were found reading a
superseded document:

  * three globbed ``revised_outline_v*_RCE_Perspective_JCB_tracked.docx``, a naming scheme the
    lineage left behind on 2026-09-22 when the author renamed his working copy, so they had been
    gating ``revised_outline_v130`` (22 Sep) while the live draft was ``RCE_Perspective_JR25``;
  * two of those three sorted the candidates LEXICALLY, where ``v99`` sorts after ``v130``, so they
    were gating v99 -- a document nine versions further back still.

Both are the pinned-filename defect the retired docstring in ``check_ms_derived`` warned about,
recurring one level up: resolving the maximum vNN keeps a gate on the live draft only for as long as
the NAME holds. So this resolver does not encode a name at all as its primary rule. It takes the
NEWEST candidate by modification time, prints what it chose with the runners-up and their dates, and
-- the part that makes it falsifiable -- WARNS LOUDLY when some other manuscript-looking .docx in the
folder is newer than the one it picked. A future rename then announces itself on the first gate run
instead of being discovered a week and twenty-five builds later.

``MS_DOCX`` in the environment overrides everything, so a build can gate its own output directly.
"""
import os
import re
import sys
import time

_D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), os.pardir, "MS Drafts")
MS_DIR = os.path.normpath(_D)

# the lineages this project has used, newest naming first; each must capture a sequence number
LINEAGES = [
    (r"^RCE_Perspective_JR(\d+)_\d{8}\.docx$", "JR"),
    (r"^revised_outline_v(\d+)_RCE_Perspective_JCB_tracked\.docx$", "v"),
    # 2026-10-02: the author works in the SUBMISSION package copy, whose name carries a package index
    # rather than a version number -- and it lives one directory down, which os.listdir never saw.  So
    # the live draft was invisible to this resolver TWICE OVER: no lineage matched it and no scan
    # reached it, and every manuscript gate was reading a file a day behind him.  Trap 35, one
    # directory lower: a resolver can be stale in a way no assertion inside the gates will ever see.
    (r"^(0?1)_Manuscript_tracked(?:_[A-Z]{2,4})?\.docx$", "pkg"),   # _JCB etc: his own save-as
]
# working copies, frozen bases and deliverables are not the draft under test
EXCLUDE = re.compile(r"authorbase|_base|base_|snapshot|prerefresh|superseded|_accepted_|~\$", re.I)
# anything matching this is a manuscript for the purpose of the staleness warning
LOOKS_LIKE_MS = re.compile(r"^(?:RCE_Perspective|revised_outline|\d*_?Manuscript).*\.docx$", re.I)


def _walk():
    """every .docx under MS Drafts except the archive -- the author's live copy has twice now been
    one directory down from where a flat listdir looks."""
    for root, dirs, files in os.walk(MS_DIR):
        dirs[:] = [d for d in dirs if not d.startswith("_archive") and d != "scripts"]
        for f in files:
            if f.endswith(".docx"):
                yield root, f


def _cands():
    out = []
    for _root, f in _walk():
        if EXCLUDE.search(f):
            continue
        for pat, tag in LINEAGES:
            m = re.match(pat, f)
            if m:
                p = os.path.join(_root, f)
                out.append((os.path.getmtime(p), int(m.group(1)), tag, p))
                break
    return sorted(out, reverse=True)


def latest_ms(verbose=True):
    """The live manuscript's path. Honours MS_DOCX; otherwise newest by mtime, with a warning."""
    env = os.environ.get("MS_DOCX")
    if env:
        if not os.path.exists(env):
            raise SystemExit("MS_DOCX points at a file that does not exist: %s" % env)
        if verbose:
            print("manuscript under test: %s   (MS_DOCX override)" % os.path.basename(env))
        return env
    c = _cands()
    if not c:
        raise SystemExit("no manuscript in %s matching any known lineage: %s"
                         % (MS_DIR, [p for p, _ in LINEAGES]))
    mt, num, tag, best = c[0]
    if verbose:
        print("manuscript under test: %s   (%s, newest of %d candidates)"
              % (os.path.basename(best), time.strftime("%Y-%m-%d %H:%M", time.localtime(mt)), len(c)))
        for mt2, _, _, p2 in c[1:3]:
            print("   next newest:        %s   (%s)"
                  % (os.path.basename(p2), time.strftime("%Y-%m-%d %H:%M", time.localtime(mt2))))
    # the falsifiable part: something newer that this resolver cannot see is a rename it must report
    newer = [os.path.relpath(os.path.join(r, f), MS_DIR) for r, f in _walk()
             if LOOKS_LIKE_MS.match(f) and not EXCLUDE.search(f)
             and os.path.getmtime(os.path.join(r, f)) > mt + 1
             and os.path.join(r, f) not in [p for _, _, _, p in c]]
    if newer:
        sys.stderr.write(
            "\n*** LATEST-MS WARNING: %d manuscript-looking file(s) in MS Drafts are NEWER than the "
            "one being gated (%s).\n*** This is how a lineage rename or a move into a subfolder silently freezes every gate. "
            "Add its pattern to data/latest_ms.LINEAGES, or set MS_DOCX.\n***   %s\n\n"
            % (len(newer), os.path.basename(best), ", ".join(sorted(newer)[:6])))
    return best


if __name__ == "__main__":
    p = latest_ms()
    print("\nall candidates, newest first:")
    for mt, num, tag, q in _cands():
        print("   %s  %-6s %3d  %s" % (time.strftime("%Y-%m-%d %H:%M", time.localtime(mt)), tag, num,
                                       os.path.basename(q)))
