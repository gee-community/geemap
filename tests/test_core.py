#!/usr/bin/env python

"""Tests for `map_widgets` module."""
import unittest
from unittest.mock import patch, Mock

import ee
import ipyleaflet
import ipywidgets

from geemap import core, map_widgets, toolbar
from tests import fake_ee, fake_map, utils


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
            "draw_control",
        ]
        for widget in widgets:
            self.core_map.remove(widget)

    def setUp(self):
        self.core_map = core.Map(ee_initialize=False, width="100%")

    def test_defaults(self):
        """Tests that map defaults are set properly."""
        self.assertEqual(self.core_map.width, "100%")
        self.assertEqual(self.core_map.height, "600px")
        self.assertEqual(self.core_map.get_center(), [0, 0])
        self.assertEqual(self.core_map.get_zoom(), 2)

        controls = self.core_map.controls
        self.assertEqual(len(controls), 6)
        self.assertIsInstance(controls[0], ipyleaflet.ZoomControl)
        self.assertIsInstance(controls[1], ipyleaflet.FullScreenControl)
        self.assertIsInstance(controls[2], core.MapDrawControl)
        self.assertIsInstance(controls[3], ipyleaflet.ScaleControl)
        self.assertIsInstance(controls[4].widget, toolbar.Toolbar)
        self.assertIsInstance(controls[5], ipyleaflet.AttributionControl)

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

    @unittest.mock.patch.object(core.Map, "bounds")
    def test_get_bounds(self, mock_bounds):
        """Tests that `get_bounds` returns the bounds of the map."""
        mock_bounds.__get__ = Mock(return_value=[[1, 2], [3, 4]])
        self.assertEqual(self.core_map.get_bounds(), [2, 1, 4, 3])
        self.assertEqual(self.core_map.getBounds(), [2, 1, 4, 3])
        expected_geo_json = {
            "geodesic": False,
            "type": "Polygon",
            "coordinates": [[0, 1], [1, 2], [0, 1]],
        }
        self.assertEqual(self.core_map.get_bounds(as_geojson=True), expected_geo_json)

        mock_bounds.__get__ = Mock(return_value=())
        with self.assertRaisesRegex(RuntimeError, "Map bounds are undefined"):
            self.core_map.get_bounds(as_geojson=True)

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
        self.assertEqual(len(self.core_map.controls), 6)
        self.assertIsInstance(self.core_map.controls[0], ipyleaflet.ZoomControl)
        self.assertEqual(self.core_map.controls[0].position, "topleft")

        self.core_map.add("zoom_control", position="bottomright")

        self.assertEqual(len(self.core_map.controls), 6)
        self.assertIsInstance(self.core_map.controls[0], ipyleaflet.ZoomControl)
        self.assertEqual(self.core_map.controls[0].position, "topleft")

    def test_add_toolbar(self):
        """Tests adding the toolbar widget."""
        self._clear_default_widgets()

        self.core_map.add("toolbar", position="bottomright")

        self.assertEqual(len(self.core_map.controls), 1)
        toolbar_control = self.core_map.controls[0].widget
        # Layer manager is selected and open by default.
        layer_button = utils.query_widget(
            toolbar_control, ipywidgets.ToggleButton, lambda c: c.tooltip == "Layers"
        )
        self.assertTrue(layer_button.value)
        self.assertIsNotNone(
            utils.query_widget(toolbar_control, map_widgets.LayerManager)
        )

        toolbar_button = utils.query_widget(
            toolbar_control, ipywidgets.ToggleButton, lambda c: c.tooltip == "Toolbar"
        )
        toolbar_button.value = True  # Open the grid of tools.
        self.assertFalse(layer_button.value)

        tool_grid = utils.query_widget(toolbar_control, ipywidgets.GridBox).children

        self.assertEqual(len(tool_grid), 3)
        self.assertEqual(tool_grid[0].tooltip, "Basemap selector")
        self.assertEqual(tool_grid[1].tooltip, "Inspector")
        self.assertEqual(tool_grid[2].tooltip, "Get help")

        # Closing the toolbar button shows both buttons in the header.
        toolbar_button.value = False
        self.assertIsNotNone(
            utils.query_widget(
                toolbar_control,
                ipywidgets.ToggleButton,
                lambda c: c.tooltip == "Toolbar",
            )
        )
        self.assertIsNotNone(
            utils.query_widget(
                toolbar_control,
                ipywidgets.ToggleButton,
                lambda c: c.tooltip == "Layers",
            )
        )

    def test_add_draw_control(self):
        """Tests adding and getting the draw widget."""

        self._clear_default_widgets()
        self.core_map.add("draw_control", position="topleft")

        self.assertEqual(len(self.core_map.controls), 1)
        self.assertIsInstance(self.core_map.get_draw_control(), core.MapDrawControl)

    def test_add_basemap_selector(self):
        """Tests adding the basemap selector widget."""
        self._clear_default_widgets()

        self.core_map.add("basemap_selector")

        self.assertEqual(len(self.core_map.controls), 1)


