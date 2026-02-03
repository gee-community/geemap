"""Tests for the ai module."""

from __future__ import annotations

import datetime
import sys
import unittest
from typing import TYPE_CHECKING
from unittest import mock

if TYPE_CHECKING:
    from geemap.ai import Collection as AICollection

MOCK_MODULES = [
    "vertexai",
    "vertexai.preview",
    "vertexai.preview.language_models",
    "google.generativeai",
    "google.ai",
    "google.ai.generativelanguage",
    "google.cloud.storage",
    "langchain",
    "langchain.embeddings",
    "langchain.embeddings.base",
    "langchain.indexes",
    "langchain.indexes.vectorstore",
    "langchain.schema",
    "langchain_google_genai",
    "langchain_core",
    "langchain_core.vectorstores",
    "langchain_core.vectorstores.base",
    "langchain_core.language_models",
    "langchain_core.language_models.base",
    "google.colab",
    "google.colab.output",
    "google.colab.data_table",
    "google.colab.syntax",
]

for mod_name in MOCK_MODULES:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = mock.MagicMock()

mock_storage = mock.MagicMock()
mock_storage.Client = mock.MagicMock()
mock_storage.Blob = mock.MagicMock()
sys.modules["google.cloud.storage"] = mock_storage

mock_embeddings_base = mock.MagicMock()
mock_embeddings_base.Embeddings = object
sys.modules["langchain.embeddings.base"] = mock_embeddings_base

from geemap import ai


class TestMatchesInterval(unittest.TestCase):

    def test_matches_interval_overlapping(self) -> None:
        collection_interval = (
            datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
            datetime.datetime(2022, 12, 31, tzinfo=datetime.UTC),
        )
        query_interval = (
            datetime.datetime(2021, 6, 1, tzinfo=datetime.UTC),
            datetime.datetime(2023, 6, 1, tzinfo=datetime.UTC),
        )
        result = ai.matches_interval(collection_interval, query_interval)
        self.assertTrue(result)

    def test_matches_interval_query_within_collection(self) -> None:
        collection_interval = (
            datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
            datetime.datetime(2025, 12, 31, tzinfo=datetime.UTC),
        )
        query_interval = (
            datetime.datetime(2021, 1, 1, tzinfo=datetime.UTC),
            datetime.datetime(2022, 1, 1, tzinfo=datetime.UTC),
        )
        result = ai.matches_interval(collection_interval, query_interval)
        self.assertTrue(result)

    def test_matches_interval_collection_within_query(self) -> None:
        collection_interval = (
            datetime.datetime(2021, 1, 1, tzinfo=datetime.UTC),
            datetime.datetime(2022, 1, 1, tzinfo=datetime.UTC),
        )
        query_interval = (
            datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
            datetime.datetime(2025, 12, 31, tzinfo=datetime.UTC),
        )
        result = ai.matches_interval(collection_interval, query_interval)
        self.assertTrue(result)

    def test_matches_interval_no_overlap_before(self) -> None:
        collection_interval = (
            datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
            datetime.datetime(2020, 12, 31, tzinfo=datetime.UTC),
        )
        query_interval = (
            datetime.datetime(2021, 1, 1, tzinfo=datetime.UTC),
            datetime.datetime(2022, 1, 1, tzinfo=datetime.UTC),
        )
        result = ai.matches_interval(collection_interval, query_interval)
        self.assertFalse(result)

    def test_matches_interval_no_overlap_after(self) -> None:
        collection_interval = (
            datetime.datetime(2023, 1, 1, tzinfo=datetime.UTC),
            datetime.datetime(2024, 12, 31, tzinfo=datetime.UTC),
        )
        query_interval = (
            datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
            datetime.datetime(2022, 1, 1, tzinfo=datetime.UTC),
        )
        result = ai.matches_interval(collection_interval, query_interval)
        self.assertFalse(result)

    def test_matches_interval_none_end_date(self) -> None:
        collection_interval = (
            datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
            None,
        )
        query_interval = (
            datetime.datetime(2021, 1, 1, tzinfo=datetime.UTC),
            datetime.datetime(2022, 1, 1, tzinfo=datetime.UTC),
        )
        result = ai.matches_interval(collection_interval, query_interval)  # type: ignore[arg-type]
        self.assertTrue(result)


