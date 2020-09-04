#!/usr/bin/env python

"""Tests for `geemap` package."""


import unittest
from click.testing import CliRunner
import ee

from geemap import geemap
from geemap import cli


class TestGeemap(unittest.TestCase):
    """Tests for `geemap` package."""

    def setUp(self):
        """Set up test fixtures, if any."""
        geemap.ee_initialize()

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_001_default_settings(self):
        """Test the default settings returns an ImageCollection"""
        sentCollection = geemap.sentinel2_timeseries()
        self.assertIsInstance(sentCollection, ee.imagecollection.ImageCollection)

    def test_002_good_years(self):
        start_year = [*range(2015, 2020, 1)]
        end_year = 2020
        for year in start_year:
            sentCollection = geemap.sentinel2_timeseries(start_year = year, end_year = end_year)
            self.assertIsInstance(sentCollection, ee.imagecollection.ImageCollection)

    def test_003_good_dates(self):
        start_date = '06-01'
        end_date = '12-01'
        sentCollection = geemap.sentinel2_timeseries(start_date = start_date, end_date = end_date)
        self.assertIsInstance(sentCollection, ee.imagecollection.ImageCollection)

    def test_004_bad_years(self):
        years = [
            [2014, 2020],
            [2015, 2021],
            [205, 2019],
            [2016, 202]
            ]
        for start_year, end_year in years:
            sentCollection = geemap.sentinel2_timeseries(start_year = start_year, end_year = end_year)
            self.assertNotIsInstance(sentCollection, ee.imagecollection.ImageCollection)

    def test_006_prior_years(self):
        years = [
            [2016, 2015],
            [2017, 2015],
            [2018, 2015],
            [2019, 2015],
            [2018, 2016],
            [2019, 2017]
            ]
        for start_year, end_year in years:
            self.assertRaises(Exception, geemap.sentinel2_timeseries(start_year = start_year, end_year = end_year))

    def test_007_bad_dates(self):
        start_date = '06-01'
        end_date = '31-12'
        self.assertRaises(Exception, geemap.sentinel2_timeseries(start_date = start_date, end_date = end_date))


    # def test_command_line_interface(self):
    #     """Test the CLI."""
    #     runner = CliRunner()
    #     result = runner.invoke(cli.main)
    #     assert result.exit_code == 0
    #     assert 'geemap.cli.main' in result.output
    #     help_result = runner.invoke(cli.main, ['--help'])
    #     assert help_result.exit_code == 0
    #     assert '--help  Show this message and exit.' in help_result.output
