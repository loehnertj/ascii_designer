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

_ICONS = { 
'downarrow': """
-
-
    ##    ##
   ###    ###---
   ####  ####
    ########
     ######
      ####
       ## 
-
""",
'uparrow': """
-
       ##
      ####
     ######
    ########
   ####  ####
   ###    ###
    ##    ##----
-
-
""",
'sort_asc': """
            ###-
            ###
            ###
        ### ###
        ### ###
        ### ###
    ### ### ###
    ### ### ###
    ### ### ###
### ### ### ###
### ### ### ###
### ### ### ###
""",
'sort_desc': """
###-------------
###
###
### ###
### ###
### ###
### ### ###
### ### ###
### ### ###
### ### ### ###
### ### ### ###
### ### ### ###
"""
}

def _on_tv_select(ev, function, widget):
    iid = widget.focus()
    if not iid:
        return
    # get the node at idx and return its ref property (the original object)
    nodelist = widget.variable.get()
    items = [n for n in nodelist.loaded_nodes if n._tk_iid == iid]
    assert len(items)==1
    obj = items[0].ref
    function(obj)
    
def _aa2xbm(txt, marker='#'):
    lines = txt.split('\n')
    lines = [l for l in lines if l]
    template = '''
        #define im_width %d
        #define im_height %d
        static char im_bits[] = { %s };
    '''
    width = max(len(l) for l in lines)
    height = len(lines)
    # pad all lines to width
    lines = [l+' '*(width-len(l)) for l in lines]
    data = ''.join(lines)
    # we need to reverse-index, but that cannot get at element 0
    # since x[n:0:-1] gives you elements n, n-1, ... 1
    # hacky solution: prepend a dummy char
    data = 'x'+''.join('1' if char == marker else '0' for char in data)
    enc_data= [
        str(int(data[ofs+8:ofs:-1],2))
        for ofs in range(0, len(data)-1, 8)
    ]
    enc_data = ','.join(enc_data)
    xbm = template%(width, height, enc_data)
    return(xbm)
    
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
    
    Box variable (placeholder): If you replace the box by setting its virtual 
    attribute, the replacement widget must have the same master as the box: in 
    case of normal box the frame root, in case of group box the group box. 
    Recommendation: ``new_widget = tk.Something(master=autoframe.the_box.master)``
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # FIXME: global radiobutton var - all rb's created by this toolkit instance are connected.
        # Find a better way of grouping (by parent maybe?)
        self._radiobutton_var = None
        
    # widget generators
    def root(self, title='Window', on_close=None):
        '''make a root (window) widget'''
        global _master_window
        if _master_window is None:
            _master_window = root = tk.Tk()
            # store as attributes so that they do not get GC'd
            root.icons = {
                key: tk.BitmapImage(name='::icons::%s'%key, data=_aa2xbm(data))
                for key, data in _ICONS.items()
            }
        else:
            root = tk.Toplevel()
        scale = root.winfo_fpixels('1i') / 72.0
        root.tk.call('tk', 'scaling', scale)
        root.option_add('*Font', self._sane_font)
        # XXX does not work when opening another frame
        style = ttk.Style()
        style.configure(".", font=self._sane_font)
        style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'))
        style.configure("Treeview", rowheight=30)
        root.title(title)
        if on_close:
            root.protocol('WM_DELETE_WINDOW', on_close)
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
        if type(widget) is tk.Frame:
            raise TypeError('Cannot assign a handler to a box.')
        elif isinstance(widget, tk.Button):
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
        if type(widget) is tk.Frame:
            return widget
        elif isinstance(widget, tk.LabelFrame):
            return widget.winfo_children()[0]
        elif isinstance(widget, ScrolledText):
            return widget.get(1., 'end')
        else:
            return widget.variable.get()
    
    def setval(self, widget, value):
        if type(widget) in (tk.Frame, tk.LabelFrame):
            if type(widget) is tk.LabelFrame:
                widget = widget.winfo_children()[0]
            # Replace the frame with the given value
            if value.master is not widget.master:
                raise ValueError('Replacement widget must have the same master')
            # copy grid info
            grid_info = widget.grid_info()
            grid_info.pop('in', None)
            # remove frame
            widget.grid_forget()
            widget.destroy()
            # place new widget
            value.grid(**grid_info)
        elif isinstance(widget, ScrolledText):
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
        
    def box(self, parent, id=None, text='', given_id=''):
        if given_id and text:
            f = tk.LabelFrame(parent, name=id, text=text)
            inner = tk.Frame(f)
            inner.grid(row=0, column=0, sticky='nsew')
        else:
            f = tk.Frame(parent, name=id)
        return f
        
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
        has_first_column = ('' in columns)
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
        
        tv.variable = NodelistVariable(NodelistTk([], keys=keys, treeview=tv))
        
        # configure tree view
        if has_first_column:
            tv.heading('#0', text=text, command=lambda: tv.variable.on_heading_click(''))
        else:
            # hide first column
            tv['show'] = 'headings'
        for key, heading in zip(keys, columns):
            if not key:
                continue
            tv.heading(key, text=heading, command=lambda key=key: tv.variable.on_heading_click(key))
        tv.bind('<<TreeviewOpen>>', tv.variable.on_expand)
        
        # set up variable
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
        old_nl.treeview.delete(*old_nl.treeview.get_children())
        self._nl = NodelistTk(val, meta=old_nl._meta, treeview=old_nl.treeview)
    
    def on_heading_click(self, key):
        if key == self._nl._meta.sort_key:
            ascending = True if not self._nl.sorted else not self._nl._meta.sort_ascending
        else:
            ascending = True
        self._nl.sort(key, ascending)
        
    def on_expand(self, stuff):
        tv = self._nl.treeview
        iid = tv.focus()
        # retrieve the item
        item = [n for n in self._nl.loaded_nodes if n._tk_iid == iid]
        assert len(item) == 1
        item = item[0]
        if item.children is None:
            item.get_children()
    
    
