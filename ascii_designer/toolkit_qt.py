'''
ToolkitQt-specific notes:

 * Alignment / Stretch not 100% reliable so far, if using row/col-span.
 * Tree / List widget not available so far
 * closing of form with X button cannot be stopped in the default handler. If 
    you need to do this, replace (root).closeEvent function.

'''
import sys
import qtpy as qt
from qtpy.QtCore import Qt, QAbstractItemModel, QModelIndex
import qtpy.QtGui as qg
import qtpy.QtWidgets as qw

from .toolkit import ToolkitBase, ListBinding
from .list_model import ObsList

__all__ = [
    'ToolkitQt',
]

_qtapp = qw.QApplication(sys.argv)
_qt_running=False

def _make_focusout(func):
    def _pte_focusOutEvent(event):
        if event.reason() != Qt.PopupFocusReason:
            func()
    return _pte_focusOutEvent

class ToolkitQt(ToolkitBase):
    default_shortcuts = {
        'new': qg.QKeySequence.New,
        'open': qg.QKeySequence.Open,
        'save': qg.QKeySequence.Save,
        'undo': qg.QKeySequence.Undo,
        'redo': qg.QKeySequence.Redo,
        'cut': qg.QKeySequence.Cut,
        'copy': qg.QKeySequence.Copy,
        'paste': qg.QKeySequence.Paste,
        'find': qg.QKeySequence.Find,
        'refresh': qg.QKeySequence.Refresh,
        # these are in addition to the Toolkit.default_shortcuts
        'save_as': qg.QKeySequence.SaveAs,
        'delete': qg.QKeySequence.Delete,
        'preferences': qg.QKeySequence.Preferences,
        'quit': qg.QKeySequence.Quit,
    }
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    # widget generators
    def root(self, title='Window', icon='', on_close=None):
        '''make a root (window) widget'''
        root = qw.QMainWindow()
        cw = qw.QWidget(root)
        root.setCentralWidget(cw)
        cw.setLayout(qw.QGridLayout())
        root.setWindowTitle(title)
        if icon:
            qicon = qg.QIcon(icon)
            if _qtapp.windowIcon().isNull():
                # Set icon for whole application; assuming that the first opened
                # window is representative
                _qtapp.setWindowIcon(qicon)
            else:
                root.setWindowIcon(qicon)
        if on_close:
            root.closeEvent = lambda ev: on_close()
        return root
        
    def show(self, frame):
        '''do what is necessary to make frame appear onscreen.'''
        frame.show()
        
        # now this is really not pretty, but as it says above, do what is necessary.
        global _qt_running
        if not _qt_running:
            _qt_running=True
            _qtapp.exec_()
            _qt_running=False
        
    def close(self, frame):
        '''close the frame'''
        frame.close()
        
    def place(self, widget, row=0, col=0, rowspan=1, colspan=1):
        '''place widget'''
        widget.parent().layout().addWidget(widget, row, col, rowspan, colspan)
        
    def connect(self, widget, function):
        '''bind the widget's default event to function.
        
        Default event is:
         * click() for a button
         * value_changed(new_value) for value-type controls;
            usually fired after focus-lost or Return-press.
        '''
        if isinstance(widget, qw.QPushButton):
            widget.clicked.connect(lambda *args: function())
            return
        elif isinstance(widget, qw.QTreeView):
            def handler(*args, widget=widget):
                mindex = widget.currentIndex()
                sl = mindex.internalPointer()
                item = sl[mindex.row()]
                function(item)
            widget.clicked.connect(handler)
            return
        # other cases
        handler = lambda *args, widget=widget: function(self.getval(widget))
        if isinstance(widget, (qw.QCheckBox, qw.QRadioButton)):
            # FIXME: For radiobutton, give the selected ID as value
            widget.toggled.connect(handler)
        elif isinstance(widget, qw.QLineEdit):
            widget.editingFinished.connect(handler)
        elif isinstance(widget, qw.QPlainTextEdit):
            widget.focusOutEvent = _make_focusout(handler)
        elif isinstance(widget, qw.QComboBox):
            if widget.isEditable():
                widget.lineEdit().editingFinished.connect(handler)
            else:
                widget.currentIndexChanged.connect(handler)
        elif isinstance(widget, qw.QSlider):
            widget.valueChanged.connect(handler)
        else:
            raise TypeError('I do not know how to connect a %s'%(widget.__class__.__name__))
            
    def getval(self, widget):
        cls = widget.__class__
        if cls is qw.QWidget: return widget
        if cls is qw.QGroupBox: 
            # child 0 is the layout, 1 the subwidget
            return widget.children()[1]
        if cls is qw.QPushButton: return widget.text()
        # FIXME: for Radio Button, return checked ID
        if cls is qw.QRadioButton: return widget.isChecked()
        if cls is qw.QCheckBox: return widget.isChecked()
        if cls is qw.QLineEdit: return widget.text()
        if cls is qw.QPlainTextEdit: return widget.toPlainText()
        if cls is qw.QSlider: return widget.value()
        if cls is qw.QComboBox:
            if widget.isEditable():
                return widget.lineEdit().text()
            else:
                idx = widget.currentIndex()
                return widget.itemText(idx) if idx >= 0 else None
        if cls is qw.QTreeView:
            return widget.model().list
            
    def setval(self, widget, value):
        if widget.hasFocus():
            # FIXME: check the appropriate modified indicators for the wiget
            # if not modified, go through
            return
        if type(widget) in (qw.QWidget, qw.QGroupBox):
            if type(widget) is qw.QGroupBox:
                # child 0 is the layout, 1 the subwidget
                widget = widget.children()[1]
            # Replace the frame with the given value
            if value.parent() is not widget.parent():
                raise ValueError('Replacement widget must have the same parent')
            # copy grid info
            layout = widget.parent().layout()
            idx = layout.indexOf(widget)
            row, col, rowspan, colspan = layout.getItemPosition(idx)
            # remove frame
            widget.deleteLater()
            # place new widget
            self.place(value, row, col, rowspan, colspan)
            # FIXME: I could not figure out how to query the orignal widget's alignment.
            self.anchor(value, True,True,True,True)
        elif isinstance(widget, qw.QPushButton):
            widget.setText(value)
        elif isinstance(widget, (qw.QCheckBox, qw.QRadioButton)):
            widget.setChecked(value)
        elif isinstance(widget, qw.QLineEdit):
            widget.setText(value)
        elif isinstance(widget, qw.QPlainTextEdit):
            widget.document().setPlainText(value)
        elif isinstance(widget, qw.QComboBox):
            if widget.isEditable():
                widget.lineEdit().setText(value)
            else:
                idx = widget.findText(value)
                if idx<0:
                   raise ValueError('Tried to set value "%s" that is not in the list.'%value)
                widget.setCurrentIndex(idx)
        elif isinstance(widget, qw.QSlider):
            widget.setValue(value)
        elif isinstance(widget, qw.QTreeView):
            widget.model().list = value
        else:
            raise TypeError('I do not know how to set the value of a %s'%(widget.__class__.__name__))
        
    def row_stretch(self, container, row, proportion):
        '''set the given row to stretch according to the proportion.'''
        if isinstance(container, qw.QMainWindow):
            container = container.centralWidget()
        container.layout().setRowStretch(row, proportion)
        
    def col_stretch(self, container, col, proportion):
        '''set the given col to stretch according to the proportion.'''
        if isinstance(container, qw.QMainWindow):
            container = container.centralWidget()
        container.layout().setColumnStretch(col, proportion)
        
    def anchor(self, widget, left=True, right=True, top=True, bottom=True):
        '''anchor the widget. Depending on the anchors, widget will be left-, 
        right-, center-aligned or stretched.
        '''
        align = {
            (False, False): Qt.AlignHCenter,
            (True, False): Qt.AlignLeft,
            (False, True): Qt.AlignRight,
            (True, True): Qt.Alignment()
            }[(left, right)]
        widget.parent().layout().setAlignment(widget, align)
                                 
        
    # Widgets
    def box(self, parent, id=None, text='', given_id=''):
        if isinstance(parent, qw.QMainWindow):
            parent = parent.centralWidget()
        if given_id and text:
            f = qw.QGroupBox(parent=parent, title=text)
            f.setLayout(qw.QGridLayout())
            self.row_stretch(f, 0, 1)
            self.col_stretch(f, 0, 1)
            inner = qw.QWidget(f)
            self.place(inner, 0, 0)
            inner.setLayout(qw.QGridLayout())
        else:
            f = qw.QWidget(parent)
            f.setLayout(qw.QGridLayout())
        return f
        
    def label(self, parent, id=None, label_id=None, text=''):
        '''label'''
        if isinstance(parent, qw.QMainWindow):
            parent = parent.centralWidget()
        return qw.QLabel(parent=parent, text=text)
        
    def button(self, parent, id=None, text=''):
        '''button'''
        if isinstance(parent, qw.QMainWindow):
            parent = parent.centralWidget()
        return qw.QPushButton(parent=parent, text=text)
    
    def textbox(self, parent, id=None, text=''):
        '''single-line text entry box'''
        if isinstance(parent, qw.QMainWindow):
            parent = parent.centralWidget()
        return qw.QLineEdit(text, parent=parent)
    
    def multiline(self, parent, id=None, text=''):
        '''multi-line text entry box'''
        if isinstance(parent, qw.QMainWindow):
            parent = parent.centralWidget()
        return qw.QPlainTextEdit(text, parent=parent)

    def treelist(self, parent, id=None, text='', columns=None):
        '''treeview (also usable as plain list)
        
        Qt notes: The model does no caching on its own, but retrieves
        item data all the time. I.e. if your columns are costly to
        calculate, roll your own caching please.
        '''
        if isinstance(parent, qw.QMainWindow):
            parent = parent.centralWidget()
        if columns:
            columns = [txt.strip() for txt in columns.split(',')]
        else:
            columns = []
        keys = [name.strip('_').lower() for name in columns]
        if text:
            keys.insert(0, '')
            columns.insert(0, text.strip())

        w = qw.QTreeView(parent)
        model = ListBindingQt(w, keys, columns)
        w.setModel(model)

        # connect events
        w.expanded.connect(model.on_gui_expand)
        w.setSortingEnabled(True)
        w.sortByColumn(-1, Qt.AscendingOrder)

        return w
    
    def dropdown(self, parent, id=None, text='', values=None):
        '''dropdown box; values is the raw string between the parens. Only preset choices allowed.'''
        if isinstance(parent, qw.QMainWindow):
            parent = parent.centralWidget()
        w = qw.QComboBox(parent)
        choices = [v.strip() for v in (values or '').split(',') if v.strip()]
        w.addItems(choices)
        return w
    
    def combo(self, parent, id=None, text='', values=None):
        '''dropdown with editable values.'''
        if isinstance(parent, qw.QMainWindow):
            parent = parent.centralWidget()
        w = self.dropdown(parent, id=id, text=text, values=values)
        w.setEditable(True)
        return w
        
    def option(self, parent, id=None, text='', checked=None):
        '''Option button. Prefix 'O' for unchecked, '0' for checked.'''
        if isinstance(parent, qw.QMainWindow):
            parent = parent.centralWidget()
        rb = qw.QRadioButton(text, parent=parent)
        rb.setChecked((checked=='x'))
        return rb
    
    def checkbox(self, parent, id=None, text='', checked=None):
        '''Checkbox'''
        if isinstance(parent, qw.QMainWindow):
            parent = parent.centralWidget()
        cb = qw.QCheckBox(text, parent=parent)
        cb.setChecked((checked=='x'))
        return cb
    
    def slider(self, parent, id=None, min=None, max=None):
        '''slider, integer values, from min to max'''
        if isinstance(parent, qw.QMainWindow):
            parent = parent.centralWidget()
        s = qw.QSlider(Qt.Horizontal, parent=parent)
        s.setMinimum(int(min))
        s.setMaximum(int(max))
        s.setTickPosition(qw.QSlider.TicksBelow)
        return s

    def menu_root(self, parent):
        '''Create menu object and set as parent's menu.'''
        return parent.menuBar()

    def menu_sub(self, parent, id, text):
        '''Append submenu labeled ``text`` to menu ``parent``.'''
        m = parent.addMenu(text)
        return m

    def menu_command(self, parent, id, text, shortcut, handler):
        '''Append command labeled ``text`` to menu ``parent``.

        Handler: ``func() -> None``, is immediately connected.
        '''
        action = qw.QAction(text, parent)
        if shortcut:
            if isinstance(shortcut, str):
                # parse shortcut
                shortcut = (shortcut
                    .upper()
                    .replace('C-', 'Ctrl+')
                    .replace('S-', 'Shift+')
                    .replace('A-', 'Alt+')
                )
                shortcut = qg.QKeySequence(shortcut)
            action.setShortcut(shortcut)
        action.triggered.connect(handler)
        parent.addAction(action)
    
