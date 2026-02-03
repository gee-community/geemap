from __future__ import annotations

import os
import shutil
import tempfile
import unittest


class GeemapTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.test_data_dir = os.path.join(os.path.dirname(__file__), "data")
        cls.temp_dir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls) -> None:
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    def get_fixture(self, filename: str) -> str:
        return os.path.join(self.test_data_dir, filename)

    def get_temp_path(self, filename: str) -> str:
        return os.path.join(self.temp_dir, filename)
