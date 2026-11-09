"""Translation progress per source file (words): draft / reviewed / total."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_strings, load_translations  # noqa: E402


def main():
    strings = load_strings()
    trans = load_translations()
    rows = {}
    for k, v in strings.items():
        w = len(v["en"].split())
        r = rows.setdefault(v["file"], [0, 0, 0])
        r[2] += w
        t = trans.get(k)
        if t:
            r[0 if t["status"] == "draft" else 1] += w
    tot = [sum(r[i] for r in rows.values()) for i in range(3)]
    show_all = "--all" in sys.argv
    print("%-45s %8s %8s %8s" % ("file", "draft", "reviewed", "total"))
    for f, r in sorted(rows.items()):
        if show_all or r[0] or r[1]:
            print("%-45s %8d %8d %8d" % (f, r[0], r[1], r[2]))
    print("%-45s %8d %8d %8d   (%.1f%% translated, %.1f%% reviewed)" % (
        "TOTAL", tot[0], tot[1], tot[2], 100.0 * (tot[0] + tot[1]) / tot[2], 100.0 * tot[1] / tot[2]))


if __name__ == "__main__":
    main()
