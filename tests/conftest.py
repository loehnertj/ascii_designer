"""Shared test fixtures and helpers for GUI testing."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ascii_designer import set_toolkit, AutoFrame
from ascii_designer.toolkit import get_toolkit


@pytest.fixture(params=["tk", "qt"], ids=["tk", "qt"])
def toolkit(request):
    """Parametrized fixture that runs tests for both Tk and Qt backends.

    Yields the toolkit name ("tk" or "qt") and ensures the toolkit is set
    for the test duration. Skips Qt if not available.
    """
    toolkit_name = request.param

    # Check if Qt is available
    if toolkit_name == "qt":
        try:
            import qtpy  # noqa: F401
        except ImportError:
            pytest.skip("Qt toolkit not available (qtpy not installed)")

    set_toolkit(toolkit_name)
    yield toolkit_name


@pytest.fixture
def tk_only(toolkit):
    """Skip if toolkit is not 'tk'."""
    if toolkit != "tk":
        pytest.skip(f"Test only runs on Tk, not {toolkit}")
    return toolkit


@pytest.fixture
def qt_only(toolkit):
    """Skip if toolkit is not 'qt'."""
    if toolkit != "qt":
        pytest.skip(f"Test only runs on Qt, not {toolkit}")
    return toolkit


@pytest.fixture
def frame_builder(toolkit):
    """Factory for creating and managing AutoFrame test instances."""
    built_frames = []

    def _builder(frame_class, **kwargs):
        toolkit_inst = get_toolkit()
        root_widget = toolkit_inst.root(title=frame_class.__name__, on_close=None)
        frame = frame_class(**kwargs)
        frame.f_build(root_widget, frame.f_body)
        built_frames.append((frame, root_widget))
        return frame

    yield _builder

    # Cleanup all frames
    for frame, root_widget in built_frames:
        try:
            frame.close()
        except Exception:
            pass
        try:
            root_widget.destroy()
        except Exception:
            pass


# Tk-specific interaction helpers


def tk_event_return(widget):
    """Simulate pressing Enter in a Tk widget."""
    widget.event_generate("<Return>")
    widget.update()


def tk_event_focusout(widget):
    """Simulate focus loss in a Tk widget."""
    widget.event_generate("<FocusOut>")
    widget.update()


def tk_event_combobox_select(widget):
    """Simulate selecting from a Tk Combobox."""
    widget.event_generate("<<ComboboxSelected>>")
    widget.update()


def tk_event_treeview_select(widget):
    """Simulate selecting a Treeview item."""
    widget.event_generate("<<TreeviewSelect>>")
    widget.update()


def tk_event_treeview_open(widget):
    """Simulate expanding a Treeview node."""
    widget.event_generate("<<TreeviewOpen>>")
    widget.update()


def tk_update_all():
    """Process all pending Tk events."""
    # Get the root window and update
    try:
        import tkinter as tk

        root = tk.Tk._root
        if root:
            root.update_idletasks()
    except Exception:
        pass


# Qt-specific interaction helpers (using pytest-qt when available)


def qt_click_button(button):
    """Simulate clicking a Qt button."""
    button.click()


def qt_set_text(widget, text):
    """Set text in a Qt widget and emit editingFinished."""
    widget.setText(text)
    widget.editingFinished.emit()


def qt_set_combo_index(combo, index):
    """Set current index in a Qt combo box."""
    combo.setCurrentIndex(index)
    combo.currentIndexChanged.emit(index)


def qt_trigger_action(action):
    """Trigger a Qt menu action."""
    action.trigger()


# Common assertion helpers


def assert_widget_exists(frame, widget_id):
    """Assert that a widget with the given ID exists in the frame."""
    toolkit = get_toolkit()
    if toolkit.name == "tk":
        # Tk-specific: check if widget is in the frame's internal dict
        assert widget_id in frame._widgets, f"Widget '{widget_id}' not found in frame"
    elif toolkit.name == "qt":
        # Qt-specific: check if widget attribute exists
        assert hasattr(frame, widget_id) or widget_id in getattr(
            frame, "_widgets", {}
        ), f"Widget '{widget_id}' not found in frame"


def assert_widget_value(frame, widget_id, expected_value):
    """Assert widget value via frame attribute access."""
    actual = getattr(frame, widget_id)
    assert (
        actual == expected_value
    ), f"Widget '{widget_id}' value {actual!r} != expected {expected_value!r}"


def assert_widget_values(frame, expected_dict):
    """Assert multiple widget values at once."""
    for widget_id, expected_value in expected_dict.items():
        assert_widget_value(frame, widget_id, expected_value)
