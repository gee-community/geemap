"""Tests for the osm module."""

from __future__ import annotations

import sys
import unittest
from unittest import mock

from shapely.geometry import Polygon

from tests.mocks.mock_osmnx import MockGeoDataFrame

mock_ox = mock.MagicMock()
mock_ox.features = mock.MagicMock()
mock_ox.geocoder = mock.MagicMock()
sys.modules["osmnx"] = mock_ox

from geemap import osm


class TestOsmGdfFromAddress(unittest.TestCase):

    def setUp(self) -> None:
        mock_ox.reset_mock()

    def test_osm_gdf_from_address_valid_input(self) -> None:
        mock_gdf = MockGeoDataFrame(geometry=[mock.Mock()], data={"name": ["Test"]})
        mock_ox.features.features_from_address.return_value = mock_gdf
        result = osm.osm_gdf_from_address("New York", {"building": True})
        self.assertIsNotNone(result)
        mock_ox.features.features_from_address.assert_called_once_with(
            "New York", {"building": True}, 1000
        )

    def test_osm_gdf_from_address_custom_distance(self) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_ox.features.features_from_address.return_value = mock_gdf
        osm.osm_gdf_from_address("Paris", {"amenity": True}, dist=500)
        mock_ox.features.features_from_address.assert_called_with(
            "Paris", {"amenity": True}, 500
        )

    def test_osm_gdf_from_address_multiple_tags(self) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_ox.features.features_from_address.return_value = mock_gdf
        tags = {"building": True, "landuse": ["retail", "commercial"]}
        osm.osm_gdf_from_address("London", tags)
        mock_ox.features.features_from_address.assert_called_with("London", tags, 1000)


class TestOsmShpFromAddress(unittest.TestCase):

    @mock.patch("geemap.osm.osm_gdf_from_address")
    def test_osm_shp_from_address_creates_file(self, mock_gdf_func: mock.Mock) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf.to_file = mock.Mock()
        mock_gdf_func.return_value = mock_gdf
        osm.osm_shp_from_address("Berlin", {"highway": True}, "/tmp/test.shp")
        mock_gdf.to_file.assert_called_once_with("/tmp/test.shp")

    @mock.patch("geemap.osm.osm_gdf_from_address")
    def test_osm_shp_from_address_passes_distance(
        self, mock_gdf_func: mock.Mock
    ) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf.to_file = mock.Mock()
        mock_gdf_func.return_value = mock_gdf
        osm.osm_shp_from_address(
            "Tokyo", {"building": True}, "/tmp/test.shp", dist=2000
        )
        mock_gdf_func.assert_called_once_with("Tokyo", {"building": True}, 2000)


class TestOsmGeojsonFromAddress(unittest.TestCase):

    @mock.patch("geemap.osm.osm_gdf_from_address")
    def test_osm_geojson_from_address_returns_dict(
        self, mock_gdf_func: mock.Mock
    ) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf_func.return_value = mock_gdf
        result = osm.osm_geojson_from_address("Sydney", {"building": True})
        self.assertIsInstance(result, dict)
        self.assertEqual(result["type"], "FeatureCollection")

    @mock.patch("geemap.osm.osm_gdf_from_address")
    def test_osm_geojson_from_address_writes_file(
        self, mock_gdf_func: mock.Mock
    ) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf.to_file = mock.Mock()
        mock_gdf_func.return_value = mock_gdf
        result = osm.osm_geojson_from_address(
            "Melbourne", {"building": True}, filepath="/tmp/test.geojson"
        )
        mock_gdf.to_file.assert_called_once_with("/tmp/test.geojson", driver="GeoJSON")
        self.assertIsNone(result)

    @mock.patch("geemap.osm.osm_gdf_from_address")
    def test_osm_geojson_from_address_none_filepath(
        self, mock_gdf_func: mock.Mock
    ) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf_func.return_value = mock_gdf
        result = osm.osm_geojson_from_address("Rome", {"highway": True}, filepath=None)
        self.assertIsNotNone(result)


class TestOsmGdfFromPlace(unittest.TestCase):

    def setUp(self) -> None:
        mock_ox.reset_mock()

    def test_osm_gdf_from_place_valid_input(self) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_ox.features.features_from_place.return_value = mock_gdf
        result = osm.osm_gdf_from_place("Manhattan, NY", {"building": True})
        self.assertIsNotNone(result)
        mock_ox.features.features_from_place.assert_called()

    def test_osm_gdf_from_place_with_which_result(self) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_ox.features.features_from_place.return_value = mock_gdf
        osm.osm_gdf_from_place("Brooklyn, NY", {"landuse": True}, which_result=1)
        mock_ox.features.features_from_place.assert_called_with(
            "Brooklyn, NY", {"landuse": True}, which_result=1
        )


