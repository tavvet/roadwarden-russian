# Roadwarden: unofficial Russian translation (machine translation by Claude, draft).
#
# Does not touch the game's script. Text is swapped for Russian at display time:
#   * renpy.translation.translate_string: say lines, menus, screen text;
#   * values interpolated as [var] (the game keeps most text in variables);
#   * history entries the game adds by hand (narrator.add_history).
# Game variables stay English, so the game's logic and saves are unaffected.
#
# F9 switches between Russian and the original.
# To uninstall, delete the game/zz_russian folder.

init -1500 python in ru:
    import hashlib
    import json
    import re

    _ws = re.compile(r"\s+", re.U)

    def _load():
        f = renpy.file("zz_russian/ru_strings.json")
        try:
            return json.loads(f.read().decode("utf-8"))
        finally:
            f.close()

    _data = _load()
    table = _data["strings"]  # {sha1(normalized English)[:keylen]: Russian}
    _keylen = _data.get("keylen", 16)

    def _key(k):
        if isinstance(k, unicode):
            k = k.encode("utf-8")
        return hashlib.sha1(k).hexdigest()[:_keylen]

    # Strings the game builds with % formatting ("Lost %s pneuma.").
    # Each item: [regex for the normalized English, Russian template, prefix].
    patterns_by_prefix = {}
    for _p in _data.get("patterns", []):
        _entry = (re.compile(_p[0], re.S | re.U), _p[1])
        patterns_by_prefix.setdefault(_p[2], []).append(_entry)

    _fmt = re.compile(r"%(?:\([a-z_]+\))?[-0-9.]*[dsfi]")

    def enabled():
        return not renpy.store.persistent.ru_disabled

    def _apply_pattern(k):
        for prefix in (k[:4], ""):
            for rx, ru in patterns_by_prefix.get(prefix, ()):
                m = rx.match(k)
                if m:
                    groups = iter(m.groups())

                    def fill(_m):
                        g = next(groups, "") or ""
                        return table.get(_key(g.strip()), g)

                    return _fmt.sub(fill, ru)
        return None

    # Debug: RU_DEBUG=/path/file.txt logs every English string that was shown
    # but had no translation (to find gaps after a game update).
    import os
    _debug_path = os.environ.get("RU_DEBUG")
    _missing = set()
    _hit = []
    _latin = re.compile(r"[A-Za-z]{2,}")
    _cyr = re.compile(u"[Ѐ-ӿ]")
    _letters = re.compile(r"[^\W\d_]", re.U)
    _markup = re.compile(r"\{[^{}]*\}|\[[^\[\]]*\]")

    def _log(line):
        if _debug_path:
            with open(_debug_path, "ab") as f:
                f.write((line + u"\n").encode("utf-8"))

    _log(u"### loaded %d strings, %d patterns" % (len(table), len(_data.get("patterns", []))))

    def lookup(s):
        """Russian text for s, or None. Keeps s's leading/trailing whitespace."""
        if not s:
            return None
        k = _ws.sub(" ", s).strip()
        if not k:
            return None
        r = table.get(_key(k))
        if r is not None and _debug_path and not _hit:
            _hit.append(k)
            _log(u"### first hit: " + k + u" -> " + r)
        if r is None:
            r = _apply_pattern(k)
            if r is None and (u"\u201c" in k or u"\u201d" in k) and not _letters.search(_markup.sub(u"", k)):
                # Letterless glue templates ('[custom1]{color=…}[price]{/color}.”'):
                # only the English quotes need changing.
                r = k.replace(u"\u201c", u"\u00ab").replace(u"\u201d", u"\u00bb")
            if r is None:
                if _debug_path and k not in _missing and _latin.search(k) and not _cyr.search(k):
                    _missing.add(k)
                    _log(u"MISS " + k)
                return None
        stripped = s.strip()
        if stripped == s:
            return r
        lead = s[:len(s) - len(s.lstrip())]
        trail = s[len(s.rstrip()):]
        return lead + r + trail

    # 1. All string translation in the engine.
    _orig_translate_string = renpy.translation.translate_string

    def translate_string(s, *args, **kwargs):
        if enabled():
            r = lookup(s)
            if r is not None:
                return r
        return _orig_translate_string(s, *args, **kwargs)

    renpy.translation.translate_string = translate_string
    renpy.exports.translate_string = translate_string
    renpy.translate_string = translate_string

    # 2. [var] interpolation: translate the variable's value too.
    _Formatter = renpy.substitutions.Formatter
    _orig_convert_field = _Formatter.convert_field

    def _convert_field(self, value, conversion):
        if conversion is None and enabled():
            obj = value[0]
            if isinstance(obj, basestring):
                r = lookup(obj)
                if r is not None:
                    return r
        return _orig_convert_field(self, value, conversion)

    _Formatter.convert_field = _convert_field

    # 3. Hand-added history entries (shown with substitute False).
    _ADV = renpy.character.ADVCharacter
    _orig_add_history = _ADV.add_history

    def _add_history(self, kind, who, what, *args, **kwargs):
        if enabled() and isinstance(what, basestring):
            r = lookup(what)
            if r is not None:
                what = r
        return _orig_add_history(self, kind, who, what, *args, **kwargs)

    _ADV.add_history = _add_history

    # 4. The Munro pixel font has no Cyrillic; draw it with Philosopher instead.
    for _b in (False, True):
        for _i in (False, True):
            renpy.config.font_replacement_map[("munro.ttf", _b, _i)] = ("philosopher.ttf", _b, _i)

    # 5. F9 toggles Russian / English (keymap is set up below, after the engine's).
    def toggle():
        p = renpy.store.persistent
        p.ru_disabled = not p.ru_disabled
        renpy.notify("Translation: English" if p.ru_disabled else "Перевод: русский")
        renpy.restart_interaction()

init 1000 python in ru:
    renpy.config.keymap["ru_toggle"] = ["K_F9"]
    renpy.config.underlay.append(renpy.Keymap(ru_toggle=toggle))
