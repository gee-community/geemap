"""Tests for `datasets` module."""

import importlib
import os
import sys
import unittest
from unittest import mock

import box

from geemap import datasets


class DatasetsTest(unittest.TestCase):
    """Tests for `datasets` module."""

    def test_get_data_csv(self):
        data_csv = datasets.get_data_csv()
        self.assertTrue(os.path.exists(data_csv))
        self.assertEqual(os.path.basename(data_csv), "ee_data_catalog.csv")

    def test_import_does_not_call_network(self):
        """Verifies that importing datasets does not make network calls."""
        # Reset cached _DATA to simulate fresh state
        datasets._DATA = None

        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            importlib.reload(datasets)
            mock_urlopen.assert_not_called()

    def test_lazy_data_access(self):
        """Verifies that accessing DATA lazily builds and caches the Box object."""
        # Reset cached _DATA
        datasets._DATA = None

        fake_dict = {"test_dataset": "users/test/dataset"}
        with mock.patch(
            "geemap.datasets.get_data_dict", return_value=fake_dict
        ) as mock_get_dict:
            data = datasets.DATA
            self.assertIsInstance(data, box.Box)
            self.assertEqual(data.test_dataset, "users/test/dataset")
            mock_get_dict.assert_called_once()

            # Second access should return cached _DATA without calling get_data_dict again
            data2 = datasets.DATA
            self.assertIs(data, data2)
            mock_get_dict.assert_called_once()

    def test_getattr_invalid_attribute(self):
        """Verifies that accessing an undefined attribute raises AttributeError."""
        with self.assertRaises(AttributeError):
            _ = datasets.NON_EXISTENT_ATTRIBUTE

    def test_dir_contains_data(self):
        """Verifies that dir(datasets) includes DATA."""
        self.assertIn("DATA", dir(datasets))


if __name__ == "__main__":
    unittest.main()
