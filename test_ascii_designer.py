'''This is part example collection, part regression test.
'''

#import tkinter as tk
from ascii_designer.tk_treeedit import TreeEdit
import logging
import sys
import random
import time
from ascii_designer import (
    AutoFrame, set_toolkit, nullable, ge0, Invalid, 
    load_translations_json, save_translations_json
)


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
     [Custom subclass           ]
     [Converters                ]
     [List view                 ]
     [List edit                 ]
     [Tree view                 ]
     [Alignment                 ]
     [Window Menu               ]
    I
       [Close]                   |
    '''
    f_icon = 'ascii_designer_icon.png'

    def autoconnect(self):
        AutoconnectDemo().f_show()
        
    def boxes_and_embedding(self):
        BoxesDemo().f_show()
        
    def bound_values(self):
        BoundCtlDemo().f_show()

    def custom_subclass(self):
        if TK not in ("tk", "ttk"):
            print("Only works under Tkinter, sorry")
        else:
            CustomSubclassDemo().f_show()
        
    def converters(self):
        if TK not in ("tk", "ttk"):
            print("Only works under Tkinter, sorry")
        else:
            ConvertersDemo().f_show()
        
    def list_view(self):
        ListDemo().f_show()
        
    def list_edit(self):
        ListEditDemo().f_show()

    def tree_view(self):
        TreeDemo().f_show()

    def on_alignment(self):
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

    def f_on_build(self):
        # How to use custom translations.
        # Use .get(key, default) to retrieve translations! Required if you want
        # to have .recording and .mark_missing work properly.
        prefix = "Color."
        tr = self.f_translations.get
        self["choose"]["values"] = [tr(prefix+value, value) for value in self["choose"]["values"]]
        self["color"]["values"] = [tr(prefix+value, value) for value in self["color"]["values"]]
        
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
        b = self.box = self.f_toolkit.button(parent=bm, text="this replaces box")
        # placeholder "value" is now the new widget
        assert self.box is b
        self.groupbox = self.f_toolkit.button(parent=gbm, text='this fills groupbox')
        
        # Nesting
        if self._level:
            self.nest_box = BoxesDemo(self._level-1)
        
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
    """creates all controls (except Treelist),
    also test out translations.
    """

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

class CustomSubclassDemo(AutoFrame):
    f_body = '''
    |                    |
     Please see the source code to understand what happens here.
     Custom entry field:  [_      ]
     Converted value:     conv_value
                          [reset]
    '''
    import tkinter.ttk as ttk

    class MyEntry(ttk.Entry):
        @property
        def float_value(self):
            v = None
            try:
                v = float(self.variable.get())
            except:
                self.state(["invalid"])
            else:
                self.state(["!invalid"])
            return v
        @float_value.setter
        def float_value(self, val):
            self.variable.set(f"{val:0.3f}")
            self.state(["!invalid"])

    def __init__(self):
        super().__init__()
        self.f_toolkit.widget_classes["textbox"] = self.MyEntry
    
    def on_custom_entry_field(self, text):
        # access the special float_value property of our field
        fval = self["custom_entry_field"].float_value
        if fval is None:
            self.label_conv_value = "<invalid>"
        else:
            # format as engineering number
            self.label_conv_value = f"{fval:e}"
    
    def on_reset(self):
        # Note how the last digits will be cut off by the format in the setter
        self["custom_entry_field"].float_value = 1.2345678
        self.on_custom_entry_field(None)

class ConvertersDemo(AutoFrame):
    f_option_tk_autovalidate = True
    f_body = """
                 |
         Float:   [ _           ]
         Int:     [ _           ]
         in-list: [_ (a, b, c) v]
         instant: [ _           ]
                  [test]
                  result
         output1: [ _           ]
         output2: [ _           ]
    """

    def f_on_build(self):
        self.label_result = ""
        self["float"].variable.convert = nullable(float)
        self["int"].variable.convert = ge0(int)
        def isinlist(val):
            if val not in ["a", "b", "c", "d"]:
                raise ValueError()
            return val
        self["inlist"].variable.convert = isinlist
        self["instant"].variable.convert = float
        # display the same value in different formats
        # Note that you will lose precision by this. Same effect as if you rounded.
        self["output1"].variable.convert_set = lambda x: f"{x:0.1e}"
        self["output2"].variable.convert_set = lambda x: f"{x:3.3f}"

    def on_instant(self, val):
        # on call of the handler, variable is retrieved and validation happens.
        # Nothing more required.
        pass

    def test(self):
        a = self.float
        b = self.int
        c = self.inlist
        d = self.instant
        if Invalid in [a, b, c, d]:
            self.label_result = "some input is invalid"
        else:
            self.label_result = "setting outputs"
            self.output1 = a if a is not None else 99.0
            self.output2 = a if a is not None else 99.0


class RankRow:
    def __init__(self, name, points, rank, is_cheater=False):
        self.name = name
        self.points = points
        self.rank = rank
        self.is_cheater = is_cheater
        
    def __str__(self):
        return f'{self.name} - {self.rank}'

    def __repr__(self):
        return f'RankRow(name={self.name!r}, points={self.points!r}, rank={self.rank!r}, is_cheater={self.is_cheater!r})'
            
class ListDemo(AutoFrame):
    f_body = '''
    |             |     |         |        |<->     |        |         |
    |Simple List   List with named~columns~~        
    I[= Shopping ] [= Players  (Name, Points, Rank) ~        ~        ]
     [ ] reorder   [Add] [Replace] [Mutate] [Remove] [resort] [unsort]                 
    '''
    def f_on_build(self):
        print(list(self.f_controls.keys()))
        self.shopping = ['Cabbage', 'Spam', 'Salmon Mousse', 'Fish'] * 5
        if TK != "qt":
            self["shopping"].variable.allow_sorting = False
        else:
            self["shopping"].model().allow_sorting = False
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

    def on_reorder(self, val):
        if TK != "qt":
            self["shopping"].variable.allow_reorder = val
        
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

    def resort(self):
        self.players.sort(restore=True)
    
    def unsort(self):
        """apply a regular python sorting, e.g. by item id"""
        self.players.sort(key=lambda item: id(item))

    def shopping(self, item):
        print('Buy: ', item)
    

class ListEditDemo(AutoFrame):
    f_body = '''
        | -
        I[= Players (Name_, Points_, Is_Cheater_, Rank)]
         Second view of same model:
         [= p2:Name_ (Points,)            ]
    '''
    def f_build(self, parent, body=None):
        super().f_build(parent, body)
        tv = self['players']
        # Configure treeviews, takes some toolkit-specific code
        if isinstance(tv, TreeEdit):
            # tk / ttk toolkit (ie. ascii_designer.tk_treeedit.TreeEdit widget)
            tv.allow = 'add, remove'
            # binding is ascii_designer.ListBindingTk
            binding = tv.variable

            # Source setup: name, rank columns are already fine. Configure points to read points property as-is & store int(edited_value).
            def setpoints(obj, val):
                obj.points = int(val)
            def set_ic(obj, val):
                obj.is_cheater = (val.lower() in ('true', '1', 'y', 'yes', 'on'))
            binding.sources(points=('points', setpoints), is_cheater=('is_cheater', set_ic))
        else:
            # qt toolkit (i.e. QTreeView)
            # binding is ascii_designer.ListBindingQt
            binding = tv.model()

            # Sources need not be configured. Qt handles varying datatype just fine.
        
        binding.factory = lambda: RankRow('', 0, 0)

        # init list
        self.players = [
            RankRow('CaptainJack', 9010, 1),
            RankRow('MasterOfDisaster', 3010, 2),
            RankRow('LittleDuck', 12, 3),
        ]
        # attach our own listeners for change events.
        # Preferably use the ObsList's events for this. This way you will not
        # only catch GUI-triggered but also externally induced changes.
        self.players.on_replace += self._print_change
        self.players.on_replace += self._check_recalc_ranks_ol
        # FIXME: flag against infinite recursion, this smells
        self._in_check_recalc = False

        # binds same ObsList instance to second view also.
        # Views are synchronized (sorting, mutation).
        # Note that this is not really a supported feature right now. Will crash
        # and burn instantly if the list has children.
        self.p2.sources('name')
        self['p2'].allow = 'add'
        self['p2'].autoedit_added = False
        binding = self["p2"].variable if isinstance(self["p2"], TreeEdit) else self["p2"].model()
        binding.factory = lambda: RankRow('', 0, 0)
        self.p2 = self.players

    def _print_change(self, toolkit_id, item):
        if not self._in_check_recalc:
            print('Item changed:', repr(item))

    def _check_recalc_ranks_ol(self, toolkit_id, item):
        if self._in_check_recalc:
            # _check_recalc_ranks triggers item_mutated again. Prevent infinite recursion.
            return
        self._in_check_recalc = True
        try:
            self._check_recalc_ranks()
        finally:
            self._in_check_recalc = False

    def _check_recalc_ranks(self):
        print('Autoupdate rank column')
        i = 1
        for row in sorted(self.players, key=(lambda row: row.points), reverse=True):
            # Note that we are not doing anything with the GUI object here. Just
            # updating a regular old Python object. Then we just tell the list "I changed this item".
            row.rank = i
            self.players.item_mutated(row)
            i += 1

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
        idx = self.files.find2(item)
        print('Result:', idx)
        print("retrieving it back:", self.files[idx])
        sib_idx = idx[:-1] + (None,)
        print("which is contained in:", self.files[sib_idx])
        

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

    t = AutoFrame.f_translations = load_translations_json("test_ascii_designer_i18n")
    # Set this to update f_translation if "missing" keys are queried. Need to
    # save afterwards. Probably should load ``language=""`` when doing this.
    #t.recording = True
    # Set this to have untranslated strings prepended by "$" dollar sign in the ui.
    t.mark_missing = True

    if sys.argv[2:]:
        F = {
            'autoconnect': AutoconnectDemo,
            'bound': BoundCtlDemo,
            'alignment': AlignmentDemo,
            'converters': ConvertersDemo,
            'boxes': BoxesDemo, 
            'list': ListDemo,
            'tree': TreeDemo,
            'listedit': ListEditDemo,
            'menu': MenuDemo,
        }[sys.argv[2]]
    else:
        F = Main
    frm = F()
    frm.f_show()

    # Uncomment if using recording mode.
    # !! will overwrite the used translation file
    #path = save_translations_json(t, "test_ascii_designer_i18n/default.json")
    #print("Saved translations:", path)