class ListBindingQt(QAbstractItemModel, ListBinding):
    def __init__(self, parent, keys, captions, **kwargs):
        super().__init__(parent=parent, keys=keys, **kwargs)
        self._captions = captions
        self._list.toolkit_parent_id = QModelIndex()
        self._tv = parent

    def _set_list(self, val):
        '''replace all current items by the new iterable ``val``.'''
        self.modelAboutToBeReset.emit()
        super()._set_list(val)
        self._list.toolkit_parent_id = QModelIndex()
        self.modelReset.emit()

    def columnCount(self, parent):
        return len(self.keys)

    def headerData(self, section, orientation, role):
        def _crop(txt):
            return txt if not txt.endswith('_') else txt[:-1]
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return _crop(self._captions[section])
        return None

    def _idx2sl(self, model_index):
        '''returns (sublist, item idx)'''
        if not model_index.isValid():
            return None, None
        return (model_index.internalPointer(), model_index.row())

    def hasChildren(self, parent):
        sl, idx = self._idx2sl(parent)
        if sl is None:
            return True
        return sl.has_children(sl[idx])

    def rowCount(self, parent):
        pl, idx = self._idx2sl(parent)
        if parent.column() > 0:
            return 0
        if pl is None:
            sl = self._list
        else:
            #sl = pl.get_children(idx)
            sl = pl._childlists[idx]
            if sl is not None:
                sl.toolkit_parent_id = parent
        return len(sl or [])

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if column >= len(self.keys):
            return QModelIndex()
        pl, idx = self._idx2sl(parent)
        
        if pl is None:
            sl = self._list
        else:
            #sl = pl.get_children(idx)
            sl = pl._childlists[idx]
            if sl is not None:
                sl.toolkit_parent_id = parent
            else:
                sl = []
        
        if row < len(sl):
            # internalPointer is the ObsList CONTAINING our item.
            model_index = self.createIndex(row, column, sl)
            sl.toolkit_ids[row] = model_index
            return model_index
        else:
            return QModelIndex()

    def data(self, index, role):
        if not index.isValid(): return None
        if role not in (Qt.DisplayRole, Qt.EditRole): return None

        sl, idx = self._idx2sl(index)
        item = sl[idx]
        key = self.keys[index.column()]
        return self.retrieve(item, key)

    def setData(self, index, value, role):
        if not index.isValid(): return False
        if not self._captions[index.column()].endswith('_'):
            # Not editable
            return False
        if role != Qt.EditRole: return None

        sl, idx = self._idx2sl(index)
        item = sl[idx]
        key = self.keys[index.column()]
        self.store(item, value, key)
        # calculated fields might also have changed. Mutate whole item.
        sl.item_mutated(item)
        return True


    def flags(self, index):
        if not index.isValid(): return Qt.NoItemFlags
        is_editable = self._captions[index.column()].endswith('_')
        result = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if is_editable:
            result |= Qt.ItemIsEditable
        return result

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        sl, idx = self._idx2sl(index)

        # root item
        if sl is self._list:
            return QModelIndex()

        # otherwise
        return sl.toolkit_parent_id

    # === ObsList handlers ===
    def on_insert(self, idx, item, toolkit_parent_id):
        self.layoutChanged.emit()

    def on_load_children(self, children):
        self.layoutChanged.emit()

    def on_replace(self, iid, item):
        sl, idx = self._list.find(item)
        top_left = self.createIndex(idx, 0, sl)
        btm_right = self.createIndex(idx, len(self.keys)-1, sl)
        self.dataChanged.emit(top_left, btm_right)

    def on_remove(self, iid):
        self.layoutChanged.emit()

    def on_sort(self, sublist, info):
        super().on_sort(sublist, info)
        self.layoutChanged.emit()

    def on_get_selection(self):
        indexes = self._tv.selectedIndexes()
        return [
            sl[idx]
            for model_index in indexes
            if model_index.column() == 0
            for sl, idx in [self._idx2sl(model_index)]
        ]

    # === GUI event handlers ===
    def on_gui_expand(self, mindex):
        sl, idx = self._idx2sl(mindex)
        print('expand', idx)
        sl.load_children(idx)

    # actually not a connected handler
    def sort(self, column, order):
        # we need to do some trickery here, because QAbstractItemModel.sort
        # collides with ListBinding.sort. We detect which is wanted by looking
        # at column's type.
        if isinstance(column, str):
            # Forward to base class
            ListBinding.sort(self, column, order)
        else:
            # Qt sort implementation.
            if column < 0:
                # do nothing
                return
            ascending = (order == Qt.AscendingOrder)
            key = self.keys[column]
            ListBinding.sort(self, key, ascending)
