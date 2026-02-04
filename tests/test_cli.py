"""Tests for the cli module."""

import unittest

from click import testing

from geemap import cli


class TestMain(unittest.TestCase):

    def setUp(self):
        self.runner = testing.CliRunner()

    def test_main_no_args(self):
        result = self.runner.invoke(cli.main)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("geemap.cli.main", result.output)
        self.assertIn("click.palletsprojects.com", result.output)

    def test_main_help_flag(self):
        result = self.runner.invoke(cli.main, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Console script for geemap", result.output)
        self.assertIn("Usage:", result.output)


if __name__ == "__main__":
    unittest.main()
