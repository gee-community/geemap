import os
import ee
import numpy as np
import pandas as pd
import multiprocessing as mp
from functools import partial


def tree_to_string(estimator, feature_names):
    """Function to convert a sklearn decision tree object to a string format that EE can interpret

    args:
        estimator (sklearn.tree.estimator): An estimator consisting of multiple decision tree classifiers. Expects object to contain estimators_ attribute
        feature_names (list[str]): List of strings that define the name of features (i.e. bands) used to create the model

    returns:
        tree_str (str): string representation of decision tree estimator

    raises:
        RuntimeError: raises run time error when function cannot determine if the estimator is for regression or classification problem
    """

    # extract out the information need to build the tree string
    n_nodes = estimator.tree_.node_count
    children_left = estimator.tree_.children_left
    children_right = estimator.tree_.children_right
    feature_idx = estimator.tree_.feature
    impurities = estimator.tree_.impurity
    n_samples = estimator.tree_.n_node_samples
    thresholds = estimator.tree_.threshold
    features = [feature_names[i] for i in feature_idx]

    raw_vals = estimator.tree_.value
    if raw_vals.ndim == 3:
        # take argmax along class axis from values
        values = np.squeeze(raw_vals.argmax(axis=-1))
    elif raw_vals.ndim == 2:
        # take values and drop un needed axis
        values = np.squeeze(raw_vals)
    else:
        raise RuntimeError(
            "could not understand estimator type and parse out the values"
        )

    # use iterative pre-order search to extract node depth and leaf information
    node_ids = np.zeros(shape=n_nodes, dtype=np.int64)
    node_depth = np.zeros(shape=n_nodes, dtype=np.int64)
    is_leaves = np.zeros(shape=n_nodes, dtype=bool)
    stack = [(0, -1)]  # seed is the root node id and its parent depth
    while len(stack) > 0:
        node_id, parent_depth = stack.pop()
        node_depth[node_id] = parent_depth + 1
        node_ids[node_id] = node_id

        # If we have a test node
        if children_left[node_id] != children_right[node_id]:
            stack.append((children_left[node_id], parent_depth + 1))
            stack.append((children_right[node_id], parent_depth + 1))
        else:
            is_leaves[node_id] = True

    # create a table of the initial structure
    # each row is a node or leaf
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
        }
    )

    # the table representation does not have lef vs right node structure
    # so we need to add in right nodes in the correct location
    # we do this by first calculating which nodes are right and then insert them at the correct index

    # get a dict of right node rows and assign key based on index where to insert
    inserts = {}
    for row in df.itertuples():
        child_r = row.children_right
        if child_r > row.Index:
            ordered_row = np.array(row)
            ordered_row[-1] = ">"
            inserts[child_r] = ordered_row[1:]  # drop index value
    # sort the inserts as to keep track of the additive indexing
    inserts_sorted = {k: inserts[k] for k in sorted(inserts.keys())}

    # loop through the row inserts and add to table (array)
    table_values = df.values
    for i, k in enumerate(inserts_sorted.keys()):
        table_values = np.insert(table_values, (k + i), inserts_sorted[k], axis=0)

    # make the ordered table array into a dataframe
    # note: df is dtype "object", need to cast later on
    ordered_df = pd.DataFrame(table_values, columns=df.columns)

    max_depth = np.max(ordered_df.node_depth.astype(int))
    tree_str = f"1) root {n_samples[0]} 9999 9999 ({impurities.sum()})\n"
    previous_depth = -1
    cnts = []
    # loop through the nodes and calculate the node number and values per node
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
                # cnt = (cnts[row.Index-1] // 2) + 1
                cnt = cnts[idx] + 1
            elif previous_depth < node_depth:
                cnt = cnts[row.Index - 1] * 2
            elif previous_depth == node_depth:
                cnt = cnts[row.Index - 1] + 1

            if node_depth == (max_depth - 1):
                value = float(ordered_df.iloc[row.Index + 1].value)
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
                    value = float(rowx.value)
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
                    value = float(rowx.value)
                    samps = int(rowx.n_samples)
                    criterion = float(rowx.criterion)

                else:
                    value = float(row.value)
                    samps = int(row.n_samples)
                    criterion = float(row.criterion)
                    tail = "\n"

            # extract out the information needed in each line
            spacing = (node_depth + 1) * "  "  # for pretty printing
            fname = str(row.feature_name)  # name of the feature (i.e. band name)
            tresh = float(row.threshold)  # threshold
            sign = str(row.sign)

            tree_str += f"{spacing}{cnt}) {fname} {sign} {tresh:.6f} {samps} {criterion:.4f} {value:.6f}{tail}"
            previous_depth = node_depth
        cnts.append(cnt)

    return tree_str


