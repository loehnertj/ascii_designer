
from .ascii_slice import slice_grid, merged_cells
from .toolkit import get_toolkit


__all__ = [
    'AutoFrame',
    ]

class AutoFrame:
    '''
    class name is converted to title.
    Override with frame_title
    body definition with frame_body
    
    to create external widgets or customize the autocreated ones, override frame_build
    
    get at the created controls using AutoFrame[key].
    
    close(), exit(), quit() provided for convenience
    
    functions with same name as a control are autobound to the default handler (click or changed)
    
    attributes are autobound to the control value (get/set), except if they are explicitly overwritten.
    '''
    def __init__(self):
        # make getattr + setattr work first
        self.__dict__['_frame_controls'] = {}
        self._toolkit = None
        
    @property
    def toolkit(self):
        '''instantiates the toolkit on first use.'''
        if self._toolkit:
            return self._toolkit
        try:
            title = self.frame_title
        except AttributeError:
            title = self.__class__.__name__
            # insert space before each capital letter
            title = ''.join(map(lambda x: x if x.islower() else " "+x, title))
            title = title.strip()
        self._toolkit = get_toolkit(external_reference_provider=self, title=title)
        return self._toolkit
        
    def frame_show(self):
        '''Bring the frame on the screen.'''
        if not self._frame_controls:
            self.frame_build(body=self.frame_body)
        self.toolkit.show(self.toolkit.root)
        
    def frame_build(self, body):
        self._frame_controls[''] = self.toolkit.root
        sliced_grid = slice_grid(body)
        
        # init rows / columns
        for col, head in enumerate(sliced_grid.column_heads):
            self.toolkit.col_stretch(col, head.count('-'))
        for row, cells in enumerate(sliced_grid.body_lines):
            # first cell
            head = cells[0:1]
            # first char of first cell
            if head: head = head[0][0:1]
            self.toolkit.row_stretch(row, 1 if head=='I' else 0)
        self.frame_add_widgets(sliced_grid)
            
    def frame_add_widgets(self, sliced_grid=None, body=None, offset_row=0, offset_col=0):
        if not sliced_grid:
            sliced_grid = slice_grid(body)
        toolkit=self.toolkit
        
        # create controls
        for grid_element in merged_cells(sliced_grid):
            if not grid_element.text.strip():
                continue
            id, widget = toolkit.parse(grid_element.text)
            self._frame_controls[id] = widget
                
            # place on the grid
            e = grid_element
            toolkit.place(widget, row=e.row+offset_row, col=e.col+offset_col, rowspan=e.rowspan, colspan=e.colspan)
            toolkit.anchor(widget, left=not e.text.startswith(' '), right=not e.text.endswith(' '))
            # autowire
            try:
                attr = getattr(self, id)
            except AttributeError:
                attr = None # not callable
            if callable(attr):
                toolkit.connect(widget, getattr(self, id))
                print('connected handler for %s'%id)
                
    def __setattr__(self, name, val):
        if name in self:
            self.toolkit.setval(self[name], val)
        else:
            super().__setattr__(name, val)
    
    def __getattr__(self, name):
        if '_frame_controls' not in self.__dict__:
            raise RuntimeError('You forgot to call super().__init__!')
        if name in self:
            # use toolkit to extract value from the widget
            return self.toolkit.getval(self[name])
        else:
            raise AttributeError('Attribute %s is not defined'%(name,))
    
    def __getitem__(self, key):
        return self._frame_controls[key]
    
    def __contains__(self, key):
        return key in self._frame_controls
    
    def close(self):
        self.toolkit.close(self[''])
    
    def quit(self):
        return self.close()
    
    def exit(self):
        return self.close()