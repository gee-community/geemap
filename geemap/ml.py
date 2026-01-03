"Module for machine learning with Google Earth Engine."

# *******************************************************************************#
# This module contains extra features of the geemap package.                     #
# The geemap community will maintain the extra features.                         #
# *******************************************************************************#

from functools import partial
import multiprocessing as mp
import os

import ee
import numpy as np
import pandas as pd


def tree_to_string(
    estimator, feature_names, labels=None, output_mode: str = "INFER"
) -> str:
    """Convert a sklearn decision tree object to a string format that EE can interpret

    Args:
        estimator (sklearn.tree.estimator): An estimator consisting of multiple decision
            tree classifiers. Expects object to contain estimators_ attribute
        feature_names (Iterable[str]): List of strings that define the name of features
            (i.e., bands) used to create the model
        labels (Iterable[numeric]): List of class labels to map outputs to, must be
            numeric values. If None, then raw outputs will be used. default = None
        output_mode: the output mode of the estimator. Options are "INFER",
            "CLASSIFIATION", or "REGRESSION" (capitalization does not matter). default =
            "INFER"

    Returns:
        tree_str (str): string representation of decision tree estimator

    Raises:
        RuntimeError: raises run time error when function cannot determine if the
            estimator is for regression or classification problem.
    """

    # Extract out the information need to build the tree string.
    n_nodes = estimator.tree_.node_count
    children_left = estimator.tree_.children_left
    children_right = estimator.tree_.children_right
    feature_idx = estimator.tree_.feature
    impurities = estimator.tree_.impurity
    n_samples = estimator.tree_.n_node_samples
    thresholds = estimator.tree_.threshold
    features = [feature_names[i] for i in feature_idx]

    raw_vals = np.squeeze(estimator.tree_.value)

    # First check if user wants to infer output mode.
    # If so, reset the output_mode variable to a valid mode.
    if output_mode == "INFER":
        if raw_vals.ndim == 2:
            output_mode = "CLASSIFICATION"

        elif raw_vals.ndim == 1:
            output_mode = "REGRESSION"

        else:
            raise RuntimeError(
                "Could not infer the output type from the estimator. "
                "Please explicitly provide the output_mode."
            )

    # Second check on the output mode after the inference.
    if output_mode == "CLASSIFICATION":
        # Take argmax along class axis from values.
        values = raw_vals.argmax(axis=-1)
        if labels is not None:
            index_labels = np.unique(values)
            lookup = {idx: labels[i] for i, idx in enumerate(index_labels)}
            values = [lookup[v] for v in values]

        out_type = int

    elif output_mode == "REGRESSION":
        # Take values and drop un needed axis.
        values = np.around(raw_vals, decimals=6)
        out_type = float

    elif output_mode == "PROBABILITY":
        # Calculate fraction of samples of the same class in a leaf.
        # Currently only supporting binary classifications.
        # Check if n classes == 2 (i.e., binary classes).
        if raw_vals.shape[-1] != 2:
            raise ValueError(
                "shape mismatch: outputs from trees = {raw_vals.shape[-1]} classes. "
                "Currently probability outputs is support for binary classifications."
            )

        probas = np.around(
            (raw_vals / np.sum(raw_vals, axis=1)[:, np.newaxis]), decimals=6
        )

        values = probas[:, -1]
        out_type = float

    elif output_mode == "MULTIPROBABILITY":
        # Calculate fraction of samples of the same class in a leaf.
        # This is a 2-d array making the output multidimensional.
        raise NotImplementedError(
            "Currently multiprobability output is not support. "
            "Please choose one of the following output modes: "
            "['CLASSIFIATION', 'REGRESSION', 'PROBABILITY' or 'INFER']"
        )
    else:
        raise RuntimeError(
            "Could not understand estimator type and parse out the values."
        )

    # Use iterative pre-order search to extract node depth and leaf information.
    node_ids = np.zeros(shape=n_nodes, dtype=np.int64)
    node_depth = np.zeros(shape=n_nodes, dtype=np.int64)
    is_leaves = np.zeros(shape=n_nodes, dtype=bool)
    stack = [(0, -1)]  # Seed is the root node id and its parent depth.
    while len(stack) > 0:
        node_id, parent_depth = stack.pop()
        node_depth[node_id] = parent_depth + 1
        node_ids[node_id] = node_id

        # If we have a test node.
        if children_left[node_id] != children_right[node_id]:
            stack.append((children_left[node_id], parent_depth + 1))
            stack.append((children_right[node_id], parent_depth + 1))
        else:
            is_leaves[node_id] = True

    # Create a table of the initial structure.
    # Each row is a node or leaf.
    df = pd.DataFrame(
        {
            "node_id": node_ids,
            "node_depth": node_depth,
            "is_leaf": is_leaves,
            "children_left": children_left,
            "children_right": children_right,
            "value": values,
            "criterion": impurities,
            "n_samples": n_samples,
            "threshold": thresholds,
            "feature_name": features,
            "sign": ["<="] * n_nodes,
        },
        dtype="object",
    )

    # The table representation does not have lef vs right node structure.
    # So we need to add in right nodes in the correct location.
    # We do this by first calculating which nodes are right and
    # then insert them at the correct index.

    # Get a dict of right node rows and assign key based on index where to insert.
    inserts = {}
    for row in df.itertuples():
        child_r = row.children_right
        if child_r > row.Index:
            ordered_row = np.array(row)
            ordered_row[-1] = ">"
            inserts[child_r] = ordered_row[1:]  # Drop index value.
    # Sort the inserts as to keep track of the additive indexing.
    inserts_sorted = {k: inserts[k] for k in sorted(inserts.keys())}

    # Loop through the row inserts and add to table (array).
    table_values = df.values
    for i, k in enumerate(inserts_sorted.keys()):
        table_values = np.insert(table_values, (k + i), inserts_sorted[k], axis=0)

    # Make the ordered table array into a dataframe.
    # Note: df is dtype "object". Need to cast later on.
    ordered_df = pd.DataFrame(table_values, columns=df.columns)

    max_depth = np.max(ordered_df.node_depth.astype(int))
    tree_str = f"1) root {n_samples[0]} 9999 9999 ({impurities.sum()})\n"
    previous_depth = -1
    cnts = []
    # Loop through the nodes and calculate the node number and values per node.
    for row in ordered_df.itertuples():
        node_depth = int(row.node_depth)
        left = int(row.children_left)
        right = int(row.children_right)
        if left != right:
            if row.Index == 0:
                cnt = 2
            elif previous_depth > node_depth:
                depths = ordered_df.node_depth.values[: row.Index]
                idx = np.where(depths == node_depth)[0][-1]
                cnt = cnts[idx] + 1
            elif previous_depth < node_depth:
                cnt = cnts[row.Index - 1] * 2
            elif previous_depth == node_depth:
                cnt = cnts[row.Index - 1] + 1

            if node_depth == (max_depth - 1):
                value = out_type(ordered_df.iloc[row.Index + 1].value)
                samps = int(ordered_df.iloc[row.Index + 1].n_samples)
                criterion = float(ordered_df.iloc[row.Index + 1].criterion)
                tail = " *\n"
            else:
                if (
                    (bool(ordered_df.loc[ordered_df.node_id == left].iloc[0].is_leaf))
                    and (
                        bool(
                            int(row.Index)
                            < int(ordered_df.loc[ordered_df.node_id == left].index[0])
                        )
                    )
                    and (str(row.sign) == "<=")
                ):
                    rowx = ordered_df.loc[ordered_df.node_id == left].iloc[0]
                    tail = " *\n"
                    value = out_type(rowx.value)
                    samps = int(rowx.n_samples)
                    criterion = float(rowx.criterion)

                elif (
                    (bool(ordered_df.loc[ordered_df.node_id == right].iloc[0].is_leaf))
                    and (
                        bool(
                            int(row.Index)
                            < int(ordered_df.loc[ordered_df.node_id == right].index[0])
                        )
                    )
                    and (str(row.sign) == ">")
                ):
                    rowx = ordered_df.loc[ordered_df.node_id == right].iloc[0]
                    tail = " *\n"
                    value = out_type(rowx.value)
                    samps = int(rowx.n_samples)
                    criterion = float(rowx.criterion)

                else:
                    value = out_type(row.value)
                    samps = int(row.n_samples)
                    criterion = float(row.criterion)
                    tail = "\n"

            # Extract out the information needed in each line.
            spacing = (node_depth + 1) * "  "  # For pretty printing.
            fname = str(row.feature_name)  # Name of the feature (i.e., band name).
            tresh = float(row.threshold)  # Threshold.
            sign = str(row.sign)

            tree_str += f"{spacing}{cnt}) {fname} {sign} {tresh:.6f} {samps} {criterion:.4f} {value}{tail}"
            previous_depth = node_depth
        cnts.append(cnt)

    return tree_str


