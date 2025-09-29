"""
``@event`` decorator for methods, to make them into subscribable events.

.. default-role:: py:obj
"""

__all__ = [
    "event",
    "Event",
    "CancelEvent",
]

import logging
import traceback
import inspect
from functools import update_wrapper
from typing import (
    Callable,
    Literal,
    ParamSpec,
    Generic,
    Self,
    TypeAlias,
    TypeVar,
    overload,
    get_args,
)

from weakref import WeakValueDictionary

# For keeping bound copies. I also tried to make listeners weak-referenced.
# Turns out that weak-referencing listeners is not that great after all, because
# it breaks using lambda or inner functions as handlers. They are immediately
# lost when the defining scope exits.

T = TypeVar("T")
P = ParamSpec("P")
R = TypeVar("R")  # return type

ExceptionPolicy: TypeAlias = Literal["log", "print", "raise", "group"]


class CancelEvent(Exception):
    """Raise this in an event handler to inhibit all further processing."""


class Event(Generic[P, R]):
    """Notifies a number of "listeners" (functions) when called.

    The principle is well-known under many names:

    * Define the event as member of a class that wants to tell the world
      about changes.
    * Arbitrary listeners can subscribe the event.
    * In the class's implementation, the event is called when the trigger
      condition occurs. Listeners will be called in the order they subscribed.

    **Defining events**

    In contrast to other adhoc event systems, this one enforces well-defined
    signatures and documentation. An event is created by decorating a method
    (the so-called "prototype") with ``@event``.

    The ``event`` will take over the method's signature, annotations and
    docstring. IDE tools and Sphinx documentation should (mostly) "see" the
    Event like any other method.

    The prototype method is executed every time the event is triggered. Usually
    it does not need any code except for a docstring or ``pass`` statement.

    Restrictions apply:

    * In ``strict`` mode, only positional-only and/or keyword-only
      args are allowed. This is to make clear to the user how the arguments
      will be given (by position or by name).

      * Yes: ``prototype(a: int, b: str, /)``
      * Yes: ``prototype(*, a: int, b: str)``
      * No: ``prototype(a:int, b:str)`` (but allowed in non-strict mode)

      ``strict`` mode is disabled for backwards compatibility, but will become
      the default in the future.

    * Arguments with default values are forbidden, since their meaning would be
      ambiguous for the user of the class.
    * The prototype does not get an automatic ``self`` argument. I.e. it works
      like a ``staticmethod``. You *can* define a ``self`` argument, but it must
      be given explicitly upon calling.

    **Listeners**

    A listener is a Callable whose signature fits the event specification.
    Event listeners can be subscribed/unsubscribed using the ``+=`` and ``-=``
    operators. Listener signature is *not* checked at the time of subscription.

    There is some freedom in listener signature. E.g. you can have extra
    parameters with default values, or you can catch the event data via
    ``*args`` / ``**kwargs``.

    **Triggering the event**

    The event is triggered by calling the ``event`` instance. Usually this
    happens within the class containing the Event.

    First, the wrapped protoype is executed, in order to verify correct arguments.
    Note that adherence to annotated types is *not* checked, in line with
    standard Python behavior.

    Any handler can raise `CancelEvent` to gracefully abort the processing of
    further listeners.

    **Return values**

    At most one listener is expected to return a value. If multiple listeners
    return a value, an exception is raised.

    The return type must always be Optional.

    **Exceptions**

    Listeners may raise exceptions that are unexpected for the event's origin
    site. `Event` has the "exceptions" parameter to control how they are
    handled:

    * ``"log"`` (default) emits a ``logging.error`` message with the traceback.
    * ``"print"`` prints the exception (using ``traceback.print_exception``).
    * ``"raise"`` raises any exception immediately. No subsequent listeners are
      called.
    * ``"group"`` calls all listeners, then raises an ``ExceptionGroup`` if any
      failed. The error is always an ``ExceptionGroup``, even in case of a single
      error.

    When using ``raise``, code that triggers an event must be prepared for any
    exception being thrown at it.

    `CancelEvent` is obviously exempt from this exception handling.

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
                self.counter_changed(123)
                # ...

        # User code
        class MyGUI:
            def __init__(self, counter_instance:MyCounter):
                self.counter_instance = counter_instance
                self.counter_instance.counter_changed_to += self.on_counter_changed

            def on_counter_changed(self, new_value):
                self.update_display(new_value)
    """

    def __init__(
        self,
        prototype: Callable[P, R],
        strict: bool | None = None,
        exceptions: ExceptionPolicy = "log",
    ):
        self._prototype = prototype
        self._listeners: list[Callable[P, R | None]] = []
        # None as default, so that we can discern from excplicit opt-in.
        # allows to add a warning in the future.
        self._strict: bool = strict or False
        if exceptions not in (policies := get_args(ExceptionPolicy)):
            raise ValueError(f"exceptions must be one of {policies}")
        self._exceptions = exceptions

        sig: inspect.Signature = inspect.signature(self._prototype)
        iP = inspect.Parameter
        if any(p.default is not iP.empty for p in sig.parameters.values()):
            raise TypeError("Default values are forbidden for events")
        if any(
            p.kind in (iP.VAR_POSITIONAL, iP.VAR_KEYWORD)
            for p in sig.parameters.values()
        ):
            raise TypeError("*args and **kwargs are forbidden for events")
        if self._strict and any(
            p.kind == iP.POSITIONAL_OR_KEYWORD for p in sig.parameters.values()
        ):
            raise TypeError(
                "Event arguments must be marked positional-only or keyword-only!"
            )
        self._self_arg = "self" in sig.parameters
        self._argnames = [p.name for p in sig.parameters.values() if p.name != "self"]
        update_wrapper(self, self._prototype)

        self._is_bound = False
        self._bound_copies = WeakValueDictionary()

    def __get__(self, instance, owner) -> "Event[P, R]":
        # Copy the event for each instance, so that that each instance
        # has its private list of listeners.
        if instance is None:
            return self
        key = id(instance)
        try:
            return self._bound_copies[key]
        except KeyError:
            ev = Event(self._prototype, strict=self._strict)
            ev._is_bound = True
            self._bound_copies[key] = ev
            return ev

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R | None:
        epolicy = self._exceptions
        results = []
        # Call to verify arguments
        r = self._prototype(*args, **kwargs)
        if r is not None:
            results.append(r)
        # === Call each listener ===
        excs = []
        for listener in self._listeners:
            try:
                r = listener(*args, **kwargs)
            except CancelEvent:
                break
            except Exception as exc:
                if epolicy == "log":
                    logging.exception(exc)
                elif epolicy == "print":
                    traceback.print_exception(exc)
                elif epolicy == "group":
                    excs.append(exc)
                else:
                    raise
            if r is not None:
                results.append(r)
        if excs:
            raise ExceptionGroup("One or more listeners raised an error.", excs)
        if len(results) > 1:
            raise RuntimeError("Multple return values from event handler")
        return None if not results else results[0]

    def __iadd__(self, listener: Callable[P, R | None]) -> Self:
        # Old handlers are most likely to vanish when new ones are added :-)
        self._listeners.append(listener)
        return self

    def __isub__(self, listener: Callable[P, R | None]) -> Self:
        if self._listeners is None:
            raise TypeError("Cannot remove listener from unbound event")
        self._listeners = [
            r_listener for r_listener in self._listeners if r_listener is not listener
        ]
        return self

    def __str__(self):
        names = ", ".join(self._argnames)
        prefix = "Bound" if self._is_bound else "Unbound"
        return f"<{prefix} Event {self._prototype.__qualname__}({names})>"

    __repr__ = __str__


# Decorator: Allow both @event and @event(params=...) syntax.


# Used as @event without parens
@overload
def event(
    prototype: Callable[P, R],
    *,
    strict: bool | None = None,
    exceptions: ExceptionPolicy = "log",
) -> Event[P, R]: ...


# Used as @event(...)
@overload
def event(
    prototype: None = None,
    *,
    strict: bool | None = None,
    exceptions: ExceptionPolicy = "log",
) -> Callable[[Callable[P, R]], Event[P, R]]: ...


def event(
    prototype: Callable[P, R] | None = None,
    *,
    strict: bool | None = None,
    exceptions: ExceptionPolicy = "log",
) -> Event[P, R] | Callable[[Callable[P, R]], Event[P, R]]:
    """Turn the decorated method into an Event.

    See `Event`. The `@event` decorator allows to pass arguments:

        @event(strict=False, exeptions="print")
        def some_event(arg1: bool, /): ...
    """
    if prototype is None:

        def wrap(prototype):
            return Event(prototype, strict=strict, exceptions=exceptions)

        return wrap
    else:
        return Event(prototype, strict=strict, exceptions=exceptions)
