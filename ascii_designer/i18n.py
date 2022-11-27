"""I18n support for ASCII Designer or other purposes.

.. default-role:: py:obj

Provides the working-data structure `.Translations`, and functions to load and
save translation files.
"""
__all__ = [
    "Translations",
]

from pathlib import Path
import sys
import os
import json
import ctypes
import locale
import logging

def L():
    return logging.getLogger(__name__)


class Translations(dict):
    """Mostly off-the shelf python dict, except for two facilities to aid translation.

    Translations should be retrieved via ``.get(key, default)`` method.

    The class has the two additional properties `.recording` and `.mark_missing`.

    * If `recording` is set to True, calls of `.get` will add missing entries
      (i.e. `.get` does the same as `.setdefault`). By setting it and opening
      all forms once, you can collect all translation keys and default strings.
    * If `mark_missing` is set and `.get` finds a missing key, the given default
      value is prefixed with a ``$`` sign.
    """

    recording: bool = False
    mark_missing: bool = False

    def get(self, key, default=None):
        if self.recording:
            return self.setdefault(key, default)
        else:
            if self.mark_missing:
                default = "$" + default
            return super().get(key, default)


def load_translations_json(dir="locale", prefix="", language=""):
    """Locate and load translations from JSON file.

    JSON file format is a simple key value store.

    The file is located due to certain rules, see `.find_json_path`.
    """
    path = find_json_path(dir, prefix, language, fallback_logic=True)
    # Not found
    if path is None:
        L().debug("No translations found")
        return Translations()
    L().debug("Load translations %s", path)
    with path.open("r") as fp:
        d = json.load(fp)
    return Translations(d)


def save_translations_json(translations, dir="locale", prefix="", language="") -> Path:
    """Save translations to JSON file.

    OVERWRITES existing file!

    ``language`` is taken as-is.
    """
    path = find_json_path(dir, prefix, language, fallback_logic=False)
    with path.open("w") as fp:
        json.dump(translations, fp, indent=2)
    L().info("Saved translations to %s", path)
    return path


def _join_ne(*strings):
    return ".".join(part for part in strings if part)


def _os_locale():
    if sys.platform.startswith("linux"):
        lang = os.getenv("LANG")
        # split off charset part
        return lang.partition(".")[0]
    elif sys.platform.startswith("win32"):
        windll = ctypes.windll.kernel32
        lang_id = windll.GetUserDefaultUILanguage()
        lang = locale.windows_locale[lang_id]
        return lang.partition(".")[0]
    else:
        raise RuntimeError("Cannot guess language on %s platform" % sys.platform)


def find_json_path(dir="locale", prefix="", language="", fallback_logic=True) -> Path:
    """Find location of translations file.

    ``dir`` gives the directory to search in, absolute or relative.

    Filename is formed by the rule "<prefix>.<language>.json" (first dot is
    ommited if one of both is empty). If both prefix and language are empty, we look
    for ``default.json``.

    If ``fallback_logic`` is ``False``, path will be formed and returned
    according to the rule, regardless whether it exists.

    If ``fallback_logic`` is ``True``, the following happens:

    If the language is not given, we try to get UI language of the OS.

    With the given or guessed language we look for an existing file:

    * First we look for the exact language string
    * then we look for the first two letters of the language string
    * then we look for emtpy language (i.e. default set).

    If none of these exists, None is returned.
    """
    dir = Path(dir)
    if not fallback_logic:
        filename = _join_ne(prefix, language, "json")
        if filename == "json":
            filename = "default.json"
        return dir / filename
    else:
        if not language:
            language = _os_locale()
            L().debug("OS language: %s", language)
        for name in [
            _join_ne(prefix, language, "json"),
            _join_ne(prefix, language[:2], "json"),
            _join_ne(prefix or "default", "json"),
        ]:
            if (dir / name).exists():
                return dir / name
        return None
