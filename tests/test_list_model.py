import pytest
from unittest.mock import Mock, call
from ascii_designer.list_model import ObsList

def test_obslist_callbacks():
    m = Mock()
    n = ObsList([
            {'name':1, 'rank':2},
            {'name':3, 'rank':4}
        ], 
        keys='name rank'.split()
    )
    n.on_insert = m.on_insert
    n.on_replace = m.on_replace
    n.on_remove = m.on_remove
    x = n.pop(0)
    m.on_remove.assert_called_with(0)
    assert list(n) == [{'name':3, 'rank':4}]
    
    x2 = {'name':5, 'rank':6}
    n += [x2]
    m.on_insert.assert_called_with(1, x2)
    n[0] = x2
    m.on_replace.assert_called_with(0, x2)
    