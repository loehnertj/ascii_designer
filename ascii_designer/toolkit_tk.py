'''This is a construction site...''' 

import logging
import tkinter as tk
import tkinter.font
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk
from .toolkit import ToolkitBase
from .list_model import ObsList

def L():
    return logging.getLogger(__name__)

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

def _unique(parent, id):
    try:
        parent.nametowidget(id)
    except KeyError:
        return id
    else:
        # id exists
        return ''
    
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

    Parameters:
        prefer_ttk (bool): 
            Prefer ttk widgets before tk widgets. This means that
            you need to use the Style system to set things like background color
            etc.
        setup_style (fn(root_widget) -> None): 
            custom callback for setting up style of the Tk windows (font size,
            themes). If not set, some sensible defaults are applied; see the
            other options, and source of :py:meth:`setup_style`.
        font_size (int): controls default font size of all widgets.
        ttk_theme (str): 
            explicit choice of theme. Per default, no theme is set if
            ``prefer_ttk`` is ``False``; otherwise, ``winnative`` is used if
            available, otherwise ``clam``.

    Box variable (placeholder): If you replace the box by setting its virtual 
    attribute, the replacement widget must have the same master as the box: in 
    case of normal box the frame root, in case of group box the group box. 
    Recommendation: ``new_widget = tk.Something(master=autoframe.the_box.master)``
    '''
    def __init__(self, *args, prefer_ttk:bool=False, setup_style=None, font_size:int=10, ttk_theme:str='', **kwargs):
        self._prefer_ttk = prefer_ttk
        super().__init__(*args, **kwargs)
        # FIXME: global radiobutton var - all rb's created by this toolkit instance are connected.
        # Find a better way of grouping (by parent maybe?)
        self._radiobutton_var = None
        self._font_size = font_size
        self._ttk_theme = ttk_theme
        if setup_style is not None:
            self.setup_style = setup_style

    def setup_style(self, root):
        '''Setup some default styling (dpi, font, ttk theme).

        For details, refer to the source.
        '''
        scale = root.winfo_fpixels('1i') / 72.0
        root.tk.call('tk', 'scaling', scale)
        fnt = tk.font.nametofont('TkDefaultFont')
        fnt.configure(size=self._font_size)
        root.option_add("*Font", fnt)
        # XXX does not work when opening another frame
        style = ttk.Style()
        if self._prefer_ttk:
            theme_list = style.theme_names()
            if self._ttk_theme:
                theme = self._ttk_theme
            elif 'winnative' in theme_list:
                theme = 'winnative'
            else:
                # On linux, set clam theme, which arguably is the nicest-looking of the builtin themes.
                # ttkthemes package has nicer themes, but this would lose the main advantage
                # of tk toolkit, i.e. being usable on vanilla python.
                theme = 'clam'
            style.theme_use(theme)
            color = ttk.Style().lookup("TFrame", "background", default="white")
            # Toplevel frame background is non-themed by default, fix that
            root['background'] = color
        style.configure(".", font=fnt)
        # Font size fixes for some widgets
        style.configure("Treeview.Heading", font=('Helvetica', self._font_size, 'bold'))
        style.configure("Treeview", rowheight=self._font_size*2)
        
    # widget generators
    def root(self, title='Window', icon='', on_close=None):
        '''make a root (window) widget'''
        global _master_window
        is_first = (_master_window is None)
        if is_first:
            _master_window = root = tk.Tk()
            # store as attributes so that they do not get GC'd
            root.icons = {
                key: tk.BitmapImage(name='::icons::%s'%key, data=_aa2xbm(data))
                for key, data in _ICONS.items()
            }
            self.setup_style(root)
        else:
            root = tk.Toplevel()
        root.title(title)
        if icon:
            try:
                img = tk.PhotoImage(file=icon)
                root.tk.call('wm', 'iconphoto', root._w, '-default' if is_first else '', img)
            except tk.TclError:
                # Icon files can be unreadable for several cases, don't fuzz about it.
                L().error('Could not set window icon from file %s', icon, exc_info=True)
        if on_close:
            root.protocol('WM_DELETE_WINDOW', on_close)
        return root
        
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
        if type(widget) in (tk.Frame, ttk.Frame):
            raise TypeError('Cannot assign a handler to a box.')
        elif isinstance(widget, (
            tk.Button, ttk.Button,
            tk.Scale, ttk.Scale,
        )):
            # ! different signature: button - no args, scale - 1 arg (value)
            widget.config(command=function)
        elif isinstance(widget, ScrolledText):
            widget.bind('<Return>', lambda ev:function(widget.get(1., 'end')))
            widget.bind('<FocusOut>', lambda ev: function(widget.get(1., 'end')))
        elif isinstance(widget, (tk.Entry, ttk.Entry)):
            widget.bind('<Return>', lambda ev:function(widget.variable.get()))
            widget.bind('<FocusOut>', lambda ev: function(widget.variable.get()))
        elif isinstance(widget, (
            tk.Radiobutton, ttk.Radiobutton, 
            tk.Checkbutton, ttk.Checkbutton,
        )):
            widget.config(command=lambda: function(widget.variable.get()))
        elif isinstance(widget, ttk.Treeview):
            widget.bind('<<TreeviewSelect>>', lambda ev: widget.variable.on_tv_focus(function))
        else:
            raise TypeError('Cannot autoconnect %s widget. Sorry.' % type(widget).__name__)
            
    def getval(self, widget):
        if type(widget) in (tk.Frame, ttk.Frame):
            return widget
        elif isinstance(widget, (tk.LabelFrame, ttk.LabelFrame)):
            return widget.winfo_children()[0]
        elif isinstance(widget, ScrolledText):
            return widget.get(1., 'end')
        else:
            return widget.variable.get()
    
    def setval(self, widget, value):
        if type(widget) in (tk.Frame, tk.LabelFrame, ttk.Frame, ttk.LabelFrame):
            if type(widget) in (tk.LabelFrame, ttk.LabelFrame):
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
        LabelFrame = ttk.LabelFrame if self._prefer_ttk else tk.LabelFrame
        Frame = ttk.Frame if self._prefer_ttk else tk.Frame
        id = _unique(parent, id)
        if given_id and text:
            f = LabelFrame(parent, name=id, text=text)
            inner = Frame(f)
            inner.grid(row=0, column=0, sticky='nsew')
            f.grid_rowconfigure(0, weight=1)
            f.grid_columnconfigure(0, weight=1)
        else:
            f = Frame(parent, name=id)
        return f
        
    def label(self, parent, id=None, label_id=None, text=''):
        '''label'''
        Label = ttk.Label if self._prefer_ttk else tk.Label
        id = _unique(parent, id)
        var = tk.StringVar(parent, text)
        l = Label(parent, name=id, textvariable=var)
        l.variable = var
        return l
        
    def button(self, parent, id=None, text=''):
        '''button'''
        Button = ttk.Button if self._prefer_ttk else tk.Button
        id = _unique(parent, id)
        var = tk.StringVar(parent, text)
        b = Button(parent, name=id, textvariable = var)
        b.variable = var
        return b
    
    def textbox(self, parent, id=None, text=''):
        '''single-line text entry box'''
        Entry = ttk.Entry if self._prefer_ttk else tk.Entry
        id = _unique(parent, id)
        var = tk.StringVar(parent, text)
        e = Entry(parent, name=id, textvariable=var)
        e.variable = var
        return e
    
    def multiline(self, parent, id=None, text=''):
        id = _unique(parent, id)
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
        Frame = ttk.Frame if self._prefer_ttk else tk.Frame
        Scrollbar = ttk.Scrollbar if self._prefer_ttk else tk.Scrollbar
        if columns:
            columns = [txt.strip() for txt in columns.split(',')]
        else:
            columns = []
        id = _unique(parent, id)
        keys = [name.lower() for name in columns]
        has_first_column = bool(text)
        if has_first_column:
            keys.insert(0, '')
            columns.insert(0, text.strip())
        
        # setup scrollable container
        frame = tk.Frame(parent)
        tv = ttk.Treeview(frame, columns=[k for k in keys if k])
        scb = Scrollbar(frame)
        scb.pack(side='right', fill='y')
        tv.pack(expand=1, fill='both')
        scb.config(command=tv.yview)
        tv.config(yscrollcommand=scb.set)
        # patch layout methods
        tv.pack = frame.pack
        tv.place = frame.place
        tv.grid = frame.grid
        
        tv.variable = NodelistVariable(tv, keys)
        
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
        tv.bind('<<TreeviewOpen>>', tv.variable.on_gui_expand)
        
        # set up variable
        return tv
        
    def dropdown(self, parent, id=None, text='', values=None):
        return self._dropdown(parent, id, text, values, False)
    
    def combo(self, parent, id=None, text='', values=None):
        return self._dropdown(parent, id, text, values, True)
    
    def _dropdown(self, parent, id=None, text='', values=None, editable=False):
        '''dropdown box; values is the raw string between the parens. Only preset choices allowed.'''
        id = _unique(parent, id)
        choices = [v.strip() for v in (values or '').split(',') if v.strip()]
        var = tk.StringVar(parent, text)
        cbo = ttk.Combobox(parent, name=id, values=choices, textvariable=var, state='normal' if editable else 'readonly')
        cbo.variable = var
        return cbo
    
    def option(self, parent, id=None, text='', checked=None):
        '''Option button. Prefix 'O' for unchecked, '0' for checked.'''
        Radiobutton = ttk.Radiobutton if self._prefer_ttk else tk.Radiobutton
        if not self._radiobutton_var:
            self._radiobutton_var = tk.StringVar(parent, id)
        rb = Radiobutton(parent,
                  text=text,
                  variable=self._radiobutton_var, 
                  name=_unique(parent, id),
                  value=id,
        )
        if checked.strip():
            self._radiobutton_var.set(id)
        rb.variable = self._radiobutton_var
        rb._id = id
        return rb
    
    def checkbox(self, parent, id=None, text='', checked=None):
        '''Checkbox'''
        Checkbutton = ttk.Checkbutton if self._prefer_ttk else tk.Checkbutton
        id = _unique(parent, id)
        var = tk.BooleanVar(parent, bool(checked.strip()))
        cb = Checkbutton(
            parent,
            text=(text or '').strip(),
            name=id,
            variable=var, onvalue=True, offvalue=False
            )
        cb.variable = var
        return cb
    
    def slider(self, parent, id=None, min=None, max=None):
        '''slider, integer values, from min to max'''
        Scale = ttk.Scale if self._prefer_ttk else tk.Scale
        id = _unique(parent, id)
        var = tk.DoubleVar(parent, min)
        s = Scale(
            parent,
            name=id,
            from_=min,
            to=max,
            orient=tk.HORIZONTAL,
            variable=var
        )
        s.variable = var
        return s

    def _get_underline(self, text):
        '''returns underline, text'''
        if '&' in text:
            idx = text.index('&')
            return idx, text[:idx] + text[idx+1:]
        else:
            return None, text

    def menu_root(self, parent):
        '''Create menu object and set as parent's menu.'''
        m = tk.Menu(parent, tearoff=0)
        parent.config(menu=m)
        return m

    def menu_sub(self, parent, id, text):
        '''Append submenu labeled ``text`` to menu ``parent``.'''
        m = tk.Menu(parent, tearoff=0)
        underline, text = self._get_underline(text)
        parent.add_cascade(label=text, menu=m, underline=underline)
        return m

    def menu_command(self, parent, id, text, shortcut, handler):
        '''Append command labeled ``text`` to menu ``parent``.

        Handler: ``func() -> None``, is immediately connected.
        '''
        underline, text = self._get_underline(text)
        if shortcut:
            # make Tk compatible
            parts = shortcut.split('-')
            binding = ''
            shift = False
            for p in parts[:-1]:
                p = p.upper()
                if p=='S':
                    shift=True
                    binding += 'Shift-'
                elif p=='C':
                    binding += 'Control-'
                elif p=='A':
                    binding += 'Alt-'
            cmd = parts[-1]
            if len(cmd) > 1:
                # do not touch key name
                binding += cmd
            # single letter, look at shift
            elif shift:
                binding += cmd.upper()
            else:
                binding += cmd.lower()
            toplevel = parent
            while isinstance(toplevel, tk.Menu):
                toplevel = toplevel.master
            toplevel.bind('<'+binding+'>', lambda _: handler())
        parent.add_command(label=text, command=handler, underline=underline, accelerator=shortcut)

    
