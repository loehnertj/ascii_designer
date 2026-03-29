"""Tests for ListEditDemo."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ascii_designer import AutoFrame, ObsListProperty
from ascii_designer.tk_treeedit import TreeEdit


class RankRow:
    def __init__(self, name, points, rank, is_cheater=False):
        self.name = name
        self.points = points
        self.rank = rank
        self.is_cheater = is_cheater


class ListEditDemo(AutoFrame):
    """Demonstrates in-place editing of list items with multiple columns."""

    f_body = """
        | -
        I[= Players (Name_, Points_, Is_Cheater?, Rank)]
    """

    players: ObsListProperty[RankRow]

    def f_build(self, parent, body=None):
        super().f_build(parent, body)
        tv = self["players"]

        if isinstance(tv, TreeEdit):
            tv.allow = "add, remove"
            binding = tv.variable

            def setpoints(obj, val):
                obj.points = int(val)

            def set_ic(obj, val):
                obj.is_cheater = bool(val)

            binding.sources(
                points=("points", setpoints), is_cheater=("is_cheater", set_ic)
            )
        else:
            binding = tv.model()

        binding.factory = lambda: RankRow("", 0, 0)

        self.players = [
            RankRow("CaptainJack", 9010, 1),
            RankRow("MasterOfDisaster", 3010, 2),
            RankRow("LittleDuck", 12, 3),
        ]
        self.players.on_replace += self._check_recalc_ranks_ol
        self._in_check_recalc = False

    def _check_recalc_ranks_ol(self, toolkit_id, item):
        if self._in_check_recalc:
            return
        self._in_check_recalc = True
        try:
            self._check_recalc_ranks()
        finally:
            self._in_check_recalc = False

    def _check_recalc_ranks(self):
        i = 1
        for row in sorted(self.players, key=(lambda row: row.points), reverse=True):
            row.rank = i
            self.players.item_mutated(row)
            i += 1


class TestListEditDemo:
    def test_build_initializes_players(self, frame_builder, toolkit):
        """Tests editable-list initialization by building the frame and asserting the default three player rows are created with expected first entry data."""
        frame = frame_builder(ListEditDemo)

        assert len(frame.players) == 3
        assert frame.players[0].name == "CaptainJack"

    def test_rank_recalculation(self, frame_builder, toolkit):
        """Tests rank autoupdate logic by changing points and asserting recalculated ranks are assigned as 1/2/3 in descending score order."""
        frame = frame_builder(ListEditDemo)

        frame.players[0].points = 10
        frame.players[1].points = 5000
        frame.players[2].points = 200

        frame._check_recalc_ranks()

        sorted_rows = sorted(frame.players, key=lambda r: r.points, reverse=True)
        assert sorted_rows[0].rank == 1
        assert sorted_rows[1].rank == 2
        assert sorted_rows[2].rank == 3

    def test_tk_cell_edit_via_binding(self, frame_builder, toolkit):
        """Tests Tk cell-edit propagation by invoking the bound cell-modified callback and asserting the row points value and resulting top rank update correctly."""
        if toolkit != "tk":
            pytest.skip("Tk-only synthetic tree-edit interaction")

        frame = frame_builder(ListEditDemo)
        tv = frame["players"]
        iid = frame.players.toolkit_ids[0]

        tv.variable.on_cell_modified(iid, "points", "12000")
        assert frame.players[0].points == 12000

        ranked = sorted(frame.players, key=lambda r: r.points, reverse=True)
        assert ranked[0].name == frame.players[0].name
        assert ranked[0].rank == 1
