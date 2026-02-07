"""Tests for the foliumap module."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest import mock

try:
    import sys
    import importlib
    import folium

    _fake_basemaps = {
        "ROADMAP": folium.TileLayer(tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", attr="Google", name="ROADMAP"),
        "SATELLITE": folium.TileLayer(tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", attr="Google", name="SATELLITE"),
        "HYBRID": folium.TileLayer(tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}", attr="Google", name="HYBRID"),
        "TERRAIN": folium.TileLayer(tiles="https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}", attr="Google", name="TERRAIN"),
        "OpenStreetMap": folium.TileLayer(tiles="OpenStreetMap", attr="OSM", name="OpenStreetMap"),
    }

    # Importing the geemap package causes `from .geemap import *` which brings
    # a Box named `basemaps` into the geemap namespace, shadowing the real
    # basemaps *module*.  When foliumap.py later does `from . import basemaps`
    # Python resolves the package attribute (the Box) instead of the module,
    # so `basemaps.xyz_to_folium()` fails.
    #
    # Fix: ensure the geemap package is loaded, then temporarily restore the
    # real basemaps module as the package attribute so foliumap's
    # `from . import basemaps` picks up the actual module (with our mock on it).
    import geemap
    _real_basemaps_module = sys.modules["geemap.basemaps"]

    # Drop any cached foliumap so the module-level code re-executes with our mock.
    sys.modules.pop("geemap.foliumap", None)

    _saved_attr = getattr(geemap, "basemaps", None)
    geemap.basemaps = _real_basemaps_module

    with mock.patch.object(_real_basemaps_module, "xyz_to_folium", return_value=_fake_basemaps):
        from geemap import foliumap

    geemap.basemaps = _saved_attr
    FOLIUM_AVAILABLE = True
except Exception:
    FOLIUM_AVAILABLE = False


@unittest.skipUnless(FOLIUM_AVAILABLE, "folium not available")
class FoliumapTest(unittest.TestCase):

    def _make_map(self, **kwargs) -> foliumap.Map:
        return foliumap.Map(ee_initialize=False, **kwargs)

    # ------------------------------------------------------------------ #
    # Map initialization
    # ------------------------------------------------------------------ #

    def test_map_init_default_params(self) -> None:
        m = self._make_map()
        self.assertIsInstance(m, folium.Map)
        self.assertEqual(m.location, [20, 0])
        self.assertEqual(m.options["zoom"], 2)

    def test_map_init_custom_center(self) -> None:
        m = self._make_map(center=[40, -100])
        self.assertEqual(m.location, [40, -100])

    def test_map_init_custom_zoom(self) -> None:
        m = self._make_map(zoom=10)
        self.assertEqual(m.options["zoom"], 10)

    def test_map_init_location_param(self) -> None:
        m = self._make_map(location=[35, 139])
        self.assertEqual(m.location, [35, 139])

    def test_map_baseclass(self) -> None:
        m = self._make_map()
        self.assertEqual(m.baseclass, "folium")

    def test_map_init_draw_features_empty(self) -> None:
        m = self._make_map()
        self.assertEqual(m.draw_features, [])
        self.assertIsNone(m.draw_last_feature)

    def test_map_max_zoom_default(self) -> None:
        m = self._make_map()
        # The default fit_bounds call uses maxZoom; verify via the FitBounds child.
        fit_children = [
            c for c in m._children.values() if type(c).__name__ == "FitBounds"
        ]
        self.assertTrue(len(fit_children) > 0)
        self.assertEqual(fit_children[0].options.get("maxZoom"), 2)

    # ------------------------------------------------------------------ #
    # set_center
    # ------------------------------------------------------------------ #

    def test_set_center_updates_bounds(self) -> None:
        m = self._make_map()
        m.set_center(-122.4, 37.8, zoom=12)
        # folium stores bounds via FitBounds children, not in get_bounds().
        fit_children = [
            c for c in m._children.values() if type(c).__name__ == "FitBounds"
        ]
        last = fit_children[-1]
        self.assertAlmostEqual(last.bounds[0][0], 37.8, places=1)
        self.assertAlmostEqual(last.bounds[0][1], -122.4, places=1)

    # ------------------------------------------------------------------ #
    # zoom_to_bounds
    # ------------------------------------------------------------------ #

    def test_zoom_to_bounds_updates_bounds(self) -> None:
        m = self._make_map()
        m.zoom_to_bounds([-122.5, 37.5, -122.0, 38.0])
        # folium stores bounds via FitBounds children.
        fit_children = [
            c for c in m._children.values() if type(c).__name__ == "FitBounds"
        ]
        last = fit_children[-1]
        south, west = last.bounds[0]
        north, east = last.bounds[1]
        self.assertAlmostEqual(south, 37.5, places=1)
        self.assertAlmostEqual(west, -122.5, places=1)
        self.assertAlmostEqual(north, 38.0, places=1)
        self.assertAlmostEqual(east, -122.0, places=1)

    # ------------------------------------------------------------------ #
    # add_tile_layer
    # ------------------------------------------------------------------ #

    def test_add_tile_layer_increases_children(self) -> None:
        m = self._make_map()
        children_before = len(m._children)
        m.add_tile_layer(
            tiles="https://tile.example.com/{z}/{x}/{y}.png",
            name="Test Layer",
            attribution="Test",
        )
        self.assertGreater(len(m._children), children_before)

    def test_add_tile_layer_name_in_children(self) -> None:
        m = self._make_map()
        m.add_tile_layer(
            tiles="https://tile.example.com/{z}/{x}/{y}.png",
            name="MyTiles",
            attribution="Test",
        )
        child_names = [
            getattr(c, "tile_name", getattr(c, "name", ""))
            for c in m._children.values()
        ]
        # The tile layer name should appear in children tile_name attributes.
        self.assertIn("MyTiles", child_names)

    # ------------------------------------------------------------------ #
    # add_wms_layer
    # ------------------------------------------------------------------ #

    def test_add_wms_layer_increases_children(self) -> None:
        m = self._make_map()
        children_before = len(m._children)
        m.add_wms_layer(
            url="https://example.com/wms",
            layers="test_layer",
            name="WMS Test",
        )
        self.assertGreater(len(m._children), children_before)

    # ------------------------------------------------------------------ #
    # add_marker
    # ------------------------------------------------------------------ #

    def test_add_marker_list(self) -> None:
        m = self._make_map()
        children_before = len(m._children)
        m.add_marker(location=[37.8, -122.4], popup="Test")
        self.assertGreater(len(m._children), children_before)

    def test_add_marker_tuple(self) -> None:
        m = self._make_map()
        children_before = len(m._children)
        m.add_marker(location=(37.8, -122.4), tooltip="Tooltip")
        self.assertGreater(len(m._children), children_before)

    def test_add_marker_invalid_type_raises(self) -> None:
        m = self._make_map()
        with self.assertRaises(TypeError):
            m.add_marker(location="invalid")

    # ------------------------------------------------------------------ #
    # add_geojson
    # ------------------------------------------------------------------ #

    def test_add_geojson_from_dict(self) -> None:
        m = self._make_map()
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-122.4, 37.8],
                    },
                    "properties": {"name": "Test Point"},
                }
            ],
        }
        children_before = len(m._children)
        m.add_geojson(geojson_data, layer_name="GeoJSON Test")
        self.assertGreater(len(m._children), children_before)

    def test_add_geojson_from_file(self) -> None:
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-122.4, 37.8],
                    },
                    "properties": {"name": "Test"},
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.geojson")
            with open(filepath, "w") as f:
                json.dump(geojson_data, f)
            m = self._make_map()
            children_before = len(m._children)
            m.add_geojson(filepath, layer_name="File GeoJSON")
            self.assertGreater(len(m._children), children_before)

    def test_add_geojson_file_not_found_raises(self) -> None:
        m = self._make_map()
        with self.assertRaises(Exception):
            m.add_geojson("/nonexistent/path.geojson")

    def test_add_geojson_invalid_type_raises(self) -> None:
        m = self._make_map()
        with self.assertRaises(Exception):
            m.add_geojson(12345)

    # ------------------------------------------------------------------ #
    # add_heatmap
    # ------------------------------------------------------------------ #

    def test_add_heatmap_from_list(self) -> None:
        m = self._make_map()
        data = [[37.8, -122.4, 1.0], [37.9, -122.3, 2.0]]
        children_before = len(m._children)
        m.add_heatmap(data=data, name="Heat")
        self.assertGreater(len(m._children), children_before)

    def test_add_heatmap_invalid_data_raises(self) -> None:
        m = self._make_map()
        with self.assertRaises(ValueError):
            m.add_heatmap(data=12345)

    # ------------------------------------------------------------------ #
    # to_html
    # ------------------------------------------------------------------ #

    def test_to_html_returns_string(self) -> None:
        m = self._make_map()
        html = m.to_html()
        self.assertIsInstance(html, str)
        self.assertIn("<html>", html.lower())
        self.assertIn("leaflet", html.lower())

    def test_to_html_saves_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_map.html")
            m = self._make_map()
            m.to_html(filepath)
            self.assertTrue(os.path.exists(filepath))
            with open(filepath) as f:
                content = f.read()
            self.assertIn("<html>", content.lower())
            self.assertIn("leaflet", content.lower())

    def test_to_html_invalid_extension_raises(self) -> None:
        m = self._make_map()
        with self.assertRaises(ValueError):
            m.to_html("output.txt")

    # ------------------------------------------------------------------ #
    # add_layer_control
    # ------------------------------------------------------------------ #

    def test_add_layer_control(self) -> None:
        m = self._make_map()
        children_before = len(m._children)
        m.add_layer_control()
        self.assertGreater(len(m._children), children_before)

    # ------------------------------------------------------------------ #
    # set_control_visibility
    # ------------------------------------------------------------------ #

    def test_set_control_visibility_adds_children(self) -> None:
        m = self._make_map()
        children_before = len(m._children)
        m.set_control_visibility(
            layerControl=True,
            fullscreenControl=True,
            latLngPopup=True,
        )
        self.assertGreater(len(m._children), children_before)

    # ------------------------------------------------------------------ #
    # setOptions
    # ------------------------------------------------------------------ #

    def test_set_options_adds_basemap(self) -> None:
        m = self._make_map()
        children_before = len(m._children)
        m.setOptions("HYBRID")
        self.assertGreater(len(m._children), children_before)

    def test_set_options_invalid_basemap_raises(self) -> None:
        m = self._make_map()
        with self.assertRaises(Exception):
            m.setOptions("INVALID_BASEMAP_XYZ")

    # ------------------------------------------------------------------ #
    # add_cog_mosaic (deprecated)
    # ------------------------------------------------------------------ #

    def test_add_cog_mosaic_raises_not_implemented(self) -> None:
        m = self._make_map()
        with self.assertRaises(NotImplementedError):
            m.add_cog_mosaic()


if __name__ == "__main__":
    unittest.main()
