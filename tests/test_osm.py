import sys
import unittest
from unittest import mock

# osm.py imports osmnx at module level with a bare except. Inject a mock
# into sys.modules so the import succeeds without installing osmnx.
mock_ox = mock.MagicMock()
mock_ox.features = mock.MagicMock()
mock_ox.geocoder = mock.MagicMock()
sys.modules["osmnx"] = mock_ox

from geemap import osm


def _make_mock_gdf():
    """Create a mock GeoDataFrame with __geo_interface__."""
    gdf = mock.MagicMock()
    gdf.__geo_interface__ = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [0, 0]},
                "properties": {"name": "test"},
            }
        ],
    }
    return gdf


class OsmTest(unittest.TestCase):

    def setUp(self):
        mock_ox.reset_mock()

    def test_gdf_from_address_default_dist(self):
        mock_ox.features.features_from_address.return_value = _make_mock_gdf()
        osm.osm_gdf_from_address("New York", {"building": True})
        mock_ox.features.features_from_address.assert_called_once_with(
            "New York", {"building": True}, 1000
        )

    def test_gdf_from_address_custom_dist(self):
        mock_ox.features.features_from_address.return_value = _make_mock_gdf()
        osm.osm_gdf_from_address("Paris", {"amenity": True}, dist=500)
        mock_ox.features.features_from_address.assert_called_once_with(
            "Paris", {"amenity": True}, 500
        )

    def test_gdf_from_address_multiple_tags(self):
        mock_ox.features.features_from_address.return_value = _make_mock_gdf()
        tags = {"building": True, "landuse": ["retail", "commercial"]}
        osm.osm_gdf_from_address("London", tags)
        mock_ox.features.features_from_address.assert_called_once_with(
            "London", tags, 1000
        )

    @mock.patch.object(osm, "osm_gdf_from_address")
    def test_shp_from_address_calls_to_file(self, mock_gdf_func):
        gdf = _make_mock_gdf()
        mock_gdf_func.return_value = gdf
        osm.osm_shp_from_address("Berlin", {"highway": True}, "/tmp/test.shp")
        gdf.to_file.assert_called_once_with("/tmp/test.shp")

    @mock.patch.object(osm, "osm_gdf_from_address")
    def test_shp_from_address_passes_dist(self, mock_gdf_func):
        gdf = _make_mock_gdf()
        mock_gdf_func.return_value = gdf
        osm.osm_shp_from_address(
            "Tokyo", {"building": True}, "/tmp/test.shp", dist=2000
        )
        mock_gdf_func.assert_called_once_with("Tokyo", {"building": True}, 2000)

    @mock.patch.object(osm, "osm_gdf_from_address")
    def test_geojson_from_address_returns_dict(self, mock_gdf_func):
        mock_gdf_func.return_value = _make_mock_gdf()
        result = osm.osm_geojson_from_address("Sydney", {"building": True})
        self.assertIsInstance(result, dict)
        self.assertEqual(result["type"], "FeatureCollection")

    @mock.patch.object(osm, "osm_gdf_from_address")
    def test_geojson_from_address_writes_file(self, mock_gdf_func):
        gdf = _make_mock_gdf()
        mock_gdf_func.return_value = gdf
        result = osm.osm_geojson_from_address(
            "Melbourne", {"building": True}, filepath="/tmp/test.geojson"
        )
        gdf.to_file.assert_called_once_with("/tmp/test.geojson", driver="GeoJSON")
        self.assertIsNone(result)

    def test_gdf_from_place_valid_input(self):
        mock_ox.features.features_from_place.return_value = _make_mock_gdf()
        osm.osm_gdf_from_place("Manhattan, NY", {"building": True})
        mock_ox.features.features_from_place.assert_called_once_with(
            "Manhattan, NY", {"building": True}, which_result=None
        )

    def test_gdf_from_place_with_which_result(self):
        mock_ox.features.features_from_place.return_value = _make_mock_gdf()
        osm.osm_gdf_from_place("Brooklyn, NY", {"landuse": True}, which_result=1)
        mock_ox.features.features_from_place.assert_called_once_with(
            "Brooklyn, NY", {"landuse": True}, which_result=1
        )

    @mock.patch.object(osm, "osm_gdf_from_place")
    def test_shp_from_place_calls_to_file(self, mock_gdf_func):
        gdf = _make_mock_gdf()
        mock_gdf_func.return_value = gdf
        osm.osm_shp_from_place("Queens, NY", {"highway": True}, "/tmp/test.shp")
        gdf.to_file.assert_called_once_with("/tmp/test.shp")

    @mock.patch.object(osm, "osm_gdf_from_place")
    def test_geojson_from_place_returns_dict(self, mock_gdf_func):
        mock_gdf_func.return_value = _make_mock_gdf()
        result = osm.osm_geojson_from_place("Bronx, NY", {"building": True})
        self.assertIsInstance(result, dict)
        self.assertEqual(result["type"], "FeatureCollection")

    @mock.patch.object(osm, "osm_gdf_from_place")
    def test_geojson_from_place_writes_file(self, mock_gdf_func):
        gdf = _make_mock_gdf()
        mock_gdf_func.return_value = gdf
        osm.osm_geojson_from_place(
            "Staten Island, NY", {"building": True}, filepath="/tmp/test.geojson"
        )
        gdf.to_file.assert_called_once_with("/tmp/test.geojson", driver="GeoJSON")

    def test_gdf_from_point_default_dist(self):
        mock_ox.features.features_from_point.return_value = _make_mock_gdf()
        osm.osm_gdf_from_point((40.7128, -74.0060), {"building": True})
        mock_ox.features.features_from_point.assert_called_once_with(
            (40.7128, -74.0060), {"building": True}, 1000
        )

    def test_gdf_from_point_custom_dist(self):
        mock_ox.features.features_from_point.return_value = _make_mock_gdf()
        osm.osm_gdf_from_point((51.5074, -0.1278), {"amenity": True}, dist=500)
        mock_ox.features.features_from_point.assert_called_once_with(
            (51.5074, -0.1278), {"amenity": True}, 500
        )

    @mock.patch.object(osm, "osm_gdf_from_point")
    def test_shp_from_point_calls_to_file(self, mock_gdf_func):
        gdf = _make_mock_gdf()
        mock_gdf_func.return_value = gdf
        osm.osm_shp_from_point(
            (48.8566, 2.3522), {"building": True}, "/tmp/test.shp"
        )
        gdf.to_file.assert_called_once_with("/tmp/test.shp")

    @mock.patch.object(osm, "osm_gdf_from_point")
    def test_geojson_from_point_returns_dict(self, mock_gdf_func):
        mock_gdf_func.return_value = _make_mock_gdf()
        result = osm.osm_geojson_from_point(
            (35.6762, 139.6503), {"building": True}
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["type"], "FeatureCollection")

    @mock.patch.object(osm, "osm_gdf_from_point")
    def test_geojson_from_point_writes_file(self, mock_gdf_func):
        gdf = _make_mock_gdf()
        mock_gdf_func.return_value = gdf
        osm.osm_geojson_from_point(
            (34.0522, -118.2437),
            {"building": True},
            filepath="/tmp/test.geojson",
        )
        gdf.to_file.assert_called_once_with("/tmp/test.geojson", driver="GeoJSON")

    def test_gdf_from_polygon(self):
        from shapely import geometry

        mock_ox.features.features_from_polygon.return_value = _make_mock_gdf()
        polygon = geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        osm.osm_gdf_from_polygon(polygon, {"building": True})
        mock_ox.features.features_from_polygon.assert_called_once_with(
            polygon, {"building": True}
        )

    @mock.patch.object(osm, "osm_gdf_from_polygon")
    def test_shp_from_polygon_calls_to_file(self, mock_gdf_func):
        from shapely import geometry

        gdf = _make_mock_gdf()
        mock_gdf_func.return_value = gdf
        polygon = geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        osm.osm_shp_from_polygon(polygon, {"building": True}, "/tmp/test.shp")
        gdf.to_file.assert_called_once_with("/tmp/test.shp")

    @mock.patch.object(osm, "osm_gdf_from_polygon")
    def test_geojson_from_polygon_returns_dict(self, mock_gdf_func):
        from shapely import geometry

        mock_gdf_func.return_value = _make_mock_gdf()
        polygon = geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        result = osm.osm_geojson_from_polygon(polygon, {"building": True})
        self.assertIsInstance(result, dict)
        self.assertEqual(result["type"], "FeatureCollection")

    @mock.patch.object(osm, "osm_gdf_from_polygon")
    def test_geojson_from_polygon_writes_file(self, mock_gdf_func):
        from shapely import geometry

        gdf = _make_mock_gdf()
        mock_gdf_func.return_value = gdf
        polygon = geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        osm.osm_geojson_from_polygon(
            polygon, {"building": True}, filepath="/tmp/test.geojson"
        )
        gdf.to_file.assert_called_once_with("/tmp/test.geojson", driver="GeoJSON")

    def test_gdf_from_bbox(self):
        mock_ox.features.features_from_bbox.return_value = _make_mock_gdf()
        osm.osm_gdf_from_bbox(40.8, 40.7, -73.9, -74.0, {"building": True})
        mock_ox.features.features_from_bbox.assert_called_once_with(
            (40.8, 40.7, -73.9, -74.0), {"building": True}
        )

    @mock.patch.object(osm, "osm_gdf_from_bbox")
    def test_shp_from_bbox_calls_to_file(self, mock_gdf_func):
        gdf = _make_mock_gdf()
        mock_gdf_func.return_value = gdf
        osm.osm_shp_from_bbox(
            40.8, 40.7, -73.9, -74.0, {"building": True}, "/tmp/test.shp"
        )
        gdf.to_file.assert_called_once_with("/tmp/test.shp")

    @mock.patch.object(osm, "osm_gdf_from_bbox")
    def test_geojson_from_bbox_returns_dict(self, mock_gdf_func):
        mock_gdf_func.return_value = _make_mock_gdf()
        result = osm.osm_geojson_from_bbox(
            40.8, 40.7, -73.9, -74.0, {"building": True}
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result["type"], "FeatureCollection")

    @mock.patch.object(osm, "osm_gdf_from_bbox")
    def test_geojson_from_bbox_writes_file(self, mock_gdf_func):
        gdf = _make_mock_gdf()
        mock_gdf_func.return_value = gdf
        osm.osm_geojson_from_bbox(
            40.8, 40.7, -73.9, -74.0, {"building": True},
            filepath="/tmp/test.geojson",
        )
        gdf.to_file.assert_called_once_with("/tmp/test.geojson", driver="GeoJSON")

    def test_gdf_from_xml_defaults(self):
        mock_ox.features.features_from_xml.return_value = _make_mock_gdf()
        osm.osm_gdf_from_xml("/path/to/file.xml")
        mock_ox.features.features_from_xml.assert_called_once_with(
            "/path/to/file.xml", polygon=None, tags=None
        )

    def test_gdf_from_xml_with_polygon(self):
        from shapely import geometry

        mock_ox.features.features_from_xml.return_value = _make_mock_gdf()
        polygon = geometry.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        osm.osm_gdf_from_xml("/path/to/file.xml", polygon=polygon)
        mock_ox.features.features_from_xml.assert_called_once_with(
            "/path/to/file.xml", polygon=polygon, tags=None
        )

    def test_gdf_from_xml_with_tags(self):
        mock_ox.features.features_from_xml.return_value = _make_mock_gdf()
        tags = {"building": True}
        osm.osm_gdf_from_xml("/path/to/file.xml", tags=tags)
        mock_ox.features.features_from_xml.assert_called_once_with(
            "/path/to/file.xml", polygon=None, tags=tags
        )

    def test_gdf_from_geocode_defaults(self):
        mock_ox.geocoder.geocode_to_gdf.return_value = _make_mock_gdf()
        osm.osm_gdf_from_geocode("New York City")
        mock_ox.geocoder.geocode_to_gdf.assert_called_once_with(
            "New York City", which_result=None, by_osmid=False
        )

    def test_gdf_from_geocode_with_which_result(self):
        mock_ox.geocoder.geocode_to_gdf.return_value = _make_mock_gdf()
        osm.osm_gdf_from_geocode("Paris", which_result=1)
        mock_ox.geocoder.geocode_to_gdf.assert_called_once_with(
            "Paris", which_result=1, by_osmid=False
        )

    def test_gdf_from_geocode_by_osmid(self):
        mock_ox.geocoder.geocode_to_gdf.return_value = _make_mock_gdf()
        osm.osm_gdf_from_geocode("R123456", by_osmid=True)
        mock_ox.geocoder.geocode_to_gdf.assert_called_once_with(
            "R123456", which_result=None, by_osmid=True
        )

    @mock.patch.object(osm, "osm_gdf_from_geocode")
    def test_shp_from_geocode_calls_to_file(self, mock_gdf_func):
        gdf = _make_mock_gdf()
        mock_gdf_func.return_value = gdf
        osm.osm_shp_from_geocode("London", "/tmp/test.shp")
        gdf.to_file.assert_called_once_with("/tmp/test.shp")

    @mock.patch.object(osm, "osm_gdf_from_geocode")
    def test_geojson_from_geocode_returns_dict(self, mock_gdf_func):
        mock_gdf_func.return_value = _make_mock_gdf()
        result = osm.osm_geojson_from_geocode("Tokyo")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["type"], "FeatureCollection")

    @mock.patch.object(osm, "osm_gdf_from_geocode")
    def test_geojson_from_geocode_writes_file(self, mock_gdf_func):
        gdf = _make_mock_gdf()
        mock_gdf_func.return_value = gdf
        osm.osm_geojson_from_geocode("Berlin", filepath="/tmp/test.geojson")
        gdf.to_file.assert_called_once_with("/tmp/test.geojson", driver="GeoJSON")

    @mock.patch.object(osm, "webbrowser")
    def test_tags_list_opens_browser(self, mock_wb):
        osm.osm_tags_list()
        mock_wb.open_new_tab.assert_called_once_with(
            "https://wiki.openstreetmap.org/wiki/Map_features"
        )


if __name__ == "__main__":
    unittest.main()