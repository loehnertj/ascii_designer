'''``ttk.TreeView`` control augmented by editing capabilities.

For basic information, see official Tkinter (``ttk``) docs.

The following additional functionality is provided:

 * Mark column as editable using :any:`TreeEdit.editable`.
 * allow= parameter to specify legal structural operations.

``allow`` is a list of strings or a comma-separated string. It can contain any of:

 * ``add`` to allow adding new items (anywhere)
 * ``addchild`` to allow insertion of child items
 * ``remove`` to allow deletion of items.

For each allowance, the corresponding control is shown, and the keybinding is activated.

The following bindings / behaviors are built-in. Generally, value is
submitted on close, except if Escape key is used.

**Treeview**:

 * Dblclick:      open edit on col
 * Scroll:        Take focus (close edit)
 * Resize:        close edit box
 * F2:            open first edit of row
 * Ctrl+plus,
   Insert:        add item (if enabled, see below)
 * Ctrl+asterisk: add child (if enabled)
 * Ctrl+minus,
 * Delete:        remove item (if enabled)

**Edit box**:

 * Lose Focus:    close
 * Return:        close
 * Escape:        close without submitting
 * Shift+enter,
 * Down arrow:    Close + edit same column in next row
 * Tab,
 * Shift+Right arrow:   close + edit next column (or 1st col in next row)
 * Shift+Tab,
 * Shift+Left arrow:    like Tab but backwards
 * Up arrow:      Close + edit same col in prev row

**Events**:

These are properties of the TreeeEdit control. 
Use ``treeedit.<property> += handler``to bind a handler, ``-=`` to unbind it.

 * ``on_cell_edit(iid, columnname, cur_value)`` when editor is opened
 * ``on_cell_modified(iid, columname, new_value)`` when editor is closed
 * ``on_add(iid)``: before item is inserted after (iid).
 * ``on_add_child(iid)``: before child is inserted under (iid).
 * ``on_remove(iid)``: before child is deleted

.. note:: 
    ``on_cell_modified``, ``on_add``, ``on_add_child``, ``on_remove`` are fired
    immediately before the respective action takes place in the widget.

    Your handler can return ``False`` to indicate that the widget content shall
    not be modified; e.g. if the action is forbidden or you took care of
    updating the tree yourself. Note that ``None`` is counted as ``True`` result
    in this case.

# TODO:
# reorder
# custom editor types (button, checkbox, combo, ... pass own widget(s))
# copy/paste
# have a handler for after-item-insertion with the actual iid as param (we don't need it currently)
'''

__all__ = ['TreeEdit',]

import sys

import tkinter as tk
import tkinter.ttk as ttk

from .event import event