class TestOsmShpFromPlace(unittest.TestCase):

    @mock.patch("geemap.osm.osm_gdf_from_place")
    def test_osm_shp_from_place_creates_file(self, mock_gdf_func: mock.Mock) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf.to_file = mock.Mock()
        mock_gdf_func.return_value = mock_gdf
        osm.osm_shp_from_place("Queens, NY", {"highway": True}, "/tmp/test.shp")
        mock_gdf.to_file.assert_called_once_with("/tmp/test.shp")


class TestOsmGeojsonFromPlace(unittest.TestCase):

    @mock.patch("geemap.osm.osm_gdf_from_place")
    def test_osm_geojson_from_place_returns_dict(
        self, mock_gdf_func: mock.Mock
    ) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf_func.return_value = mock_gdf
        result = osm.osm_geojson_from_place("Bronx, NY", {"building": True})
        self.assertIsInstance(result, dict)

    @mock.patch("geemap.osm.osm_gdf_from_place")
    def test_osm_geojson_from_place_writes_file(self, mock_gdf_func: mock.Mock) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf.to_file = mock.Mock()
        mock_gdf_func.return_value = mock_gdf
        osm.osm_geojson_from_place(
            "Staten Island, NY", {"building": True}, filepath="/tmp/test.geojson"
        )
        mock_gdf.to_file.assert_called_once_with("/tmp/test.geojson", driver="GeoJSON")


class TestOsmGdfFromPoint(unittest.TestCase):

    def setUp(self) -> None:
        mock_ox.reset_mock()

    def test_osm_gdf_from_point_valid_coords(self) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_ox.features.features_from_point.return_value = mock_gdf
        result = osm.osm_gdf_from_point((40.7128, -74.0060), {"building": True})
        self.assertIsNotNone(result)
        mock_ox.features.features_from_point.assert_called_with(
            (40.7128, -74.0060), {"building": True}, 1000
        )

    def test_osm_gdf_from_point_custom_distance(self) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_ox.features.features_from_point.return_value = mock_gdf
        osm.osm_gdf_from_point((51.5074, -0.1278), {"amenity": True}, dist=500)
        mock_ox.features.features_from_point.assert_called_with(
            (51.5074, -0.1278), {"amenity": True}, 500
        )

    def test_osm_gdf_from_point_zero_coords(self) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_ox.features.features_from_point.return_value = mock_gdf
        osm.osm_gdf_from_point((0.0, 0.0), {"building": True})
        mock_ox.features.features_from_point.assert_called()


class TestOsmShpFromPoint(unittest.TestCase):

    @mock.patch("geemap.osm.osm_gdf_from_point")
    def test_osm_shp_from_point_creates_file(self, mock_gdf_func: mock.Mock) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf.to_file = mock.Mock()
        mock_gdf_func.return_value = mock_gdf
        osm.osm_shp_from_point((48.8566, 2.3522), {"building": True}, "/tmp/test.shp")
        mock_gdf.to_file.assert_called_once_with("/tmp/test.shp")


class TestOsmGeojsonFromPoint(unittest.TestCase):

    @mock.patch("geemap.osm.osm_gdf_from_point")
    def test_osm_geojson_from_point_returns_dict(
        self, mock_gdf_func: mock.Mock
    ) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf_func.return_value = mock_gdf
        result = osm.osm_geojson_from_point((35.6762, 139.6503), {"building": True})
        self.assertIsInstance(result, dict)

    @mock.patch("geemap.osm.osm_gdf_from_point")
    def test_osm_geojson_from_point_writes_file(self, mock_gdf_func: mock.Mock) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf.to_file = mock.Mock()
        mock_gdf_func.return_value = mock_gdf
        osm.osm_geojson_from_point(
            (35.6762, 139.6503), {"building": True}, filepath="/tmp/test.geojson"
        )
        mock_gdf.to_file.assert_called_once_with("/tmp/test.geojson", driver="GeoJSON")


