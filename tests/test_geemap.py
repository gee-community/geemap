#!/usr/bin/env python
"""Tests for `geemap` package."""

import unittest
from unittest import mock

import geemap
from geemap.basemaps import (
    OSM_ATTRIBUTION,
    OSM_MAX_NATIVE_ZOOM,
    OSM_REFERRER_POLICY,
    OSM_URL,
    get_xyz_dict,
)
from geemap import coreutils
from geemap import foliumap
import ipyleaflet


class TestGeemap(unittest.TestCase):
    """Tests for `geemap` package."""

    @mock.patch.object(coreutils, "get_google_maps_api_key", return_value=None)
    def test_map_default_basemap_and_controls(self, unused_mock_api_key):
        """Tests default Map basemap metadata and attribution_ctrl handling."""
        m = geemap.Map(ee_initialize=False)
        self.assertIsInstance(m, ipyleaflet.Map)
        base_layer = m.layers[0]
        self.assertEqual(base_layer.url, OSM_URL)
        self.assertEqual(base_layer.attribution, OSM_ATTRIBUTION)
        self.assertTrue(base_layer.base)
        self.assertEqual(base_layer.max_zoom, 30)
        self.assertEqual(base_layer.max_native_zoom, OSM_MAX_NATIVE_ZOOM)
        self.assertEqual(
            getattr(base_layer, "referrer_policy", None),
            OSM_REFERRER_POLICY,
        )

        m_no_attr = geemap.Map(
            ee_initialize=False, toolbar_ctrl=False, attribution_ctrl=False
        )
        self.assertFalse(
            any(
                isinstance(c, ipyleaflet.AttributionControl) for c in m_no_attr.controls
            )
        )
        m_no_attr.add("attribution_ctrl")
        self.assertTrue(
            any(
                isinstance(c, ipyleaflet.AttributionControl) for c in m_no_attr.controls
            )
        )

    @mock.patch.object(coreutils, "get_google_maps_api_key", return_value=None)
    def test_map_construction_variants(self, unused_mock_api_key):
        """Tests Map construction across lite_mode, basemap names, and WMS."""
        lite_map = geemap.Map(ee_initialize=False, lite_mode=True)
        self.assertEqual(
            getattr(lite_map.layers[0], "referrer_policy", None),
            OSM_REFERRER_POLICY,
        )

        osm_map = geemap.Map(ee_initialize=False, basemap="OpenStreetMap")
        self.assertEqual(osm_map.layers[0].url, OSM_URL)
        self.assertEqual(osm_map.layers[0].attribution, OSM_ATTRIBUTION)
        self.assertTrue(osm_map.layers[0].base)

        wms_map = geemap.Map(ee_initialize=False, basemap="USGS NAIP Imagery")
        self.assertIsInstance(wms_map.layers[0], ipyleaflet.WMSLayer)

        grid = geemap.linked_maps(rows=1, cols=2, ee_initialize=False)
        self.assertIsNotNone(grid)

    @mock.patch.object(coreutils, "get_google_maps_api_key", return_value=None)
    def test_basemap_addition_and_update_methods(self, unused_mock_api_key):
        """Tests add_basemap, add, get_basemap, add_tile_layer, and split_map."""
        m = geemap.Map(ee_initialize=False, basemap="HYBRID")
        self.assertIsNone(getattr(m.layers[0], "referrer_policy", None))

        m.add_basemap("OpenStreetMap")
        osm_layer = m.layers[-1]
        self.assertEqual(osm_layer.url, OSM_URL)
        self.assertEqual(osm_layer.attribution, OSM_ATTRIBUTION)
        self.assertEqual(osm_layer.max_zoom, 30)
        self.assertEqual(osm_layer.max_native_zoom, OSM_MAX_NATIVE_ZOOM)
        self.assertEqual(
            getattr(osm_layer, "referrer_policy", None),
            OSM_REFERRER_POLICY,
        )

        m.add_basemap("OpenStreetMap.Mapnik")
        mapnik_layer = m.layers[-1]
        self.assertEqual(mapnik_layer.url, OSM_URL)
        self.assertEqual(mapnik_layer.attribution, OSM_ATTRIBUTION)
        self.assertEqual(mapnik_layer.max_zoom, 30)
        self.assertEqual(mapnik_layer.max_native_zoom, OSM_MAX_NATIVE_ZOOM)
        self.assertEqual(
            getattr(mapnik_layer, "referrer_policy", None),
            OSM_REFERRER_POLICY,
        )

        provider = get_xyz_dict()["OpenStreetMap.Mapnik"]
        m.add_basemap(provider)
        self.assertEqual(m.layers[-1].max_zoom, 30)
        self.assertEqual(m.layers[-1].max_native_zoom, OSM_MAX_NATIVE_ZOOM)

        m2 = geemap.Map(ee_initialize=False, basemap="ROADMAP")
        m2.add("OpenStreetMap")
        self.assertEqual(
            getattr(m2.layers[-1], "referrer_policy", None),
            OSM_REFERRER_POLICY,
        )
        m2.set_options("HYBRID")
        self.assertEqual(m2.layers[-1].name, "Esri.WorldImagery")

        for bname in ("OpenStreetMap", "OpenStreetMap.Mapnik"):
            got = geemap.get_basemap(bname)
            self.assertEqual(got.url, OSM_URL)
            self.assertEqual(got.attribution, OSM_ATTRIBUTION)
            self.assertEqual(got.max_native_zoom, OSM_MAX_NATIVE_ZOOM)
            self.assertEqual(
                getattr(got, "referrer_policy", None),
                OSM_REFERRER_POLICY,
            )

        m2.add_tile_layer()
        default_tile = m2.layers[-1]
        self.assertEqual(default_tile.url, OSM_URL)
        self.assertEqual(default_tile.attribution, OSM_ATTRIBUTION)
        self.assertEqual(default_tile.max_native_zoom, OSM_MAX_NATIVE_ZOOM)
        self.assertEqual(
            getattr(default_tile, "referrer_policy", None),
            OSM_REFERRER_POLICY,
        )

        m2.add_tile_layer("https://example.com/{z}/{x}/{y}.png", name="Custom")
        custom_tile = m2.layers[-1]
        self.assertEqual(custom_tile.attribution, "")
        self.assertEqual(custom_tile.max_native_zoom, 100)
        self.assertIsNone(getattr(custom_tile, "referrer_policy", None))

        m3 = geemap.Map(ee_initialize=False)
        m3.split_map("OpenStreetMap", "HYBRID")
        split_controls = [
            c for c in m3.controls if isinstance(c, ipyleaflet.SplitMapControl)
        ]
        self.assertEqual(len(split_controls), 1)
        self.assertEqual(
            getattr(split_controls[0].left_layer, "referrer_policy", None),
            OSM_REFERRER_POLICY,
        )
        self.assertEqual(split_controls[0].right_layer.name, "Esri.WorldImagery")
        self.assertIsNone(
            getattr(split_controls[0].right_layer, "referrer_policy", None)
        )

    def test_foliumap_basemap_and_referrer_policy(self):
        """Tests foliumap.Map default, multiple instances, and basemap methods."""
        fmap1 = foliumap.Map(ee_initialize=False)
        fmap2 = foliumap.Map(ee_initialize=False)
        for fmap in (fmap1, fmap2):
            html = fmap.get_root().render()
            self.assertIn("tile.openstreetmap.org", html)
            self.assertIn("https://www.openstreetmap.org/copyright", html)
            self.assertIn(OSM_REFERRER_POLICY, html)

        non_osm_fmap = foliumap.Map(
            ee_initialize=False,
            tiles="CartoDB positron",
            add_google_map=False,
        )
        self.assertNotIn(
            OSM_REFERRER_POLICY,
            non_osm_fmap.get_root().render(),
        )

        non_osm_fmap.add_basemap("OpenStreetMap")
        non_osm_fmap.add_basemap("OpenStreetMap.Mapnik")
        non_osm_fmap.add_basemap(get_xyz_dict()["OpenStreetMap.Mapnik"])
        non_osm_fmap.add_tile_layer()
        rendered_after = non_osm_fmap.get_root().render()
        self.assertGreaterEqual(rendered_after.count(OSM_REFERRER_POLICY), 4)


if __name__ == "__main__":
    unittest.main()
