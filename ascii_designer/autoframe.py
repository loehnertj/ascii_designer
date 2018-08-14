
from .ascii_slice import slice_grid, merged_cells
from .toolkit import get_toolkit


__all__ = [
    'AutoFrame',
    'BoundValue',
    ]

def _callable_members(obj):
    yield from (name for name in dir(obj) if callable(getattr(obj, name)) )
    
class BoundValue:
    pass

class AutoFrame:
    '''
    class name is converted to title.
    Override with frame_title
    body definition with frame_body
    
    to create external widgets or customize the autocreated ones, override frame_build
    
    get at the created controls using .frame_controls[key] or AutoFrame[key].
    
    close(), exit(), quit() provided for convenience
    
    functions with same name as a control are autobound to the default handler (click or changed)
    
    attributes set to BoundValue are autobound to the control value (get/set).
    '''
        
    def frame_show(self):
        '''Bring the frame on the screen.'''
        try:
            title = self.frame_title
        except AttributeError:
            title = self.__class__.__name__
            # insert space before each capital letter
            title = ''.join(map(lambda x: x if x.islower() else " "+x, title))
            title = title.strip()
        self.toolkit = get_toolkit(external_reference_provider=self, title=title)
        self._bound_names = {}
        self.frame_build(body=self.frame_body)
        self.toolkit.show(self.toolkit.root)
        
    def frame_build(self, body):
        self.frame_controls = {}
        self.frame_controls[''] = self.toolkit.root
        sliced_grid = slice_grid(body)
        
        # init rows / columns
        for col, head in enumerate(sliced_grid.column_heads):
            self.toolkit.col_stretch(col, head.count('-'))
        for row, cells in enumerate(sliced_grid.body_lines):
            # first cell
            head = cells[0:1]
            # first char of first cell
            if head: head= head[0][0:1]
            self.toolkit.row_stretch(row, 1 if head=='I' else 0)
        self.frame_add_widgets(sliced_grid)
            
    def frame_add_widgets(self, sliced_grid=None, body=None, offset_row=0, offset_col=0):
        if not sliced_grid:
            sliced_grid = slice_grid(body)
        callables = set(_callable_members(self))
        toolkit=self.toolkit
        
        # create controls
        for grid_element in merged_cells(sliced_grid):
            if not grid_element.text.strip():
                continue
            id, widget = toolkit.parse(grid_element.text)
            self.frame_controls[id] = widget
                
            # place on the grid
            e = grid_element
            toolkit.place(widget, row=e.row+offset_row, col=e.col+offset_col, rowspan=e.rowspan, colspan=e.colspan)
            toolkit.anchor(widget, left=not e.text.startswith(' '), right=not e.text.endswith(' '))
            # autowire
            # FIXME: bindings can never removed
            if getattr(self, id, BoundValue) is BoundValue:
                print('bind attribute "%s"'%id)
                self._bound_names[id] = widget
                try:
                    delattr(self, id)
                except AttributeError:
                    pass
            elif id in callables:
                toolkit.connect(widget, getattr(self, id))
                print('connected handler for %s'%id)
                
    def __setattr__(self, name, val):
        bn = getattr(self, '_bound_names', {})
        if name in bn:
            self.toolkit.setval(bn[name], val)
        else:
            super().__setattr__(name, val)
    
    def __getattr__(self, name):
        if name == '_bound_names': return super().__getattr__(name)
        bn = getattr(self, '_bound_names', {})
        if name in bn:
            ctl = bn[name]
            return self.toolkit.getval(ctl)
        else:
            return super().__getattr__(name)
    
    def __getitem__(self, key):
        return self.frame_controls[key]
    
    def close(self):
        self.toolkit.close(self[''])
    
    def quit(self):
        return self.close()
    
    def exit(self):
        return self.close()