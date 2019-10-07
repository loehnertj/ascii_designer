import logging
import re
import itertools as it

L = lambda: logging.getLogger(__name__)

__all__ = [
    'set_toolkit',
    'get_toolkit',
    'ToolkitBase',
    'auto_id',
    ]

_TOOLKIT_NAME  = 'qt'

def set_toolkit(toolkit_name):
    toolkit_name = toolkit_name.lower()
    if toolkit_name not in 'tk qt'.split(' '):
        raise ValueError('Unsupported toolkit "%s"'%toolkit_name)
    global _TOOLKIT_NAME
    _TOOLKIT_NAME = toolkit_name
    
def get_toolkit():
    if _TOOLKIT_NAME == 'tk':
        from .toolkit_tk import ToolkitTk
        return ToolkitTk()
    elif _TOOLKIT_NAME == 'qt':
        from .toolkit_qt import ToolkitQt
        return ToolkitQt()

_unique_id_dispenser = it.count()
_re_whitelist = re.compile(r'[a-zA-Z0-9_]')
def auto_id(id, text=None, last_label_id=''):
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
        id = 'x'+str(next(_unique_id_dispenser))
    return id

_re_maybe_id_text = r'(?:\s*(?P<id>[a-zA-Z0-9_]+)\s*\:)?\s*(?P<text>[^(]*?)?\s*'

class ToolkitBase:
    # (name, regex, human-readable explanation)
    grammar = [
        ('box', r'\<%s\>'%_re_maybe_id_text, '"<Text>"'),
        ('option',   r'\((?P<checked> |x)\)\s+%s$'%_re_maybe_id_text, '"( ) text" or "(x) text"'),
        ('checkbox', r'\[(?P<checked> |x)\]\s+%s$'%_re_maybe_id_text, '"[ ] Text" or "[x] Text"'),
        ('slider', r'\[\s*(?P<id>[a-zA-Z0-9_]+)\s*\:\s*(?P<min>\d+)\s*\-\+\-\s*(?P<max>\d+)\s*\]', '[id: 0 -+- 100]'),
        ('multiline',r'\[%s__\s*\]'%_re_maybe_id_text, '"[Text__]"'),
        ('textbox',r'\[%s_\s*\]'%_re_maybe_id_text, '"[Text_]"'),
        ('treelist',r'\[\s*=%s(?:\((?P<columns>.*?)\))?\s*\]'%_re_maybe_id_text, '"[= Text]" or [= Text (column1, column2, ..)]'),
        ('combo',r'\[%s_\s*(?:\((?P<values>.*?)\))?\s+v\s*\]'%_re_maybe_id_text, '"[Text_ v]" or "[Text_ (val1, val2, ...) v]'),
        ('dropdown',r'\[%s(?:\((?P<values>.*?)\))?\s+v\s*\]'%_re_maybe_id_text, '"[Text v]" or "[Text (val1, val2, ...) v]'),
        ('button', r'\[%s\]'%_re_maybe_id_text, '"[Text]"'),
        ('label', r'(?P<id>)(?:\.)?(?P<text>.+?)$', '"Text" or ".Text"'),
        ]

    menu_grammar = [
        ('sub', r'%s>'%_re_maybe_id_text, '"text >"'),
        ('command', r'''(?ix)\s*
                        (?P<id>[a-zA-Z0-9_]+\s*\:)?
                        (?P<text>[^#]+)
                        (?:\#(?P<shortcut>[a-zA-Z0-9-]+))?
                    ''', '"text :C-A-S-x"'),
    ]
    
    def __init__(self):
        self._last_label_id = ''
        
    def root(self, title='Window', on_close=None):
        '''make a root (window) widget. Optionally you can give a close handler.'''
        
    def parse(self, parent, text):
        '''Returns the widget id and widget generated from the textual definition.
        
        Autogenerates id:
        
          - If given, use it
          - else, try to use text (extract all ``a-z0-9_`` chars)
          - else, use 'x123' with 123 being a globally unique number
        
        For label type, id handling is special:
        
          - The label's id will be ``"label_"`` + id
          - The id will be remembered and used on the next widget, if it has no id.
        
        If nothing matched, return None, None.
        '''
        mangled_text = text.replace("~", ' ').strip()
        for name, regex, _ in self.grammar:
            m = re.match(regex, mangled_text)
            if m:
                d = m.groupdict()
                # special treatment for box
                if name == 'box':
                    d['given_id'] = d['id']
                d['id'] = auto_id(d['id'], d.get('text', ''), self._last_label_id)
                # Special treatment for label
                if name == 'label':
                    self._last_label_id = d['id']
                    d['id'] = 'label_'+d['id']
                else:
                    self._last_label_id = ''
                if 'text' in d:
                    d['text'] = (d['text'] or '').strip()
                L().debug('%r --> %s %r', text, name, d)
                widget = getattr(self, name)(parent, **d)
                if widget is None:
                    widget = self.label(parent, text='<UNSUPPORTED>')
                    #raise ValueError('This toolkit does not support %s widget type.'%name)
                return d['id'], widget
        raise ValueError('Could not convert widget: %r'%(text,))

    def parse_menu(self, parent, menudef, handlers):
        '''Parse menu definition list and attach to the handlers'''
        menudef = menudef[:]
        while menudef:
            item = menudef.pop(0)
            for name, regex, _ in self.menu_grammar:
                m = re.match(regex, item)
                if m:
                    d = m.groupdict()
                    d['id'] = auto_id(d['id'], d.get('text', ''))
                    if 'text' in d:
                        d['text'] = (d['text'] or '').strip()
                    L().debug('Menuentry %r --> %s %r', item, name, d)
                    if name == 'sub':
                        submenu = self.menu_sub(parent, **d)
                        self.parse_menu(submenu, menudef.pop(0), handlers)
                    elif name == 'command':
                        self.menu_command(parent, handler=getattr(handlers, d['id']), **d)
                    else:
                        raise ValueError(item)
                    break
    
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
    
    
    # ----- widget generators ------
    def box(self, parent, id=None, text='', given_id=''):
        '''An empty panel (frame, widget, however you call it) or group box that you can fill with own widgets.
        
        ``given_id`` is the user-given id value, as opposed to ``id`` (the autogenerated one).
        A Group box is created if text AND given_id are set.
        
        The virtual attribute value is the panel itself, or in case of groupbox the contained panel.
        '''
        
    def label(self, parent, id=None, label_id=None, text=''):
        '''label'''
    def button(self, parent, id=None, text=''):
        '''button'''
    def textbox(self, parent, id=None, text=''):
        '''single-line text entry box'''
    def multiline(self, parent, id=None, text=''):
        '''multiline text entry box'''
    def treelist(self, parent, id=None, text='', columns=None):
        '''treeview (also usable as plain list)'''
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

    def menu_root(self, parent):
        '''Create menu object and set as parent's menu.'''
    def menu_sub(self, parent, id, text):
        '''Append submenu labeled ``text`` to menu ``parent``.'''
    def menu_command(self, parent, id, text, shortcut, handler):
        '''Append command labeled ``text`` to menu ``parent``.

        Handler: ``func() -> None``, is immediately connected.

        ``shortcut`` follows the syntax ``(modifier)-(key)``,
        where ``modifier`` is one or more of ``C``, ``S``, ``A`` for Ctrl,
        Shift, Alt respectively.
        '''