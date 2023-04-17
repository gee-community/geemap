import box
import os
import pkg_resources

_pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
_datasets_path = os.path.join(_pkg_dir, "examples/datasets.txt")
_baseurl = (
    "https://raw.githubusercontent.com/gee-community/geemap/master/examples/data/"
)

with open(_datasets_path) as f:
    _names = [line.strip() for line in f.readlines()]

_links = [f"{_baseurl}{_name}" for _name in _names]
datasets = box.Box(dict(zip(_names, _links)), frozen_box=True)


def get_path(name):
    """Get the HTTP URL to an example dataset.

    Args:
        name (str): The name of the dataset.

    Raises:
        ValueError: If the dataset name is not found.

    Returns:
        str: The HTTP URL to the dataset.
    """
    if name in datasets:
        return datasets[name]
    else:
        raise ValueError(
            f"{name} not found in example datasets. It must be one of {list(datasets.keys())}"
        )


def get_ee_path(name):
    """Get the Earth Engine asset ID of an example dataset.

    Args:
        name (str): The name of the dataset, such as contents, countries, us_cities, us_states,
            china, CONUS_HU8, chn_admin_level0, chn_admin_level1, chn_admin_level2, chn_admin_line

    Returns:
        str: The Earth Engine asset ID of the dataset.
    """
    return f"{'users/giswqs/public/'}{name}"


def get_names():
    """Get a list of names of the example datasets.

    Returns:
        list: A list of names of the example datasets.
    """

    return list(datasets.keys())


def get_links():
    """Get a list of HTTP URLs to the example datasets.

    Returns:
        list: A list of HTTP URLs to the example datasets.
    """

    return list(datasets.values())
