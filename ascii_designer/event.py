"""
``@event`` decorator for methods, to make them into "subscribable" events.
"""

___all__ = [
    "event",
    "Event",
    "CancelEvent",
]

import inspect
from functools import wraps

try:
    from typing import Self
except ImportError:
    Self = None

from weakref import WeakValueDictionary
# FIXME: Use weakref for listeners as well


class CancelEvent(Exception):
    """Raise this in an event handler to inhibit all further processing."""


class Event:
    """Event descriptor

    - call to notify all listeners
    - exception in a listener will stop processing and be raised at the call
    (Trigger) site. Event-triggering function should handle any exceptions
    thrown at it.
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
    """Decorator that turns a method into an Event.

    Event handlers can be subscribed/unsubscribed using the ``+=`` and ``-=`` operators.

    Invocation of an event methods makes it call its associated handlers.

    The event method is expected to not have any body except for a docstring.

    Arguments with default values are forbidden, since their meaning would be
    ambiguous for the consumer.

    ``by_name`` controls whether arguments are passed to the handlers as positional
    arguments (args) or as named arguments (kwargs). The latter is recommended.

    * ``by_name=True``: Handlers must provide the same argument names as in the signature
    * ``by_name=False``: Handlers must provide the same argument order as in the singature.
    """
    if not prototype:
        # when called as @decorator(...)
        return lambda prototype: event(prototype=prototype, by_name=by_name)

    fn_wrapper = Event(prototype, by_name=by_name)
    fn_wrapper = wraps(prototype)(fn_wrapper)
    return fn_wrapper


# === usage demo ===


class HasEvents:
    """a class that defines an event"""

    @event(by_name=False)
    def foo(self, arg1: int, boolarg: bool):
        """Triggered when foo happens."""
