"""Tests for `ee_tile_layer_utils` package."""

import unittest
from unittest.mock import patch

import box
import ee

import fake_ee
from geemap import ee_tile_layer_utils


@patch.object(ee, "Feature", fake_ee.Feature)
@patch.object(ee, "FeatureCollection", fake_ee.FeatureCollection)
@patch.object(ee, "Geometry", fake_ee.Geometry)
@patch.object(ee, "Image", fake_ee.Image)
@patch.object(ee, "ImageCollection", fake_ee.ImageCollection)
class TestEeTileLayerUtils(unittest.TestCase):
    """Tests for `ee_tile_layer_utils` package."""

    def test_validate_vis_params_none(self):
        vis_params = None
        self.assertEqual(ee_tile_layer_utils.validate_vis_params(vis_params), {})

    def test_validate_vis_params_invalid_palette_type(self):
        vis_params = {"min": 0.1, "palette": {}}
        with self.assertRaisesRegex(ValueError, "palette must be"):
            ee_tile_layer_utils.validate_vis_params(vis_params)

    def test_validate_vis_params_box_palette_no_default(self):
        vis_params = {"min": 0.1, "palette": box.Box({"unknown-key": 2})}
        with self.assertRaisesRegex(ValueError, "Box object is invalid"):
            ee_tile_layer_utils.validate_vis_params(vis_params)

    def test_validate_vis_params_box_palette(self):
        vis_params = {"min": 0.1, "palette": box.Box({"default": ["#00ff00"]})}
        self.assertEqual(
            ee_tile_layer_utils.validate_vis_params(vis_params),
            {"min": 0.1, "palette": ["#00ff00"]},
        )

    def test_validate_vis_params_str_palette(self):
        vis_params = {"min": 0.1, "palette": "00FF00"}
        self.assertEqual(
            ee_tile_layer_utils.validate_vis_params(vis_params),
            {"min": 0.1, "palette": "#00ff00"},
        )

    def test_validate_vis_params_list_palette(self):
        vis_params = {"min": 0.1, "palette": ["#00ff00"]}
        self.assertEqual(
            ee_tile_layer_utils.validate_vis_params(vis_params),
            {"min": 0.1, "palette": ["#00ff00"]},
        )

    def test_get_tile_url_format_geometry(self):
        self.assertEqual(
            ee_tile_layer_utils.get_tile_url_format(ee.Geometry(""), {}), "url-format"
        )
        self.assertEqual(
            ee_tile_layer_utils.get_tile_url_format(ee.Feature(""), {}), "url-format"
        )
        self.assertEqual(
            ee_tile_layer_utils.get_tile_url_format(ee.FeatureCollection([]), {}),
            "url-format",
        )

    def test_get_tile_url_format_image(self):
        self.assertEqual(
            ee_tile_layer_utils.get_tile_url_format(ee.Image(), {}), "url-format"
        )

    def test_get_tile_url_format_imagecollection(self):
        self.assertEqual(
            ee_tile_layer_utils.get_tile_url_format(ee.ImageCollection([]), {}),
            "url-format",
        )

    def test_get_tile_url_format_invalid_type(self):
        with self.assertRaisesRegex(AttributeError, "Cannot add an object of type str"):
            ee_tile_layer_utils.get_tile_url_format("some-invalid-type", {})
