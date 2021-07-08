
ASCII Designer Manual
=====================

.. default-role:: py:obj

What is this?
-------------

A library that:

 * creates GUI from ASCII-art (with well-defined syntax)
 * maps widgets to virtual class attributes
 * relieves you from the boring parts of Form building while leaving you in 
   control.
 
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

If you like menus, ``f_menu`` can be used for concise definition of menu
structures.

The ``f_icon`` property can be set to the name of an image file to use as window
icon. Note that the supported formats depend on the toolkit and maybe also
operating system.
        
Finally, there is the :any:`f_build()` method, which does the actual form
generation. It calls the :any:`f_on_build` hook, that you might want to
override to initialize controls.

Toolkit
-------

Currently there are implementations for Qt and Tkinter toolkit. You need to
decide which one to use. Before showing the first ``AutoFrame``, use
``set_toolkit(name)`` to set the toolkit.

In particular, ``set_toolkit`` supports:

 * ``"qt"`` for Qt toolkit (using qtpy).
 * ``"tk"`` for Tkinter
 * ``"ttk"`` also for Tkinter, but using ttk-themed widgets wherever possible.

If you use any native methods / properties, e.g. to set text box backgrounds,
obviously changing the toolkit requires changing these parts of your code.


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

Anchoring refers to the positioning and stretching of the widget *within* its 
grid cell.

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
     
Note how tilde character is used as space substitute. This is because trailing 
space is badly visible, and also removed by some text editors automatically. The 
last row shows another possibility by explicitly putting a pipe sign at the end.
  
Vertical anchoring is not controllable. It defaults to "fill", which is the 
right thing most of the time. If not, you can use toolkit-native methods to 
change the anchoring afterwards.


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
 - ``Hello World: |  [  ]`` gives a label with id ``label_hello_world`` and a 
   button with id ``hello_world``
 - ``[ $%&§§% ]`` gives a button with id ``x1`` (assuming this is the first 
   control withoud id).
 
The control id can be used to get/set the control value or the control object 
from the form - see below.

Notes about specific widgets
............................

**Dropdown** and **combobox** without values can be populated after creation.

All **radio buttons** on one form are grouped together. For multiple radio 
groups, create individiual AutoFrames for the group, and embed them in a box.

**Slider**: only supported with horizontal orientation. For a vertical slider, 
change orientation afterwards; or use a placeholder box and create it yourself.

**Listview**: The first column will have the text as heading. The subsequent 
columns have the given column headings. If Text is empty (or only id given), 
only the named columns are there. This makes a difference when using 
value-binding (see below).


Value and event binding
-----------------------

Control objects
...............

Usually you will access your controls from methods in your :any:`AutoFrame` 
subclass. So let us assume that your ``AutoFrame`` variable is called ``self``.

Then, access the generated controls by using ``self["control_id"]`` or 
``self.f_controls["control_id"]``. The result is a toolkit-native widget, i.e. a 
``QWidget`` subclass in Qt case, a ``tkinter`` widget in Tk case.

For Tk widgets, if there is an associated Variable object (``StringVar`` or 
similar), you can find it as ``self["control_id"].variable`` attribute on the 
control.


Event binding
.............

If you define a method named after a control-id, it will be automatically called 
("bound", "connected") as follows:

 * Button: When user clicks the button; without arguments (except for ``self``).
 * Any other widget type: When the value changes; with one argument, being the 
   new value.
 
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

As second option, you can name the method ``on_<control-id>`` (e.g.: 
``on_text_field``). Thus the handler can easily coexist with the virtual value 
attribute (read on).


Virtual value attribute
.......................

If the control is not bound to a function, you can access the value of the control 
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

Boxes are a bit special. An empty box's value is the box widget itself. A framed 
box contains an empty box, which is returned as value.

You can set the virtual attribute to another (any) widget the toolkit 
understands. In this case, the original box is destroyed, and the new "value" 
takes its place. For a framed box, the inner empty box is replaced. So you can 
use the box as a placeholder for a custom widget (say, a graph) that you 
generate yourself.

.. note:: The new widget must have the same parent as the box you replace.

A second possibility is to use the box as parent for one or more widgets that 
you add later. For instance, you can render another AutoFrame into the box. (see 
under Extending).

List / Tree View
----------------

.. note::
    Lists and tree views are considerably more complex than the other widgets. I 
    am still experimenting with how to make handling as convenient as possible. Be 
    prepared for changes here if you update.

The general picture is this: The Listview has a value, which on the python side 
looks mostly like a list. You can slice it, insert/remove items and so on. It is
actually an instance of `ObsList`, which provides "events" for all changes to
the list. Also you can make it into a tree by configuring `children_source` (see below).