class TestMatchesDatetime(unittest.TestCase):

    def test_matches_datetime_within_interval(self) -> None:
        collection_interval = (
            datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
            datetime.datetime(2025, 12, 31, tzinfo=datetime.UTC),
        )
        query_datetime = datetime.datetime(2022, 6, 15, tzinfo=datetime.UTC)
        result = ai.matches_datetime(collection_interval, query_datetime)
        self.assertTrue(result)

    def test_matches_datetime_at_start(self) -> None:
        collection_interval = (
            datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
            datetime.datetime(2025, 12, 31, tzinfo=datetime.UTC),
        )
        query_datetime = datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC)
        result = ai.matches_datetime(collection_interval, query_datetime)
        self.assertTrue(result)

    def test_matches_datetime_at_end(self) -> None:
        collection_interval = (
            datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
            datetime.datetime(2025, 12, 31, tzinfo=datetime.UTC),
        )
        query_datetime = datetime.datetime(2025, 12, 31, tzinfo=datetime.UTC)
        result = ai.matches_datetime(collection_interval, query_datetime)
        self.assertTrue(result)

    def test_matches_datetime_before_interval(self) -> None:
        collection_interval = (
            datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
            datetime.datetime(2025, 12, 31, tzinfo=datetime.UTC),
        )
        query_datetime = datetime.datetime(2019, 6, 15, tzinfo=datetime.UTC)
        result = ai.matches_datetime(collection_interval, query_datetime)
        self.assertFalse(result)

    def test_matches_datetime_after_interval(self) -> None:
        collection_interval = (
            datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
            datetime.datetime(2025, 12, 31, tzinfo=datetime.UTC),
        )
        query_datetime = datetime.datetime(2026, 6, 15, tzinfo=datetime.UTC)
        result = ai.matches_datetime(collection_interval, query_datetime)
        self.assertFalse(result)

    def test_matches_datetime_none_end_date(self) -> None:
        collection_interval = (
            datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC),
            None,
        )
        query_datetime = datetime.datetime(2022, 6, 15, tzinfo=datetime.UTC)
        result = ai.matches_datetime(collection_interval, query_datetime)
        self.assertTrue(result)


class TestBBox(unittest.TestCase):

    def test_bbox_init(self) -> None:
        bbox = ai.BBox(west=-10.0, south=-20.0, east=30.0, north=40.0)
        self.assertEqual(bbox.west, -10.0)
        self.assertEqual(bbox.south, -20.0)
        self.assertEqual(bbox.east, 30.0)
        self.assertEqual(bbox.north, 40.0)

    def test_bbox_is_global_true(self) -> None:
        bbox = ai.BBox(west=-180, south=-90, east=180, north=90)
        self.assertTrue(bbox.is_global())

    def test_bbox_is_global_false(self) -> None:
        bbox = ai.BBox(west=-10.0, south=-20.0, east=30.0, north=40.0)
        self.assertFalse(bbox.is_global())

    def test_bbox_from_list_valid(self) -> None:
        bbox = ai.BBox.from_list([-10.0, -20.0, 30.0, 40.0])
        self.assertEqual(bbox.west, -10.0)
        self.assertEqual(bbox.south, -20.0)
        self.assertEqual(bbox.east, 30.0)
        self.assertEqual(bbox.north, 40.0)

    def test_bbox_from_list_inverted_lon_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            ai.BBox.from_list([30.0, -20.0, -10.0, 40.0])
        self.assertIn("west", str(ctx.exception).lower())

    def test_bbox_from_list_inverted_lat_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            ai.BBox.from_list([-10.0, 40.0, 30.0, -20.0])
        self.assertIn("south", str(ctx.exception).lower())

    def test_bbox_to_list(self) -> None:
        bbox = ai.BBox(west=-10.0, south=-20.0, east=30.0, north=40.0)
        result = bbox.to_list()
        self.assertEqual(result, [-10.0, -20.0, 30.0, 40.0])

    def test_bbox_intersects_overlapping(self) -> None:
        bbox1 = ai.BBox(west=0, south=0, east=20, north=20)
        bbox2 = ai.BBox(west=10, south=10, east=30, north=30)
        self.assertTrue(bbox1.intersects(bbox2))

    def test_bbox_intersects_contained(self) -> None:
        bbox1 = ai.BBox(west=0, south=0, east=100, north=100)
        bbox2 = ai.BBox(west=10, south=10, east=30, north=30)
        self.assertTrue(bbox1.intersects(bbox2))

    def test_bbox_intersects_no_overlap_horizontal(self) -> None:
        bbox1 = ai.BBox(west=0, south=0, east=10, north=10)
        bbox2 = ai.BBox(west=20, south=0, east=30, north=10)
        self.assertFalse(bbox1.intersects(bbox2))

    def test_bbox_intersects_no_overlap_vertical(self) -> None:
        bbox1 = ai.BBox(west=0, south=0, east=10, north=10)
        bbox2 = ai.BBox(west=0, south=20, east=10, north=30)
        self.assertFalse(bbox1.intersects(bbox2))

    def test_bbox_intersects_touching_edge(self) -> None:
        bbox1 = ai.BBox(west=0, south=0, east=10, north=10)
        bbox2 = ai.BBox(west=10, south=0, east=20, north=10)
        self.assertFalse(bbox1.intersects(bbox2))


