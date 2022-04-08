"""Tkinter generic variable.

Comes with tools:

* ``Invalid`` special value
* ``gt0``, ``ge0``, ``nullable`` converter compositors

Also, it sports the ``validated_hook`` property for all-in-one validation and conversion.
"""

__all__ = [
    "GenericVar",
    "Invalid",
    "ge0",
    "gt0",
    "nullable",
]

from typing import Callable
import weakref
from tkinter import Variable, Widget


class Invalid:
    """Sentinel object to signal that the read value was invalid.
    
    ``Invalid`` will returned as itself (i.e. not as instance).
    """


class GenericVar(Variable):
    """Generic variable.
    
    A conversion function can be specified to get a "native" value from the
    string representation and vice-versa. By default, behaves like a StringVar.

    ``master`` can be given as master widget.
    ``value`` is an optional value (defaults to "")
    ``name`` is an optional Tcl name (defaults to PY_VARnum).
    If ``name`` matches an existing variable and ``value`` is omitted
    then the existing value is retained.


    """
    _default = ""

    def __init__(self, master=None, value=None, name=None, convert=str, convert_set=str, validated_hook=None):
        self.convert = convert
        """
        Gives the conversion to apply when ``get``-ting the value.

        ``convert`` takes the string (widget content) as single argument and
        returns a converted value. Any Exceptions will be caught (see `get`).
        """
        self.convert_set = convert_set
        """
        Gives the function to apply to a value passed in to ``set``.
        
        In most cases the default (``str``) will be sufficient.
        """
        self.validated_hook = validated_hook
        Variable.__init__(self, master, value, name)

    @property
    def validated_hook(self) -> Callable[[bool], None]:
        """If set, adds a side-effect to ``get`` depending on whether the value was valid or not.

        It shall be a callback taking a single bool argument ``valid``; which is
        True or False depending on whether ``convert`` raised an exception.

        If you set ``validated_hook`` to a Tk widget, we will automatically convert it into a callback:

        * For a Tk widget, foreground color will be set to ``red`` /
          original color depending on ``valid``.
        * For a Ttk widget, ``invalid`` state will be set/reset. Note that in
          most themes, by default no visual change happens, unless you
          configured an appropriate style map.
        """
        return self._validated_hook

    @validated_hook.setter
    def validated_hook(self, val):
        if isinstance(val, Widget):
            val = _make_hook_for_widget(val)
        self._validated_hook = val

    def get(self):
        """Return converted value of variable.
        
        If conversion failed, returns :py:obj:`.Invalid`."""
        # We use here the fact, that when used in a widget, the value will be
        # retrieved directly instead through .get(). Thus the widget will always "see" the str representation.
        value = self._tk.globalgetvar(self._name)
        try:
            value = self.convert(value)
        except Exception as e:
            value = Invalid
        if self._validated_hook:
            self._validated_hook(value is not Invalid)
        return value

    def set(self, value):
        value = self.convert_set(value)
        super().set(value)

def _make_hook_for_widget(widget):
    wwidget = weakref.ref(widget)
    if hasattr(widget, "state"):
        # TTK
        def setvalid(valid):
            widget = wwidget()
            if widget is None:
                return
            widget.state(["!invalid"] if valid else ["invalid"])
    else:
        # plain Tk
        orig_color = widget["foreground"]
        def setvalid(valid):
            widget = wwidget()
            if widget is None:
                return
            widget["foreground"] = orig_color if valid else "red"
    return setvalid


def gt0(convert):
    '''Applies ``convert``, then raises if value is not greater than 0.
    
    ``convert`` must return something number-like.

    >>> generic_var.convert = gt0(int)
    '''
    def wrap_convert(x):
        x = convert(x)
        if not x > 0:
            raise ValueError("Expected number greater than 0")
        return x
    return wrap_convert


def ge0(convert):
    '''Applies ``convert``, then raises if value is not greater or equal to 0.
    
    ``convert`` must return something number-like.

    >>> generic_var.convert = ge0(int)
    '''
    def wrap_convert(x):
        x = convert(x)
        if not x >= 0:
            raise ValueError("Expected number greater or equal to 0")
        return x
    return wrap_convert


def nullable(convert):
    '''Creates a converter that returns ``None`` on empty string, otherwise applies given converter.
    
    >>> generic_var = GenericVar(tkroot, convert=nullable(float))
    >>> generic_var.set("1.0")
    >>> generic_var.get()
    1.0
    >>> generic_var.set("")
    >>> generic_var.get()
    None
    >>> generic_var.set("foo")
    >>> generic_var.get()
    <class Invalid>
    '''
    def wrap_convert(x):
        if x == "":
            return None
        else:
            return convert(x)
    return wrap_convert
