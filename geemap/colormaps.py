"""Module for commonly used colormaps and palettes for visualizing Earth Engine data.
"""
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from box import Box
from typing import Any, Optional, Union


_palette_dict = {
    "ndvi": [
        "FFFFFF",
        "CE7E45",
        "DF923D",
        "F1B555",
        "FCD163",
        "99B718",
        "74A901",
        "66A000",
        "529400",
        "3E8601",
        "207401",
        "056201",
        "004C00",
        "023B01",
        "012E01",
        "011D01",
        "011301",
    ],
    "ndwi": [
        "#ece7f2",
        "#d0d1e6",
        "#a6bddb",
        "#74a9cf",
        "#3690c0",
        "#0570b0",
        "#045a8d",
        "#023858",
    ],
    "dem": ["006633", "E5FFCC", "662A00", "D8D8D8", "F5F5F5"],
    "dw": [
        "#419BDF",
        "#397D49",
        "#88B053",
        "#7A87C6",
        "#E49635",
        "#DFC35A",
        "#C4281B",
        "#A59B8F",
        "#B39FE1",
    ],
    "esri_lulc": [
        "#1A5BAB",
        "#358221",
        "#000000",
        "#87D19E",
        "#FFDB5C",
        "#000000",
        "#ED022A",
        "#EDE9E4",
        "#F2FAFF",
        "#C8C8C8",
        "#C6AD8D",
    ],
}


def get_palette(
    cmap_name: str = None, n_class: str = None, hashtag: bool = False
) -> list[str]:
    """Get a palette from a matplotlib colormap. See the list of colormaps at https://matplotlib.org/stable/tutorials/colors/colormaps.html.

    Args:
        cmap_name (str, optional): The name of the matplotlib colormap. Defaults to None.
        n_class (int, optional): The number of colors. Defaults to None.
        hashtag (bool, optional): Whether to return a list of hex colors. Defaults to False.

    Returns:
        list: A list of hex colors.
    """

    if cmap_name in ["ndvi", "ndwi", "dem", "dw", "esri_lulc"]:
        colors = _palette_dict[cmap_name]
    else:
        cmap = plt.cm.get_cmap(cmap_name, n_class)
        colors = [mpl.colors.rgb2hex(cmap(i))[1:] for i in range(cmap.N)]
    if hashtag:
        colors = ["#" + i for i in colors]

    return colors


def get_colorbar(
    colors: list[str],
    vmin: float = 0,
    vmax: float = 1,
    width: float = 6.0,
    height: float = 0.4,
    orientation: str = "horizontal",
    discrete: Optional[bool] = False,
    return_fig: Optional[bool] = False,
) -> Union[plt.Figure, None]:
    """Creates a colorbar based on custom colors.

    Args:
        colors (list): A list of hex colors.
        vmin (float, optional): The minimum value range. Defaults to 0.
        vmax (float, optional): The maximum value range. Defaults to 1.0.
        width (float, optional): The width of the colormap. Defaults to 6.0.
        height (float, optional): The height of the colormap. Defaults to 0.4.
        orientation (str, optional): The orientation of the colormap. Defaults to "horizontal".
        discrete (bool, optional): Whether to create a discrete colormap.
        return_fig (bool, optional): Whether to return the figure. Defaults to False.
    """
    hexcodes = [i if i[0] == "#" else "#" + i for i in colors]
    fig, ax = plt.subplots(figsize=(width, height))
    if discrete:
        cmap = mpl.colors.ListedColormap(hexcodes)
        vals = np.linspace(vmin, vmax, cmap.N + 1)
        norm = mpl.colors.BoundaryNorm(vals, cmap.N)
    else:
        cmap = mpl.colors.LinearSegmentedColormap.from_list("custom", hexcodes, N=256)
        norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
    mpl.colorbar.ColorbarBase(ax, norm=norm, cmap=cmap, orientation=orientation)
    if return_fig:
        return fig
    else:
        plt.show()


