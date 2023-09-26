#!/usr/bin/env python

"""Tests for `draw_control` module."""

import unittest

import ee
import fake_ee
import fake_map

from geemap import draw_control
from unittest.mock import patch


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
        map = fake_map.FakeMap()
        self._draw_control = TestAbstractDrawControl.TestDrawControl(map)

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

    def test_handles_creation(self):
        self._draw_control.create(self.geo_json)
        self.assertEquals(
            self._draw_control.geometries,
            [fake_ee.Geometry(self.geo_json["geometry"])],
        )

    def test_handles_deletion(self):
        self._draw_control.create(self.geo_json)
        self.assertEquals(len(self._draw_control.geometries), 1)
        self._draw_control.delete(0)
        self.assertEquals(len(self._draw_control.geometries), 0)

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
        self.assertEquals(
            self._draw_control.last_draw_action, draw_control.DrawActions.CREATED
        )
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

        self._draw_control.create(self.geo_json)
        self.assertEquals(len(self._draw_control.geometries), 1)
        # When clear_draw_control is False, does not delete the underlying
        # geometries.
        self._draw_control.reset(clear_draw_control=False)
        self.assertEquals(len(self._draw_control.geometries), 0)
        self.assertEquals(len(self._draw_control.geo_jsons), 1)

    def test_remove_geometry(self):
        self._draw_control.create(self.geo_json)
        self._draw_control.create(self.geo_json2)
        geometry1 = self._draw_control.geometries[0]
        geometry2 = self._draw_control.geometries[1]
        self.assertEquals(len(self._draw_control.geometries), 2)
        self.assertEquals(len(self._draw_control.properties), 2)
        self.assertEquals(
            self._draw_control.last_draw_action, draw_control.DrawActions.CREATED
        )
        self.assertEquals(self._draw_control.last_geometry, geometry2)

        # When there are two geometries and the removed geometry is the last
        # one, then we treat it like an undo.
        self._draw_control.remove_geometry(geometry2)
        self.assertEquals(len(self._draw_control.geometries), 1)
        self.assertEquals(len(self._draw_control.properties), 1)
        self.assertEquals(
            self._draw_control.last_draw_action, draw_control.DrawActions.REMOVED_LAST
        )
        self.assertEquals(self._draw_control.last_geometry, geometry1)

        # When there's only one geometry, last_geometry is the removed geometry.
        self._draw_control.remove_geometry(geometry1)
        self.assertEquals(len(self._draw_control.geometries), 0)
        self.assertEquals(len(self._draw_control.properties), 0)
        self.assertEquals(
            self._draw_control.last_draw_action, draw_control.DrawActions.REMOVED_LAST
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
        self.assertEquals(
            self._draw_control.last_draw_action, draw_control.DrawActions.DELETED
        )
        self.assertEquals(self._draw_control.last_geometry, geometry1)

    class TestDrawControl(draw_control.AbstractDrawControl):
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