def rf_to_strings(estimator, feature_names, processes=2):
    """Function to convert a ensemble of decision trees into a list of strings. Wraps `tree_to_string`

    args:
        estimator (sklearn.ensemble.estimator): A decision tree classifier or regressor object created using sklearn
        feature_names (list[str]): List of strings that define the name of features (i.e. bands) used to create the model

    kwargs:
        processess (int): number of cpu processes to spawn. Increasing processes will improve speed for large models. default = 2

    returns:
        trees (list[str]): list of strings where each string represents a decision tree estimator and collectively represent an ensemble decision tree estimator (i.e. RandomForest)

    """

    # extract out the estimator trees
    estimators = estimator.estimators_

    # check that number of processors set to use is not more than available
    if processes >= mp.cpu_count():
        # if so, force to use only cpu count - 1
        processes = mp.cpu_count() - 1

    # run the tree extraction process in parallel
    with mp.Pool(processes) as pool:
        proc = pool.map_async(
            partial(tree_to_string, feature_names=feature_names), estimators
        )
        trees = list(proc.get())

    return trees


def strings_to_classifier(trees):
    """Function that takes string representation of decision trees and creates a ee.Classifier that can be used with ee objects

    args:
        trees (list[str]): list of string representation of the decision trees

    returns:
        classifier (ee.Classifier): ee classifier object representing an ensemble decision tree

    """

    # convert strings to ee.String objects
    ee_strings = [ee.String(tree) for tree in trees]

    # pass list of ee.Strings to an ensemble decision tree classifier (i.e. RandomForest)
    classifier = ee.Classifier.decisionTreeEnsemble(ee_strings)

    return classifier


def fc_to_classifier(fc):
    """Function that takes a feature collection resulting from `export_trees_to_fc` and creates a ee.Classifier that can be used with ee objects

    args:
        fc (ee.FeatureCollection): feature collection that has trees property for each feature that represents the decision tree

    returns:
        classifier (ee.Classifier): ee classifier object representing an ensemble decision tree

    """

    # get a list of tree strings from feature collection
    tree_strings = fc.aggregate_array("tree").map(
        lambda x: ee.String(x).replace(
            "#", "\n", "g"
        )  # expects that # is ecoded to be a return
    )
    # pass list of ee.Strings to an ensemble decision tree classifier (i.e. RandomForest)
    classifier = ee.Classifier.decisionTreeEnsemble(tree_strings)

    return classifier


def export_trees_to_fc(trees, asset_id, description="geemap_rf_export"):
    """Function that creates a feature collection with a property tree which contains the string representation of decision trees and exports to ee asset for later use

    args:
        trees (list[str]): list of string representation of the decision trees
        asset_id (str): ee asset id path to export the feature collection to

    kwargs:
        description (str): optional description to provide export information. default = "geemap_rf_export"

    """
    # create a null geometry point. This is needed to properly export the feature collection
    null_island = ee.Geometry.Point([0, 0])

    # create a list of feature over null island
    # set the tree property as the tree string
    # encode return values (\n) as #, use to parse later
    features = [
        ee.Feature(null_island, {"tree": tree.replace("\n", "#")}) for tree in trees
    ]
    # cast as feature collection
    fc = ee.FeatureCollection(features)

    # get export task and start
    task = ee.batch.Export.table.toAsset(
        collection=fc, description=description, assetId=asset_id
    )
    task.start()


def trees_to_csv(trees, out_csv):
    """Save a list of strings (an ensemble of decision trees) to a CSV file.

    Args:
        trees (list): A list of strings (an ensemble of decision trees).
        out_csv (str): File path to the output csv
    """
    out_csv = os.path.abspath(out_csv)
    with open(out_csv, "w") as f:
        f.writelines([tree.replace("\n", "#") + "\n" for tree in trees])


def csv_to_classifier(in_csv):
    """Convert a CSV file containing a list of strings (an ensemble of decision trees) to an ee.Classifier.

    Args:
        in_csv (str): File path to the input CSV.
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
