"""Top-level package for geemap."""

__author__ = """Qiusheng Wu"""
__email__ = "giswqs@gmail.com"
__version__ = "0.8.8"


def in_colab_shell():
    """Tests if the code is being executed within Google Colab."""
    try:
        import google.colab

        return True
    except ImportError:
        return False


if in_colab_shell():
    from .eefolium import *
else:
    from .geemap import *
