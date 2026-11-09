"""Shared helpers for the Roadwarden Russian translation tools."""
import hashlib
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.environ.get(
    "ROADWARDEN_GAME",
    os.path.expanduser(
        "~/Library/Application Support/Steam/steamapps/common/Roadwarden/"
        "Roadwarden.app/Contents/Resources/autorun/game"
    ),
)
DATA = os.path.join(ROOT, "data")
TRANSLATIONS = os.path.join(ROOT, "translations")
WORK = os.path.join(ROOT, "work")

_WS = re.compile(r"\s+")


def norm(s):
    """Lookup key: whitespace collapsed and trimmed. The in-game hook does the same."""
    return _WS.sub(" ", s).strip()


def sid(s):
    return hashlib.sha1(norm(s).encode("utf-8")).hexdigest()[:10]


def file_key(relpath):
    """areas/creeks02elah.rpy -> areas__creeks02elah"""
    return relpath[:-4].replace("/", "__")


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, path)


def load_strings():
    return load_json(os.path.join(DATA, "strings.json"), {})


def load_translations():
    """{id: {"ru": str, "status": "draft"|"reviewed"}} merged from all translation files."""
    out = {}
    if not os.path.isdir(TRANSLATIONS):
        return out
    for name in sorted(os.listdir(TRANSLATIONS)):
        if name.endswith(".json"):
            out.update(load_json(os.path.join(TRANSLATIONS, name), {}))
    return out


TAG_RE = re.compile(r"\{[^{}]*\}")
VAR_RE = re.compile(r"\[[^\[\]]*\]")
FMT_RE = re.compile(r"%(?:\([a-z_]+\))?[-0-9.]*[dsfi%]")
