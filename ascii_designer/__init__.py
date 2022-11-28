'''
ASCII Designer: Library to generate Forms from ASCII Art... and then some.

:any:`AutoFrame` is the main workhorse class. Subclass it and set the ``f_body`` 
and maybe further attributes.

Package overview:

 * :any:`autoframe` provides the :any:`AutoFrame` class, which by itself
   contains the build logic and the automatic binding infrastructure.
 * :any:`toolkit` provides the widget generators and actual value and event
   binding. The base :any:`ToolkitBase` contains the parsing function and lots
   of abstract methods.
 * :any:`toolkit_tk` and :any:`toolkit_qt` provide actual implementations of the
   Toolkit interface.
 * :any:`ascii_slice` contains the text slicing algorithm used to cut text into
   grid cells.
 * :any:`list_model` contains the list-like value class for list view / tree
   view. The :any:`ObsList` is toolkit-agnostic and has has lots of hooks where
   the GUI bindings (in the ``toolkit_`` modules) connect to.
'''
from .autoframe import AutoFrame
from .toolkit import set_toolkit
from .event import EventSource, CancelEvent
from .i18n import Translations, load_translations_json, save_translations_json
from .tk_generic_var import Invalid, nullable, gt0, ge0

__all__ = [
    'AutoFrame',
    'set_toolkit',
    'EventSource',
    'CancelEvent',
    'Invalid',
    'nullable',
    'gt0',
    'ge0',
    'Translations',
    'load_translations_json',
    'save_translations_json',
    ]
