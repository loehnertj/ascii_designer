# AutoFrame GUI Test Migration - Implementation Summary

**Date:** 29. März 2026  
**Status:** Main migration pass complete + synthetic-interaction enhancement pass complete + P0 and P1 gap-closure pass complete + Qt treelist/model fix applied

## Overview

The manual `test_ascii_designer.py` demos have been migrated into automated pytest modules under `tests/`, with shared backend-parametrized infrastructure in `tests/conftest.py`.

The current setup runs both Tk and Qt paths where supported, keeps Tk-only demos explicit, and currently has no expected-failure markers in the demo-derived modules.

## Current Test Results

Full suite run:

- `141 passed`
- `7 skipped`

Command used:

- `/home/jo/.local/bin/uv run pytest`

Delta vs earlier baseline:

- Former Qt treelist/list-edit `xfail` cases now pass after a `ListBindingQt` initialization/reset-signal robustness fix in `src/ascii_designer/toolkit_qt.py`.

## Implemented Test Modules

One scenario-focused test file now exists for each requested area:

- `tests/test_autoconnect_demo.py`
- `tests/test_boxes_subgrids_demo.py`
- `tests/test_alignment_demo.py`
- `tests/test_bound_ctl_demo.py`
- `tests/test_custom_subclass_demo.py` (Tk-only)
- `tests/test_converters_demo.py` (Tk-only)
- `tests/test_list_demo.py`
- `tests/test_list_edit_demo.py`
- `tests/test_tree_demo.py`
- `tests/test_menu_demo.py`

## Shared Test Infrastructure

`tests/conftest.py` provides:

- toolkit parametrization (`tk`, `qt`) via `set_toolkit`
- frame factory fixture that builds `AutoFrame` instances with toolkit roots
- teardown/cleanup for built frames
- Tk and Qt interaction helper functions
- fixtures for toolkit-scoped tests (`tk_only`, `qt_only`)

## Toolkit Scope Decisions Applied

- Tk-only modules kept Tk-only by fixture gating:
  - `test_custom_subclass_demo.py`
  - `test_converters_demo.py`
- Cross-toolkit modules run on both Tk and Qt where behavior is currently stable.
- Previous Qt treelist/edit instability in test setup was resolved in library code (`ListBindingQt` construction/reset handling).

## Qt Status

Qt is now active in the environment and tests execute under Qt.

### Qt treelist/list-edit status

Resolved in this pass:

- Root cause was a Qt model-reset signal emission timing issue during `ListBindingQt` initialization.
- Fix was applied in `src/ascii_designer/toolkit_qt.py` by making `_set_list()` resilient when reset signals are unavailable during early initialization.
- `xfail` guards for these Qt paths were removed from `tests/test_list_edit_demo.py` and `tests/test_tree_demo.py`.

Current status: Qt paths in those modules are passing.

## Synthetic Interaction Coverage Added

Additional toolkit-native interaction tests were added after the initial migration pass:

- `tests/test_menu_demo.py`
  - Native menu triggering for Tk (`Menu.invoke`) and Qt (`QAction.trigger`) in `test_menu_native_trigger_actions`.
- `tests/test_list_edit_demo.py`
  - Tk synthetic edit flow via binding callback (`on_cell_modified`) in `test_tk_cell_edit_via_binding`.
- `tests/test_tree_demo.py`
  - Tk synthetic tree selection and expand events (`<<TreeviewSelect>>`, `<<TreeviewOpen>>`) in `test_tk_treeview_select_and_expand_events`.

Alignment-specific additions from this pass:

- Existing Qt `QSizePolicy` checks retained and expanded.
- Added Tk layout assertions for stretch weights, spans, explicit left/center/right horizontal alignment, and vertical fill semantics.

## Notes on Plan Alignment

- Copied demo classes into test modules (did not refactor/remove `test_ascii_designer.py`).
- Added one scenario-focused test file per requested behavior area.
- Avoided source-library behavior changes; only test-layer adaptation and known-failure documentation were added.
- Tree tests use mock data in test copy (no real filesystem traversal delays).
- Keep backend interaction strategy explicit: prefer native synthetic events where wiring is under test, and use direct model/signal calls for backend-divergent controls.
- Preserve toolkit scope boundaries: `CustomSubclassDemo` and `ConvertersDemo` remain Tk-only unless production code is generalized.
- Library code changes are now allowed for validated root-cause fixes (as done for Qt `ListBindingQt` initialization/reset handling).
- Continue local-first verification with `uv run pytest`; CI/headless hardening remains a separate follow-up stream.

