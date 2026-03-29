"""Tests for CustomSubclassDemo (Tk-only)."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ascii_designer import AutoFrame


class CustomSubclassDemo(AutoFrame):
    """Demonstrates custom widget subclasses with specialized properties."""

    f_body = """
    |                    |
     Please see the source code to understand what happens here.
     Custom entry field:  [_      ]
     Converted value:     conv_value
                          [reset]
    """

    import tkinter.ttk as ttk

    class MyEntry(ttk.Entry):
        @property
        def float_value(self):
            v = None
            try:
                v = float(self.variable.get())
            except Exception:
                self.state(["invalid"])
            else:
                self.state(["!invalid"])
            return v

        @float_value.setter
        def float_value(self, val):
            self.variable.set(f"{val:0.3f}")
            self.state(["!invalid"])

    def __init__(self):
        super().__init__()
        self.f_toolkit.widget_classes["textbox"] = self.MyEntry

    def on_custom_entry_field(self, text):
        fval = self["custom_entry_field"].float_value
        if fval is None:
            self.label_conv_value = "<invalid>"
        else:
            self.label_conv_value = f"{fval:e}"

    def on_reset(self):
        self["custom_entry_field"].float_value = 1.2345678
        self.on_custom_entry_field(None)


class TestCustomSubclassDemo:
    def test_custom_entry_widget_instance(self, frame_builder, tk_only):
        """Tests custom widget substitution by building the frame and asserting `custom_entry_field` is instantiated as the declared `MyEntry` subclass."""
        frame = frame_builder(CustomSubclassDemo)
        assert isinstance(frame["custom_entry_field"], CustomSubclassDemo.MyEntry)

    def test_invalid_input_sets_invalid_label(self, frame_builder, tk_only):
        """Tests invalid conversion handling by entering non-float text and asserting the converted-value label is set to the factual invalid marker `<invalid>`."""
        frame = frame_builder(CustomSubclassDemo)

        frame["custom_entry_field"].variable.set("not-a-float")
        frame.on_custom_entry_field(None)
        assert frame.label_conv_value == "<invalid>"

    def test_reset_formats_value(self, frame_builder, tk_only):
        """Tests reset formatting behavior by invoking reset and asserting the entry is formatted to three decimals and the converted label reflects that numeric value."""
        frame = frame_builder(CustomSubclassDemo)

        frame.on_reset()
        assert frame["custom_entry_field"].variable.get() == "1.235"
        assert "1.235" in frame.label_conv_value
