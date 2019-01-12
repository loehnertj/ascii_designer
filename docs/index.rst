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
| Label                 | ``blah blah`` (just write plain text) or |
|                       | ``label_id: Text``; or ``.Text`` to      |
|                       | force treatment as text.                 |
+-----------------------+------------------------------------------+
| Button                | ``[  ]`` or ``[Text]`` or                |
|                       | ``[control_id: Text]``.                  |
|                       |                                          |
|                       | (From here on simplified as              |
|                       | ``id_and_text``).                        |
+-----------------------+------------------------------------------+
| Text field            | ``[id_and_text_]`` (single-line), or     |
|                       | ``[id_and_text__]`` (multi-line)         |
+-----------------------+------------------------------------------+
| Dropdown Chooser      | ``[id_and_text v]`` or                   |
|                       | ``[id_and_text (choice1, choice2) v]``   |
+-----------------------+------------------------------------------+
| Combobox              | ``[id_and_text_ v]`` or                  |
|                       | ``[id_and_text_ (choice1, choice2) v]``  |
+-----------------------+------------------------------------------+
| Checkbox              | ``[ ] id_and_text`` or                   |
|                       | ``[x] id_and_text``                      |
+-----------------------+------------------------------------------+
| Radio button          | ``( ) id_and_text`` or                   |
|                       | ``(x) id_and_text``                      |
+-----------------------+------------------------------------------+
| List/Tree view        | ``[= id_and_text]`` or                   |
|                       | ``[= id_and_text (Column1, Column2)]``   |
+-----------------------+------------------------------------------+
| Placeholder (empty or | ``<name>`` for empty box;                |
| framed box)           | ``<name:Text>`` for framed box           |
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

**Listview**: The first column will have the text as heading. The subsequent columns have the given column headings. If Text is empty (or only id given), only the named columns are there. This makes a difference when using value-binding (see below).


Value and event binding
-----------------------

to be done

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

