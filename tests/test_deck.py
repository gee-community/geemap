#!/usr/bin/env python

"""Tests for `geemap.deck` package."""

import unittest
from unittest.mock import patch

from box import Box
import ee
import geemap.deck as gmd
from tests import fake_ee

try:
    import pydeck as pdk

except ImportError:
    raise ImportError("pydeck needs to be installed to use this module.")


FAKE_URL = "http://fake.apis.com/v1/projects/fake-project/maps/XXX/tiles/{z}/{x}/{y}"


@patch.object(ee, "Image", fake_ee.Image, spec=True)
class TestMap(unittest.TestCase):
    """Tests for `geemap.deck.Map` class."""

    def setUp(self):
        """Set up test fixtures."""
        self.view_state = pdk.ViewState()
        self.ee_object = fake_ee.Image()

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_ee_layer_opacity(self):
        """Verify the opacity parameter is processed."""
        m = gmd.Map(ee_initialize=False, initial_view_state=self.view_state)
        with patch.object(ee.Image, "getMapId", autospec=True) as mock_get_map_id:
            mock_get_map_id.return_value = {
                "tile_fetcher": Box({"url_format": FAKE_URL})
            }
            m.add_ee_layer(self.ee_object, vis_params={}, opacity=0.5)

        self.assertEquals(len(m.layers), 1)
        layer = m.layers[0]

        self.assertIsInstance(layer, pdk.Layer)
        self.assertEqual(layer.opacity, 0.5)
