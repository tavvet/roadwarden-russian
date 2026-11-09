"""Extract every player-visible string literal from the game's .rpy sources.

Writes data/strings.json: {id: {"en", "file", "line", "order", "count"}}.
Re-running after a game update keeps ids stable (id = hash of normalized text).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA, GAME_DIR, TAG_RE, VAR_RE, norm, save_json, sid  # noqa: E402

# Files whose strings we never want (Ren'Py template leftovers).
SKIP_FILES = {"sample.rpy"}

PATH_RE = re.compile(r"\.(png|jpg|jpeg|webp|ogg|mp3|wav|opus|ttf|otf|rpy|txt|json)\b|/", re.I)
IDENT_RE = re.compile(r"^[\w\-]+(?:\.\w+)*$")
DEF_RE = re.compile(
    r"^\s*(?:label|screen|style|transform|image|default|define|init\s+python\s+in)\s+([A-Za-z_][\w.]*)"
    r"|^\s*\$?\s*([A-Za-z_]\w*)\s*(?:\+|-)?=[^=]"
    r"|\bdef\s+(\w+)",
    re.M,
)
_inc = os.path.join(DATA, "include_words.txt")
INCLUDE_WORDS = set(open(_inc, encoding="utf-8").read().split()) if os.path.exists(_inc) else set()

STOPWORDS = {
    "nvl", "adv", "basic", "pixel", "dissolve", "fade", "music", "sound", "audio",
    "voice", "screen", "say", "menu", "center", "left", "right", "top", "bottom",
    "true", "false", "none", "auto", "hover", "idle", "insensitive", "selected",
    "main", "game", "start", "quit", "rollback", "rollforward", "default",
}


def dequote(body):
    """Ren'Py-statement string semantics (parser.Lexer.string)."""
    body = re.sub(r"\s+", " ", body)

    def rep(m):
        c = m.group(1)
        if c == "n":
            return "\n"
        if c == "t":
            return "\t"
        if c[0] == "u" and m.group(2):
            return chr(int(m.group(2), 16))
        return c

    s = re.sub(r"\\(u([0-9a-fA-F]{1,4})|.)", rep, body)
    # Spaces around paragraph breaks are invisible in game; tidy them for translators.
    s = re.sub(r" *\n *", "\n", s)
    return s


def scan(src):
    """Yield (line_no, string_body) for each string literal outside comments."""
    i, n, line = 0, len(src), 1
    while i < n:
        c = src[i]
        if c == "\n":
            line += 1
            i += 1
        elif c == "#":
            j = src.find("\n", i)
            i = n if j < 0 else j
        elif c in "'\"`":
            triple = src[i:i + 3] == c * 3
            q = c * 3 if triple else c
            start_line = line
            j = i + len(q)
            buf = []
            while j < n:
                if src[j] == "\\" and j + 1 < n:
                    buf.append(src[j:j + 2])
                    j += 2
                    continue
                if src.startswith(q, j):
                    break
                buf.append(src[j])
                j += 1
            body = "".join(buf)
            line += body.count("\n")
            i = j + len(q)
            yield start_line, body
        else:
            i += 1


def displayable(s, idents):
    bare = VAR_RE.sub("", TAG_RE.sub("", s)).strip()
    if not re.search(r"[A-Za-z]", bare):
        return False
    if PATH_RE.search(bare) and " " not in bare:
        return False
    st = s.strip()
    if IDENT_RE.match(st):
        if re.search(r"[0-9_]|\w\.\w", st):
            return False
        if st in idents or st in STOPWORDS:
            return False
        # Lowercase single words are almost always internal keys ("thehuntercabin").
        # Ones that really are shown go into data/include_words.txt.
        if st.islower() and st not in INCLUDE_WORDS:
            return False
    if st.startswith("#") and re.match(r"^#[0-9a-fA-F]{3,8}$", st):
        return False
    # Menu placeholders replaced by nvlchoices.rpy: '(elah1 set)'
    if re.match(r"^\(\w+ set\)$", st):
        return False
    # Python conditions used by menus: condition="at == 'friendly' and not x_y"
    if re.search(r"==|!=|>=|<=|\w\(|\b\w+_\w+\b", bare) and not re.search(r"[“”’]", st):
        words = re.findall(r"[A-Za-z_]\w*", bare)
        codeish = sum(1 for w in words if "_" in w or w in ("and", "or", "not", "in", "is", "None", "True", "False"))
        if re.search(r"==|!=|>=|<=", bare) or codeish * 2 >= len(words):
            return False
    return True


def main():
    files = []
    for dirpath, dirnames, filenames in os.walk(GAME_DIR):
        dirnames[:] = sorted(d for d in dirnames if d not in ("tl", "cache", "zz_russian"))
        for fn in sorted(filenames):
            if fn.endswith(".rpy") and fn not in SKIP_FILES:
                files.append(os.path.relpath(os.path.join(dirpath, fn), GAME_DIR))

    sources = {}
    idents = set()
    for rel in files:
        with open(os.path.join(GAME_DIR, rel), encoding="utf-8") as f:
            src = f.read()
        sources[rel] = src
        for m in DEF_RE.finditer(src):
            for g in m.groups():
                if g:
                    idents.add(g.split(".")[-1])

    strings = {}
    order = 0
    for rel in files:
        for line_no, body in scan(sources[rel]):
            text = dequote(body)
            if not displayable(text, idents):
                continue
            key = sid(text)
            if key in strings:
                strings[key]["count"] += 1
                continue
            strings[key] = {"en": norm(text) if "\n" not in text else text.strip(),
                            "file": rel, "line": line_no, "order": order, "count": 1}
            order += 1

    save_json(os.path.join(DATA, "strings.json"), strings)

    words = {}
    for v in strings.values():
        words[v["file"]] = words.get(v["file"], 0) + len(v["en"].split())
    total = sum(words.values())
    print(f"{len(strings)} unique strings, {total} words, {len(files)} files")
    for f, w in sorted(words.items(), key=lambda x: -x[1])[:12]:
        print(f"  {w:7d}  {f}")


if __name__ == "__main__":
    main()
