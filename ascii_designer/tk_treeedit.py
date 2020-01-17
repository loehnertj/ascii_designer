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

 * TODO

# Emit events for:
# Value changed
# (more as needed)

# insert-row, insert-child, delete-row function
'''

import tkinter as tk
from tkinter.ttk import Treeview

class TreeEdit(Treeview):
    def __init__(self, master, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._editvar = tk.StringVar(self, '')
        self._editbox = tk.Entry(self, textvariable=self._editvar)
        self._edit_cell = None
        self._editable = {}
        self._all_columns = ['#0'] + list(kwargs.get('columns', []))
        for name in self._all_columns:
            self._editable[name] = False
        self.bind('<Double-Button-1>', self._dblclick)
        self.bind('<F2>', self._begin_edit_row)
        # Scroll wheel
        self.bind('<4>', self._close_edit_refocus)
        self.bind('<5>', self._close_edit_refocus)
        self.bind('<Configure>', self.close_edit)

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
            self._edit_cell = None
            # TODO send event
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

def main():
    import tkinter as tk
    from tkinter import ttk
    from tkinter import font
    tl = tk.Tk()
    style = ttk.Style()
    style.configure(".", font= font.Font(family='Helvetica'))
    style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))
    style.configure("Treeview", rowheight=30)
    te = TreeEdit(tl, columns=['col1', 'col2', 'col3'])
    te.pack(fill='both', expand=True)

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