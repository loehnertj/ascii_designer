'''Provides an event dispatcher class.
'''

# Bells and whistles that could be added:
# - return values
# - signature check
# - description

___all__ = [
    'EventSource',
    'CancelEvent',

]

class CancelEvent(Exception):
    '''Raise this in an event handler to inhibit all further processing.'''

class EventSource:
    '''Event dispatcher class
    
    You can register / unregister handlers via ``+=`` and ``-=`` methods.
    '''
    def __init__(self):
        self._handlers = []

    def __iadd__(self, handler):
        self._handlers.append(handler)
        return self

    def __isub__(self, handler):
        self._handlers.remove(handler)
        return self

    def __call__(self, *args, **kwargs):
        '''Trigger the event. To be called by the event's owner.'''
        for handler in self._handlers:
            try:
                handler(*args, **kwargs)
            except CancelEvent:
                return