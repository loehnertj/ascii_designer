from PyQt4 import Qt
from PyQt4 import QtCore as qc
from PyQt4 import QtGui as qg

from pathlib import Path
from ascii_designer import AutoFrame, set_toolkit

set_toolkit('qt')

def aligned(ofs, size=16):
    return ofs // size * size

class Chunk:
    def __init__(self, raw, ofs=0, count=16, indent=0, content=''):
        self.content = content
        self.offset = '0x{0:08X}'.format(ofs-indent)
        self.indent = indent
        self._part = raw[ofs:ofs+count]
        self.actual_len = len(self._part)

        # printable representation
        r = [chr(x) if 32 <= x < 128 else '.' for x in self._part]
        r = ''.join(r)
        r = ' '*self.indent+r
        self.repr = r

        # hex representation
        hpart = self._part.hex().upper()
        for i, propname in enumerate('0123456789abcdef'):
            if i < self.indent or i >= self.indent+self.actual_len:
                ch = ''
            else:
                ii = 2*(i-self.indent)
                ch = hpart[ii:ii+2]
            setattr(self, propname, ch)

def make_chunks(raw, ofs=0, count=-1, content=''):
    if count<0:
        count = len(raw)-ofs
    indent = ofs - aligned(ofs)
    while count > 0:
        c = Chunk(raw, ofs, count=min(count, 16-indent), indent=indent, content=content)
        ofs += c.actual_len
        count -= c.actual_len
        indent = 0
        yield c
        content = ""

class MainWindow(AutoFrame):
    f_title = 'Hex Viewer'
    f_menu = [
        'File >', [
            'Open',
            'Quit',
        ]
    ]
    f_body = '''
    | -
    I[ = content (Offset, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, A, B, C, D, E, F, repr)]
    '''
    def __init__(self):
        super().__init__()
        self._raw = b'Hello World! This is the default content.'

    def f_build(self, parent, body=None):
        super().f_build(parent, body)
        # set col width
        desktop = qg.QDesktopWidget()
        geom = desktop.availableGeometry(desktop.primaryScreen())
        self[''].resize(geom.size()*0.7)
        # source of first column is the content attribute.
        self.content.sources('content')
        tv = self.f_controls['content']
        tv.setColumnWidth(0, 120)
        tv.setColumnWidth(1, 120)
        for i in range(2,18):
            tv.setColumnWidth(i, 40)

        self.update_view()

    def open(self):
        path = qg.QFileDialog.getOpenFileName(self[""], "Open", "", "All Files (*.*)")
        if not path:
            return
        raw = Path(path).read_bytes()
        self._raw = raw
        self.update_view()
    
    def update_view(self):
        items = list(make_chunks(self._raw, content='Raw bytes'))
        self.content=items
