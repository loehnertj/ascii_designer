"""Functions related to Tk List / Tree View setup and behavior.
"""
__all__ = [
    "make_treelist",
    "ListBindingTk",
]
import logging
from typing import List
import dataclasses as dc
import tkinter as tk
from tkinter import ttk

from .toolkit import ListBinding
from .tk_treeedit import TreeEdit


def L():
    return logging.getLogger(__name__)


def _unique(parent, id):
    try:
        parent.nametowidget(id)
    except KeyError:
        return id
    else:
        # id exists
        return ""


def make_treelist(
    parent,
    id=None,
    text="",
    columns=None,
    first_column_editable=False,
    widget_classes=None,
    sort_asc_icon=None,
    sort_desc_icon=None,
):
    """treeview (also usable as plain list)

    Implementation note: Uses a ttk.TreeView, and wraps it into a frame
    together with a vertical scrollbar. For correct placement, the
    .place, .grid, .pack methods of the returned tv are replaced by that of
    the frame.

    Columns can be marked editable by appending "_" to the name.
    If any column is editable, a :any:`TreeEdit` is generated instead of the TreeView.

    Returns the treeview widget (within the frame).
    """
    if widget_classes is None:
        widget_classes = {
            "box": tk.Frame,
            "scrollbar": tk.Scrollbar,
            "treelist": ttk.Treeview,
            "treelist_editable": TreeEdit,
        }
    Frame = widget_classes["box"]
    Scrollbar = widget_classes["scrollbar"]
    text = text.strip()
    id = _unique(parent, id)
    is_editable = first_column_editable or any(column.editable for column in columns)
    has_first_column = bool(text)

    # setup scrollable container
    frame = Frame(parent)
    if is_editable:
        tv = widget_classes["treelist_editable"](frame, columns=[c.id for c in columns])
    else:
        tv = widget_classes["treelist"](frame, columns=[c.id for c in columns])
    scb = Scrollbar(frame)
    scb.pack(side="right", fill="y")
    tv.pack(expand=1, fill="both")
    scb.config(command=tv.yview)
    tv.config(yscrollcommand=scb.set)
    # patch layout methods
    tv.pack = frame.pack
    tv.place = frame.place
    tv.grid = frame.grid

    keys = [column.id for column in columns]
    if has_first_column:
        keys.insert(0, "")
    tv.variable = ListBindingTk(tv, keys)
    tv.variable.sort_asc_icon = sort_asc_icon
    tv.variable.sort_desc_icon = sort_desc_icon

    # configure tree view
    if has_first_column:
        tv.heading("#0", text=text, command=lambda: tv.variable.on_heading_click(""))
        if first_column_editable:
            tv.editable("#0", True)
    else:
        # hide first column
        tv["show"] = "headings"
    for column in columns:
        if not column.id:
            continue
        tv.heading(
            column.id,
            text=column.text,
            command=lambda key=column.id: tv.variable.on_heading_click(key),
        )
        if column.editable:
            tv.editable(column.id, True)
    if is_editable:
        tv.on_cell_modified += tv.variable.on_cell_modified
        tv.on_add += tv.variable.on_add_cmd
        tv.on_remove += tv.variable.on_remove_cmd
        tv.on_add_child += tv.variable.on_add_child_cmd

    tv.bind("<<TreeviewOpen>>", tv.variable.on_gui_expand)

    # set up variable
    return tv


