"""Tests for the plotlymap module."""

import unittest

import pandas as pd

try:
    from plotly import graph_objects as go
    from geemap import plotlymap

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


@unittest.skipUnless(PLOTLY_AVAILABLE, "plotly not available")
class PlotlymapTest(unittest.TestCase):

    def test_map_init_default_params(self):
        m = plotlymap.Map(ee_initialize=False)
        self.assertEqual(m.layout.mapbox.center.lat, 20)
        self.assertEqual(m.layout.mapbox.center.lon, 0)
        self.assertEqual(m.layout.mapbox.zoom, 1)
        self.assertEqual(m.layout.mapbox.style, "open-street-map")
        self.assertEqual(m.layout.height, 600)
        self.assertEqual(len(m.data), 1)

    def test_map_init_custom_center(self):
        m = plotlymap.Map(center=(40, -100), ee_initialize=False)
        self.assertEqual(m.layout.mapbox.center.lat, 40)
        self.assertEqual(m.layout.mapbox.center.lon, -100)

    def test_map_init_custom_zoom(self):
        m = plotlymap.Map(zoom=10, ee_initialize=False)
        self.assertEqual(m.layout.mapbox.zoom, 10)

    def test_map_init_custom_height(self):
        m = plotlymap.Map(height=800, ee_initialize=False)
        self.assertEqual(m.layout.height, 800)

    def test_map_init_custom_basemap(self):
        m = plotlymap.Map(basemap="carto-positron", ee_initialize=False)
        self.assertEqual(m.layout.mapbox.style, "carto-positron")

    def test_set_center_with_zoom(self):
        m = plotlymap.Map(ee_initialize=False)
        m.set_center(lat=37.8, lon=-122.4, zoom=12)
        self.assertEqual(m.layout.mapbox.center.lat, 37.8)
        self.assertEqual(m.layout.mapbox.center.lon, -122.4)
        self.assertEqual(m.layout.mapbox.zoom, 12)

    def test_set_center_without_zoom(self):
        m = plotlymap.Map(ee_initialize=False)
        m.set_center(lat=37.8, lon=-122.4)
        self.assertEqual(m.layout.mapbox.center.lat, 37.8)
        self.assertEqual(m.layout.mapbox.center.lon, -122.4)
        self.assertEqual(m.layout.mapbox.zoom, 1)

    def test_add_controls_string_and_list(self):
        m = plotlymap.Map(ee_initialize=False)
        m.add_controls("drawline")
        m.add_controls(["drawline", "drawopenpath"])

    def test_add_controls_invalid_type_raises(self):
        m = plotlymap.Map(ee_initialize=False)
        with self.assertRaises(ValueError):
            m.add_controls(12345)

    def test_remove_controls_string_and_list(self):
        m = plotlymap.Map(ee_initialize=False)
        m.remove_controls("zoomin")
        m.remove_controls(["zoomin", "zoomout"])

    def test_remove_controls_invalid_type_raises(self):
        m = plotlymap.Map(ee_initialize=False)
        with self.assertRaises(ValueError):
            m.remove_controls(12345)

    def test_add_tile_layer(self):
        m = plotlymap.Map(ee_initialize=False)
        m.add_tile_layer(
            url="https://tile.example.com/{z}/{x}/{y}.png",
            name="Test Layer",
        )
        self.assertIn("Test Layer", m.get_tile_layers())

    def test_add_layer(self):
        m = plotlymap.Map(ee_initialize=False)
        layer = go.Scattermapbox(lat=[37.8], lon=[-122.4])
        m.add_layer(layer, name="My Layer")
        self.assertIn("My Layer", m.get_data_layers())

    def test_get_layers_empty(self):
        m = plotlymap.Map(ee_initialize=False)
        self.assertEqual(m.get_layers(), {})
        self.assertEqual(m.get_tile_layers(), {})
        self.assertEqual(m.get_data_layers(), {})

    def test_find_layer_index_not_found(self):
        m = plotlymap.Map(ee_initialize=False)
        self.assertIsNone(m.find_layer_index("nonexistent"))

    def test_find_layer_index_data_layer(self):
        m = plotlymap.Map(ee_initialize=False)
        layer = go.Scattermapbox(lat=[37.8], lon=[-122.4], name="pts")
        m.add_layer(layer)
        self.assertEqual(m.find_layer_index("pts"), 1)

    def test_clear_layers_keeps_basemap(self):
        m = plotlymap.Map(ee_initialize=False)
        layer = go.Scattermapbox(lat=[37.8], lon=[-122.4], name="extra")
        m.add_layer(layer)
        m.clear_layers()
        self.assertEqual(len(m.data), 1)

    def test_clear_layers_with_basemap(self):
        m = plotlymap.Map(ee_initialize=False)
        m.clear_layers(clear_basemap=True)
        self.assertEqual(len(m.data), 0)

    def test_add_heatmap_dataframe(self):
        m = plotlymap.Map(ee_initialize=False)
        df = pd.DataFrame(
            {
                "latitude": [37.8, 37.7],
                "longitude": [-122.4, -122.3],
                "value": [1.0, 0.5],
            }
        )
        m.add_heatmap(df)
        self.assertEqual(len(m.data), 2)

    def test_add_heatmap_invalid_data_raises(self):
        m = plotlymap.Map(ee_initialize=False)
        with self.assertRaises(ValueError):
            m.add_heatmap({"invalid": "data"})

    def test_add_basemap_invalid_raises(self):
        m = plotlymap.Map(ee_initialize=False)
        with self.assertRaises(ValueError):
            m.add_basemap("INVALID_BASEMAP_XYZ")

    def test_add_ee_layer_invalid_type_raises(self):
        m = plotlymap.Map(ee_initialize=False)
        with self.assertRaises(AttributeError):
            m.add_ee_layer("not_an_ee_object")

    def test_addlayer_alias(self):
        m = plotlymap.Map(ee_initialize=False)
        self.assertEqual(m.addLayer, m.add_ee_layer)

    def test_remove_layer(self):
        m = plotlymap.Map(ee_initialize=False)
        m.add_tile_layer(
            url="https://tile.example.com/{z}/{x}/{y}.png",
            name="removable",
        )
        self.assertIn("removable", m.get_tile_layers())
        m.remove_layer("removable")
        self.assertNotIn("removable", m.get_tile_layers())

    def test_set_layer_visibility(self):
        m = plotlymap.Map(ee_initialize=False)
        layer = go.Scattermapbox(lat=[0], lon=[0], name="vis_test")
        m.add_layer(layer)
        m.set_layer_visibility("vis_test", show=False)
        idx = m.find_layer_index("vis_test")
        self.assertFalse(m.data[idx].visible)

    def test_set_layer_opacity(self):
        m = plotlymap.Map(ee_initialize=False)
        m.add_tile_layer(
            url="https://tile.example.com/{z}/{x}/{y}.png",
            name="opacity_test",
        )
        m.set_layer_opacity("opacity_test", opacity=0.5)
        idx = m.find_layer_index("opacity_test")
        self.assertEqual(m.layout.mapbox.layers[idx].opacity, 0.5)


if __name__ == "__main__":
    unittest.main()
