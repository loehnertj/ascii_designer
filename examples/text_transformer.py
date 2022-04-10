#!/usr/bin/env python3
'''Minimalistic but full working example form.'''

from ascii_designer import AutoFrame

class TextTransformer(AutoFrame):
    f_body='''
                            |              |
        Text to transform:   [ Text_      ]
        
        Select transformation:
        
        (x) Uppercase
        ( ) Lowercase
        ( ) Title-case
        
            [ OK ]            [ Cancel ]~

    '''
    def ok(self):
        text = self.text
        if self.uppercase:
            text = text.upper()
        elif self.lowercase:
            text = text.lower()
        elif self.titlecase:
            text = text.title()
        print(text)
        self.close()
        
    def cancel(self):
        self.close()
        
if __name__ == '__main__':
    TextTransformer().f_show()

