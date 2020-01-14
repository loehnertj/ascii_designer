import pytest
from ascii_designer.toolkit import ToolkitBase
from unittest.mock import Mock

def _returns_method_args_kwargs(methodname):
    def fn(*args, **kwargs):
        return methodname, args, kwargs
    return fn


@pytest.fixture
def toolkit():
    t = ToolkitBase()
    for name in (
        'row_stretch col_stretch anchor place connect setval show close'
    ).split():
        setattr(t, name, Mock())
    for name in (
        'root getval box label button textbox multiline treelist dropdown'
        ' combo option checkbox slider menu_root menu_sub menu_command'
    ).split():
        setattr(t, name, _returns_method_args_kwargs(name))
    return t

class Parent:
    '''Parent singleton object'''

@pytest.mark.parametrize('wdef,expect_result', [
    # '' key is the widget type (called function)
    ('[Test]', {'': 'button', 'id': 'test', 'text': 'Test'}),
]
)
def test_parse_button(toolkit, wdef, expect_result):
    id, (wtype, args, params) = toolkit.parse(Parent, wdef)
    assert args == (Parent,)
    params[''] = wtype
    assert params == expect_result