class ListBindingTk(ListBinding):
    """
    Use ``get`` to return the ObsList;
    ``set`` to replace the value using a new list.

    All the on_ methods are internal event handlers.
    """

    def __init__(self, treeview, keys, **kwargs):
        super().__init__(keys=keys, **kwargs)
        self.list.toolkit_parent_id = ""
        self._tv = treeview
        self.sort_asc_icon = None
        """header icon for ascending column"""
        self.sort_desc_icon = None
        """header icon for descending column"""
        self._reorder_behavior = None

    @property
    def allow_reorder(self):
        return self._reorder_behavior is not None

    @allow_reorder.setter
    def allow_reorder(self, val):
        if val == self.allow_reorder:
            return
        if not val:
            if self._reorder_behavior:
                self._reorder_behavior.unbind()
            self._reorder_behavior = None
        else:
            self._reorder_behavior = ReorderBehavior(self._tv)

    def get(self):
        """get underlying list"""
        return self.list

    def set(self, val):
        """Set underlying list"""
        self.list = val

    def _set_list(self, val):
        if self._list is not None:
            self._tv.delete(*self._tv.get_children())
        super()._set_list(val)
        # val could have been cast into ObsList, use internal value.
        for idx, item in enumerate(self._list):
            iid = self.on_insert(idx, item, "")
            self._list.toolkit_ids[idx] = iid

    # === ObsList event-handler implementations ===

    def on_insert(self, idx, item, toolkit_parent_id):
        """create visible tree entry"""
        iid = self._tv.insert(toolkit_parent_id, idx, text=self.retrieve(item, ""))
        # insert placeholder so that "+" icon appears
        if self._list.has_children(item):
            self._tv.insert(iid, 0, text="")
        self.on_replace(iid, item)
        return iid

    def on_load_children(self, children):
        """replace subnodes"""
        self._tv.delete(*self._tv.get_children(children.toolkit_parent_id))
        for idx, item in enumerate(children):
            iid = self.on_insert(idx, item, children.toolkit_parent_id)
            children.toolkit_ids[idx] = iid

    def on_replace(self, iid, item):
        """replace visible tree entry"""
        tv = self._tv
        tv.item(iid, text=self.retrieve(item, ""))
        for column in self.keys:
            if column == "":
                continue
            txt = str(self.retrieve(item, column))
            tv.set(iid, column, txt)
        self._update_sortarrows()

    def on_remove(self, iid):
        """called when item was removed from list"""
        self._tv.delete(iid)

    def on_sort(self, sublist, info):
        """Called when list was sorted, via GUI or list.sort()"""
        super().on_sort(sublist, info)
        tv = self._tv
        _parent_iid = sublist.toolkit_parent_id
        for idx, iid in enumerate(sublist.toolkit_ids):
            tv.move(iid, _parent_iid, idx)
        self._update_sortarrows()

    def _update_sortarrows(self):
        tv = self._tv
        for key in self.keys:
            tv.heading(key or "#0", image="")
        if self.sort_key is not None:
            image = self.sort_asc_icon if self.sort_ascending else self.sort_desc_icon
            tv.heading(self.sort_key or "#0", image=image)

    def on_get_selection(self):
        """called to get the GUI selection as list items"""
        iids = self._tv.selection()
        nodes = []

        def add_nodes(nodelist):
            for node, tkid, childlist in zip(
                nodelist, nodelist.toolkit_ids, nodelist._childlists
            ):
                if tkid in iids:
                    nodes.append(node)
                if childlist:
                    add_nodes(childlist)

        add_nodes(self._list)
        return nodes

    # === GUI event handlers ===

    def _item(self, iid):
        sublist, idx = self._list.find_by_toolkit_id(iid)
        return sublist[idx], sublist

    def on_tv_focus(self, function):
        """call function with focused item"""
        iid = self._tv.focus()
        if not iid:
            return
        item, _ = self._item(iid)
        function(item)

    def on_gui_expand(self, stuff):
        """called when GUI item is expanded"""
        iid = self._tv.focus()
        # retrieve the idx
        sublist, idx = self._list.find_by_toolkit_id(iid)
        # on_load_children callback does the rest
        sublist.load_children(idx)

    def on_heading_click(self, key: str):
        """called when heading is clicked"""
        if self.sort_key is not None and key == self.sort_key:
            ascending = not self.sort_ascending
        else:
            ascending = True
        self.sort(key, ascending)

    def on_cell_modified(self, iid, columnname, val):
        item, sublist = self._item(iid)
        if columnname == "#0":
            columnname = ""
        self.store(item, val, columnname)
        sublist.item_mutated(item)
        return False

    # == TreeEdit structural changes ==

    def on_add_cmd(self, after_iid):
        if not after_iid:
            sublist, idx = self._list, -1
        else:
            sublist, idx = self._list.find_by_toolkit_id(after_iid)
        item = self.factory()
        sublist.insert(idx + 1, item)
        iid = sublist.toolkit_ids[idx + 1]
        self._tv.focus(iid)
        if self._tv.autoedit_added:
            self._tv.begin_edit_row(None)
        return False

    def on_add_child_cmd(self, parent_iid):
        if not parent_iid:
            sublist, idx = self._list, -1
        else:
            sublist, idx = self._list.find_by_toolkit_id(parent_iid)
        sublist = sublist.get_children(idx)
        item = self.factory()
        sublist.append(item)
        iid = sublist.toolkit_ids[-1]
        self._tv.focus(iid)
        if self._tv.autoedit_added:
            self._tv.begin_edit_row(None)
        return False

    def on_remove_cmd(self, iid):
        if not iid:
            return
        item, sublist = self._item(iid)
        sublist.remove(item)
        return False


