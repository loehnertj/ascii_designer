'''Provides an event dispatcher class.
'''

# Bells and whistles that could be added:
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

    Handlers *may* return a result. If multiple handlers return results, last
    one is returned to the event's source.
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
        all_result = None
        for handler in self._handlers:
            try:
                result = handler(*args, **kwargs)
            except CancelEvent:
                break
            if result is not None:
                all_result = result
        return all_result
