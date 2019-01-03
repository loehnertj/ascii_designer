'''This is a construction site...''' 

import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import font
from tkinter import ttk
from .toolkit import ToolkitBase, NodelistBase

#ttk = tk


__all__ = [
    'ToolkitTk',
]

def _on_tv_select(ev, function, widget):
    f = widget.focus()
    if not f:
        return
    idx = int(widget.focus())
    # get the node at idx and return its ref property (the original object)
    obj = widget.variable.get()[idx].ref
    function(obj)
    
_master_window = None
def start_mainloop_if_necessary(widget):
    if isinstance(widget, tk.Tk):
        widget.mainloop()

class ToolkitTk(ToolkitBase):
    '''
    Builds Tk widgets.
    
    Returns the raw Tk widget (no wrapper).

    For each widget, a Tk Variable is generated. It is stored in 
    ``<widget>.variable`` (attached as additional property).
    
    If you create Radio buttons, they will all share the same variable.
    
    The multiline widget is a tkinter.scrolledtext.ScrolledText and has no 
    variable.
    
    The ComboBox / Dropdown box is taken from ttk.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # FIXME: global radiobutton var - all rb's created by this toolkit instance are connected.
        # Find a better way of grouping (by parent maybe?)
        self._radiobutton_var = None
        
    # widget generators
    def root(self, title='Window'):
        '''make a root (window) widget'''
        print('make root: '+title)
        global _master_window
        if _master_window is None:
            _master_window = root = tk.Tk()
        else:
            root = tk.Toplevel()
        root.tk.call('tk', 'scaling', 2.0)
        root.option_add('*Font', self._sane_font)
        # XXX does not work when opening another frame
        style = ttk.Style()
        style.configure(".", font=self._sane_font)
        style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'))
        style.configure("Treeview", rowheight=30)
        root.title(title)
        return root
        
    @property
    def _sane_font(self):
        if not hasattr(self, '_sane_font_cached'):
            self._sane_font_cached = font.Font(family='Helvetica', size=12)
        return self._sane_font_cached
    
    def show(self, frame):
        '''do what is necessary to make frame appear onscreen.'''
        start_mainloop_if_necessary(frame)
        
    def close(self, frame):
        '''close the frame'''
        frame.destroy()
        
    def place(self, widget, row=0, col=0, rowspan=1, colspan=1):
        '''place widget'''
        widget.grid(row=row,rowspan=rowspan, column=col, columnspan=colspan)
        
    def connect(self, widget, function):
        '''bind the widget's default event to function.
        
        Default event is:
         * click() for a button
         * value_changed(new_value) for value-type controls;
            usually fired after focus-lost or Return-press.
        '''
        if isinstance(widget, tk.Button):
            widget.config(command=function)
        elif isinstance(widget, ScrolledText):
            widget.bind('<Return>', lambda ev:function(widget.get(1., 'end')))
            widget.bind('<FocusOut>', lambda ev: function(widget.get(1., 'end')))
        elif isinstance(widget, tk.Entry):
            widget.bind('<Return>', lambda ev:function(widget.variable.get()))
            widget.bind('<FocusOut>', lambda ev: function(widget.variable.get()))
        elif isinstance(widget, ttk.Treeview):
            widget.bind('<<TreeviewSelect>>', lambda ev: _on_tv_select(ev, function, widget))
        else:
            widget.variable.trace('w', lambda *args: function(widget.variable.get()))
            
    def getval(self, widget):
        if isinstance(widget, ScrolledText):
            return widget.get(1., 'end')
        else:
            return widget.variable.get()
    
    def setval(self, widget, value):
        if isinstance(widget, ScrolledText):
            widget.delete(1., 'end')
            widget.insert('end', value)
        else:
            widget.variable.set(value)
        
    def row_stretch(self, container, row, proportion):
        '''set the given row to stretch according to the proportion.'''
        container.grid_rowconfigure(row, weight=proportion)
        
    def col_stretch(self, container, col, proportion):
        '''set the given col to stretch according to the proportion.'''
        container.grid_columnconfigure(col, weight=proportion)
        
    def anchor(self, widget, left=True, right=True, top=True, bottom=True):
        sticky = ''
        if left: sticky += 'w'
        if right: sticky += 'e'
        if top: sticky += 'n'
        if bottom: sticky += 's'
        widget.grid(sticky=sticky)
        
    def spacer(self, parent):
        '''a vertical/horizontal spacer'''
        
    def label(self, parent, id=None, label_id=None, text=''):
        '''label'''
        var = tk.StringVar(parent, text)
        l = tk.Label(parent, name=id, textvariable=var)
        l.variable = var
        return l
        
    def button(self, parent, id=None, text=''):
        '''button'''
        var = tk.StringVar(parent, text)
        b = tk.Button(parent, name=id, textvariable = var)
        b.variable = var
        return b
    
    def textbox(self, parent, id=None, text=''):
        '''single-line text entry box'''
        var = tk.StringVar(parent, text)
        e = tk.Entry(parent, name=id, textvariable=var)
        e.variable = var
        return e
    
    def multiline(self, parent, id=None, text=''):
        t = ScrolledText(parent, name=id, height=3)
        t.insert('end', text)
        return t
    
    def treelist(self, parent, id=None, text='', columns=None):
        '''treeview (also usable as plain list)
        
        Implementation note: Uses a ttk.TreeView, and wraps it into a frame
        together with a vertical scrollbar. For correct placement, the
        .place, .grid, .pack methods of the returned tv are replaced by that of 
        the frame.
        
        Returns the treeview widget (within the frame).
        '''
        columns = columns or ''
        columns = [txt.strip() for txt in columns.split(',')]
        has_first_column = ['' in columns]
        keys = [name.lower() for name in columns]
        
        # setup scrollable container
        frame = tk.Frame(parent)
        tv = ttk.Treeview(frame, columns=[k for k in keys if k])
        scb = tk.Scrollbar(frame)
        scb.pack(side='right', fill='y')
        tv.pack(expand=1, fill='both')
        scb.config(command=tv.yview)
        tv.config(yscrollcommand=scb.set)
        # patch layout methods
        tv.pack = frame.pack
        tv.place = frame.place
        tv.grid = frame.grid
        
        # configure tree view
        if has_first_column:
            tv.heading('#0', text=text)
        else:
            # hide first column
            tv['show'] = 'headings'
        for key, heading in zip(keys, columns):
            if not key:
                continue
            tv.heading(key, text=heading)
        
        # set up variable
        nodelist = NodelistVariable(NodelistTk(keys, tv))
        tv.variable = nodelist
        return tv
        
    def dropdown(self, parent, id=None, text='', values=None):
        return self._dropdown(parent, id, text, values, False)
    
    def combo(self, parent, id=None, text='', values=None):
        return self._dropdown(parent, id, text, values, True)
    
    def _dropdown(self, parent, id=None, text='', values=None, editable=False):
        '''dropdown box; values is the raw string between the parens. Only preset choices allowed.'''
        choices = [v.strip() for v in (values or '').split(',') if v.strip()]
        var = tk.StringVar(parent, text)
        cbo = ttk.Combobox(parent, name=id, values=choices, textvariable=var, state='normal' if editable else 'readonly')
        cbo.variable = var
        return cbo
    
    def option(self, parent, id=None, text='', checked=None):
        '''Option button. Prefix 'O' for unchecked, '0' for checked.'''
        if not self._radiobutton_var:
            self._radiobutton_var = tk.StringVar(parent, id)
        rb = tk.Radiobutton(parent,
                  text=text,
                  variable=self._radiobutton_var, 
                  name=id,
                  value=id,
        )
        if checked.strip():
            self._radiobutton_var.set(id)
        rb.variable = self._radiobutton_var
        rb._id = id
        return rb
    
    def checkbox(self, parent, id=None, text='', checked=None):
        '''Checkbox'''
        var = tk.BooleanVar(parent, bool(checked.strip()))
        cb = tk.Checkbutton(
            parent,
            text=(text or '').strip(),
            name=id,
            variable=var, onvalue=True, offvalue=False
            )
        cb.variable = var
        return cb
    
    def slider(self, parent, id=None, min=None, max=None):
        '''slider, integer values, from min to max'''
        var = tk.IntVar(parent, min)
        s = tk.Scale(
            parent,
            name=id,
            from_=min,
            to=max,
            orient=tk.HORIZONTAL,
            variable=var
        )
        s.variable = var
        return s
    
class NodelistVariable:
    def __init__(self, nodelist):
        self._nl = nodelist
        
    def get(self):
        return self._nl
        
    def set(self, val):
        old_nl = self._nl
        old_nl.attached = False
        self._nl = NodelistTk(old_nl.keys, old_nl.treeview, val)
        
    
class NodelistTk(NodelistBase):
    def __init__(self, keys, treeview=None, iterable=None):
        self.attached = False
        super().__init__(keys, iterable=iterable)
        self.treeview = treeview
        self.attached = (treeview is not None)
        for idx, node in enumerate(self._nodes):
            self._treeinsert(idx, node)
        
    def __setitem__(self, idx, item):
        super().__setitem__(idx, item)
        if not self.attached: 
            return
        item = self._nodes[idx]
        self._update_item(idx, item)
        
    def __delitem__(self, idx):
        super().__delitem__(idx)
        if not self.attached: 
            return
        
    def insert(self, idx, item):
        # returns actual idx (within list range) and inserted item.
        idx, item = super().insert(idx, item)
        if not self.attached: 
            return
        self._treeinsert(idx, item)
        
    def _treeinsert(self, idx, item):
        item = self._nodes[idx]
        self.treeview.insert('', idx, iid=str(idx), text=item.text)
        self._update_item(idx, item)
        
    def _update_item(self, idx, item):
        tv = self.treeview
        iid = str(idx)
        tv.item(iid, text=item.text)
        for column in self.keys:
            if column == '': continue
            tv.set(iid, column, str(item[column]))
            
    def _on_node_setkey(self, node, key, val):
        if not self.attached:
            return
        tv = self.treeview
        idx = self._nodes.index(node)
        iid = str(idx)
        if key=='':
            tv.item(iid, text=str(val))
        else:
            tv.set(iid, key, str(val))