@dc.dataclass
class GrabbedItem:
    """The currently grabbed item"""

    tk_id: str = ""
    """Tkinter treeview item id"""
    index: int = 0
    """current position in the list"""
    grabbed_at_y: int = 0
    """Where grab started, used to apply start-threshold distance"""
    move_active = False
    """Item is being moved - Set to true after mouse was moved by threshold distance"""


SORT_THRESHOLD = 10
SCROLL_EDGES = (60, 30)
"""height of upper / lower scroll hit target.

Upper target is larger to accomodate heading space."""


class ReorderBehavior:
    """Allows interactive reordering of a ascii designer listview.

    In ``f_on_build()``, just use ``ReorderBehavior(tk_treeview)``. Will bind
    all necessary event handlers. It is recommended to store the reference away
    as variable.

    The list is updated immediately while dragging is in progress.

    We generate ``<<ReorderStarted>>`` and ``<<ReorderFinished>>`` virtual events on
    the Treeview when dragging starts / ends.

    WILL NOT work with a regular listview. Reordering happens by changing the bound list.

    Currently, multilevel lists (a.k.a trees) cannot be reordered.

    Binds:

    * ButtonPress, "grabs" item under mouse.
    * Motion event, updates item's position in the list.
    * ButtonRelease, ungrabs item.
    * Leave event, ungrabs item.
    """

    def __init__(self, tv):
        self.tv = tv
        """Treeview object. Must have ``.variable`` property (ListBindingTk instance)"""
        self.grabbed: GrabbedItem = None
        """Currently grabbed item"""
        self._tk_bind_handles = []
        self.bind()

    @property
    def list(self) -> List:
        """return the list model"""
        return self.tv.variable.list

    def bind(self):
        """Bind event handlers, i.e. activate sorting behavior.

        Happens automatically on initialization."""
        tv = self.tv
        self.unbind()
        self._tk_bind_handles = [
            tv.bind("<ButtonPress-1>", self._grab, add="+"),
            tv.bind("<Motion>", self._motion, add="+"),
            tv.bind("<ButtonRelease-1>", self._ungrab, add="+"),
            tv.bind("<Leave>", self._ungrab, add="+"),
        ]

    def unbind(self):
        """Unbind event handlers i.e. deactivate sorting behavior."""
        tv = self.tv
        events = ["<ButtonPress-1>", "<Motion>", "<ButtonRelease-1>", "<Leave>"]
        for event, handle in zip(events, self._tk_bind_handles):
            tv.unbind(event, handle)
        self._tk_bind_handles = []

    def _grab(self, ev):
        if self.tv.identify_region(ev.x, ev.y) != "tree":
            return
        iid = self.tv.identify_row(ev.y)
        if not iid:
            return
        list, index = self.list.find_by_toolkit_id(iid)
        assert list is self.list, "Cannot sort subtrees yet"
        self.grabbed = GrabbedItem(iid, index, grabbed_at_y=ev.y)
        # L().debug("Grab %s", self.grabbed)

    def _motion(self, ev):
        if not self.grabbed:
            return
        if (
            not self.grabbed.move_active
            and abs(self.grabbed.grabbed_at_y - ev.y) > SORT_THRESHOLD
        ):
            self.tv.event_generate("<<ReorderStarted>>")
            self.grabbed.move_active = True
            self.tv.after(100, self._scroll_timer)
            self.tv["cursor"] = "sb_v_double_arrow"
        if not self.grabbed.move_active:
            return
        iid = self.tv.identify_row(ev.y)
        if not iid:
            return
        index = self.tv.index(iid)
        if index != self.grabbed.index:
            L().debug("Move %d -> %d", self.grabbed.index, index)
            self._move(self.grabbed.index, index)
            self.grabbed.index = index

    def _move(self, from_index, to_index):
        l = self.list
        if from_index != to_index:
            l.insert(to_index, l.pop(from_index))
        self.tv.update_idletasks()

    def _scroll_timer(self):
        if not self.grabbed:
            return
        self.tv.after(200, self._scroll_timer)
        y = self.tv.winfo_pointery() - self.tv.winfo_rooty()
        h = self.tv.winfo_height()

        if y < SCROLL_EDGES[0]:
            # scroll up
            self.tv.yview_scroll(-1, "units")
        elif h - y < SCROLL_EDGES[1]:
            # scroll down
            self.tv.yview_scroll(1, "units")
        else:
            return
        self.tv.update_idletasks()
        y_ = y

        class dummy_ev_args:
            y = y_

        self._motion(dummy_ev_args)

    def _ungrab(self, ev):
        if self.grabbed and self.grabbed.move_active:
            self.tv["cursor"] = ""
            self.tv.event_generate("<<ReorderFinished>>")
        self.grabbed = None
