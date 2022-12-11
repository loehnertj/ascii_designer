import logging
import re
from collections import namedtuple
import itertools as it
from . import list_model

L = lambda: logging.getLogger(__name__)

__all__ = [
    'set_toolkit',
    'get_toolkit',
    'ToolkitBase',
    'ListBinding',
    'auto_id',
    ]

_TOOLKIT_NAME  = 'qt'
_TOOLKIT_OPTIONS = {}

def set_toolkit(toolkit_name, toolkit_options=None):
    '''Set the toolkit to use and toolkit options.

    Toolkit name can be ``tk``, ``ttk``, ``qt``.

    ``toolkit_options`` is a dictionary of toolkit specific global settings like
    font size or theme. See :py:obj:`.ToolkitTk`, :py:obj:`ToolkitQt`.
    '''
    toolkit_name = toolkit_name.lower()
    if toolkit_name not in 'tk ttk qt'.split(' '):
        raise ValueError('Unsupported toolkit "%s"'%toolkit_name)
    global _TOOLKIT_NAME
    global _TOOLKIT_OPTIONS
    _TOOLKIT_NAME = toolkit_name
    _TOOLKIT_OPTIONS = toolkit_options or {}
    
def get_toolkit():
    '''Get toolkit instance as previously set.'''
    if _TOOLKIT_NAME in ('tk', 'ttk'):
        from .toolkit_tk import ToolkitTk
        return ToolkitTk(prefer_ttk=(_TOOLKIT_NAME=='ttk'), **_TOOLKIT_OPTIONS)
    elif _TOOLKIT_NAME == 'qt':
        from .toolkit_qt import ToolkitQt
        return ToolkitQt(**_TOOLKIT_OPTIONS)

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

class TreelistColumn(
    namedtuple("TreelistColumnBase", "id text editable")
):
    """Tree/listview column definition"""

