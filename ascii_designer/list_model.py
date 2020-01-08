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

__all__ = [
    'ObsList',
    'ListMeta',
    ]

L = lambda: logging.getLogger(__name__)

def _do_nothing(*args, **kwargs):
    pass

class ListMeta():
    '''holds the metadata of a ObsList.'''
    def __init__(self, keys):
        self.keys = list(keys or [])
        self.sources = {k:k for k in self.keys}
        # set text source always
        self.sources.setdefault('', '')
        self.children_source = None
        self.has_children_source = None
        self.sort_key = ''
        self.sort_ascending = True
        self.listener = None

    def get_observer(self, name):
        try:
            handler = getattr(self.listener, 'on_'+name)
        except AttributeError:
            handler = _do_nothing
        return handler
        
    def copy(self):
        nm = ListMeta(self.keys)
        nm.sources = self.sources.copy()
        nm.children_source = self.children_source
        nm.has_children_source = self.has_children_source
        nm.sort_key = self.sort_key
        nm.sort_ascending = self.sort_ascending
        nm.listener = self.listener
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
        
    
class ObsList(MutableSequence):
    '''
    Base class for treelist values.
    
    Behaves mostly like a list, except that:
     * it maintains a list of expected attributes (columns)
     * it provides notification when items are added or removed
     
    Attributes:
        meta (:any:`ListMeta`): Container for keys, source functions and remembered sorting. 
        sorted (bool): whether list is currently sorted *by one of the list columns*.
            Sorting the list with a key function ("Python way") resets ``sorted`` to ``False``.
        toolkit_ids: can be indexed in the same way as the nodelist,
            and gives the toolkit-specific identifier of the list/treeview node.
    '''
    def __init__(self, iterable=None, keys=None, meta=None, toolkit_parent_id=None):
        if meta:
            self._meta = meta.copy()
        else:
            self._meta = ListMeta(keys)
        self.attached = True
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
        self.sorted = False
        
    @property
    def selection(self):
        '''returns the sublist of all currently-selected items.
        
        Raises RuntimeError if the nodelist is detached.
        '''
        handler = self._meta.get_observer('get_selection')
        return handler()

    def set_listener(self, listener):
        '''Set listener that observes the list.

        The listener can provide any or all of the following methods:

        * ``on_insert(idx, item, toolkit_parent_id) -> toolkit_id``: function to call for each inserted item
        * ``on_replace(toolkit_id, item)``: function to call for replaced item
            Replacement of item implies that children are "collapsed" again.
        * ``on_remove(toolkit_id)``: function to call for each removed item
        * ``on_load_children(toolkit_parent_id, sublist)``: function when children of a node are retrieved.
        * ``on_get_selection()``: return the items selected in the GUI
            Must return a List of (original) items.
        * ``on_sort()``: when list is reordered

        ``set_listener(None)`` to reset listener.
        '''
        self._meta.listener = listener
    
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
            if key not in self._meta.keys:
                raise KeyError('No column "%s" exists'%key)
        if _text is not None:
            kwargs[''] = _text
        self._meta.sources.update(kwargs)
        
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
        self._meta.children_source = children_source
        if not has_children_source:
            has_children_source = (lambda obj: True)
        self._meta.has_children_source = has_children_source
        self._childlists = [None] * len(self._nodes)

    def has_children(self, item):
        if not self._meta.children_source:
            return False
        source = self._meta.has_children_source
        return self._meta.retrieve(item, source)

    def load_children(self, idx):
        '''Retrieves the childlist of item at given idx.
        '''
        source = self._meta.children_source
        if not source:
            return
        item = self._nodes[idx]
        childlist = self._meta.retrieve(item, source)
        childlist = ObsList(childlist, toolkit_parent_id=self.toolkit_ids[idx])
        # Child SHARES _meta instance.
        childlist._meta = self._meta
        self._childlists[idx] = childlist
        on_load_children = self._meta.get_observer('load_children')
        on_load_children(childlist)

    def get_children(self, idx):
        '''Get childlist of item at given idx, loading it if not already loaded.'''
        if self._childlists[idx] is None:
            self.load_children(idx)
        return self._childlists[idx]

    def retrieve(self, item, column=''):
        source = self._meta.sources[column]
        return self._meta.retrieve(item, source)

    def sort(self, key=None, ascending:bool=None, restore=False):
        '''Sort the list.
        
        ``key`` can be a string, refering to the particular column of the 
        listview. Use Empty String to refer to the anonymous column.
        
        If ``key`` is a callable, the list is sorted in normal fashion.
        
        Instead of specifying ``key`` and ``ascending``, you can set
        ``restore=True`` to reuse the last applied sorting, if any.
        '''
        if restore and key is None:
            key = self._meta.sort_key
        if restore and ascending is None:
            ascending = self._meta.sort_ascending
        if isinstance(key, str):
            self._meta.sort_key = key
            self._meta.sort_ascending = ascending
            self.sorted = True
            keyfunc = lambda item: self.retrieve(item, key)
        else:
            # reset remembered sorting
            self._meta.sort_key = ''
            self._meta.sort_ascending = True
            self.sorted = False
            keyfunc = key
        sl = [ 
            (item, iid, childlist) 
            for item, iid, childlist in zip(
                self._nodes, self.toolkit_ids, self._childlists
            )
        ]
        sl.sort(key=lambda t: keyfunc(t[0]), reverse=not ascending)
        self._nodes = [t[0] for t in sl]
        self.toolkit_ids = [t[1] for t in sl]
        self._childlists = [t[2] for t in sl]
        self._meta.get_observer('sort')(self)
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
        on_replace = self._meta.get_observer('replace')
        on_replace(self.toolkit_ids[idx], item)
        
    def __delitem__(self, idx):
        del self._nodes[idx]
        self._childlists.pop(idx)
        tkid = self.toolkit_ids.pop(idx)
        on_remove = self._meta.get_observer('remove')
        on_remove(tkid)
        
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
        on_insert = self._meta.get_observer('insert')
        tkid = on_insert(idx, item, self.toolkit_parent_id)
        self.toolkit_ids.insert(idx, tkid)
        return idx, item

    def item_mutated(self, item):
        '''Call this when you mutated the item (which must be in this list)
        and want to update the GUI.
        '''
        idx = self._nodes.index(item)
        # do NOT collapse
        self.sorted = False
        on_replace = self._meta.get_observer('replace')
        on_replace(self.toolkit_ids[idx], item)

