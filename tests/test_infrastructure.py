"""Tests for the test infrastructure (mocks, helpers, conftest)."""

from __future__ import annotations

import os
import unittest

from tests.conftest import GeemapTestCase
from tests.helpers import assertions, factories
from tests.mocks import (mock_ee, mock_map, mock_osmnx, mock_plotly,
                         mock_requests)


class TestMockEe(unittest.TestCase):

    def test_image_creation(self) -> None:
        img = mock_ee.Image()
        self.assertIsNotNone(img)

    def test_image_getinfo(self) -> None:
        img = mock_ee.Image()
        info = img.getInfo()
        self.assertIn("type", info)
        self.assertEqual(info["type"], "Image")

    def test_geometry_point(self) -> None:
        point = mock_ee.Geometry.Point([0, 0])
        self.assertIsNotNone(point)
        info = point.getInfo()
        self.assertEqual(info["type"], "Point")

    def test_geometry_polygon(self) -> None:
        poly = mock_ee.Geometry.Polygon()
        self.assertIsNotNone(poly)
        info = poly.getInfo()
        self.assertEqual(info["type"], "Polygon")

    def test_feature_collection(self) -> None:
        fc = mock_ee.FeatureCollection([])
        self.assertIsNotNone(fc)
        self.assertEqual(fc.size().getInfo(), 0)

    def test_image_collection(self) -> None:
        ic = mock_ee.ImageCollection([mock_ee.Image()])
        self.assertIsNotNone(ic)
        info = ic.getInfo()
        self.assertEqual(info["type"], "ImageCollection")

    def test_list(self) -> None:
        ee_list = mock_ee.List(["a", "b", "c"])
        self.assertEqual(ee_list.getInfo(), ["a", "b", "c"])
        self.assertEqual(ee_list.size().getInfo(), 3)

    def test_dictionary(self) -> None:
        ee_dict = mock_ee.Dictionary({"key": "value"})
        self.assertEqual(ee_dict.getInfo(), {"key": "value"})

    def test_reducer(self) -> None:
        reducer = mock_ee.Reducer.mean()
        self.assertIsNotNone(reducer)

    def test_filter(self) -> None:
        filt = mock_ee.Filter.eq("prop", "value")
        self.assertIsNotNone(filt)


class TestMockMap(unittest.TestCase):

    def test_fake_map_creation(self) -> None:
        fake_map = mock_map.FakeMap()
        self.assertIsNotNone(fake_map)

    def test_fake_map_layers(self) -> None:
        fake_map = mock_map.FakeMap()
        self.assertEqual(len(fake_map.layers), 0)

    def test_fake_map_add_layer(self) -> None:
        fake_map = mock_map.FakeMap()
        layer = mock_map.FakeTileLayer(name="test")
        fake_map.add_layer(layer, name="test")
        self.assertEqual(len(fake_map.layers), 1)

    def test_fake_ee_tile_layer(self) -> None:
        layer = mock_map.FakeEeTileLayer(name="test")
        self.assertEqual(layer.name, "test")
        self.assertTrue(layer.visible)

    def test_fake_geojson_layer(self) -> None:
        layer = mock_map.FakeGeoJSONLayer(name="test")
        self.assertEqual(layer.name, "test")


class TestMockRequests(unittest.TestCase):

    def test_mock_response_success(self) -> None:
        response = mock_requests.MockResponse(
            json_data={"key": "value"},
            status_code=200,
        )
        self.assertTrue(response.ok)
        self.assertEqual(response.json(), {"key": "value"})

    def test_mock_response_error(self) -> None:
        response = mock_requests.MockResponse(status_code=404)
        self.assertFalse(response.ok)
        with self.assertRaises(mock_requests.RequestError):
            response.raise_for_status()

    def test_create_mock_response(self) -> None:
        response = mock_requests.create_mock_response(
            json_data={"data": [1, 2, 3]},
            status_code=200,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], [1, 2, 3])