@patch.object(ee, "FeatureCollection", fake_ee.FeatureCollection)
@patch.object(ee, "Feature", fake_ee.Feature)
@patch.object(ee, "Geometry", fake_ee.Geometry)
@patch.object(ee, "Image", fake_ee.Image)
class TestAbstractDrawControl(unittest.TestCase):
    """Tests for the draw control interface in the `draw_control` module."""

    geo_json = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [0, 1],
                    [0, -1],
                    [1, -1],
                    [1, 1],
                    [0, 1],
                ]
            ],
        },
        "properties": {"name": "Null Island"},
    }
    geo_json2 = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [0, 2],
                    [0, -2],
                    [2, -2],
                    [2, 2],
                    [0, 2],
                ]
            ],
        },
        "properties": {"name": "Null Island 2x"},
    }

    def setUp(self):
        self.map = fake_map.FakeMap()
        self._draw_control = TestAbstractDrawControl.TestDrawControl(self.map)

    def tearDown(self):
        pass

    def test_initialization(self):
        # Initialized is set by the `_bind_draw_controls` method.
        self.assertTrue(self._draw_control.initialized)
        self.assertIsNone(self._draw_control.layer)
        self.assertEquals(self._draw_control.geometries, [])
        self.assertEquals(self._draw_control.properties, [])
        self.assertIsNone(self._draw_control.last_geometry)
        self.assertIsNone(self._draw_control.last_draw_action)
        self.assertEquals(self._draw_control.features, [])
        self.assertEquals(self._draw_control.collection, fake_ee.FeatureCollection([]))
        self.assertIsNone(self._draw_control.last_feature)
        self.assertEquals(self._draw_control.count, 0)
        self.assertFalse("Drawn Features" in self.map.ee_layers)

    def test_handles_creation(self):
        self._draw_control.create(self.geo_json)
        self.assertEquals(
            self._draw_control.geometries,
            [fake_ee.Geometry(self.geo_json["geometry"])],
        )
        self.assertTrue("Drawn Features" in self.map.ee_layers)

    def test_handles_deletion(self):
        self._draw_control.create(self.geo_json)
        self.assertTrue("Drawn Features" in self.map.ee_layers)
        self.assertEquals(len(self._draw_control.geometries), 1)
        self._draw_control.delete(0)
        self.assertEquals(len(self._draw_control.geometries), 0)
        self.assertFalse("Drawn Features" in self.map.ee_layers)

    def test_handles_edit(self):
        self._draw_control.create(self.geo_json)
        self.assertEquals(len(self._draw_control.geometries), 1)

        self._draw_control.edit(0, self.geo_json2)
        self.assertEquals(len(self._draw_control.geometries), 1)
        self.assertEquals(
            self._draw_control.geometries[0],
            fake_ee.Geometry(self.geo_json2["geometry"]),
        )

    def test_property_accessors(self):
        self._draw_control.create(self.geo_json)

        # Test layer accessor.
        self.assertIsNotNone(self._draw_control.layer)
        # Test geometries accessor.
        geometry = fake_ee.Geometry(self.geo_json["geometry"])
        self.assertEquals(len(self._draw_control.geometries), 1)
        self.assertEquals(self._draw_control.geometries, [geometry])
        # Test properties accessor.
        self.assertEquals(self._draw_control.properties, [None])
        # Test last_geometry accessor.
        self.assertEquals(self._draw_control.last_geometry, geometry)
        # Test last_draw_action accessor.
        self.assertEquals(self._draw_control.last_draw_action, core.DrawActions.CREATED)
        # Test features accessor.
        feature = fake_ee.Feature(geometry, None)
        self.assertEquals(self._draw_control.features, [feature])
        # Test collection accessor.
        self.assertEquals(
            self._draw_control.collection, fake_ee.FeatureCollection([feature])
        )
        # Test last_feature accessor.
        self.assertEquals(self._draw_control.last_feature, feature)
        # Test count accessor.
        self.assertEquals(self._draw_control.count, 1)

    def test_feature_property_access(self):
        self._draw_control.create(self.geo_json)
        geometry = self._draw_control.geometries[0]
        self.assertIsNone(self._draw_control.get_geometry_properties(geometry))
        self.assertEquals(
            self._draw_control.features, [fake_ee.Feature(geometry, None)]
        )
        self._draw_control.set_geometry_properties(geometry, {"test": 1})
        self.assertEquals(
            self._draw_control.features, [fake_ee.Feature(geometry, {"test": 1})]
        )

    def test_reset(self):
        self._draw_control.create(self.geo_json)
        self.assertEquals(len(self._draw_control.geometries), 1)

        # When clear_draw_control is True, deletes the underlying geometries.
        self._draw_control.reset(clear_draw_control=True)
        self.assertEquals(len(self._draw_control.geometries), 0)
        self.assertEquals(len(self._draw_control.geo_jsons), 0)
        self.assertFalse("Drawn Features" in self.map.ee_layers)

        self._draw_control.create(self.geo_json)
        self.assertEquals(len(self._draw_control.geometries), 1)
        # When clear_draw_control is False, does not delete the underlying
        # geometries.
        self._draw_control.reset(clear_draw_control=False)
        self.assertEquals(len(self._draw_control.geometries), 0)
        self.assertEquals(len(self._draw_control.geo_jsons), 1)
        self.assertFalse("Drawn Features" in self.map.ee_layers)

    def test_remove_geometry(self):
        self._draw_control.create(self.geo_json)
        self._draw_control.create(self.geo_json2)
        geometry1 = self._draw_control.geometries[0]
        geometry2 = self._draw_control.geometries[1]
        self.assertEquals(len(self._draw_control.geometries), 2)
        self.assertEquals(len(self._draw_control.properties), 2)
        self.assertEquals(self._draw_control.last_draw_action, core.DrawActions.CREATED)
        self.assertEquals(self._draw_control.last_geometry, geometry2)

        # When there are two geometries and the removed geometry is the last
        # one, then we treat it like an undo.
        self._draw_control.remove_geometry(geometry2)
        self.assertEquals(len(self._draw_control.geometries), 1)
        self.assertEquals(len(self._draw_control.properties), 1)
        self.assertEquals(
            self._draw_control.last_draw_action, core.DrawActions.REMOVED_LAST
        )
        self.assertEquals(self._draw_control.last_geometry, geometry1)

        # When there's only one geometry, last_geometry is the removed geometry.
        self._draw_control.remove_geometry(geometry1)
        self.assertEquals(len(self._draw_control.geometries), 0)
        self.assertEquals(len(self._draw_control.properties), 0)
        self.assertEquals(
            self._draw_control.last_draw_action, core.DrawActions.REMOVED_LAST
        )
        self.assertEquals(self._draw_control.last_geometry, geometry1)

        # When there are two geometries and the removed geometry is the first
        # one, then treat it like a normal delete.
        self._draw_control.create(self.geo_json)
        self._draw_control.create(self.geo_json2)
        geometry1 = self._draw_control.geometries[0]
        geometry2 = self._draw_control.geometries[1]
        self._draw_control.remove_geometry(geometry1)
        self.assertEquals(len(self._draw_control.geometries), 1)
        self.assertEquals(len(self._draw_control.properties), 1)
        self.assertEquals(self._draw_control.last_draw_action, core.DrawActions.DELETED)
        self.assertEquals(self._draw_control.last_geometry, geometry1)

    class TestDrawControl(core.AbstractDrawControl):
        """Implements an AbstractDrawControl for tests."""

        geo_jsons = []
        initialized = False

        def __init__(self, host_map, **kwargs):
            """Initialize the test draw control.

            Args:
                host_map (geemap.Map): The geemap.Map object
            """
            super(TestAbstractDrawControl.TestDrawControl, self).__init__(
                host_map=host_map, **kwargs
            )
            self.geo_jsons = []

        def _get_synced_geojson_from_draw_control(self):
            return [data.copy() for data in self.geo_jsons]

        def _bind_to_draw_control(self):
            # In a non-test environment, `_on_draw` would be used here.
            self.initialized = True

        def _remove_geometry_at_index_on_draw_control(self, index):
            geo_json = self.geo_jsons[index]
            del self.geo_jsons[index]
            self._on_draw("deleted", geo_json)

        def _clear_draw_control(self):
            self.geo_jsons = []

        def _on_draw(self, action, geo_json):
            """Mimics the ipyleaflet DrawControl handler."""
            if action == "created":
                self._handle_geometry_created(geo_json)
            elif action == "edited":
                self._handle_geometry_edited(geo_json)
            elif action == "deleted":
                self._handle_geometry_deleted(geo_json)

        def create(self, geo_json):
            self.geo_jsons.append(geo_json)
            self._on_draw("created", geo_json)

        def edit(self, i, geo_json):
            self.geo_jsons[i] = geo_json
            self._on_draw("edited", geo_json)

        def delete(self, i):
            geo_json = self.geo_jsons[i]
            del self.geo_jsons[i]
            self._on_draw("deleted", geo_json)
