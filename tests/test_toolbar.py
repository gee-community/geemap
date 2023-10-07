#!/usr/bin/env python

"""Tests for `map_widgets` module."""

import unittest

from dataclasses import dataclass
from unittest.mock import patch, Mock

import ipywidgets

import geemap
from geemap.toolbar import Toolbar, _cleanup_toolbar_item
from tests import fake_map, utils


class TestToolbar(unittest.TestCase):
    """Tests for the Toolbar class in the `toolbar` module."""

    def _query_layers_button(self, toolbar):
        return utils.query_widget(
            toolbar, ipywidgets.ToggleButton, lambda c: c.tooltip == "Layers"
        )

    def _query_open_button(self, toolbar):
        return utils.query_widget(
            toolbar, ipywidgets.ToggleButton, lambda c: c.tooltip == "Toolbar"
        )

    def _query_tool_grid(self, toolbar):
        return utils.query_widget(toolbar, ipywidgets.GridBox, lambda c: True)

    def setUp(self) -> None:
        self.callback_calls = 0
        self.last_called_with_selected = None
        self.last_called_item = None
        self.item = Toolbar.Item(
            icon="info", tooltip="dummy item", callback=self.dummy_callback
        )
        self.no_reset_item = Toolbar.Item(
            icon="question",
            tooltip="no reset item",
            callback=self.dummy_callback,
            reset=False,
        )
        return super().setUp()

    def tearDown(self) -> None:
        patch.stopall()
        return super().tearDown()

    def dummy_callback(self, m, selected, item):
        del m
        self.last_called_with_selected = selected
        self.last_called_item = item
        self.callback_calls += 1

    def test_no_tools_throws(self):
        map = geemap.Map(ee_initialize=False)
        self.assertRaises(ValueError, Toolbar, map, [], [])

    def test_only_main_tools_exist_if_no_extra_tools(self):
        map = geemap.Map(ee_initialize=False)
        toolbar = Toolbar(map, [self.item], [])
        self.assertIsNone(toolbar.toggle_widget)
        self.assertEqual(len(toolbar.all_widgets), 1)
        self.assertEqual(toolbar.all_widgets[0].icon, "info")
        self.assertEqual(toolbar.all_widgets[0].tooltip, "dummy item")
        self.assertFalse(toolbar.all_widgets[0].value)
        self.assertEqual(toolbar.num_rows_collapsed, 1)
        self.assertEqual(toolbar.num_rows_expanded, 1)

    def test_all_tools_and_toggle_exist_if_extra_tools(self):
        map = geemap.Map(ee_initialize=False)
        toolbar = Toolbar(map, [self.item], [self.no_reset_item])
        self.assertIsNotNone(toolbar.toggle_widget)
        self.assertEqual(len(toolbar.all_widgets), 3)
        self.assertEqual(toolbar.all_widgets[2].icon, "question")
        self.assertEqual(toolbar.all_widgets[2].tooltip, "no reset item")
        self.assertFalse(toolbar.all_widgets[2].value)
        self.assertEqual(toolbar.num_rows_collapsed, 1)
        self.assertEqual(toolbar.num_rows_expanded, 1)

    def test_has_correct_number_of_rows(self):
        map = geemap.Map(ee_initialize=False)
        toolbar = Toolbar(map, [self.item, self.item], [self.item, self.item])
        self.assertEqual(toolbar.num_rows_collapsed, 1)
        self.assertEqual(toolbar.num_rows_expanded, 2)

    def test_toggle_expands_and_collapses(self):
        map = geemap.Map(ee_initialize=False)
        toolbar = Toolbar(map, [self.item], [self.no_reset_item])
        self.assertEqual(len(toolbar.grid.children), 2)
        self.assertIsNotNone(toolbar.toggle_widget)
        toggle = toolbar.all_widgets[1]
        self.assertEqual(toggle.icon, "plus")
        self.assertEqual(toggle.tooltip, "Expand toolbar")

        # Expand
        toggle.value = True
        self.assertEqual(len(toolbar.grid.children), 3)
        self.assertEqual(toggle.icon, "minus")
        self.assertEqual(toggle.tooltip, "Collapse toolbar")
        # After expanding, button is unselected.
        self.assertFalse(toggle.value)

        # Collapse
        toggle.value = True
        self.assertEqual(len(toolbar.grid.children), 2)
        self.assertEqual(toggle.icon, "plus")
        self.assertEqual(toggle.tooltip, "Expand toolbar")
        # After collapsing, button is unselected.
        self.assertFalse(toggle.value)

    def test_triggers_callbacks(self):
        map = geemap.Map(ee_initialize=False)
        toolbar = Toolbar(map, [self.item, self.no_reset_item])
        self.assertIsNone(self.last_called_with_selected)
        self.assertIsNone(self.last_called_item)

        # Select first tool, which resets.
        toolbar.all_widgets[0].value = True
        self.assertFalse(self.last_called_with_selected)  # was reset by callback
        self.assertEqual(self.callback_calls, 2)
        self.assertFalse(toolbar.all_widgets[0].value)
        self.assertEqual(self.item, self.last_called_item)

        # Select second tool, which does not reset.
        toolbar.all_widgets[1].value = True
        self.assertTrue(self.last_called_with_selected)
        self.assertEqual(self.callback_calls, 3)
        self.assertTrue(toolbar.all_widgets[1].value)
        self.assertEqual(self.no_reset_item, self.last_called_item)

    def test_layers_toggle_callback(self):
        """Verifies the on_layers_toggled callback is triggered."""
        map_fake = fake_map.FakeMap()
        toolbar = Toolbar(map_fake, [self.item, self.no_reset_item])
        self._query_open_button(toolbar).value = True

        self.assertIsNotNone(layers_button := self._query_layers_button(toolbar))
        on_toggled_mock = Mock()
        toolbar.on_layers_toggled = on_toggled_mock
        layers_button.value = True

        on_toggled_mock.assert_called_once()

    def test_accessory_widget(self):
        """Verifies the accessory widget replaces the tool grid."""
        map_fake = fake_map.FakeMap()
        toolbar = Toolbar(map_fake, [self.item, self.no_reset_item])
        self._query_open_button(toolbar).value = True
        self.assertIsNotNone(self._query_tool_grid(toolbar))

        toolbar.accessory_widget = ipywidgets.ToggleButton(tooltip="test-button")

        self.assertIsNone(self._query_tool_grid(toolbar))
        self.assertIsNotNone(
            utils.query_widget(
                toolbar, ipywidgets.ToggleButton, lambda c: c.tooltip == "test-button"
            )
        )

    @dataclass
    class TestWidget:
        selected_count = 0
        cleanup_count = 0

        def cleanup(self):
            self.cleanup_count += 1

    def test_cleanup_toolbar_item_decorator(self):
        widget = TestToolbar.TestWidget()

        @_cleanup_toolbar_item
        def callback(m, selected, item):
            widget.selected_count += 1
            return widget

        item = Toolbar.Item(
            icon="info", tooltip="dummy item", callback=callback, reset=False
        )
        map_fake = fake_map.FakeMap()
        toolbar = Toolbar(map_fake, [item])
        toolbar.all_widgets[0].value = True
        self.assertEqual(1, widget.selected_count)
        self.assertEqual(0, widget.cleanup_count)

        toolbar.all_widgets[0].value = False
        self.assertEqual(1, widget.selected_count)
        self.assertEqual(1, widget.cleanup_count)

        toolbar.all_widgets[0].value = True
        self.assertEqual(2, widget.selected_count)
        self.assertEqual(1, widget.cleanup_count)

        widget.cleanup()
        self.assertEqual(2, widget.selected_count)
        self.assertEqual(3, widget.cleanup_count)
        self.assertFalse(toolbar.all_widgets[0].value)
