import re
import itertools as it


__all__ = [
    'set_toolkit',
    'get_toolkit',
    'ToolkitBase',
    ]

_TOOLKIT_NAME  = 'qt'

def set_toolkit(toolkit_name):
    toolkit_name = toolkit_name.lower()
    if toolkit_name not in 'tk qt'.split(' '):
        raise ValueError('Unsupported toolkit "%s"'%toolkit_name)
    global _TOOLKIT_NAME
    _TOOLKIT_NAME = toolkit_name
    
def get_toolkit(external_reference_provider=None):
    if _TOOLKIT_NAME == 'tk':
        from .toolkit_tk import ToolkitTk
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
        
    def root(self, title='Window'):
        '''make a root (window) widget'''
        
    def parse(self, parent, text):
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
        mangled_text = text.replace("~", ' ').strip()
        for name, regex, _ in self.grammar:
            m = re.match(regex, mangled_text)
            if m:
                d = m.groupdict()
                d['id'] = _auto_id(d['id'], d.get('text', ''), self._last_label_id)
                # Special treatment for label
                if name == 'label':
                    self._last_label_id = d['id']
                    d['id'] = 'label_'+d['id']
                else:
                    self._last_label_id = ''
                if 'text' in d:
                    d['text'] = (d['text'] or '').strip()
                print('%r --> %s %r'%(text, name, d))
                widget = getattr(self, name)(parent, **d)
                if widget is None:
                    widget = self.label(parent, text='<UNSUPPORTED>')
                    #raise ValueError('This toolkit does not support %s widget type.'%name)
                return d['id'], widget
        raise ValueError('Could not convert widget: %r'%(text,))
    
    def row_stretch(self, container, row, proportion):
        '''set the given row to stretch according to the proportion.'''
        
    def col_stretch(self, container, col, proportion):
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
    def getval(self, widget):
        '''get python-type value from widget.
        '''
        
    def setval(self, widget, value):
        '''update the widget from given python-type value.
        
        value-setting must not interfere with, i.e. not happen when the user 
        is editing the widget.
        '''
        
    def show(self, frame):
        '''do what is necessary to make frame appear onscreen.
        
        This should start the event loop if necessary.
        '''
        
    def close(self, frame):
        '''close the frame'''
        
    # widget generators
    def spacer(self, parent):
        '''a vertical/horizontal spacer'''
    def label(self, parent, id=None, label_id=None, text=''):
        '''label'''
    def button(self, parent, id=None, text=''):
        '''button'''
    def textbox(self, parent, id=None, text=''):
        '''single-line text entry box'''
    def multiline(self, parent, id=None, text=''):
        '''multiline text entry box'''
    def dropdown(self, parent, id=None, text='', values=None):
        '''dropdown box; values is the raw string between the parens. Only preset choices allowed.'''
    def combo(self, parent, id=None, text='', values=None):
        '''combo box; values is the raw string between the parens. Free-text allowed.'''
    def option(self, parent, id=None, text='', checked=None):
        '''Option button. Prefix 'O' for unchecked, '0' for checked.'''
    def checkbox(self, parent, id=None, text='', checked=None):
        '''Checkbox'''
    def slider(self, parent, id=None, min=None, max=None):
        '''slider, integer values, from min to max'''
    def external(self, parent, id=None):
        '''external reference. Parent is ignored.'''
        return getattr(self._external_reference_provider, id)
    