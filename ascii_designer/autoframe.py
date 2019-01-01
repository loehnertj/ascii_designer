
from .ascii_slice import slice_grid, merged_cells
from .toolkit import get_toolkit


__all__ = [
    'AutoFrame',
    ]

def _convert_title(classname):
    # insert space before each capital letter
    title = ''.join(map(lambda x: x if x.islower() else " "+x, classname))
    title = title.strip()
    return title

class FrameMachinery:
    def __init__(self):
        self.toolkit = get_toolkit()
        self.controls = {}
            
    def add_widgets(self, parent, sliced_grid=None, body=None, offset_row=0, offset_col=0, autoframe=None):
        if not sliced_grid:
            sliced_grid = slice_grid(body)
        toolkit=self.toolkit
        
        # create controls
        for grid_element in merged_cells(sliced_grid):
            if not grid_element.text.strip():
                continue
            id, widget = toolkit.parse(parent, grid_element.text, externals=autoframe)
            self.controls[id] = widget
                
            # place on the grid
            e = grid_element
            toolkit.place(widget, row=e.row+offset_row, col=e.col+offset_col, rowspan=e.rowspan, colspan=e.colspan)
            text = e.text.replace('~',' ')
            toolkit.anchor(widget, left=not text.startswith(' '), right=not text.endswith(' '))
            # autowire
            try:
                attr = getattr(autoframe, id)
            except AttributeError:
                attr = None # not callable
            if callable(attr):
                toolkit.connect(widget, getattr(autoframe, id))
                
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
        self.__dict__['F'] = FrameMachinery()
        try:
            title = self.TITLE
        except AttributeError:
            title = _convert_title(self.__class__.__name__)
        self.F.title = title
        
    def show(self, buildfunc=None):
        '''Bring the frame on the screen.'''
        if not self.F.controls:
            root = self.F.controls[''] = self.F.toolkit.root(title=self.F.title)
            self.build(root, self.BODY)
        self.F.toolkit.show(root)
        
    def build(self, parent, body=None, autoframe=None):
        body = body or self.BODY
        sliced_grid = slice_grid(body)
        
        # init rows / columns
        for col, head in enumerate(sliced_grid.column_heads):
            self.F.toolkit.col_stretch(parent, col, head.count('-'))
        for row, cells in enumerate(sliced_grid.body_lines):
            # first cell
            head = cells[0:1]
            # first char of first cell
            if head: head = head[0][0:1]
            self.F.toolkit.row_stretch(parent, row, 1 if head=='I' else 0)
        self.F.add_widgets(parent, sliced_grid, autoframe=self)
        
    def __setattr__(self, name, val):
        if name in self:
            self.F.toolkit.setval(self[name], val)
        else:
            super().__setattr__(name, val)
    
    def __getattr__(self, name):
        if 'F' not in self.__dict__:
            raise RuntimeError('You forgot to call super().__init__!')
        if name in self.F.controls:
            # use toolkit to extract value from the widget
            return self.F.toolkit.getval(self[name])
        else:
            raise AttributeError('Attribute %s is not defined'%(name,))
    
    def __getitem__(self, key):
        return self.F.controls[key]
    
    def __contains__(self, key):
        return key in self.F.controls
    
    def close(self):
        self.F.toolkit.close(self[''])
    
    def quit(self):
        return self.close()
    
    def exit(self):
        return self.close()