## Behavior-Assertion Coverage Audit (follow-up)

Follow-up review compared verbal behavior assertions in `test_ascii_designer.py` docstrings/comments against concrete assertions in migrated `tests/test_*_demo.py` modules.

### Confirmed as covered

- Boxes/Subgrids structural assertions are covered (placeholder replacement, nesting, and subgrid control creation).
- Alignment stretch/spanning checks are covered (Qt size-policy expansion plus Tk column weights and rowspan/colspan checks).
- CustomSubclassDemo core behavior is covered (custom entry subclass usage, invalid handling, reset formatting).
- ConvertersDemo success/failure result flows are covered (valid path sets outputs, invalid path reports invalid input).
- MenuDemo action wiring/triggering is covered with toolkit-native triggering paths.
- TreeDemo basic population, child lookup, and `find2` retrieval path are covered.

### Partially covered / missing assertions

- **ListDemo**
  - Many narrative interactions are not yet asserted end-to-end: sorting via headers, add/replace/mutate/remove actions, resort/unsort behavior, reorder-gating semantics, and selection callback semantics.

- **ListEditDemo**
  - Rank recalculation and one Tk binding path are covered, but broader in-place editing/keybinding interaction claims are only partially covered.



### Prioritized gap-closure checklist

#### P0 (high value, low/medium complexity)

- **AutoconnectDemo callback wiring** (`tests/test_autoconnect_demo.py`)
  - [x] `test_choose_routes_to_on_choose_handler`
  - [x] `test_dropdown_empty_routes_to_handler`
  - [x] `test_dynamic_write_here_routes_to_on_write_here_handler`

- **BoundCtlDemo scenario parity for set/get contract** (`tests/test_bound_ctl_demo.py`)
  - [x] `test_set_all_assigns_expected_values`
  - [x] `test_get_all_reads_back_current_values`
  - [x] `test_set_all_then_get_all_roundtrip_contract`

- **ListDemo core action behavior** (`tests/test_list_demo.py`)
  - [x] `test_add_inserts_player_and_restores_sort`
  - [x] `test_replace_updates_selected_players`
  - [x] `test_mutate_updates_selected_players_and_notifies`
  - [x] `test_remove_deletes_selected_players`
  - [x] `test_resort_restores_last_sort_order`
  - [x] `test_unsort_applies_custom_python_sort`

#### P1 (important, medium complexity)

- **Alignment explicit alignment/fill semantics** (`tests/test_alignment_demo.py`)
  - [x] `test_tk_button_horizontal_alignment_left_center_right`
  - [x] `test_tk_controls_fill_vertically`
  - [x] `test_qt_controls_expand_vertically_and_horizontally`

- **TreeDemo behavior claims not yet asserted** (`tests/test_tree_demo.py`)
  - [x] `test_remark_edit_persists_in_remarks_mapping`
  - [x] `test_reexpand_uses_cached_children_without_reload`

- **Menu keyboard/quit contract** (`tests/test_menu_demo.py`)
  - [x] `test_shortcuts_trigger_expected_menu_actions`
  - [x] `test_quit_menu_action_closes_frame`

#### P2 (broader interaction depth, backend-sensitive)

- **ListEdit deeper in-place edit UX** (`tests/test_list_edit_demo.py`)
  - [ ] `test_tk_edit_name_points_and_boolean_cells`
  - [ ] `test_tk_add_and_remove_row_via_widget_controls`
  - [ ] `test_qt_edit_path_documented_or_xfailed_with_reason`

- **ListDemo reorder/selection interaction semantics** (`tests/test_list_demo.py`)
  - [ ] `test_reorder_toggle_updates_allow_reorder_state`
  - [ ] `test_on_shopping_selection_callback_receives_item`

## Remaining Follow-up (optional)

1. Complete P2 assertions (ListEdit deeper edit UX; ListDemo reorder/selection semantics).
2. Increase synthetic-event depth further for additional controls where practical.
3. Add/expand CI headless hardening for cross-toolkit GUI runs.
