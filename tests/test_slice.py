import pytest
from ascii_designer.ascii_slice import slice_grid, SlicedGrid, merged_cells, MCell

def slice(text):
    return list(merged_cells(slice_grid(text)))

def test_slice_simple():
    s = """
        |   |
         A   Bb
         C   D

    """
    grid = slice_grid(s)
    assert grid == SlicedGrid(
        column_heads=[
            "   ",
            ""
        ],
        body_lines=[
            [" A  ", " Bb"],
            [" C  ", " D "],
        ]
    )
    cells = list(merged_cells(grid))
    assert cells == [
        MCell(0, 0, "A  "),
        MCell(0, 1, "Bb"),
        MCell(1, 0, "C  "),
        MCell(1, 1, "D "),
    ]

def test_slice_merge_col():
    s = """
        | |
         A B
         C~D
    """
    cells = slice(s)
    assert cells == [
        MCell(0, 0, "A"),
        MCell(0, 1, "B"),
        MCell(1, 0, "C~D", colspan=2),
    ]

def test_slice_merge_row():
    s = """
        |
         {abc
         {def
          {ghi
          {jkl
         {mno
         {pqr
    """
    cells = slice(s)
    assert cells == [
        MCell(0,0, "abc \ndef ", rowspan=2),
        MCell(2,0, "ghi\njkl", rowspan=2),
        MCell(4,0, "mno \npqr ", rowspan=2),
    ]

def test_slice_overlapping_merge():
    """overlapping merge areas raise ValueError in merged_cells"""
    s = """
        |   |   |   
         abc {de fgh
         {jk {lm nop
         {rstuvw xyz
    """
    grid = slice_grid(s)
    with pytest.raises(ValueError):
        cells = list(merged_cells(grid))
