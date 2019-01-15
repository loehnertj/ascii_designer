ASCII Designer
===============

.. toctree::
   :maxdepth: 2
   :hidden:
   
   self
   api

.. contents::


What is this?
-------------

A library that:

 * creates GUI from ASCII-art (with well-defined syntax)
 * maps widgets to virtual class attributes
 * relieves you from the boring parts of Form building while leaving you in control.
 
The workhorse class is the :any:`AutoFrame`::

    from ascii_designer import AutoFrame
    
The created widgets are **"raw", native widgets**. You do not get wrappers; 
instead, the library focuses on specific tasks - building the layout, 
event-/value binding - and lets you do everything else with the API you know and 
(maybe) love.
    

AutoFrame overview
------------------

:any:`AutoFrame` is used by subclassing it. Then, define the special attribute 
``f_body`` to define the design::

    class MyForm(AutoFrame):
        f_body = '''
            |            |
             Hello World!
              [Close]
        '''

That's it: A working form. Show it by calling :any:`f_show()`. If necessary, it 
will set up an application object and main loop for you; the boilerplate code 
reduces to::

    if __name__ == '__main__':
        MyForm().f_show()
        
You can set the ``f_title`` attribute for a custom window title. Otherwise, your 
class named is turned into a title by space-separating on uppercase characters.
        
Finally, there is the :any:`f_build()` method, which does the actual form 
generation. This is the method to override for custom building and 
initialization code.


Grid slicing, stretching and anchors
------------------------------------

ASCII designer generates grid layouts. The first step of processing ``f_body`` 
is to cut it up into text "cells". Each line of the ``f_body`` string is 
converted into one grid layout row. 

Before processing, leading and trailing whitespace lines are cropped. Also, 
common leading whitespace is removed.

Slicing
.......

The first line is used to define the split
points by means of the pipe character (``|``). The lines below are split exactly 
underneath the pipe signs, IF the respective text-column is either space or pipe 
character. If, on the other hand, any other character is present in that line 
and text-column, a column-spanning cell is created, containing the joint text 
of both cells.

If you want to join but have a space character at this point, you can use the 
tilde ``~`` character instead of the space. It will be converted to space in the 
subsequent processing.

