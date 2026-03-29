"""Tests for TreeDemo with mock tree data."""

import pytest
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ascii_designer import AutoFrame, ObsListProperty


@dataclass
class Node:
    name: str
    children: list["Node"] = field(default_factory=list)


class TreeDemo(AutoFrame):
    """Demonstrates tree views with lazy-loading data."""

    f_body = """
    |  <-> Tree
     Tree~
    I[= Files:File (Remark_) ]
     [ Test Find ]
    """
    files: ObsListProperty[Node]

    def __init__(self):
        super().__init__()
        self.remarks: dict[str, str] = {}
        self.last_focus = None
        self.last_selection = []
        self.children_calls = 0

    def _populate_folder(self):
        leaf_a = Node("leaf-a")
        leaf_b = Node("leaf-b")
        folder_a = Node("folder-a", [leaf_a])
        folder_b = Node("folder-b", [leaf_b])

        def children_of(node):
            self.children_calls += 1
            return node.children

        def has_children(node):
            return bool(node.children)

        self.files.children_source(children_of, has_children_source=has_children)

        def setremark(node: Node, text: str):
            self.remarks[node.name] = text

        self.files.sources(
            remark=(lambda node: self.remarks.get(node.name, ""), setremark)
        )
        self.files = [folder_a, folder_b]

    def on_files(self, item):
        self.last_focus = item
        self.last_selection = list(self.files.selection)


class TestTreeDemo:
    def test_tree_initial_population(self, frame_builder, toolkit):
        """Tests initial tree population by loading mock root nodes and asserting two top-level folders are created with expected names."""
        frame = frame_builder(TreeDemo)
        frame._populate_folder()

        assert len(frame.files) == 2
        assert frame.files[0].name == "folder-a"
        assert frame.files[1].name == "folder-b"

    def test_lazy_load_children_and_find2(self, frame_builder, toolkit):
        """Tests lazy child access and lookup by retrieving children for the first node and asserting `find2` resolves that child to index `(0, 0)`."""
        frame = frame_builder(TreeDemo)
        frame._populate_folder()

        children = frame.files.get_children((0,))
        assert len(children) == 1
        assert children[0].name == "leaf-a"

        idx = frame.files.find2(children[0])
        assert idx == (0, 0)

    def test_tk_treeview_select_and_expand_events(self, frame_builder, toolkit):
        """Tests Tk synthetic tree events by firing selection/open events and asserting focus/selection callbacks update and expansion exposes one loaded child."""
        if toolkit != "tk":
            pytest.skip("Tk-only synthetic treeview event test")

        frame = frame_builder(TreeDemo)
        frame._populate_folder()

        tv = frame["files"]
        first_iid = frame.files.toolkit_ids[0]

        tv.focus(first_iid)
        tv.selection_set((first_iid,))
        tv.event_generate("<<TreeviewSelect>>")
        tv.update()

        assert frame.last_focus is frame.files[0]
        assert frame.files[0] in frame.last_selection

        tv.focus(first_iid)
        tv.event_generate("<<TreeviewOpen>>")
        tv.update()

        loaded = frame.files.get_children((0,))
        assert len(loaded) == 1

    def test_remark_edit_persists_in_remarks_mapping(self, frame_builder, toolkit):
        """Tests remark persistence by storing a remark through the list-binding source and asserting the frame's remarks mapping and retrieval source reflect the new text."""
        frame = frame_builder(TreeDemo)
        frame._populate_folder()

        node = frame.files[0]
        frame.files.binding.store(node, "note-1", "remark")

        assert frame.remarks[node.name] == "note-1"
        assert frame.files.binding.retrieve(node, "remark") == "note-1"

    def test_reexpand_uses_cached_children_without_reload(self, frame_builder, toolkit):
        """Tests tree child caching by loading the same node's children twice and asserting the second access reuses cached children without another source call."""
        frame = frame_builder(TreeDemo)
        frame._populate_folder()

        assert frame.children_calls == 0
        children_first = frame.files.get_children((0,))
        calls_after_first = frame.children_calls
        children_second = frame.files.get_children((0,))

        assert calls_after_first == 1
        assert frame.children_calls == calls_after_first
        assert children_first is children_second
