import sys
import PyQt4 as qt
from PyQt4.QtCore import Qt
import PyQt4.QtGui as qg

from .toolkit import ToolkitBase

__all__ = [
    'ToolkitQt',
]

_qtapp = qg.QApplication(sys.argv)
_qt_running=False

def _make_focusout(func):
    def _pte_focusOutEvent(event):
        if event.reason() != Qt.PopupFocusReason:
            func()
    return _pte_focusOutEvent

class ToolkitQt(ToolkitBase):
    def __init__(self, **kwargs):
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
        self._layout.addWidget(widget, row, col, rowspan, colspan)
        
    def connect(self, widget, function):
        '''bind the widget's default event to function.
        
        Default event is:
         * click() for a button
         * value_changed(new_value) for value-type controls;
            usually fired after focus-lost or Return-press.
        '''
        testhandler = lambda widget=widget, *args: print("TESTHANDLER: ", widget, args)
        if isinstance(widget, qg.QPushButton):
            widget.clicked.connect(lambda *args: function())
            return
        # other cases
        handler = lambda *args, widget=widget: function(self.getval(widget))
        if isinstance(widget, (qg.QCheckBox, qg.QRadioButton)):
            widget.toggled.connect(handler)
        elif isinstance(widget, qg.QLineEdit):
            widget.editingFinished.connect(handler)
        elif isinstance(widget, qg.QPlainTextEdit):
            widget.focusOutEvent = _make_focusout(handler)
        elif isinstance(widget, qg.QComboBox):
            if widget.isEditable():
                widget.lineEdit().editingFinished.connect(handler)
            else:
                widget.currentIndexChanged.connect(handler)
        elif isinstance(widget, qg.QSlider):
            widget.valueChanged.connect(handler)
        else:
            raise TypeError('I do not know how to connect a %s'%(widget.__class__.__name__))
            
    def getval(self, widget):
        cls = widget.__class__
        if cls is qg.QPushButton: raise TypeError('A button has no value')
        if cls is qg.QRadioButton: return widget.isChecked()
        if cls is qg.QCheckBox: return widget.isChecked()
        if cls is qg.QLineEdit: return widget.text(),
        if cls is qg.QPlainTextEdit: return widget.toPlainText()
        if cls is qg.QSlider: return widget.value()
        if cls is qg.QComboBox:
            if widget.isEditable():
                return widget.lineEdit().text()
            else:
                idx = widget.currentIndex()
                return widget.itemText(idx) if idx >= 0 else None
            
    def setval(self, widget, value):
        if widget.hasFocus():
            # FIXME: check the appropriate modified indicators for the wiget
            # if not modified, go through
            return
        if isinstance(widget, qg.QPushButton):
            raise ValueError('Cannot set value of Push Button')
        elif isinstance(widget, qg.QCheckBox, qg.QRadioButton):
            widget.setChecked(value)
        elif isinstance(widget, qg.QLineEdit):
            widget.setText(value)
        elif isinstance(widget, qg.QPlainTextEdit):
            widget.document().setText(value)
        elif isinstance(widget, qg.QComboBox):
            if widget.isEditable():
                widget.lineEdit().setText(value)
            else:
                idx = widget.findText(value)
                if idx<0:
                   raise ValueError('Tried to set value "%s" that is not in the list.'%value)
                widget.setCurrentIndex(idx)
        elif isinstance(widget, qg.QSlider):
            widget.setValue(value)
        else:
            raise TypeError('I do not know how to set the value of a %s'%(widget.__class__.__name__))
        
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
    