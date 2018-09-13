#import tkinter as tk
import sys
from ascii_designer import AutoFrame, set_toolkit

TK = 'tk'
if sys.argv[1:]:
    TK = sys.argv[1]
set_toolkit(TK)

menu = '''
    File
        Open
        Save
        Save As...
        Quit, C-Q
    Help
        About...
'''

toolbar = '''
 [ Open ]
 [ Save ]
 [ Save as... ]
'''

panel1 = '''
|                       | <---------------------------->
 [ Button 1 ]            [ Textbox_ ]
 [ Button 2 ]            [ Dropdown (val1, val2, val3) v]

 Static text:            [ _ ]
 Label as ID:            [ v ]
I *external_object -----------------------------------
 
 [            Button with column span                  ]
                        |
I{ [ Multiline Text __ ]
I{
 
 {      *rowcolspan_object
 {
 
 [ Save As ... ]
 [ okbtn: OK ]
 [ slider: 0 -+- 100 ]  |
 
 [ ] Checkbox 1            [ ] cb2 : Checkbox 2
 ( ) Option 1
 (x) Option 2
 ( ) Option 3
 .O grim fate!


=+- boxcaption -|-------------+
 | [ Button 3]    [ Button 4 ] 
 +----------------------------+
'''

demo_all = '''
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
 External:       *external_object
 [ Align Demo ]  [ Bound ctl demo ]
 [ Quit ]
'''

# Row/Column stretch is controlled by "-" in the column head and "I" in row head
# Widget anchoring is controlled by presence of leading/trailing whitespace 
# within the cell.
demo_alignments = '''
|              |     <->          |   <-->         |
 [ fixed col  ] [  stretch 1x    ] [stretch 2x    ]
                [ colspan stretch 3x              ]
I               [ stretch h+v __ ]|[left]          |
I               {[left, v 2x __ ] |  [center]      |
I               {                           [right]|
'''

class Main(AutoFrame):
    menubar=menu
    toolbar=toolbar
    frame_body = demo_all
    
    def frame_build(self, body):
        # initialize something
        self.external_object = self.toolkit.label(self.toolkit.root, text="<External label>")
        super().frame_build(body)
    
    def press_me(self):
        print('press_me was pressed')
        row_3 = '''
                  |
        Text box:  [ Write here_ ]
        '''
        self.frame_add_widgets(body=row_3, offset_row=2)
        
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
        
    def align_demo(self):
        f = AlignmentDemo()
        f.frame_show()
        
    def bound_ctl_demo(self):
        f = BoundCtlDemo()
        f.frame_show()
        
class AlignmentDemo(AutoFrame):
    frame_body = demo_alignments
        
    def frame_build(self, body):
        super().frame_build(body)
        if TK=='qt':
            from PyQt4.QtGui import QSizePolicy
            # Qt: -> Rowspan seems to not play well with RowStretch. The buttons must be
            # set to Expanding to make the RowStretch work.
            self['center'].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self['right'].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
class BoundCtlDemo(AutoFrame):
    frame_body = '''
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
    
class EmptyFrame(AutoFrame):
    frame_body = ''
    
    
if __name__ == '__main__':
    frm = Main()
    frm.frame_show()