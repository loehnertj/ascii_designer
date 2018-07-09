import sys
import PyQt4 as qt
from PyQt4.QtCore import Qt
import PyQt4.QtGui as qg

from .toolkit import ToolkitBase

def _make_focusout(func):
    def _pte_focusOutEvent(event):
        if event.reason() != Qt.PopupFocusReason:
            func()
    return _pte_focusOutEvent
        
class ToolkitQt(ToolkitBase):
    def __init__(self, **kwargs):
        self._app = qg.QApplication(sys.argv)
        super().__init__(**kwargs)
        
    # widget generators
    @property
    def root(self):
        '''return the root widget'''
        if not self._root:
            self._root = qg.QWidget()
            self._layout = qg.QGridLayout()
            self._root.setLayout(self._layout)
            self._root.setWindowTitle(self._title)
        return self._root
        
    def show(self, frame):
        '''do what is necessary to make frame appear onscreen.'''
        frame.show()
        self._app.exec_()
        
    def close(self, frame):
        '''close the frame'''
        frame.close()
        
    def place(self, widget, row=0, col=0, rowspan=1, colspan=1):
        '''place widget'''
        self._layout.addWidget(widget, row, col, rowspan, colspan)
        
        
    def connect(self, widget, function):
        '''bind the widget's default event to function.
        
        Default event is:
         * click() for a button
         * value_changed(new_value) for value-type controls;
            usually fired after focus-lost or Return-press.
        '''
        testhandler = lambda widget=widget, *args: print("TESTHANDLER: ", widget, args)
        if isinstance(widget, (qg.QPushButton, qg.QRadioButton)):
            widget.clicked.connect(lambda *args: function())
        elif isinstance(widget, qg.QCheckBox):
            widget.toggled.connect(lambda *args: function(widget.isChecked()))
        elif isinstance(widget, qg.QLineEdit):
            widget.editingFinished.connect(lambda: function(widget.text()))
        elif isinstance(widget, qg.QPlainTextEdit):
            widget.focusOutEvent = _make_focusout(lambda: function(widget.toPlainText()))
        elif isinstance(widget, qg.QComboBox):
            if widget.isEditable():
                widget.lineEdit().editingFinished.connect(lambda: function(widget.lineEdit().text()))
            else:
                widget.currentIndexChanged.connect(lambda idx: function(widget.itemText(idx) if idx>=0 else None))
        elif isinstance(widget, qg.QSlider):
            widget.valueChanged.connect(function)
        
    def row_stretch(self, row, proportion):
        '''set the given row to stretch according to the proportion.'''
        self._layout.setRowStretch(row, proportion)
        
    def col_stretch(self, col, proportion):
        '''set the given col to stretch according to the proportion.'''
        self._layout.setColumnStretch(col, proportion)
        
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
        self._layout.setAlignment(widget, align)
                                 
        
    # Widgets
    def frame(self, title=''):
        f = qg.QWidget()
        if title:
            f.setTitle(title)
        return f
    
    def spacer(self):
        '''a vertical/horizontal spacer'''
        
    def label(self, id=None, label_id=None, text=None):
        '''label'''
        return qg.QLabel(parent=self.root, text=(text or '').strip())
        
    def button(self, id=None, text=None):
        '''button'''
        return qg.QPushButton(parent=self.root, text=(text or '').strip())
    
    def textbox(self, id=None, text=None):
        '''single-line text entry box'''
        return qg.QLineEdit((text or '').strip(), parent=self.root)
    
    def multiline(self, id=None, text=None):
        '''multi-line text entry box'''
        return qg.QPlainTextEdit((text or '').strip(), parent=self.root)
    
    def dropdown(self, id=None, text=None, values=None):
        '''dropdown box; values is the raw string between the parens. Only preset choices allowed.'''
        w = qg.QComboBox(self.root)
        choices = [v.strip() for v in (values or '').split(',') if v.strip()]
        w.addItems(choices)
        return w
    
    def combo(self, id=None, text=None, values=None):
        '''not supported'''
        w = self.dropdown(id=id, text=text, values=values)
        w.setEditable(True)
        return w
        
    def option(self, id=None, text=None, checked=None):
        '''Option button. Prefix 'O' for unchecked, '0' for checked.'''
        rb = qg.QRadioButton((text or '').strip(), parent=self.root)
        rb.setChecked((checked=='x'))
        return rb
    
    def checkbox(self, id=None, text=None, checked=None):
        '''Checkbox'''
        cb = qg.QCheckBox((text or '').strip(), parent=self.root)
        cb.setChecked((checked=='x'))
        return cb
    
    def slider(self, id=None, min=None, max=None):
        '''slider, integer values, from min to max'''
        s = qg.QSlider(Qt.Horizontal, parent=self.root)
        s.setMinimum(int(min))
        s.setMaximum(int(max))
        s.setTickPosition(qg.QSlider.TicksBelow)
        return s
        
    def external(self, id=None):
        '''external reference'''
        return getattr(self._external_reference_provider, id)
    