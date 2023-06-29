"""Tests for `basemaps` module."""

import unittest
from unittest.mock import patch

from geemap.basemaps import get_xyz_dict

import xyzservices


class FakeProvider(xyzservices.TileProvider):
    def __init__(self, name: str, url: str):
        super().__init__(
            name=name,
            url=url,
            attribution="&copy; Fake Provider",
            accessToken="<insert your access token here>"
        )


class FakeXyz(xyzservices.Bunch):
    def __init__(self):
        token = "https://fake-server.com/tiles/{z}/{x}/{y}?apikey={accessToken}"
        no_token = "https://fake-server.com/tiles/{z}/{x}/{y}"

        self.fake_tile_a = FakeProvider('a', no_token)
        self.fake_tile_b = FakeProvider('b', token)
        self.fake_tile_c_1 = FakeProvider('c_1', no_token)
        self.fake_tile_c_France = FakeProvider('c_France', no_token)

        self.providers = xyzservices.Bunch(
            a=self.fake_tile_a,
            b=self.fake_tile_b,
            c=xyzservices.Bunch(
                c_1=self.fake_tile_c_1,
                c_2=self.fake_tile_c_France
            )
        )


@patch('xyzservices.providers', FakeXyz().providers)
class TestGetXyzDict(unittest.TestCase):
    def test_get_xyz_dict_structure(self):
        """Tests that get_xyz_dict returns correct object structure."""
        xyz_dict = get_xyz_dict()
        tile_a = xyz_dict["a"]
        tile_a_keys = tile_a.keys()

        self.assertIsInstance(xyz_dict, dict)
        self.assertEqual("c_1", list(xyz_dict.keys())[1])
        self.assertIsInstance(tile_a, xyzservices.lib.TileProvider)
        self.assertIn("name", tile_a_keys)
        self.assertIn("url", tile_a_keys)
        self.assertIn("attribution", tile_a_keys)
        self.assertIn("accessToken", tile_a_keys)
        self.assertEqual("xyz", tile_a["type"])
        self.assertEqual("a", tile_a.name)
        self.assertEqual("https://fake-server.com/tiles/{z}/{x}/{y}",
                         tile_a.build_url())

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
