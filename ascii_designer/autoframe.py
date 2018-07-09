
from .ascii_slice import slice_grid, merged_cells
from .toolkit import get_toolkit


def _callable_members(obj):
    yield from (name for name in dir(obj) if callable(getattr(obj, name)) )

class AutoFrame:
    def frame_show(self):
        try:
            title = self.frame_title
        except AttributeError:
            title = self.__class__.__name__
        self.toolkit = get_toolkit(external_reference_provider=self, title=title)
        root = self.frame_build(toolkit=self.toolkit, body=self.frame_body)
        self.toolkit.show(root)
        
    def frame_build(self, toolkit, body):
        self.frame_controls = {}
        callables = set(_callable_members(self))
        root = self.frame_controls[''] = toolkit.root
        sliced_grid = slice_grid(body)
        
        # init rows / columns
        for col, head in enumerate(sliced_grid.column_heads):
            toolkit.col_stretch(col, head.count('-'))
        for row, cells in enumerate(sliced_grid.body_lines):
            # first cell
            head = cells[0:1]
            # first char of first cell
            if head: head= head[0][0:1]
            toolkit.row_stretch(row, 1 if head=='I' else 0)
        # create controls
        for grid_element in merged_cells(sliced_grid):
            if not grid_element.text.strip():
                continue
            id, widget = toolkit.parse(grid_element.text)
            self.frame_controls[id] = widget
                
            # place on the grid
            e = grid_element
            toolkit.place(widget, row=e.row, col=e.col, rowspan=e.rowspan, colspan=e.colspan)
            toolkit.anchor(widget, left=not e.text.startswith(' '), right=not e.text.endswith(' '))
            # autowire
            if id in callables:
                toolkit.connect(widget, getattr(self, id))
                print('connected handler for %s'%id)
        return root
    
    def __getitem__(self, key):
        return self.frame_controls[key]
    
    def close(self):
        self.toolkit.close(self[''])
    
    def quit(self):
        return self.close()
    
    def exit(self):
        return self.close()