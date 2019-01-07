'''
ASCII Designer: Library to generate Forms from ASCII Art... and then some.

``AutoFrame`` is the main workhorse class. Subclass it and set the ``f_body`` 
and maybe further attributes. All the reserved attributes are prepended with 
``f_`` to get out of your way when subclassing.

  * ``f_body`` is the textual definition of the form.
  * There is a **well-defined syntax** for how to get the usual widget types. In 
    the example you can find labels (plain text), a text box, radio buttons and 
    normal buttons. WIP: List / Tree View widget.
  * If a method exists with the same name as a widget id, it is **automatically 
    bound** to the usually-wanted event (click in case of button, value-changed in 
    case of basically anything else). Oh, and ``close`` and ``quit`` are already 
    there for your convenience.
  * Otherwise, you can retrieve and set the widget's value by using its id like
    a class **attribute**.
    
The ``Toolkit`` classes provide the binding to a certain toolkit. Currently 
there are subclasses for the Qt and tkinter toolkits, the latter being more 
complete.

The created widgets are **"raw", native widgets**. You do not get wrappers; 
instead, the library focuses on specific tasks - building the layout, 
event-/value binding - and lets you do everything else with the API you know and 
(maybe) love.
'''
from .autoframe import AutoFrame
from .toolkit import set_toolkit

__all__ = [
    'AutoFrame',
    'set_toolkit',
    ]