def _split_columns(columns, translations, translation_prefix):
    """Convert treelist column string to list of TreelistColumn's."""
    columns = columns or ''
    columns = [txt.strip() for txt in columns.split(',') if txt.strip()]
    def make_column(txt):
        editable = txt.endswith("_")
        if editable:
            txt = txt[:-1]
        id = auto_id('', txt)
        txt = translations.get(translation_prefix+id, txt)
        return TreelistColumn(id, txt, editable)
    return [ make_column(txt) for txt in columns ]


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
        (
            'label', 
            r'''(?x)
                (?:                                 # Optional prefix:
                    \s*(?P<id>[a-zA-Z0-9_]+)\s*:(?=.+)    # Identifier followed by : followed by something
                    | \.                            # OR single .
                )?
                (?P<text>.*?)$                      # Any text up to end of string
                ''',
            '"Text" or ".Text"'
         ),
        ]

    menu_grammar = [
        ('sub', r'%s>'%_re_maybe_id_text, '"text >"'),
        ('command', r'''(?ix)\s*
                        (?P<id>[a-zA-Z0-9_]+\s*\:)?
                        (?P<text>[^#]+)
                        (?:\#(?P<shortcut>[a-zA-Z0-9-]*))?
                    ''', '"text :C-A-S-x"'),
    ]

    default_shortcuts = {
        'new': 'C-N',
        'open': 'C-O',
        'save': 'C-S',
        'undo': 'C-Z',
        'redo': 'C-S-Z',
        'cut': 'C-X',
        'copy': 'C-C',
        'paste': 'C-P',
        'find': 'C-F',
        'refresh': 'F5',
    }

    widget_classes = {
        "label": None,
        "box": None,
        "box_labeled": None,
        "option": None,
        "checkbox": None,
        "slider": None,
        "multiline": None,
        "textbox": None,
        "treelist": None,
        "treelist_editable": None,
        "combo": None,
        "dropdown": None,
        "button": None
    }
    """Actual class to use for each widget type.
    
    This allows you to override the actual widget with a custom subclass, if
    desired.

    Obviously, this should be done *before* building the frame, e.g. in ``__init__``.

    The replacement must have the same init signature as the original widget
    class.
    """
    
    def __init__(self):
        # Make a local copy, so that mutating on an instance won't have global side effects.
        self.widget_classes = self.widget_classes.copy()
        self._last_label_id = ''

    def root(self, title='Window', icon='', on_close=None):
        '''make a root (window) widget. Optionally you can give a close handler.'''
        
    def parse(self, parent, text, translations=None, translation_prefix=""):
        '''Returns the widget id and widget generated from the textual definition.
        
        Autogenerates id:
        
          - If given, use it
          - else, try to use text (extract all ``a-z0-9_`` chars)
          - else, use 'x123' with 123 being a globally unique number
        
        For label type, id handling is special:
        
          - The label's id will be ``"label_"`` + id
          - The id will be remembered and used on the next widget, if it has no id.
        
        If nothing matched, return None, None.

        Supports automatic translation of widgets.

        - translations is a dict-like object. We will use ``.get(key, default)``
          to retrieve values.
        - ``translation_prefix`` is a global prefix, so that you can use the
          same dict for multiple forms.
        - For each widget that has ``text``, we look up
          ``<translation_prefix><id>`` in the dict. If present, the content will
          be used instead of original ``text``.
        - For treelist, we will also look up
          ``<translation_prefix><id>.<column_id>`` and use it as column name, if
          found.
        '''
        if translations is None:
            translations = {}
        mangled_text = text.replace("~", ' ').strip()
        for name, regex, _ in self.grammar:
            m = re.match(regex, mangled_text)
            if m:
                d = m.groupdict()
                # special treatment for box and label
                if name in ('box', 'label'):
                    d['given_id'] = d['id']
                d['id'] = auto_id(d['id'], d.get('text', ''), self._last_label_id)
                # Special treatment for label
                if name == 'label':
                    self._last_label_id = d['id']
                    d['id'] = d.pop('given_id', '') or 'label_'+d['id']
                else:
                    self._last_label_id = ''
                # Special treatment for treelist
                if name == 'treelist':
                    text = d.get('text', '').strip()
                    editable = d['first_column_editable'] = text.endswith('_')
                    if editable:
                        d['text'] = text[:-1]
                    prefix = translation_prefix + d["id"] + "."
                    d['columns'] = _split_columns(d.get('columns', ''), translations, prefix)
                if 'text' in d:
                    text = (d['text'] or '').strip()
                    d['text'] = translations.get(translation_prefix+d['id'], text)
                L().debug('%r --> %s %r', text, name, d)
                widget = getattr(self, name)(parent, **d)
                if widget is None:
                    widget = self.label(parent, text='<UNSUPPORTED>')
                    #raise ValueError('This toolkit does not support %s widget type.'%name)
                return d['id'], widget
        raise ValueError('Could not convert widget: %r'%(text,))

    def parse_menu(self, parent, menudef, handlers, translations=None, translation_prefix=""):
        '''Parse menu definition list and attach to the handlers.
        
        Translations work the same as for `.parse`.'''
        if translations is None:
            translations = {}
        menudef = menudef[:]
        while menudef:
            item = menudef.pop(0)
            for name, regex, _ in self.menu_grammar:
                m = re.match(regex, item)
                if m:
                    d = m.groupdict()
                    d['id'] = auto_id(d['id'], d.get('text', ''))
                    if 'text' in d:
                        text = (d['text'] or '').strip()
                        d['text'] = translations.get(translation_prefix+d['id'], text)
                    L().debug('Menuentry %r --> %s %r', item, name, d)
                    if name == 'sub':
                        submenu = self.menu_sub(parent, **d)
                        self.parse_menu(submenu, menudef.pop(0), handlers, translations, translation_prefix)
                    elif name == 'command':
                        if d['shortcut'] is None and d['id'] in self.default_shortcuts:
                            d['shortcut'] = self.default_shortcuts[d['id']]
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
    def treelist(self, parent, id=None, text='', columns=None, first_column_editable=False):
        '''treeview (also usable as plain list)
        Column is a list of column definitions: something with .id, .text, .editable attrs.
        '''
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

