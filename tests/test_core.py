#!/usr/bin/env python

"""Tests for `map_widgets` module."""
import unittest
from unittest.mock import patch, Mock

import ee
import ipyleaflet
import ipywidgets

from geemap import core, toolbar
from tests import fake_ee, utils


@patch.object(ee, "FeatureCollection", fake_ee.FeatureCollection)
@patch.object(ee, "Geometry", fake_ee.Geometry)
class TestMap(unittest.TestCase):
    """Tests for Map."""

    def _clear_default_widgets(self):
        widgets = [
            "zoom_control",
            "fullscreen_control",
            "scale_control",
            "attribution_control",
            "toolbar",
            "inspector",
            "layer_manager",
        ]
        for widget in widgets:
            self.core_map.remove(widget)

    def setUp(self):
        self.core_map = core.Map(ee_initialize=False)

    def test_defaults(self):
        """Tests that map defaults are set properly."""
        self.assertEqual(self.core_map.width, "100%")
        self.assertEqual(self.core_map.height, "600px")
        self.assertEqual(self.core_map.get_center(), [0, 0])
        self.assertEqual(self.core_map.get_zoom(), 2)

        controls = self.core_map.controls
        self.assertEqual(len(controls), 5)
        self.assertIsInstance(controls[0], ipyleaflet.ZoomControl)
        self.assertIsInstance(controls[1], ipyleaflet.FullScreenControl)
        self.assertIsInstance(controls[2], ipyleaflet.ScaleControl)
        self.assertIsInstance(controls[3].widget, toolbar.Toolbar)
        self.assertIsInstance(controls[4], ipyleaflet.AttributionControl)

    def test_set_center(self):
        """Tests that `set_center` sets the center and zoom."""
        self.core_map.set_center(1, 2, 3)
        self.assertEqual(self.core_map.get_center(), [2, 1])
        self.assertEqual(self.core_map.get_zoom(), 3)
        self.core_map.set_center(5, 6)
        self.assertEqual(self.core_map.get_center(), [6, 5])
        self.assertEqual(self.core_map.get_zoom(), 3)

    def test_scale(self):
        """Tests that `scale` is calculated correctly."""
        self.core_map.set_center(0, 0, 2)
        self.assertAlmostEqual(self.core_map.get_scale(), 39135.76, places=2)
        self.core_map.set_center(-10, 4, 8)
        self.assertAlmostEqual(self.core_map.get_scale(), 610.01, places=2)

    def test_center_object(self):
        """Tests that `center_object` fits the object to the bounds."""
        fit_bounds_mock = Mock()
        self.core_map.fit_bounds = fit_bounds_mock
        self.core_map.center_object(ee.Geometry.Point())
        fit_bounds_mock.assert_called_with([[-76, -178], [80, 179]])

        fit_bounds_mock = Mock()
        self.core_map.fit_bounds = fit_bounds_mock
        self.core_map.center_object(ee.FeatureCollection([]))
        fit_bounds_mock.assert_called_with([[-76, -178], [80, 179]])

        set_center_mock = Mock()
        self.core_map.set_center = set_center_mock
        self.core_map.center_object(ee.Geometry.Point(), 2)
        set_center_mock.assert_called_with(120, -70, 2)

        with self.assertRaisesRegex(Exception, "must be one of"):
            self.core_map.center_object("invalid object")

        with self.assertRaisesRegex(ValueError, "Zoom must be an integer"):
            self.core_map.center_object(ee.Geometry.Point(), "2")

    def test_add_basic_widget_by_name(self):
        """Tests that `add` adds widgets by name."""
        self._clear_default_widgets()

        self.core_map.add("scale_control", position="topleft", metric=False)

        self.assertEqual(len(self.core_map.controls), 1)
        control = self.core_map.controls[0]
        self.assertIsInstance(control, ipyleaflet.ScaleControl)
        self.assertEqual(control.position, "topleft")
        self.assertEqual(control.metric, False)

    def test_add_basic_widget(self):
        """Tests that `add` adds widget instances to the map."""
        self._clear_default_widgets()

        self.core_map.add(ipyleaflet.ScaleControl(position="topleft", metric=False))

        self.assertEqual(len(self.core_map.controls), 1)
        control = self.core_map.controls[0]
        self.assertIsInstance(control, ipyleaflet.ScaleControl)
        self.assertEqual(control.position, "topleft")
        self.assertEqual(control.metric, False)

    def test_add_duplicate_basic_widget(self):
        """Tests adding a duplicate widget to the map."""
        self.assertEqual(len(self.core_map.controls), 5)
        self.assertIsInstance(self.core_map.controls[0], ipyleaflet.ZoomControl)
        self.assertEqual(self.core_map.controls[0].position, "topleft")

        self.core_map.add("zoom_control", position="bottomright")

        self.assertEqual(len(self.core_map.controls), 5)
        self.assertIsInstance(self.core_map.controls[0], ipyleaflet.ZoomControl)
        self.assertEqual(self.core_map.controls[0].position, "topleft")

    def test_add_toolbar(self):
        """Tests adding the toolbar widget."""
        self._clear_default_widgets()

        self.core_map.add("toolbar", position="bottomright")

        self.assertEqual(len(self.core_map.controls), 1)
        toolbar_control = self.core_map.controls[0].widget
        utils.query_widget(
            toolbar_control, ipywidgets.ToggleButton, lambda c: c.tooltip == "Toolbar"
        ).value = True  # Open the grid of tools.
        tool_grid = utils.query_widget(toolbar_control, ipywidgets.GridBox).children
        self.assertEqual(len(tool_grid), 2)
        self.assertEqual(tool_grid[0].tooltip, "Inspector")
        self.assertEqual(tool_grid[1].tooltip, "Get help")
