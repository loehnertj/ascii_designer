'''Pythonic list and tree classes that can be used in a GUI.

The general concept for Lists is this:

 - List is wrapped into an :any:`ObsList` (by :any:`ToolkitBase.setval`)
 - The "code-side" of the ``ObsList`` quacks (mostly) like a regular list.
 - The "gui-side" of the ``ObsList``
    - provides event callbacks for insert, replace, remove, sort.
 - a ``ListBinding``:
    - provides COLUMNS (key-value items) dynamically retrieved from each list
      item (using `retrieve` function from here)
    - remembers column and order to be used when sorting
    - has a notion of "selection" (forwarded to a callback)

'''

import logging
from collections.abc import MutableSequence
import weakref
from .event import event

__all__ = [
    'ObsList',
    'retrieve',
    'store',
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
    
    If ``source`` is a 2-tuple, use the first item ("getter") as above.
    '''
    if isinstance(source, tuple) and len(source) == 2:
        return retrieve(obj, source[0])
    elif isinstance(source, str):
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

def store(obj, val, source):
    '''Automagic storing of object properties.
    
    If ''source`` is a plain string (identifier), use ``setattr`` on ``obj``.

    If ``source`` is a list with a single string-valued item, use ``setitem`` on ``obj``.

    If ``source`` is a callable, call it as ``fn(obj, val)``.

    If ``source`` is a 2-tuple of things, use the second item ("setter") as above.

    .. note::
        `store` is not fully symmetric to its counterpart `retrieve`.

            * Empty source can not be used for `store`
            * Plain string source will always use `setitem` without fallback.

        If you use a single callable as source, it must be able to discern
        between "getter" and "setter" calls, e.g. by having a special default
        value for the second parameter.
    '''
    if isinstance(source, tuple) and len(source) == 2:
        store(obj, val, source[1])
    elif isinstance(source, str):
        if source == '':
            raise ValueError('Empty string source cannot be used to store data.')
        else:
            setattr(obj, source, val)
    elif isinstance(source, list) and len(source) == 1:
        obj[source[0]] = val
    elif callable(source):
        source(obj, val)
    else:
        raise ValueError('Could not evaluate source: %r' % source)

    
class ObsList(MutableSequence):
    '''
    Base class for treelist values.
    
    Behaves mostly like a list, except that:
     * it maintains a list of expected attributes (columns)
     * it provides notification when items are added or removed
     * it can be made into a tree by means of the ``children_source`` setting (see there).

    If configured as tree, indexing happens via tuples:

     * ``mylist[8]`` returns the 8th item at toplevel, as usual
     * ``mylist[3, 2]`` returns the 2nd item of the 3rd items' children.
     * ``mylist[3, 2, 12, 0]`` goes 4 levels deep
     * ``mylist[3, None]`` can be used to retreive the list of children of item
       3, instead of a specific child item.
     
    Attributes:
        toolkit_ids: can be indexed in the same way as the nodelist,
            and gives the toolkit-specific identifier of the list/treeview node.

    Events:

    .. note:: Events are defined with positional args for backwards-compat reasons.

    * ``on_insert(idx, item, toolkit_parent_id) -> toolkit_id``: function to call for each inserted item
    * ``on_replace(toolkit_id, item)``: function to call for replaced item
        Replacement of item implies that children are "collapsed" again.
    * ``on_remove(toolkit_id)``: function to call for each removed item
    * ``on_load_children(sublist)``: function when children of a node are retrieved.
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

    @event(by_name=False)
    def on_insert(self, idx:int, item, toolkit_parent_id):
        """Event: An item was inserted.

        Parameters:
            idx (int): insertion position
            item: Inserted item
            toolkit_parent_id: 
                In case of tree structure, the toolkit id of the
                lists's parent in the view.

        The handler must return the "Toolkit ID" of the inserted item, which
        is is stored in the `.toolkit_id` list. Toolkit ID can be of any type
        (e.g string or QModelIndex).
        """

    @event(by_name=False)
    def on_replace(self, toolkit_id, item):
        """Event: Item with the associated toolkit ID was replaced by the given one.
    
        Replacement of item implies that children are "collapsed" again.
        """

    @event(by_name=False)
    def on_remove(self, toolkit_id):
        """Event: item with the given toolkit_id was removed."""

    @event(by_name=False)
    def on_load_children(self, sublist:"ObsList"):
        """Event: children of a node were retrieved."""

    @event(by_name=False)
    def on_get_selection(self):
        """Event: .selection property is retrieved

        Meaning that we need the selection from the GUI.

        Handler must return the items selected in the GUI. Must return a List of
        (original) items.
        """
        # FIXME: Code smell here. Instead of misusing the event mechanism, the
        # ListVariable should rather set a callback on the list object.

    @event(by_name=False)
    def on_sort(self, sublist:"ObsList", info: dict):
        """Indicates that the given ``sublist`` was sorted.

        ``info`` is a dictionary of sort settings (key, direction).
        """

    @property
    def binding(self):
        '''Weak reference to the binding using this list.
        
        If list is attached to multiple Bindings, last one wins. (TODO: make it a list)
        '''
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

    def load_children(self, idx_tuple):
        '''Retrieves the childlist of item at given idx.
        '''
        source = self._children_source
        if not source: # not a tree
            return
        lst, idx = self._list_idx(idx_tuple) 
        item = lst._nodes[idx]
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
        lst._childlists[idx] = childlist
        lst.on_load_children(childlist)

    def get_children(self, idx_tuple):
        '''Get childlist of item at given idx, loading it if not already loaded.'''
        lst, idx = self._list_idx(idx_tuple)
        if lst._childlists[idx_tuple] is None:
            self.load_children(idx_tuple)
        return lst._childlists[idx]

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

        Returns ``(sublist: ObsList, idx: int)``.

        If not found, raises ValueError.  Scans the whole tree for the item.
        '''
        return self._find(item, False, False)

    def find2(self, item):
        '''Finds the tuple-index of the item.

        Returns ``idx: Tuple[int]``.

        If not found, raises ValueError.  Scans the whole tree for the item.
        '''
        return self._find(item, False, True)

    def find_by_toolkit_id(self, toolkit_id):
        '''finds the sublist and index of the item having the given toolkit id.
        
        Returns ``(sublist: ObsList, idx: int)``.

        If not found, raises ValueError.  Scans the whole tree for the item.
        '''
        return self._find(toolkit_id, True, False)

    def find_by_toolkit_id2(self, item):
        '''Finds the tuple-index of the item having the given toolkit id.

        Returns ``idx: Tuple[int]``.

        If not found, raises ValueError.  Scans the whole tree for the item.
        '''
        return self._find(item, True, True)

    def _find(self, needle, is_tkid, return_idx_tuple):
        """Implementation of find."""
        lst = self.toolkit_ids if is_tkid else self._nodes
        try:
            idx = lst.index(needle)
            # if we got here, we found it
            if return_idx_tuple:
                return (idx,)
            else:
                return self, idx
        except ValueError:
            # Not in own items, search children
            for n, childlist in enumerate(self._childlists):
                if childlist is None:
                    continue
                try:
                    result = childlist._find(needle, is_tkid, return_idx_tuple)
                except ValueError:
                    continue
                else:
                    if return_idx_tuple:
                        return (n,) + result
                    else:
                        return result
        # not found
        raise ValueError(f'{"Toolkit ID " if is_tkid else "Item"} not in tree', needle)

    def _list_idx(self, idx_tuple):
        if isinstance(idx_tuple, tuple):
            lst = self
            for idx in idx_tuple[:-1]:
                lst = lst._childlists[idx]
            return lst, idx_tuple[-1]
        else:
            return self, idx_tuple

    def __getitem__(self, idx_tuple):
        lst, idx = self._list_idx(idx_tuple)
        return lst if idx is None else lst._nodes[idx]
        
    def __len__(self):
        return len(self._nodes)
    
    def __setitem__(self, idx_tuple, item):
        lst, idx = self._list_idx(idx_tuple)
        lst._nodes[idx] = item
        # collapse
        lst._childlists[idx] = None
        lst.sorted = False
        lst.on_replace(self.toolkit_ids[idx], item)
        
    def __delitem__(self, idx_tuple):
        lst, idx = self._list_idx(idx_tuple)
        del lst._nodes[idx]
        lst._childlists.pop(idx)
        tkid = lst.toolkit_ids.pop(idx)
        lst.on_remove(tkid)
        
    def insert(self, idx_tuple, item):
        lst, idx = self._list_idx(idx_tuple)
        N = len(lst._nodes)
        if idx<0:
            idx += N
            if idx<0: idx = 0
        else:
            if idx > N: idx = N
        lst._nodes.insert(idx, item)
        # cannot use "truthy" value since list might be empty
        lst._childlists.insert(idx, None)
        lst.sorted = False
        tkid = lst.on_insert(idx, item, self.toolkit_parent_id)
        lst.toolkit_ids.insert(idx, tkid)
        return idx, item

    def item_mutated(self, item):
        '''Call this when you mutated the item (which must be in this list)
        and want to update the GUI.
        '''
        idx = self._nodes.index(item)
        # do NOT collapse
        self.sorted = False
        self.on_replace(self.toolkit_ids[idx], item)
