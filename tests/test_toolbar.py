#!/usr/bin/env python
"""Tests for `map_widgets` module."""
import dataclasses
import unittest
from unittest import mock

import geemap
from geemap.toolbar import Toolbar, ToolbarItem, _cleanup_toolbar_item
from tests import fake_map


class TestToolbar(unittest.TestCase):
    """Tests for the Toolbar class in the `toolbar` module."""

    def setUp(self):
        super().setUp()
        self.callback_calls = 0
        self.last_called_with_selected = None
        self.last_called_item = None
        self.item = ToolbarItem(
            icon="info", tooltip="dummy item", callback=self.dummy_callback
        )
        self.reset_item = ToolbarItem(
            icon="question",
            tooltip="no reset item",
            callback=self.dummy_callback,
            reset=True,
        )

    def tearDown(self):
        # For fake_map.
        mock.patch.stopall()
        super().tearDown()

    def dummy_callback(self, m, selected, item):
        del m  # Unused.
        self.last_called_with_selected = selected
        self.last_called_item = item
        self.callback_calls += 1

    def test_no_tools_throws(self):
        map = geemap.Map(ee_initialize=False)
        self.assertRaises(ValueError, Toolbar, map, [], [])

    def test_only_main_tools_exist_if_no_extra_tools(self):
        map = geemap.Map(ee_initialize=False)
        toolbar = Toolbar(map, [self.item], [])
        self.assertNotIn(toolbar.toggle_widget, toolbar.main_tools)

    def test_all_tools_and_toggle_exist_if_extra_tools(self):
        map = geemap.Map(ee_initialize=False)
        toolbar = Toolbar(map, [self.item], [self.reset_item])
        self.assertIsNotNone(toolbar.toggle_widget)

    def test_toggle_expands_and_collapses(self):
        map = geemap.Map(ee_initialize=False)
        toolbar = Toolbar(map, [self.item], [self.reset_item])
        self.assertIsNotNone(toolbar.toggle_widget)
        toggle = toolbar.toggle_widget
        self.assertEqual(toggle.icon, "add")
        self.assertEqual(toggle.tooltip_text, "Expand toolbar")
        self.assertFalse(toolbar.expanded)

        # Expand
        toggle.active = True
        self.assertTrue(toolbar.expanded)
        self.assertEqual(toggle.icon, "remove")
        self.assertEqual(toggle.tooltip_text, "Collapse toolbar")
        # After expanding, button is unselected.
        self.assertFalse(toggle.active)

        # Collapse
        toggle.active = True
        self.assertFalse(toolbar.expanded)
        self.assertEqual(toggle.icon, "add")
        self.assertEqual(toggle.tooltip_text, "Expand toolbar")
        # After collapsing, button is unselected.
        self.assertFalse(toggle.active)

    def test_triggers_callbacks(self):
        map = geemap.Map(ee_initialize=False)
        toolbar = Toolbar(map, [self.item, self.reset_item], [])
        self.assertIsNone(self.last_called_with_selected)
        self.assertIsNone(self.last_called_item)

        # Select first tool, which does not reset.
        toolbar.main_tools[0].active = True
        self.assertTrue(self.last_called_with_selected)
        self.assertEqual(self.callback_calls, 1)
        self.assertTrue(toolbar.main_tools[0].active)
        self.assertEqual(self.item, self.last_called_item)

        # Select second tool, which resets.
        toolbar.main_tools[1].active = True
        self.assertFalse(self.last_called_with_selected)  # was reset by callback
        self.assertEqual(self.callback_calls, 3)
        self.assertFalse(toolbar.main_tools[1].active)
        self.assertEqual(self.reset_item, self.last_called_item)

    @dataclasses.dataclass
    class TestWidget:
        selected_count: int = 0
        cleanup_count: int = 0

        def cleanup(self):
            self.cleanup_count += 1

    def test_cleanup_toolbar_item_decorator(self):
        widget = TestToolbar.TestWidget()

        @_cleanup_toolbar_item
        def callback(m, selected, item):
            widget.selected_count += 1
            return widget

        item = ToolbarItem(
            icon="info", tooltip="dummy item", callback=callback, reset=False
        )
        map_fake = fake_map.FakeMap()
        toolbar = Toolbar(map_fake, [item], [])
        toolbar.main_tools[0].active = True
        self.assertEqual(1, widget.selected_count)
        self.assertEqual(0, widget.cleanup_count)

        toolbar.main_tools[0].active = False
        self.assertEqual(1, widget.selected_count)
        self.assertEqual(1, widget.cleanup_count)

        toolbar.main_tools[0].active = True
        self.assertEqual(2, widget.selected_count)
        self.assertEqual(1, widget.cleanup_count)

        widget.cleanup()
        self.assertEqual(2, widget.selected_count)
        self.assertEqual(3, widget.cleanup_count)
        self.assertFalse(toolbar.main_tools[0].active)


if __name__ == "__main__":
    unittest.main()
