"""Tests for AlignmentDemo."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ascii_designer import AutoFrame


class AlignmentDemo(AutoFrame):
    """Demonstrates row/column stretching and widget alignment."""

    f_body = """
    |              |     <->          |   <-->         |
     [fixed col   ] [  stretch 1x    ] [stretch 2x    ]
                    [ colspan stretch 3x              ]
    I               [ stretch h+v __ ]|[left]          |
    I               {[left, v 2x __ ] |  [center]      |
    I               {                           [right]|
    """

    def f_on_build(self):
        if self.f_toolkit.__class__.__name__.lower().endswith("qt"):
            from qtpy.QtWidgets import QSizePolicy

            self["center"].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self["right"].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


class TestAlignmentDemo:
    def test_alignment_widgets_exist(self, frame_builder):
        """Tests control creation for alignment buttons by building the frame and asserting `left`, `center`, and `right` controls are all created."""
        frame = frame_builder(AlignmentDemo)

        assert "left" in frame.f_controls
        assert "center" in frame.f_controls
        assert "right" in frame.f_controls

    def test_qt_size_policy_is_expanding(self, frame_builder, toolkit):
        """Tests Qt stretch behavior by asserting `center` and `right` widgets use `QSizePolicy.Expanding` in both directions after build."""
        if toolkit != "qt":
            return

        from qtpy.QtWidgets import QSizePolicy

        frame = frame_builder(AlignmentDemo)
        center_policy = frame["center"].sizePolicy()
        right_policy = frame["right"].sizePolicy()

        assert center_policy.horizontalPolicy() == QSizePolicy.Expanding
        assert center_policy.verticalPolicy() == QSizePolicy.Expanding
        assert right_policy.horizontalPolicy() == QSizePolicy.Expanding
        assert right_policy.verticalPolicy() == QSizePolicy.Expanding

    def test_tk_grid_stretch_and_spans(self, frame_builder, toolkit):
        """Tests Tk layout semantics by asserting configured column stretch weights are non-stretch/1x/2x and that the documented colspan and rowspan are at least 2."""
        if toolkit != "tk":
            return

        frame = frame_builder(AlignmentDemo)
        root = frame[""]

        col_weights = [root.grid_columnconfigure(i).get("weight", 0) for i in range(3)]
        assert col_weights[0] == 0
        assert col_weights[1] >= 1
        assert col_weights[2] >= 2

        stretch_hv_info = frame["colspan_stretch_3x"].grid_info()
        left_v_info = frame["left_v_2x"].grid_info()
        assert int(stretch_hv_info.get("columnspan", 1)) >= 2
        assert int(left_v_info.get("rowspan", 1)) >= 2

    def test_tk_button_horizontal_alignment_left_center_right(
        self, frame_builder, toolkit
    ):
        """Tests documented horizontal alignment by asserting Tk grid sticky settings place `left` west, `center` centered (no west/east), and `right` east."""
        if toolkit != "tk":
            return

        frame = frame_builder(AlignmentDemo)
        left_sticky = frame["left"].grid_info().get("sticky", "")
        center_sticky = frame["center"].grid_info().get("sticky", "")
        right_sticky = frame["right"].grid_info().get("sticky", "")

        assert "w" in left_sticky and "e" not in left_sticky
        assert "w" not in center_sticky and "e" not in center_sticky
        assert "e" in right_sticky and "w" not in right_sticky

    def test_tk_controls_fill_vertically(self, frame_builder, toolkit):
        """Tests vertical fill semantics by asserting representative Tk controls include both north and south sticky flags so they expand to cell height."""
        if toolkit != "tk":
            return

        frame = frame_builder(AlignmentDemo)
        for ctl in ["left", "center", "right", "fixed_col", "stretch_1x", "stretch_2x"]:
            sticky = frame[ctl].grid_info().get("sticky", "")
            assert "n" in sticky and "s" in sticky

    def test_qt_controls_expand_vertically_and_horizontally(
        self, frame_builder, toolkit
    ):
        """Tests Qt expansion semantics by asserting the controls explicitly configured in the demo (`center`, `right`) are expanding in both dimensions."""
        if toolkit != "qt":
            return

        from qtpy.QtWidgets import QSizePolicy

        frame = frame_builder(AlignmentDemo)
        for ctl in ["center", "right"]:
            policy = frame[ctl].sizePolicy()
            assert policy.horizontalPolicy() == QSizePolicy.Expanding
            assert policy.verticalPolicy() == QSizePolicy.Expanding
