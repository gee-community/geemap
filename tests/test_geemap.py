#!/usr/bin/env python

"""Tests for `geemap` package."""


import unittest
import geemap
import ipyleaflet


class TestGeemap(unittest.TestCase):
    """Tests for `geemap` package."""

    def setUp(self):
        """Set up test fixtures, if any."""
        # geemap.ee_initialize()

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_map(self):
        m = geemap.Map(ee_initialize=False)
        self.assertIsInstance(m, ipyleaflet.Map)