class NodelistTk(NodelistBase):
    def __init__(self, iterable=None, keys=None, meta=None, treeview=None, parent_iid=''):
        self.attached = False
        super().__init__(iterable=iterable, keys=keys, meta=meta)
        self.treeview = treeview
        self.attached = (treeview is not None)
        self._parent_iid = parent_iid
        for idx, node in enumerate(self._nodes):
            self._treeinsert(idx, node)
            
    def _children_of(self, node, iterable):
        if self.attached:
            self.treeview.delete(*self.treeview.get_children(node._tk_iid))
        # automatically inserts the children
        return NodelistTk(iterable, meta=self._meta, treeview=self.treeview, parent_iid=node._tk_iid)
    
    @property
    def loaded_nodes(self):
        '''return all nodes in tree regardless of which list they are in.'''
        childnodes = [
            cn
            for node in self._nodes if node.children
            for cn in node.children.loaded_nodes
        ]
        return self._nodes + childnodes
            
    @property
    def selection(self):
        '''returns the sublist of all currently-selected items.
        
        Raises RuntimeError if the nodelist is detached.
        '''
        if not self.attached:
            raise RuntimeError('This nodelist is detached!')
        iids = self.treeview.selection()
        nodes = [node for node in self._nodes if node._tk_iid in iids]
        # recursively collect children
        for node in self._nodes:
            if node.children:
                nodes += node.children.selection
        return nodes
    
        
    def __setitem__(self, idx, item):
        iid = self._nodes[idx]._tk_iid
        super().__setitem__(idx, item)
        if not self.attached: 
            return
        item = self._nodes[idx]
        item._tk_iid = iid
        self._update_item(item)
        
    def __delitem__(self, idx):
        iid = self._nodes[idx]._tk_iid
        super().__delitem__(idx)
        if not self.attached: 
            return
        self.treeview.delete(iid)
        
    def insert(self, idx, item):
        # returns actual idx (within list range) and inserted item.
        idx, item = super().insert(idx, item)
        if not self.attached: 
            return
        self._treeinsert(idx, item)
        
    def sort(self, column=None, ascending=None):
        super().sort(column, ascending)
        if not self.attached:
            return
        for idx, node in enumerate(self._nodes):
            self.treeview.move(node._tk_iid, self._parent_iid, idx)
        self._update_sortarrows()
        
    def _treeinsert(self, idx, item):
        '''create visible tree entry'''
        item._tk_iid = self.treeview.insert(self._parent_iid, idx, text=item.text)
        if item.has_children:
            self.treeview.insert(item._tk_iid, 0, text='')
        self._update_item(item)
        
    def _update_item(self, item):
        '''replace visible tree entry'''
        tv = self.treeview
        iid = item._tk_iid
        tv.item(iid, text=item.text)
        for column in self._meta.keys:
            if column == '': continue
            tv.set(iid, column, str(item[column]))
        self._update_sortarrows()
            
    def _on_node_setkey(self, node, key, val):
        super()._on_node_setkey(node, key, val)
        if not self.attached:
            return
        tv = self.treeview
        iid = node._tk_iid
        if key=='':
            tv.item(iid, text=str(val))
        else:
            tv.set(iid, key, str(val))
        if not self.sorted:
            self._update_sortarrows()
            
    def _on_node_setchildren(self, node, val):
        super()._on_node_setchildren(node, val)
        if not self.attached:
            return
        tv = self.treeview
        # TODO
            
    def _update_sortarrows(self):
        if not self.attached:
            return
        tv = self.treeview
        for key in self._meta.keys:
            tv.heading(key or '#0', image='')
        if self.sorted:
            image = _master_window.icons['sort_asc' if self._meta.sort_ascending else 'sort_desc']
            tv.heading(self._meta.sort_key or '#0', image=image)