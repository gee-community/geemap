"""Tests for `basemaps` module."""

import os
import unittest
from unittest import mock

import folium
import ipyleaflet
import requests
import xyzservices

# TODO - Why can't we just import basemaps?
from geemap.basemaps import (
    OSM_ATTRIBUTION,
    OSM_MAX_NATIVE_ZOOM,
    OSM_REFERRER_POLICY,
    OSM_URL,
    TileLayer,
    basemap_to_tiles,
    configure_folium_tile_layer,
    configure_leaflet_tile_layer,
    custom_tiles,
    get_default_referrer_policy,
    get_qms,
    get_xyz_dict,
    search_qms,
    xyz_to_folium,
    xyz_to_leaflet,
    xyz_to_plotly,
)
from geemap import common


class TestCustomTiles(unittest.TestCase):

    def test_custom_tiles_types(self):
        """Tests that custom_tiles is a dict and contains expected keys."""
        self.assertIsInstance(custom_tiles, dict)
        expected_keys = ["xyz", "wms"]
        for key in custom_tiles:
            self.assertIn(key, expected_keys)

    def test_custom_tiles_xyz(self):
        """Tests that custom_tiles["xyz"] is a dict w/ expected keys/values."""
        tiles = custom_tiles["xyz"]
        self.assertIsInstance(tiles, dict)
        for _, value in tiles.items():
            self.assertIn("url", value)
            self.assertIn("attribution", value)
            self.assertIn("name", value)
            self.assertTrue(value["url"].startswith("http"))

    def test_custom_tiles_wms(self):
        """Tests that custom_tiles["wms"] is a dict w/ expected keys/values."""
        tiles = custom_tiles["wms"]
        self.assertIsInstance(tiles, dict)
        for _, value in tiles.items():
            self.assertIsInstance(value["url"], str)
            self.assertIsInstance(value["attribution"], str)
            self.assertIsInstance(value["name"], str)
            self.assertTrue(value["url"].startswith("http"))

    def test_openstreetmap_custom_tile_definition(self):
        """Tests that the custom OpenStreetMap entry uses standard URL and attribution."""
        osm = custom_tiles["xyz"]["OpenStreetMap"]
        self.assertEqual(osm["url"], OSM_URL)
        self.assertNotIn("{s}", osm["url"])
        self.assertEqual(osm["attribution"], OSM_ATTRIBUTION)
        self.assertIn("https://www.openstreetmap.org/copyright", osm["attribution"])
        self.assertEqual(osm["max_native_zoom"], OSM_MAX_NATIVE_ZOOM)


