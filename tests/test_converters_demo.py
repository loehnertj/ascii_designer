"""Tests for ConvertersDemo (Tk-only)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ascii_designer import AutoFrame, nullable, ge0, Invalid


class ConvertersDemo(AutoFrame):
    """Demonstrates value conversion and validation for different data types."""

    f_option_tk_autovalidate = True
    f_body = """
                 |
         Float:   [ _           ]
         Int:     [ _           ]
         in-list: [_ (a, b, c) v]
         instant: [ _           ]
                  [test]
                  result
         output1: [ _           ]
         output2: [ _           ]
    """

    def f_on_build(self):
        self.label_result = ""
        self["float"].variable.convert = nullable(float)
        self["int"].variable.convert = ge0(int)

        def isinlist(val):
            if val not in ["a", "b", "c", "d"]:
                raise ValueError()
            return val

        self["inlist"].variable.convert = isinlist
        self["instant"].variable.convert = float
        self["output1"].variable.convert_set = lambda x: f"{x:0.1e}"
        self["output2"].variable.convert_set = lambda x: f"{x:3.3f}"

    def on_instant(self, val):
        pass

    def test(self):
        a = self.float
        b = self.int
        c = self.inlist
        d = self.instant
        if Invalid in [a, b, c, d]:
            self.label_result = "some input is invalid"
        else:
            self.label_result = "setting outputs"
            self.output1 = a if a is not None else 99.0
            self.output2 = a if a is not None else 99.0


class TestConvertersDemo:
    def test_valid_values_produce_outputs(self, frame_builder, tk_only):
        """Tests converter success flow by assigning valid float/int/in-list/instant inputs and asserting validation succeeds with formatted outputs populated."""
        frame = frame_builder(ConvertersDemo)

        frame.float = "12.5"
        frame.int = "3"
        frame.inlist = "a"
        frame.instant = "7.0"

        frame.test()
        assert frame.label_result == "setting outputs"
        assert "e" in frame.output1
        assert frame.output2.startswith("12.5")

    def test_invalid_values_mark_result_invalid(self, frame_builder, tk_only):
        """Tests converter failure flow by assigning invalid inputs and asserting the result label reports that some input is invalid."""
        frame = frame_builder(ConvertersDemo)

        frame.float = "12.5"
        frame.int = "-1"
        frame.inlist = "z"
        frame.instant = "oops"

        frame.test()
        assert frame.label_result == "some input is invalid"
