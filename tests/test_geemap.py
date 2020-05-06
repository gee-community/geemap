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

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_001_default_settings(self):
        """Test the default settings returns an ImageCollection"""
        sentCollection = geemap.sentinel2_timeseries()
        self.assertIsInstance(sentCollection, ee.imagecollection.ImageCollection)

    def test_002_good_roi(self):
        roi = ee.Geometry.Polygon(
            [[[-88.3286743, 15.4259033],
                [-88.1582641, 15.4259033],
                [-88.1582641, 15.5667724],
            [-88.3286743, 15.5667724],
            [-88.3286743, 15.4259033]]], None, False)
        sentCollection = geemap.sentinel2_timeseries(roi = roi)
        self.assertIsInstance(sentCollection, ee.imagecollection.ImageCollection)

    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        assert 'geemap.cli.main' in result.output
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert '--help  Show this message and exit.' in help_result.output
