ASCII Designer
===============

.. toctree::
   :maxdepth: 3
   
   manual
   api

Changelog
---------

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

