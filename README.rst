ASCII Designer
==============

Did you ever design a form by scribbling something like this in your editor::

    To:        [ Name here_    ]
    
    Do you want to go out with me?
    
    ( ) Yes
    ( ) No
    ( ) Maybe
    
    [ Send ]     [ Abort ]

Only to wish you could be done with design and start coding? Look at this::

    from ascii_designer import AutoFrame
    
    class LoveLetter(AutoFrame):
        frame_body='''
                      |                    |
            To:        [ Name here_    ]
            
            Do you want to go out with me?
            
            ( ) Yes
            ( ) No
            ( ) Maybe
            
            [ Send ]     [ Abort ]
        '''
        def send(self):
            name = self['name_here'].text
            




INSTALLATION
------------

Requirements: Python >= 3, (currently) Pyqt4.

Then::

    pip install https://github.com/loehnertj/asciidesigner/archive/master.zip
    
Or, download / clone and use ``python setup.py install``.
    
    
DOCUMENTATION
-------------

Please proceed to http://asciidesigner.readthedocs.io/en/latest/index.html
    
TODO
----

Alpha-state software, mostly working.

This is a hobby project. If you need something quick, contact me or better, send a pull request.
