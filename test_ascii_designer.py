'''This is part example collection, part regression test.
'''

#import tkinter as tk
import sys
from ascii_designer import AutoFrame, set_toolkit

TK = 'tk'
if sys.argv[1:]:
    TK = sys.argv[1]
set_toolkit(TK)

# Idea for later
menu = '''
    File
        Open
        Save
        Save As...
        Quit, C-Q
    Help
        About...
'''

# Idea for later
toolbar = '''
 [ Open ]
 [ Save ]
 [ Save as... ]
'''


class Main(AutoFrame):
    f_title = 'Ascii Designer Demo Menu'
    f_body = '''
    |    <->                     |
     - ASCII Designer Demo Menu -
     [Autoconnect               ]
     [Boxes and embedding       ]
     [Bound values              ]
     [Tree view                 ]
     [Alignment                 ]
    I
       [Close]                   |
    '''
    def autoconnect(self):
        AutoconnectDemo().f_show()
        
    def boxes_and_embedding(self):
        BoxesDemo().f_show()
        
    def bound_values(self):
        BoundCtlDemo().f_show()
        
    def tree_view(self):
        TreeDemo().f_show()
        
    def alignment(self):
        AlignmentDemo().f_show()
        

class AutoconnectDemo(AutoFrame):
    f_body = '''
                       |      <->                                        ~
        Label:          This is a label
        Button:         [ Press me ]
        
        Multiline:      [ foo__ ]
        Dropdown:       [ Choose (Red,Green,Blue) v]
        Dropdown empty: [ v ]
        Combo:          [ Color_ (Red,Green,Blue) v]
        Option:         ( ) Option A
                        (x) Option B
        Checkbox:       [x] agree:I agree to the terms and conditions.
        Slider:         [ slider: 0 -+- 100 ]
        '''
        
    def close(self):
        print('Closing now.')
        super().close()
    
    def press_me(self):
        print('press_me was pressed')
        row_3 = '''
                  |
        Text box:  [ Write here_ ]
        '''
        self.f_add_widgets(self[''], body=row_3, offset_row=2)
        
    def write_here(self, text):
        print('write_here: "%s"'%text)
    def foo(self, text):
        print('foo: "%s"'%text)
    def choose(self, val):
        print('choose: "%s"'%val)
        
    def dropdown_empty(self, val):
        print('dropdown_empty: %r'%(val,))
    def color(self, val):
        print('color: "%s"'%val)
        print('foo: "%s"'%self.foo)
    def option_a(self, checked=True):
        print('option_a %s'%checked)
    def option_b(self, checked=True):
        print('option_b %s'%checked)
    def agree(self, checked):
        print('agree: %s'%checked)
    def slider(self, val):
        print('slider: %s'%val)
        
        
class BoxesDemo(AutoFrame):
    f_body = '''
        |               |  <->
         Use the source code to understand what is demonstrated here.
         Box:            <box>
        IGroup box:      <groupbox: Test >
        INesting:        <nest_box:Turtles all the way down>
        
    '''
    
    def __init__(self, level=2):
        super().__init__()
        self._level = level
        
    
    def f_build(self, parent, body):
        super().f_build(parent, body)
        # Replace placeholder with a label
        if TK == 'tk':
            bm = self.box.master
            gbm = self.groupbox.master
        elif TK == 'qt':
            bm = self.box.parent()
            gbm = self.groupbox.parent()
        self.box = self.f_toolkit.button(parent=bm, text="this replaces box")
        self.groupbox = self.f_toolkit.button(parent=gbm, text='this fills groupbox')
        
        # Nesting
        if self._level:
            inner = BoxesDemo(self._level-1)
            inner.f_build(parent=self.nest_box, body=inner.f_body)
        
class AlignmentDemo(AutoFrame):
    '''Row/Column stretch is controlled by "-" in the column head and "I" in row head
    Widget anchoring is controlled by presence of leading/trailing whitespace 
    within the cell.
    '''
    f_body = '''
    |              |     <->          |   <-->         |
    [ fixed col  ] [  stretch 1x    ] [stretch 2x    ]
                    [ colspan stretch 3x              ]
    I               [ stretch h+v __ ]|[left]          |
    I               {[left, v 2x __ ] |  [center]      |
    I               {                           [right]|
    '''
        
    def f_build(self, parent, body):
        super().f_build(parent, body)
        if TK=='qt':
            from PyQt4.QtGui import QSizePolicy
            # Qt: -> Rowspan seems to not play well with RowStretch. The buttons must be
            # set to Expanding to make the RowStretch work.
            self['center'].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self['right'].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
class BoundCtlDemo(AutoFrame):
    f_body = '''
    |               |  <->                                            ~
     Textbox:        [ _ ]
     Multiline:      [ __ ]
     Dropdown:       [ Choose (Red,Green,Blue) v]
     Combo:          [ Color_ (Red,Green,Blue) v]
     Option:         ( ) Option A
                     (x) Option B
     Checkbox:       [x] agree:I agree to the terms and conditions.
     Slider:         [ slider: 0 -+- 100 ]
    I
     [Get all]       [Set all]
    '''
    
    bind_names = 'textbox multiline choose color option_a option_b agree slider'.split(' ')
    
    def set_all(self):
        self.textbox = 'text'
        self.multiline = 'more\ntext'
        self.choose = 'Green'
        self.color = 'Shade of grey'
        self.option_b = True # FIXME for tk toolkit, must set 'option_b'
        self.agree = False
        self.slider = 50
        
    def get_all(self):
        for name in self.bind_names:
            print('%s: %s'%(name, getattr(self, name)))
            
from collections import namedtuple
RankRow = namedtuple('RankRow', 'name points rank')
            
class TreeDemo(AutoFrame):
    f_body = '''
    |             |              <->                |
    |Simple List   List with named columns~
    I[= Shopping ] [= Players (,Name, Points, Rank)]
    '''
    def f_build(self, parent, body):
        super().f_build(parent, body)
        print(list(self.f_controls.keys()))
        self.shopping = ['Cabbage', 'Spam', 'Salmon Mousse']
        self.players = [
            RankRow('CaptainJack', 9010, 1),
            RankRow('MasterOfDisaster', 3010, 2),
            RankRow('LittleDuck', 12, 3),
        ]
        self.players[1]['name'] = 'Changed Name'
        self.players[2] = RankRow('BigDuck', 44, 3)
        self.players.sources(name=['name'], points=['points'], rank=['rank'], **{'': lambda obj:'ItsLikeMagic'})
        self.players.append({'name': 'Last', 'points': -1, 'rank': 4})
        
    def shopping(self, item):
        print('Buy: ', item)
        
    
class EmptyFrame(AutoFrame):
    f_body = ''
    
    
if __name__ == '__main__':
    frm = Main()
    frm.f_show()