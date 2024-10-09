#!/usr/bin/env python

"""Tests for `coreutils` module."""
import os
import sys
import unittest
from unittest import mock

from geemap import coreutils


class FakeSecretNotFoundError(Exception):
    """google.colab.userdata.SecretNotFoundError fake."""


class FakeNotebookAccessError(Exception):
    """google.colab.userdata.NotebookAccessError fake."""


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
