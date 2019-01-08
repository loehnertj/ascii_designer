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

to be done

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

