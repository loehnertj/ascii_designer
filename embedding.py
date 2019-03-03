import tkinter as tk
from ascii_designer import AutoFrame, set_toolkit
set_toolkit('tk')

class Host(AutoFrame):
    f_body = '''
        |
            <placeholder>
    '''
    def f_build(self, parent, body):
        super().f_build(parent, body)
        #self.placeholder.setLayout(QGridLayout()) # only for Qt
        
        # create instance
        af_embedded = Embedded()
        # render widgets as children of self.placeholder
        af_embedded.f_build(parent=self.placeholder)
        # store away for later use    
        self._embedded = af_embedded
        
class Embedded(AutoFrame):
    f_body = '''
        |
            <another placeholder>
    '''
    def f_build(self, parent, body=None):
        super().f_build(parent, body)
        parent = self.another_placeholder.master
        self.another_placeholder = tk.Button(parent, text='3rd-party control')
        
if __name__ == '__main__':
    Host().f_show()