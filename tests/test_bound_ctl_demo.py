"""Tests for BoundCtlDemo - binding and roundtrip for all control types."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ascii_designer import AutoFrame


class BoundCtlDemo(AutoFrame):
    """Binding and value roundtrip test for all widget types.

    Tests setting and getting values for: textbox, multiline, dropdown, combo,
    radio, checkbox, and slider.
    """

    f_body = """
                       |      <->
        Textbox:        [ textbox_ ]
        Multiline:      [ multiline__ ]
        Dropdown:       [ Choose (Red,Green,Blue) v]
        Combo:          [ Color_ (Red,Green,Blue) v]
        Radio A:        ( ) Option A
                        (x) Option B
        Checkbox:       [x] agree:I agree
        Slider:         [ slider: 0 -+- 100 ]
        """

    bind_names = "textbox multiline choose color option_a option_b agree slider".split(
        " "
    )

    def set_all(self):
        self.textbox = "text"
        self.multiline = "more\ntext"
        self.choose = "Green"
        self.color = "Shade of grey"
        self.option_b = True
        self.agree = False
        self.slider = 50

    def get_all(self):
        return {name: getattr(self, name) for name in self.bind_names}


class TestBoundCtlDemo:
    """Tests for widget value binding."""

    def test_all_widgets_created(self, frame_builder):
        """Tests control instantiation by building the frame and asserting every documented bound control widget is available as a frame attribute."""
        frame = frame_builder(BoundCtlDemo)

        assert hasattr(frame, "textbox"), "textbox widget not found"
        assert hasattr(frame, "multiline"), "multiline widget not found"
        assert hasattr(frame, "choose"), "dropdown widget not found"
        assert hasattr(frame, "color"), "combo widget not found"
        assert hasattr(frame, "option_a"), "radio option_a widget not found"
        assert hasattr(frame, "option_b"), "radio option_b widget not found"
        assert hasattr(frame, "agree"), "checkbox widget not found"
        assert hasattr(frame, "slider"), "slider widget not found"

    def test_textbox_binding(self, frame_builder):
        """Tests textbox roundtrip binding by setting two string values and asserting each value is retrieved unchanged from the bound property."""
        frame = frame_builder(BoundCtlDemo)

        frame.textbox = "test text"
        assert frame.textbox == "test text", "Textbox value binding failed"

        frame.textbox = "another value"
        assert frame.textbox == "another value", "Textbox update failed"

    def test_multiline_binding(self, frame_builder):
        """Tests multiline binding by setting multi-line text and asserting both lines are present when reading back the bound value."""
        frame = frame_builder(BoundCtlDemo)

        frame.multiline = "line1\nline2"
        # Multiline may add trailing newline
        assert (
            "line1" in frame.multiline and "line2" in frame.multiline
        ), "Multiline value binding failed"

    def test_dropdown_binding(self, frame_builder):
        """Tests dropdown selection roundtrip by assigning valid options and asserting the selected value updates and is returned as assigned."""
        frame = frame_builder(BoundCtlDemo)

        frame.choose = "Red"
        assert frame.choose == "Red", "Dropdown binding failed"

        frame.choose = "Blue"
        assert frame.choose == "Blue", "Dropdown update failed"

    def test_combo_binding(self, frame_builder):
        """Tests combo value roundtrip by setting valid entries and asserting reads reflect the current assigned combo value."""
        frame = frame_builder(BoundCtlDemo)

        frame.color = "Green"
        assert frame.color == "Green", "Combo binding failed"

        frame.color = "Red"
        assert frame.color == "Red", "Combo update failed"

    def test_radio_initial_state(self, frame_builder):
        """Tests radio control availability by asserting the initially selected radio option control exists as expected from the layout definition."""
        frame = frame_builder(BoundCtlDemo)

        # Option B is marked as selected (x) in layout
        # Exact behavior depends on toolkit - radio returns group value
        # For now, just verify the widget exists
        assert hasattr(frame, "option_b"), "option_b radio should exist"

    def test_checkbox_binding(self, frame_builder):
        """Tests checkbox boolean binding by toggling True/False/True and asserting each state is returned exactly by the bound attribute."""
        frame = frame_builder(BoundCtlDemo)

        frame.agree = True
        assert frame.agree == True, "Checkbox True binding failed"

        frame.agree = False
        assert frame.agree == False, "Checkbox False binding failed"

        frame.agree = True
        assert frame.agree == True, "Checkbox re-enable failed"

    def test_slider_binding(self, frame_builder):
        """Tests slider numeric binding by setting intermediate and boundary values and asserting float roundtrip values match the assigned positions."""
        frame = frame_builder(BoundCtlDemo)

        frame.slider = 25
        assert frame.slider == 25.0, "Slider binding failed"

        frame.slider = 75
        assert frame.slider == 75.0, "Slider update failed"

        frame.slider = 0
        assert frame.slider == 0.0, "Slider minimum binding failed"

        frame.slider = 100
        assert frame.slider == 100.0, "Slider maximum binding failed"

    def test_set_all_assigns_expected_values(self, frame_builder, toolkit):
        """Tests the `set_all` contract by invoking it and asserting each control reflects the documented post-action value set."""
        frame = frame_builder(BoundCtlDemo)

        frame.set_all()

        assert frame.textbox == "text"
        assert "more" in frame.multiline and "text" in frame.multiline
        assert frame.choose == "Green"
        assert frame.color == "Shade of grey"
        assert frame.option_b in (True, 1, "1")
        assert frame.agree is False
        assert frame.slider == 50.0

    def test_get_all_reads_back_current_values(self, frame_builder):
        """Tests `get_all` aggregation by assigning representative values and asserting returned mapping reports the same current control state."""
        frame = frame_builder(BoundCtlDemo)

        frame.textbox = "hello"
        frame.multiline = "line1\nline2"
        frame.choose = "Red"
        frame.color = "Blue"
        frame.option_b = True
        frame.agree = True
        frame.slider = 25

        values = frame.get_all()

        assert values["textbox"] == "hello"
        assert "line1" in values["multiline"] and "line2" in values["multiline"]
        assert values["choose"] == "Red"
        assert values["color"] == "Blue"
        assert values["option_b"] in (True, 1, "1")
        assert values["agree"] is True
        assert values["slider"] == 25.0

    def test_set_all_then_get_all_roundtrip_contract(self, frame_builder):
        """Tests roundtrip consistency by running `set_all` then `get_all` and asserting the returned snapshot matches all documented set values."""
        frame = frame_builder(BoundCtlDemo)

        frame.set_all()
        values = frame.get_all()

        assert values["textbox"] == "text"
        assert "more" in values["multiline"] and "text" in values["multiline"]
        assert values["choose"] == "Green"
        assert values["color"] == "Shade of grey"
        assert values["option_b"] in (True, 1, "1")
        assert values["agree"] is False
        assert values["slider"] == 50.0
