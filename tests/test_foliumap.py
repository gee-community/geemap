"""Tests for the foliumap module."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest import mock

import pandas as pd

try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

FOLIUMAP_MODULE = None
IMPORT_ERROR = None


def get_foliumap():
    global FOLIUMAP_MODULE, IMPORT_ERROR
    if FOLIUMAP_MODULE is not None:
        return FOLIUMAP_MODULE
    if IMPORT_ERROR is not None:
        raise IMPORT_ERROR
    try:
        with mock.patch("geemap.coreutils.ee_initialize"):
            from geemap import foliumap
            FOLIUMAP_MODULE = foliumap
            return foliumap
    except Exception as e:
        IMPORT_ERROR = e
        raise


@unittest.skipUnless(FOLIUM_AVAILABLE, "folium not available")
class FoliumapTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.mkdtemp()
        try:
            cls.foliumap = get_foliumap()
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
            self.skipTest(f"foliumap import failed: {self.skip_reason}")


@unittest.skipUnless(FOLIUM_AVAILABLE, "folium not available")
class TestMapInit(FoliumapTestCase):

    def test_map_init_default_params(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            self.assertEqual(m.baseclass, "folium")
            self.assertEqual(m.draw_features, [])
            self.assertIsNone(m.draw_last_feature)

    def test_map_init_custom_center(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(center=[40, -100], ee_initialize=False)
            self.assertEqual(m.baseclass, "folium")

    def test_map_init_custom_zoom(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(zoom=10, ee_initialize=False)
            self.assertEqual(m.baseclass, "folium")

    def test_map_init_plugins_disabled(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(
                plugin_Fullscreen=False,
                plugin_Draw=False,
                search_control=False,
                ee_initialize=False,
            )
            self.assertEqual(m.baseclass, "folium")

    def test_map_init_width_height(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(width=800, height=600, ee_initialize=False)
            self.assertEqual(m.baseclass, "folium")


@unittest.skipUnless(FOLIUM_AVAILABLE, "folium not available")
class TestSetCenter(FoliumapTestCase):

    def test_set_center_valid_coords(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            with mock.patch("geemap.common.is_arcpy", return_value=False):
                m = self.foliumap.Map(ee_initialize=False)
                m.set_center(-122.4, 37.8, zoom=12)

    def test_setcenter_alias(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            with mock.patch("geemap.common.is_arcpy", return_value=False):
                m = self.foliumap.Map(ee_initialize=False)
                self.assertEqual(m.setCenter, m.set_center)


@unittest.skipUnless(FOLIUM_AVAILABLE, "folium not available")
class TestZoomToBounds(FoliumapTestCase):

    def test_zoom_to_bounds_valid_bounds(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            m.zoom_to_bounds([-122.5, 37.5, -122.0, 38.0])


@unittest.skipUnless(FOLIUM_AVAILABLE, "folium not available")
class TestAddTileLayer(FoliumapTestCase):

    def test_add_tile_layer_valid_url(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            m.add_tile_layer(
                tiles="https://tile.example.com/{z}/{x}/{y}.png",
                name="Test Layer",
                attribution="Test",
            )


@unittest.skipUnless(FOLIUM_AVAILABLE, "folium not available")
class TestAddWmsLayer(FoliumapTestCase):

    def test_add_wms_layer_valid_params(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            m.add_wms_layer(
                url="https://wms.example.com/service",
                layers="layer1",
                name="WMS Layer",
            )


@unittest.skipUnless(FOLIUM_AVAILABLE, "folium not available")
class TestAddMarker(FoliumapTestCase):

    def test_add_marker_list_location(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            m.add_marker(location=[37.8, -122.4], popup="Test Popup")

    def test_add_marker_tuple_location(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            m.add_marker(location=(37.8, -122.4), tooltip="Test Tooltip")

    def test_add_marker_invalid_location_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            with self.assertRaises(TypeError) as ctx:
                m.add_marker(location="invalid")
            self.assertIn("list or a tuple", str(ctx.exception))


@unittest.skipUnless(FOLIUM_AVAILABLE, "folium not available")
class TestAddGeojson(FoliumapTestCase):

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
            m = self.foliumap.Map(ee_initialize=False)
            m.add_geojson(geojson_data, layer_name="Test GeoJSON")

    def test_add_geojson_from_file(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            geojson_data = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [0, 0]},
                        "properties": {"id": 1},
                    }
                ],
            }
            temp_path = os.path.join(self.temp_dir, "test.geojson")
            with open(temp_path, "w") as f:
                json.dump(geojson_data, f)

            m = self.foliumap.Map(ee_initialize=False)
            m.add_geojson(temp_path, layer_name="Test File")

    def test_add_geojson_file_not_found_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            with self.assertRaises(Exception):
                m.add_geojson("/nonexistent/path/file.geojson")

    def test_add_geojson_invalid_type_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            with self.assertRaises(Exception):
                m.add_geojson(12345)


@unittest.skipUnless(FOLIUM_AVAILABLE, "folium not available")
class TestAddShapefile(FoliumapTestCase):

    def test_add_shapefile_not_found_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            with self.assertRaises(FileNotFoundError):
                m.add_shapefile("/nonexistent/path/file.shp")


@unittest.skipUnless(FOLIUM_AVAILABLE, "folium not available")
class TestAddHeatmap(FoliumapTestCase):

    def test_add_heatmap_list_data(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            data = [[37.8, -122.4, 1.0], [37.7, -122.3, 0.5]]
            m.add_heatmap(data=data, name="Test Heatmap")

    def test_add_heatmap_dataframe(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            df = pd.DataFrame(
                {"latitude": [37.8, 37.7], "longitude": [-122.4, -122.3], "value": [1.0, 0.5]}
            )
            m.add_heatmap(data=df, name="Test Heatmap")

    def test_add_heatmap_invalid_data_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            with self.assertRaises(ValueError):
                m.add_heatmap(data={"invalid": "data"})


@unittest.skipUnless(FOLIUM_AVAILABLE, "folium not available")
class TestAddColorbar(FoliumapTestCase):

    def test_add_colorbar_not_dict_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            with self.assertRaises(ValueError) as ctx:
                m.add_colorbar("not_a_dict")
            self.assertIn("dictionary", str(ctx.exception))

    def test_add_colorbar_no_palette_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            with self.assertRaises(ValueError) as ctx:
                m.add_colorbar({"min": 0, "max": 100})
            self.assertIn("palette", str(ctx.exception))


@unittest.skipUnless(FOLIUM_AVAILABLE, "folium not available")
class TestAddLayerControl(FoliumapTestCase):

    def test_add_layer_control(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            m.add_layer_control()

    def test_addlayercontrol_alias(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            self.assertEqual(m.addLayerControl, m.add_layer_control)


@unittest.skipUnless(FOLIUM_AVAILABLE, "folium not available")
class TestToHtml(FoliumapTestCase):

    def test_to_html_returns_string(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            html = m.to_html()
            self.assertIsInstance(html, str)

    def test_to_html_saves_file(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            temp_path = os.path.join(self.temp_dir, "test_map.html")
            m.to_html(temp_path)
            self.assertTrue(os.path.exists(temp_path))


@unittest.skipUnless(FOLIUM_AVAILABLE, "folium not available")
class TestSetControlVisibility(FoliumapTestCase):

    def test_set_control_visibility_all_true(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            m.set_control_visibility(
                layerControl=True, fullscreenControl=True, latLngPopup=True
            )

    def test_setcontrolvisibility_alias(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            self.assertEqual(m.setControlVisibility, m.set_control_visibility)


@unittest.skipUnless(FOLIUM_AVAILABLE, "folium not available")
class TestAddCogMosaic(FoliumapTestCase):

    def test_add_cog_mosaic_raises_not_implemented(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            with self.assertRaises(NotImplementedError):
                m.add_cog_mosaic()


@unittest.skipUnless(FOLIUM_AVAILABLE, "folium not available")
class TestAddRemoteTile(FoliumapTestCase):

    def test_add_remote_tile_non_url_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            with self.assertRaises(Exception) as ctx:
                m.add_remote_tile("/local/path/file.tif")
            self.assertIn("URL", str(ctx.exception))


@unittest.skipUnless(FOLIUM_AVAILABLE, "folium not available")
class TestSetOptions(FoliumapTestCase):

    def test_setoptions_alias(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.foliumap.Map(ee_initialize=False)
            self.assertEqual(m.set_options, m.setOptions)


if __name__ == "__main__":
    unittest.main()
