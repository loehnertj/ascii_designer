'''
Functions to slice up a fixed-column-width ASCII grid.

:any:`slice_grids` splits up lines according to a header row with ``|`` separators.

:any:`merged_cells` iterates over this grid and returns merge areas.

Columns are merged if there is something different from ``|`` or space below 
the separator in the header row.

Rows are merged by prefixing the cells with ``{``. The symbols must be in the 
same text column.
'''
import dataclasses as dc
import textwrap

__all__ = [
    'slice_grids',
    'SlicedGrid',
    'merged_cells',
    'MCell',
    ] 

# for testing
_overlapping_merge = '''
    |   |   |   
     abc {de fgh
     {jk {lm nop
     {rstuvw xyz
    '''
_adj_row_merge = '''
    |    |   
     {abc
     {def
      {ghi
      {jkl
     {mno
     {pqr
     '''
     
@dc.dataclass
class SlicedGrid:
    # text between (not including) | | splitters
    column_heads:list[str] = dc.field(default_factory=list)
    # "dumbly" splitted grid cells:
    # list of lists, row - column - string
    # each string being the cell text including the PRECEDING separator's column
    body_lines:list[list[str]] = dc.field(default_factory=list)
    subgrids:dict[str,"SlicedGrid"] = dc.field(default_factory=dict)


def slice_grids(grid_text) -> SlicedGrid:
    '''slice grids up by the first (nonempty) row.
    
    Before slicing, empty lines before/after are removed,
    and the text is dedented.
    
    The first row is split by | characters.
    The first column can contain a | character or not.

    A grid can be followed by subgrids. Start of a subgrid is indicated by the
    text ``:subgridid:`` on a separate line, where ``subgridid`` can be any
    text. The first ``:`` MUST be on the same indentation level as the first
    ``|`` (which is required).
    
    Returns a SlicedGrid with Properties:
        * column_heads: the split up parts of the first line (not including the separators).
        * body_lines: list of following lines; each item is a list of strings, 
          where each string is the grid "cell" including the preceding separator column.
          I.e. if you join the cell list without separator, you regain the text line.
        * subgrid: Dictionary of subgrids, keyed by subgridid.
    '''
    grid_text = textwrap.dedent(grid_text)
    lines = grid_text.splitlines()
    grid, lines = _slice_grid(lines)
    while lines:
        idline = lines.pop(0).strip()
        if not (idline.startswith(":") and idline.endswith(":")):
            raise ValueError(f"Subgrid id is invalid: '{idline}'")
        subgrid_id = idline[1:-1]
        grid.subgrids[subgrid_id], lines = _slice_grid(lines)
    return grid

def _slice_grid(lines) -> tuple[SlicedGrid,list[str]]:
    '''slice a grid up by the first (nonempty) row.
    
    Before slicing, empty lines before/after are removed,
    and the text is dedented.
    
    The first row is split by | characters.
    The first column can contain a | character or not.
    
    Returns a SlicedGrid with Properties:
        * column_heads: the split up parts of the first line (not including the separators).
        * body_lines: list of following lines; each item is a list of strings, 
          where each string is the grid "cell" including the preceding separator column.
          I.e. if you join the cell list without separator, you regain the text line.

    ``remainder`` are the lines following the grid.
    '''
    for n, line in enumerate(lines):
        if line.startswith(":") and line.endswith(":"):
            remain = lines[n:]
            lines = lines[:n]
            break
    else:
        remain = []
    # remove leading and trailing whitespace lines
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return SlicedGrid(), remain
    column_heads = lines.pop(0).split('|')
    if not column_heads[0]:
        # first | is there
        column_heads.pop(0)
    else:
        # no first |, add padding to first column
        lines = [' '+line for line in lines]
        
    widths = [len(part)+1 for part in column_heads]
    # if any line is longer than the header, adjust width of last column.
    maxlen = max((len(line) for line in lines), default=0)
    widths[-1] = max(widths[-1], maxlen-sum(widths[:-1]))

    body_lines = []
    for line in lines:
        body_line = []
        for w in widths[:]:
            cell, line = line[:w], line[w:]
            if len(cell) < w:
                cell = cell + ' '*(w-len(cell))
            body_line.append(cell)
        body_lines.append(body_line)
    return SlicedGrid(column_heads=column_heads, body_lines=body_lines), remain

@dc.dataclass
class MCell:
    row:int = 0
    """Cell's row, counting from 0"""
    col:int = 0
    """Cell's column, counting from 0"""
    text:str = ""
    """Merged-area text"""
    rowspan:int = 1
    """Spanned rows, at least 1"""
    colspan:int = 1
    """Spanned columns, at least 1"""


def merged_cells(sliced_grid):
    '''Generator: takes the sliced grid, and returns merged cells one by one.
    
    Cells are merged by the following logic:
     
      * If the first character of a (stripped) cell is '{', cells of the following 
        row(s) are merged while they also start with '{' in the same column.
      * Then, columns are merged if the following (column's) cell starts neither 
        with space nor with '|'.
    
    Yields MCell instances with:
    
      * row, col: cell position (int, 0-based)
      * rowspan, colspan: spanned rows/cols, at least 1
      * text: merged area text, as sliced out from the text editor; not 
        including the leading '{'; "ragged" linebreaks retained.
            
    Iteration order is row-wise.
    
    Merge areas must not overlap. (However this should rarely happen on accident).
    
    Note: If you need two row-merge ranges above each other, indent the 
    '{' differently.
    '''
    # make a deep copy first
    body_lines = [ cells[:] for cells in sliced_grid.body_lines ]
    for row, line in enumerate(body_lines):
        for col, cell in enumerate(line):
            rowspan = 1
            colspan = 1
            if cell is None:
                # part of previously merged cell
                continue
            cell = cell[1:]
            # calculate Row span
            ofs = 0
            if cell.lstrip().startswith('{'):
                ofs = cell.index('{')+1
            if ofs:
                while True:
                    try:
                        cell_below = body_lines[row+rowspan][col][1:]
                    except IndexError:
                        break
                    # no aligned { or not empty before
                    if cell_below[ofs-1:ofs] != '{' or cell_below[:ofs-1].strip():
                        break
                    rowspan += 1
                # now we talked about it, delete prefix
                for row2 in range(row, row+rowspan):
                    body_lines[row2][col] = body_lines[row2][col][ofs:]
                cell = cell[ofs:]
            # calculate column_span
            colspans = [] # collect for merged rows
            for row2 in range(row, row+rowspan):
                colspan = 1
                while True:
                    try:
                        cell_right = body_lines[row2][col+colspan]
                    except IndexError:
                        break
                    # "not cell" also covers the "already-merged" case.
                    if (not cell_right) or cell_right.startswith(' ') or cell_right.startswith('|'):
                        break
                    colspan += 1
                colspans.append(colspan)
            colspan = max(colspans)
            # All clear. Collect text.
            try:
                mrows = [
                    ''.join(body_lines[row2][col:col+colspan])[1:]
                    for row2 in range(row, row+rowspan)
                ]
            except TypeError as e:
                # caught a None entry
                raise ValueError('Overlapping merge areas') from e
            text = '\n'.join(mrows)
            yield MCell(row=row, col=col, text=text, rowspan=rowspan, colspan=colspan)
            # white-out merge area
            for row2 in range(row, row+rowspan):
                for col2 in range(col, col+colspan):
                    try:
                        body_lines[row2][col2] = None
                    except IndexError:
                        pass
