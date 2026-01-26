#!/usr/bin/env python
"""Tests for `coreutils` module."""
import json
import os
import string
import sys
import tempfile
from typing import Any
import unittest
from unittest import mock
import uuid

import ee

from geemap import coreutils
from tests import fake_ee


class FakeSecretNotFoundError(Exception):
    """google.colab.userdata.SecretNotFoundError fake."""


class FakeNotebookAccessError(Exception):
    """google.colab.userdata.NotebookAccessError fake."""


def _read_json_file(path: str) -> dict[str, Any]:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, f"data/{path}")
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


@mock.patch.object(ee, "Feature", fake_ee.Feature)
@mock.patch.object(ee, "Image", fake_ee.Image)
@mock.patch.object(ee, "ImageCollection", fake_ee.ImageCollection)
class TestCoreUtils(unittest.TestCase):
    """Tests for core utilss."""

    def test_get_environment_invalid_key(self):
        """Verifies None is returned if keys are invalid."""
        self.assertIsNone(coreutils.get_env_var(None))
        self.assertIsNone(coreutils.get_env_var(""))

    @mock.patch.dict(os.environ, {"key": "value"})
    def test_get_env_var_unknown_key(self):
        """Verifies None is returned if the environment variable could not be found."""
        self.assertIsNone(coreutils.get_env_var("unknown-key"))

    @mock.patch.dict(os.environ, {"key": "value"})
    def test_get_env_var_from_env(self):
        """Verifies environment variables are read from environment variables."""
        self.assertEqual(coreutils.get_env_var("key"), "value")

    @mock.patch.dict("sys.modules", {"google.colab": mock.Mock()})
    def test_get_env_var_from_colab(self):
        """Verifies environment variables are read from Colab secrets."""
        mock_colab = sys.modules["google.colab"]
        mock_colab.userdata.get.return_value = "colab-value"

        self.assertEqual(coreutils.get_env_var("key"), "colab-value")
        mock_colab.userdata.get.assert_called_once_with("key")

    @mock.patch.dict(os.environ, {"key": "environ-value"})
    @mock.patch.dict("sys.modules", {"google.colab": mock.Mock()})
    def test_get_env_var_colab_fails_fallback_to_env(self):
        """Verifies environment variables are read if a Colab secret read fails."""
        mock_colab = sys.modules["google.colab"]
        mock_colab.userdata.SecretNotFoundError = FakeSecretNotFoundError
        mock_colab.userdata.NotebookAccessError = FakeNotebookAccessError
        mock_colab.userdata.get.side_effect = FakeNotebookAccessError()

        self.assertEqual(coreutils.get_env_var("key"), "environ-value")

    def test_build_computed_object_tree_feature(self):
        """Tests building a JSON computed object tree for a Feature."""
        tree = coreutils.build_computed_object_tree(ee.Feature({}))
        expected = _read_json_file("feature_tree.json")
        self.assertEqual(tree, expected)

    def test_build_computed_object_tree_image(self):
        """Tests building a JSON computed object tree for an Image."""
        tree = coreutils.build_computed_object_tree(ee.Image(0))
        expected = _read_json_file("image_tree.json")
        self.assertEqual(tree, expected)

    def test_build_computed_object_tree_image_collection(self):
        """Tests building a JSON computed object tree for an ImageCollection."""
        tree = coreutils.build_computed_object_tree(ee.ImageCollection([ee.Image(0)]))
        expected = _read_json_file("image_collection_tree.json")
        self.assertEqual(tree, expected)


class TestHelpers(unittest.TestCase):

    def test_hex_to_rgb(self):
        """Tests hex_to_rgb."""
        self.assertEqual(coreutils.hex_to_rgb(), (255, 255, 255))
        self.assertEqual(coreutils.hex_to_rgb("FFFFFF"), (255, 255, 255))
        self.assertEqual(coreutils.hex_to_rgb("#FFFFFF"), (255, 255, 255))
        self.assertEqual(coreutils.hex_to_rgb("000000"), (0, 0, 0))
        self.assertEqual(coreutils.hex_to_rgb("ff0000"), (255, 0, 0))
        self.assertEqual(coreutils.hex_to_rgb("00ff00"), (0, 255, 0))
        self.assertEqual(coreutils.hex_to_rgb("0000ff"), (0, 0, 255))
        self.assertEqual(coreutils.hex_to_rgb("FFF"), (15, 15, 15))
        self.assertEqual(coreutils.hex_to_rgb("#ABC"), (10, 11, 12))
        self.assertEqual(coreutils.hex_to_rgb("000"), (0, 0, 0))
        with self.assertRaises(ValueError):
            coreutils.hex_to_rgb("garbage")

    def test_random_string(self):
        """Tests random_string."""
        s = coreutils.random_string()
        self.assertEqual(len(s), 3)
        self.assertTrue(all(c in string.ascii_lowercase for c in s))

        s = coreutils.random_string(10)
        self.assertEqual(len(s), 10)
        self.assertTrue(all(c in string.ascii_lowercase for c in s))

    def test_github_raw_url(self):
        url = "https://github.com/opengeos/geemap/blob/master/geemap/geemap.py"
        expected = (
            "https://raw.githubusercontent.com/opengeos/geemap/master/geemap/geemap.py"
        )
        self.assertEqual(coreutils.github_raw_url(url), expected)

        url = "https://example.com/file.txt"
        self.assertEqual(coreutils.github_raw_url(url), url)

        url = "https://github.com/opengeos/geemap"
        self.assertEqual(coreutils.github_raw_url(url), url)

        url = 123
        self.assertEqual(
            coreutils.github_raw_url(url), url
        )  # pytype: disable=wrong-arg-types

    def test_temp_file_path(self):
        """Tests temp_file_path."""
        path = coreutils.temp_file_path("txt")
        self.assertIsInstance(path, str)
        self.assertTrue(path.startswith(tempfile.gettempdir()))
        self.assertTrue(path.endswith(".txt"))
        filename = os.path.basename(path)
        file_id, _ = os.path.splitext(filename)
        try:
            uuid.UUID(file_id, version=4)
        except ValueError:
            self.fail("file id is not a valid UUID4")

        path2 = coreutils.temp_file_path(".geojson")
        self.assertTrue(path2.endswith(".geojson"))
        filename2 = os.path.basename(path2)
        file_id2, _ = os.path.splitext(filename2)
        try:
            uuid.UUID(file_id2, version=4)
        except ValueError:
            self.fail("file id is not a valid UUID4")


if __name__ == "__main__":
    unittest.main()
