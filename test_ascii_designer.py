'''This is part example collection, part regression test.
'''

#import tkinter as tk
import logging
import sys
import random
import time
from ascii_designer import AutoFrame, set_toolkit



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
     [List view                 ]
     [Tree view                 ]
     [Alignment                 ]
     [Window Menu               ]
    I
       [Close]                   |
    '''
    def autoconnect(self):
        AutoconnectDemo().f_show()
        
    def boxes_and_embedding(self):
        BoxesDemo().f_show()
        
    def bound_values(self):
        BoundCtlDemo().f_show()
        
    def list_view(self):
        ListDemo().f_show()
        
    def tree_view(self):
        TreeDemo().f_show()
        
    def alignment(self):
        AlignmentDemo().f_show()

    def window_menu(self):
        MenuDemo().f_show()
        

class AutoconnectDemo(AutoFrame):
    f_body = '''
                       |      <->
        Label:          This is a label
        Button:         [ Press me ]
        
        Multiline:      [ foo__ ]
        Dropdown:       [ Choose (Red,Green,Blue) v]
        Dropdown empty: [ v ]
        Combo:          [ Color_ (Red,Green,Blue) v]
        Option:         ( ) Option A
                        (x) Option B
                        - checkbox below should be centered,
                        - longest line in the layout:
        Checkbox:       [x] agree:I agree to the terms and conditions.
        Slider:         [ slider: 0 -+- 100 ]
                        this appears twice
                        this appears twice
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
        
    def on_write_here(self, text):
        print('write_here: "%s" / "%s"'%(text, self.write_here))
    def foo(self, text):
        print('foo: "%s"'%text)
    def on_choose(self, val):
        '''use on_<attr> if you want to be able to retrieve the auto-value as 
well.
        '''
        print('choose: "%s" / "%s"'%(val, self.choose))
        
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
        
    
    def f_on_build(self):
        # Replace placeholder with a label
        if TK in ('tk', 'ttk'):
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
     [fixed col   ] [  stretch 1x    ] [stretch 2x    ]
                    [ colspan stretch 3x              ]
    I               [ stretch h+v __ ]|[left]          |
    I               {[left, v 2x __ ] |  [center]      |
    I               {                           [right]|
    '''
        
    def f_on_build(self):
        if TK=='qt':
            from qtpy.QtWidgets import QSizePolicy
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
            
class RankRow:
    def __init__(self, name, points, rank):
        self.name = name
        self.points = points
        self.rank = rank
        
    def __str__(self):
        return 'RR'
            
class ListDemo(AutoFrame):
    f_body = '''
    |             |     |         |        |<->          |
    |Simple List   List with named columns~~        
    I[= Shopping ] [= Players  (Name, Points, Rank)     ]
                   [Add] [Replace] [Mutate] [Remove] ~                 
    '''
    def f_on_build(self):
        print(list(self.f_controls.keys()))
        self.shopping = ['Cabbage', 'Spam', 'Salmon Mousse']
        self._populate_players()
        
    def _populate_players(self):
        self.players = [
            RankRow('CaptainJack', 9010, 1),
            RankRow('MasterOfDisaster', 3010, 2),
            RankRow('LittleDuck', 12, 3),
        ]
        self.players[1].name = 'Changed Name'
        # Notify listview about mutated item
        self.players.item_mutated(self.players[1])
        self.players[2] = RankRow('BigDuck', 44, 3)
        self.players.sources(lambda obj:'ItsLikeMagic', name=['name'], points=['points'], rank=['rank'])
        # not recommended: mixed item types
        self.players.append({'name': 'Last', 'points': -1, 'rank': 4})
        self.players.sources(name='name', points='points', rank='rank')
        
    def add(self):
        p = RankRow(
            'new%d'%(random.randint(1,1000)),
            points=random.randint(1,999),
            rank=9
        )
        idx = random.randint(0, len(self.players))
        self.players.insert(idx, p)
        # sorting needs to be restored explicitly
        self.players.sort(restore=True)
        # Also possible; however causes reload of the whole list (since replaced by new list)
        #self.players += [p]

    def replace(self):
        for item in self.players.selection:
            idx = self.players.index(item)
            p = RankRow(
                'replaced-%d'%(random.randint(1,1000)),
                points=random.randint(1,999),
                rank=9
            )
            self.players[idx] = p

    def mutate(self):
        for item in self.players.selection:
            item.name = 'changed%d' % random.randint(1, 1000)
            self.players.item_mutated(item)
    
    def remove(self):
        nodes = self.players.selection[:]
        for node in nodes:
            self.players.remove(node)

    def shopping(self, item):
        print('Buy: ', item)
    

class TreeDemo(AutoFrame):
    f_body = '''
    |  <-> Tree        |
     Tree~
    I[= Files         ]
     [ Test Find ]
    '''
    def f_on_show(self):
        self._populate_folder()
        
    def _populate_folder(self):
        import pathlib
        def children_of(fld):
            print('Now retrieving children of %s, wait 1second'%(fld,))
            time.sleep(1.0)
            for item in fld.iterdir():
                if not item.name.startswith('.'):
                    yield item
        def has_children(fld):
            #print('Has children?: %s'%(fld,))
            if not fld.is_dir():
                return False
            try:
                next(fld.iterdir())
            except StopIteration:
                return False
            return True
        # set the attribute or method which retrieves the iterable of children
        self.files.children_source(children_of, has_children_source=has_children)
        # use a generator to set folder
        self.files = children_of(pathlib.Path.home())
        
    def on_files(self, item):
        print('focus', item)
        print('selection', self.files.selection)

    def test_find(self):
        item = self.files.selection[0]
        print('Find', item)
        print('REsult:', self.files.find(item))
        

class MenuDemo(AutoFrame):
    f_menu = [
        # For "Save" entry, explicitly set (no) shortcut
        '&File >', ['Open', '&Save #', '&Quit'],
        '&Nested >', [
            # Subitem 1 and Item 2 to test correct discrimination of Shift key
            'Submenu 1 >', [ 'Subitem 1 #C-S-I'],
            'Item 2 #C-I',
            'Sub&menu 3 >', [],
        ],
        'Help >', ['About #F1']
    ]
    f_body = '''
    |
    '''

    # all handlers must be there
    def open(self):
        print('menu action: open')
    def save(self):
        print('menu action: save')
    # quit is predefined by AutoFrame
    def subitem_1(self):
        print('menu action: subitem_1')
    def item_2(self):
        print('menu action: item_2')
    def about(self):
        print('menu action: about')

        
    
class EmptyFrame(AutoFrame):
    f_body = ''
    
    
if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')
    TK = 'tk'
    if sys.argv[1:]:
        TK = sys.argv[1]
    set_toolkit(TK)
    if sys.argv[2:]:
        F = {
            'autoconnect': AutoconnectDemo,
            'bound': BoundCtlDemo,
            'alignment': AlignmentDemo,
            'boxes': BoxesDemo, 
            'list': ListDemo,
            'tree': TreeDemo,
        }[sys.argv[2]]
    else:
        F = Main
    frm = F()
    frm.f_show()