class NodelistVariable:
    '''
    Use ``get`` to return the ObsList;
    ``set`` to replace the value using a new list.
    
    All the on_ methods are internal event handlers.
    '''
    def __init__(self, treeview, keys):
        self._keys = keys
        self._nl = ObsList(keys=keys, toolkit_parent_id='')
        self._nl.set_listener(self)
        self._tv = treeview
        
    def get(self):
        return self._nl
        
    def set(self, val):
        old_nl = self._nl
        if old_nl is not None:
            old_nl.set_listener(None)
            self._tv.delete(*self._tv.get_children())
        self._nl = ObsList(val, meta=old_nl._meta, toolkit_parent_id='')
        self._nl.set_listener(self)
        for idx, item in enumerate(self._nl):
            iid = self.on_insert(idx, item, '')
            self._nl.toolkit_ids[idx] = iid
            # FIXME: _nl might already have children.
            
    def item_changed(self, item):
        '''For user code, to notify GUI that you did something to ``item``
        '''
        idx = self._nl.index(item)
        self.on_replace(idx, item)

    # === ObsList handlers ===

    def on_insert(self, idx, item, toolkit_parent_id):
        '''create visible tree entry'''
        iid = self._tv.insert(
            toolkit_parent_id,
            idx,
            text=self._nl.retrieve(item)
        )
        # insert placeholder so that "+" icon appears
        if self._nl.has_children(item):
            self._tv.insert(iid, 0, text='')
        self.on_replace(iid, item)
        return iid

    def on_load_children(self, children):
        '''replace subnodes'''
        self._tv.delete(*self._tv.get_children(children.toolkit_parent_id))
        for idx, item in enumerate(children):
            iid = self.on_insert(idx, item, children.toolkit_parent_id)
            children.toolkit_ids[idx] = iid
     
    def on_replace(self, iid, item):
        '''replace visible tree entry'''
        tv = self._tv
        tv.item(iid, text=self._nl.retrieve(item))
        for column in self._keys:
            if column == '': continue
            txt = str(self._nl.retrieve(item, column))
            tv.set(iid, column, txt)
        self._update_sortarrows()
     
    def on_remove(self, iid):
         self._tv.delete(iid)
         
    def on_sort(self, nl):
        tv = self._tv
        _parent_iid = ''
        for idx, iid in enumerate(nl.toolkit_ids):
            tv.move(iid, _parent_iid,  idx)
        self._update_sortarrows()
         
    def _update_sortarrows(self):
        tv = self._tv
        for key in self._keys:
            tv.heading(key or '#0', image='')
        if self._nl.sorted:
            image = _master_window.icons['sort_asc' if self._nl._meta.sort_ascending else 'sort_desc']
            tv.heading(self._nl._meta.sort_key or '#0', image=image)
    
    def on_get_selection(self):
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
        add_nodes(self._nl)
        return nodes

    # === GUI event handlers ===
    
    def on_tv_focus(self, function):
        iid = self._tv.focus()
        if not iid:
            return
        # get the node at idx and return its ref property (the original object)
        sublist, idx = self._nl.find_by_toolkit_id(iid)
        function(sublist[idx])

    def on_gui_expand(self, stuff):
        iid = self._tv.focus()
        # retrieve the idx
        sublist, idx = self._nl.find_by_toolkit_id(iid)
        # on_load_children callback does the rest
        sublist.load_children(idx)
            
    def on_heading_click(self, key:str):
        if key == self._nl._meta.sort_key:
            ascending = True if not self._nl.sorted else not self._nl._meta.sort_ascending
        else:
            ascending = True
        self._nl.sort(key, ascending)
        
                
    
"""
        self._parent_iid = parent_iid
            
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
    
"""