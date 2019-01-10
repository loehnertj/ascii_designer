'''
ToolkitQt-specific notes:

 * Alignment / Stretch not 100% reliable so far, if using row/col-span.
 * Tree / List widget not available so far
 * closing of form with X button cannot be stopped in the default handler. If 
    you need to do this, replace (root).closeEvent function.

'''
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
    def root(self, title='Window', on_close=None):
        '''make a root (window) widget'''
        root = qg.QWidget()
        root.setLayout(qg.QGridLayout())
        root.setWindowTitle(title)
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
        if isinstance(widget, qg.QPushButton):
            widget.clicked.connect(lambda *args: function())
            return
        # other cases
        handler = lambda *args, widget=widget: function(self.getval(widget))
        if isinstance(widget, (qg.QCheckBox, qg.QRadioButton)):
            # FIXME: For radiobutton, give the selected ID as value
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
        if cls is qg.QWidget: return widget
        if cls is qg.QGroupBox: 
            # child 0 is the layout, 1 the subwidget
            return widget.children()[1]
        if cls is qg.QPushButton: return widget.text()
        # FIXME: for Radio Button, return checked ID
        if cls is qg.QRadioButton: return widget.isChecked()
        if cls is qg.QCheckBox: return widget.isChecked()
        if cls is qg.QLineEdit: return widget.text()
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
        if type(widget) in (qg.QWidget, qg.QGroupBox):
            if type(widget) is qg.QGroupBox:
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
        elif isinstance(widget, qg.QPushButton):
            widget.setText(value)
        elif isinstance(widget, (qg.QCheckBox, qg.QRadioButton)):
            widget.setChecked(value)
        elif isinstance(widget, qg.QLineEdit):
            widget.setText(value)
        elif isinstance(widget, qg.QPlainTextEdit):
            widget.document().setPlainText(value)
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
        
    def row_stretch(self, container, row, proportion):
        '''set the given row to stretch according to the proportion.'''
        container.layout().setRowStretch(row, proportion)
        
    def col_stretch(self, container, col, proportion):
        '''set the given col to stretch according to the proportion.'''
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
        if given_id and text:
            f = qg.QGroupBox(parent=parent, title=text)
            f.setLayout(qg.QGridLayout())
            self.row_stretch(f, 0, 1)
            self.col_stretch(f, 0, 1)
            inner = qg.QWidget(f)
            self.place(inner, 0, 0)
            inner.setLayout(qg.QGridLayout())
        else:
            f = qg.QWidget(parent)
            f.setLayout(qg.QGridLayout())
        return f
        
    def label(self, parent, id=None, label_id=None, text=''):
        '''label'''
        return qg.QLabel(parent=parent, text=text)
        
    def button(self, parent, id=None, text=''):
        '''button'''
        return qg.QPushButton(parent=parent, text=text)
    
    def textbox(self, parent, id=None, text=''):
        '''single-line text entry box'''
        return qg.QLineEdit(text, parent=parent)
    
    def multiline(self, parent, id=None, text=''):
        '''multi-line text entry box'''
        return qg.QPlainTextEdit(text, parent=parent)
    
    def dropdown(self, parent, id=None, text='', values=None):
        '''dropdown box; values is the raw string between the parens. Only preset choices allowed.'''
        w = qg.QComboBox(parent)
        choices = [v.strip() for v in (values or '').split(',') if v.strip()]
        w.addItems(choices)
        return w
    
    def combo(self, parent, id=None, text='', values=None):
        '''not supported'''
        w = self.dropdown(parent, id=id, text=text, values=values)
        w.setEditable(True)
        return w
        
    def option(self, parent, id=None, text='', checked=None):
        '''Option button. Prefix 'O' for unchecked, '0' for checked.'''
        rb = qg.QRadioButton(text, parent=parent)
        rb.setChecked((checked=='x'))
        return rb
    
    def checkbox(self, parent, id=None, text='', checked=None):
        '''Checkbox'''
        cb = qg.QCheckBox(text, parent=parent)
        cb.setChecked((checked=='x'))
        return cb
    
    def slider(self, parent, id=None, min=None, max=None):
        '''slider, integer values, from min to max'''
        s = qg.QSlider(Qt.Horizontal, parent=parent)
        s.setMinimum(int(min))
        s.setMaximum(int(max))
        s.setTickPosition(qg.QSlider.TicksBelow)
        return s
    