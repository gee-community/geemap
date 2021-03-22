"""Top-level package for geemap."""

__author__ = """Qiusheng Wu"""
__email__ = "giswqs@gmail.com"
__version__ = "0.8.13"

import os


def in_colab_shell():
    """Tests if the code is being executed within Google Colab."""
    import sys

    if "google.colab" in sys.modules:
        return True
    else:
        return False


def is_github_action():
    """Tests if the code is being executed with GitHub Actions."""
    if os.environ.get("RUN_GITHUB_ACTION") is not None:
        return True
    else:
        return False


if in_colab_shell() or is_github_action():
    from .eefolium import *
else:
    from .geemap import *
