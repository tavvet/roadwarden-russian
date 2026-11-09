"""Check a translated chunk without merging it.

    python3 tools/validate.py work/areas__prologue__01.ru.json

Prints missing ids, unknown ids and per-string problems. Exit code 0 = all good.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check import problems  # noqa: E402


def main():
    path = sys.argv[1]
    src = path[:-len(".ru.json")] + ".json"
    with open(src, encoding="utf-8") as f:
        items = {i["id"]: i["en"] for i in json.load(f)["items"]}
    try:
        with open(path, encoding="utf-8") as f:
            ru = json.load(f)
    except ValueError as e:
        print("INVALID JSON:", e)
        sys.exit(1)
    bad = 0
    missing = [k for k in items if k not in ru]
    extra = [k for k in ru if k not in items]
    for k in missing:
        print("MISSING", k, repr(items[k][:80]))
    for k in extra:
        print("UNKNOWN ID", k)
    for k, text in ru.items():
        if k in items:
            for p in problems(items[k], text):
                bad += 1
                print("PROBLEM", k, p)
    print("strings %d, translated %d, missing %d, unknown %d, problems %d" % (
        len(items), len(ru), len(missing), len(extra), bad))
    sys.exit(0 if not (missing or extra or bad) else 1)


if __name__ == "__main__":
    main()