There is a toolkit specific adapter between the `ObsList` object and the actual
onscreen widget - the `ListBinding`. It interconnects list and widget events,
and provides the mapping between list item (any object) and column values.

 * With TK/TTk Toolkit, get the binding object by ``self['widgetname'].variable``.
 * With Qt Toolkit, get the binding object by ``self['widgetname'].model()``.

Items are displayed in the list view in textual form. The value list
is attached to the actual list view. I.e. if you update the list, the changes
immediately reflect in the ListView widget.

The value list can become detached if you replace the virtual value while
keeping the old reference somehow.  You can still use it like a normal python
object, but it will not have an onscreen representation anymore. If you attached
own event handlers, take care of detaching them.

The :any:`ListBinding.sources` method of the binding is used to configure how
values are read from the given objects into the predefined columns. By default
we look for attributes matching the column names. If you have a first column
(defined via the "Text", not the "Columns" list in parens), it gets the object's
string representation.

The simplemost way of using the List is this::

    class SimpleList(AutoFrame):
        f_body = '''
            |
             [= Some Items]
        '''
        def f_on_build(self):
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
        def f_on_build(self):
            self.players = [
                RankRow('CaptainJack', 9010, 1),
                RankRow('MasterOfDisaster', 3010, 2),
                RankRow('LittleDuck', 12, 3),
            ]
            # Replacing items triggers updating of the displayed data
            self.players[2] = RankRow('BigDuck', 24, 3)
            # change the data binding:
            self.players.sources(
                    lambda obj: 'ItsLikeMagic',  # unnamed arg: sets the default text (first column)
                    name=['foo'], points=['bar'], # use __getitem__ for those
                    # custom callback
                    rank=lambda obj: obj['baz'], 
            )
            self.players.append({'foo': 'Last', 'bar': -1, 'baz': 4})
            
