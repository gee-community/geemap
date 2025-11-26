#!/usr/bin/env python
"""Tests for `report` package."""

import unittest

import geemap.report
import scooby


class TestReport(unittest.TestCase):

    def test_report(self):
        """Test that we can instantiate the report."""
        report = geemap.report.Report()
        self.assertIsInstance(report, scooby.Report)
        report_str = str(report)
        self.assertIn("geemap : 0.", report_str)
        self.assertIn("ee : ", report_str)
        self.assertIn("ipyleaflet : 0.", report_str)
        self.assertIn("folium : ", report_str)
        self.assertIn("jupyterlab : ", report_str)
        self.assertIn("notebook : ", report_str)
        self.assertIn("ipyevents : ", report_str)


if __name__ == "__main__":
    unittest.main()
