"""Tests for the kepler module."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest import mock

import pandas as pd

try:
    import keplergl

    KEPLERGL_AVAILABLE = True
except ImportError:
    KEPLERGL_AVAILABLE = False

KEPLER_MODULE = None
IMPORT_ERROR = None


def get_kepler():
    global KEPLER_MODULE, IMPORT_ERROR
    if KEPLER_MODULE is not None:
        return KEPLER_MODULE
    if IMPORT_ERROR is not None:
        raise IMPORT_ERROR
    try:
        with mock.patch("geemap.coreutils.ee_initialize"):
            from geemap import kepler

            KEPLER_MODULE = kepler
            return kepler
    except Exception as e:
        IMPORT_ERROR = e
        raise


@unittest.skipUnless(KEPLERGL_AVAILABLE, "keplergl not available")
class KeplerTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.mkdtemp()
        try:
            cls.kepler = get_kepler()
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
            self.skipTest(f"kepler import failed: {self.skip_reason}")


@unittest.skipUnless(KEPLERGL_AVAILABLE, "keplergl not available")
class TestMapInit(KeplerTestCase):

    def test_map_init_default_params(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map()
            self.assertIsInstance(m, keplergl.KeplerGl)
            self.assertIn("config", dir(m))

    def test_map_init_custom_center(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map(center=[40, -100])
            self.assertIsInstance(m, keplergl.KeplerGl)
            self.assertEqual(m.config["config"]["mapState"]["latitude"], 40)
            self.assertEqual(m.config["config"]["mapState"]["longitude"], -100)

    def test_map_init_custom_zoom(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map(zoom=10)
            self.assertIsInstance(m, keplergl.KeplerGl)
            self.assertEqual(m.config["config"]["mapState"]["zoom"], 10)

    def test_map_init_custom_height_width(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map(height=800, width=1000)
            self.assertIsInstance(m, keplergl.KeplerGl)
            self.assertEqual(m.config["config"]["mapState"]["height"], 800)
            self.assertEqual(m.config["config"]["mapState"]["width"], 1000)

    def test_map_init_height_width_with_px(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map(height="800px", width="1000px")
            self.assertEqual(m.config["config"]["mapState"]["height"], "800")
            self.assertEqual(m.config["config"]["mapState"]["width"], "1000")

    def test_map_init_pitch_bearing(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map(pitch=45, bearing=90)
            self.assertEqual(m.config["config"]["mapState"]["pitch"], 45)
            self.assertEqual(m.config["config"]["mapState"]["bearing"], 90)

    def test_map_init_drag_rotate(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map(dragRotate=True)
            self.assertTrue(m.config["config"]["mapState"]["dragRotate"])

    def test_map_init_is_split(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map(isSplit=True)
            self.assertTrue(m.config["config"]["mapState"]["isSplit"])


@unittest.skipUnless(KEPLERGL_AVAILABLE, "keplergl not available")
class TestAddGeojson(KeplerTestCase):

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
            m = self.kepler.Map()
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

            m = self.kepler.Map()
            m.add_geojson(temp_path, layer_name="Test File")

    def test_add_geojson_file_not_found_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map()
            with self.assertRaises(Exception):
                m.add_geojson("/nonexistent/path/file.geojson")

    def test_add_geojson_invalid_type_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map()
            with self.assertRaises(Exception):
                m.add_geojson(12345)


@unittest.skipUnless(KEPLERGL_AVAILABLE, "keplergl not available")
class TestAddShapefile(KeplerTestCase):

    def test_add_shapefile_not_found_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map()
            with self.assertRaises(FileNotFoundError):
                m.add_shp("/nonexistent/path/file.shp")


@unittest.skipUnless(KEPLERGL_AVAILABLE, "keplergl not available")
class TestAddDf(KeplerTestCase):

    def test_add_df_valid(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map()
            df = pd.DataFrame(
                {
                    "latitude": [37.8, 37.7],
                    "longitude": [-122.4, -122.3],
                    "value": [1.0, 0.5],
                }
            )
            m.add_df(df, layer_name="Test DataFrame")


@unittest.skipUnless(KEPLERGL_AVAILABLE, "keplergl not available")
class TestAddCsv(KeplerTestCase):

    def test_add_csv_valid(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            df = pd.DataFrame(
                {
                    "latitude": [37.8, 37.7],
                    "longitude": [-122.4, -122.3],
                    "value": [1.0, 0.5],
                }
            )
            temp_path = os.path.join(self.temp_dir, "test.csv")
            df.to_csv(temp_path, index=False)

            m = self.kepler.Map()
            m.add_csv(temp_path, layer_name="Test CSV")


@unittest.skipUnless(KEPLERGL_AVAILABLE, "keplergl not available")
class TestAddVector(KeplerTestCase):

    def test_add_vector_shp_not_found_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map()
            with self.assertRaises(FileNotFoundError):
                m.add_vector("/nonexistent/path/file.shp")

    def test_add_vector_geojson_not_found_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map()
            with self.assertRaises(Exception):
                m.add_vector("/nonexistent/path/file.geojson")


@unittest.skipUnless(KEPLERGL_AVAILABLE, "keplergl not available")
class TestAddKml(KeplerTestCase):

    def test_add_kml_not_found_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map()
            with self.assertRaises(FileNotFoundError):
                m.add_kml("/nonexistent/path/file.kml")


@unittest.skipUnless(KEPLERGL_AVAILABLE, "keplergl not available")
class TestToHtml(KeplerTestCase):

    def test_to_html_returns_string(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map()
            html = m.to_html()
            self.assertIsInstance(html, str)

    def test_to_html_saves_file(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map()
            temp_path = os.path.join(self.temp_dir, "test_map.html")
            m.to_html(temp_path)
            self.assertTrue(os.path.exists(temp_path))

    def test_to_html_invalid_extension_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map()
            temp_path = os.path.join(self.temp_dir, "test_map.txt")
            with self.assertRaises(ValueError) as ctx:
                m.to_html(temp_path)
            self.assertIn("html", str(ctx.exception))


@unittest.skipUnless(KEPLERGL_AVAILABLE, "keplergl not available")
class TestLoadConfig(KeplerTestCase):

    def test_load_config_none(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map()
            m.load_config(None)

    def test_load_config_dict(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map()
            config = {"version": "v1", "config": {"mapState": {}}}
            m.load_config(config)
            self.assertEqual(m.config, config)

    def test_load_config_from_file(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            config = {"version": "v1", "config": {"mapState": {"zoom": 5}}}
            temp_path = os.path.join(self.temp_dir, "config.json")
            with open(temp_path, "w") as f:
                json.dump(config, f)

            m = self.kepler.Map()
            m.load_config(temp_path)
            self.assertEqual(m.config["config"]["mapState"]["zoom"], 5)

    def test_load_config_file_not_found_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map()
            with self.assertRaises(FileNotFoundError):
                m.load_config("/nonexistent/path/config.json")

    def test_load_config_invalid_type_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map()
            with self.assertRaises(TypeError):
                m.load_config(12345)


@unittest.skipUnless(KEPLERGL_AVAILABLE, "keplergl not available")
class TestSaveConfig(KeplerTestCase):

    def test_save_config_valid(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map()
            temp_path = os.path.join(self.temp_dir, "saved_config.json")
            m.save_config(temp_path)
            self.assertTrue(os.path.exists(temp_path))

            with open(temp_path) as f:
                saved_config = json.load(f)
            self.assertEqual(saved_config["version"], "v1")

    def test_save_config_invalid_extension_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map()
            temp_path = os.path.join(self.temp_dir, "config.txt")
            with self.assertRaises(ValueError) as ctx:
                m.save_config(temp_path)
            self.assertIn("json", str(ctx.exception))

    def test_save_config_invalid_type_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.kepler.Map()
            with self.assertRaises(TypeError):
                m.save_config(12345)


@unittest.skipUnless(KEPLERGL_AVAILABLE, "keplergl not available")
class TestStaticMap(KeplerTestCase):

    def test_static_map_invalid_type_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            with self.assertRaises(TypeError):
                not_a_map = "not a map"
                self.kepler.Map.static_map(not_a_map)


if __name__ == "__main__":
    unittest.main()