class TestCollection(unittest.TestCase):

    def setUp(self) -> None:
        self.sample_stac = {
            "id": "LANDSAT/LC08/C02/T1",
            "title": "Landsat 8 Collection 2 Tier 1",
            "gee:type": "image_collection",
            "extent": {
                "spatial": {"bbox": [[-180, -90, 180, 90]]},
                "temporal": {
                    "interval": [["2013-04-11T00:00:00Z", "2024-01-01T00:00:00Z"]]
                },
            },
            "summaries": {
                "eo:bands": [
                    {"name": "B1", "description": "Coastal"},
                    {"name": "B2", "description": "Blue"},
                ],
                "gsd": [30],
            },
            "gee:interval": {"interval": 16, "unit": "day"},
            "links": [
                {
                    "rel": "preview",
                    "href": "https://example.com/preview.png",
                    "type": "image/png",
                },
                {
                    "rel": "catalog",
                    "href": "https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1",
                },
            ],
            "code": {
                "js_code": "var image = ee.Image();",
                "py_code": "image = ee.Image()",
            },
        }

    def test_collection_getitem(self) -> None:
        collection = ai.Collection(self.sample_stac)
        self.assertEqual(collection["id"], "LANDSAT/LC08/C02/T1")

    def test_collection_get_existing(self) -> None:
        collection = ai.Collection(self.sample_stac)
        self.assertEqual(collection.get("title"), "Landsat 8 Collection 2 Tier 1")

    def test_collection_get_missing_returns_default(self) -> None:
        collection = ai.Collection(self.sample_stac)
        self.assertIsNone(collection.get("nonexistent"))
        self.assertEqual(collection.get("nonexistent", "default"), "default")

    def test_collection_public_id(self) -> None:
        collection = ai.Collection(self.sample_stac)
        self.assertEqual(collection.public_id(), "LANDSAT/LC08/C02/T1")

    def test_collection_hyphen_id(self) -> None:
        collection = ai.Collection(self.sample_stac)
        self.assertEqual(collection.hyphen_id(), "LANDSAT_LC08_C02_T1")

    def test_collection_get_dataset_type(self) -> None:
        collection = ai.Collection(self.sample_stac)
        self.assertEqual(collection.get_dataset_type(), "image_collection")

    def test_collection_is_deprecated_false(self) -> None:
        collection = ai.Collection(self.sample_stac)
        self.assertFalse(collection.is_deprecated())

    def test_collection_is_deprecated_true(self) -> None:
        stac = self.sample_stac.copy()
        stac["gee:status"] = "deprecated"
        collection = ai.Collection(stac)
        self.assertTrue(collection.is_deprecated())

    def test_collection_datetime_interval(self) -> None:
        collection = ai.Collection(self.sample_stac)
        intervals = list(collection.datetime_interval())
        self.assertEqual(len(intervals), 1)
        start, end = intervals[0]
        self.assertEqual(start.year, 2013)
        self.assertEqual(end.year, 2024)  # type: ignore[union-attr]

    def test_collection_datetime_interval_none_end(self) -> None:
        stac = self.sample_stac.copy()
        stac["extent"]["temporal"]["interval"] = [["2013-04-11T00:00:00Z", None]]  # type: ignore[index]
        collection = ai.Collection(stac)
        intervals = list(collection.datetime_interval())
        start, end = intervals[0]
        self.assertEqual(start.year, 2013)  # type: ignore[union-attr]
        self.assertIsNone(end)

    def test_collection_start(self) -> None:
        collection = ai.Collection(self.sample_stac)
        self.assertEqual(collection.start().year, 2013)

    def test_collection_start_str(self) -> None:
        collection = ai.Collection(self.sample_stac)
        self.assertEqual(collection.start_str(), "2013-04-11")

    def test_collection_end(self) -> None:
        collection = ai.Collection(self.sample_stac)
        self.assertEqual(collection.end().year, 2024)  # type: ignore[union-attr]

    def test_collection_end_str(self) -> None:
        collection = ai.Collection(self.sample_stac)
        self.assertEqual(collection.end_str(), "2024-01-01")

    def test_collection_end_str_none(self) -> None:
        stac = self.sample_stac.copy()
        stac["extent"]["temporal"]["interval"] = [["2013-04-11T00:00:00Z", None]]  # type: ignore[index]
        collection = ai.Collection(stac)
        self.assertEqual(collection.end_str(), "")

    def test_collection_bbox_list(self) -> None:
        collection = ai.Collection(self.sample_stac)
        bboxes = collection.bbox_list()
        self.assertEqual(len(bboxes), 1)
        self.assertTrue(bboxes[0].is_global())

    def test_collection_bbox_list_no_extent(self) -> None:
        stac = self.sample_stac.copy()
        del stac["extent"]
        collection = ai.Collection(stac)
        bboxes = collection.bbox_list()
        self.assertEqual(len(bboxes), 1)
        self.assertTrue(bboxes[0].is_global())

    def test_collection_bands(self) -> None:
        collection = ai.Collection(self.sample_stac)
        bands = collection.bands()
        self.assertEqual(len(bands), 2)
        self.assertEqual(bands[0]["name"], "B1")

    def test_collection_bands_no_summaries(self) -> None:
        stac = self.sample_stac.copy()
        del stac["summaries"]  # type: ignore[attr-defined]
        collection = ai.Collection(stac)
        self.assertEqual(collection.bands(), [])

    def test_collection_spatial_resolution_m(self) -> None:
        collection = ai.Collection(self.sample_stac)
        self.assertEqual(collection.spatial_resolution_m(), 30)

    def test_collection_spatial_resolution_m_no_gsd(self) -> None:
        stac = self.sample_stac.copy()
        del stac["summaries"]["gsd"]  # type: ignore[attr-defined]
        collection = ai.Collection(stac)
        self.assertEqual(collection.spatial_resolution_m(), -1)

    def test_collection_temporal_resolution_str(self) -> None:
        collection = ai.Collection(self.sample_stac)
        self.assertEqual(collection.temporal_resolution_str(), "16 day")

    def test_collection_temporal_resolution_str_no_interval(self) -> None:
        stac = self.sample_stac.copy()
        del stac["gee:interval"]
        collection = ai.Collection(stac)
        self.assertEqual(collection.temporal_resolution_str(), "")

    def test_collection_python_code(self) -> None:
        collection = ai.Collection(self.sample_stac)
        self.assertEqual(collection.python_code(), "image = ee.Image()")

    def test_collection_python_code_missing(self) -> None:
        stac = self.sample_stac.copy()
        del stac["code"]
        collection = ai.Collection(stac)
        self.assertEqual(collection.python_code(), "")

    def test_collection_set_python_code(self) -> None:
        collection = ai.Collection(self.sample_stac)
        collection.set_python_code("new_code = ee.Image('NEW')")
        self.assertEqual(collection.python_code(), "new_code = ee.Image('NEW')")

    def test_collection_image_preview_url(self) -> None:
        collection = ai.Collection(self.sample_stac)
        self.assertEqual(
            collection.image_preview_url(), "https://example.com/preview.png"
        )

    def test_collection_image_preview_url_not_found_raises(self) -> None:
        stac = self.sample_stac.copy()
        stac["links"] = []
        collection = ai.Collection(stac)
        with self.assertRaises(ValueError):
            collection.image_preview_url()

    def test_collection_catalog_url(self) -> None:
        collection = ai.Collection(self.sample_stac)
        url = collection.catalog_url()
        self.assertIn("developers.google.com", url)


