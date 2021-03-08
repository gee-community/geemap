import os
import pkg_resources
import shutil
import ipywidgets as widgets
import pandas as pd
from pathlib import Path
from box import Box
from .common import download_from_url, search_ee_data, ee_data_html
from IPython.display import display


def get_data_csv():
    """Gets the file path to the CSV file containing the information about the Earth Engien Data Catalog.

    Returns:
        str: File path to the CSV file.
    """
    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
    template_dir = os.path.join(pkg_dir, "data/template")
    data_csv = os.path.join(template_dir, "ee_data_catalog.csv")
    return data_csv


def update_data_list(out_dir="."):
    """Updates the Earth Engine Data Catalog dataset list.

    Args:
        out_dir (str, optional): The output directory to save the GitHub repositor. Defaults to ".".

    Raises:
        Exception: If the CSV file fails to save.
    """
    try:

        url = (
            "https://github.com/samapriya/Earth-Engine-Datasets-List/archive/master.zip"
        )
        filename = "Earth-Engine-Datasets-List-master.zip"
        dir_name = filename.replace(".zip", "")

        out_dir = os.path.abspath(out_dir)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        download_from_url(
            url, out_file_name=filename, out_dir=out_dir, unzip=True, verbose=False
        )

        work_dir = os.path.join(out_dir, dir_name)
        in_csv = list(Path(work_dir).rglob("*.csv"))[0]

        out_csv = get_data_csv()

        shutil.copyfile(in_csv, out_csv)
        os.remove(os.path.join(out_dir, filename))
        shutil.rmtree(os.path.join(out_dir, dir_name))

    except Exception as e:
        raise Exception(e)


def get_data_list(update=False):
    """Gets the list of the Earth Engine datasets.

    Args:
        update (bool, optional): Whether to download the latest version from GitHub. Defaults to False.

    Returns:
        list: The list of datasets.
    """
    data_csv = get_data_csv()

    if update or (not os.path.exists(data_csv)):
        update_data_list()

    df = pd.read_csv(data_csv)

    datasets = list(df["id"])

    extra_ids = [
        "countries",
        "us_states",
        "us_cities",
        "chn_admin_line",
        "chn_admin_level0",
        "chn_admin_level1",
        "chn_admin_level2",
    ]

    extra_datasets = ["users/giswqs/public/" + uid for uid in extra_ids]

    return datasets + extra_datasets


def merge_dict(dict1, dict2):
    """Merges two nested dictionaries.

    Args:
        dict1 (dict): The first dictionary to merge.
        dict2 (dict): The second dictionary to merge.

    Returns:
        dict: The merged dictionary.
    """
    for key, val in dict1.items():
        if type(val) == dict:
            if key in dict2 and type(dict2[key] == dict):
                merge_dict(dict1[key], dict2[key])
        else:
            if key in dict2:
                dict1[key] = dict2[key]

    for key, val in dict2.items():
        if not key in dict1:
            dict1[key] = val

    return dict1


def get_data_dict(update=False):
    """Gets the Earth Engine Data Catalog as a nested dictionary.

    Args:
        update (bool, optional): Whether to download the latest version from GitHub. Defaults to False.

    Returns:
        dict: The nested dictionary containing the information about the Earth Engine Data Catalog.
    """
    data_dict = {}
    datasets = get_data_list(update=update)

    for dataset in datasets:
        tree_dict = {}
        items = dataset.split("/")
        for index, key in enumerate(reversed(items)):
            if index == 0:
                tree_dict = {key: dataset}
            else:
                tree_dict = {key: tree_dict}

        data_dict = merge_dict(data_dict, tree_dict)
        data_dict[dataset.replace("/", "_")] = dataset

    return data_dict


def get_metadata(asset_id):
    """Gets metadata about an Earth Engine asset.

    Args:
        asset_id (str): The Earth Engine asset id.

    Raises:
        Exception: If search fails.
    """
    try:
        ee_assets = search_ee_data(asset_id)
        html = ee_data_html(ee_assets[0])
        html_widget = widgets.HTML()
        html_widget.value = html
        display(html_widget)

    except Exception as e:
        raise Exception(e)


DATA = Box(get_data_dict(), frozen_box=True)