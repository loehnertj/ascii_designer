'''``ttk.TreeView`` control augmented by editing capabilities.

For basic information, see official Tkinter (``ttk``) docs.

The following additional functionality is provided:

 * Mark column as editable using :any:`Treeedit.editable`.

The following bindings / behaviors are built-in. Generally, value is
submitted on close, except if Escape key is used.

**Treeview**:

 * Dblclick:      open edit on col
 * Scroll:        Take focus (close edit)
 * Resize:        close edit box
 * F2:            open first edit of row

**Edit box**:

 * Lose Focus:    close
 * Return:        close
 * Escape:        close without submitting
 * Shift+enter,
 * Down arrow:    Close + edit same column in next row
 * Tab,
 * Right arrow:   close + edit next column (or 1st col in next row)
 * Shift+Tab,
 * Left arrow:    like Tab but backwards
 * Up arrow:      Close + edit same col in prev row

**Events**:

 * ``<<CellEdit>>`` when editor is opened
 * ``<<CellModified>>`` when editor is closed

To find the cell that is being edited, look at the ``.edit_cell`` and ``.modified_cell`` properties.

Two properties control whether items can be inserted and deleted. They can
either be True or a callback that takes a single argument. The argument is
the ID of the inserted item.
 
 * ``on_new_item``: bool or a function that inserts a new item. If truthy,
   "add" and "remove" buttons are shown. The same functions are bound to
   Ctrl-Plus and Ctrl-Minus.
 * ``on_new_child``: bool or a function that inserts a new child item. If truthy,
   "add-child" button is shown. The same function is bound to
   Ctrl-asterisk.

# TODO:
# reorder
'''

import tkinter as tk
from tkinter.ttk import Treeview

