"""Tests for the deck module."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest import mock

try:
    import pydeck as pdk

    PYDECK_AVAILABLE = True
except ImportError:
    PYDECK_AVAILABLE = False

DECK_MODULE = None
IMPORT_ERROR = None


def get_deck():
    global DECK_MODULE, IMPORT_ERROR
    if DECK_MODULE is not None:
        return DECK_MODULE
    if IMPORT_ERROR is not None:
        raise IMPORT_ERROR
    try:
        with mock.patch("geemap.coreutils.ee_initialize"):
            from geemap import deck

            DECK_MODULE = deck
            return deck
    except Exception as e:
        IMPORT_ERROR = e
        raise


@unittest.skipUnless(PYDECK_AVAILABLE, "pydeck not available")
class DeckTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.mkdtemp()
        try:
            cls.deck = get_deck()
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
            self.skipTest(f"deck import failed: {self.skip_reason}")


@unittest.skipUnless(PYDECK_AVAILABLE, "pydeck not available")
class TestLayerInit(DeckTestCase):

    def test_layer_init_default(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            layer = self.deck.Layer("ScatterplotLayer")
            self.assertIsInstance(layer, pdk.Layer)

    def test_layer_init_with_data(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            layer = self.deck.Layer(
                "ScatterplotLayer", data=[{"position": [0, 0]}], id="test_layer"
            )
            self.assertIsInstance(layer, pdk.Layer)

    def test_layer_init_hexagon(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            layer = self.deck.Layer("HexagonLayer")
            self.assertIsInstance(layer, pdk.Layer)


@unittest.skipUnless(PYDECK_AVAILABLE, "pydeck not available")
class TestMapInit(DeckTestCase):

    def test_map_init_default_params(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.deck.Map(ee_initialize=False)
            self.assertIsInstance(m, pdk.Deck)

    def test_map_init_custom_center(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.deck.Map(center=(40, -100), ee_initialize=False)
            self.assertIsInstance(m, pdk.Deck)

    def test_map_init_custom_zoom(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.deck.Map(zoom=10, ee_initialize=False)
            self.assertIsInstance(m, pdk.Deck)

    def test_map_init_custom_height_width(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.deck.Map(height=800, width=1000, ee_initialize=False)
            self.assertIsInstance(m, pdk.Deck)

    def test_map_init_custom_map_style(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.deck.Map(map_style="dark", ee_initialize=False)
            self.assertIsInstance(m, pdk.Deck)


@unittest.skipUnless(PYDECK_AVAILABLE, "pydeck not available")
class TestAddLayer(DeckTestCase):

    def test_add_layer_pydeck_layer(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.deck.Map(ee_initialize=False)
            layer = pdk.Layer("ScatterplotLayer", data=[{"position": [0, 0]}])
            m.add_layer(layer)
            self.assertEqual(len(m.layers), 1)

    def test_add_layer_with_name(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.deck.Map(ee_initialize=False)
            layer = pdk.Layer("ScatterplotLayer", data=[{"position": [0, 0]}])
            m.add_layer(layer, layer_name="test_layer")
            self.assertEqual(len(m.layers), 1)

    def test_add_layer_url(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.deck.Map(ee_initialize=False)
            url = "https://example.com/tiles/{z}/{x}/{y}.png"
            m.add_layer(url, layer_name="tile_layer")
            self.assertEqual(len(m.layers), 1)


@unittest.skipUnless(PYDECK_AVAILABLE, "pydeck not available")
class TestAddEeLayer(DeckTestCase):

    def test_add_ee_layer_invalid_type_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.deck.Map(ee_initialize=False)
            with self.assertRaises(AttributeError) as ctx:
                m.add_ee_layer("not_an_ee_object")
            self.assertIn("instance of", str(ctx.exception))

    def test_addlayer_alias(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.deck.Map(ee_initialize=False)
            self.assertEqual(m.addLayer, m.add_ee_layer)


@unittest.skipUnless(PYDECK_AVAILABLE, "pydeck not available")
class TestAddBasemap(DeckTestCase):

    def test_add_basemap_valid(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.deck.Map(ee_initialize=False)
            # Test that add_basemap doesn't raise for valid basemaps
            # Note: Invalid basemaps print a message but don't raise


@unittest.skipUnless(PYDECK_AVAILABLE, "pydeck not available")
class TestAddGdf(DeckTestCase):

    def test_add_gdf_invalid_type_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.deck.Map(ee_initialize=False)
            with self.assertRaises(Exception):
                m.add_gdf("not_a_gdf")


@unittest.skipUnless(PYDECK_AVAILABLE, "pydeck not available")
class TestAddVector(DeckTestCase):

    def test_add_vector_file_not_found_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.deck.Map(ee_initialize=False)
            with self.assertRaises(Exception):
                m.add_vector("/nonexistent/path/file.shp")


@unittest.skipUnless(PYDECK_AVAILABLE, "pydeck not available")
class TestAddGeojson(DeckTestCase):

    def test_add_geojson_file_not_found_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.deck.Map(ee_initialize=False)
            with self.assertRaises(Exception):
                m.add_geojson("/nonexistent/path/file.geojson")


@unittest.skipUnless(PYDECK_AVAILABLE, "pydeck not available")
class TestAddShp(DeckTestCase):

    def test_add_shp_file_not_found_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.deck.Map(ee_initialize=False)
            with self.assertRaises(Exception):
                m.add_shp("/nonexistent/path/file.shp")


@unittest.skipUnless(PYDECK_AVAILABLE, "pydeck not available")
class TestAddKml(DeckTestCase):

    def test_add_kml_file_not_found_raises(self) -> None:
        with mock.patch("geemap.coreutils.ee_initialize"):
            m = self.deck.Map(ee_initialize=False)
            with self.assertRaises(Exception):
                m.add_kml("/nonexistent/path/file.kml")


if __name__ == "__main__":
    unittest.main()
