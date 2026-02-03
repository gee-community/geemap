"""Tests for the plotlymap module."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

import pandas as pd

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

PLOTLYMAP_MODULE = None
IMPORT_ERROR = None


def get_plotlymap():
    global PLOTLYMAP_MODULE, IMPORT_ERROR
    if PLOTLYMAP_MODULE is not None:
        return PLOTLYMAP_MODULE
    if IMPORT_ERROR is not None:
        raise IMPORT_ERROR
    try:
        with mock.patch("geemap.coreutils.ee_initialize"):
            from geemap import plotlymap
            PLOTLYMAP_MODULE = plotlymap
            return plotlymap
    except Exception as e:
        IMPORT_ERROR = e
        raise


@unittest.skipUnless(PLOTLY_AVAILABLE, "plotly not available")
class PlotlymapTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.mkdtemp()
        try:
            cls.plotlymap = get_plotlymap()
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
            self.skipTest(f"plotlymap import failed: {self.skip_reason}")


@unittest.skipUnless(PLOTLY_AVAILABLE, "plotly not available")
class TestMapInit(PlotlymapTestCase):

    def test_map_init_default_params(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            self.assertIsInstance(m, go.FigureWidget)

    def test_map_init_custom_center(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(center=(40, -100), ee_initialize=False)
            self.assertIsInstance(m, go.FigureWidget)

    def test_map_init_custom_zoom(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(zoom=10, ee_initialize=False)
            self.assertIsInstance(m, go.FigureWidget)

    def test_map_init_custom_height(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(height=800, ee_initialize=False)
            self.assertIsInstance(m, go.FigureWidget)

    def test_map_init_custom_basemap(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(basemap="carto-positron", ee_initialize=False)
            self.assertIsInstance(m, go.FigureWidget)


@unittest.skipUnless(PLOTLY_AVAILABLE, "plotly not available")
class TestSetCenter(PlotlymapTestCase):

    def test_set_center_valid(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            m.set_center(lat=37.8, lon=-122.4, zoom=12)

    def test_set_center_without_zoom(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            m.set_center(lat=37.8, lon=-122.4)


@unittest.skipUnless(PLOTLY_AVAILABLE, "plotly not available")
class TestAddBasemap(PlotlymapTestCase):

    def test_add_basemap_invalid_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            with self.assertRaises(ValueError):
                m.add_basemap("INVALID_BASEMAP_NAME_XYZ")


@unittest.skipUnless(PLOTLY_AVAILABLE, "plotly not available")
class TestAddRemoveControls(PlotlymapTestCase):

    def test_add_controls_string(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            m.add_controls("drawline")

    def test_add_controls_list(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            m.add_controls(["drawline", "drawopenpath"])

    def test_add_controls_invalid_type_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            with self.assertRaises(ValueError):
                m.add_controls(12345)

    def test_remove_controls_string(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            m.remove_controls("zoomin")

    def test_remove_controls_list(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            m.remove_controls(["zoomin", "zoomout"])

    def test_remove_controls_invalid_type_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            with self.assertRaises(ValueError):
                m.remove_controls(12345)


@unittest.skipUnless(PLOTLY_AVAILABLE, "plotly not available")
class TestAddTileLayer(PlotlymapTestCase):

    def test_add_tile_layer_valid(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            m.add_tile_layer(
                url="https://tile.example.com/{z}/{x}/{y}.png",
                name="Test Layer",
                attribution="Test"
            )


@unittest.skipUnless(PLOTLY_AVAILABLE, "plotly not available")
class TestAddLayer(PlotlymapTestCase):

    def test_add_layer_valid(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            layer = go.Scattermapbox(lat=[37.8], lon=[-122.4], name="test")
            m.add_layer(layer, name="Test Layer")


@unittest.skipUnless(PLOTLY_AVAILABLE, "plotly not available")
class TestLayerManagement(PlotlymapTestCase):

    def test_get_layers_empty(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            layers = m.get_layers()
            self.assertIsInstance(layers, dict)

    def test_get_tile_layers_empty(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            layers = m.get_tile_layers()
            self.assertIsInstance(layers, dict)

    def test_get_data_layers_empty(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            layers = m.get_data_layers()
            self.assertIsInstance(layers, dict)

    def test_clear_layers(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            m.clear_layers()

    def test_clear_layers_with_basemap(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            m.clear_layers(clear_basemap=True)

    def test_find_layer_index_not_found(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            index = m.find_layer_index("nonexistent_layer")
            self.assertIsNone(index)


@unittest.skipUnless(PLOTLY_AVAILABLE, "plotly not available")
class TestAddHeatmap(PlotlymapTestCase):

    def test_add_heatmap_dataframe(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            df = pd.DataFrame({
                "latitude": [37.8, 37.7],
                "longitude": [-122.4, -122.3],
                "value": [1.0, 0.5]
            })
            m.add_heatmap(df)

    def test_add_heatmap_invalid_data_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            with self.assertRaises(ValueError):
                m.add_heatmap({"invalid": "data"})


@unittest.skipUnless(PLOTLY_AVAILABLE, "plotly not available")
class TestAddEeLayer(PlotlymapTestCase):

    def test_add_ee_layer_invalid_type_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            with self.assertRaises(AttributeError):
                m.add_ee_layer("not_an_ee_object")

    def test_addlayer_alias(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            self.assertEqual(m.addLayer, m.add_ee_layer)


@unittest.skipUnless(PLOTLY_AVAILABLE, "plotly not available")
class TestAddGdf(PlotlymapTestCase):

    def test_add_gdf_invalid_type_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.plotlymap.Map(ee_initialize=False)
            with self.assertRaises(Exception):
                m.add_gdf(12345)


if __name__ == "__main__":
    unittest.main()
