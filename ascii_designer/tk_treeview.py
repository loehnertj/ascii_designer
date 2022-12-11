"""Functions related to Tk List / Tree View setup and behavior.
"""
__all__ = [
    "make_treelist",
    "ListBindingTk",
]
import tkinter as tk
from tkinter import ttk

from .toolkit import ListBinding
from .tk_treeedit import TreeEdit


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
