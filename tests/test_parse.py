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
    # XXX: empty string is filtered out by autoframe (no widget)
    # however if it somehow ends up in parse() it should
    # yield a label.
    ('', {'': 'label', 'id': 'label_', 'text': ''}),
    ('~', {'': 'label', 'id': 'label_', 'text': ''}),
    ('.', {'': 'label', 'id': 'label_', 'text': ''}),
    ('..', {'': 'label', 'id': 'label_', 'text': '.'}),
    ('...', {'': 'label', 'id': 'label_', 'text': '..'}),
    ('lbl:', {'':'label', 'id': 'lbl', 'text': ''}),
    # text stripped
    ('lbl: abc ', {'':'label', 'id': 'lbl', 'text': 'abc'}),
    # identifier must precede :, otherwise part of text
    (': abc ', {'':'label', 'id': 'label__abc', 'text': ': abc'}),
    (' abc ', {'':'label', 'id': 'label_abc', 'text': 'abc'}),
    # dot after : is literal
    ('lbl:. abc ', {'':'label', 'id': 'lbl', 'text': '. abc'}),
    # dot before makes it all label text
    ('.lbl: abc ', {'':'label', 'id': 'label_lbl_abc', 'text': 'lbl: abc'}),
    ('<Test>', {'': 'box', 'id': 'test', 'text': 'Test', 'given_id': None}),
    ('<test:Test>', {'': 'box', 'id': 'test', 'text': 'Test', 'given_id': 'test'}),
    ('( ) Test', {'': 'option', 'id': 'test', 'text': 'Test', 'checked': ' '}),
    ('(x) Test', {'': 'option', 'id': 'test', 'text': 'Test', 'checked': 'x'}),
    ('[ ] Test', {'': 'checkbox', 'id': 'test', 'text': 'Test', 'checked': ' '}),
    ('[x] Test', {'': 'checkbox', 'id': 'test', 'text': 'Test', 'checked': 'x'}),
    ('[sl: 1 -+- 22]', {'': 'slider', 'id': 'sl', 'min': '1', 'max': '22'}),
    ('[Test__]', {'': 'multiline', 'id': 'test', 'text': 'Test'}),
    ('[Test_]', {'': 'textbox', 'id': 'test', 'text': 'Test'}),
    ('[Test_ v]', {'': 'combo', 'id': 'test', 'text': 'Test', 'values': None}),
    ('[Test v]', {'': 'dropdown', 'id': 'test', 'text': 'Test', 'values':None}),
    ('[Test (a, b, c) v]', {'': 'dropdown', 'id': 'test', 'text': 'Test', 'values':'a, b, c'}),
    ('[= Test]', {'': 'treelist', 'id': 'test', 'text': 'Test', 'columns':None}),
    ('[= Test (a, b, c)]', {'': 'treelist', 'id': 'test', 'text': 'Test', 'columns':'a, b, c'}),
    ('[= test: (a, b, c)]', {'': 'treelist', 'id': 'test', 'text': '', 'columns':'a, b, c'}),
    ('[Test]', {'': 'button', 'id': 'test', 'text': 'Test'}),
]
)
def test_parse(toolkit, wdef, expect_result):
    id, (wtype, args, params) = toolkit.parse(Parent, wdef)
    assert args == (Parent,)
    params[''] = wtype
    # cut off auto id (unpredictable)
    if 'x' in params['id']:
        params['id'] = params['id'].rsplit('x', 1)[0]
    assert params == expect_result
