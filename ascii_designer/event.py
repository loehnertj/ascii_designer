"""
``Event`` object and ``@event`` decorator for methods, to make them into
"subscribable" events.

.. default-role:: py:obj
"""

__all__ = [
    "event",
    "Event",
    "CancelEvent",
]

import inspect
from functools import wraps, update_wrapper

try:
    from typing import Self
except ImportError:
    Self = None

from weakref import WeakValueDictionary
# FIXME: Use weakref for listeners as well


class CancelEvent(Exception):
    """Raise this in an event handler to inhibit all further processing."""


class Event:
    """Notifies a number of "listeners" (functions) when called.

    The principle is well-known under many names:

    * Define the ``Event`` as member of a class that wants to tell the world
      about changes.
    * Arbitrary listeners can subscribe the event.
    * In the class's implementation, the ``Event`` is called when the trigger
      condition occurs. Listeners will be called in the order they subscribed.

    **Defining events**

    In contrast to many adhoc event systems, this one encourages well-defined
    signatures and documentation. The recommended way to create an event is by
    decorating a method (the so-called "prototype") with ``@event``.

    The ``Event`` will take over the method's signature, annotations and
    docstring. IDE tools and Sphinx documentation should (mostly) "see" the
    Event like any other method.

    The prototype method is executed every time the event is triggered. Usually
    it does not need any code except for a docstring or ``pass`` statement.

    Arguments with default values are forbidden, since their meaning would be
    ambiguous for the user of the class.

    That said, you can also create an "untyped" event by assigning ``Event()``
    to a variable.

    **Listeners**

    A listener is a Callable whose signature fits the event specification.
    Event listeners can be subscribed/unsubscribed using the ``+=`` and ``-=``
    operators. Listener signature is *not* checked at the time of subscription.

    ``by_name`` controls whether arguments are passed to the listeners as
    positional arguments (args) or as named arguments (kwargs). The latter is
    recommended.

    * ``by_name=True``: Listeners must provide the same argument *names* as in
      the signature
    * ``by_name=False``: Listeners must provide the same argument *order* as in
      the signature.

    There is some freedom in listener signature. E.g. you can have extra
    parameters with default values, or you can catch the event data via
    ``*args`` or ``**kwargs``.

    **Triggering the event**

    The event is triggered by calling the ``Event``. Usually this happens within
    the class containing the Event.

    First, the wrapped protoype is executed, in order to verify correct arguments.
    Note that adherence to annotated types is *not* checked, in line with
    standard Python behavior.

    Then, arguments are normalized to be all-positional or all-named args,
    depending on the ``by_name`` setting. Listeners are then called with these
    args in order of subscription.

    At most one handler is allowed to return a non-``None`` result, wich will
    be returned as result of the event trigger call. If multiple handlers return
    something, ``ValueError`` is raised.

    Any handler can raise `CancelEvent` to gracefully abort the processing of
    further listeners.

    If the event was defined without prototype using ``Event()``, there will be
    no check of arguments and no "normalization" to args-only / kwargs-only.

    .. note::
        Any exception raised by a listener will stop processing and is
        raised at the call (Trigger) site. Event-triggering function must be
        prepared to handle any exceptions thrown at it.

    **``self`` argument**

    The wrapped method *can* have a ``self`` argument, which will simply be
    filtered out. From the purist standpoint, it doesn't make sense to have it;
    however its absence confuses tools, so I advise to include it.

    **Unbound/Bound distinction**

    Analogous to unbound methods, the class will contain the event as "unbound"
    event. You can in principle subscribe to it, and trigger it using
    ``Class.event()``. There is only one, global list of subscribers.

    A class *instance* will have a "bound" copy of the ``Event``, meaning that
    it has its own list of subscribers independent from all other instances. It
    does *not* inherit listeners from the unbound event. Typically, the *bound*
    event is the one you want to subscribe to.

    Lastly, you can also apply ``@event`` to a module-level function. There will
    be only one, global list of subscribers, same as for an unbound event.

    **Example**::

        # Class definition
        class MyCounter:
            @event
            def counter_changed_to(self, new_value:int):
                '''Event: counter changed to given value'''

            def my_timer_function(self):
                # ...
                try:
                    self.counter_changed(123)
                except:
                    logging.error("Error in event listener", exc_info=True)
                # ...

        # User code
        class MyGUI:
            def __init__(self, counter_instance:MyCounter):
                self.counter_instance = counter_instance
                self.counter_instance.counter_changed_to += self.on_counter_changed

            def on_counter_changed(self, new_value):
                self.update_display(new_value)
    """

    def __init__(self, prototype=None, by_name=True):
        self._prototype = prototype
        self._by_name = by_name
        self._listeners = []
        if self._prototype:
            sig: inspect.Signature = inspect.signature(self._prototype)
            P = inspect.Parameter
            if any(p.default is not P.empty for p in sig.parameters.values()):
                raise TypeError("Default values are forbidden for events")
            if any(
                p.kind in (P.VAR_POSITIONAL, P.VAR_KEYWORD)
                for p in sig.parameters.values()
            ):
                raise TypeError("*args and **kwargs are forbidden for events")
            self._self_arg = "self" in sig.parameters
            self._argnames = [
                p.name for p in sig.parameters.values() if p.name != "self"
            ]
            update_wrapper(self, prototype)
        else:
            self._self_arg = False
            self._argnames = []
        self._is_bound = False
        self._bound_copies = WeakValueDictionary()

    def __get__(self, instance, owner):
        # Copy the event for each instance, so that that each instance
        # has its private list of listeners.
        if instance is None:
            return self
        key = id(instance)
        try:
            return self._bound_copies[key]
        except KeyError:
            ev = Event(self._prototype, self._by_name)
            ev._is_bound = True
            self._bound_copies[key] = ev
            return ev

    def __call__(self, *args, **kwargs):
        results = []
        if self._prototype:
            # Checks args/kwargs against specificed signature
            # If the self arg is there, supply it.
            if self._self_arg:
                r = self._prototype(None, *args, **kwargs)
            else:
                r = self._prototype(*args, **kwargs)
            if r is not None:
                results.append((r, self._prototype))
            # Hide internal call semantics (by-position or by-name) from called
            # listeners, by normalizing to the specified behavior.
            if self._by_name:
                # convert args to kwargs
                kwargs1 = {name: val for name, val in zip(self._argnames, args)}
                kwargs = kwargs.copy()
                kwargs.update(kwargs1)
                args = []
            else:
                # convert kwargs to args
                args = list(args)
                for name in self._argnames[len(args) :]:
                    args.append(kwargs[name])
                kwargs = {}
        # === Call each listener ===
        for listener in self._listeners:
            try:
                r = listener(*args, **kwargs)
                if r is not None:
                    results.append((r, listener))
            except CancelEvent:
                break
        if len(results) > 1:
            raise ValueError("Got more than one event result: %r" % (results,))
        elif len(results) == 1:
            return results[0][0]
        else:
            return None

    # TODO: Signature of listener
    def __iadd__(self, listener) -> Self:
        if self._listeners is None:
            raise TypeError("Cannot add listener to unbound event")
        self._listeners.append(listener)
        return self

    def __isub__(self, listener) -> Self:
        if self._listeners is None:
            raise TypeError("Cannot remove listener from unbound event")
        self._listeners.remove(listener)
        return self

    def __str__(self):
        if not self._prototype:
            return "<Event>"
        names = ", ".join(self._argnames)
        prefix = "Bound" if self._is_bound else "Unbound"
        return f"<{prefix} Event {self._prototype.__qualname__}({names})>"

    __repr__ = __str__


# legacy alias
EventSource = Event


def event(prototype=None, by_name=True):
    """Decorator that turns a function or method into an `Event`.

    See `Event`. The decorated function is used as prototype; special constraints apply.
    """
    if not prototype:
        # when called as @decorator(...)
        return lambda prototype: event(prototype=prototype, by_name=by_name)

    return Event(prototype, by_name=by_name)
