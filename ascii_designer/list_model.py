import logging
from collections.abc import MutableSequence

__all__ = [
    'ObsList',
    'ListMeta',
    ]

L = lambda: logging.getLogger(__name__)

class ListMeta():
    '''holds the metadata of a ObsList.'''
    def __init__(self, keys):
        self.keys = list(keys or [])
        self.sources = {k:k for k in self.keys}
        self.children_source = None
        self.has_children_source = None
        self.sort_key = ''
        self.sort_ascending = True
        
    def copy(self):
        nm = ListMeta(self.keys)
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
        
    
class ObsList(MutableSequence):
    '''
    Base class for treelist values.
    
    Behaves mostly like a list, except that:
     * it maintains a list of expected attributes (columns)
     * it provides notification when items are added or removed
     
    Attributes:
     * ``meta``: Container for keys, source functions and remembered sorting. 
     * ``sorted``: bool, whether list is currently sorted *by one of the list columns*.
       Sorting the list with a key function ("Python way") resets ``sorted`` to ``False``.
     * ``toolkit_ids``: can be indexed in the same way as the nodelist,
       and gives the toolkit-specific identifier of the list/treeview node.
     * ``on_insert(idx, item) -> toolkit_id``: function to call for each inserted item
     * ``on_replace(toolkit_id, item)``: function to call for replaced item
     * ``on_remove(toolkit_id)``: function to call for each removed item
     * ``on_get_selection()``: return the items selected in the GUI
     * ``on_sort()``: when list is reordered
    '''
    def __init__(self, iterable=None, keys=None, meta=None):
        if meta:
            self._meta = meta.copy()
        else:
            self._meta = ListMeta(keys)
        self.attached = True
        if iterable:
            self._nodes = [item for item in iterable]
        else:
            self._nodes = []
        self.toolkit_ids = [None] * len(self._nodes)
        self.sorted = False
        self.on_insert = None
        self.on_replace = None
        self.on_remove = None
        self.on_get_selection = None # type: Optional[Callable[[],List[Any]]]
        self.on_sort = None
        
    # FIXME: BROKEN
    def _children_of(self, node, iterable):
        '''Create a new nodelist instance representing child nodes of the given node.
        
        Override in subclass to create the fitting class instance, and insert 
        the children in the tree if you see fit.
        '''
        return ObsList(iterable, meta=self._meta)
            
    @property
    def selection(self):
        '''returns the sublist of all currently-selected items.
        
        Raises RuntimeError if the nodelist is detached.
        '''
        if not self.on_get_selection:
            raise RuntimeError('ObsList has no selection')
        return self.on_get_selection()
    
    
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
        
    def children(self, children_source, has_children_source=None):
        '''Sets the source for children of each list item, turning the list into a tree.
        
        ``children``, ``has_children`` follow the same semantics as other sources.
        
        Resolving ``children`` should return an iterable that will be turned 
        into a NodeList according to the rules.
        
        ``has_children`` should return a truthy value that is used to decide 
        whether to display the expander. If omitted, all nodes get the expander 
        initially if children_source is set.
        
        Children source only applies when the list of children is initially 
        retrieved. Once the children are retrieved, source changes do not affect 
        a Node anymore.
        
        ``has_children`` is usually evaluated immediately, because the treeview 
        needs to decide whether to display an expander icon.
        '''
        self._meta.children_source = children_source
        self._meta.has_children_source = has_children_source
        
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
        sl = [ (item, iid) for item, iid in zip(self._nodes, self.toolkit_ids)]
        sl.sort(key=lambda t: keyfunc(t[0]), reverse=not ascending)
        self._nodes = [t[0] for t in sl]
        self.toolkit_ids = [t[1] for t in sl]
        if self.on_sort:
            self.on_sort()
        
    def __getitem__(self, idx):
        return self._nodes[idx]
        
    def __len__(self):
        return len(self._nodes)
    
    def __setitem__(self, idx, item):
        self._nodes[idx] = item
        self.sorted = False
        if self.on_replace:
            self.on_replace(self.toolkit_ids[idx], item)
        
    def __delitem__(self, idx):
        del self._nodes[idx]
        if self.on_remove:
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
        self.sorted = False
        tkid = None
        if self.on_insert:
            tkid = self.on_insert(idx, item)
            print('got tkid' , tkid)
        self.toolkit_ids.insert(idx, tkid)
        return idx, item
