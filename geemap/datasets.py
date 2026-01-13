"""Module for accessing the Earth Engine Data Catalog with dot notation."""

# *******************************************************************************#
# This module contains extra features of the geemap package.                     #
# The geemap community will maintain the extra features.                         #
# *******************************************************************************#

import importlib
import json
import os
import pathlib
import shutil
from typing import Any
import urllib.request

import box
import ipywidgets as widgets
from IPython.display import display

from . import common


def get_data_csv() -> str:
    """Returns the path to the CSV file summarizing the Earth Engine Data Catalog."""
    pkg_dir = str(
        # pytype: disable=attribute-error
        importlib.resources.files("geemap")
        .joinpath("geemap.py")
        .parent
        # pytype: enable=attribute-error
    )
    template_dir = os.path.join(pkg_dir, "data/template")
    data_csv = os.path.join(template_dir, "ee_data_catalog.csv")
    return data_csv


def update_data_list(out_dir: str = ".") -> None:
    """Updates the Earth Engine Data Catalog dataset list.

    Args:
        out_dir: The output directory to save the GitHub repository. Defaults to ".".

    Raises:
        Exception: If the CSV file fails to save.
    """
    url = "https://github.com/samapriya/Earth-Engine-Datasets-List/archive/master.zip"
    filename = "Earth-Engine-Datasets-List-master.zip"
    dir_name = filename.replace(".zip", "")

    out_dir = os.path.abspath(out_dir)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    common.download_from_url(
        url, out_file_name=filename, out_dir=out_dir, unzip=True, verbose=False
    )

    work_dir = os.path.join(out_dir, dir_name)
    in_csv = list(pathlib.Path(work_dir).rglob("*.csv"))[0]

    out_csv = get_data_csv()

    shutil.copyfile(in_csv, out_csv)
    os.remove(os.path.join(out_dir, filename))
    shutil.rmtree(os.path.join(out_dir, dir_name))


def get_data_list() -> list[str]:
    """Returns a list of Earth Engine dataset IDs."""
    datasets = get_ee_stac_list()
    extra_datasets = get_geemap_data_list()
    community_datasets = get_community_data_list()

    return datasets + extra_datasets + community_datasets


def get_geemap_data_list() -> list[str]:
    """Returns the list of the public datasets from GEE users."""
    extra_ids = [
        "countries",
        "us_states",
        "us_cities",
        "chn_admin_line",
        "chn_admin_level0",
        "chn_admin_level1",
        "chn_admin_level2",
    ]

    extra_datasets = [f"users/giswqs/public/{uid}" for uid in extra_ids]
    return extra_datasets


def get_community_data_list() -> list[str]:
    """Returns the list of community dataset IDs.

    From https://github.com/samapriya/awesome-gee-community-datasets/blob/master/community_datasets.json
    """
    collections = common.search_ee_data(".*", regex=True, source="community")
    return [collection.get("id", None) for collection in collections]


def get_ee_stac_list() -> list[str]:
    """Returns the STAC list of the Earth Engine Data Catalog.

    Raises:
        Exception: If the JSON file fails to download.
    """
    stac_url = "https://raw.githubusercontent.com/samapriya/Earth-Engine-Datasets-List/master/gee_catalog.json"

    datasets = []
    with urllib.request.urlopen(stac_url) as url:
        data = json.loads(url.read().decode())
        datasets = [item["id"] for item in data]

    return datasets


def merge_dict(dict1: dict[Any, Any], dict2: dict[Any, Any]) -> dict[Any, Any]:
    """Returns the merge of two nested dictionaries.

    Args:
        dict1: The first dictionary to merge.
        dict2: The second dictionary to merge.
    """
    return {**dict1, **dict2}


def get_data_dict() -> dict[str, Any]:
    """Returns the Earth Engine Data Catalog as a nested dictionary."""
    data_dict = {}
    datasets = get_data_list()

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


def get_metadata(asset_id: str, source: str = "ee") -> None:
    """Displays metadata about an Earth Engine asset.

    Args:
        asset_id: The Earth Engine asset id.
        source: 'ee', 'community' or 'all'.

    Raises:
        Exception: If search fails.
    """
    ee_assets = common.search_ee_data(asset_id, source=source)
    html = common.ee_data_html(ee_assets[0])
    html_widget = widgets.HTML()
    html_widget.value = html
    display(html_widget)


DATA = box.Box(get_data_dict(), frozen_box=True)
