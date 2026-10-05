"""Subscript convention shared by the manuscript writer, the SI builder and the document reader (2026-09-11, author: "stuff
like i_lim or k_c ... needs to look professional ... properly rendered as subscripts").

    split("i_lim = nFD_SC_S/δ") -> [("i", False), ("lim", True), (" = nFD", False), ("S", True), ("C", False), ("S", True), ("/δ", False)]

A piece with the flag True is written as a Word subscript run; data/docx_text.py reads such a run back as "_" + text, so
split() and the reader are inverses and every gate phrase keeps its underscore spelling. The token after "_" is the LONGEST
entry of subscript_tokens.json that prefixes the alphanumeric run following the underscore; an underscore followed by no
listed token is left as a literal underscore (and `unconverted()` reports it)."""
import json, os, re

_HERE = os.path.dirname(os.path.abspath(__file__))
TOKENS = sorted(json.load(open(os.path.join(_HERE, "subscript_tokens.json"), encoding="utf8"))["tokens"], key=len, reverse=True)
_BASE = r"[A-Za-z0-9)Ͱ-Ͽµ]"           # what may precede the underscore: a letter, digit, ")", Greek, micro
_RE = re.compile(r"(?<=%s)_([A-Za-z0-9]+)" % _BASE)


def _token(text, m):
    """The longest listed token that starts the alphanumeric run after the underscore and either exhausts it or is followed
    by another symbol's underscore (the D_SC_S case); otherwise None, so H_EXT and si_001 stay literal."""
    run = m.group(1); after = text[m.end():m.end() + 1]
    for t in TOKENS:
        if run.startswith(t) and (len(run) == len(t) or after == "_"):
            return t
    return None


def split(text):
    """[(piece, is_subscript), ...] in document order; adjacent plain pieces are merged."""
    out, pos = [], 0
    for m in _RE.finditer(text):
        run = m.group(1)
        tok = _token(text, m)
        if tok is None:
            continue                                      # not a symbol we know: the underscore stays literal
        if m.start() > pos:
            out.append((text[pos:m.start()], False))
        out.append((tok, True))
        pos = m.start() + 1 + len(tok)
    if pos < len(text):
        out.append((text[pos:], False))
    return out


def unconverted(text):
    """The BASE_run occurrences split() leaves alone (no listed token), for the builders to report."""
    return [text[m.start() - 1:m.end()] for m in _RE.finditer(text) if _token(text, m) is None]     # with its base letter


def roundtrip(text):
    return "".join(("_" + t) if s else t for t, s in split(text))


if __name__ == "__main__":
    for s in ("i_lim = nFD_SC_S/δ", "n_cFD_cC_c", "nFDC_bulk", "x_k = √(D/kC_S)", "k c_ox c_S x/(s_ox i/F)", "F C_med √(D k C_S)",
              "h_int, T_boil, i_design, V_A, A_external, Med_red, delta_eff, H_EXT, si_001, max_x c, x_f/δ, i_lim,", "no underscore here", "S5.1-S5.7"):
        assert roundtrip(s) == s, (s, roundtrip(s))
        print("%-50s -> %s   unconverted: %s" % (s, split(s), unconverted(s)))
    assert unconverted("H_EXT, si_001, kappa_crit") == ["H_EXT", "i_001"], unconverted("H_EXT, si_001, kappa_crit")
    assert [t for t, sub in split("nFD_SC_S") if sub] == ["S", "S"] and [t for t, sub in split("n_cFD_cC_c") if sub] == ["c", "c", "c"]
    print("subscripts.py self-test OK")
