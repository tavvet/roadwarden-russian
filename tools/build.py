"""Build the translation package and (optionally) install it into the game.

    python3 tools/build.py              # build dist/zz_russian
    python3 tools/build.py --install    # build and copy into the game folder
    python3 tools/build.py --uninstall  # remove it from the game folder

    python3 tools/build.py --zip        # build and pack release/roadwarden-ru-<date>.zip

The package is the hook (hook/ru_hook.rpy) plus ru_strings.json:
{"keylen": N, "strings": {sha1(normalized English)[:N]: Russian},
 "patterns": [[regex, Russian template, prefix]]}
Keys are hashes so the package does not carry the game's English text.
"""
import argparse
import datetime
import hashlib
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FMT_RE, GAME_DIR, DATA, ROOT, load_json, load_strings, load_translations, norm, save_json  # noqa: E402

DIST = os.path.join(ROOT, "dist", "zz_russian")
RELEASE = os.path.join(ROOT, "release")
KEYLEN = 16  # hex chars of sha1; the hook reads it from the file


def key(en_norm):
    return hashlib.sha1(en_norm.encode("utf-8")).hexdigest()[:KEYLEN]


def pattern_for(en_norm):
    parts = FMT_RE.split(en_norm)
    holes = FMT_RE.findall(en_norm)
    rx = "^"
    for i, lit in enumerate(parts):
        rx += re.escape(lit)
        if i < len(holes):
            rx += r"(-?\d+)" if holes[i].endswith("d") else r"(.*?)"
    rx += "$"
    prefix = en_norm[:4] if len(parts[0]) >= 4 else ""
    return rx, prefix


def build():
    strings = load_strings()
    trans = load_translations()
    table, patterns = {}, []
    for k, t in trans.items():
        if k not in strings:
            continue  # string disappeared after a game update
        # The hook restores the original's leading/trailing whitespace at runtime.
        en, ru = strings[k]["en"], t["ru"].strip()
        variants = [(en, ru)]
        # nvlchoices.rpy strips "(disabled)" before showing the caption.
        if "(disabled)" in en:
            variants.append((en.replace("(disabled)", ""), ru.replace("(disabled)", "").rstrip()))
        # ...and swaps the d6 icon in pixel text style.
        for e, r in list(variants):
            if "{image=d6}" in e:
                variants.append((e.replace("{image=d6}", "{image=d62}"), r.replace("{image=d6}", "{image=d62}")))
        for e, r in variants:
            table[key(norm(e))] = r
            if FMT_RE.search(e):
                rx, prefix = pattern_for(norm(e))
                patterns.append([rx, r, prefix])
    for e, r in load_json(os.path.join(DATA, "manual_ru.json"), {}).items():
        table[key(norm(e))] = r

    os.makedirs(DIST, exist_ok=True)
    save_json(os.path.join(DIST, "ru_strings.json"), {"keylen": KEYLEN, "strings": table, "patterns": patterns})
    shutil.copy(os.path.join(ROOT, "hook", "ru_hook.rpy"), os.path.join(DIST, "ru_hook.rpy"))
    print("built %d strings, %d patterns -> %s" % (len(table), len(patterns), DIST))


def pack():
    """Zip dist/zz_russian plus the player instructions for a GitHub release."""
    import zipfile
    os.makedirs(RELEASE, exist_ok=True)
    path = os.path.join(RELEASE, "roadwarden-ru-%s.zip" % datetime.date.today().isoformat())
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in ("ru_hook.rpy", "ru_strings.json"):
            z.write(os.path.join(DIST, name), "zz_russian/" + name)
        z.write(os.path.join(ROOT, "INSTALL.txt"), "INSTALL.txt")
    print("packed ->", path)


def install():
    dst = os.path.join(GAME_DIR, "zz_russian")
    os.makedirs(dst, exist_ok=True)
    for name in ("ru_hook.rpy", "ru_strings.json"):
        shutil.copy(os.path.join(DIST, name), os.path.join(dst, name))
    print("installed ->", dst)


def uninstall():
    dst = os.path.join(GAME_DIR, "zz_russian")
    if os.path.isdir(dst):
        shutil.rmtree(dst)
        print("removed", dst)
    else:
        print("not installed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--zip", action="store_true")
    a = ap.parse_args()
    if a.uninstall:
        uninstall()
        return
    build()
    if a.install:
        install()
    if a.zip:
        pack()


if __name__ == "__main__":
    main()
