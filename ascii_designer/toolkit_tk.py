'''This is a construction site...''' 

import tkinter as tk
from .toolkit import ToolkitBase

__all__ = [
    'ToolkitTk',
]

class ToolkitTk(ToolkitBase):
    # widget generators
    @property
    def root(self):
        '''return the root widget'''
        if not self._root:
            self._root = tk.Tk()
        return self._root
        
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
        elif isinstance(widget, tk.OptionMenu):
            widget.config(command=function)
            
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
        return tk.Label(self.root, text=(text or '').strip())
        
    def button(self, id=None, text=None):
        '''button'''
        return tk.Button(self.root, text=(text or '').strip())
    
    def textbox(self, id=None, text=None):
        '''single-line text entry box'''
        return tk.Entry(self.root, text=(text or '').strip())
    
    def multiline(self, id=None, text=None):
        '''not supported'''
    
    def dropdown(self, id=None, text=None, values=None):
        '''dropdown box; values is the raw string between the parens. Only preset choices allowed.'''
        choices = [v.strip() for v in (values or '').split(',') if v.strip()]
        return tk.OptionMenu(self.root, '',(text or '').strip(), *choices)
    
    def combo(self, id=None, text=None, values=None):
        '''not supported'''
        
    def option(self, id=None, text=None, checked=None):
        '''Option button. Prefix 'O' for unchecked, '0' for checked.'''
    def checkbox(self, id=None, text=None, checked=None):
        '''Checkbox'''
    def slider(self, id=None, min=None, max=None):
        '''slider, integer values, from min to max'''
    def external(self, id=None):
        '''external reference'''
        return getattr(self._external_reference_provider, id)
    