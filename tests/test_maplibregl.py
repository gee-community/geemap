"""Tests for the maplibregl module."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest import mock

try:
    from maplibre.ipywidget import MapWidget
    MAPLIBRE_AVAILABLE = True
except ImportError:
    MAPLIBRE_AVAILABLE = False

MAPLIBREGL_MODULE = None
IMPORT_ERROR = None


def get_maplibregl():
    global MAPLIBREGL_MODULE, IMPORT_ERROR
    if MAPLIBREGL_MODULE is not None:
        return MAPLIBREGL_MODULE
    if IMPORT_ERROR is not None:
        raise IMPORT_ERROR
    try:
        with mock.patch("geemap.coreutils.ee_initialize"):
            from geemap import maplibregl
            MAPLIBREGL_MODULE = maplibregl
            return maplibregl
    except Exception as e:
        IMPORT_ERROR = e
        raise


@unittest.skipUnless(MAPLIBRE_AVAILABLE, "maplibre not available")
class MaplibreglTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.mkdtemp()
        try:
            cls.maplibregl = get_maplibregl()
            cls.skip_tests = False
        except Exception as e:
            cls.skip_tests = True
            cls.skip_reason = str(e)

    @classmethod
    def tearDownClass(cls) -> None:
        import shutil
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def setUp(self) -> None:
        if self.skip_tests:
            self.skipTest(f"maplibregl import failed: {self.skip_reason}")


@unittest.skipUnless(MAPLIBRE_AVAILABLE, "maplibre not available")
class TestMapInit(MaplibreglTestCase):

    def test_map_init_default_params(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map()
            self.assertIsInstance(m, MapWidget)

    def test_map_init_custom_center(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map(center=(-100, 40))
            self.assertIsInstance(m, MapWidget)

    def test_map_init_custom_zoom(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map(zoom=10)
            self.assertIsInstance(m, MapWidget)

    def test_map_init_custom_pitch(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map(pitch=45)
            self.assertIsInstance(m, MapWidget)

    def test_map_init_custom_bearing(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map(bearing=90)
            self.assertIsInstance(m, MapWidget)

    def test_map_init_custom_height(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map(height="800px")
            self.assertIsInstance(m, MapWidget)

    def test_map_init_carto_style(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map(style="positron")
            self.assertIsInstance(m, MapWidget)

    def test_map_init_no_controls(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map(controls={})
            self.assertIsInstance(m, MapWidget)


@unittest.skipUnless(MAPLIBRE_AVAILABLE, "maplibre not available")
class TestSetCenter(MaplibreglTestCase):

    def test_set_center_valid(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map()
            m.set_center(lon=-122.4, lat=37.8, zoom=12)

    def test_set_center_without_zoom(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map()
            m.set_center(lon=-122.4, lat=37.8)


@unittest.skipUnless(MAPLIBRE_AVAILABLE, "maplibre not available")
class TestSetZoom(MaplibreglTestCase):

    def test_set_zoom_valid(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map()
            m.set_zoom(10)


@unittest.skipUnless(MAPLIBRE_AVAILABLE, "maplibre not available")
class TestFitBounds(MaplibreglTestCase):

    def test_fit_bounds_list_of_lists(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map()
            m.fit_bounds([[-122.5, 37.5], [-122.0, 38.0]])

    def test_fit_bounds_flat_list(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map()
            m.fit_bounds([-122.5, 37.5, -122.0, 38.0])


@unittest.skipUnless(MAPLIBRE_AVAILABLE, "maplibre not available")
class TestAddControl(MaplibreglTestCase):

    def test_add_control_scale(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map(controls={})
            m.add_control("scale", position="bottom-left")

    def test_add_control_fullscreen(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map(controls={})
            m.add_control("fullscreen", position="top-right")

    def test_add_control_navigation(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map(controls={})
            m.add_control("navigation", position="top-right")


@unittest.skipUnless(MAPLIBRE_AVAILABLE, "maplibre not available")
class TestAddRemoveLayer(MaplibreglTestCase):

    def test_remove_layer_not_existing(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map()
            m.remove_layer("nonexistent_layer")


@unittest.skipUnless(MAPLIBRE_AVAILABLE, "maplibre not available")
class TestAddTileLayer(MaplibreglTestCase):

    def test_add_tile_layer_valid(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map()
            m.add_tile_layer(
                url="https://tile.example.com/{z}/{x}/{y}.png",
                name="Test Layer",
                attribution="Test"
            )


@unittest.skipUnless(MAPLIBRE_AVAILABLE, "maplibre not available")
class TestAddGeojson(MaplibreglTestCase):

    def test_add_geojson_dict_input(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            geojson_data = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [-122.4, 37.8]},
                        "properties": {"name": "Test"},
                    }
                ],
            }
            m = self.maplibregl.Map()
            m.add_geojson(geojson_data, name="Test GeoJSON", fit_bounds=False)

    def test_add_geojson_invalid_type_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map()
            with self.assertRaises(ValueError):
                m.add_geojson(12345)


@unittest.skipUnless(MAPLIBRE_AVAILABLE, "maplibre not available")
class TestAddGdf(MaplibreglTestCase):

    def test_add_gdf_invalid_type_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.maplibregl.Map()
            with self.assertRaises(ValueError):
                m.add_gdf("not_a_gdf")


if __name__ == "__main__":
    unittest.main()
