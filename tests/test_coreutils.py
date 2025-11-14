#!/usr/bin/env python
"""Tests for `coreutils` module."""
import json
import os
import sys
from typing import Any
import unittest
from unittest import mock

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
    with open(file_path, "r", encoding="utf-8") as f:
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


if __name__ == "__main__":
    unittest.main()
