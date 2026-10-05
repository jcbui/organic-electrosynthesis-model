"""Open a CDXML in ChemDraw 23 and save it in other formats, touching nothing else ChemDraw has open.

ChemDraw is usually running with the author's own documents open, so every step here is scoped to the one
document this script opens:
  * the file is opened without waiting on the AppleEvent (a large file can outlast the default timeout);
  * the document is addressed by name (ChemDraw's document ids exceed AppleScript's integer range and come
    back as rounded reals); at the end only documents that were not open beforehand are closed;
  * a refusal is raised, not a guess, if a document of that name is already open;
  * the only dialog ever dismissed is ChemDraw's "The objects will not fit in the document" question (Cancel), which
    means the page setup is too small -- that is reported as a failure. Any other dialog is left untouched.

Usage:  python chemdraw_render.py in.cdxml out.pdf [out2.cdxml ...]   (format taken from each extension)
"""
import os
import subprocess
import sys
import time

APP = "ChemDraw 23.1.2"
TYPES = {".pdf": "PDF", ".cdxml": "ChemDraw XML", ".cdx": "ChemDraw"}   # CFBundleTypeName in ChemDraw's Info.plist


def osa(script, timeout=60):
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr).strip()


def open_names():
    return osa('tell application "%s" to get name of every document' % APP)[1]


def dialog_text():
    rc, out = osa('tell application "System Events" to tell process "ChemDraw"\n'
                  'set ws to (every window whose subrole is "AXDialog")\n'
                  'if (count of ws) is 0 then return ""\n'
                  'return value of static text 1 of (item 1 of ws)\nend tell')
    return out if rc == 0 else ""


def render(cdxml, outputs, wait=90):
    """Open `cdxml` and save it to each path in `outputs`; returns the documents open afterwards."""
    cdxml = os.path.abspath(cdxml)
    name = os.path.basename(cdxml)
    before = set(open_names().split(", "))
    if name in before:
        raise SystemExit("%s is already open in ChemDraw; refusing" % name)
    osa('ignoring application responses\ntell application "%s" to open (POSIX file "%s")\nend ignoring' % (APP, cdxml))
    t0, failed = time.time(), None
    while True:
        if time.time() - t0 > wait:
            raise SystemExit("ChemDraw did not open %s within %d s" % (name, wait))
        time.sleep(1.5)
        d = dialog_text()
        if d.startswith("The objects will not fit"):
            osa('tell application "System Events" to tell process "ChemDraw" to click button "Cancel" of '
                '(first window whose subrole is "AXDialog")')
            failed = "the page setup is too small for the drawing: " + d
            time.sleep(2)
        elif d:
            raise SystemExit("unexpected ChemDraw dialog, left untouched: %r" % d)
        if name in open_names():
            break
    ref = 'item 1 of (every document whose name is "%s")'
    cur = name
    try:
        # exports first (they do not rename the document), native formats last
        for path in sorted(outputs, key=lambda p: os.path.splitext(p)[1] != ".pdf"):
            kind = TYPES[os.path.splitext(path)[1].lower()]
            path = os.path.abspath(path)
            new = os.path.basename(path)
            if kind != "PDF" and new != cur and new in before:
                raise SystemExit("a document named %s is already open; refusing to save over its name" % new)
            if os.path.exists(path):
                os.remove(path)
            rc, out = osa('with timeout of 120 seconds\ntell application "%s" to save (%s) in '
                          '(POSIX file "%s") as "%s"\nend timeout' % (APP, ref % cur, path, kind), 150)
            if rc != 0 or not os.path.exists(path):
                raise SystemExit("saving %s as %s failed: %s" % (path, kind, out))
            if kind != "PDF" and new in open_names().split(", "):
                cur = new                          # the save renamed the document (ChemDraw 23 does not)
    finally:
        mine = {name} | {os.path.basename(p) for p in outputs}
        for n in mine - before:
            osa('tell application "%s"\nrepeat with d in (every document whose name is "%s")\nclose d saving no\n'
                'end repeat\nend tell' % (APP, n))
    if failed:
        raise SystemExit(failed)
    return open_names()


if __name__ == "__main__":
    print("open after render:", render(sys.argv[1], sys.argv[2:]))
