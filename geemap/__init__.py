"""Top-level package for geemap."""

__author__ = """Qiusheng Wu"""
__email__ = "giswqs@gmail.com"
__version__ = "0.37.1.post0"

import os
import sys

from .report import Report


def in_colab_shell() -> bool:
    """Tests if the code is being executed within Google Colab."""
    return "google.colab" in sys.modules


def use_folium() -> bool:
    """Whether to use the folium or ipyleaflet plotting backend."""
    return os.environ.get("USE_FOLIUM") is not None


def _use_eerepr(token: str = "USE_EEREPR") -> bool:
    """Returns whether to use eerepr for printing Earth Engine objects."""
    return os.environ.get(token) is None


if use_folium():
    from .foliumap import *
else:
    try:
        from .geemap import *
    except Exception as e:
        if in_colab_shell():
            print(
                "Please restart Colab runtime after installation if you encounter any "
                "errors when importing geemap."
            )
        else:
            print(
                "Please restart Jupyter kernel after installation if you encounter any "
                "errors when importing geemap."
            )
        raise e

if _use_eerepr():
    import eerepr

    eerepr.initialize()
