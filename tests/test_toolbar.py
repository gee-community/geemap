#!/usr/bin/env python
"""Tests for `map_widgets` module."""
import dataclasses
import unittest

import geemap
from geemap import toolbar


class TestToolbar(unittest.TestCase):
    """Tests for the Toolbar class in the `toolbar` module."""

    callback_calls: int
    last_called_with_selected: bool
    last_called_item: toolbar.ToolbarItem
    item: toolbar.ToolbarItem
    reset_item: toolbar.ToolbarItem

    def setUp(self):
        super().setUp()
        self.callback_calls = 0
        self.last_called_with_selected = None
        self.last_called_item = None
        self.item = toolbar.ToolbarItem(
            icon="info", tooltip="dummy item", callback=self.dummy_callback
        )
        self.reset_item = toolbar.ToolbarItem(
            icon="question",
            tooltip="no reset item",
            callback=self.dummy_callback,
            reset=True,
        )

    def dummy_callback(self, m, selected, item):
        del m  # Unused.
        self.last_called_with_selected = selected
        self.last_called_item = item
        self.callback_calls += 1

    def test_no_tools_throws(self):
        a_map = geemap.Map(ee_initialize=False)
        self.assertRaises(ValueError, toolbar.Toolbar, a_map, [], [])

    def test_only_main_tools_exist_if_no_extra_tools(self):
        a_map = geemap.Map(ee_initialize=False)
        a_toolboor = toolbar.Toolbar(a_map, [self.item], [])
        self.assertNotIn(a_toolboor.toggle_widget, a_toolboor.main_tools)

    def test_all_tools_and_toggle_exist_if_extra_tools(self):
        a_map = geemap.Map(ee_initialize=False)
        a_toolboor = toolbar.Toolbar(a_map, [self.item], [self.reset_item])
        self.assertIsNotNone(a_toolboor.toggle_widget)

    def test_toggle_expands_and_collapses(self):
        """Toggle widget correctly expands and collapses the toolbar."""
        a_map = geemap.Map(ee_initialize=False)
        a_toolboor = toolbar.Toolbar(a_map, [self.item], [self.reset_item])
        self.assertIsNotNone(a_toolboor.toggle_widget)
        toggle = a_toolboor.toggle_widget
        self.assertEqual(toggle.icon, "add")
        self.assertEqual(toggle.tooltip_text, "Expand toolbar")
        self.assertFalse(a_toolboor.expanded)

        # Expand
        toggle.active = True
        self.assertTrue(a_toolboor.expanded)
        self.assertEqual(toggle.icon, "remove")
        self.assertEqual(toggle.tooltip_text, "Collapse toolbar")
        # After expanding, button is unselected.
        self.assertFalse(toggle.active)

        # Collapse
        toggle.active = True
        self.assertFalse(a_toolboor.expanded)
        self.assertEqual(toggle.icon, "add")
        self.assertEqual(toggle.tooltip_text, "Expand toolbar")
        # After collapsing, button is unselected.
        self.assertFalse(toggle.active)

    def test_triggers_callbacks(self):
        """Tests that toolbar item callbacks are triggered correctly."""
        a_map = geemap.Map(ee_initialize=False)
        a_toolboor = toolbar.Toolbar(a_map, [self.item, self.reset_item], [])
        self.assertIsNone(self.last_called_with_selected)
        self.assertIsNone(self.last_called_item)

        # Select first tool, which does not reset.
        a_toolboor.main_tools[0].active = True
        self.assertTrue(self.last_called_with_selected)
        self.assertEqual(self.callback_calls, 1)
        self.assertTrue(a_toolboor.main_tools[0].active)
        self.assertEqual(self.item, self.last_called_item)

        # Select second tool, which resets.
        a_toolboor.main_tools[1].active = True
        # Was reset by callback.
        self.assertFalse(self.last_called_with_selected)
        self.assertEqual(self.callback_calls, 3)
        self.assertFalse(a_toolboor.main_tools[1].active)
        self.assertEqual(self.reset_item, self.last_called_item)

    @dataclasses.dataclass
    class TestWidget:
        selected_count: int = 0
        cleanup_count: int = 0

        def cleanup(self):
            self.cleanup_count += 1

    def test_cleanup_toolbar_item_decorator(self):
        """Tests the _cleanup_toolbar_item decorator functionality."""
        widget = TestToolbar.TestWidget()

        # pylint: disable-next=protected-access
        @toolbar._cleanup_toolbar_item
        def callback(m, selected, item):
            del m, selected, item  # Unused.
            widget.selected_count += 1
            return widget

        item = toolbar.ToolbarItem(
            icon="info", tooltip="dummy item", callback=callback, reset=False
        )
        a_map = geemap.Map(ee_initialize=False)
        a_toolboor = toolbar.Toolbar(a_map, [item], [])
        a_toolboor.main_tools[0].active = True
        self.assertEqual(1, widget.selected_count)
        self.assertEqual(0, widget.cleanup_count)

        a_toolboor.main_tools[0].active = False
        self.assertEqual(1, widget.selected_count)
        self.assertEqual(1, widget.cleanup_count)

        a_toolboor.main_tools[0].active = True
        self.assertEqual(2, widget.selected_count)
        self.assertEqual(1, widget.cleanup_count)

        widget.cleanup()
        self.assertEqual(2, widget.selected_count)
        self.assertEqual(3, widget.cleanup_count)
        self.assertFalse(a_toolboor.main_tools[0].active)


if __name__ == "__main__":
    unittest.main()