class TestOsmGdfFromPolygon(unittest.TestCase):

    def setUp(self) -> None:
        mock_ox.reset_mock()

    def test_osm_gdf_from_polygon_valid_geom(self) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_ox.features.features_from_polygon.return_value = mock_gdf
        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        result = osm.osm_gdf_from_polygon(polygon, {"building": True})
        self.assertIsNotNone(result)
        mock_ox.features.features_from_polygon.assert_called_with(
            polygon, {"building": True}
        )

    def test_osm_gdf_from_polygon_multiple_tags(self) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_ox.features.features_from_polygon.return_value = mock_gdf
        polygon = Polygon([(-1, -1), (1, -1), (1, 1), (-1, 1)])
        tags = {"building": True, "highway": "primary"}
        osm.osm_gdf_from_polygon(polygon, tags)
        mock_ox.features.features_from_polygon.assert_called_with(polygon, tags)


class TestOsmShpFromPolygon(unittest.TestCase):

    @mock.patch("geemap.osm.osm_gdf_from_polygon")
    def test_osm_shp_from_polygon_creates_file(self, mock_gdf_func: mock.Mock) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf.to_file = mock.Mock()
        mock_gdf_func.return_value = mock_gdf
        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        osm.osm_shp_from_polygon(polygon, {"building": True}, "/tmp/test.shp")
        mock_gdf.to_file.assert_called_once_with("/tmp/test.shp")


class TestOsmGeojsonFromPolygon(unittest.TestCase):

    @mock.patch("geemap.osm.osm_gdf_from_polygon")
    def test_osm_geojson_from_polygon_returns_dict(
        self, mock_gdf_func: mock.Mock
    ) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf_func.return_value = mock_gdf
        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        result = osm.osm_geojson_from_polygon(polygon, {"building": True})
        self.assertIsInstance(result, dict)

    @mock.patch("geemap.osm.osm_gdf_from_polygon")
    def test_osm_geojson_from_polygon_writes_file(
        self, mock_gdf_func: mock.Mock
    ) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf.to_file = mock.Mock()
        mock_gdf_func.return_value = mock_gdf
        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        osm.osm_geojson_from_polygon(
            polygon, {"building": True}, filepath="/tmp/test.geojson"
        )
        mock_gdf.to_file.assert_called_once_with("/tmp/test.geojson", driver="GeoJSON")


class TestOsmGdfFromBbox(unittest.TestCase):

    def setUp(self) -> None:
        mock_ox.reset_mock()

    def test_osm_gdf_from_bbox_valid_bounds(self) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_ox.features.features_from_bbox.return_value = mock_gdf
        result = osm.osm_gdf_from_bbox(40.8, 40.7, -73.9, -74.0, {"building": True})
        self.assertIsNotNone(result)
        mock_ox.features.features_from_bbox.assert_called_with(
            (40.8, 40.7, -73.9, -74.0), {"building": True}
        )

    def test_osm_gdf_from_bbox_global_bounds(self) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_ox.features.features_from_bbox.return_value = mock_gdf
        osm.osm_gdf_from_bbox(90, -90, 180, -180, {"natural": True})
        mock_ox.features.features_from_bbox.assert_called()


class TestOsmShpFromBbox(unittest.TestCase):

    @mock.patch("geemap.osm.osm_gdf_from_bbox")
    def test_osm_shp_from_bbox_creates_file(self, mock_gdf_func: mock.Mock) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf.to_file = mock.Mock()
        mock_gdf_func.return_value = mock_gdf
        osm.osm_shp_from_bbox(
            40.8, 40.7, -73.9, -74.0, {"building": True}, "/tmp/test.shp"
        )
        mock_gdf.to_file.assert_called_once_with("/tmp/test.shp")


class TestOsmGeojsonFromBbox(unittest.TestCase):

    @mock.patch("geemap.osm.osm_gdf_from_bbox")
    def test_osm_geojson_from_bbox_returns_dict(self, mock_gdf_func: mock.Mock) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf_func.return_value = mock_gdf
        result = osm.osm_geojson_from_bbox(40.8, 40.7, -73.9, -74.0, {"building": True})
        self.assertIsInstance(result, dict)

    @mock.patch("geemap.osm.osm_gdf_from_bbox")
    def test_osm_geojson_from_bbox_writes_file(self, mock_gdf_func: mock.Mock) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf.to_file = mock.Mock()
        mock_gdf_func.return_value = mock_gdf
        osm.osm_geojson_from_bbox(
            40.8, 40.7, -73.9, -74.0, {"building": True}, filepath="/tmp/test.geojson"
        )
        mock_gdf.to_file.assert_called_once_with("/tmp/test.geojson", driver="GeoJSON")