class ListBinding:
    '''Glue code to connect an ObsList to a GUI List widget.
    
    Takes care of:

        * Extracting column values from list items
        * Remembering/applying GUI-sorting
        * Mapping "model" events to GUI actions and vice-versa.

    Properties:
        keys (list of str)
            column keys
        list (ObsList)
            the bound list
        sort_key (str)
            column sorted by
        sort_ascending (bool)
            sort order
        sorted (bool) 
            whether list is currently sorted *by one of the list columns*.
            Sorting the list with a key function ("Python way") resets ``sorted`` to ``False``.
        factory (function() -> Any)
            Factory function for new items (on add).
            Signature might change in future releases. I am not sure right now
            what parameters might be useful.

    Abstract base class. Override methods where noted.
    '''
    def __init__(self, keys, **kwargs):
        super().__init__(**kwargs)
        self.keys = list(keys or [])
        self._sources = {k:k for k in self.keys}
        # set text source always
        self._sources.setdefault('', '')
        self.allow_sorting = True
        """Enable / disable sorting by clicking on a column header"""

        self.sort_key = None
        """column by which list is currently sorted"""
        self.sort_ascending = True
        """sorted ascending yes/no"""
        self.sorted = False
        """List is currently sorted by GUI interaction"""
        # Set a dummy list first
        self._list:list_model.ObsList = None
        self.list = list_model.ObsList(binding=self)
        """underlying list"""
        
        def no_factory():
            raise RuntimeError('In order to create items, you need to set a factory!')
        self.factory = no_factory

    @property
    def list(self) -> list_model.ObsList:
        return self._list

    @list.setter
    def list(self, val):
        if val is self._list:
            return
        self._set_list(val)
    
    def _set_list(self, val):
        '''Actual list setter. Extracted as method to allow subclassing.'''
        # detach old list if set
        l = self._list
        if l is not None:
            l.on_insert -= self.on_insert
            l.on_replace -= self.on_replace
            l.on_remove -= self.on_remove
            l.on_load_children -= self.on_load_children
            l.on_sort -= self.on_sort
            l.on_get_selection -= self.on_get_selection
            l.binding = None
        
        # attach new list
        # If the passed-in value is not an obs list, make a copy. Retain the old
        # ObsList's children source property if set.
        if not isinstance(val, list_model.ObsList):
            val = list_model.ObsList(val, binding=self, toolkit_parent_id='')
            # Copy children / has_children from previous list.
            # FIXME: This is super hacky, think about where children_source should go.
            if self._list is not None:
                val.children_source(self._list._children_source, self._list._has_children_source)
        l = self._list = val
        if l is not None:
            l.on_insert += self.on_insert
            l.on_replace += self.on_replace
            l.on_remove += self.on_remove
            l.on_load_children += self.on_load_children
            l.on_sort += self.on_sort
            l.on_get_selection += self.on_get_selection
            l.binding = self

    def sources(self, _text=None, **kwargs):
        '''Alter the data binding for each column.
        
        Takes the column names as kwargs and the data source as value; which can be:
        
            * Empty string to retrieve str(obj)
            * String ``"name"`` to retrieve attribute ``name`` from the source object
                (on attribute error, try to get as item)
            * list of one item ``['something']`` to get item ``'something'`` (think of it as index without object)
            * Callable ``lambda obj: ..`` to do a custom computation.
            
        The ``_text`` argument, if given, is used to set the source
        for the "default" (anynomous-column) value.
        '''
        for key in kwargs:
            if key not in self.keys:
                raise KeyError('No column "%s" exists'%key)
        if _text is not None:
            kwargs[''] = _text
        self._sources.update(kwargs)
    
    def retrieve(self, item, column=''):
        return list_model.retrieve(item, self._sources[column])

    def store(self, item, val, column=''):
        return list_model.store(item, val, self._sources[column])

    def sort(self, key=None, ascending:bool=None, restore=False):
        '''Sort the list using one of the columns.
        
        ``key`` can be a string, refering to the particular column of the 
        listview. Use Empty String to refer to the anonymous column.
        
        If ``key`` is a callable, the list is sorted in normal fashion.
        
        Instead of specifying ``key`` and ``ascending``, you can set
        ``restore=True`` to reuse the last applied sorting, if any.

        If ``allow_sorting`` is set to ``False``, nothing happens.
        '''
        if not self.allow_sorting:
            return
        if restore:
            key = self.sort_key
            ascending = self.sort_ascending
        if isinstance(key, str):
            keyfunc = lambda item: self.retrieve(item, key)
            info = {
                'sort_ascending': ascending,
                'sort_key': key,
            }
        else:
            # just use passed-in keyfunc, assume that it
            #doesn't match a column.
            keyfunc = key
            info = {}
        self._list.sort(
            keyfunc, 
            reverse=not ascending, 
            info=info
        )

    def on_insert(self, idx, item, toolkit_parent_id):
        '''ABSTRACT: Insert item in tree, return toolkit_id'''
    def on_replace(self, iid, item):
        '''ABSTRACT: update GUI with changed item'''
    def on_remove(self, iid):
        '''ABSTRACT: remove item in GUI'''
    def on_load_children(self, children):
        '''ABSTRACT: insert children into GUI tree'''
    def on_sort(self, sublist, info):
        '''reorder rows in GUI
        
        Base implementation remembers sort_key, sort_ascending entries
        from info, and sets ``sorted`` flag if both are there.

        Subclasses should call the base, and then update header formatting if
        appropriate.
        '''
        key = info.get('sort_key', None)
        asc = info.get('sort_ascending', None)

        if key is not None and asc is not None:
            self.sorted = True
            self.sort_key = key
            self.sort_ascending = asc
        else:
            self.sorted = False
            self.sort_key = None
            self.sort_ascending = True

    def on_get_selection(self):
        '''ABSTRACT: query selected nodes from GUI'''