def list_colormaps(
    add_extra: Optional[bool] = False, lowercase: Optional[bool] = False
) -> list[str]:
    """List all available colormaps. See a complete lost of colormaps at https://matplotlib.org/stable/tutorials/colors/colormaps.html.
    Args:
        add_extra (bool, optional): Whether to add the extra colormaps "dem", "ndvi", and "ndwi" to the list. Defaults to False.
        lowercase (bool, optional): Whether to convert all the colormap names to lowercase. Defaults to False.

    Returns:
        list: The list of colormap names.
    """
    result = plt.colormaps()
    if add_extra:
        result += ["dem", "ndvi", "ndwi"]
    if lowercase:
        result = [i.lower() for i in result]
    result.sort()
    return result


def plot_colormap(
    cmap: str,
    width: float = 8.0,
    height: float = 0.4,
    orientation: str = "horizontal",
    vmin: float = 0,
    vmax: float = 1.0,
    axis_off: Optional[bool] = True,
    show_name: Optional[bool] = False,
    font_size: Optional[int] = 12,
    return_fig: Optional[bool] = False,
) -> Union[plt.Figure, None]:
    """Plot a matplotlib colormap.

    Args:
        cmap (str): The name of the colormap.
        width (float, optional): The width of the colormap. Defaults to 8.0.
        height (float, optional): The height of the colormap. Defaults to 0.4.
        orientation (str, optional): The orientation of the colormap. Defaults to "horizontal".
        vmin (float, optional): The minimum value range. Defaults to 0.
        vmax (float, optional): The maximum value range. Defaults to 1.0.
        axis_off (bool, optional): Whether to turn axis off. Defaults to True.
        show_name (bool, optional): Whether to show the colormap name. Defaults to False.
        font_size (int, optional): Font size of the text. Defaults to 12.
        return_fig (bool, optional): Whether to return the figure. Defaults to False.
    """
    fig, ax = plt.subplots(figsize=(width, height))
    col_map = plt.get_cmap(cmap)

    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

    mpl.colorbar.ColorbarBase(ax, norm=norm, cmap=col_map, orientation=orientation)
    if axis_off:
        ax.set_axis_off()

    if show_name:
        pos = list(ax.get_position().bounds)
        x_text = pos[0] - 0.01
        y_text = pos[1] + pos[3] / 2.0
        fig.text(x_text, y_text, cmap, va="center", ha="right", fontsize=font_size)

    if return_fig:
        return fig
    else:
        plt.show()


def plot_colormaps(width: float = 8.0, height: float = 0.4) -> None:
    """Plot all available colormaps.

    Args:
        width (float, optional): Width of the colormap. Defaults to 8.0.
        height (float, optional): Height of the colormap. Defaults to 0.4.
    """
    cmap_list = list_colormaps()
    nrows = len(cmap_list)
    fig, axes = plt.subplots(nrows=nrows, figsize=(width, height * nrows))
    fig.subplots_adjust(top=0.95, bottom=0.01, left=0.2, right=0.99)

    gradient = np.linspace(0, 1, 256)
    gradient = np.vstack((gradient, gradient))

    for ax, name in zip(axes, cmap_list):
        ax.imshow(gradient, aspect="auto", cmap=plt.get_cmap(name))
        ax.set_axis_off()
        pos = list(ax.get_position().bounds)
        x_text = pos[0] - 0.01
        y_text = pos[1] + pos[3] / 2.0
        fig.text(x_text, y_text, name, va="center", ha="right", fontsize=12)

    # Turn off *all* ticks & spines, not just the ones with colormaps.
    for ax in axes:
        ax.set_axis_off()

    plt.show()


for index, cmap_name in enumerate(list_colormaps()):
    if index < len(list_colormaps()):
        color_dict = {}
        color_dict["default"] = get_palette(cmap_name)
        for i in range(3, 13):
            name = "n" + str(i).zfill(2)
            colors = get_palette(cmap_name, i)
            color_dict[name] = colors
        _palette_dict[cmap_name] = color_dict


palettes = Box(_palette_dict, frozen_box=True)
