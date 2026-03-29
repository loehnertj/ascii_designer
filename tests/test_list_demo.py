"""Tests for ListDemo - frame building with list widgets."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ascii_designer import AutoFrame, ObsListProperty, ObsList


class DemoListData:
    """Simple structured list data."""

    def __init__(self, name, count):
        self.name = name
        self.count = count


class ListDemo(AutoFrame):
    """List/tree widget demo.

    Demonstrates list views with simple items and structured data.
    """

    f_body = """
    |             |     |         |        |<->     |        |         |
    |Simple List   List with columns
    I[= Shopping__ ] [= Players  (Name, Count) ~        ~        ]
    """

    # Declare list properties
    shopping: ObsListProperty
    players: ObsListProperty

    def f_on_build(self):
        # Initialize lists
        self.shopping = ObsList(["Apples", "Bananas", "Oranges"])
        self.players = ObsList(
            [
                DemoListData("Alice", 100),
                DemoListData("Bob", 50),
            ]
        )

    def add(self):
        self.players.insert(1, DemoListData("Carol", 75))
        self.players.sort(restore=True)

    def replace(self):
        for item in self.players.selection:
            idx = self.players.index(item)
            self.players[idx] = DemoListData(f"replaced-{item.name}", item.count + 1)

    def mutate(self):
        for item in self.players.selection:
            item.name = f"changed-{item.name}"
            self.players.item_mutated(item)

    def remove(self):
        for item in list(self.players.selection):
            self.players.remove(item)

    def resort(self):
        self.players.sort(restore=True)

    def unsort(self):
        self.players.sort(key=lambda item: id(item))


class TestListDemo:
    """Tests for list/tree widget creation and basic operations."""

    def test_frame_builds_with_lists(self, frame_builder):
        """Tests list-demo construction by building the frame and asserting controls are created, proving list widgets initialize without build errors."""
        frame = frame_builder(ListDemo)

        # Verify the widgets were created
        assert hasattr(frame, "f_controls"), "Frame controls should exist"
        assert len(frame.f_controls) > 0, "Frame should have some controls"

    def test_list_properties_initialized(self, frame_builder):
        """Tests bound list-property initialization by asserting `shopping` and `players` exist and are concrete `ObsList` instances after build."""
        frame = frame_builder(ListDemo)

        # Verify properties were set
        assert hasattr(frame, "shopping"), "shopping property not found"
        assert hasattr(frame, "players"), "players property not found"

        # Verify we can access the lists themselves
        assert isinstance(frame.shopping, ObsList), "shopping should be an ObsList"
        assert isinstance(frame.players, ObsList), "players should be an ObsList"

    def test_shopping_list_initial_contents(self, frame_builder):
        """Tests initial shopping data population by asserting the list contains the expected three starter items in declared order."""
        frame = frame_builder(ListDemo)

        assert len(frame.shopping) == 3, "Shopping list should have 3 items"
        assert frame.shopping[0] == "Apples", "First item should be Apples"
        assert frame.shopping[1] == "Bananas", "Second item should be Bananas"

    def test_players_list_initial_contents(self, frame_builder):
        """Tests initial structured player data by asserting two player rows are present and named Alice then Bob."""
        frame = frame_builder(ListDemo)

        assert len(frame.players) == 2, "Players list should have 2 items"
        assert frame.players[0].name == "Alice", "First player should be Alice"
        assert frame.players[1].name == "Bob", "Second player should be Bob"

    def test_list_modifications(self, frame_builder):
        """Tests mutable list behavior by appending, replacing, and removing shopping items and asserting the list content and length update accordingly."""
        frame = frame_builder(ListDemo)

        # Test adding to shopping list
        frame.shopping.append("Grapes")
        assert (
            len(frame.shopping) == 4
        ), "Shopping list should have 4 items after append"
        assert frame.shopping[-1] == "Grapes", "Last item should be Grapes"

        # Test replacing
        frame.shopping[0] = "Pears"
        assert frame.shopping[0] == "Pears", "First item should now be Pears"

        # Test removing
        frame.shopping.pop()
        assert len(frame.shopping) == 3, "Shopping list should have 3 items after pop"

    def test_add_inserts_player_and_restores_sort(self, frame_builder):
        """Tests add+restore behavior by defining a prior sort, inserting a player, and asserting list order remains sorted according to stored sort settings."""
        frame = frame_builder(ListDemo)

        frame.players.sort(
            key=lambda item: item.count, reverse=True, info={"by": "count"}
        )
        frame.add()

        assert len(frame.players) == 3
        counts = [item.count for item in frame.players]
        assert counts == sorted(counts, reverse=True)

    def test_replace_updates_selected_players(self, frame_builder):
        """Tests replacement behavior by selecting one player via selection provider, invoking `replace`, and asserting the selected row is replaced with expected data."""
        frame = frame_builder(ListDemo)
        selected = frame.players[0]
        frame.players.on_get_selection = lambda: [selected]

        frame.replace()

        assert frame.players[0].name.startswith("replaced-")
        assert frame.players[0].count == selected.count + 1

    def test_mutate_updates_selected_players_and_notifies(self, frame_builder):
        """Tests mutation behavior by selecting a player, mutating through `mutate`, and asserting name change plus a replace/mutate notification callback is emitted."""
        frame = frame_builder(ListDemo)
        selected = frame.players[0]
        frame.players.on_get_selection = lambda: [selected]
        seen = []
        frame.players.on_replace += lambda toolkit_id, item: seen.append(item)

        frame.mutate()

        assert selected.name.startswith("changed-")
        assert seen and seen[-1] is selected

    def test_remove_deletes_selected_players(self, frame_builder):
        """Tests removal behavior by selecting one player, invoking `remove`, and asserting list length decreases and the selected item is gone."""
        frame = frame_builder(ListDemo)
        selected = frame.players[0]
        frame.players.on_get_selection = lambda: [selected]

        frame.remove()

        assert len(frame.players) == 1
        assert selected not in frame.players

    def test_resort_restores_last_sort_order(self, frame_builder):
        """Tests resort behavior by storing a sort order, perturbing data, invoking `resort`, and asserting ordering returns to the remembered sort criterion."""
        frame = frame_builder(ListDemo)

        frame.players.sort(
            key=lambda item: item.count, reverse=True, info={"by": "count"}
        )
        frame.players.append(DemoListData("Zed", 999))

        frame.resort()

        counts = [item.count for item in frame.players]
        assert counts == sorted(counts, reverse=True)

    def test_unsort_applies_custom_python_sort(self, frame_builder):
        """Tests unsort behavior by invoking `unsort` and asserting resulting player order matches ascending object-id sort."""
        frame = frame_builder(ListDemo)

        frame.unsort()

        ids = [id(item) for item in frame.players]
        assert ids == sorted(ids)
