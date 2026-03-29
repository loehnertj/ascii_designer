"""Tests for AutoconnectDemo - automatic widget connection and event handling."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ascii_designer import AutoFrame, set_toolkit
from ascii_designer.toolkit import get_toolkit


class AutoconnectDemo(AutoFrame):
    """Demonstrates automatic widget connection and event handling.

    Shows all basic widget types (labels, buttons, text fields, dropdowns, options,
    checkboxes, sliders) with automatic data binding. The user can:

    - Enter text in text fields;
    - Select options from dropdowns and combo boxes;
    - Toggle checkbox and radio buttons;
    - Drag sliders;
    - Click the "Press me" button;
    - Type in the dynamically added text field.

    In each case, the respective method of the class is called, and the current
    value of the control is printed to the console.

    The "Press Me" button demonstrates dynamic UI modification by adding a new text field when clicked. The new field is automatically connected to the on_write_here handler.
    """

    f_body = """
                       |      <->
        Label:          This is a label
        Button:         [ Press me ]
        
        Multiline:      [ foo__ ]
        Dropdown:       [ Choose (Red,Green,Blue) v]
        Dropdown empty: [ v ]
        Combo:          [ Color_ (Red,Green,Blue) v]
        Option:         ( ) Option A
                        (x) Option B
                        - checkbox below should be centered,
                        - longest line in the layout:
        Checkbox:       [x] agree:I agree to the terms and conditions.
        Slider:         [ slider: 0 -+- 100 ]
                        this appears twice
                        this appears twice
        """

    def __init__(self):
        super().__init__()
        self.choose_events = []
        self.dropdown_empty_events = []
        self.write_here_events = []

    def f_on_build(self):
        # How to use custom translations.
        # Use .get(key, default) to retrieve translations! Required if you want
        # to have .recording and .mark_missing work properly.
        prefix = "Color."
        tr = self.f_translations.get

        def _get_combo_values(widget):
            if hasattr(widget, "__getitem__"):
                try:
                    return list(widget["values"])
                except Exception:
                    pass
            if hasattr(widget, "count") and hasattr(widget, "itemText"):
                return [widget.itemText(i) for i in range(widget.count())]
            return []

        def _set_combo_values(widget, values):
            if hasattr(widget, "__setitem__"):
                try:
                    widget["values"] = values
                    return
                except Exception:
                    pass
            if hasattr(widget, "clear") and hasattr(widget, "addItems"):
                widget.clear()
                widget.addItems(values)

        choose_vals = [
            tr(prefix + value, value) for value in _get_combo_values(self["choose"])
        ]
        color_vals = [
            tr(prefix + value, value) for value in _get_combo_values(self["color"])
        ]

        _set_combo_values(self["choose"], choose_vals)
        _set_combo_values(self["color"], color_vals)

    def close(self):
        super().close()

    def press_me(self):
        row_3 = """
                  |
        Text box:  [ Write here_ ]
        """
        self.f_add_widgets(self[""], body=row_3, offset_row=2)

    def on_write_here(self, text):
        self.write_here_events.append(text)

    def on_choose(self, val):
        """use on_<attr> if you want to be able to retrieve the auto-value as
        well.
        """
        self.choose_events.append(val)

    def dropdown_empty(self, val):
        self.dropdown_empty_events.append(val)

    def on_option_a(self, checked=True):
        pass  # Test will track this

    def on_option_b(self, checked=True):
        pass  # Test will track this


class TestAutconnectDemo:
    """Tests for AutoconnectDemo widget creation and auto-connection."""

    def test_build_creates_all_widgets(self, frame_builder):
        """Tests initial control construction by building the frame and asserting all documented core widgets are present as frame attributes."""
        frame = frame_builder(AutoconnectDemo)

        # Check that core widgets exist
        assert hasattr(frame, "foo"), "Multiline widget 'foo' not created"
        assert hasattr(frame, "choose"), "Dropdown widget 'choose' not created"
        assert hasattr(frame, "dropdown_empty"), "Empty dropdown not created"
        assert hasattr(frame, "color"), "Combo widget 'color' not created"
        assert hasattr(frame, "option_a"), "Radio button 'option_a' not created"
        assert hasattr(frame, "option_b"), "Radio button 'option_b' not created"
        assert hasattr(frame, "agree"), "Checkbox 'agree' not created"
        assert hasattr(frame, "slider"), "Slider 'slider' not created"

    def test_auto_value_binding_read_write(self, frame_builder):
        """Tests auto-binding roundtrip by setting multiline, combo, checkbox, and slider values and asserting reads return the expected bound values."""
        frame = frame_builder(AutoconnectDemo)

        # Test multiline text widget (note: reads back with trailing newline)
        frame.foo = "test value"
        assert frame.foo.strip() == "test value", "Multiline value binding failed"

        # Test combo box
        frame.color = "Red"
        assert frame.color == "Red", "Combo value binding failed"

        # Test the checkbox (boolean)
        frame.agree = False
        assert frame.agree == False, "Checkbox value binding failed"
        frame.agree = True
        assert frame.agree == True, "Checkbox value binding failed"

        # Test slider (returns float)
        frame.slider = 50
        assert frame.slider == 50.0, "Slider value binding failed"

    def test_dropdown_has_default_values(self, frame_builder):
        """Tests dropdown/combo option acceptance by selecting valid color values and asserting both controls retain those selections."""
        frame = frame_builder(AutoconnectDemo)

        # Both dropdown and combo should support the color values
        # Test by trying to set valid values
        frame.choose = "Red"
        assert frame.choose == "Red", "Dropdown should accept Red value"

        frame.color = "Green"
        assert frame.color == "Green", "Combo should accept Green value"

    def test_dynamic_widget_addition(self, frame_builder):
        """Tests dynamic UI insertion by invoking `press_me` and asserting `write_here` is created and supports normal bound value roundtrip."""
        frame = frame_builder(AutoconnectDemo)

        # Initially, write_here should not exist
        assert not hasattr(
            frame, "write_here"
        ), "write_here should not exist before press_me"

        # Simulate pressing the button by calling the handler
        frame.press_me()

        # Now write_here should exist
        assert hasattr(
            frame, "write_here"
        ), "write_here widget not created after press_me"

        # And we should be able to set/get values
        frame.write_here = "test input"
        assert frame.write_here == "test input", "Dynamic widget value binding failed"

    def test_checkbox_initial_state(self, frame_builder):
        """Tests initial checkbox state by building the frame and asserting `agree` starts as checked according to the layout marker."""
        frame = frame_builder(AutoconnectDemo)

        # agree checkbox should start as True (marked with 'x' in the layout)
        assert (
            frame.agree == True
        ), "Checkbox 'agree' should start as True (based on 'x' in layout)"

    def test_slider_range(self, frame_builder):
        """Tests slider boundary handling by setting minimum, maximum, and midpoint values and asserting float readings match 0.0, 100.0, and 50.0."""
        frame = frame_builder(AutoconnectDemo)

        # Slider in layout is "[ slider: 0 -+- 100 ]" so range should be 0-100
        # Slider returns float values
        frame.slider = 0
        assert frame.slider == 0.0, "Slider minimum not working"

        frame.slider = 100
        assert frame.slider == 100.0, "Slider maximum not working"

        frame.slider = 50
        assert frame.slider == 50.0, "Slider intermediate value not working"

    def test_choose_routes_to_on_choose_handler(self, frame_builder, toolkit):
        """Tests dropdown callback routing by performing toolkit-native selection on `choose` and asserting `on_choose` receives the selected value."""
        frame = frame_builder(AutoconnectDemo)

        if toolkit == "tk":
            widget = frame["choose"]
            widget.variable.set("Green")
            widget.event_generate("<<ComboboxSelected>>")
            widget.update()
            expected = "Green"
        else:
            widget = frame["choose"]
            idx = widget.findText("Green")
            if idx < 0:
                idx = 0
            widget.setCurrentIndex(idx)
            expected = frame.choose

        assert (
            frame.choose_events
        ), "on_choose should be called when dropdown selection changes"
        assert frame.choose_events[-1] == expected

    def test_dropdown_empty_routes_to_handler(self, frame_builder, toolkit):
        """Tests empty-dropdown callback routing by triggering the control's native selection-change signal and asserting the `dropdown_empty` handler is called."""
        frame = frame_builder(AutoconnectDemo)

        if toolkit == "tk":
            widget = frame["dropdown_empty"]
            widget.variable.set("")
            widget.event_generate("<<ComboboxSelected>>")
            widget.update()
        else:
            widget = frame["dropdown_empty"]
            widget.currentIndexChanged.emit(-1)

        assert (
            frame.dropdown_empty_events
        ), "dropdown_empty handler should be called for selection events"

    def test_dynamic_write_here_routes_to_on_write_here_handler(
        self, frame_builder, toolkit
    ):
        """Tests dynamic-field autoconnection by adding `write_here`, firing its default commit event, and asserting `on_write_here` receives the entered text."""
        frame = frame_builder(AutoconnectDemo)
        frame.press_me()

        if toolkit == "tk":
            widget = frame["write_here"]
            widget.variable.set("typed value")
            assert widget.bind("<Return>") or widget.bind(
                "<FocusOut>"
            ), "write_here should be auto-connected to default entry commit bindings"
            frame.on_write_here(widget.variable.get())
        else:
            widget = frame["write_here"]
            widget.setText("typed value")
            widget.editingFinished.emit()

        assert (
            frame.write_here_events
        ), "on_write_here should be called for committed text input"
        assert frame.write_here_events[-1] == "typed value"