class TestReferrerPolicyAndTileConversion(unittest.TestCase):

    def test_get_default_referrer_policy(self):
        """Tests referrer policy detection for OpenStreetMap and non-OSM URLs."""
        self.assertEqual(get_default_referrer_policy(OSM_URL), OSM_REFERRER_POLICY)
        self.assertEqual(
            get_default_referrer_policy(
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            ),
            OSM_REFERRER_POLICY,
        )
        self.assertEqual(
            get_default_referrer_policy(
                "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"
            ),
            OSM_REFERRER_POLICY,
        )
        self.assertEqual(
            get_default_referrer_policy("OpenStreetMap"), OSM_REFERRER_POLICY
        )
        self.assertIsNone(get_default_referrer_policy(""))
        self.assertIsNone(
            get_default_referrer_policy(
                "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            )
        )
        self.assertIsNone(
            get_default_referrer_policy(
                "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
            )
        )
        self.assertIsNone(
            get_default_referrer_policy(
                "https://a.tile.opentopomap.org/{z}/{x}/{y}.png"
            )
        )
        self.assertIsNone(
            get_default_referrer_policy(
                "https://a.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png"
            )
        )
        self.assertIsNone(
            get_default_referrer_policy("https://notopenstreetmap.org/{z}/{x}/{y}.png")
        )

    def test_tile_layer_and_leaflet_configuration(self):
        """Tests TileLayer and configure_leaflet_tile_layer referrer policy behavior."""
        osm_layer = TileLayer()
        self.assertEqual(osm_layer.url, OSM_URL)
        self.assertEqual(osm_layer.referrer_policy, OSM_REFERRER_POLICY)
        self.assertIn("referrer_policy", osm_layer.options)

        custom_policy_layer = TileLayer(url=OSM_URL, referrer_policy="origin")
        self.assertEqual(custom_policy_layer.referrer_policy, "origin")

        non_osm_layer = TileLayer(url="https://example.com/{z}/{x}/{y}.png")
        self.assertIsNone(non_osm_layer.referrer_policy)

        plain_osm = ipyleaflet.TileLayer()
        configure_leaflet_tile_layer(plain_osm)
        self.assertEqual(
            getattr(plain_osm, "referrer_policy", None), OSM_REFERRER_POLICY
        )
        self.assertIn("referrer_policy", plain_osm.options)

        plain_non_osm = ipyleaflet.TileLayer(url="https://example.com/{z}/{x}/{y}.png")
        configure_leaflet_tile_layer(plain_non_osm)
        self.assertFalse(plain_non_osm.has_trait("referrer_policy"))

    def test_configure_folium_tile_layer(self):
        """Tests configure_folium_tile_layer for OpenStreetMap and non-OSM layers."""
        osm_folium = folium.TileLayer("OpenStreetMap")
        configure_folium_tile_layer(osm_folium)
        self.assertEqual(osm_folium.options.get("referrer_policy"), OSM_REFERRER_POLICY)

        non_osm_folium = folium.TileLayer(
            tiles="https://example.com/{z}/{x}/{y}.png", attr="Example"
        )
        configure_folium_tile_layer(non_osm_folium)
        self.assertNotIn("referrer_policy", non_osm_folium.options)

    def test_basemap_to_tiles(self):
        """Tests basemap_to_tiles across providers and custom dicts."""
        osm_provider = get_xyz_dict()["OpenStreetMap.Mapnik"]
        osm_tile = basemap_to_tiles(osm_provider, max_zoom=30, base=True)
        self.assertEqual(osm_tile.url, OSM_URL)
        self.assertEqual(osm_tile.attribution, OSM_ATTRIBUTION)
        self.assertTrue(osm_tile.base)
        self.assertEqual(osm_tile.max_zoom, 30)
        self.assertEqual(osm_tile.max_native_zoom, OSM_MAX_NATIVE_ZOOM)
        self.assertEqual(osm_tile.referrer_policy, OSM_REFERRER_POLICY)

        for provider in get_xyz_dict().values():
            layer = basemap_to_tiles(provider, max_zoom=30)
            self.assertIsInstance(layer, ipyleaflet.TileLayer)

        custom_dict = {
            "url": "https://example.com/{z}/{x}/{y}.png",
            "name": "Example",
            "attribution": "Example Attr",
            "min_zoom": None,
            "max_zoom": None,
        }
        custom_tile = basemap_to_tiles(custom_dict)
        self.assertEqual(custom_tile.min_zoom, 0)
        self.assertEqual(custom_tile.max_zoom, 24)
        self.assertIsNone(custom_tile.referrer_policy)

        with self.assertRaises(ValueError):
            basemap_to_tiles("invalid")


class TestXyzToLeaflet(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tiles = xyz_to_leaflet()

    def test_xyz_to_leaflet_is_dictionary(self):
        """Tests that xyz_to_leaflet returns a dict."""
        self.assertIsInstance(self.tiles, dict)

    def test_xyz_to_leaflet_sources(self):
        """Tests that xyz_to_leaflet has custom xyz, wms, and xyzservices."""
        expected_keys = {
            "custom_xyz": "OpenStreetMap",
            "custom_wms": "USGS NAIP Imagery",
            "xyzservices_xyz": "Esri.WorldTopoMap",
        }
        for _, expected_name in expected_keys.items():
            self.assertIn(expected_name, self.tiles)

    def test_xyz_to_leaflet_openstreetmap_metadata(self):
        """Tests OpenStreetMap URL, HTML attribution, and zoom metadata in xyz_to_leaflet."""
        for key in ("OpenStreetMap", "OpenStreetMap.Mapnik"):
            info = self.tiles[key]
            self.assertEqual(info["url"], OSM_URL)
            self.assertEqual(info["attribution"], OSM_ATTRIBUTION)
            self.assertEqual(info["max_zoom"], 30)
            self.assertEqual(info["max_native_zoom"], OSM_MAX_NATIVE_ZOOM)


class TestXyzToFolium(unittest.TestCase):

    def test_xyz_to_folium_sources(self):
        """Tests that xyz_to_folium has custom xyz, wms, and xyzservices."""
        tiles = xyz_to_folium()
        self.assertIn("OpenStreetMap", tiles)  # custom xyz
        self.assertIn("FWS NWI Wetlands", tiles)  # custom wms
        self.assertIn("OpenTopoMap", tiles)  # xyzservices

        for name, tile_layer in tiles.items():
            if name in custom_tiles["wms"]:
                self.assertIsInstance(tile_layer, folium.WmsTileLayer)
            else:
                self.assertIsInstance(tile_layer, folium.TileLayer)

        for key in ("OpenStreetMap", "OpenStreetMap.Mapnik"):
            osm_layer = tiles[key]
            self.assertEqual(osm_layer.tiles, OSM_URL)
            self.assertEqual(osm_layer.options["attribution"], OSM_ATTRIBUTION)
            self.assertEqual(osm_layer.options["max_zoom"], 30)
            self.assertEqual(osm_layer.options["max_native_zoom"], OSM_MAX_NATIVE_ZOOM)
            self.assertEqual(osm_layer.options["referrer_policy"], OSM_REFERRER_POLICY)

        self.assertNotIn("referrer_policy", tiles["OpenTopoMap"].options)
        self.assertNotIn("referrer_policy", tiles["ROADMAP"].options)

    @mock.patch.dict(os.environ, {"PLANET_API_KEY": "fake_api_key"})
    @mock.patch.object(common, "planet_tiles")
    def test_xyz_to_folium_with_planet(self, mock_planet_tiles):
        """Tests that xyz_to_folium includes planet tiles if API key is set."""
        mock_planet_tiles.return_value = {
            "Planet Basemap": folium.TileLayer(
                tiles="https://fake-planet.com/tiles/{z}/{x}/{y}",
                attr="Planet",
                name="Planet Basemap",
            )
        }
        tiles = xyz_to_folium()
        self.assertIn("Planet Basemap", tiles)
        mock_planet_tiles.assert_called_once_with(tile_format="folium")


class FakeProvider(xyzservices.TileProvider):

    def __init__(self, name: str, url: str):
        super().__init__(
            name=name,
            url=url,
            attribution="&copy; Fake Provider",
            accessToken="<insert your access token here>",
        )


class FakeXyz(xyzservices.Bunch):

    def __init__(self):
        token = "https://fake-server.com/tiles/{z}/{x}/{y}?apikey={accessToken}"
        no_token = "https://fake-server.com/tiles/{z}/{x}/{y}"

        self.fake_tile_a = FakeProvider("a", no_token)
        self.fake_tile_b = FakeProvider("b", token)
        self.fake_tile_c_1 = FakeProvider("c_1", no_token)
        self.fake_tile_c_France = FakeProvider("c_France", no_token)

        self.providers = xyzservices.Bunch(
            a=self.fake_tile_a,
            b=self.fake_tile_b,
            c=xyzservices.Bunch(c_1=self.fake_tile_c_1, c_2=self.fake_tile_c_France),
        )


@mock.patch.object(xyzservices, "providers", FakeXyz().providers)
class TestGetXyzDict(unittest.TestCase):

    def test_get_xyz_dict_structure(self):
        """Tests that get_xyz_dict returns correct object structure."""
        xyz_dict = get_xyz_dict()
        tile_a = xyz_dict["a"]
        tile_a_keys = tile_a.keys()

        self.assertEqual("c_1", list(xyz_dict.keys())[1])
        self.assertIsInstance(tile_a, xyzservices.lib.TileProvider)
        self.assertIn("name", tile_a_keys)
        self.assertIn("url", tile_a_keys)
        self.assertIn("attribution", tile_a_keys)
        self.assertIn("accessToken", tile_a_keys)
        self.assertEqual("xyz", tile_a["type"])
        self.assertEqual("a", tile_a.name)
        self.assertEqual(
            "https://fake-server.com/tiles/{z}/{x}/{y}", tile_a.build_url()
        )

    def test_get_xyz_dict_free_tiles(self):
        """Tests that get_xyz_dict correctly filters for free tile layers."""
        xyz_dict_free = get_xyz_dict(free_only=True)
        xyz_dict_all = get_xyz_dict(free_only=False)

        self.assertNotIn("b", xyz_dict_free.keys())
        self.assertIn("b", xyz_dict_all.keys())

    def test_get_xyz_dict_france_tiles(self):
        """Tests that get_xyz_dict correctly filters for France tile layers."""
        xyz_dict_all = get_xyz_dict(france=True)
        xyz_dict_no_france = get_xyz_dict(france=False)

        self.assertNotIn("c_France", xyz_dict_no_france.keys())
        self.assertIn("c_France", xyz_dict_all.keys())


class TestXyzToPlotly(unittest.TestCase):

    def test_xyz_to_plotly_sources(self):
        """Tests that xyz_to_plotly has custom xyz and xyzservices."""
        tiles = xyz_to_plotly()
        self.assertIn("OpenStreetMap", tiles)  # custom xyz
        self.assertIn("OpenTopoMap", tiles)  # xyzservices

        for _, tile_layer in tiles.items():
            self.assertIn("below", tile_layer)
            self.assertIn("sourcetype", tile_layer)
            self.assertEqual("raster", tile_layer["sourcetype"])
            self.assertIn("source", tile_layer)
            self.assertIsInstance(tile_layer["source"], list)


class TestQms(unittest.TestCase):

    @mock.patch.object(requests, "get")
    def test_search_qms_no_results(self, mock_get):
        """Tests search_qms with no results."""
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"count": 0, "results": []}
        result = search_qms("no results")
        self.assertIsNone(result)
        mock_get.assert_called_once_with(
            "https://qms.nextgis.com/api/v1/geoservices/?search=no results&type=tms&epsg=3857&limit=10"
        )

    @mock.patch.object(requests, "get")
    def test_search_qms_with_results(self, mock_get):
        """Tests search_qms with results."""
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
            "count": 1,
            "results": [{"id": 1, "name": "result1"}],
        }
        result = search_qms("results")
        self.assertEqual(result, [{"id": 1, "name": "result1"}])
        mock_get.assert_called_once_with(
            "https://qms.nextgis.com/api/v1/geoservices/?search=results&type=tms&epsg=3857&limit=10"
        )

    @mock.patch.object(requests, "get")
    def test_search_qms_with_limit(self, mock_get):
        """Tests search_qms with limit."""
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
            "count": 1,
            "results": [{"id": 1, "name": "result1"}],
        }
        result = search_qms("results", limit=5)
        self.assertEqual(result, [{"id": 1, "name": "result1"}])
        mock_get.assert_called_once_with(
            "https://qms.nextgis.com/api/v1/geoservices/?search=results&type=tms&epsg=3857&limit=5"
        )

    @mock.patch.object(requests, "get")
    def test_search_qms_count_greater_than_limit(self, mock_get):
        """Tests search_qms with count > limit."""
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
            "count": 2,
            "results": [{"id": 1, "name": "result1"}, {"id": 2, "name": "result2"}],
        }
        result = search_qms("results", limit=1)
        self.assertEqual(result, [{"id": 1, "name": "result1"}])
        mock_get.assert_called_once_with(
            "https://qms.nextgis.com/api/v1/geoservices/?search=results&type=tms&epsg=3857&limit=1"
        )

    @mock.patch.object(requests, "get")
    def test_get_qms(self, mock_get):
        """Tests get_qms."""
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"id": 123, "name": "service1"}
        result = get_qms("123")
        self.assertEqual(result, {"id": 123, "name": "service1"})
        mock_get.assert_called_once_with(
            "https://qms.nextgis.com/api/v1/geoservices/123"
        )


if __name__ == "__main__":
    unittest.main()