When working with the list, keep in mind that it **can be changed by user
interaction** (like any other widget's value). E.g. if the user sorts the list
view, the underlying `ObsList` changes order. In case of doubt, make a copy.

Editing
.......

As of v0.4, a list column can be made editable by appending ``_`` (underscore)
to the column caption. Some default shortcuts (``F2``, ``Return``, etc.) apply.

The `ListBinding.sources` setting for the column also determines how edits are processed.

 * If set to a string value, the corresponding property is set.
 * If set to a 1-item list, ``setitem`` is used. I.e. ``object[<name>] = <value>``.
 * If set to a callable, ``fn(obj, val)`` is called.

Especially in the latter case, you will want to split into getter and setter
method. To achieve this, set the source to a 2-tuple of definitions. Example::

    def my_setter(obj, val):
      obj.my_property = float(val)

    self.my_list.binding.sources(my_column=('my_property', my_setter))

reads the value of ``my_column`` by taking ``my_property``, but upon edit,
converts the value to float.

If you use the Tk toolkit, instead of ``ttk.Treeview`` you will get a
`tk_treeedit.TreeEdit` instance. This is a custom Tk widget providing the edit
functionality as well as some more. Please refer to its documentation for details.

The ``add``, ``adchild`` and ``remove`` actions, if permitted, are handled by
the binding. `ListBindingTk` has a ``factory`` property which provides new items
when ``add`` function is used. 

In Qt toolkit, Add / Add Child / Remove functions are currently not provided as
builtin function.

.. note ::
  Differences between Qt and Tk:

  Tk retrieves the "source" values once to build all the list items. Meaning
  that changes in the underlying items do not reflect in the list unless
  explicitly updated. 

  Qt on the other hand queries the items permanently (e.g. on
  mouse-over). This means that changes are immediately visible onscreen, but
  that you should not do complicated calculations or I/O to retrieve column
  values.

  In Tk, a custom editable list widget is provided. In Qt, the native editing
  capabilites are used. 

Trees
.....

**Trees** are created by using the :any:`ObsList.children_source` method, 
which works similar to  `ListBinding.sources`. Here you can define two sources, one
for ``has_children`` (bool) and one for ``children`` (list).

The tree is lazy-loading, i.e. children are only retrieved when a 
node is expanded. On repeated expansion, children are reloaded.

``has_children`` is queried to determine whether expanders should be drawn on 
each item. If not given, we assume that each entry might have children, and they 
all get expanders initially.

The ``children`` property, if retrieved, is again a special list like the "root" one.

.. note::
    If you assign a non-`ObsList` value to a ListView virtual-value, it is
    converted into an `ObsList`. The ``children_source`` is taken over from the
    **previous** value. I.e. you can configure it once and then assign plain
    lists, retaining tree configuration. This is done for your convenience and
    for backward compatibility.

    If on the other hand, you assign an `ObsList` instance as value, it is
    assumed that its `children_source` is already configured, and it won't be
    touched. This is because `children_source` is taken to be part of the
    data-model and not of the GUI binding.

Toolkit-native identifiers
..........................

If you handle toolkit-native events yourself, you will likely need to cope with
"toolkit native" identifiers (TKinter item id or Qt ``QModelIndex``,
respectively). `ObsList` keeps track of the association between toolkit ID and
actual list item for you.

To identify items in the tree, the two methods :any:`ObsList.find` and
:any:`ObsList.find_by_toolkit_id` are provided, which yield container list
and index given the item or its toolkit-native identifier, respectively.

For Tk, the toolkit-native identifier is the ``iid`` value of the tree item.

For Qt it is unset; only ``parent_toolkit_id`` is set to the parent
``QModelIndex``. Given a ``QModelIndex``, its ``internalPointer()`` refers to
the containing list and ``row()`` gives the index of the item.


Menus
-----

Define menus by setting (overriding) the f_menu property of your AutoFrame.
An example menu looks like this::

    f_menu = [
        "File >", ["Open", "Save", "Quit"],
        "Nested >", [
            "Item 1 #C-I",
            "Submenu 1 >", [ "Subitem 1"],
            "Item 2",
        ],
    ]

There are two kinds of menu entries:

 * Normal actions are just simple strings. An identifier is created from the
   text according to the rules above, e.g. ``item_1`` for the text
   ``"Item 1"``. The ``AutoFrame`` **must** have a method of that name and
   without parameters except ``self``. It will automatically be bound to the
   menu entry.
 * If on the other hand the text ends with ``>``, it defines a submenu. The
   next list entry is expected to be a nested list defining the submenu. No
   handler function is bound to the submenu label.

Normal actions can be followed by a shortcut definition introduced by hash
sign ``#``. It can contain any of ``C-``, ``A-``, ``S-`` modifiers followed
by a letter.

For common actions like Open/Save or Cut and Paste, Shortcuts are generated
automatically. Those are defined in :any:`ToolkitBase.default_shortcuts`.
(In :any:`ToolkitQt` this map is overriden to use the ``QKeySequence.X``
defaults).

The menu is generated by the :any:`AutoFrame.f_build_menu` function, which is
called from :any:`f_show`. No menu is built if using :any:`f_build` directly
(since you are most likely embedding the frame). If crucial functionality is
missing because of this, it is your own fault...


Extending / integrating
-----------------------

In any real-world scenario, you will hit the limits of this library pretty soon. Usually it boils down to one of the questions:
    
  - How do I use toolkit-native methods on the widgets?
  - How can I embed generated controls into a "3rd-party" window?
  - How can include "3rd-party" controls in the generated grid?
  
Toolkit-native methods
......................

Having an AutoFrame ``self``, access the toolkit-native controls by using 
``self["control_id"]`` or ``self.f_controls["control_id"]``. Do whatever you 
like with them.

Embedding ``AutoFrame`` into a 3rd-party host window
....................................................

The :any:`AutoFrame.f_build` method takes a parent window as argument. You can 
use this to "render" the AutoFrame into a custom container.

  - The container can be any widget taking children. It must be preconfigured to 
    have a grid layout. I.e. for ``tk`` toolkit, ``.pack()`` must not have been used; in 
    case of ``qt`` toolkit, a ``QGridLayout`` must have been set via ``.setLayout()``.
  - Already-existing children are ignored and left in place. However, row/column 
    stretching is modified.
  - Automatic method / property binding works as usual.
  
Including 3rd-party controls into an ``AutoFrame``
..................................................

This is what the ``<placeholder>`` control is for. It creates an empty Frame / 
Widget / Panel which you can either use as parent, or replace with your own 
control. 

For the former, get the placeholder object (via its value attribute) and use it 
as parent. You must do the layout yourself.

For the latter, set its virtual value attribute to your widget. This 
destroys the placeholder. The layout of the placeholder (Grid position and 
stretching) is copied onto the new widget.

Nesting ``AutoFrame``
.....................

Combining both methods, you can also embed one AutoFrame into another. The 
following example showcases everything::

    class Host(AutoFrame):
        f_body = '''
            |
             <placeholder>
        '''
        def f_on_build(self):
            # self.placeholder.setLayout(QGridLayout()) # only for Qt
            
            # create instance
            af_embedded = Embedded()
            # render widgets as children of self.placeholder
            af_embedded.f_build(parent=self.placeholder)
            # store away for later use    
            self._embedded = af_embedded
            
    class Embedded(AutoFrame):
        f_body = '''
            |
             <another placeholder>
        '''
        def f_on_build(self):
            parent = self.another_placeholder.master
            self.another_placeholder = tk.Button(parent, text='3rd-party control')
            

   
