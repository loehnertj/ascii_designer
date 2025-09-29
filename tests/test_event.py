import pytest
import inspect
from unittest.mock import Mock
from ascii_designer.event import Event, event, CancelEvent

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
    @event(exceptions="raise")
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
        # args are passed as given. Use *, / in signature to make clear what is passed.
        (lambda *args: None, False),
        (lambda **kwargs: None, True),
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


def test_event_force_namedargs():
    """If signature forces named args, ev cannot be called with positional args.

    Handlers get indeed passed named args.
    """

    @event
    def ev(*, a, b):
        pass

    ev += (m := Mock())
    with pytest.raises(TypeError):
        ev(1, 2)
    ev(a=1, b=2)
    m.assert_called_with(a=1, b=2)


def test_event_posargs():
    """If signature forces positional args, ev cannot be called with named args.

    Handlers get indeed passed positional args.
    """

    @event
    def ev(a, b, /):
        pass

    ev += (m := Mock())
    with pytest.raises(TypeError):
        ev(a=1, b=2)
    ev(1, 2)
    m.assert_called_with(1, 2)


def test_class_event_fire(Cls):
    """Object-level event notification works in principle"""
    o = Cls()
    o.ev1 += (m := Mock())
    o.ev1(a=1)
    m.assert_called_with(a=1)


def test_class_handler_separation(Cls):
    """Instances have separate handler lists"""
    o1 = Cls()
    o2 = Cls()
    o1.ev1 += (m1 := Mock())
    o2.ev1 += (m2 := Mock())
    o1.ev1(a=1)
    o2.ev1(a=2)
    m1.assert_called_once_with(a=1)
    m2.assert_called_once_with(a=2)


def test_event_copy_instance(Cls):
    """event can be copied from one instance to another (retaining handlers)"""
    o1 = Cls()
    o2 = Cls()
    o1.ev1 += (m1 := Mock())
    o2.ev1 = o1.ev1
    assert o2.ev1 is o1.ev1
    o2.ev1(a=2)
    m1.assert_called_once_with(a=2)
    o1.ev1 -= m1
    o2.ev1(a=1)
    m1.assert_called_once_with(a=2)


def test_class_self_handling(Cls):
    """self argument is not allowed"""
    o = Cls()

    with pytest.raises(TypeError):
        Cls.ev2(a=1)
    with pytest.raises(TypeError):
        o.ev2(a=2)
