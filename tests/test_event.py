import pytest
import inspect
from unittest.mock import Mock
from ascii_designer.event import Event, EventSource, event, CancelEvent

# TBD:
# binding to class event:
# XXX: Expectation? Should invoke both on Cls.foo and instance.foo?
# XXX: how about subclassing, invoke for all subclasses?
# How should the self parameter work?


@pytest.fixture
def ev1():
    @event
    def ev1():
        """Event 1"""

    return ev1


@pytest.fixture
def ev2():
    @event
    def ev2(a: int):
        """Event 2"""

    return ev2


@pytest.fixture
def Cls():
    class Cls:
        @event
        def ev1(a: int):
            pass

        @event
        def ev2(self, a):
            pass

    return Cls


def test_event_source_legacy_alias():
    assert EventSource is Event


def test_event_legacy():
    """Can define and use Event() without prototype (legacy behavior)

    Will accept and pass on any arguments as given.
    """
    ev = Event()
    ev += (m := Mock())
    ev()
    m.assert_called_with()
    ev(1, x=2)
    m.assert_called_with(1, x=2)


def test__event_docstring(ev1):
    """Docstring is passed through"""
    assert ev1.__doc__ == "Event 1"


# not working yet, since Event is actually a class
def test_event_signature():
    """parameter names and annotations are passed"""

    @event
    def ev(a: int):
        pass

    sig = inspect.signature(ev)
    assert len(sig.parameters) == 1
    p = sig.parameters["a"]
    assert p.name == "a"
    assert p.annotation is int


def test_event_signature_check(ev2):
    """Calling event with bad parameters raises TypeError"""
    ev = ev2

    with pytest.raises(TypeError):  # a is missing
        ev()
    with pytest.raises(TypeError):  # b is extra
        ev(1, b=1)
    with pytest.raises(TypeError):  # 2, 3 are extra
        ev(1, 2, 3)
    # This does not constitute an error, since type hints are not enforced.
    ev("not an integer")
    # Can use kwarg syntax as well
    ev(a=1)


@pytest.mark.parametrize(
    "handler,iserror",
    [
        (lambda a, b: None, True),
        (lambda a, b=1: None, False),
        # By default, kwargs are passed
        (lambda *args: None, True),
        (lambda **kwargs: None, False),
        # a is missing
        (lambda b, c: None, True),
    ],
)
def test_event_handler_signature(ev2, handler, iserror):
    """Event *handler* signature is not enforced when subscribing.

    Handler with wrong signature will raise TypeError when invoked.

    Handler may specify additional params with default value, and/or catch
    values in ``**kwargs``.
    """
    # Never fails
    ev2 += handler
    if iserror:
        with pytest.raises(TypeError):
            ev2(1)
    else:
        ev2(1)


def test_event_str(ev1, Cls):
    o = Cls()
    assert str(Event()) == "<Event>"
    assert str(ev1) == "<Unbound Event ev1.<locals>.ev1()>"
    assert str(Cls.ev1) == "<Unbound Event Cls.<locals>.Cls.ev1(a)>"
    assert str(Cls.ev2) == "<Unbound Event Cls.<locals>.Cls.ev2(a)>"
    assert str(o.ev1) == "<Bound Event Cls.<locals>.Cls.ev1(a)>"
    assert str(o.ev2) == "<Bound Event Cls.<locals>.Cls.ev2(a)>"


def test_event_no_kwarg():
    """Cannot define event with kwargs"""
    with pytest.raises(TypeError):

        @event
        def ev(kwarg=1):
            pass


def test_event_no_args():
    """Cannot define event with *args"""
    with pytest.raises(TypeError):

        @event
        def ev(*args):
            pass


def test_event_no_kwargs():
    """Cannot define event with **kwargs"""
    with pytest.raises(TypeError):

        @event
        def ev(**kwargs):
            pass


def test_module_event_fire(ev1):
    """Module-level event notification works in principle"""
    ev1 += (m := Mock())
    ev1()
    m.assert_called_with()


def test_event_namedargs():
    """By default, args are passed as named args"""

    @event
    def ev(a, b):
        pass

    ev += (m := Mock())
    ev(1, 2)
    m.assert_called_with(a=1, b=2)


def test_event_posargs():
    """If configured so, args are passed positional"""

    @event(by_name=False)
    def ev(a, b):
        pass

    ev += (m := Mock())
    ev(1, 2)
    m.assert_called_with(1, 2)


def test_class_event_fire(Cls):
    """Object-level event notification works in principle"""
    o = Cls()
    o.ev1 += (m := Mock())
    o.ev1(1)
    m.assert_called_with(a=1)


def test_class_handler_separation(Cls):
    """Instances have separate handler lists"""
    o1 = Cls()
    o2 = Cls()
    o1.ev1 += (m1 := Mock())
    o2.ev1 += (m2 := Mock())
    o1.ev1(1)
    o2.ev1(2)
    m1.assert_called_once_with(a=1)
    m2.assert_called_once_with(a=2)


def test_event_copy_instance(Cls):
    """event can be copied from one instance to another (retaining handlers)"""
    o1 = Cls()
    o2 = Cls()
    o1.ev1 += (m1 := Mock())
    o2.ev1 = o1.ev1
    assert o2.ev1 is o1.ev1
    o2.ev1(2)
    m1.assert_called_once_with(a=2)
    o1.ev1 -= m1
    o2.ev1(1)
    m1.assert_called_once_with(a=2)


def test_class_self_handling(Cls):
    """self argument CAN be there but is ignored."""
    o = Cls()
    Cls.ev2 += (m1 := Mock())
    o.ev2 += (m2 := Mock())

    Cls.ev2(1)
    o.ev2(2)

    m1.assert_called_once_with(a=1)
    m2.assert_called_once_with(a=2)


# Not yet implemented
@pytest.mark.xfail
def test_class_call_with_self(Cls):
    Cls.ev2 += (m := Mock())
    o = Cls()
    Cls.ev2(o, 3)
    # XXX WHat do we expect here!?