class TreeEdit(Treeview):
    def __init__(self, master, on_new_item=None, on_new_child=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._editvar = tk.StringVar(self, '')
        self._editbox = tk.Entry(self, textvariable=self._editvar)
        self._edit_cell = None
        self._modified_cell = None
        self._editable = {}
        self._all_columns = ['#0'] + list(kwargs.get('columns', []))
        for name in self._all_columns:
            self._editable[name] = False
        self.bind('<Double-Button-1>', self._dblclick)
        self.bind('<F2>', self._begin_edit_row)
        # Scroll wheel
        self.bind('<4>', self._close_edit_refocus)
        self.bind('<5>', self._close_edit_refocus)
        self.bind('<Configure>', self._on_configure)
        self.bind('<Control-plus>', self._ins_item)
        self.bind('<Control-asterisk>', lambda ev: self._ins_item(child=True))
        self.bind('<Control-minus>', self._delitem)
        self.bind('<Delete>', self._delitem)

        self._editbox.bind('<FocusOut>', self.close_edit)
        self._editbox.bind('<Return>', self._close_edit_refocus)
        self._editbox.bind('<Escape>', lambda ev: self._close_edit_refocus(ev, cancel=True))
        self._editbox.bind('<Right>', lambda ev: self._advance('right'))
        self._editbox.bind('<Tab>', lambda ev: self._advance('right'))
        self._editbox.bind('<Left>', lambda ev: self._advance('left'))
        self._editbox.bind('<Shift-Tab>', lambda ev: self._advance('left'))
        self._editbox.bind('<Shift-ISO_Left_Tab>', lambda ev: self._advance('left'))
        self._editbox.bind('<Shift-Return>', lambda ev: self._advance('down'))
        self._editbox.bind('<Down>', lambda ev: self._advance('down'))
        self._editbox.bind('<Up>', lambda ev: self._advance('up'))

        self._editbox.bind('<Control-plus>', self._ins_item)
        self._editbox.bind('<Control-asterisk>', lambda ev: self._ins_item(child=True))
        self._editbox.bind('<Control-minus>', self._delitem)

        self._on_new_item = on_new_item
        self._on_new_child = on_new_child

        self._update_controls()

    @property
    def edit_cell(self):
        '''Returns the currently-edited cell. Tuple (item id, column name).

        Use this to get at the edited item when processing
        ``<<CellEdit>>``. Unfortunately we cannot pass data with
        a tkinter event.

        If no edit is in progress, value is None.
        '''
        return self._edit_cell

    @property
    def modified_cell(self):
        '''Returns the last-modified cell. Tuple (item id, column name).

        Use this to get at the edited item when processing
        ``<<CellModified>>``. Unfortunately we cannot pass data with
        a tkinter event.

        If no edit was done, value is None.
        '''
        return self._modified_cell

    @property
    def on_new_item(self):
        return self._on_new_item
    @on_new_item.setter
    def on_new_item(self, val):
        self._on_new_item = val
        self._update_controls()
    
    @property
    def on_new_child(self):
        return self._on_new_child
    @on_new_child.setter
    def on_new_child(self, val):
        self._on_new_child = val
        self._update_controls()
    

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
        self.close_edit()
        self.see(iid)
        self.focus(iid)
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
        self.event_generate('<<CellEdit>>')

    def _close_edit_refocus(self, ev=None, cancel=False):
        self.close_edit(ev, cancel)
        self.focus_set()

    def close_edit(self, ev=None, cancel=False):
        if not cancel and self._edit_cell is not None:
            iid, column = self._edit_cell
            if column == '#0':
                self.item(iid, text=self._editvar.get())
            else:
                self.set(iid, column, self._editvar.get())
            self._modified_cell = (iid, column)
            self.event_generate( '<<CellModified>>')
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

    def _begin_edit_row(self, ev):
        # get current row and first editable column
        iid = self.focus()
        columns = self._ed_list
        if not columns:
            return
        self.begin_edit(iid, columns[0])

    def _advance(self, direction='right'):
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

    def _on_configure(self, ev):
        self.close_edit()
        if self._controls:
            self._controls.place(relx=1, rely=1, anchor='se')

    def _update_controls(self):
        on_new_item = self._on_new_item
        on_new_child = self._on_new_child
        if on_new_item or on_new_child:
            ctls = self._controls = tk.Frame(self)
            if on_new_item:
                addbtn = tk.Button(ctls, text=' + ', command=lambda:self._ins_item())
                addbtn.pack(side='left')
            if on_new_child:
                addcbtn = tk.Button(ctls, text='+>', command=lambda:self._ins_item(child=True))
                addcbtn.pack(side='left')
            delbtn = tk.Button(ctls, text=' X ', command=self._delitem)
            delbtn.pack(side='left')
        else:
            self._controls = None

    def _ins_item(self, ev=None, child=False):
        callback = self._on_new_child if child else self._on_new_item
        if not callback:
            return
        f = self.focus()
        self.close_edit()
        new_iid = self.insert(f if child else self.parent(f), self.index(f)+1)
        if callable(callback):
            callback(new_iid)
        elif child and callable(self._on_new_item):
            self._on_new_item(new_iid)
        self.focus(new_iid)
        self._begin_edit_row(None)

    def _delitem(self, ev=None):
        self.close_edit(cancel=True)
        self.delete(self.focus())

def main():
    import tkinter as tk
    from tkinter import ttk
    from tkinter import font
    tl = tk.Tk()
    style = ttk.Style()
    style.configure(".", font= font.Font(family='Helvetica'))
    style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))
    style.configure("Treeview", rowheight=30)

    def ins_item(iid):
        print('inserted: ', iid)

    te = TreeEdit(tl, columns=['col1', 'col2', 'col3'])
    te.pack(fill='both', expand=True)

    te.on_new_item = ins_item
    #te.on_new_child = True

    def print_begin(event):
        print('Edit: ', te.edit_cell)
    def print_change(event):
        print('Modified: ', te.modified_cell)

    te.bind('<<CellEdit>>', print_begin)
    te.bind('<<CellModified>>', print_change)

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