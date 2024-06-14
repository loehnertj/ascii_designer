"""I18n support for ASCII Designer or other purposes.

.. default-role:: py:obj

Provides the working-data structure `.Translations`, and functions to load and
save translation files.
"""
__all__ = [
    "Translations",
    "load_translations_json",
    "save_translations_json",
]

from pathlib import Path, PurePath
try:
    import importlib.resources as resources
except ImportError:
    resources = None
import sys
import os
import json
import ctypes
import locale
import logging


def L():
    return logging.getLogger(__name__)


class Translations(dict):
    """Mostly off-the shelf python dict, except for some facilities to aid translation.

    Translations should be retrieved via ``.get(key, default)`` method.

    The class has the two additional properties `.recording` and `.mark_missing`.

    * If `recording` is set to True, calls of `~.Translations.get` will add missing entries
      (i.e. `~.Translations.get` does the same as `.setdefault`). By setting it and opening
      all forms once, you can collect all translation keys and default strings.
    * If `mark_missing` is set and `~.Translations.get` finds a missing key, the given default
      value is prefixed with a ``$`` sign.

    Additionally, it sports the convenience methods `get_prefix` and `get_exception`.
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

    def get_prefix(self, prefix):
        """Returns a getter function like ``get`` that augments keys with
        the given prefix.

        I.e.: ``tr.get("prefix.name", "..")`` is equivalent to
        ``tr.get_prefix("prefix")(".name", "..")``.
        """
        return lambda key, default: self.get(prefix + key, default)

    def get_exception(self, exc, prefix="exc."):
        """Return translation for the given exception.

        Translation is retrieved using they key ``<prefix><exc. class>``.
        E.g. ``exc.ValueError``.

        The translated string MAY contain placeholders corresponding to
        attributes of the exception object. Additionally, ``{exc}`` can be
        used to insert the original string representation of the exception.

        Fallback text is str(exc).
        """
        text: str = self.get(f"{prefix}{exc.__class__.__name__}", "")
        if not text:
            return str(exc)
        else:
            return text.format(str=str(exc), **exc.__dict__)

def load_translations_json(package_or_dir="locale", prefix="", language=None):
    """Locate and load translations from JSON file.

    JSON file format is a simple key value store.

    If given a package name, use the resource loading system. If given a
    dir, use file access.

    The argument is interpreted as dir if:

    * the string contains ``/`` or ``\\``
    * the argument is a ``pathlib.PurePath`` instance.

    Resource name is formed by the rule "<prefix>.<language>.json" (first dot is
    ommited if one of both is empty). If both prefix and language are empty, we look
    for ``default.json``.

    If the language is not given, the OS's UI language is used.

    With the given or guessed language we look for an existing file:

    * First we look for the exact language string (e.g. "de_DE.json")
    * then we look for the first two letters of the language string ("de.json")
    * then we look for emtpy language (i.e. default set).

    If none of these exists, empty ``Translations`` object is returned.
    """
    if (
        isinstance(package_or_dir, PurePath)
        or "/" in package_or_dir
        or "\\" in package_or_dir
    ):
        # filesystem path
        path = find_json_path(package_or_dir, prefix, language)
        openfunc = lambda: path.open("r")
        type = "file"
    else:
        # resource dir
        if resources is None:
            L().error("importlib.resource is not available, translations must be loaded from file instead.")
            return Translations()
        path = find_resource(package_or_dir, prefix, language)
        openfunc = lambda: resources.open_text(package_or_dir, path)
        type = "resource"
    # Not found
    if path is None:
        L().debug("No translations found")
        return Translations()
    L().debug("Load translations from %s %s", type, path)
    with openfunc() as fp:
        d = json.load(fp)
    return Translations(d)


def save_translations_json(translations, path):
    """Save translations to JSON file.

    OVERWRITES existing file!

    In contrast to ``load_translations_json``, we only accept a path here.
    """
    path = Path(path)
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


def find_json_path(dir, prefix="", language=None) -> Path:
    """Find location of translations file.

    ``dir`` gives the directory to search in, absolute or relative.

    Filename is formed by the rule "<prefix>.<language>.json" (first dot is
    ommited if one of both is empty). If both prefix and language are empty, we look
    for ``default.json``.

    If the language is not given, we try to get UI language of the OS.

    With the given or guessed language we look for an existing file:

    * First we look for the exact language string
    * then we look for the first two letters of the language string
    * then we look for emtpy language (i.e. default set).

    If none of these exists, None is returned.
    """
    dir = Path(dir)
    if language is None:
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


def find_resource(package, prefix="", language=None):
    if language is None:
        language = _os_locale()
        L().debug("OS language: %s", language)
    for name in [
        _join_ne(prefix, language, "json"),
        _join_ne(prefix, language[:2], "json"),
        _join_ne(prefix or "default", "json"),
    ]:
        if resources.is_resource(package, name):
            return name
    return None