def rf_to_strings(estimator, feature_names, processes=2, output_mode="INFER"):
    """Convert a ensemble of decision trees into a list of strings.

    Wraps `tree_to_string`.

    Args:
        estimator (sklearn.ensemble.estimator): A decision tree classifier or regressor
            object created using sklearn.
        feature_names (list[str]): List of strings that define the name of features
            (i.e., bands) used to create the model.
        processes (int): Number of cpu processes to spawn. Increasing processes will
            improve speed for large models. default = 2
        output_mode (str): Output mode of the estimator. Options are "INFER",
            "CLASSIFIATION", or "REGRESSION" (capitalization does not matter). default =
            "INFER"

    Returns:
        trees (list[str]): list of strings where each string represents a decision tree
            estimator and collectively represent an ensemble decision tree estimator
            (i.e., RandomForest)
    """

    # Force output mode to be capital.
    output_mode = output_mode.upper()

    available_modes = ["INFER", "CLASSIFICATION", "REGRESSION", "PROBABILITY"]

    if output_mode not in available_modes:
        raise ValueError(
            "The provided output_mode is not available. "
            f"Please provide one from the following list: {available_modes}"
        )

    # Extract out the estimator trees.
    estimators = np.squeeze(estimator.estimators_)

    if output_mode == "INFER":
        if estimator.criterion in ["gini", "entropy"]:
            class_labels = estimator.classes_
        elif estimator.criterion in ["mse", "mae"]:
            class_labels = None
        else:
            raise RuntimeError(
                "Could not infer the output type from the estimator. "
                "Please explicitly provide the output_mode."
            )

    elif output_mode == "CLASSIFICATION":
        class_labels = estimator.classes_

    else:
        class_labels = None

    # Check that number of processors set to use is not more than available.
    if processes >= mp.cpu_count():
        # If so, force to use only cpu count - 1.
        processes = mp.cpu_count() - 1

    # Run the tree extraction process in parallel.
    with mp.Pool(processes) as pool:
        proc = pool.map_async(
            partial(
                tree_to_string,
                feature_names=feature_names,
                labels=class_labels,
                output_mode=output_mode,
            ),
            estimators,
        )
        trees = list(proc.get())

    return trees


