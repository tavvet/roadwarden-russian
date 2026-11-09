"""Cut untranslated strings into work chunks for translators.

    python3 tools/chunk.py areas/creeks02elah.rpy [more files...] [--words 2500]
    python3 tools/chunk.py --list          # files with untranslated words

Writes work/<filekey>__NN.json = {"file", "items": [{"id", "en"}]} in script order.
A translator writes the answer next to it as work/<filekey>__NN.ru.json = {id: ru}.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import WORK, file_key, load_strings, load_translations, save_json  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--words", type=int, default=2500)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    strings = load_strings()
    done = load_translations()
    pending = {}
    for k, v in strings.items():
        if k not in done:
            pending.setdefault(v["file"], []).append((v["order"], k, v["en"]))

    if a.list or not a.files:
        for f, items in sorted(pending.items(), key=lambda x: x[0]):
            print("%7d words  %5d strings  %s" % (sum(len(e.split()) for _, _, e in items), len(items), f))
        return

    os.makedirs(WORK, exist_ok=True)
    for f in a.files:
        items = sorted(pending.get(f, []))
        if not items:
            print("nothing to do:", f)
            continue
        chunks, cur, words = [], [], 0
        for _, k, en in items:
            cur.append({"id": k, "en": en})
            words += len(en.split())
            if words >= a.words:
                chunks.append(cur)
                cur, words = [], 0
        if cur:
            chunks.append(cur)
        for n, ch in enumerate(chunks, 1):
            path = os.path.join(WORK, "%s__%02d.json" % (file_key(f), n))
            save_json(path, {"file": f, "items": ch})
            print(path, len(ch), "strings", sum(len(i["en"].split()) for i in ch), "words")


if __name__ == "__main__":
    main()