class TreeEdit(ttk.Treeview):
    '''see module docs'''

    list_bindings = [
        ('<Double-Button-1>', "_dblclick"),
        ('<F2>', 'begin_edit_row'),
        # Scroll wheel
        ('<4>', '_close_edit_refocus'),
        ('<5>', '_close_edit_refocus'),
        ('<Control-plus>', 'ins_item'),
        ('<Insert>', 'ins_item'),
        ('<Control-asterisk>', 'ins_child_item'),
        ('<Control-minus>', 'del_item'),
        ('<Delete>', 'del_item'),
    ]
    editbox_bindings = [
        ('<FocusOut>', 'close_edit'),
        ('<Return>', '_close_edit_refocus'),
        ('<KP_Enter>', '_close_edit_refocus'),
        ('<Escape>', '_cancel_edit_refocus'),
        ('<Shift-Right>', 'advance_right'),
        ('<Tab>', 'advance_right'),
        ('<Shift-Left>', 'advance_left'),
        ('<Shift-Tab>', 'advance_left'),
        ('<Shift-Return>', 'advance_down'),
        ('<Shift-KP_Enter>', 'advance_down'),
        ('<Down>', 'advance_down'),
        ('<Up>', 'advance_up'),
        ('<Control-plus>', 'ins_item'),
        ('<Control-asterisk>', 'ins_child_item'),
        ('<Control-minus>', 'del_item'),
    ] + (
        [] if not sys.platform.startswith('linux') else  [
            ('<Shift-ISO_Left_Tab>', 'advance_left'),
        ]
    )

    def __init__(self, master, allow=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self._editvar = tk.StringVar(self, '')
        self._editbox = ttk.Entry(self, textvariable=self._editvar)
        self._edit_cell = None
        self._editable = {}
        self._all_columns = ['#0'] + list(kwargs.get('columns', []))
        for name in self._all_columns:
            self._editable[name] = False

        self.bind('<Configure>', self._on_configure)
        for trigger, handler in self.list_bindings:
            if isinstance(handler, str):
                handler = getattr(self, handler)
            self.bind(trigger, handler)
        for trigger, handler in self.editbox_bindings:
            if isinstance(handler, str):
                handler = getattr(self, handler)
            self._editbox.bind(trigger, handler)

        self.allow = allow
        self.autoedit_added = True

    @property
    def allow(self):
        '''Allowed structural edits (add, delete, addchild).

        Pass the allowed actions as list of strings or comma-separated string.

        Can be updated during operation.
        '''
        return self._allow[:]
    @allow.setter
    def allow(self, allow):
        allow = allow or []
        if isinstance(allow, str):
            allow = allow.split(',')
        allow = [item.strip() for item in allow]
        bad_items = [item for item in allow if item not in ['add', 'addchild', 'remove']]
        if bad_items:
            raise ValueError('Unknown allow entries: %s' % (bad_items,))
        self._allow = allow
        self._update_controls()

    @property
    def autoedit_added(self) -> bool:
        '''Automatically begin editing added items yes/no''' 
        return self._autoedit_added
    @autoedit_added.setter
    def autoedit_added(self, val: bool):
        self._autoedit_added = bool(val)

    @event(by_name=False)
    def on_add(self, after_iid:str):
        """Event: Item is about to be added.
        
        ``after_iid`` gives the currently-selected item.
        
        A handler may return ``False`` to indicate that it already took care
        about inserting item in the view.
        """

    @event(by_name=False)
    def on_add_child(self, below_iid:str):
        """Event: Child item is about to be added.
        
        ``below_iid`` gives the currently-selected item.
        
        A handler may return ``False`` to indicate that it already took care
        about inserting item in the view.
        """

    @event(by_name=False)
    def on_remove(self, iid):
        """Event: Item is about to be removed.

        A handler may return ``False`` to indicate that it already took care
        about removing item from the view.
        """

    @event(by_name=False)
    def on_cell_edit(self, iid:str, columnname:str, cur_value:str):
        """Event: cell is about to be edited."""

    @event(by_name=False)
    def on_cell_modified(self, iid:str, columname:str, new_value:str):
        """Event: editing is finished"""
    
    def editable(self, column, editable=None):
        '''Query or specify whether the column is editable.

        Only accepts Column Name or ``'#0'``.
        '''
        if column not in self._editable:
            raise KeyError(column)
        if editable is not None:
            self._editable[column] = bool(editable)
        return self._editable[column]

    @property
    def _ed_list(self):
        return [name for name in self._all_columns if self._editable[name]]

    def begin_edit(self, iid, column):
        '''Show edit widget for the specified cell.'''
        self.close_edit()
        self.see(iid)
        self.focus(iid)
        self.update_idletasks()
        try:
            x, y, w, h = self.bbox(iid, column=column)
        except ValueError:
            # not visible
            return
        if column == '#0':
            val = self.item(iid, option='text')
        else:
            # self.set GETS the value!
            val = self.set(iid, column)
        self._editvar.set(val)
        self._editbox.place(x=x, y=y, width=w, height=h)
        self._edit_cell = (iid, column)
        self._editbox.selection_range(0, 'end')
        self._editbox.focus_set()
        self.on_cell_edit(iid, column, self._editvar.get())

    def _close_edit_refocus(self, ev=None, cancel=False):
        self.close_edit(ev, cancel)
        self.focus_set()
        return "break"

    def _cancel_edit_refocus(self, ev=None):
        self.close_edit(ev, cancel=True)
        self.focus_set()
        return "break"

    def close_edit(self, ev=None, cancel=False):
        '''Close the currently open editor, if any.'''
        if not cancel and self._edit_cell is not None:
            iid, column = self._edit_cell
            result = self.on_cell_modified(iid, column, self._editvar.get()) 
            if result is None or result:
                # Modify content
                if column == '#0':
                    self.item(iid, text=self._editvar.get())
                else:
                    self.set(iid, column, self._editvar.get())
        self._edit_cell = None
        self._editbox.place_forget()
    
    def _dblclick(self, ev):
        iid = self.identify_row(ev.y)
        column = self.identify_column(ev.x)
        idx = int(column[1:])
        if idx > 0:
            dc = self['displaycolumns']
            if dc == ('#all',):
                dc = self['columns']
            colname = dc[idx-1]
        else:
            colname = '#0'

        if not iid or not self._editable[colname]:
            return
        self.begin_edit(iid, colname)
        return "break"

    def begin_edit_row(self, ev):
        '''Start editing the first editable column of the focused row.'''
        iid = self.focus()
        columns = self._ed_list
        if not columns:
            return
        self.begin_edit(iid, columns[0])

    def advance(self, direction='right'):
        '''switch to next cell.

        ``direction`` can be left, right, up, down.

        If going left/right beyond the first or last cell, edit box moves to
        the previous/next row.
        '''
        if self._edit_cell is None:
            return
        iid, column = self._edit_cell
        if direction == 'down':
            iid = self.next(iid)
        elif direction == 'up':
            iid = self.prev(iid)
        elif direction == 'left':
            columns = self._ed_list
            idx = columns.index(column)-1
            if idx < 0:
                idx = len(columns)-1
                iid = self.prev(iid)
            column = columns[idx]
        elif direction == 'right':
            columns = self._ed_list
            idx = columns.index(column)+1
            if idx >= len(columns):
                idx=0
                iid = self.next(iid)
            column = columns[idx]
        else:
            raise ValueError('invalid direction %s' % direction)

        if iid:
            self.begin_edit(iid, column)
        else:
            self._close_edit_refocus()
        # to disable default behaviour
        return 'break'

    def advance_left(self, ev=None):
        return self.advance('left')

    def advance_right(self, ev=None):
        return self.advance('right')

    def advance_up(self, ev=None):
        return self.advance('up')

    def advance_down(self, ev=None):
        return self.advance('down')

    def _on_configure(self, ev):
        self.close_edit()
        if self._controls:
            self._controls.place(relx=1, rely=1, anchor='se')

    def _update_controls(self):
        allow = self._allow
        if allow:
            ctls = self._controls = ttk.Frame(self)
            if 'add' in allow:
                addbtn = ttk.Button(ctls, text=' + ', command=lambda:self.ins_item())
                addbtn.pack(side='left')
            if 'addchild' in allow:
                addcbtn = ttk.Button(ctls, text='+>', command=lambda:self.ins_item(child=True))
                addcbtn.pack(side='left')
            if 'remove' in allow:
                delbtn = ttk.Button(ctls, text=' X ', command=self.del_item)
                delbtn.pack(side='left')
        else:
            self._controls = None

    def ins_item(self, ev=None, child=False):
        '''Trigger insertion of a new item.'''
        if ('addchild' if child else 'add') not in self._allow:
            return
        f = self.focus()
        self.close_edit()
        if child:
            result = self.on_add_child(f)
        else:
            result = self.on_add(f)
        if result is None or result:
            new_iid = self.insert(f if child else self.parent(f), self.index(f)+1)
            self.focus(new_iid)
            if self.autoedit_added:
                self.begin_edit_row(None)

    def ins_child_item(self, ev=None):
        '''Trigger insertion of new child item'''
        return self.ins_item(ev, child=True)

    def del_item(self, ev=None):
        '''Trigger deletion of focused item.'''
        if 'remove' not in self._allow:
            return
        self.close_edit(cancel=True)
        iid = self.focus()
        if iid:
            result = self.on_remove(iid)
            if result is None or result:
                self.delete(iid)

def main():
    import tkinter as tk
    from tkinter import ttk
    from tkinter import font
    tl = tk.Tk()
    tl.grid_rowconfigure(0, weight=1)
    tl.grid_columnconfigure(0, weight=1)
    style = ttk.Style()
    style.configure(".", font= font.Font(family='Helvetica'))
    style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))
    style.configure("Treeview", rowheight=30)

    te = TreeEdit(tl, columns=['col1', 'col2', 'col3'])
    #te.pack(fill='both', expand=True)
    te.grid(row=0, column=0, sticky='nsew')
    te.allow = 'add,remove,addchild'

    te.on_add += lambda focus: print('inserting an item after', focus)
    def delete_myself(iid):
        print('delete', iid)
        te.delete(iid)
        return False
    te.on_remove += delete_myself

    def print_begin(iid, column, current_val):
        print('Edit: ', iid, column, current_val)
    def print_change(iid, column, new_val):
        print('Modified: ', iid, column, new_val)

    te.on_cell_edit += print_begin
    te.on_cell_modified += print_change

    te.editable('#0', True)
    te.editable('col1', True)
    te.editable('col3', True)

    fakedata = [
        ['this', 'is', 'a', 'row'],
        ['another', 'row', 'is', 'here'],
        ['lorem', 'ipsum', 'dolor', 'sit'],
        ['romanes', 'eunt', 'domus', ''],
        ['romani', 'ite', 'domum', ''],
    ]*5
    parent = ''
    for i in range(2):
        for data in fakedata:
            txt, t1, t2, t3 = data
            iid = te.insert(parent, 'end', text=txt)
            te.set(iid, 'col1', t1)
            te.set(iid, 'col2', t2)
            te.set(iid, 'col3', t3)
        parent = iid
    tl.mainloop()

if __name__ == '__main__':
    main()