class TestOsmGdfFromXml(unittest.TestCase):

    def setUp(self) -> None:
        mock_ox.reset_mock()

    def test_osm_gdf_from_xml_valid_file(self) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_ox.features.features_from_xml.return_value = mock_gdf
        result = osm.osm_gdf_from_xml("/path/to/file.xml")
        self.assertIsNotNone(result)
        mock_ox.features.features_from_xml.assert_called_with(
            "/path/to/file.xml", polygon=None, tags=None
        )

    def test_osm_gdf_from_xml_with_polygon(self) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_ox.features.features_from_xml.return_value = mock_gdf
        polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        osm.osm_gdf_from_xml("/path/to/file.xml", polygon=polygon)
        mock_ox.features.features_from_xml.assert_called_with(
            "/path/to/file.xml", polygon=polygon, tags=None
        )

    def test_osm_gdf_from_xml_with_tags(self) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_ox.features.features_from_xml.return_value = mock_gdf
        tags = {"building": True}
        osm.osm_gdf_from_xml("/path/to/file.xml", tags=tags)
        mock_ox.features.features_from_xml.assert_called_with(
            "/path/to/file.xml", polygon=None, tags=tags
        )


class TestOsmGdfFromGeocode(unittest.TestCase):

    def setUp(self) -> None:
        mock_ox.reset_mock()

    def test_osm_gdf_from_geocode_valid_query(self) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_ox.geocoder.geocode_to_gdf.return_value = mock_gdf
        result = osm.osm_gdf_from_geocode("New York City")
        self.assertIsNotNone(result)
        mock_ox.geocoder.geocode_to_gdf.assert_called_with(
            "New York City", which_result=None, by_osmid=False
        )

    def test_osm_gdf_from_geocode_with_which_result(self) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_ox.geocoder.geocode_to_gdf.return_value = mock_gdf
        osm.osm_gdf_from_geocode("Paris", which_result=1)
        mock_ox.geocoder.geocode_to_gdf.assert_called_with(
            "Paris", which_result=1, by_osmid=False
        )

    def test_osm_gdf_from_geocode_by_osmid(self) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_ox.geocoder.geocode_to_gdf.return_value = mock_gdf
        osm.osm_gdf_from_geocode("R123456", by_osmid=True)
        mock_ox.geocoder.geocode_to_gdf.assert_called_with(
            "R123456", which_result=None, by_osmid=True
        )


class TestOsmShpFromGeocode(unittest.TestCase):

    @mock.patch("geemap.osm.osm_gdf_from_geocode")
    def test_osm_shp_from_geocode_creates_file(self, mock_gdf_func: mock.Mock) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf.to_file = mock.Mock()
        mock_gdf_func.return_value = mock_gdf
        osm.osm_shp_from_geocode("London", "/tmp/test.shp")
        mock_gdf.to_file.assert_called_once_with("/tmp/test.shp")


class TestOsmGeojsonFromGeocode(unittest.TestCase):

    @mock.patch("geemap.osm.osm_gdf_from_geocode")
    def test_osm_geojson_from_geocode_returns_dict(
        self, mock_gdf_func: mock.Mock
    ) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf_func.return_value = mock_gdf
        result = osm.osm_geojson_from_geocode("Tokyo")
        self.assertIsInstance(result, dict)

    @mock.patch("geemap.osm.osm_gdf_from_geocode")
    def test_osm_geojson_from_geocode_writes_file(
        self, mock_gdf_func: mock.Mock
    ) -> None:
        mock_gdf = MockGeoDataFrame()
        mock_gdf.to_file = mock.Mock()
        mock_gdf_func.return_value = mock_gdf
        osm.osm_geojson_from_geocode("Berlin", filepath="/tmp/test.geojson")
        mock_gdf.to_file.assert_called_once_with("/tmp/test.geojson", driver="GeoJSON")


class TestOsmTagsList(unittest.TestCase):

    @mock.patch("geemap.osm.webbrowser.open_new_tab")
    def test_osm_tags_list_opens_browser(self, mock_open: mock.Mock) -> None:
        osm.osm_tags_list()
        mock_open.assert_called_once_with(
            "https://wiki.openstreetmap.org/wiki/Map_features"
        )


if __name__ == "__main__":
    unittest.main()