Row-spans are created by prepending the cell content with a brace ``{`` 
character. No matching close-brace is needed. The brace characters must be 
aligned, i.e. exactly above each other.

Stretch
.......

By default, column widths will "shrinkwrap" the content. To make a column 
stretchable, insert one or more minus ``-`` signs in the first line between the 
pipe chars::

    |    -      |             |
     stretches   fixed width
    
If you want it nice-looking, you can make a double arrow like so: 
``<-->``; however to the program only the minus characters count.

If you define multiple stretchable columns, the stretch proportion of each 
column is equal to the number of minus chars above.

Row-stretch is defined similarly. You need to create a special "first 
text-column" by having a pipe char before any content underneath::

 |              |               |
  <- special text-column
  column 1       column 2
  
In this text-column, put a capital ``I`` before rows that you want to stretch.
Stretch proportion is equal for all stretchable rows. Use row-span to have some 
widgets stretch more than others vertically.

Anchoring
.........

Anchoring refers to the positioning and stretching of the widget *within* its grid cell.

Horizontal anchoring of widgets within the grid cell is controlled by whether 
the text is space-padded at the beginning and/or end of its text cell:

 * No space at beginning nor end makes the widget full-width.
 * Space at only beginning gives right-, at end gives left-align.
 * Space at both begin and end gives center alignment.
 
In graphical form::

 |                |
   Alignment:
  [Fill          ]
  [Left]         ~
           [Right]
     [Center]    ~
   [also center ] |
     
Note how tilde character is used as space substitute. This is because trailing space is badly visible, and also removed by some text editors automatically. The last row shows another possibility by explicitly putting a pipe sign at the end.
  
Vertical anchoring is not controllable. It defaults to "fill", which is the right thing most of the time. If not, you can use toolkit-native methods to change the anchoring afterwards.


Widget specification
--------------------

+-----------------------+------------------------------------------+
| To create a:          | Use the syntax:                          |
+=======================+==========================================+
| Label                 | | ``blah blah`` (just write plain text), |
|                       | | ``label_id: Text`` or                  |
|                       | | ``.Text``                              |
+-----------------------+------------------------------------------+
| Button                | | ``[  ]`` or                            |
|                       | | ``[Text]`` or                          |
|                       | | ``[control_id: Text]``.                |
|                       | | (From here on simplified as            |
|                       |   ``id_and_text``).                      |
+-----------------------+------------------------------------------+
| Text field            | | ``[id_and_text_]`` (single-line) or    |
|                       | | ``[id_and_text__]`` (multi-line)       |
+-----------------------+------------------------------------------+
| Dropdown Chooser      | | ``[id_and_text v]`` or                 |
|                       | | ``[id_and_text (choice1, choice2) v]`` |
+-----------------------+------------------------------------------+
| Combobox              | | ``[id_and_text_ v]`` or                |
|                       | | ``[id_and_text_ (choice1, choice2) v]``|
+-----------------------+------------------------------------------+
| Checkbox              | | ``[ ] id_and_text`` or                 |
|                       | | ``[x] id_and_text``                    |
+-----------------------+------------------------------------------+
| Radio button          | | ``( ) id_and_text`` or                 |
|                       | | ``(x) id_and_text``                    |
+-----------------------+------------------------------------------+
| Slider (horizontal)   | | ``[id: 0 -+- 100]``                    |
+-----------------------+------------------------------------------+
| List/Tree view        | | ``[= id_and_text]`` or                 |
| (only in Tk for now)  | | ``[= id_and_text (Column1, Column2)]`` |
+-----------------------+------------------------------------------+
| Placeholder (empty or | | ``<name>`` for empty box;              |
| framed box)           | | ``<name:Text>`` for framed box         |
+-----------------------+------------------------------------------+

Control ID
..........

Each control gets an identifier which is generated as follows:

 - If a control id is explicitly given, it has of course precedence.
 - Otherwise, the control Text is converted to an identifier by
 
    - replacing space with underscore
    - lower-casing
    - removing all characters not in (a-z, 0-9, ``_``)
    - prepending ``x`` if the result starts with a number.
    - Special-Case: Labels get ``label_`` prepended.
    
 - If that yields no ID (e.g. Text is empty), the ID of a preceding Label 
   (without ``label_`` prefix) is used. This requires the label to be *left* of the 
   control in question.
 - If that fails as well, an ID of the form ``x1``, ``x2``, ... is assigned.

Examples:

 - ``[ Hello ]`` gives id ``hello``
 - ``[ Hello World! ]`` gives id ``hello_world``
 - ``Hello World: |  [  ]`` gives a label with id ``label_hello_world`` and a button with id ``hello_world``
 - ``[ $%&§§% ]`` gives a button with id ``x1`` (assuming this is the first control withoud id).
 
The control id can be used to get/set the control value or the control object from the form - see below.

Notes about specific widgets
............................

**Dropdown** and **combobox** without values can be populated after creation.

All **radio buttons** on one form are grouped together. For multiple radio groups, create individiual AutoFrames for the group, and embed them in a box.

**Slider**: only supported with horizontal orientation. For a vertical slider, 
change orientation afterwards; or use a placeholder box and create it yourself.

**Listview**: The first column will have the text as heading. The subsequent columns have the given column headings. If Text is empty (or only id given), only the named columns are there. This makes a difference when using value-binding (see below).


Value and event binding
-----------------------

Control objects
...............

Usually you will access your controls from methods in your :any:`AutoFrame` 
subclass. So let us assume that your ``AutoFrame`` variable is called ``self``.

Then, access the generated controls by using ``self["control_id"]`` or 
``self.f_controls["control_id"]``. The result is a toolkit-native widget, i.e. a 
``QWidget`` subclass in Qt case, a ``tkinter`` widget in Tk case.

For Tk widgets, if there is an associated Variable object (``StringVar`` or similar), you can find it as ``self["control_id"].variable`` attribute on the control.


Event binding
.............

If you define a method named after a control-id, it will be automatically called ("bound", "connected") as follows:

 * Button: When user clicks the button; without arguments (except for ``self``).
 * Any other widget type: When the value changes; with one argument, being the new value.
 
Example::

    class EventDemo(AutoFrame):
        f_body = '''
            |               |
             [ My Button   ]
             [ Text field_ ]
        '''
        def my_button(self):
            print('My Button was clicked')
        
        def text_field(self, val):
            print('Text "%s" was entered'%val)
            
In case of the ListView, the method is called on selection (focus) of a row.


Virtual value attribute
.......................

If the control is not bound to a function, you can access the value of a control 
by using it like a class attribute::

    class AttributeDemo(AutoFrame):
        f_body = '''
            |               |
             [ Text field_ ]
        '''
        def some_function(self):
            x = self.text_field
            self.text_field = 'new_text'

For label and button, the value is the text of the control.

Boxes are a bit special. An empty box's value is the box widget itself. A framed box contains an empty box, which is returned as value.

You can set the virtual attribute to another (any) widget the toolkit understands. In this case, the original box is destroyed, and the new "value" takes its place. For a framed box, the inner empty box is replaced. So you can use the box as a placeholder for a custom widget (say, a graph) that you generate yourself.

.. note:: The new widget must have the same parent as the box you replace.

A second possibility is to use the box as parent for one or more widgets that 
you add later. For instance, you can render another AutoFrame into the box. (see under Extending).

Value of  List / Tree View
...........................

.. note::
    Lists and tree views are considerably more complex than the other widgets. I am still experimenting with how to make handling as convenient as possible. Be prepared for changes here if you update.

The general picture is this: The Listview has a value, which on the python side looks mostly like a list. You can slice it, insert/remove items and so on.

However, inserted items are turned into :any:`Node` instances fit for displaying in the list view. 
The value list is attached to the actual list view. I.e. if you update the list or its items, the changes immediately reflect in the ListView widget.

The value list or its items can become detached if you replace the list or pop nodes of it. You can still use it like a normal python object, but it will not have an onscreen representation anymore.

The :any:`sources` method of the list can be used to configure how values are read from the given objects into the predefined columns. By default we look for attributes matching the column names. If you have a first column (defined via the "Text", not the "Columns" list in parens), it gets the object's string representation.

That means that the simplemost way of using the List is this::

    class SimpleList(AutoFrame):
        f_body = '''
            |
             [= Some Items]
        '''
        def f_build(self, parent, body):
            super().f_build(parent, body)
            # populate the list
            self.some_items = ['First', 'Second', 'Fifth']

            
A more complex example to showcase how additional columns work::

    # RankRow is a stand-in for a "real" class.
    RankRow = namedtuple('RankRow', 'name points rank')
    
    class TreeDemo(AutoFrame):
        f_body = '''
        |              <->                |
        I[= Players (,Name, Points, Rank)]
        '''
        def f_build(self, parent, body):
            super().f_build(parent, body)
            self.players = [
                RankRow('CaptainJack', 9010, 1),
                RankRow('MasterOfDisaster', 3010, 2),
                RankRow('LittleDuck', 12, 3),
            ]
            # changing columns / items triggers updating of the displayed data
            self.players[1]['name'] = 'Changed Name'
            self.players[2] = RankRow('BigDuck', 24, 3)
            # change the data binding:
            self.players.sources(
                    name=['foo'], points=['bar'], # use __getitem__ for those
                    # custom callback
                    rank=lambda obj: obj['baz'], 
                    # change binding for first ("default") column
                    **{'': lambda obj:'ItsLikeMagic'}
            )
            self.players.append({'foo': 'Last', 'bar': -1, 'baz': 4})


Extending / integrating
-----------------------

to be done

   
Developers
----------

The project is located at https://github.com/loehnertj/ascii_designer

This is a hobby project. If you need something quick, contact me or better, send a pull request.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

