"""Tests for `datasets` module."""

import os
import unittest

from geemap import datasets


class DatasetsTest(unittest.TestCase):
    """Tests for `datasets` module."""

    def test_get_data_csv(self):
        data_csv = datasets.get_data_csv()
        self.assertTrue(os.path.exists(data_csv))
        self.assertEqual(os.path.basename(data_csv), "ee_data_catalog.csv")


if __name__ == "__main__":
    unittest.main()
