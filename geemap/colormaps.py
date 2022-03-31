"""Module for commonly used colormaps and palettes for visualizing Earth Engine data.
"""
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from box import Box
      
_palette_dict = {
    "ndvi": [
        "#FFFFFF",
        "#CE7E45",
        "#DF923D",
        "#F1B555",
        "#FCD163",
        "#99B718",
        "#74A901",
        "#66A000",
        "#529400",
        "#3E8601",
        "#207401",
        "#056201",
        "#004C00",
        "#023B01",
        "#012E01",
        "#011D01",
        "#011301",
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
    "dem": ["#006633", "#E5FFCC", "#662A00", "#D8D8D8", "#F5F5F5"],
}

_cpt_city_dict ={
    "DEM_poster" : "http://soliton.vm.bytemark.co.uk/pub/cpt-city/td/DEM_poster.cpt",
    "DEM_print"  : "http://soliton.vm.bytemark.co.uk/pub/cpt-city/td/DEM_print.cpt",
    "DEM_screen" : "http://soliton.vm.bytemark.co.uk/pub/cpt-city/td/DEM_screen.cpt",
    "elevation"  : "http://soliton.vm.bytemark.co.uk/pub/cpt-city/grass/elevation.cpt",
    "costa-rica" : "http://soliton.vm.bytemark.co.uk/pub/cpt-city/esri/hypsometry/ca/costa-rica.cpt",
    "mexico"     : "http://soliton.vm.bytemark.co.uk/pub/cpt-city/esri/hypsometry/ca/mexico.cpt",
    "sd-a"       : "http://soliton.vm.bytemark.co.uk/pub/cpt-city/jm/sd/sd-a.cpt",
    "sd-b"       : "http://soliton.vm.bytemark.co.uk/pub/cpt-city/jm/sd/sd-b.cpt",
    "sd-c"       : "http://soliton.vm.bytemark.co.uk/pub/cpt-city/jm/sd/sd-c.cpt",
    "usgs"       : "http://soliton.vm.bytemark.co.uk/pub/cpt-city/usgs/usgs.cpt",
    "europe_8"   : "http://soliton.vm.bytemark.co.uk/pub/cpt-city/esri/hypsometry/eu/europe_8.cpt",
    "europe_9"   : "http://soliton.vm.bytemark.co.uk/pub/cpt-city/esri/hypsometry/eu/europe_9.cpt",
}

def get_palette(cmap_name=None, n_class=None, hashtag=False):
    """Get a palette from a matplotlib colormap. See the list of colormaps at https://matplotlib.org/stable/tutorials/colors/colormaps.html.

    Args:
        cmap_name (str, optional): The name of the matplotlib colormap. Defaults to None.
        n_class (int, optional): The number of colors. Defaults to None.
        hashtag (bool, optional): Whether to return a list of hex colors. Defaults to False.

    Returns:
        list: A list of hex colors.
    """

    if cmap_name in ["dem", "ndvi", "ndwi"]:
        colors = _palette_dict[cmap_name]
    elif cmap_name in _cpt_city_dict.keys():
        cmap = cmap_from_cptcity_url(_cpt_city_dict[cmap_name])    
        colors = [mpl.colors.rgb2hex(cmap(i)) for i in range(cmap.N)]
    else:
        cmap = plt.cm.get_cmap(cmap_name, n_class)
        colors = [mpl.colors.rgb2hex(cmap(i))[1:] for i in range(cmap.N)]
    if hashtag:
        colors = ["#" + i for i in colors]
    return colors


def get_colorbar(
    colors,
    vmin=0,
    vmax=1,
    width=6.0,
    height=0.4,
    orientation="horizontal",
    discrete=False,
    return_fig=False,
):
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


def list_colormaps(add_extra=False, lowercase=False, add_cpt_city=False):
    """List all available colormaps. See a complete lost of colormaps at https://matplotlib.org/stable/tutorials/colors/colormaps.html.
    Args:
        add_extra(bool, optional)   : Plot extral palettes of NDVI, NDWI, and DEM. Defaults to False
        add_cpt_city(bool, optional): Plot palettes from cpt-city. See details at http://soliton.vm.bytemark.co.uk/pub/cpt-city/views/totp-svg.html. Defaults to False
    Returns:
        list: The list of colormap names.
    """
    result = plt.colormaps()
    if add_extra:
        result += ["dem", "ndvi", "ndwi"]
    if lowercase:
        result = [i.lower() for i in result]
    if add_cpt_city:
        result += _cpt_city_dict.keys()
    result.sort()
    return result


def plot_colormap(
    cmap,
    width=8.0,
    height=0.4,
    orientation="horizontal",
    vmin=0,
    vmax=1.0,
    axis_off=True,
    show_name=False,
    font_size=12,
    return_fig=False,
):
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
    if cmap in _cpt_city_dict.keys():
        col_map = cmap_from_cptcity_url(_cpt_city_dict[cmap])
    else:
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


def plot_colormaps(width=8.0, height=0.4, add_cpt_city=False):
    """Plot all available colormaps.

    Args:
        width (float, optional)     : Width of the colormap. Defaults to 8.0.
        height (float, optional)    : Height of the colormap. Defaults to 0.4.
        add_cpt_city(bool, optional): Plot palettes from cpt-city. See details at http://soliton.vm.bytemark.co.uk/pub/cpt-city/views/totp-svg.html. Defaults to False
    """
    cmap_list = list_colormaps(add_extra=add_extra, add_cpt_city=add_cpt_city)
    nrows = len(cmap_list)
    fig, axes = plt.subplots(nrows=nrows, figsize=(width, height * nrows))
    fig.subplots_adjust(top=0.95, bottom=0.01, left=0.2, right=0.99)
    
    gradient = np.linspace(0, 1, 256)
    gradient = np.vstack((gradient, gradient))

    for ax, name in zip(axes, cmap_list):
        if name in _cpt_city_dict.keys():
            cmap = cmap_from_cptcity_url(_cpt_city_dict[name])
        else:
            cmap = plt.get_cmap(name)
        ax.imshow(gradient, aspect="auto", cmap=cmap)
        ax.set_axis_off()
        pos = list(ax.get_position().bounds)
        x_text = pos[0] - 0.01
        y_text = pos[1] + pos[3] / 2.0
        fig.text(x_text, y_text, name, va="center", ha="right", fontsize=12)

    # Turn off *all* ticks & spines, not just the ones with colormaps.
    for ax in axes:
        ax.set_axis_off()

    plt.show()

def gmtColormap_openfile(cptf, name=None):
    """Read a GMT color map from an OPEN cpt file
    Parameters
    ----------
    cptf : open file or url handle
        path to .cpt file
    name : str, optional
        name for color map
        if not provided, the file name will be used
    """
    import colorsys  
    
    # generate cmap name
    if name is None:
        name = '_'.join(os.path.basename(cptf.name).split('.')[:-1])

    # process file
    x = []
    r = []
    g = []
    b = []
    lastls = None
    for l in cptf.readlines():
        ls = l.split()

        # skip empty lines
        if not ls:
            continue

        # parse header info
        if ls[0] in ["#COLOR_MODEL",b"#COLOR_MODEL","#", b"#"]:
            if ls[-1] in ["HSV", b"HSV"]:
                colorModel = "HSV"
            else:
                colorModel = "RGB"
            continue
        
        # skip comment or BFN info
        if ls[0] in ["#", b"#","B", b"B", "F", b"F", "N", b"N"]:              
            continue    
        
        # parse color vectors
        x.append(float(ls[0]))
        r.append(float(ls[1]))
        g.append(float(ls[2]))
        b.append(float(ls[3]))

        # save last row
        lastls = ls

    x.append(float(lastls[4]))
    r.append(float(lastls[5]))
    g.append(float(lastls[6]))
    b.append(float(lastls[7]))
    
    x = np.array(x)
    r = np.array(r)
    g = np.array(g)
    b = np.array(b)

    if colorModel == "HSV":
        for i in range(r.shape[0]):
            # convert HSV to RGB
            rr,gg,bb = colorsys.hsv_to_rgb(r[i]/360., g[i], b[i])
            r[i] = rr ; g[i] = gg ; b[i] = bb
    elif colorModel == "RGB":
        r /= 255.
        g /= 255.
        b /= 255.

    red = []
    blue = []
    green = []
    xNorm = (x - x[0])/(x[-1] - x[0])
    for i in range(len(x)):
        red.append([xNorm[i],r[i],r[i]])
        green.append([xNorm[i],g[i],g[i]])
        blue.append([xNorm[i],b[i],b[i]])

    # return colormap
    cdict = dict(red=red,green=green,blue=blue)
    return mpl.colors.LinearSegmentedColormap(name=name,segmentdata=cdict)

def cmap_from_cptcity_url(
    url,
    baseurl='http://soliton.vm.bytemark.co.uk/pub/cpt-city/',
    name=None):
    """Create a colormap from a url at cptcity
    Parameters
    ----------
    url : str
        relative or absolute URL to a .cpt file
    baseurl : str, optional
        main directory at cptcity
    name : str, optional
        name for color map
    """
    
    import os
    from urllib.parse import urljoin
    from urllib.request import urlopen
          
    if name is None:
        name = '_'.join(os.path.basename(url).split('.')[:-1])

    url = urljoin(baseurl, url)
    
    # process file directly from online source
    response = urlopen(url)
    return gmtColormap_openfile(response, name=name)

for index, cmap_name in enumerate(list_colormaps(add_extra=True,add_cpt_city=True)):
    if index < len(list_colormaps()):
        color_dict = {}
        color_dict["default"] = get_palette(cmap_name)
        for i in range(3, 13):
            name = "n" + str(i).zfill(2)
            colors = get_palette(cmap_name, i)
            color_dict[name] = colors
        _palette_dict[cmap_name] = color_dict

palettes = Box(_palette_dict, frozen_box=True)