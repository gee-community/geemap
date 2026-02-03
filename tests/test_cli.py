"""Tests for the cli module."""

from __future__ import annotations

import unittest

from click.testing import CliRunner

from geemap.cli import main


class TestMain(unittest.TestCase):

    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_main_no_args_returns_zero(self) -> None:
        result = self.runner.invoke(main)
        self.assertEqual(result.exit_code, 0)

    def test_main_no_args_outputs_message(self) -> None:
        result = self.runner.invoke(main)
        self.assertIn("geemap.cli.main", result.output)

    def test_main_no_args_outputs_click_docs_reference(self) -> None:
        result = self.runner.invoke(main)
        self.assertIn("click.palletsprojects.com", result.output)

    def test_main_help_flag_shows_help(self) -> None:
        result = self.runner.invoke(main, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Console script for geemap", result.output)

    def test_main_help_flag_shows_usage(self) -> None:
        result = self.runner.invoke(main, ["--help"])
        self.assertIn("Usage:", result.output)


if __name__ == "__main__":
    unittest.main()
