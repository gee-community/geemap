#!/usr/bin/env python

"""Tests for `geemap` package."""


import unittest
import ee

import geemap
from geemap.common import sentinel2_timeseries


class TestGeemap(unittest.TestCase):
    """Tests for `geemap` package."""

    def setUp(self):
        """Set up test fixtures, if any."""
        geemap.ee_initialize()

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_001_default_settings(self):
        """Test the default settings returns an ImageCollection"""
        sentCollection = sentinel2_timeseries()
        self.assertIsInstance(sentCollection, ee.imagecollection.ImageCollection)

    def test_002_good_years(self):
        start_year = [*range(2015, 2020, 1)]
        end_year = 2020
        for year in start_year:
            sentCollection = sentinel2_timeseries(start_year=year, end_year=end_year)
            self.assertIsInstance(sentCollection, ee.imagecollection.ImageCollection)

    def test_003_good_dates(self):
        start_date = "06-01"
        end_date = "12-01"
        sentCollection = sentinel2_timeseries(start_date=start_date, end_date=end_date)
        self.assertIsInstance(sentCollection, ee.imagecollection.ImageCollection)
