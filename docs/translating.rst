Translating forms
=================

.. default-role:: py:obj

ASCII designer has a custom translation system for forms. You can also add own content e.g. for dynamic texts.

Builtin translation covers:

* Widget and label texts (Key ``<Class>.<widget_id>``)
* List column headers (Key ``<Class>.<widget_id>.<column_id>``)
* Menu entries (Key ``<Class>.<menuitem_id>``)
* Form title (Key ``<Class>.f_title``)

Translations are stored as JSON files. The content is a simple key-value store.

Translation files can be stored either within some python package (recommended), or accessed via path.

Whichever folder you use, name the files:

* ``default.json`` for fallback translations (usually English)
* ``<code>.json`` e.g. ``de.json``, ``en.json``, ... for individual languages
* If required, add country-specific versions as ``de_DE.json``, ``de_CH.json``.


Loading translations from a package
------------------------------------

Assume that the translations files are stored in ``my_app`` package, in a
subfolder ``locale``. I.e. the actual translation package is ``my_app.locale``.
Remember that in Python 3.3+, the ``__init__.py`` is not required anymore.

File structure::

    my_app/
        __init__.py
        my_app.py
        ...etc...
        locale/
            default.json
            de.json
            es.json
            ...etc...

To use translations, add the following code where you init your app::

    from ascii_designer import AutoFrame, load_translations_json

    # in Setup code
    translations = load_translations_json("my_app.locale")
    AutoFrame.f_translations = translations

Remarks
.......

Language will be picked up from the OS. To force a language, use e.g.
``load_translations_json("my_app.locale", language="es")``.

The ``importlib.resource`` loader will be used, meaning you can put package and
translations in a zip file if needed. `.load_translations_json` will not fail
even if no translation file is found.

``translations`` is a `~.i18n.Translations` instance. For the most part, it's
just a dict matching the JSON's content.

Keys are formed as ``<ClassName>.<widget_id>``. Additionally, List column
headers are stored as ``<ClassName>.<widget_id>.<column_id>``. It is recommended
to use the recording feature to generate the file (see below).

By setting the class attribute ``AutoFrame.f_translations``, Translations are
shared among all ``AutoFrame`` subclasses. You can also set translations just for
an individual form or even instance, by setting their respective ``f_translations``
class or instance attribute.


Loading translations from a file
---------------------------------

Works nearly the same. Pass to `.load_translations_json`:

* a ``pathlib.Path``, or
* a string containing at least one slash ``/`` or backslash ``\``.

Instead of the ``importlib.resource`` loader, normal file loading is used.


Generating or updating translation files
----------------------------------------

`.Translations` has a special flag `~.Translations.recording` that you can set.
The dictionary will then record all translation keys that are queried.

Extend your startup code as follows::


    from ascii_designer import AutoFrame, load_translations_json, save_translations_json

    # in Setup code
    translations = load_translations_json("my_app.locale", language="")
    AutoFrame.f_translations = translations
    translations.recording = True

    # Show your app here
    # After mainloop exits (last window closed):
    save_translations_json(AutoFrame.f_translations, "default.json")

Note that the default language is forced when loading.

Run the app, and open all forms that need to be translated at least once. After
exiting the app, the new translation file is saved.

Existing entries of the translation file are kept untouched. New entries are
appended at the end.

Now, copy or move the file to your translations directory. Make a copy for each
language to translate into, e.g ``de.json``, ... Then edit the translations with
any tool of choice.


To see if there are any translations missing in the GUI
--------------------------------------------------------

Set `.Translations.mark_missing` flag. All GUI strings missing in the
translation file will be prepended with ``$``.


Adding custom translations
---------------------------

Just add them to the JSON dictionary under whatever key(s) you like.

In a Form method, retrieve them by::

    custom_text = self.f_translations.get("my_key", "Default text here")

**Always use** `~.Translations.get`. That way the key can be "captured" by the ``recording``
and ``mark_missing`` features.
