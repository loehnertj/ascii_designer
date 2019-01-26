import logging
import re
import itertools as it
from collections.abc import MutableSequence

L = lambda: logging.getLogger(__name__)

__all__ = [
    'set_toolkit',
    'get_toolkit',
    'ToolkitBase',
    'NodelistBase',
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

_re_maybe_id_text = r'(?:\s*(?P<id>[a-zA-Z0-9_]+)\s*\:)?\s*(?P<text>[^(]+?)?\s*'

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
        
        
class NodesMeta():
    '''holds the metadata of a NodeList or Node.'''
    def __init__(self, keys):
        self.keys = list(keys or [])
        self.sources = {k:k for k in self.keys}
        self.children_source = None
        self.has_children_source = None
        self.sort_key = None
        self.sort_ascending = None
        
    def copy(self):
        nm = NodesMeta(self.keys)
        nm.sources = self.sources.copy()
        nm.children_source = self.children_source
        nm.has_children_source = self.has_children_source
        nm.sort_key = self.sort_key
        nm.sort_ascending = self.sort_ascending
        return nm
        
    def retrieve(self, obj, source):
        if isinstance(source, str):
            if source == '':
                return str(obj)
            else:
                try:
                    return getattr(obj, source)
                except AttributeError as e:
                    try:
                        return obj[source]
                    except TypeError:
                        # raise original exception
                        raise e
        elif isinstance(source, list) and len(source)==1:
            return obj[source[0]]
        elif callable(source):
            return source(obj)
        else:
            raise ValueError('Could not evaluate source: %r'%source)
        
    
class NodelistBase(MutableSequence):
    '''
    Base class for treelist values.
    
    Behaves mostly like a list, except that:
     * it maintains a list of expected attributes (columns)
     * all inserted items are automatically converted to a Node object.
     
    The node list is usually attached to an actual treeview, but can become 
    detached if the tree "value" is replaced but a reference to the old list is 
    retained. In the same way, individual nodes can become detached when popped 
    out of the list.
     
    Subclasses should implement the display update logic on modification.
    '''
    def __init__(self, iterable=None, keys=None, meta=None):
        if meta:
            self._meta = meta.copy()
        else:
            self._meta = NodesMeta(keys)
        self.attached = True
        if iterable:
            self._nodes = [self._node_from(item) for item in iterable]
        else:
            self._nodes = []
        self.sorted = False
            
    @property
    def selection(self):
        '''returns the sublist of all currently-selected items.
        
        Raises RuntimeError if the nodelist is detached.
        '''
        raise RuntimeError('NodelistBase has no selection')
    
    def sources(self, **kwargs):
        '''Alter the data binding for each column.
        
        Takes the column names as kwargs and the data source as value; which can be:
        
            * Empty string to retrieve str(obj)
            * String ``"name"`` to retrieve attribute ``name`` from the source object
                (on attribute error, try to get as item)
            * list of one item ``['something']`` to get item ``'something'`` (think of it as index without object)
            * Callable ``lambda obj: ..`` to do a custom computation.
        '''
        for key in kwargs:
            if key not in self._meta.keys:
                raise KeyError('No column "%s" exists'%key)
        self._meta.sources.update(kwargs)
        
    def children(self, children_source, has_children_source=None):
        '''Sets the source for children of each node, turning the list into a tree.
        
        ``children``, ``has_children`` follow the same semantics as other sources.
        
        Resolving ``children`` should return an iterable that will be turned into a NodeList according to the rules.
        
        ``has_children`` should return a truthy value that is used to decide whether to display the expander. If omitted, all nodes get the expander initially.
        '''
        self._meta.children_source = children_source
        self._meta.has_children_source = has_children_source
        
    def sort(self, key:str=None, ascending:bool=None):
        '''sort the list. If key and/or ascending are not given, the settings from Meta (i.e. last used settings) are used.
        '''
        if key is None:
            key = self._meta.sort_key
        if ascending is None:
            ascending = self._meta.sort_ascending
        self._meta.sort_key = key
        self._meta.sort_ascending = ascending
        self._nodes.sort(key=lambda node: node[key], reverse=not ascending)
        self.sorted = True
        
    def __getitem__(self, idx):
        return self._nodes[idx]
        
    def __len__(self):
        return len(self._nodes)
    
    def __setitem__(self, idx, item):
        self._nodes[idx].detach()
        self._nodes[idx] = self._node_from(item)
        self.sorted = False
        
    def __delitem__(self, idx):
        self._nodes[idx].detach()
        del self._nodes[idx]
        
    def insert(self, idx, item):
        node = self._node_from(item)
        N = len(self._nodes)
        if idx<0:
            idx += N
            if idx<0: idx = 0
        else:
            if idx > N: idx = N
        self._nodes.insert(idx, node)
        self.sorted = False
        return idx, node
    
    def _on_node_setkey(self, node, key, value):
        # callback when a node value (key) is changed.
        # subclass should update view.
        if key == self._meta.sort_key:
            self.sorted = False
    
    def _node_from(self, item):
        return Node(self, item, self._meta)
    
class Node(dict):
    '''Node(nodelist, obj, sources)
    
    Params:
        nodelist (:any:`NodelistBase`): the nodelist including this node (for calling back when node is changed)
        obj (any): source object
        sources (dict): sources dict
        
    ``soures`` defines which columns to retrieve and how. The keys are the column names. The values can be:
    
        * Empty string to retrieve str(obj)
        * String ``"name"`` to retrieve attribute ``name`` from the source object
            (on attribute error, try to get as item)
        * list of one item ``['something']`` to get item ``'something'`` (think of it as index without object)
        * Callable ``lambda obj: ..`` to do a custom computation.
    '''
    def __init__(self, nodelist, obj, meta, attached=None):
        # initially set to 'no nodelist' to disable callbacks
        self.nodelist = None
        self.text = ''
        self.ref = obj
        self._meta = meta
        self._children = None
        for key, source in self._meta.sources.items():
            self[key] = self._meta.retrieve(obj, source)
            if key=='':
                self.text = self[key]
        self.nodelist = nodelist
        
    @property
    def has_children(self):
        if self._meta.has_children_source:
            return True
        return self._meta.retrieve(self.ref, self._meta.has_children_source)
    
    @property
    def children(self):
        '''retrieve list of children. Cached on first call.'''
        if self._children is None:
            if self._meta.children_source is None:
                self._children = []
            else:
                self._children = self._meta.retrieve(self.ref, self._meta.children_source)
        return self._children
    
    def detach(self):
        self.nodelist = None
        
    def __setitem__(self, key, val):
        super().__setitem__(key, val)
        if self.nodelist:
            self.nodelist._on_node_setkey(self, key, val)
            
    def __setattr__(self, key, val):
        super().__setattr__(key, val)
        if key == 'text':
            if self.nodelist:
                self.nodelist._on_node_setkey(self, key, val)
        
    def __repr__(self):
        items = '\, '.join('%r: %r'%(k, v) for k, v in self.items())
        return 'Node({%s}, attached=%r)'%(items, (self.nodelist is not None))
        
def test_nodelist():
    n = NodelistBase([
            {'name':1, 'rank':2},
            {'name':3, 'rank':4}
        ], 
        keys='name rank'.split()
    )
    L().info(n._nodes)
    x = n.pop(0)
    L().info(n._nodes)
    L().info('popped:', x)
    x2 = {'name':5, 'rank':6}
    n += [x2]
    L().info(n._nodes)
    
if __name__=='__main__':
    test_nodelist()