class TestCollectionList(unittest.TestCase):

    def setUp(self) -> None:
        self.stac1 = {
            "id": "LANDSAT/LC08/C02/T1",
            "title": "Landsat 8",
            "gee:type": "image_collection",
            "extent": {
                "spatial": {"bbox": [[-180, -90, 180, 90]]},
                "temporal": {
                    "interval": [["2013-04-11T00:00:00Z", "2024-01-01T00:00:00Z"]]
                },
            },
            "summaries": {"gsd": [30]},
            "links": [],
        }
        self.stac2 = {
            "id": "COPERNICUS/S2",
            "title": "Sentinel-2",
            "gee:type": "image_collection",
            "extent": {
                "spatial": {"bbox": [[-180, -90, 180, 90]]},
                "temporal": {
                    "interval": [["2015-06-27T00:00:00Z", "2024-01-01T00:00:00Z"]]
                },
            },
            "summaries": {"gsd": [10]},
            "links": [],
        }
        self.stac3 = {
            "id": "MODIS/006/MOD09GA",
            "title": "MODIS",
            "gee:type": "image_collection",
            "extent": {
                "spatial": {"bbox": [[-180, -90, 180, 90]]},
                "temporal": {
                    "interval": [["2000-02-24T00:00:00Z", "2024-01-01T00:00:00Z"]]
                },
            },
            "summaries": {"gsd": [500]},
            "links": [],
        }
        self.col1 = ai.Collection(self.stac1)
        self.col2 = ai.Collection(self.stac2)
        self.col3 = ai.Collection(self.stac3)
        self.collection_list = ai.CollectionList([self.col1, self.col2, self.col3])

    def test_collection_list_len(self) -> None:
        self.assertEqual(len(self.collection_list), 3)

    def test_collection_list_getitem(self) -> None:
        self.assertEqual(self.collection_list[0].public_id(), "LANDSAT/LC08/C02/T1")
        self.assertEqual(self.collection_list[1].public_id(), "COPERNICUS/S2")

    def test_collection_list_iter(self) -> None:
        ids = [c.public_id() for c in self.collection_list]
        self.assertEqual(
            ids, ["LANDSAT/LC08/C02/T1", "COPERNICUS/S2", "MODIS/006/MOD09GA"]
        )

    def test_collection_list_eq(self) -> None:
        other = ai.CollectionList([self.col1, self.col2, self.col3])
        self.assertEqual(self.collection_list, other)

    def test_collection_list_filter_by_ids(self) -> None:
        filtered = self.collection_list.filter_by_ids(["COPERNICUS/S2"])
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].public_id(), "COPERNICUS/S2")

    def test_collection_list_filter_by_ids_multiple(self) -> None:
        filtered = self.collection_list.filter_by_ids(
            ["COPERNICUS/S2", "MODIS/006/MOD09GA"]
        )
        self.assertEqual(len(filtered), 2)

    def test_collection_list_filter_by_ids_none_match(self) -> None:
        filtered = self.collection_list.filter_by_ids(["NONEXISTENT"])
        self.assertEqual(len(filtered), 0)

    def test_collection_list_filter_by_datetime(self) -> None:
        query_dt = datetime.datetime(2010, 1, 1, tzinfo=datetime.UTC)
        filtered = self.collection_list.filter_by_datetime(query_dt)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].public_id(), "MODIS/006/MOD09GA")

    def test_collection_list_filter_by_datetime_all_match(self) -> None:
        query_dt = datetime.datetime(2020, 1, 1, tzinfo=datetime.UTC)
        filtered = self.collection_list.filter_by_datetime(query_dt)
        self.assertEqual(len(filtered), 3)

    def test_collection_list_filter_by_interval(self) -> None:
        query_interval = (
            datetime.datetime(2010, 1, 1, tzinfo=datetime.UTC),
            datetime.datetime(2012, 1, 1, tzinfo=datetime.UTC),
        )
        filtered = self.collection_list.filter_by_interval(query_interval)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].public_id(), "MODIS/006/MOD09GA")

    def test_collection_list_filter_by_bounding_box(self) -> None:
        query_bbox = ai.BBox(west=-10, south=-10, east=10, north=10)
        filtered = self.collection_list.filter_by_bounding_box(query_bbox)
        self.assertEqual(len(filtered), 3)

    def test_collection_list_filter_by_bounding_box_regional(self) -> None:
        stac_regional = {
            "id": "REGIONAL/DATA",
            "title": "Regional",
            "gee:type": "image",
            "extent": {
                "spatial": {"bbox": [[100, 10, 110, 20]]},
                "temporal": {
                    "interval": [["2020-01-01T00:00:00Z", "2024-01-01T00:00:00Z"]]
                },
            },
            "links": [],
        }
        col_regional = ai.Collection(stac_regional)
        col_list = ai.CollectionList([self.col1, col_regional])
        query_bbox = ai.BBox(west=-10, south=-10, east=10, north=10)
        filtered = col_list.filter_by_bounding_box(query_bbox)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].public_id(), "LANDSAT/LC08/C02/T1")

    def test_collection_list_sort_by_spatial_resolution(self) -> None:
        sorted_list = self.collection_list.sort_by_spatial_resolution()
        resolutions = [c.spatial_resolution_m() for c in sorted_list]
        self.assertEqual(resolutions, [10, 30, 500])

    def test_collection_list_sort_by_spatial_resolution_reverse(self) -> None:
        sorted_list = self.collection_list.sort_by_spatial_resolution(reverse=True)
        resolutions = [c.spatial_resolution_m() for c in sorted_list]
        self.assertEqual(resolutions, [500, 30, 10])

    def test_collection_list_sort_by_spatial_resolution_unknown_at_end(self) -> None:
        stac_no_gsd = {
            "id": "NO_GSD/DATA",
            "title": "No GSD",
            "gee:type": "image",
            "extent": {
                "spatial": {"bbox": [[-180, -90, 180, 90]]},
                "temporal": {
                    "interval": [["2020-01-01T00:00:00Z", "2024-01-01T00:00:00Z"]]
                },
            },
            "links": [],
        }
        col_no_gsd = ai.Collection(stac_no_gsd)
        col_list = ai.CollectionList([col_no_gsd, self.col1, self.col2])
        sorted_list = col_list.sort_by_spatial_resolution()
        self.assertEqual(sorted_list[2].public_id(), "NO_GSD/DATA")

    def test_collection_list_limit(self) -> None:
        limited = self.collection_list.limit(2)
        self.assertEqual(len(limited), 2)
        self.assertEqual(limited[0].public_id(), "LANDSAT/LC08/C02/T1")
        self.assertEqual(limited[1].public_id(), "COPERNICUS/S2")

    def test_collection_list_limit_larger_than_list(self) -> None:
        limited = self.collection_list.limit(10)
        self.assertEqual(len(limited), 3)

    def test_collection_list_to_df(self) -> None:
        df = self.collection_list.to_df()
        self.assertEqual(len(df), 3)
        self.assertIn("id", df.columns)
        self.assertIn("name", df.columns)
        self.assertIn("spatial_res_m", df.columns)
        self.assertEqual(df.iloc[0]["id"], "LANDSAT/LC08/C02/T1")


if __name__ == "__main__":
    unittest.main()
