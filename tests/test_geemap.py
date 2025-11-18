#!/usr/bin/env python
"""Tests for `geemap` package."""

import unittest

import geemap
import ipyleaflet


class TestGeemap(unittest.TestCase):
    """Tests for `geemap` package."""

    def test_map(self):
        m = geemap.Map(ee_initialize=False)
        self.assertIsInstance(m, ipyleaflet.Map)


if __name__ == "__main__":
    unittest.main()
