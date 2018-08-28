'''This is a construction site...''' 

import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import font
from tkinter import ttk
from .toolkit import ToolkitBase

#ttk = tk


__all__ = [
    'ToolkitTk',
]

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
        self._root = None
        self._radiobutton_var = None
        
    # widget generators
    @property
    def root(self):
        '''return the root widget'''
        if not self._root:
            self._root = tk.Tk()
            self._root.tk.call('tk', 'scaling', 2.0)
            self._root.option_add('*Font', self._sane_font)
        return self._root
        
    @root.setter
    def root(self, val):
        self._root = val
        
    @property
    def _sane_font(self):
        if not hasattr(self, '_sane_font_cached'):
            self._sane_font_cached = font.Font(family='Helvetica', size=12)
        return self._sane_font_cached
    
    def show(self, frame):
        '''do what is necessary to make frame appear onscreen.'''
        frame.mainloop()
        
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
        
    def row_stretch(self, row, proportion):
        '''set the given row to stretch according to the proportion.'''
        self.root.grid_rowconfigure(row, weight=proportion)
        
    def col_stretch(self, col, proportion):
        '''set the given col to stretch according to the proportion.'''
        self.root.grid_columnconfigure(col, weight=proportion)
        
    def anchor(self, widget, left=True, right=True, top=True, bottom=True):
        sticky = ''
        if left: sticky += 'w'
        if right: sticky += 'e'
        if top: sticky += 'n'
        if bottom: sticky += 's'
        widget.grid(sticky=sticky)
        
    def spacer(self):
        '''a vertical/horizontal spacer'''
        
    def label(self, id=None, label_id=None, text=''):
        '''label'''
        var = tk.StringVar(self.root, text)
        l = tk.Label(self.root, name=id, textvariable=var)
        l.variable = var
        return l
        
    def button(self, id=None, text=''):
        '''button'''
        var = tk.StringVar(self.root, text)
        b = tk.Button(self.root, name=id, textvariable = var)
        b.variable = var
        return b
    
    def textbox(self, id=None, text=''):
        '''single-line text entry box'''
        var = tk.StringVar(self.root, text)
        e = tk.Entry(self.root, name=id, textvariable=var)
        e.variable = var
        return e
    
    def multiline(self, id=None, text=''):
        t = ScrolledText(self.root, name=id, height=3)
        t.insert('end', text)
        return t
        
    def dropdown(self, id=None, text='', values=None):
        return self._dropdown(id, text, values, False)
    
    def combo(self, id=None, text='', values=None):
        return self._dropdown(id, text, values, True)
    
    def _dropdown(self, id=None, text='', values=None, editable=False):
        '''dropdown box; values is the raw string between the parens. Only preset choices allowed.'''
        choices = [v.strip() for v in (values or '').split(',') if v.strip()]
        var = tk.StringVar(self.root, text)
        cbo = ttk.Combobox(self.root, name=id, values=choices, textvariable=var, state='normal' if editable else 'readonly')
        cbo.variable = var
        return cbo
    
    def option(self, id=None, text='', checked=None):
        '''Option button. Prefix 'O' for unchecked, '0' for checked.'''
        if not self._radiobutton_var:
            self._radiobutton_var = tk.StringVar(self._root, id)
        rb = tk.Radiobutton(self.root,
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
    
    def checkbox(self, id=None, text='', checked=None):
        '''Checkbox'''
        var = tk.BooleanVar(self._root, bool(checked.strip()))
        cb = tk.Checkbutton(
            self.root,
            text=(text or '').strip(),
            name=id,
            variable=var, onvalue=True, offvalue=False
            )
        cb.variable = var
        return cb
    
    def slider(self, id=None, min=None, max=None):
        '''slider, integer values, from min to max'''
        var = tk.IntVar(self.root, min)
        s = tk.Scale(
            self.root,
            name=id,
            from_=min,
            to=max,
            orient=tk.HORIZONTAL,
            variable=var
        )
        s.variable = var
        return s
    
    def external(self, id=None):
        '''external reference'''
        return getattr(self._external_reference_provider, id)
    