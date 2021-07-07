'''Pythonic list and tree classes that can be used in a GUI.

The general concept for Lists is this:

 - List is wrapped into an :any:`ObsList` (by :any:`ToolkitBase.setval`)
 - The "code-side" of the ``ObsList`` quacks (mostly) like a regular list.
 - The "gui-side" of the ``ObsList``
    - provides COLUMNS (key-value items) dynamically retrieved from each list
      item
    - remembers column and order to be used when sorting
    - has a notion of "selection" (forwarded to a callback)
    - provides event callbacks for insert, replace, remove, sort.
 - Internally, the :any:`ListMeta` class holds the state data for those
   functions.

'''

import logging
from collections.abc import MutableSequence
import weakref
from .event import EventSource

__all__ = [
    'ObsList',
    'retrieve',
    'ListMeta',
    ]

L = lambda: logging.getLogger(__name__)

def _do_nothing(*args, **kwargs):
    pass

def retrieve(obj, source):
    '''Automagic retrieval of object properties.

    If ``source`` is empty string, return ``str(obj)``.

    If ``source`` is a plain string (identifier), use ``getattr`` on ``obj``; on
    error, try ``getitem``.

    If ``source`` is a list with a single string-valued item, use ``getitem`` on
    ``obj``.

    If ``source`` is a callable, return ``source(obj)``.
    '''
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

    
class ObsList(MutableSequence):
    '''
    Base class for treelist values.
    
    Behaves mostly like a list, except that:
     * it maintains a list of expected attributes (columns)
     * it provides notification when items are added or removed
     
    Attributes:
        meta (:any:`ListMeta`): Container for keys, source functions and remembered sorting. 
        toolkit_ids: can be indexed in the same way as the nodelist,
            and gives the toolkit-specific identifier of the list/treeview node.

    Events:

        * ``on_insert(idx, item, toolkit_parent_id) -> toolkit_id``: function to call for each inserted item
        * ``on_replace(toolkit_id, item)``: function to call for replaced item
            Replacement of item implies that children are "collapsed" again.
        * ``on_remove(toolkit_id)``: function to call for each removed item
        * ``on_load_children(toolkit_parent_id, sublist)``: function when children of a node are retrieved.
        * ``on_get_selection()``: return the items selected in the GUI
            Must return a List of (original) items.
        * ``on_sort(sublist, info)``: when list is reordered

    For ``on_insert``, the handler should return the toolkit_id. This is an
    unspecified, toolkit-native object identifier. It is used in the other
    events and for ``find_by_toolkit_id``. Its purpose is to allow easier
    integration with toolkit-native events and methods.

    ``on_sort``: Info argument is a dict containing custom info, e.g. column
    that was sorted by.
    '''
    def __init__(self, iterable=None, binding=None, toolkit_parent_id=None):
        # TODO: binding is only needed to forward .source(), and causes lots of
        # headache. How to get rid of it?
        self.binding = binding
        self._children_source = None
        self._has_children_source = None
        if iterable:
            self._nodes = [item for item in iterable]
        else:
            self._nodes = []
        self.toolkit_parent_id = toolkit_parent_id
        self.toolkit_ids = [None] * len(self._nodes)
        # If List is turned into a tree by setting children_source,
        # this is made into a list of child ObsList.
        # Initially all children are set to None, and will be loaded
        # lazily by explicit call to ``load_children``.
        self._childlists = [None]*len(self._nodes)
        def dummy_handler(*args, **kwargs):
            return None
        # key, reverse, info
        self._sort_info = (None, False, {})

        # Events
        self.on_insert = EventSource()
        self.on_replace = EventSource()
        self.on_remove = EventSource()
        self.on_sort = EventSource()
        self.on_load_children = EventSource()
        self.on_get_selection = EventSource()

    @property
    def binding(self):
        return self._binding()

    @binding.setter
    def binding(self, val):
        if val is None:
            self._binding = lambda: None
        else:
            self._binding = weakref.ref(val)
    
        
    @property
    def selection(self):
        '''returns the sublist of all currently-selected items.
        
        Returns empty list if no handler is attached.
        '''
        selection = self.on_get_selection() or []
        return selection
    
    def sources(self, _text=None, **kwargs):
        '''Forwards to `ListBinding.sources` - see there.
        '''
        binding = self.binding
        if binding is None:
            raise RuntimeError('Cannot set sources of detached ObsList')
        binding.sources(_text=_text, **kwargs)
        
    def children_source(self, children_source, has_children_source=None):
        '''Sets the source for children of each list item, turning the list into a tree.
        
        ``children``, ``has_children`` follow the same semantics as other sources.
        
        Resolving ``children`` should return an iterable that will be turned 
        into an ``ObsList`` of its own.
        
        ``has_children`` should return a truthy value that is used to decide 
        whether to display the expander. If omitted, all nodes get the expander 
        initially if children_source is set.
        
        Children source only applies when the list of children is initially 
        retrieved. Once the children are retrieved, source changes do not affect 
        already-retrieved children anymore.
        
        ``has_children`` is usually evaluated immediately, because the treeview 
        needs to decide whether to display an expander icon.
        '''
        self._children_source = children_source
        if not has_children_source:
            has_children_source = (lambda obj: True)
        self._has_children_source = has_children_source
        self._childlists = [None] * len(self._nodes)

    def has_children(self, item):
        if not self._children_source:
            return False
        return retrieve(item, self._has_children_source)

    def load_children(self, idx):
        '''Retrieves the childlist of item at given idx.
        '''
        source = self._children_source
        if not source: # not a tree
            return
        item = self._nodes[idx]
        childlist = retrieve(item, source)
        childlist = ObsList(childlist, toolkit_parent_id=self.toolkit_ids[idx])
        # Child SHARES event handlers and child source
        childlist._children_source = self._children_source
        childlist._has_children_source = self._has_children_source
        childlist.on_insert = self.on_insert
        childlist.on_replace = self.on_replace
        childlist.on_remove = self.on_remove
        childlist.on_load_children = self.on_load_children
        childlist.on_sort = self.on_sort
        childlist.on_get_selection = self.on_get_selection
        self._childlists[idx] = childlist
        self.on_load_children(childlist)

    def get_children(self, idx):
        '''Get childlist of item at given idx, loading it if not already loaded.'''
        if self._childlists[idx] is None:
            self.load_children(idx)
        return self._childlists[idx]

    def sort(self, key=None, reverse=False, info=None, restore=False):
        '''Sort the list.

        ``info`` is optional information to be passed on to on_sort.

        Set ``restore`` to reuse key and info from last ``sort`` call.
        '''
        if restore:
            key, reverse, info = self._sort_info
        self._sort_info = (key, reverse, info)
        if key is None: 
            key=lambda x: x
        sl = [ 
            (item, iid, childlist) 
            for item, iid, childlist in zip(
                self._nodes, self.toolkit_ids, self._childlists
            )
        ]
        sl.sort(key=lambda t: key(t[0]), reverse=reverse)
        self._nodes = [t[0] for t in sl]
        self.toolkit_ids = [t[1] for t in sl]
        self._childlists = [t[2] for t in sl]
        self.on_sort(self, info=info or {})
        # FIXME: sort childlists as well?

    def find(self, item):
        '''Finds the sublist and index of the item.

        Returns ``(sublist: ObsList, idx:int)``.

        If not found, raises ValueError.
        
        Scans the whole tree for the item.
        '''
        try:
            idx = self._nodes.index(item)
            # if we got here, we found it
            return self, idx
        except ValueError:
            # Not in own items, search children
            for childlist in self._childlists:
                if childlist is None:
                    continue
                try:
                    return childlist.find(item)
                except ValueError:
                    continue
        # not found
        raise ValueError('Item not in tree', item)

    def find_by_toolkit_id(self, toolkit_id):
        '''finds the sublist and index of the item having the given toolkit id.
        
        Returns ``(sublist: ObsList, idx: int)``

        If not found, raises ValueError.

        Scans the whole tree for the item.
        '''
        try:
            idx = self.toolkit_ids.index(toolkit_id)
            # if we got here, we found it
            return self, idx
        except ValueError:
            # Not in own items, search children
            for childlist in self._childlists:
                if childlist is None:
                    continue
                try:
                    return childlist.find_by_toolkit_id(toolkit_id)
                except ValueError:
                    continue
        # not found
        raise ValueError('Toolkit ID not in tree', toolkit_id)

    def __getitem__(self, idx):
        return self._nodes[idx]
        
    def __len__(self):
        return len(self._nodes)
    
    def __setitem__(self, idx, item):
        self._nodes[idx] = item
        # collapse
        self._childlists[idx] = None
        self.sorted = False
        self.on_replace(self.toolkit_ids[idx], item)
        
    def __delitem__(self, idx):
        del self._nodes[idx]
        self._childlists.pop(idx)
        tkid = self.toolkit_ids.pop(idx)
        self.on_remove(tkid)
        
    def insert(self, idx, item):
        N = len(self._nodes)
        if idx<0:
            idx += N
            if idx<0: idx = 0
        else:
            if idx > N: idx = N
        self._nodes.insert(idx, item)
        # cannot use "truthy" value since list might be empty
        self._childlists.insert(idx, None)
        self.sorted = False
        tkid = self.on_insert(idx, item, self.toolkit_parent_id)
        self.toolkit_ids.insert(idx, tkid)
        return idx, item

    def item_mutated(self, item):
        '''Call this when you mutated the item (which must be in this list)
        and want to update the GUI.
        '''
        idx = self._nodes.index(item)
        # do NOT collapse
        self.sorted = False
        self.on_replace(self.toolkit_ids[idx], item)