def strings_to_classifier(trees: list[str]) -> ee.Classifier:
    """Returns an ee.Classifier from a string representation of decision trees."""

    # Convert strings to ee.String objects.
    ee_strings = [ee.String(tree) for tree in trees]

    # Pass list of ee.Strings to an ensemble decision tree classifier (i.e.,
    # RandomForest).
    classifier = ee.Classifier.decisionTreeEnsemble(ee_strings)

    return classifier


def fc_to_classifier(fc):
    """Returns an ee.Classifier from a feature collection.

    The feature collection must be from  from `export_trees_to_fc`.

    Args:
        fc (ee.FeatureCollection): feature collection that has trees property for each
            feature that represents the decision tree

    Returns:
        classifier (ee.Classifier): ee classifier object representing an ensemble decision tree
    """

    # Get a list of tree strings from feature collection.
    tree_strings = fc.aggregate_array("tree").map(
        lambda x: ee.String(x).replace(
            "#", "\n", "g"
        )  # Expects that # is ecoded to be a return.
    )
    # Pass list of ee.Strings to an ensemble decision tree classifier
    # (i.e., RandomForest).
    classifier = ee.Classifier.decisionTreeEnsemble(tree_strings)

    return classifier


def export_trees_to_fc(trees, asset_id, description="geemap_rf_export"):
    """Starts an export task to create a feature collection of a decision tree.

    Creates a feature collection with a property tree which contains the string
    representation of decision trees and exports to ee asset for later use.

    Args:
        trees (list[str]): List of string representation of the decision trees.
        asset_id (str): ee asset id path to export the feature collection to.

    kwargs:
        description (str): optional description to provide export information. default =
            "geemap_rf_export"
    """
    # Create a null geometry point.
    # This is needed to properly export the feature collection.
    null_island = ee.Geometry.Point([0, 0])

    # Create a list of feature over null island.
    # Set the tree property as the tree string.
    # Encode return values (\n) as #, use to parse later.
    features = [
        ee.Feature(null_island, {"tree": tree.replace("\n", "#")}) for tree in trees
    ]
    # Cast as feature collection.
    fc = ee.FeatureCollection(features)

    # Get export task and start.
    task = ee.batch.Export.table.toAsset(
        collection=fc, description=description, assetId=asset_id
    )
    task.start()


def trees_to_csv(trees: list[str], out_csv: str) -> None:
    """Save a list of strings (an ensemble of decision trees) to a CSV file.

    Args:
        trees: A list of strings (an ensemble of decision trees).
        out_csv: File path to the output csv.
    """
    out_csv = os.path.abspath(out_csv)
    with open(out_csv, "w") as f:
        f.writelines([tree.replace("\n", "#") + "\n" for tree in trees])


def csv_to_classifier(in_csv: str) -> ee.Classifier | None:
    """Returns an ee.Classifier from a CSV file.

    The file must contain a list of strings (an ensemble of decision trees).

    Args:
        in_csv: File path to the input CSV.

    Returns:
        object: ee.Classifier.
    """
    in_csv = os.path.join(in_csv)

    try:
        with open(in_csv) as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"{in_csv} could not be found.")
        return None

    null_island = ee.Geometry.Point([0, 0])
    features = [ee.Feature(null_island, {"tree": line.strip()}) for line in lines]
    rf_fc = ee.FeatureCollection(features)
    classifier = fc_to_classifier(rf_fc)

    return classifier
