import pytest
from ascii_designer.list_model import NodelistBase

def test_nodelist():
    n = NodelistBase([
            {'name':1, 'rank':2},
            {'name':3, 'rank':4}
        ], 
        keys='name rank'.split()
    )
    print(n._nodes)
    x = n.pop(0)
    print(n._nodes)
    print('popped:', x)
    x2 = {'name':5, 'rank':6}
    n += [x2]
    print(n._nodes)