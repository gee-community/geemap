#!/usr/bin/env python
"""Tests for `osm` module."""

import unittest
from unittest import mock

from geemap import osm


class TestOsm(unittest.TestCase):
    """Tests for osm."""

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_gdf_from_address(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.features.features_from_address.return_value = mock_gdf

        res = osm.osm_gdf_from_address("address", {"building": True}, 1000)

        mock_ox.features.features_from_address.assert_called_with(
            "address", {"building": True}, 1000
        )
        self.assertEqual(res, mock_gdf)

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_shp_from_address(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.features.features_from_address.return_value = mock_gdf

        osm.osm_shp_from_address("address", {"building": True}, "test.shp", 1000)

        mock_ox.features.features_from_address.assert_called_with(
            "address", {"building": True}, 1000
        )
        mock_gdf.to_file.assert_called_with("test.shp")

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_geojson_from_address(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.features.features_from_address.return_value = mock_gdf

        osm.osm_geojson_from_address(
            "address", {"building": True}, "test.geojson", 1000
        )
        mock_gdf.to_file.assert_called_with("test.geojson", driver="GeoJSON")

        mock_gdf.__geo_interface__ = {"type": "FeatureCollection"}
        res = osm.osm_geojson_from_address("address", {"building": True}, None, 1000)
        self.assertEqual(res, {"type": "FeatureCollection"})

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_gdf_from_place(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.features.features_from_place.return_value = mock_gdf

        res = osm.osm_gdf_from_place("place", {"building": True})

        mock_ox.features.features_from_place.assert_called_with(
            "place", {"building": True}, which_result=None
        )
        self.assertEqual(res, mock_gdf)

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_shp_from_place(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.features.features_from_place.return_value = mock_gdf

        osm.osm_shp_from_place("place", {"building": True}, "test.shp")

        mock_gdf.to_file.assert_called_with("test.shp")

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_geojson_from_place(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.features.features_from_place.return_value = mock_gdf

        osm.osm_geojson_from_place("place", {"building": True}, "test.geojson")
        mock_gdf.to_file.assert_called_with("test.geojson", driver="GeoJSON")

        mock_gdf.__geo_interface__ = {"type": "FeatureCollection"}
        res = osm.osm_geojson_from_place("place", {"building": True}, None)
        self.assertEqual(res, {"type": "FeatureCollection"})

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_gdf_from_point(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.features.features_from_point.return_value = mock_gdf

        res = osm.osm_gdf_from_point((1.0, 2.0), {"building": True}, 1000)

        mock_ox.features.features_from_point.assert_called_with(
            (1.0, 2.0), {"building": True}, 1000
        )
        self.assertEqual(res, mock_gdf)

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_shp_from_point(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.features.features_from_point.return_value = mock_gdf

        osm.osm_shp_from_point((1.0, 2.0), {"building": True}, "test.shp", 1000)

        mock_gdf.to_file.assert_called_with("test.shp")

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_geojson_from_point(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.features.features_from_point.return_value = mock_gdf

        osm.osm_geojson_from_point((1.0, 2.0), {"building": True}, "test.geojson", 1000)
        mock_gdf.to_file.assert_called_with("test.geojson", driver="GeoJSON")

        mock_gdf.__geo_interface__ = {"type": "FeatureCollection"}
        res = osm.osm_geojson_from_point((1.0, 2.0), {"building": True}, None, 1000)
        self.assertEqual(res, {"type": "FeatureCollection"})

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_gdf_from_polygon(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.features.features_from_polygon.return_value = mock_gdf

        res = osm.osm_gdf_from_polygon("polygon", {"building": True})

        mock_ox.features.features_from_polygon.assert_called_with(
            "polygon", {"building": True}
        )
        self.assertEqual(res, mock_gdf)

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_shp_from_polygon(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.features.features_from_polygon.return_value = mock_gdf

        osm.osm_shp_from_polygon("polygon", {"building": True}, "test.shp")

        mock_gdf.to_file.assert_called_with("test.shp")

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_geojson_from_polygon(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.features.features_from_polygon.return_value = mock_gdf

        osm.osm_geojson_from_polygon("polygon", {"building": True}, "test.geojson")
        mock_gdf.to_file.assert_called_with("test.geojson", driver="GeoJSON")

        mock_gdf.__geo_interface__ = {"type": "FeatureCollection"}
        res = osm.osm_geojson_from_polygon("polygon", {"building": True}, None)
        self.assertEqual(res, {"type": "FeatureCollection"})

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_gdf_from_bbox(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.features.features_from_bbox.return_value = mock_gdf

        res = osm.osm_gdf_from_bbox(1.0, 2.0, 3.0, 4.0, {"building": True})

        mock_ox.features.features_from_bbox.assert_called_with(
            (1.0, 2.0, 3.0, 4.0), {"building": True}
        )
        self.assertEqual(res, mock_gdf)

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_shp_from_bbox(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.features.features_from_bbox.return_value = mock_gdf

        osm.osm_shp_from_bbox(1.0, 2.0, 3.0, 4.0, {"building": True}, "test.shp")

        mock_gdf.to_file.assert_called_with("test.shp")

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_geojson_from_bbox(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.features.features_from_bbox.return_value = mock_gdf

        osm.osm_geojson_from_bbox(
            1.0, 2.0, 3.0, 4.0, {"building": True}, "test.geojson"
        )
        mock_gdf.to_file.assert_called_with("test.geojson", driver="GeoJSON")

        mock_gdf.__geo_interface__ = {"type": "FeatureCollection"}
        res = osm.osm_geojson_from_bbox(1.0, 2.0, 3.0, 4.0, {"building": True}, None)
        self.assertEqual(res, {"type": "FeatureCollection"})

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_gdf_from_xml(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.features.features_from_xml.return_value = mock_gdf

        res = osm.osm_gdf_from_xml(
            "test.xml", polygon="polygon", tags={"building": True}
        )

        mock_ox.features.features_from_xml.assert_called_with(
            "test.xml", polygon="polygon", tags={"building": True}
        )
        self.assertEqual(res, mock_gdf)

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_gdf_from_geocode(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.geocoder.geocode_to_gdf.return_value = mock_gdf

        res = osm.osm_gdf_from_geocode("query", which_result=1, by_osmid=True)

        mock_ox.geocoder.geocode_to_gdf.assert_called_with(
            "query", which_result=1, by_osmid=True
        )
        self.assertEqual(res, mock_gdf)

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_shp_from_geocode(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.geocoder.geocode_to_gdf.return_value = mock_gdf

        osm.osm_shp_from_geocode("query", "test.shp", which_result=1, by_osmid=True)

        mock_gdf.to_file.assert_called_with("test.shp")

    @mock.patch.object(osm, "ox", create=True)
    def test_osm_geojson_from_geocode(self, mock_ox):
        mock_gdf = mock.MagicMock()
        mock_ox.geocoder.geocode_to_gdf.return_value = mock_gdf

        osm.osm_geojson_from_geocode(
            "query", "test.geojson", which_result=1, by_osmid=True
        )
        mock_gdf.to_file.assert_called_with("test.geojson", driver="GeoJSON")

        mock_gdf.__geo_interface__ = {"type": "FeatureCollection"}
        res = osm.osm_geojson_from_geocode("query", None, which_result=1, by_osmid=True)
        self.assertEqual(res, {"type": "FeatureCollection"})

    @mock.patch.object(osm.webbrowser, "open_new_tab")
    def test_osm_tags_list(self, mock_open):
        osm.osm_tags_list()
        mock_open.assert_called_with("https://wiki.openstreetmap.org/wiki/Map_features")


if __name__ == "__main__":
    unittest.main()
