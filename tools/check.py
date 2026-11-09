"""Validation of a single translation against its English source."""
import re
from collections import Counter

from common import FMT_RE, TAG_RE, VAR_RE


def _latin_share(s):
    s = VAR_RE.sub("", TAG_RE.sub("", s.replace("(disabled)", "")))
    lat = len(re.findall(r"[A-Za-z]", s))
    cyr = len(re.findall(r"[А-Яа-яЁё]", s))
    return lat / (lat + cyr) if lat + cyr else 0.0


def _vars(s):
    # "[[" is a literal bracket in Ren'Py, not the start of a substitution.
    return Counter(VAR_RE.findall(s.replace("[[", "\0")))


def problems(en, ru):
    """Return a list of human-readable problems; empty list means OK."""
    out = []
    if not isinstance(ru, str) or not ru.strip():
        return ["пустой перевод"]
    if Counter(TAG_RE.findall(en)) != Counter(TAG_RE.findall(ru)):
        out.append("теги {} не совпадают: %s vs %s" % (sorted(TAG_RE.findall(en)), sorted(TAG_RE.findall(ru))))
    if _vars(en) != _vars(ru):
        out.append("подстановки [] не совпадают: %s vs %s" % (sorted(_vars(en)), sorted(_vars(ru))))
    for ch in "{}[]":
        if en.count(ch) != ru.count(ch):
            out.append("число скобок %s не совпадает (%d vs %d) — сломан тег или подстановка" % (ch, en.count(ch), ru.count(ch)))
    if en.count("[[") != ru.count("[[") or en.count("{{") != ru.count("{{"):
        out.append("экранированные [[ или {{ не совпадают")
    if FMT_RE.findall(en) != FMT_RE.findall(ru):
        out.append("%%-подстановки не совпадают: %s vs %s" % (FMT_RE.findall(en), FMT_RE.findall(ru)))
    if en.count("(disabled)") != ru.count("(disabled)"):
        out.append("служебный суффикс (disabled) должен остаться как есть")
    if en.count("\n\n") != ru.count("\n\n"):
        out.append("число абзацев (\\n\\n) не совпадает: %d vs %d" % (en.count("\n\n"), ru.count("\n\n")))
    if len(en.split()) >= 3 and _latin_share(ru) > 0.4:
        out.append("похоже, не переведено (много латиницы)")
    return out
