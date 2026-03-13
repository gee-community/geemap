import multiprocessing
import pathlib
import tempfile
import unittest
from unittest import mock

try:
    import numpy as np
    import sklearn.ensemble
    import sklearn.tree

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

import ee

from geemap import ml


class TestML(unittest.TestCase):
    @unittest.skipIf(not HAS_SKLEARN, "sklearn not installed")
    def test_tree_to_string_classification(self):
        # Create a simple decision tree classifier.
        X = np.array([[0, 0], [1, 1], [0, 1], [1, 0]])
        y = np.array([0, 1, 1, 0])
        clf = sklearn.tree.DecisionTreeClassifier(max_depth=2, random_state=42)
        clf.fit(X, y)

        tree_str = ml.tree_to_string(
            clf, feature_names=["f1", "f2"], output_mode="CLASSIFICATION"
        )
        self.assertIsInstance(tree_str, str)
        self.assertTrue(tree_str.startswith("1) root"))

    @unittest.skipIf(not HAS_SKLEARN, "sklearn not installed")
    def test_tree_to_string_regression(self):
        # Create a simple decision tree regressor.
        X = np.array([[0, 0], [1, 1], [0, 1], [1, 0]])
        y = np.array([0.1, 0.9, 0.8, 0.2])
        reg = sklearn.tree.DecisionTreeRegressor(max_depth=2, random_state=42)
        reg.fit(X, y)

        tree_str = ml.tree_to_string(
            reg, feature_names=["f1", "f2"], output_mode="REGRESSION"
        )
        self.assertIsInstance(tree_str, str)
        self.assertTrue(tree_str.startswith("1) root"))

    @unittest.skipIf(not HAS_SKLEARN, "sklearn not installed")
    @mock.patch.object(multiprocessing, "Pool")
    def test_rf_to_strings(self, mock_pool):
        # We need to mock multiprocessing because we don't want to actually spin up processes.
        mock_pool_instance = mock_pool.return_value.__enter__.return_value
        # Mock map_async to return a mock result.
        mock_async_result = mock.MagicMock()
        mock_async_result.get.return_value = ["tree1_str", "tree2_str"]
        mock_pool_instance.map_async.return_value = mock_async_result

        X = np.array([[0, 0], [1, 1], [0, 1], [1, 0]])
        y = np.array([0, 1, 1, 0])
        rf = sklearn.ensemble.RandomForestClassifier(
            n_estimators=2, max_depth=2, random_state=42
        )
        rf.fit(X, y)

        # Mock classes_ to avoid issues if output_mode INFER logic needs it.
        rf.classes_ = np.array([0, 1])
        # Set criterion to gini so INFER mode knows it's a classifier.
        rf.criterion = "gini"

        trees = ml.rf_to_strings(
            rf, feature_names=["f1", "f2"], processes=1, output_mode="CLASSIFICATION"
        )
        self.assertEqual(len(trees), 2)
        self.assertEqual(trees[0], "tree1_str")
        self.assertEqual(trees[1], "tree2_str")

    @mock.patch.object(ee.Classifier, "decisionTreeEnsemble")
    @mock.patch.object(ee, "String")
    def test_strings_to_classifier(self, mock_ee_string, mock_ensemble):
        mock_ensemble.return_value = "mocked_classifier"
        mock_ee_string.side_effect = lambda x: x

        trees = ["tree1", "tree2"]
        classifier = ml.strings_to_classifier(trees)
        self.assertEqual(classifier, "mocked_classifier")
        mock_ensemble.assert_called_once()
        mock_ee_string.assert_any_call("tree1")

    @mock.patch.object(ee.Classifier, "decisionTreeEnsemble")
    def test_fc_to_classifier(self, mock_ensemble):
        mock_ensemble.return_value = "mocked_classifier"

        # Mock ee.FeatureCollection and its aggregate_array method.
        mock_fc = mock.MagicMock()
        mock_aggregate = mock.MagicMock()
        # The map function should return a list-like of ee.Strings, we'll just return a list.
        mock_aggregate.map.return_value = ["tree1\n", "tree2\n"]
        mock_fc.aggregate_array.return_value = mock_aggregate

        classifier = ml.fc_to_classifier(mock_fc)
        self.assertEqual(classifier, "mocked_classifier")
        mock_ensemble.assert_called_once()
        mock_fc.aggregate_array.assert_called_with("tree")

    @mock.patch.object(ee.batch.Export.table, "toAsset")
    @mock.patch.object(ee, "FeatureCollection")
    @mock.patch.object(ee, "Feature")
    @mock.patch.object(ee.Geometry, "Point")
    def test_export_trees_to_fc(self, mock_point, mock_feature, mock_fc, mock_to_asset):
        mock_task = mock.MagicMock()
        mock_to_asset.return_value = mock_task
        mock_point.return_value = "mocked_point"
        mock_feature.return_value = "mocked_feature"
        mock_fc.return_value = "mocked_fc"

        trees = ["tree1\n", "tree2\n"]
        ml.export_trees_to_fc(trees, asset_id="users/test/test_rf")

        mock_to_asset.assert_called_once_with(
            collection="mocked_fc",
            description="geemap_rf_export",
            assetId="users/test/test_rf",
        )
        mock_task.start.assert_called_once()

    def test_trees_to_csv(self):
        trees = ["tree1\n", "tree2\n"]
        with tempfile.TemporaryDirectory() as temp_dir:
            out_csv = pathlib.Path(temp_dir) / "test_trees.csv"
            ml.trees_to_csv(trees, str(out_csv))
            self.assertTrue(out_csv.exists())

            content = out_csv.read_text(encoding="utf-8")
            self.assertIn("tree1#", content)
            self.assertIn("tree2#", content)

    @mock.patch.object(ml, "fc_to_classifier")
    @mock.patch.object(ee, "FeatureCollection")
    @mock.patch.object(ee, "Feature")
    @mock.patch.object(ee.Geometry, "Point")
    def test_csv_to_classifier(
        self, mock_point, mock_feature, mock_fc, mock_fc_to_classifier
    ):
        mock_fc_to_classifier.return_value = "mocked_classifier"

        trees = ["tree1", "tree2"]
        with tempfile.TemporaryDirectory() as temp_dir:
            out_csv = pathlib.Path(temp_dir) / "test_trees.csv"
            out_csv.write_text("\n".join(trees), encoding="utf-8")

            classifier = ml.csv_to_classifier(str(out_csv))
            self.assertEqual(classifier, "mocked_classifier")
            mock_fc_to_classifier.assert_called_once()

    def test_csv_to_classifier_file_not_found(self):
        classifier = ml.csv_to_classifier("non_existent_file.csv")
        self.assertIsNone(classifier)

    @unittest.skipIf(not HAS_SKLEARN, "sklearn not installed")
    def test_tree_to_string_infer_classification(self):
        X = np.array([[0, 0], [1, 1], [0, 1], [1, 0]])
        y = np.array([0, 1, 1, 0])
        clf = sklearn.tree.DecisionTreeClassifier(max_depth=2, random_state=42)
        clf.fit(X, y)
        tree_str = ml.tree_to_string(
            clf, feature_names=["f1", "f2"], output_mode="INFER"
        )
        self.assertIsInstance(tree_str, str)

    @unittest.skipIf(not HAS_SKLEARN, "sklearn not installed")
    def test_tree_to_string_infer_regression(self):
        X = np.array([[0, 0], [1, 1], [0, 1], [1, 0]])
        y = np.array([0.1, 0.9, 0.8, 0.2])
        reg = sklearn.tree.DecisionTreeRegressor(max_depth=2, random_state=42)
        reg.fit(X, y)
        tree_str = ml.tree_to_string(
            reg, feature_names=["f1", "f2"], output_mode="INFER"
        )
        self.assertIsInstance(tree_str, str)

    @unittest.skipIf(not HAS_SKLEARN, "sklearn not installed")
    def test_tree_to_string_infer_runtime_error(self):
        X = np.array([[0, 0], [1, 1]])
        y = np.array([0, 1])
        clf = sklearn.tree.DecisionTreeClassifier(max_depth=2, random_state=42)
        clf.fit(X, y)
        # Manually mess up the shape of raw_vals via mocking the shape.
        with mock.patch.object(np, "squeeze") as mock_squeeze:
            mock_arr = mock.MagicMock()
            mock_arr.ndim = 3
            mock_squeeze.return_value = mock_arr
            with self.assertRaisesRegex(
                RuntimeError, "Could not infer the output type from the estimator"
            ):
                ml.tree_to_string(clf, feature_names=["f1", "f2"], output_mode="INFER")

    @unittest.skipIf(not HAS_SKLEARN, "sklearn not installed")
    def test_tree_to_string_classification_labels(self):
        X = np.array([[0, 0], [1, 1]])
        y = np.array([0, 1])
        clf = sklearn.tree.DecisionTreeClassifier(max_depth=2, random_state=42)
        clf.fit(X, y)
        tree_str = ml.tree_to_string(
            clf,
            feature_names=["f1", "f2"],
            output_mode="CLASSIFICATION",
            labels=[10, 20],
        )
        self.assertIsInstance(tree_str, str)

    @unittest.skipIf(not HAS_SKLEARN, "sklearn not installed")
    def test_tree_to_string_probability(self):
        X = np.array([[0, 0], [1, 1], [0, 1], [1, 0]])
        y = np.array([0, 1, 1, 0])
        clf = sklearn.tree.DecisionTreeClassifier(max_depth=2, random_state=42)
        clf.fit(X, y)
        tree_str = ml.tree_to_string(
            clf, feature_names=["f1", "f2"], output_mode="PROBABILITY"
        )
        self.assertIsInstance(tree_str, str)

    @unittest.skipIf(not HAS_SKLEARN, "sklearn not installed")
    def test_tree_to_string_probability_value_error(self):
        # Trigger ValueError if raw_vals.shape[-1] != 2.
        X = np.array([[0, 0], [1, 1], [0, 1], [1, 0]])
        y = np.array([0, 1, 2, 0])  # 3 classes.
        clf = sklearn.tree.DecisionTreeClassifier(max_depth=2, random_state=42)
        clf.fit(X, y)
        with self.assertRaisesRegex(ValueError, "shape mismatch: outputs from trees"):
            ml.tree_to_string(
                clf, feature_names=["f1", "f2"], output_mode="PROBABILITY"
            )

    @unittest.skipIf(not HAS_SKLEARN, "sklearn not installed")
    def test_tree_to_string_multiprobability(self):
        X = np.array([[0, 0], [1, 1]])
        y = np.array([0, 1])
        clf = sklearn.tree.DecisionTreeClassifier(max_depth=2, random_state=42)
        clf.fit(X, y)
        with self.assertRaisesRegex(
            NotImplementedError, "Currently multiprobability output is not support"
        ):
            ml.tree_to_string(
                clf, feature_names=["f1", "f2"], output_mode="MULTIPROBABILITY"
            )

    @unittest.skipIf(not HAS_SKLEARN, "sklearn not installed")
    def test_tree_to_string_unknown_output_mode(self):
        X = np.array([[0, 0], [1, 1]])
        y = np.array([0, 1])
        clf = sklearn.tree.DecisionTreeClassifier(max_depth=2, random_state=42)
        clf.fit(X, y)
        with self.assertRaisesRegex(
            RuntimeError,
            "Could not understand estimator type and parse out the values.",
        ):
            ml.tree_to_string(clf, feature_names=["f1", "f2"], output_mode="UNKNOWN")

    @unittest.skipIf(not HAS_SKLEARN, "sklearn not installed")
    def test_tree_to_string_left_right_leaves(self):
        # Create a tree structured specifically to hit the specific branch coverage
        # for left/right nodes being leaves (lines 211-215, 227-231).

        # Left leaf tree.
        X1 = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
        y1 = np.array([0, 0, 1, 0])
        clf1 = sklearn.tree.DecisionTreeClassifier(random_state=42)
        clf1.fit(X1, y1)
        tree_str1 = ml.tree_to_string(
            clf1, feature_names=["f1", "f2"], output_mode="CLASSIFICATION"
        )
        self.assertIsInstance(tree_str1, str)

        # Right leaf tree.
        X2 = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
        y2 = np.array([0, 1, 0, 0])
        clf2 = sklearn.tree.DecisionTreeClassifier(random_state=42)
        clf2.fit(X2, y2)
        tree_str2 = ml.tree_to_string(
            clf2, feature_names=["f1", "f2"], output_mode="CLASSIFICATION"
        )
        self.assertIsInstance(tree_str2, str)

    @unittest.skipIf(not HAS_SKLEARN, "sklearn not installed")
    def test_rf_to_strings_invalid_output_mode(self):
        X = np.array([[0, 0], [1, 1]])
        y = np.array([0, 1])
        rf = sklearn.ensemble.RandomForestClassifier(n_estimators=2, random_state=42)
        rf.fit(X, y)
        with self.assertRaisesRegex(
            ValueError, "The provided output_mode is not available."
        ):
            ml.rf_to_strings(rf, feature_names=["f1", "f2"], output_mode="INVALID")

    @unittest.skipIf(not HAS_SKLEARN, "sklearn not installed")
    @mock.patch.object(multiprocessing, "Pool")
    def test_rf_to_strings_infer_classification(self, mock_pool):
        mock_pool_instance = mock_pool.return_value.__enter__.return_value
        mock_async_result = mock.MagicMock()
        mock_async_result.get.return_value = ["tree1", "tree2"]
        mock_pool_instance.map_async.return_value = mock_async_result

        X = np.array([[0, 0], [1, 1]])
        y = np.array([0, 1])
        rf = sklearn.ensemble.RandomForestClassifier(n_estimators=2, random_state=42)
        rf.fit(X, y)

        trees = ml.rf_to_strings(rf, feature_names=["f1", "f2"], output_mode="INFER")
        self.assertEqual(len(trees), 2)

    @unittest.skipIf(not HAS_SKLEARN, "sklearn not installed")
    @mock.patch.object(multiprocessing, "Pool")
    def test_rf_to_strings_infer_regression(self, mock_pool):
        mock_pool_instance = mock_pool.return_value.__enter__.return_value
        mock_async_result = mock.MagicMock()
        mock_async_result.get.return_value = ["tree1", "tree2"]
        mock_pool_instance.map_async.return_value = mock_async_result

        X = np.array([[0, 0], [1, 1]])
        y = np.array([0.1, 0.9])
        rf = sklearn.ensemble.RandomForestRegressor(n_estimators=2, random_state=42)
        rf.fit(X, y)
        # Force criterion to squared_error (which used to be mse) or mae.
        rf.criterion = "mse"

        trees = ml.rf_to_strings(rf, feature_names=["f1", "f2"], output_mode="INFER")
        self.assertEqual(len(trees), 2)

    @unittest.skipIf(not HAS_SKLEARN, "sklearn not installed")
    def test_rf_to_strings_infer_error(self):
        X = np.array([[0, 0], [1, 1]])
        y = np.array([0, 1])
        rf = sklearn.ensemble.RandomForestClassifier(n_estimators=2, random_state=42)
        rf.fit(X, y)
        rf.criterion = "unknown_criterion"
        with self.assertRaisesRegex(
            RuntimeError, "Could not infer the output type from the estimator."
        ):
            ml.rf_to_strings(rf, feature_names=["f1", "f2"], output_mode="INFER")

    @unittest.skipIf(not HAS_SKLEARN, "sklearn not installed")
    @mock.patch.object(multiprocessing, "Pool")
    def test_rf_to_strings_probability(self, mock_pool):
        mock_pool_instance = mock_pool.return_value.__enter__.return_value
        mock_async_result = mock.MagicMock()
        mock_async_result.get.return_value = ["tree1", "tree2"]
        mock_pool_instance.map_async.return_value = mock_async_result

        X = np.array([[0, 0], [1, 1]])
        y = np.array([0, 1])
        rf = sklearn.ensemble.RandomForestClassifier(n_estimators=2, random_state=42)
        rf.fit(X, y)

        trees = ml.rf_to_strings(
            rf, feature_names=["f1", "f2"], output_mode="PROBABILITY"
        )
        self.assertEqual(len(trees), 2)

    @unittest.skipIf(not HAS_SKLEARN, "sklearn not installed")
    @mock.patch.object(multiprocessing, "cpu_count")
    @mock.patch.object(multiprocessing, "Pool")
    def test_rf_to_strings_processes_limit(self, mock_pool, mock_cpu_count):
        mock_cpu_count.return_value = 2
        mock_pool_instance = mock_pool.return_value.__enter__.return_value
        mock_async_result = mock.MagicMock()
        mock_async_result.get.return_value = ["tree1", "tree2"]
        mock_pool_instance.map_async.return_value = mock_async_result

        X = np.array([[0, 0], [1, 1]])
        y = np.array([0, 1])
        rf = sklearn.ensemble.RandomForestClassifier(n_estimators=2, random_state=42)
        rf.fit(X, y)
        rf.criterion = "gini"

        # Requesting 10 processes, but cpu_count is 2, so it should cap at 1.
        trees = ml.rf_to_strings(
            rf, feature_names=["f1", "f2"], output_mode="CLASSIFICATION", processes=10
        )
        self.assertEqual(len(trees), 2)
        # Ensure Pool was called with processes=1.
        mock_pool.assert_called_with(1)


if __name__ == "__main__":
    unittest.main()
