from __future__ import annotations

import os
import re
import unittest


def assert_valid_geojson(test_case: unittest.TestCase, geojson: dict) -> None:
    valid_types = [
        "Feature",
        "FeatureCollection",
        "Point",
        "LineString",
        "Polygon",
        "MultiPoint",
        "MultiLineString",
        "MultiPolygon",
        "GeometryCollection",
    ]
    test_case.assertIn("type", geojson)
    test_case.assertIn(geojson["type"], valid_types)


def assert_file_created(test_case: unittest.TestCase, filepath: str) -> None:
    test_case.assertTrue(
        os.path.exists(filepath),
        f"File not created: {filepath}",
    )


def assert_file_not_empty(test_case: unittest.TestCase, filepath: str) -> None:
    assert_file_created(test_case, filepath)
    test_case.assertGreater(
        os.path.getsize(filepath),
        0,
        f"File is empty: {filepath}",
    )


def assert_valid_hex_color(test_case: unittest.TestCase, color: str) -> None:
    pattern = r"^#?([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
    test_case.assertIsNotNone(
        re.match(pattern, color),
        f"Invalid hex color: {color}",
    )


def assert_valid_rgb_color(
    test_case: unittest.TestCase, color: tuple[int, int, int]
) -> None:
    test_case.assertEqual(len(color), 3, "RGB color must have 3 components")
    for i, component in enumerate(color):
        test_case.assertGreaterEqual(
            component, 0, f"RGB component {i} must be >= 0"
        )
        test_case.assertLessEqual(
            component, 255, f"RGB component {i} must be <= 255"
        )


def assert_valid_bbox(
    test_case: unittest.TestCase,
    bbox: tuple[float, float, float, float],
) -> None:
    test_case.assertEqual(len(bbox), 4, "Bounding box must have 4 components")
    west, south, east, north = bbox
    test_case.assertLessEqual(west, east, "West must be <= East")
    test_case.assertLessEqual(south, north, "South must be <= North")
    test_case.assertGreaterEqual(west, -180, "West must be >= -180")
    test_case.assertLessEqual(east, 180, "East must be <= 180")
    test_case.assertGreaterEqual(south, -90, "South must be >= -90")
    test_case.assertLessEqual(north, 90, "North must be <= 90")


def assert_dict_contains_keys(
    test_case: unittest.TestCase,
    d: dict,
    keys: list[str],
) -> None:
    for key in keys:
        test_case.assertIn(key, d, f"Missing key: {key}")