class TestMockOsmnx(unittest.TestCase):

    def test_mock_geodataframe(self) -> None:
        gdf = mock_osmnx.MockGeoDataFrame()
        self.assertTrue(gdf.empty)

    def test_mock_features_from_address(self) -> None:
        result = mock_osmnx.mock_features_from_address(
            "Test Address",
            tags={"building": True},
        )
        self.assertIsNotNone(result)
        self.assertFalse(result.empty)

    def test_mock_features_from_bbox(self) -> None:
        result = mock_osmnx.mock_features_from_bbox(
            bbox=(-122, 37, -121, 38),
            tags={"building": True},
        )
        self.assertIsNotNone(result)


class TestMockPlotly(unittest.TestCase):

    def test_mock_figure(self) -> None:
        fig = mock_plotly.MockFigure()
        self.assertIsNotNone(fig)

    def test_mock_figure_update_layout(self) -> None:
        fig = mock_plotly.MockFigure()
        fig.update_layout(title="Test")
        self.assertEqual(fig.layout["title"], "Test")

    def test_mock_plotly_express_bar(self) -> None:
        fig = mock_plotly.MockPlotlyExpress.bar()
        self.assertEqual(fig.data[0]["type"], "bar")

    def test_mock_plotly_express_pie(self) -> None:
        fig = mock_plotly.MockPlotlyExpress.pie()
        self.assertEqual(fig.data[0]["type"], "pie")


class TestHelperFactories(unittest.TestCase):

    def test_create_ee_image(self) -> None:
        img = factories.create_ee_image(bands=["B1", "B2"])
        self.assertEqual(img._bands, ["B1", "B2"])

    def test_create_ee_feature_collection(self) -> None:
        fc = factories.create_ee_feature_collection()
        self.assertIsNotNone(fc)

    def test_create_ee_geometry(self) -> None:
        geom = factories.create_ee_geometry("Point", [10, 20])
        self.assertIsNotNone(geom)

    def test_create_sample_dataframe(self) -> None:
        df = factories.create_sample_dataframe(rows=10)
        self.assertEqual(len(df), 10)

    def test_create_sample_geojson(self) -> None:
        geojson = factories.create_sample_geojson(num_features=5)
        self.assertEqual(len(geojson["features"]), 5)


class TestHelperAssertions(unittest.TestCase):

    def test_assert_valid_geojson_feature(self) -> None:
        geojson = {"type": "Feature", "geometry": {}, "properties": {}}
        assertions.assert_valid_geojson(self, geojson)

    def test_assert_valid_geojson_collection(self) -> None:
        geojson = {"type": "FeatureCollection", "features": []}
        assertions.assert_valid_geojson(self, geojson)

    def test_assert_valid_hex_color(self) -> None:
        assertions.assert_valid_hex_color(self, "#FF0000")
        assertions.assert_valid_hex_color(self, "FF0000")
        assertions.assert_valid_hex_color(self, "#FFF")

    def test_assert_valid_rgb_color(self) -> None:
        assertions.assert_valid_rgb_color(self, (255, 0, 0))
        assertions.assert_valid_rgb_color(self, (0, 128, 255))

    def test_assert_valid_bbox(self) -> None:
        assertions.assert_valid_bbox(self, (-122, 37, -121, 38))

    def test_assert_dict_contains_keys(self) -> None:
        d = {"a": 1, "b": 2, "c": 3}
        assertions.assert_dict_contains_keys(self, d, ["a", "b"])


class TestGeemapTestCase(GeemapTestCase):

    def test_temp_dir_exists(self) -> None:
        self.assertTrue(os.path.exists(self.temp_dir))

    def test_get_temp_path(self) -> None:
        path = self.get_temp_path("test.txt")
        self.assertTrue(path.endswith("test.txt"))
        self.assertIn(self.temp_dir, path)

    def test_temp_file_creation(self) -> None:
        path = self.get_temp_path("test_file.txt")
        with open(path, "w") as f:
            f.write("test content")
        assertions.assert_file_created(self, path)


if __name__ == "__main__":
    unittest.main()
