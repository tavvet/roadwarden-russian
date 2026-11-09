"""Validate translated chunks (work/*.ru.json) and merge them into translations/.

    python3 tools/merge.py              # merge all finished chunks
    python3 tools/merge.py --status reviewed work/x__01.ru.json   # after a review pass

Bad entries are not merged; they are listed in work/<chunk>.problems.json.
Fully merged chunks are moved to work/done/.
"""
import argparse
import glob
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check import problems  # noqa: E402
from common import TRANSLATIONS, WORK, file_key, load_json, load_strings, save_json  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chunks", nargs="*")
    ap.add_argument("--status", default="draft", choices=["draft", "reviewed"])
    a = ap.parse_args()

    strings = load_strings()
    paths = a.chunks or sorted(glob.glob(os.path.join(WORK, "*.ru.json")))
    total_ok = total_bad = 0
    for path in paths:
        ru = load_json(path, {})
        bad = {}
        by_file = {}
        skipped = 0
        for k, text in ru.items():
            if k not in strings:
                skipped += 1  # string no longer extracted (placeholder or removed in an update)
                continue
            en = strings[k]["en"]
            p = problems(en, text)
            if p:
                bad[k] = {"en": en, "ru": text, "problems": p}
            else:
                by_file.setdefault(strings[k]["file"], {})[k] = {"ru": text, "status": a.status}
        for f, entries in by_file.items():
            tpath = os.path.join(TRANSLATIONS, file_key(f) + ".json")
            cur = load_json(tpath, {})
            cur.update(entries)
            save_json(tpath, dict(sorted(cur.items(), key=lambda kv: strings[kv[0]]["order"])))
        ok = sum(len(e) for e in by_file.values())
        total_ok += ok
        total_bad += len(bad)
        src = path[:-len(".ru.json")] + ".json"
        expected = len(load_json(src, {}).get("items", [])) if os.path.exists(src) else len(ru)
        missing = expected - len(ru)
        prob_path = path[:-len(".ru.json")] + ".problems.json"
        if bad:
            save_json(prob_path, bad)
        elif os.path.exists(prob_path):
            os.remove(prob_path)
        print("%s: ok %d, problems %d, missing %d, obsolete %d" % (
            os.path.basename(path), ok, len(bad), max(missing, 0), skipped))
        if not bad and missing <= 0 and path.startswith(WORK):
            os.makedirs(os.path.join(WORK, "done"), exist_ok=True)
            for p in (path, src):
                if os.path.exists(p):
                    shutil.move(p, os.path.join(WORK, "done", os.path.basename(p)))
    print("total ok %d, problems %d" % (total_ok, total_bad))


if __name__ == "__main__":
    main()
