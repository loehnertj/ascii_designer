import re
import itertools as it

import tkinter as tk

__all__ = [
    'set_toolkit',
    'get_toolkit',
    'ToolkitBase',
    ]

_TOOLKIT_NAME  = 'tk'

def set_toolkit(toolkit_name):
    toolkit_name = toolkit_name.lower()
    if toolkit_name not in 'tk qt'.split(' '):
        raise ValueError('Unsupported toolkit "%s"'%toolkit_name)
    global _TOOLKIT_NAME
    _TOOLKIT_NAME = toolkit_name
    
def get_toolkit(external_reference_provider=None):
    if _TOOLKIT_NAME == 'tk':
        return ToolkitTk(external_reference_provider=external_reference_provider)
    elif _TOOLKIT_NAME == 'qt':
        from .toolkit_qt import ToolkitQt
        return ToolkitQt(external_reference_provider=external_reference_provider)

_unique_id_dispenser = it.count()
_re_whitelist = re.compile(r'[a-zA-Z0-9_]')
def _auto_id(id, text=None, last_label_id=''):
    '''for missing id, calculate one from text.'''
    if id:
        return id.casefold()
    text = text or ''
    text = text.strip().casefold().replace(" ", "_")
    good_chars = [c for c in text if _re_whitelist.match(c)]
    id = ''.join(good_chars)
    if id[0:1].isnumeric():
        id = 'x'+id
    if not id:
        id = last_label_id
    if not id:
        id = 'x'+next(_unique_id_dispenser)
    return id

_re_maybe_id_text = r'(?:\s*(?P<id>[a-zA-Z0-9_]+)\s*\:)?\s*(?P<text>.+?)?\s*'

class ToolkitBase:
    # (name, regex, human-readable explanation)
    grammar = [
        ('external', r'\*(?P<id>[a-zA-Z0-9_]+)', '*identifier'),
        ('option',   r'\((?P<checked> |x)\)\s+%s$'%_re_maybe_id_text, '"O text" or "0 text"'),
        ('checkbox', r'\[(?P<checked> |x)\]\s+%s$'%_re_maybe_id_text, '"[ ] Text" or "[x] Text"'),
        ('slider', r'\[\s*(?P<id>[a-zA-Z0-9_]+)\s*\:\s*(?P<min>\d+)\s*\-\+\-\s*(?P<max>\d+)\s*\]', '[id: 0 -+- 100]'),
        ('multiline',r'\[%s__\s*\]'%_re_maybe_id_text, '"[Text__]"'),
        ('textbox',r'\[%s_\s*\]'%_re_maybe_id_text, '"[Text_]"'),
        ('combo',r'\[%s_\s*(?:\((?P<values>.*?)\))?\s+v\s*\]'%_re_maybe_id_text, '"[Text_]"'),
        ('dropdown',r'\[%s(?:\((?P<values>.*?)\))?\s+v\s*\]'%_re_maybe_id_text, '"[Text_]"'),
        ('button', r'\[%s\]'%_re_maybe_id_text, '"[Text]"'),
        ('label', r'(?P<id>)(?:\.)?(?P<text>.+?)$', '"Text" or ".Text"'),
        ]
    
    def __init__(self, external_reference_provider):
        self._external_reference_provider = external_reference_provider
        self._last_label_id = ''
        # root widget; autogenerated on request
        self._root = None
        
    def parse(self, text):
        '''Returns the widget id and widget generated from the textual definition.
        
        Autogenerates id:
        - If given, use it
        - else, try to use text (extract all a-z0-9_ chars)
        - else, use 'x123' with 123 being a globally unique number
        
        For label type, id handling is special:
            - The label's id will be "label_" + id
            - The id will be remembered and used on the next widget, if it has no id.
        
        If nothing matched, return None, None.
        '''
        text = text.strip().replace("~", ' ')
        for name, regex, _ in self.grammar:
            m = re.match(regex, text.strip())
            if m:
                d = m.groupdict()
                d['id'] = _auto_id(d['id'], d.get('text', ''), self._last_label_id)
                # Special treatment for label
                if name == 'label':
                    self._last_label_id = d['id']
                    d['id'] = 'label_'+d['id']
                else:
                    self._last_label_id = ''
                print(name, d)
                widget = getattr(self, name)(**d)
                if widget is None:
                    widget = self.label(text='<UNSUPPORTED>')
                    #raise ValueError('This toolkit does not support %s widget type.'%name)
                return d['id'], widget
        raise ValueError('Could not convert widget: %r'%(text,))
    
    def row_stretch(self, row, proportion):
        '''set the given row to stretch according to the proportion.'''
        
    def col_stretch(self, col, proportion):
        '''set the given col to stretch according to the proportion.'''
        
    def anchor(self, widget, left=True, right=True, top=True, bottom=True):
        '''anchor the widget. Depending on the anchors, widget will be left-, 
        right-, center-aligned or stretched.
        '''
    
    def place(self, widget, row=0, col=0, rowspan=1, colspan=1):
        '''place widget'''
        
    def connect(self, widget, function):
        '''bind the widget's default event to function.
        
        Default event is:
         * click() for a button
         * value_changed(new_value) for value-type controls;
            usually fired after focus-lost or Return-press.
        '''
        
    def show(self, frame):
        '''do what is necessary to make frame appear onscreen.'''
        
    def close(self, frame):
        '''close the frame'''
        
    # widget generators
    @property
    def root(self):
        '''return the root widget'''
        
    def spacer(self):
        '''a vertical/horizontal spacer'''
    def label(self, id=None, label_id=None, text=None):
        '''label'''
    def button(self, id=None, text=None):
        '''button'''
    def textbox(self, id=None, text=None):
        '''single-line text entry box'''
    def multiline(self, id=None, text=None):
        '''multiline text entry box'''
    def dropdown(self, id=None, text=None, values=None):
        '''dropdown box; values is the raw string between the parens. Only preset choices allowed.'''
    def combo(self, id=None, text=None, values=None):
        '''combo box; values is the raw string between the parens. Free-text allowed.'''
    def option(self, id=None, text=None, checked=None):
        '''Option button. Prefix 'O' for unchecked, '0' for checked.'''
    def checkbox(self, id=None, text=None, checked=None):
        '''Checkbox'''
    def slider(self, id=None, min=None, max=None):
        '''slider, integer values, from min to max'''
    def external(self, id=None):
        '''external reference'''
        return getattr(self._external_reference_provider, id)
    
    
class ToolkitTk(ToolkitBase):
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
        
    def show(self, frame):
        '''do what is necessary to make frame appear onscreen.'''
        frame.mainloop()
        
    def close(self, frame):
        '''close the frame'''
        frame.destroy()
        
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
        
    # widget generators
    @property
    def root(self):
        '''return the root widget'''
        if not self._root:
            self._root = tk.Tk()
        return self._root
        
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
    