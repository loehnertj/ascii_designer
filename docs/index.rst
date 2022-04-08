ASCII Designer
===============

.. toctree::
   :maxdepth: 3
   
   manual
   api

Changelog
---------

 * v0.5.0:

   * TK/TTK: Add ``GenericVar`` supporting automatic conversion and
     validated-hook; opt-in automatic update of control's invalid state.
     See :ref:`generic-var`
   * introduce ``Toolkit.widget_classes`` attribute, allowing injection of
     custom widget subclasses
   * export ``EventSource``, ``CancelEvent``, ``Invalid``, ``nullable``,
     ``gt0``, ``ge0``  on package-level

 * v0.4.4:
 
   * Fix edit-widget placement issues in Tk Treeedit
   * Treeedit subwidgets are now ttk (i.e. stylable)
   * Treeedit ``autoedit_added`` property
   * Fix icon "inheritance" on Windows

 * v0.4.3:
   
   * Fix ``f_icon`` not working on Windows (with ``.ico`` files).
   * Tk (choice only) dropdown: fire event immediately on selection, not on
     ``FocusOut`` / ``Return`` press
   * Change virtual-value handling of placeholders. Placeholder "remembers" and
     returns what was assigned to it. Also, when assigned an unbuilt AutoFrame
     instance, it will automatically build it, reducing boilerplate for the
     typical embedding case.

 * v0.4.2:
   
   * Fix 2 issues in ListBindingTk related to editable lists.

 * v0.4.1:

   * Make tk_treeedit key bindings a class property (list) that can be modified.
     Fix crash on Windows due to nonexisting Keysym.

 * v0.4.0:

   * Refactor internal implementation of List Binding. Architecture simplified
     to `ObsList` (data model) and `ListBinding` classes.
   * Add basic editing capabilites to List / Tree view.

 * v0.3.4:

   * Add ``setup_style`` parameter to `ToolkitTk` for custom style setup
   * Fix #6: for some Tk controls, value change via code would trigger the
     control's autoconnected handler.

 * v0.3.3:

   * Qt now depends on qtpy, not PyQt4 anymore.
   * :py:obj:`set_toolkit` can set Options. Add ``font_size`` and ``ttk_theme``
     option for Tkinter.
   * Can set window icon by f_icon property

 * v0.3.2: 

   * Add "ttk" toolkit (which is actually :any:`ToolkitTk` with a new option). YMMV.
   * Add :any:`f_on_build` and :any:`f_on_show` hooks
   * Fix several bugs in control parser, esp. concerning labels.
   
 * v0.3.1: Qt Toolkit menu accelerators
 * v0.3.0: menus added (TBD: accelerators for Qt menus); fix Qt List crash
 * v0.2.0: rework of the list model

Developers
----------

The project is located at https://github.com/loehnertj/ascii_designer

This is a hobby project. If you need something quick, contact me or better, send 
a pull request.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

