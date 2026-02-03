"""Tests for the ml module."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

import numpy as np

from tests.mocks import mock_ee


class MockTree:

    def __init__(
        self,
        n_nodes: int = 7,
        n_classes: int = 2,
        is_classifier: bool = True,
    ) -> None:
        self.node_count = n_nodes
        self.children_left = np.array([1, 2, -1, -1, 5, -1, -1])
        self.children_right = np.array([4, 3, -1, -1, 6, -1, -1])
        self.feature = np.array([0, 1, -2, -2, 0, -2, -2])
        self.impurity = np.array([0.5, 0.4, 0.0, 0.0, 0.3, 0.0, 0.0])
        self.n_node_samples = np.array([100, 60, 30, 30, 40, 20, 20])
        self.threshold = np.array([0.5, 0.3, -2.0, -2.0, 0.7, -2.0, -2.0])

        if is_classifier:
            self.value = np.array([
                [[50, 50]],
                [[40, 20]],
                [[30, 0]],
                [[10, 20]],
                [[10, 30]],
                [[5, 15]],
                [[5, 15]],
            ])
        else:
            self.value = np.array([0.5, 0.4, 0.3, 0.5, 0.6, 0.7, 0.8])


class MockDecisionTreeClassifier:

    def __init__(self, n_nodes: int = 7, n_classes: int = 2) -> None:
        self.tree_ = MockTree(n_nodes=n_nodes, n_classes=n_classes, is_classifier=True)


class MockDecisionTreeRegressor:

    def __init__(self, n_nodes: int = 7) -> None:
        self.tree_ = MockTree(n_nodes=n_nodes, is_classifier=False)


class MockRandomForestClassifier:

    def __init__(self, n_estimators: int = 3) -> None:
        self.estimators_ = [MockDecisionTreeClassifier() for _ in range(n_estimators)]
        self.criterion = "gini"
        self.classes_ = np.array([0, 1])


class MockRandomForestRegressor:

    def __init__(self, n_estimators: int = 3) -> None:
        self.estimators_ = [MockDecisionTreeRegressor() for _ in range(n_estimators)]
        self.criterion = "mse"


class TestTreeToString(unittest.TestCase):

    def test_tree_to_string_valid_tree(self) -> None:
        from geemap import ml

        estimator = MockDecisionTreeClassifier()
        feature_names = ["band1", "band2"]

        result = ml.tree_to_string(estimator, feature_names)

        self.assertIsInstance(result, str)
        self.assertIn("root", result)
        self.assertIn("band1", result)

    def test_tree_to_string_classification_mode(self) -> None:
        from geemap import ml

        estimator = MockDecisionTreeClassifier()
        feature_names = ["band1", "band2"]

        result = ml.tree_to_string(
            estimator, feature_names, output_mode="CLASSIFICATION"
        )

        self.assertIsInstance(result, str)
        self.assertIn("root", result)

    def test_tree_to_string_regression_mode(self) -> None:
        from geemap import ml

        estimator = MockDecisionTreeRegressor()
        feature_names = ["band1", "band2"]

        result = ml.tree_to_string(estimator, feature_names, output_mode="REGRESSION")

        self.assertIsInstance(result, str)
        self.assertIn("root", result)

    def test_tree_to_string_probability_mode(self) -> None:
        from geemap import ml

        estimator = MockDecisionTreeClassifier()
        feature_names = ["band1", "band2"]

        result = ml.tree_to_string(
            estimator, feature_names, output_mode="PROBABILITY"
        )

        self.assertIsInstance(result, str)
        self.assertIn("root", result)

    def test_tree_to_string_with_labels(self) -> None:
        from geemap import ml

        estimator = MockDecisionTreeClassifier()
        feature_names = ["band1", "band2"]
        labels = [10, 20]

        result = ml.tree_to_string(
            estimator, feature_names, labels=labels, output_mode="CLASSIFICATION"
        )

        self.assertIsInstance(result, str)
        self.assertIn("root", result)

    def test_tree_to_string_infer_classification(self) -> None:
        from geemap import ml

        estimator = MockDecisionTreeClassifier()
        feature_names = ["band1", "band2"]

        result = ml.tree_to_string(estimator, feature_names, output_mode="INFER")

        self.assertIsInstance(result, str)

    def test_tree_to_string_infer_regression(self) -> None:
        from geemap import ml

        estimator = MockDecisionTreeRegressor()
        feature_names = ["band1", "band2"]

        result = ml.tree_to_string(estimator, feature_names, output_mode="INFER")

        self.assertIsInstance(result, str)

    def test_tree_to_string_multiprobability_raises(self) -> None:
        from geemap import ml

        estimator = MockDecisionTreeClassifier()
        feature_names = ["band1", "band2"]

        with self.assertRaises(NotImplementedError):
            ml.tree_to_string(
                estimator, feature_names, output_mode="MULTIPROBABILITY"
            )

    def test_tree_to_string_invalid_mode_raises(self) -> None:
        from geemap import ml

        estimator = MockDecisionTreeClassifier()
        feature_names = ["band1", "band2"]

        with self.assertRaises(RuntimeError):
            ml.tree_to_string(estimator, feature_names, output_mode="INVALID")


class TestRfToStrings(unittest.TestCase):

    @mock.patch("geemap.ml.mp.Pool")
    def test_rf_to_strings_valid_forest(self, mock_pool: mock.Mock) -> None:
        from geemap import ml

        mock_pool_instance = mock.MagicMock()
        mock_pool.return_value.__enter__.return_value = mock_pool_instance
        mock_result = mock.MagicMock()
        mock_result.get.return_value = ["tree1", "tree2", "tree3"]
        mock_pool_instance.map_async.return_value = mock_result

        estimator = MockRandomForestClassifier(n_estimators=3)
        feature_names = ["band1", "band2"]

        result = ml.rf_to_strings(estimator, feature_names)

        self.assertEqual(len(result), 3)

    @mock.patch("geemap.ml.mp.Pool")
    def test_rf_to_strings_regression(self, mock_pool: mock.Mock) -> None:
        from geemap import ml

        mock_pool_instance = mock.MagicMock()
        mock_pool.return_value.__enter__.return_value = mock_pool_instance
        mock_result = mock.MagicMock()
        mock_result.get.return_value = ["tree1", "tree2"]
        mock_pool_instance.map_async.return_value = mock_result

        estimator = MockRandomForestRegressor(n_estimators=2)
        feature_names = ["band1", "band2"]

        result = ml.rf_to_strings(estimator, feature_names, output_mode="REGRESSION")

        self.assertEqual(len(result), 2)

    def test_rf_to_strings_invalid_mode_raises(self) -> None:
        from geemap import ml

        estimator = MockRandomForestClassifier()
        feature_names = ["band1", "band2"]

        with self.assertRaises(ValueError):
            ml.rf_to_strings(estimator, feature_names, output_mode="INVALID_MODE")

    @mock.patch("geemap.ml.mp.Pool")
    @mock.patch("geemap.ml.mp.cpu_count", return_value=4)
    def test_rf_to_strings_respects_cpu_limit(
        self, mock_cpu_count: mock.Mock, mock_pool: mock.Mock
    ) -> None:
        from geemap import ml

        mock_pool_instance = mock.MagicMock()
        mock_pool.return_value.__enter__.return_value = mock_pool_instance
        mock_result = mock.MagicMock()
        mock_result.get.return_value = ["tree1"]
        mock_pool_instance.map_async.return_value = mock_result

        estimator = MockRandomForestClassifier(n_estimators=1)
        feature_names = ["band1", "band2"]

        ml.rf_to_strings(estimator, feature_names, processes=10)

        mock_pool.assert_called_once_with(3)


class TestStringsToClassifier(unittest.TestCase):

    @mock.patch("geemap.ml.ee", mock_ee)
    def test_strings_to_classifier_valid_input(self) -> None:
        from geemap import ml

        trees = ["1) root 100 9999 9999", "1) root 100 9999 9999"]

        result = ml.strings_to_classifier(trees)

        self.assertIsInstance(result, mock_ee.Classifier)

    @mock.patch("geemap.ml.ee", mock_ee)
    def test_strings_to_classifier_empty_list(self) -> None:
        from geemap import ml

        trees = []

        result = ml.strings_to_classifier(trees)

        self.assertIsInstance(result, mock_ee.Classifier)

    @mock.patch("geemap.ml.ee", mock_ee)
    def test_strings_to_classifier_single_tree(self) -> None:
        from geemap import ml

        trees = ["1) root 100 9999 9999 (0.5)\n  2) band1 <= 0.5 50 0.4 0"]

        result = ml.strings_to_classifier(trees)

        self.assertIsInstance(result, mock_ee.Classifier)


class TestFcToClassifier(unittest.TestCase):

    @mock.patch("geemap.ml.ee", mock_ee)
    def test_fc_to_classifier_valid_fc(self) -> None:
        from geemap import ml

        fc = mock_ee.FeatureCollection()

        result = ml.fc_to_classifier(fc)

        self.assertIsInstance(result, mock_ee.Classifier)


class TestExportTreesToFc(unittest.TestCase):

    @mock.patch("geemap.ml.ee", mock_ee)
    def test_export_trees_to_fc_starts_task(self) -> None:
        from geemap import ml

        trees = ["1) root 100\n  2) band1 <= 0.5", "1) root 100\n  2) band2 > 0.3"]
        asset_id = "users/test/rf_export"

        ml.export_trees_to_fc(trees, asset_id)

    @mock.patch("geemap.ml.ee", mock_ee)
    def test_export_trees_to_fc_custom_description(self) -> None:
        from geemap import ml

        trees = ["1) root 100"]
        asset_id = "users/test/rf_export"

        ml.export_trees_to_fc(trees, asset_id, description="custom_export")


class TestTreesToCsv(unittest.TestCase):

    def test_trees_to_csv_creates_file(self) -> None:
        from geemap import ml

        trees = ["1) root 100\n  2) band1 <= 0.5", "1) root 100\n  2) band2 > 0.3"]

        with tempfile.TemporaryDirectory() as tmpdir:
            out_csv = os.path.join(tmpdir, "trees.csv")
            ml.trees_to_csv(trees, out_csv)
            self.assertTrue(os.path.exists(out_csv))

    def test_trees_to_csv_correct_content(self) -> None:
        from geemap import ml

        trees = ["1) root 100\n  2) band1 <= 0.5", "1) root 100\n  2) band2 > 0.3"]

        with tempfile.TemporaryDirectory() as tmpdir:
            out_csv = os.path.join(tmpdir, "trees.csv")
            ml.trees_to_csv(trees, out_csv)

            with open(out_csv) as f:
                lines = f.readlines()

            self.assertEqual(len(lines), 2)
            self.assertIn("#", lines[0])

    def test_trees_to_csv_empty_list(self) -> None:
        from geemap import ml

        trees = []

        with tempfile.TemporaryDirectory() as tmpdir:
            out_csv = os.path.join(tmpdir, "trees.csv")
            ml.trees_to_csv(trees, out_csv)

            with open(out_csv) as f:
                content = f.read()

            self.assertEqual(content, "")


class TestCsvToClassifier(unittest.TestCase):

    @mock.patch("geemap.ml.ee", mock_ee)
    def test_csv_to_classifier_valid_csv(self) -> None:
        from geemap import ml

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "trees.csv")
            with open(csv_path, "w") as f:
                f.write("1) root 100#  2) band1 <= 0.5\n")
                f.write("1) root 100#  2) band2 > 0.3\n")

            result = ml.csv_to_classifier(csv_path)

            self.assertIsInstance(result, mock_ee.Classifier)

    @mock.patch("geemap.ml.ee", mock_ee)
    def test_csv_to_classifier_missing_file(self) -> None:
        from geemap import ml

        result = ml.csv_to_classifier("/nonexistent/path/trees.csv")

        self.assertIsNone(result)

    @mock.patch("geemap.ml.ee", mock_ee)
    def test_csv_to_classifier_empty_csv(self) -> None:
        from geemap import ml

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "empty.csv")
            with open(csv_path, "w") as f:
                pass

            result = ml.csv_to_classifier(csv_path)

            self.assertIsInstance(result, mock_ee.Classifier)


if __name__ == "__main__":
    unittest.main()
