"""Top-level package for geemap."""

__author__ = """Qiusheng Wu"""
__email__ = "giswqs@gmail.com"
__version__ = "0.17.1"

import os


def in_colab_shell():
    """Tests if the code is being executed within Google Colab."""
    import sys

    if "google.colab" in sys.modules:
        return True
    else:
        return False


def use_folium():
    """Whether to use the folium or ipyleaflet plotting backend."""
    if os.environ.get("USE_FOLIUM") is not None:
        return True
    else:
        return False


if use_folium():
    from .foliumap import *
else:
    try:
        from .geemap import *
    except NotImplementedError as e:
        if in_colab_shell():
            print(
                "Please restart runtime after installing geemap if you encounter errors."
            )
        raise NotImplementedError(e)
    except Exception as e:
        print("Please restart kernel after installing geemap.")
        raise Exception(e)

from .report import Report
