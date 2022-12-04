import logging

from .ascii_slice import slice_grid, merged_cells
from .toolkit import get_toolkit

__all__ = [
    'AutoFrame',
    ]

def L():
    return logging.getLogger(__name__)

def _convert_title(classname):
    # insert space before each capital letter
    title = ''.join(map(lambda x: x if x.islower() else " "+x, classname))
    title = title.strip()
    return title

class AutoFrame:
    '''
    Automatic frame.

    class name is converted to title. Override with ``f_title``.

    Set window icon by giving an icon file's path in ``f_icon``. Supported
    formats are OS-specific; recommended are ``.ico`` on Windows and ``.png`` on
    Unix.
    
    Body definition with ``f_body``, menu definition with ``f_menu``.
    
    To create own widgets or customize the autocreated ones, override :any:`f_on_build`.

    To add initialization code, override :any:`f_on_show`.

    Get at the created controls using AutoFrame[key].
    
    close(), exit(), quit() provided for convenience.
    
    Functions with same name as a control are autobound to the default handler (click or changed).
    
    Attributes are autobound to the control value (get/set), except if they are explicitly overwritten.
    '''

    f_option_tk_autovalidate:bool = False
    """
    If True, tk/ttk Entry and Combobox are set up for automatic update of widget state when validated.

    I.e. when value is retrieved or handler is called, the widgets foreground color (tk) or ``invalid`` state (ttk) is updated.

    Opt-in, because it might interfere with user code if not expected.
    """

    f_translations = {}
    """Translation dictionary.
    
    This can be set per-form or globally on the AutoFrame class. We only
    actually need the ``.get(key, default)`` method.
    
    Translation keys are formed as ``<Class name>.<Widget ID>``.

    Translations are used in ``f_build`` and ``f_build_menu`` functions.
    Currently there is no facility to retranslate after building the form.
    """

    def __init__(self):
        self.__dict__['f_controls'] = {}
        self.__dict__['f_toolkit'] = get_toolkit()
        try:
            title = self.f_title
        except AttributeError:
            self.f_title = _convert_title(self.__class__.__name__)
        try:
            menu = self.f_menu
        except AttributeError:
            self.f_menu = []
        try:
            icon = self.f_icon
        except AttributeError:
            self.f_icon = ''
        
    def f_show(self):
        '''Bring the frame on the screen.'''
        if not self.f_controls:
            prefix = self.__class__.__qualname__ + "."
            root = self.f_controls[''] = self.f_toolkit.root(
                title=self.f_translations.get(prefix+"f_title", self.f_title),
                icon=self.f_icon,
                on_close=self.close
            )
            self.f_build(root, self.f_body)
            self.f_build_menu(root, self.f_menu)
        self.f_on_show()
        self.f_toolkit.show(root)
        
    def f_build(self, parent, body=None):
        body = body or self.f_body
        sliced_grid = slice_grid(body)
        
        # init rows / columns
        for col, head in enumerate(sliced_grid.column_heads):
            self.f_toolkit.col_stretch(parent, col, head.count('-'))
        for row, cells in enumerate(sliced_grid.body_lines):
            # first cell
            head = cells[0:1]
            # first char of first cell
            if head: head = head[0][0:1]
            self.f_toolkit.row_stretch(parent, row, 1 if head=='I' else 0)
        self.f_add_widgets(parent, sliced_grid, autoframe=self)
        self.f_on_build()

    def f_on_build(self):
        '''Hook that is called after form has been built. 
        
        Override this to add custom initialization of widgets.
        '''

    def f_on_show(self):
        '''Hook that is called when form is about to be shown on screen.

        In contrast to f_on_build, this is called again if the form is closed
        and reopened.
        '''
        
    def f_build_menu(self, parent, menu=None):
        '''Builds the menu from the given menu definition.

        Menu definition is a list which can (currently) contain actions
        and submenus.

        An Action is simply a string, which is converted to an identifier
        following the same rules as the other widgets. It triggers the
        ``self.`` method named as the identifier. The method must
        be defined.

        A submenu is created by a string ending in ">", followed by an item
        which is itself a list (the submenu content).
        
        Example:

            >>> menu = [
                    'File >', ['Open', 'Save', 'Quit'],
                    'Help >', ['About'],
                ]
            >>> autoframe.f_build_menu(autoframe.f_controls(''), menu)
        '''

        menudef = menu or self.f_menu
        if not menudef:
            return
        toolkit = self.f_toolkit

        mroot = toolkit.menu_root(parent)
        toolkit.parse_menu(
            mroot, 
            menudef, 
            self,
            translations=self.f_translations,
            translation_prefix = self.__class__.__qualname__ + "."
        )

    def f_add_widgets(self, parent, sliced_grid=None, body=None, offset_row=0, offset_col=0, autoframe=None):
        if not sliced_grid:
            sliced_grid = slice_grid(body)
        toolkit = self.f_toolkit
        if hasattr(toolkit, "autovalidate"):
            toolkit.autovalidate = self.f_option_tk_autovalidate
        autoframe = autoframe or self
        translation_prefix = self.__class__.__qualname__ + "."
        
        # create controls
        for grid_element in merged_cells(sliced_grid):
            if not grid_element.text.strip():
                continue
            id, widget = toolkit.parse(
                parent,
                grid_element.text,
                translations=self.f_translations,
                translation_prefix=translation_prefix
            )
                
            # place on the grid
            e = grid_element
            toolkit.place(widget, row=e.row+offset_row, col=e.col+offset_col, rowspan=e.rowspan, colspan=e.colspan)
            text = e.text.replace('~',' ')
            toolkit.anchor(widget, left=not text.startswith(' '), right=not text.endswith(' '))
            # autowire
            try:
                attr = getattr(autoframe, id)
            except AttributeError:
                attr = None
            if attr is None or not callable(attr):
                # try with "on_<attr>"
                try:
                    attr = getattr(autoframe, 'on_'+id)
                except AttributeError:
                    attr = None # not callable
            if callable(attr):
                toolkit.connect(widget, attr)
            self.f_controls[id] = widget
                
        
    def __setattr__(self, name, val):
        if name in self:
            self.f_toolkit.setval(self[name], val)
        else:
            super().__setattr__(name, val)
    
    def __getattr__(self, name):
        if 'f_controls' not in self.__dict__:
            raise RuntimeError('You forgot to call super().__init__!')
        if name in self.f_controls:
            # use toolkit to extract value from the widget
            return self.f_toolkit.getval(self[name])
        else:
            raise AttributeError('Attribute %s is not defined'%(name,))
    
    def __getitem__(self, key):
        return self.f_controls[key]
    
    def __contains__(self, key):
        return key in self.f_controls
    
    def close(self):
        '''Close the window. 
        
        This is also called when the window is closed using the x button. Be 
        sure to call ``super().close()`` or your window won't close.
        '''
        self.f_toolkit.close(self[''])
    
    def quit(self):
        return self.close()
    
    def exit(self):
        return self.close()