"""Tests for BoxesDemo and SubgridsDemo."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ascii_designer import AutoFrame


class BoxesDemo(AutoFrame):
    """Demonstrates boxes, group boxes, and widget embedding."""

    f_body = """
        |               |  <->
         Use the source code to understand what is demonstrated here.
         Box:            <box>
        IGroup box:      <groupbox: Test >
        INesting:        <nest_box:Turtles all the way down>
    """

    def __init__(self, level=2):
        super().__init__()
        self._level = level

    def f_on_build(self):
        box_parent = (
            self.box.master if hasattr(self.box, "master") else self.box.parent()
        )
        group_parent = (
            self.groupbox.master
            if hasattr(self.groupbox, "master")
            else self.groupbox.parent()
        )

        self.box = self.f_toolkit.button(parent=box_parent, text="this replaces box")
        self.groupbox = self.f_toolkit.button(
            parent=group_parent, text="this fills groupbox"
        )

        if self._level:
            self.nest_box = BoxesDemo(self._level - 1)


class SubgridsDemo(AutoFrame):
    """Demonstrates nested sub-layouts with subgrids."""

    f_body = """
        |  -
         <normal_frame          >
        I<gb_frame:In groupbox  >

        :normal_frame:
        |  -
         [Top button   ]
         [Bottom button]

        :gb_frame:
        |      -      |
         [Left Button] [Right Button]
        I<s: V Fill  >
    """


class TestBoxesDemo:
    def test_placeholder_replacement_and_nesting(self, frame_builder):
        """Tests placeholder replacement and recursive embedding by building the frame and asserting box placeholders are replaced, nesting control exists, and `nest_box` is a `BoxesDemo` with decremented level."""
        frame = frame_builder(BoxesDemo, level=1)

        assert "box" in frame.f_controls
        assert "groupbox" in frame.f_controls
        assert "nest_box" in frame.f_controls
        assert isinstance(frame.nest_box, BoxesDemo)
        assert frame.nest_box._level == 0


class TestSubgridsDemo:
    def test_subgrids_build_into_placeholders(self, frame_builder):
        """Tests subgrid expansion by building the frame and asserting placeholder hosts and all subgrid-defined button controls are present in `f_controls`."""
        frame = frame_builder(SubgridsDemo)

        assert "normal_frame" in frame.f_controls
        assert "gb_frame" in frame.f_controls
        assert "s" in frame.f_controls

        # Subgrid buttons are created as controls from subgrid sections.
        assert "top_button" in frame.f_controls
        assert "bottom_button" in frame.f_controls
        assert "left_button" in frame.f_controls
        assert "right_button" in frame.f_controls
