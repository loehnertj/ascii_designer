"""This is part example collection, part regression test."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).with_name("src")))

# import tkinter as tk
from ascii_designer import ObsListProperty
from ascii_designer.tk_treeedit import TreeEdit
import logging
import sys
import random
import time
from ascii_designer import (
    AutoFrame,
    set_toolkit,
    nullable,
    ge0,
    Invalid,
    load_translations_json,
    save_translations_json,
)


# Idea for later
toolbar = """
 [ Open ]
 [ Save ]
 [ Save as... ]
"""


class Main(AutoFrame):
    """Main demonstration menu for Ascii Designer examples.
    
    Click the buttons to launch different demo windows. Each button click opens
    a new frame with specific feature demonstrations.
    """
    f_title = "Ascii Designer Demo Menu"
    f_body = """
    |    <->                     |
     - ASCII Designer Demo Menu -
     [Autoconnect               ]
     [Boxes and embedding       ]
     [Subgrids                  ]
     [Bound values              ]
     [Custom subclass           ]
     [Converters                ]
     [List view                 ]
     [List edit                 ]
     [Tree view                 ]
     [Alignment                 ]
     [Window Menu               ]
    I
       [Close]                   |
    """
    f_icon = "ascii_designer_icon.png"

    def autoconnect(self):
        AutoconnectDemo().f_show()

    def boxes_and_embedding(self):
        BoxesDemo().f_show()

    def subgrids(self):
        SubgridsDemo().f_show()

    def bound_values(self):
        BoundCtlDemo().f_show()

    def custom_subclass(self):
        if TK not in ("tk", "ttk"):
            print("Only works under Tkinter, sorry")
        else:
            CustomSubclassDemo().f_show()

    def converters(self):
        if TK not in ("tk", "ttk"):
            print("Only works under Tkinter, sorry")
        else:
            ConvertersDemo().f_show()

    def list_view(self):
        ListDemo().f_show()

    def list_edit(self):
        ListEditDemo().f_show()

    def tree_view(self):
        TreeDemo().f_show()

    def on_alignment(self):
        AlignmentDemo().f_show()

    def window_menu(self):
        MenuDemo().f_show()


class AutoconnectDemo(AutoFrame):
    """Demonstrates automatic widget connection and event handling.
    
    Shows all basic widget types (labels, buttons, text fields, dropdowns, options,
    checkboxes, sliders) with automatic data binding. The user can:

    - Enter text in text fields;
    - Select options from dropdowns and combo boxes;
    - Toggle checkbox and radio buttons;
    - Drag sliders;
    - Click the "Press me" button;
    - Type in the dynamically added text field.

    In each case, the respective method of the class is called, and the current
    value of the control is printed to the console.

    The "Press Me" button demonstrates dynamic UI modification by adding a new text field when clicked. The new field is automatically connected to the on_write_here handler.
    """
    f_body = """
                       |      <->
        Label:          This is a label
        Button:         [ Press me ]
        
        Multiline:      [ foo__ ]
        Dropdown:       [ Choose (Red,Green,Blue) v]
        Dropdown empty: [ v ]
        Combo:          [ Color_ (Red,Green,Blue) v]
        Option:         ( ) Option A
                        (x) Option B
                        - checkbox below should be centered,
                        - longest line in the layout:
        Checkbox:       [x] agree:I agree to the terms and conditions.
        Slider:         [ slider: 0 -+- 100 ]
                        this appears twice
                        this appears twice
        """

    def f_on_build(self):
        # How to use custom translations.
        # Use .get(key, default) to retrieve translations! Required if you want
        # to have .recording and .mark_missing work properly.
        prefix = "Color."
        tr = self.f_translations.get
        self["choose"]["values"] = [
            tr(prefix + value, value) for value in self["choose"]["values"]
        ]
        self["color"]["values"] = [
            tr(prefix + value, value) for value in self["color"]["values"]
        ]

    def close(self):
        print("Closing now.")
        super().close()

    def press_me(self):
        print("press_me was pressed")
        row_3 = """
                  |
        Text box:  [ Write here_ ]
        """
        self.f_add_widgets(self[""], body=row_3, offset_row=2)

    def on_write_here(self, text):
        print('write_here: "%s" / "%s"' % (text, self.write_here))

    def foo(self, text):
        print('foo: "%s"' % text)

    def on_choose(self, val):
        """use on_<attr> if you want to be able to retrieve the auto-value as
        well.
        """
        print('choose: "%s" / "%s"' % (val, self.choose))

    def dropdown_empty(self, val):
        print("dropdown_empty: %r" % (val,))

    def color(self, val):
        print('color: "%s"' % val)
        print('foo: "%s"' % self.foo)

    def option_a(self, checked=True):
        print("option_a %s" % checked)

    def option_b(self, checked=True):
        print("option_b %s" % checked)

    def agree(self, checked):
        print("agree: %s" % checked)

    def slider(self, val):
        print("slider: %s" % val)


class BoxesDemo(AutoFrame):
    """Demonstrates boxes, group boxes, and widget embedding.
    
    Shows how to use placeholder elements and replace them with custom widgets
    or nested AutoFrame instances. 
    
    ``<box>`` and ``<groupbox: Test >`` are placeholders that can be filled with
    any widget. ``<box>`` (without label) is replaced entirely by a button in
    code, and ``<groupbox: Test >`` is filled with another button. 

    ``<nest_box:...>`` is used to embed another autoframe (in the example,
    BoxesDemo itself) recursively. Note that the ``AutoFrame`` is built
    automatically when assigned to the placeholder.
    
    Also note that the buttons are not bound to a handler automatically.
    """
    f_body = """
        |               |  <->
         Use the source code to understand what is demonstrated here.
         Box:            <box>
        IGroup box:      <groupbox: Test >
        INesting:        <nest_box:Turtles all the way down>
        
    """

    def __init__(self, level=2):
        super().__init__()
        self._level = level

    def f_on_build(self):
        # Replace placeholder with a label
        if TK in ("tk", "ttk"):
            bm = self.box.master
            gbm = self.groupbox.master
        elif TK == "qt":
            bm = self.box.parent()
            gbm = self.groupbox.parent()
        b = self.box = self.f_toolkit.button(parent=bm, text="this replaces box")
        # placeholder "value" is now the new widget
        assert self.box is b
        self.groupbox = self.f_toolkit.button(parent=gbm, text="this fills groupbox")

        # Nesting
        if self._level:
            self.nest_box = BoxesDemo(self._level - 1)

    # This is illegal and causes TypeError when building. You cannot have a
    # handler for a placeholder. If you create the widgets yourself, you must
    # also do the event binding yourself.
    #def on_box(self): ...


class SubgridsDemo(AutoFrame):
    """Demonstrates nested sub-layouts with subgrids.
    
    Shows how to define complex layouts by organizing widgets into separate
    subgrid sections defined with :id: markers. 

    Start subgrids by :id: line.

    The subgrid is built into the placeholder in the main grid frame
    with the same id.

    The buttons do nothing. Their purpose is only to visually outline the
    created layout.
    """

    f_body = """
        |  -
         <normal_frame          >
        I<gb_frame:In groupbox  >

        :normal_frame:
        |  -
         [Top button   ]
         [Bottom button]

        :gb_frame:
        |      -      |
         [Left Button] [Right Button]
        I<s: V Fill  >
    """


class AlignmentDemo(AutoFrame):
    """Demonstrates row/column stretching and widget alignment.
    
    Shows how column width and row height stretch, and how widgets align within cells.
    The user can resize the window. 
    
    * Stretching columns (``-`` in header) expand proportionally to fill
      horizontal space. Proportion is equal to number of ``-`` signs. I.e. first
      column is not stretched, second column is stretched 1x, third column is
      stretched 2x.
    * Stretching rows (``I`` underneath first pipe symbol) expand proportionally
      to fill vertical space. Proportion is equal for all rows with ``I``.
    * ``left``, ``center`` and ``right`` buttons have the respective horizontal
      alignment within their cells.
    * Widgets are always "fill"-aligned vertically, meaning they will expand to
      fill the cell height.
    * The ``colspan_stretch_3x`` textarea spans over second and third grid column.
    * The ``left_v_2x`` textarea spans over fourth and fifth row of the grid.

    The buttons do nothing. Their purpose is only to visually outline the
    created layout.
    """

    f_body = """
    |              |     <->          |   <-->         |
     [fixed col   ] [  stretch 1x    ] [stretch 2x    ]
                    [ colspan stretch 3x              ]
    I               [ stretch h+v __ ]|[left]          |
    I               {[left, v 2x __ ] |  [center]      |
    I               {                           [right]|
    """

    def f_on_build(self):
        if TK == "qt":
            from qtpy.QtWidgets import QSizePolicy

            # Qt: -> Rowspan seems to not play well with RowStretch. The buttons must be
            # set to Expanding to make the RowStretch work.
            self["center"].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self["right"].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


class BoundCtlDemo(AutoFrame):
    """Demonstrates data binding and value retrieval for all standard widget types.
    
    Shows all widget types (text, multiline text, dropdown, combo box, radio buttons,
    checkbox, slider) with data binding. The user can:

    - Modify any control, which does not cause any immediate action
    - Click "Get all" to print all current values to the console
    - Click "Set all" to programmatically set all values; the UI updates to display
      the new values:
         - Textbox is set to "text"
         - Multiline is set to "more<newline>text"
         - Dropdown is set to "Green"
         - Combo box is set to "Shade of grey"
         - Option B is selected, Option A is deselected
         - Checkbox is unchecked
         - Slider is set to 50
    """

    f_body = """
    |               |  <->                                            ~
     Textbox:        [ _ ]
     Multiline:      [ __ ]
     Dropdown:       [ Choose (Red,Green,Blue) v]
     Combo:          [ Color_ (Red,Green,Blue) v]
     Option:         ( ) Option A
                     (x) Option B
     Checkbox:       [x] agree:I agree to the terms and conditions.
     Slider:         [ slider: 0 -+- 100 ]
    I
     [Get all]       [Set all]
    """

    bind_names = "textbox multiline choose color option_a option_b agree slider".split(
        " "
    )

    def set_all(self):
        self.textbox = "text"
        self.multiline = "more\ntext"
        self.choose = "Green"
        self.color = "Shade of grey"
        self.option_b = True  # FIXME for tk toolkit, must set 'option_b'
        self.agree = False
        self.slider = 50

    def get_all(self):
        for name in self.bind_names:
            print("%s: %s" % (name, getattr(self, name)))


class CustomSubclassDemo(AutoFrame):
    """Demonstrates custom widget subclasses with specialized properties.

    
    Shows how to create custom widget classes that extend standard widgets with
    custom behavior. Here, a custom ``Entry`` subclass is used instead of the
    standard one.
    
    The user can:

    - Enter numeric values in the custom entry field; values are validated and
      formatted as floats
    - If input is invalid, the field displays an error state
    - The converted value is formatted as float with 3 decimals in the UI
    - Click "reset" to set the field to a predefined value; the display updates

    ``on_custom_entry_field`` and ``on_reset`` handlers show that the widget
    (``self["custom_entry_field"]``) is indeed an instance of the custom
    subclass.
    """
    f_body = """
    |                    |
     Please see the source code to understand what happens here.
     Custom entry field:  [_      ]
     Converted value:     conv_value
                          [reset]
    """
    import tkinter.ttk as ttk

    class MyEntry(ttk.Entry):
        @property
        def float_value(self):
            v = None
            try:
                v = float(self.variable.get())
            except:
                self.state(["invalid"])
            else:
                self.state(["!invalid"])
            return v

        @float_value.setter
        def float_value(self, val):
            self.variable.set(f"{val:0.3f}")
            self.state(["!invalid"])

    def __init__(self):
        super().__init__()
        self.f_toolkit.widget_classes["textbox"] = self.MyEntry

    def on_custom_entry_field(self, text):
        # access the special float_value property of our field
        fval = self["custom_entry_field"].float_value
        if fval is None:
            self.label_conv_value = "<invalid>"
        else:
            # format as engineering number
            self.label_conv_value = f"{fval:e}"

    def on_reset(self):
        # Note how the last digits will be cut off by the format in the setter
        self["custom_entry_field"].float_value = 1.2345678
        self.on_custom_entry_field(None)


class ConvertersDemo(AutoFrame):
    """Demonstrates value conversion and validation for different data types.
    
    Shows how converters transform input strings into typed values with validation.
    The user can:
    - Enter values in the float, int, and in-list fields; invalid entries are rejected
    - Click "test" to validate all inputs;  ``label_result`` text indicates if
      all are valid.
    - For the ``instant`` field, validation also happens upon press of return and on focus loss.
    - If all values are valid, output fields display the float value (``a``) in two different
      formats (scientific notation and fixed-point), to prove that the value was understood as number.
    """
    f_option_tk_autovalidate = True
    f_body = """
                 |
         Float:   [ _           ]
         Int:     [ _           ]
         in-list: [_ (a, b, c) v]
         instant: [ _           ]
                  [test]
                  result
         output1: [ _           ]
         output2: [ _           ]
    """

    def f_on_build(self):
        self.label_result = ""
        self["float"].variable.convert = nullable(float)
        self["int"].variable.convert = ge0(int)

        def isinlist(val):
            if val not in ["a", "b", "c", "d"]:
                raise ValueError()
            return val

        self["inlist"].variable.convert = isinlist
        self["instant"].variable.convert = float
        # display the same value in different formats
        # Note that you will lose precision by this. Same effect as if you rounded.
        self["output1"].variable.convert_set = lambda x: f"{x:0.1e}"
        self["output2"].variable.convert_set = lambda x: f"{x:3.3f}"

    def on_instant(self, val):
        # on call of the handler, variable is retrieved and validation happens.
        # Nothing more required.
        pass

    def test(self):
        a = self.float
        b = self.int
        c = self.inlist
        d = self.instant
        if Invalid in [a, b, c, d]:
            self.label_result = "some input is invalid"
        else:
            self.label_result = "setting outputs"
            self.output1 = a if a is not None else 99.0
            self.output2 = a if a is not None else 99.0


class RankRow:
    def __init__(self, name, points, rank, is_cheater=False):
        self.name = name
        self.points = points
        self.rank = rank
        self.is_cheater = is_cheater

    def __str__(self):
        return f"{self.name} - {self.rank}"

    def __repr__(self):
        return f"RankRow(name={self.name!r}, points={self.points!r}, rank={self.rank!r}, is_cheater={self.is_cheater!r})"


class ListDemo(AutoFrame):
    """Demonstrates list views with simple items and structured data rows.
    
    Shows two lists: one with simple strings (`shopping_list`) and one with custom objects displayed
    in multiple columns (`players`). 
    
    In `shopping_list`, the user can:

    - Click items to select them
    - Toggle "reorder checkbox" to enable/disable drag-and-drop reordering of ``shopping_list``
    - If reordering is enabled: Drag and drop items in `shopping_list` to
      reorder them. (Not demonstrated: Drag-and-drop reordering immediately
      updates the underlying list order, which can be observed by printing the
      list after reordering.)
    - Click items of ``shopping_list`` to focus and see selection printed to console

    In `players`, the user can:

    - Click column headings to sort by that column ascending or descending (second click)
    - Click "Add" to insert a random new player at a random position
    - Click "Replace" to replace selected players with new ones
    - Click "Mutate" to change selected player names (mutate the underlying
      object); changes appear immediately
    - Click "Remove" to delete selected items from the list
    - Click "resort" to restore the last sorting (e.g. after adding new items)
    - Click "unsort" to apply custom sorting by object ID (demonstrating
      application of the standard python sorting mechanism)

    In the `_populate_players` method, we can see how the columns are attached
    to object properties in three ways:

    - by callback function ``fn(obj) -> value`` (e.g. for "name" column)
    - by index access ``["name"]``
    - by property name ``"name"``
    """
    f_body = """
    |             |     |         |        |<->     |        |         |
    |Simple List   List with named~columns~~        
    I[= Shopping ] [= Players  (Name, Points, Rank) ~        ~        ]
     [ ] reorder   [Add] [Replace] [Mutate] [Remove] [resort] [unsort]                 
    """

    shopping: ObsListProperty[str]
    players: ObsListProperty[RankRow]

    def f_on_build(self):
        print(list(self.f_controls.keys()))
        self.shopping = ["Cabbage", "Spam", "Salmon Mousse", "Fish"] * 5
        if TK != "qt":
            self["shopping"].variable.allow_sorting = False
        else:
            self["shopping"].model().allow_sorting = False
        self._populate_players()

    def _populate_players(self):
        self.players = [
            RankRow("CaptainJack", 9010, 1),
            RankRow("MasterOfDisaster", 3010, 2),
            RankRow("LittleDuck", 12, 3),
        ]
        self.players[1].name = "Changed Name"
        # Notify listview about mutated item
        self.players.item_mutated(self.players[1])
        self.players[2] = RankRow("BigDuck", 44, 3)
        self.players.sources(
            lambda obj: "ItsLikeMagic", name=["name"], points=["points"], rank=["rank"]
        )
        # not recommended but possible: mixed item types
        # If you need a heterogenous list, the recommended pattern is to use
        # items with a common base class, which provides a consistent interface.
        # If necessary, define wrapper classes for the original data.
        self.players.append({"name": "Last", "points": -1, "rank": 4})
        # Don't do this: redefining sources differently for the same list. This
        # will break on items already in the list, if they don't have the
        # required properties.
        self.players.sources(name="name", points="points", rank="rank")

    def on_reorder(self, val):
        if TK != "qt":
            self["shopping"].variable.allow_reorder = val

    def add(self):
        p = RankRow(
            "new%d" % (random.randint(1, 1000)), points=random.randint(1, 999), rank=9
        )
        idx = random.randint(0, len(self.players))
        self.players.insert(idx, p)
        # sorting needs to be restored explicitly
        self.players.sort(restore=True)
        # Also possible; however causes reload of the whole list (since replaced by new list)
        # self.players += [p]

    def replace(self):
        for item in self.players.selection:
            idx = self.players.index(item)
            p = RankRow(
                "replaced-%d" % (random.randint(1, 1000)),
                points=random.randint(1, 999),
                rank=9,
            )
            self.players[idx] = p

    def mutate(self):
        for item in self.players.selection:
            item.name = "changed%d" % random.randint(1, 1000)
            self.players.item_mutated(item)

    def remove(self):
        nodes = self.players.selection[:]
        for node in nodes:
            self.players.remove(node)

    def resort(self):
        self.players.sort(restore=True)

    def unsort(self):
        """apply a regular python sorting, e.g. by item id"""
        self.players.sort(key=lambda item: id(item))

    def on_shopping(self, item):
        print("Buy: ", item)


class ListEditDemo(AutoFrame):
    """Demonstrates in-place editing of list items with multiple columns.
    
    Shows an editable list view with player data where users can modify individual
    cells. The user can:

    - Doubleclick values in the ``name``, ``value``  columns to edit its value in-place
    - Doubleclick the ``is_cheater`` column to toggle the boolean value
    - Enter new values for name, points, or cheater status
    - Press Enter to confirm the edit; the list updates and console shows the change
    - Add new rows using the "Add" button included in the list view
    - Delete rows using the "Remove" button included in the list view
    - use various key bindings for navigation and editing: `F2` to edit,
      `Delete` to remove, `Insert` to add new row, `Tab` and `Shift+Arrow-key` to
      move between editable cells - see `TreeEdit` documentation for all details.

    Whenever an item is changed, a message is printed to the console showing the changed item. 
    
    Additionally, changed values trigger automatic rank recalculation, which
    updates the rank column.

    Note that due to the complexity of the topic, we need some Tk and Qt
    specific code in the implementation.
    """
    f_body = """
        | -
        I[= Players (Name_, Points_, Is_Cheater?, Rank)]
    """

    players: ObsListProperty[RankRow]

    def f_build(self, parent, body=None):
        super().f_build(parent, body)
        tv = self["players"]
        # Configure treeviews, takes some toolkit-specific code
        if isinstance(tv, TreeEdit):
            # tk / ttk toolkit (ie. ascii_designer.tk_treeedit.TreeEdit widget)
            tv.allow = "add, remove"
            # binding is ascii_designer.ListBindingTk
            binding = tv.variable

            # Source setup: name, rank columns are already fine. Configure points to read points property as-is & store int(edited_value).
            def setpoints(obj, val):
                obj.points = int(val)

            def set_ic(obj, val):
                # ? suffix makes bool column 
                assert isinstance(val, bool)
                obj.is_cheater = val

            binding.sources(
                points=("points", setpoints), is_cheater=("is_cheater", set_ic)
            )
        else:
            # qt toolkit (i.e. QTreeView)
            # binding is ascii_designer.ListBindingQt
            binding = tv.model()

            # Sources need not be configured. Qt handles varying datatype just fine.

        binding.factory = lambda: RankRow("", 0, 0)

        # init list
        self.players = [
            RankRow("CaptainJack", 9010, 1),
            RankRow("MasterOfDisaster", 3010, 2),
            RankRow("LittleDuck", 12, 3),
        ]
        # attach our own listeners for change events.
        # Preferably use the ObsList's events for this. This way you will not
        # only catch GUI-triggered but also externally induced changes.
        self.players.on_replace += self._print_change
        self.players.on_replace += self._check_recalc_ranks_ol
        # FIXME: flag against infinite recursion, this smells
        self._in_check_recalc = False

    def _print_change(self, toolkit_id, item):
        if not self._in_check_recalc:
            print("Item changed:", repr(item))

    def _check_recalc_ranks_ol(self, toolkit_id, item):
        if self._in_check_recalc:
            # _check_recalc_ranks triggers item_mutated again. Prevent infinite recursion.
            return
        self._in_check_recalc = True
        try:
            self._check_recalc_ranks()
        finally:
            self._in_check_recalc = False

    def _check_recalc_ranks(self):
        print("Autoupdate rank column")
        i = 1
        for row in sorted(self.players, key=(lambda row: row.points), reverse=True):
            # Note that we are not doing anything with the GUI object here. Just
            # updating a regular old Python object. Then we just tell the list "I changed this item".
            row.rank = i
            self.players.item_mutated(row)
            i += 1


class TreeDemo(AutoFrame):
    """Demonstrates tree views with lazy-loading file system navigation.
    
    Shows a navigable file tree starting from the user's home directory. The user can:

    - Expand folders by clicking the expansion arrow; children are loaded from disk.
      Loading is delayed by ~1 second per folder to simulate real data retrieval.
    - Collapse expanded folders; the tree structure is preserved
    - Reexpanding a previously collapsed folder does not trigger reloading;
      children are cached
    - Click items to focus them; selection is printed to console
    - Edit the "Remark" column for any item; remarks are stored in the remarks dict
    - Click "Test Find" to locate a selected item in the tree and retrieve it
      (demonstrate find2 method and index retrieval)
    - Toggle between expanded/collapsed states multiple times
    """
    f_body = """
    |  <-> Tree       
     Tree~
    I[= Files:File (Remark_) ]
     [ Test Find ]
    """
    files: ObsListProperty[Path]

    def __init__(self):
        super().__init__()
        self.remarks: dict[Path, str] = {}

    def f_on_build(self):
        # To test event spillout from tree-edit
        try:
            self[""].bind("<Return>", lambda ev: print("Return-press detected"))
            self[""].bind("<Escape>", lambda ev: self.close())
        except:
            pass

    def f_on_show(self):
        self._populate_folder()

    def _populate_folder(self):
        import pathlib

        def children_of(fld):
            print("Now retrieving children of %s, wait 1second" % (fld,))
            time.sleep(1.0)
            for item in fld.iterdir():
                if not item.name.startswith("."):
                    yield item

        def has_children(fld):
            # print('Has children?: %s'%(fld,))
            if not fld.is_dir():
                return False
            try:
                next(fld.iterdir())
            except StopIteration:
                return False
            return True

        # set the attribute or method which retrieves the iterable of children
        self.files.children_source(children_of, has_children_source=has_children)

        def setremark(path: Path, text: str):
            self.remarks[path] = text

        self.files.sources(remark=(lambda path: self.remarks.get(path, ""), setremark))
        # use a generator to set folder
        self.files = children_of(pathlib.Path.home())

    def on_files(self, item):
        print("focus", item)
        print("selection", self.files.selection)

    def test_find(self):
        item = self.files.selection[0]
        print("Find", item)
        idx = self.files.find2(item)
        print("Result:", idx)
        print("retrieving it back:", self.files[idx])
        sib_idx = idx[:-1] + (None,)
        print("which is contained in:", self.files[sib_idx])


class MenuDemo(AutoFrame):
    """Demonstrates menu bar handling with nested menus and keyboard shortcuts.
    
    Shows a complete menu structure with File, Nested, and Help categories. Look in the code to see how menu items and submenus are defined.

    The user can:
    - Click menu items to trigger actions; actions are printed to console
    - Use keyboard shortcuts (e.g., Ctrl+I, Ctrl+Shift+I, F1) to invoke menu items
    - Navigate nested submenus
    - Select "Quit" to close the window
    """
    f_menu = [
        # For "Save" entry, explicitly set (no) shortcut
        "&File >",
        ["open:Open", "&Save #", "&Quit"],
        "&Nested >",
        [
            # Subitem 1 and Item 2 to test correct discrimination of Shift key
            "Submenu 1 >",
            ["Subitem 1 #C-S-I"],
            "Item 2 #C-I",
            "Sub&menu 3 >",
            [],
        ],
        "Help >",
        ["About #F1"],
    ]
    f_body = """
    |
    """

    # all handlers must be there
    def open(self):
        print("menu action: open")

    def save(self):
        print("menu action: save")

    # quit is predefined by AutoFrame
    def subitem_1(self):
        print("menu action: subitem_1")

    def item_2(self):
        print("menu action: item_2")

    def about(self):
        print("menu action: about")


class EmptyFrame(AutoFrame):
    f_body = ""


if __name__ == "__main__":
    logging.basicConfig(level="DEBUG")
    TK = "tk"
    if sys.argv[1:]:
        TK = sys.argv[1]

    set_toolkit(TK)

    t = AutoFrame.f_translations = load_translations_json("test_ascii_designer_i18n")
    # Set this to update f_translation if "missing" keys are queried. Need to
    # save afterwards. Probably should load ``language=""`` when doing this.
    # t.recording = True
    # Set this to have untranslated strings prepended by "$" dollar sign in the ui.
    t.mark_missing = True

    if sys.argv[2:]:
        F = {
            "autoconnect": AutoconnectDemo,
            "bound": BoundCtlDemo,
            "alignment": AlignmentDemo,
            "converters": ConvertersDemo,
            "boxes": BoxesDemo,
            "list": ListDemo,
            "tree": TreeDemo,
            "listedit": ListEditDemo,
            "menu": MenuDemo,
        }[sys.argv[2]]
    else:
        F = Main
    frm = F()
    frm.f_show()

    # Uncomment if using recording mode.
    # !! will overwrite the used translation file
    # path = save_translations_json(t, "test_ascii_designer_i18n/default.json")
    # print("Saved translations:", path)
