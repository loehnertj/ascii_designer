'''This is a construction site...''' 

import tkinter as tk
from tkinter import font
from tkinter import ttk
from .toolkit import ToolkitBase

#ttk = tk


__all__ = [
    'ToolkitTk',
]

class ToolkitTk(ToolkitBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        r = self.root
        s = ttk.Style()
        # set tkinter widget fonts
        #s.configure('', font=self._sane_font)
        
        self._radiobutton_var = tk.StringVar()
        
    # widget generators
    @property
    def root(self):
        '''return the root widget'''
        if not self._root:
            self._root = tk.Tk()
            self._root.tk.call('tk', 'scaling', 2.0)
            self._root.option_add('*Font', self._sane_font)
        return self._root
        
    @property
    def _sane_font(self):
        if not hasattr(self, '_sane_font_cached'):
            self._sane_font_cached = font.Font(family='Helvetica', size=12)
        return self._sane_font_cached
    
    @root.setter
    def root(self, val):
        self._root = val
        
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
        elif isinstance(widget, tk.Entry):
            widget.bind('<Return>', lambda ev:function(widget.get()))
            widget.bind('<FocusOut>', lambda ev: function(widget.get()))
            
    def getval(self, widget):
        # FIXME
        pass
    
    def setval(self, widget, value):
        # FIXME
        pass
        
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
        
    def label(self, id=None, label_id=None, text=None):
        '''label'''
        return tk.Label(self.root, name=id, text=(text or '').strip())
        
    def button(self, id=None, text=None):
        '''button'''
        return tk.Button(self.root, name=id, text=(text or '').strip())
    
    def textbox(self, id=None, text=None):
        '''single-line text entry box'''
        return tk.Entry(self.root, name=id, text=(text or '').strip())
    
    def multiline(self, id=None, text=None):
        '''not supported'''
        
    def dropdown(self, id=None, text=None, values=None):
        return self._dropdown(id, text, values, False)
    
    def combo(self, id=None, text=None, values=None):
        return self._dropdown(id, text, values, True)
    
    def _dropdown(self, id=None, text=None, values=None, editable=False):
        '''dropdown box; values is the raw string between the parens. Only preset choices allowed.'''
        choices = [v.strip() for v in (values or '').split(',') if v.strip()]
        tv = tk.StringVar()
        tv.set((text or '').strip())
        cbo = ttk.Combobox(self.root, name=id, values=choices, textvariable=tv, state='normal' if editable else 'readonly')
        return cbo
    
    def option(self, id=None, text=None, checked=None):
        '''Option button. Prefix 'O' for unchecked, '0' for checked.'''
        rb = tk.Radiobutton(self.root,
                  text=(text or '').strip(),
                  variable=self._radiobutton_var, 
                  name=id,
                  value=id,
        )
        if checked:
            self._radiobutton_var.set(id)
        return rb
    
    def checkbox(self, id=None, text=None, checked=None):
        '''Checkbox'''
        v = tk.IntVar()
        cb = tk.Checkbutton(
            self.root,
            text=(text or '').strip(),
            name=id,
            variable=v
            )
        if checked:
            v.set(1)
        return cb
    def slider(self, id=None, min=None, max=None):
        '''slider, integer values, from min to max'''
        return tk.Scale(self.root, name=id, from_=min, to=max, orient=tk.HORIZONTAL)
    
    def external(self, id=None):
        '''external reference'''
        return getattr(self._external_reference_provider, id)
    