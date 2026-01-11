"""The cartoee module contains functions for creating publication-quality maps with cartopy and Earth Engine data."""

# *******************************************************************************#
# This module contains extra features of the geemap package.                     #
# The geemap community will maintain the extra features.                         #
# *******************************************************************************#

from collections.abc import Iterable
import importlib
import io
import logging
import os
import subprocess
import sys
import warnings

import ee
import matplotlib as mpl
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib import cm, colors
from matplotlib import font_manager as mfonts
from matplotlib.lines import Line2D
import numpy as np
import requests

from . import basemaps

try:
    import cartopy.crs as ccrs
    import cartopy.io.img_tiles as cimgt
    from cartopy.mpl.geoaxes import GeoAxes, GeoAxesSubplot
    from cartopy.mpl.gridliner import LATITUDE_FORMATTER, LONGITUDE_FORMATTER
    from PIL import Image
except ImportError:
    installing_url = (
        "https://scitools.org.uk/cartopy/docs/latest/installing.html#installing"
    )
    print(
        f"cartopy is not installed. Please see {installing_url} for instructions on "
        "how to install cartopy.\n"
        "The easiest way to install cartopy is using conda:\n"
        "    conda install -c conda-forge cartopy"
    )


def get_map(
    ee_object, proj=None, basemap: str | None = None, zoom_level: int = 2, **kwargs
):
    """Returns a new cartopy plot with project and adds Earth Engine image results.

    Args:
        ee_object (ee.Image | ee.FeatureCollection): Earth Engine image result to
            plot.
        proj (cartopy.crs, optional): Cartopy projection that determines the projection
            of the resulting plot. By default uses an equirectangular projection,
            PlateCarree.
        basemap: Basemap to use. It can be one of ["ROADMAP", "SATELLITE", "TERRAIN",
            "HYBRID"] or cartopy.io.img_tiles, such as cimgt.StamenTerrain(). Defaults
            to None. See
            https://scitools.org.uk/cartopy/docs/v0.19/cartopy/io/img_tiles.html.
        zoom_level: Zoom level of the basemap. Defaults to 2.
        **kwargs: remaining keyword arguments are passed to addLayer()

    Returns:
        ax (cartopy.mpl.geoaxes.GeoAxesSubplot): cartopy GeoAxesSubplot object with
            Earth Engine results displayed.
    """
    if (
        isinstance(ee_object, ee.geometry.Geometry)
        or isinstance(ee_object, ee.feature.Feature)
        or isinstance(ee_object, ee.featurecollection.FeatureCollection)
    ):
        features = ee.FeatureCollection(ee_object)

        if "style" in kwargs and kwargs["style"] is not None:
            style = kwargs["style"]
        else:
            style = {}

        props = features.first().propertyNames().getInfo()
        if "style" in props:
            ee_object = features.style(**{"styleProperty": "style"})
        else:
            ee_object = features.style(**style)
    elif isinstance(ee_object, ee.imagecollection.ImageCollection):
        ee_object = ee_object.mosaic()

    if proj is None:
        proj = ccrs.PlateCarree()

    if "style" in kwargs:
        del kwargs["style"]

    ax = mpl.pyplot.axes(projection=proj)

    if basemap is not None:
        if isinstance(basemap, str):
            if basemap.upper() in ["ROADMAP", "SATELLITE", "TERRAIN", "HYBRID"]:
                basemap = cimgt.GoogleTiles(
                    url=basemaps.custom_tiles["xyz"][basemap.upper()]["url"]
                )

        try:
            ax.add_image(basemap, zoom_level)
        except Exception as e:
            print("Failed to add basemap: ", e)

    add_layer(ax, ee_object, **kwargs)

    return ax


def add_layer(
    ax,
    ee_object,
    dims=1000,
    region=None,
    cmap: str | None = None,
    vis_params=None,
    **kwargs,
):
    """Add an Earth Engine image to a cartopy plot.

    Args:
        ax (cartopy.mpl.geoaxes.GeoAxesSubplot | cartopy.mpl.geoaxes.GeoAxes): required
            cartopy GeoAxesSubplot object to add image overlay to.
        ee_object (ee.Image | ee.FeatureCollection): Earth Engine image result to plot.
        dims (list | tuple | int, optional): dimensions to request earth engine result
            as [WIDTH,HEIGHT]. If only one number is passed, it is used as the maximum,
            and the other dimension is computed by proportional scaling. Default None
            and infers dimensions.
        region (list | tuple, optional): Geospatial region of the image to render in
            format [E,S,W,N]. By default, the whole image.
        cmap: String specifying matplotlib colormap to colorize image. If cmap is
            specified visParams cannot contain 'palette' key.
        vis_params (dict, optional): visualization parameters as a dictionary. See
            https://developers.google.com/earth-engine/image_visualization for options.

    Returns:
        ax (cartopy.mpl.geoaxes.GeoAxesSubplot): cartopy GeoAxesSubplot object with
            Earth Engine results displayed.

    Raises:
        ValueError: If `dims` is not of type list, tuple, or int.
        ValueError: If `imgObj` is not of type ee.image.Image.
        ValueError: If `ax` if not of type cartopy.mpl.geoaxes.GeoAxesSubplot.
    """

    if (
        isinstance(ee_object, ee.geometry.Geometry)
        or isinstance(ee_object, ee.feature.Feature)
        or isinstance(ee_object, ee.featurecollection.FeatureCollection)
    ):
        features = ee.FeatureCollection(ee_object)

        if "style" in kwargs and kwargs["style"] is not None:
            style = kwargs["style"]
        else:
            style = {}

        props = features.first().propertyNames().getInfo()
        if "style" in props:
            ee_object = features.style(**{"styleProperty": "style"})
        else:
            ee_object = features.style(**style)
    elif isinstance(ee_object, ee.imagecollection.ImageCollection):
        ee_object = ee_object.mosaic()

    if type(ee_object) is not ee.image.Image:
        raise ValueError("provided `ee_object` is not of type ee.Image")

    if region is not None:
        map_region = ee.Geometry.Rectangle(region).getInfo()["coordinates"]
        view_extent = (region[2], region[0], region[1], region[3])
    else:
        map_region = ee_object.geometry(100).bounds(1).getInfo()["coordinates"]
        # get the image bounds
        x, y = list(zip(*map_region[0]))
        view_extent = [min(x), max(x), min(y), max(y)]

        if ee_object.bandNames().getInfo() == ["vis-red", "vis-green", "vis-blue"]:
            msg = (
                "The region parameter is not specified. Using the default "
                f"region {map_region}. Please specify a region if you get a blank "
                "image."
            )
            warnings.warn(msg)

    if type(dims) not in [list, tuple, int]:
        raise ValueError("provided dims not of type list, tuple, or int")

    if type(ax) not in [GeoAxes, GeoAxesSubplot]:
        raise ValueError(
            "provided axes not of type cartopy.mpl.geoaxes.GeoAxes "
            "or cartopy.mpl.geoaxes.GeoAxesSubplot"
        )

    args = {"format": "png", "crs": "EPSG:4326"}
    args["region"] = map_region
    if dims:
        args["dimensions"] = dims

    if vis_params:
        keys = list(vis_params.keys())
        if cmap and ("palette" in keys):
            raise KeyError(
                "cannot provide `palette` in vis_params if `cmap` is specified"
            )
        elif cmap:
            args["palette"] = ",".join(build_palette(cmap))
        else:
            pass

        args = {**args, **vis_params}

    url = ee_object.getThumbUrl(args)
    response = requests.get(url)
    if response.status_code != 200:
        error = eval(response.content)["error"]
        raise requests.exceptions.HTTPError(f"{error}")

    with io.BytesIO(response.content) as f:
        image = np.array(Image.open(f))

    if image.shape[-1] == 2:
        image = np.concatenate(
            [np.repeat(image[:, :, 0:1], 3, axis=2), image[:, :, -1:]], axis=2
        )

    ax.imshow(
        np.squeeze(image),
        extent=view_extent,
        origin="upper",
        transform=ccrs.PlateCarree(),
        zorder=1,
    )


def build_palette(cmap: str, n: int = 256) -> list[str]:
    """Creates hex color code palette from a matplotlib colormap.

    Args:
        cmap: String specifying matplotlib colormap to colorize image. If cmap is
            specified visParams cannot contain 'palette' key.
        n: Number of hex color codes to create from colormap. Default is 256.

    Returns:
        List of hex color codes from matplotlib colormap for n intervals.
    """
    colormap = cm.get_cmap(cmap, n)
    vals = np.linspace(0, 1, n)
    palette = list(map(lambda x: colors.rgb2hex(colormap(x)[:3]), vals))

    return palette


def add_colorbar(
    ax,
    vis_params,
    loc: str | None = None,
    cmap: str = "gray",
    discrete: bool = False,
    label=None,
    **kwargs,
):
    """Add a colorbar to the map based on visualization parameters provided.

    Args:
        ax (cartopy.mpl.geoaxes.GeoAxesSubplot | cartopy.mpl.geoaxes.GeoAxes): Required
            cartopy GeoAxesSubplot object to add image overlay to.
        loc (str, optional): String specifying the position.
        TODO: Fix the args documentation.
        vis_params (dict, optional): visualization parameters as a dictionary. See
            https://developers.google.com/earth-engine/guides/image_visualization for
            options.
        **kwargs: Remaining keyword arguments are passed to colorbar().

    Raises:
        Warning: If 'discrete' is true when "palette" key is not in visParams.
        ValueError: If `ax` is not of type cartopy.mpl.geoaxes.GeoAxesSubplot.
        ValueError: If 'cmap' or "palette" key in visParams is not provided.
        ValueError: If "min" in visParams is not of type scalar.
        ValueError: If "max" in visParams is not of type scalar.
        ValueError: If 'loc' or 'cax' keywords are not provided.
        ValueError: If 'loc' is not of type str or does not equal available options.
    """
    if type(ax) not in [GeoAxes, GeoAxesSubplot]:
        raise ValueError(
            "provided axes not of type cartopy.mpl.geoaxes.GeoAxes "
            "or cartopy.mpl.geoaxes.GeoAxesSubplot"
        )

    if loc:
        if type(loc) == str and loc in ["left", "right", "bottom", "top"]:
            if "posOpts" not in kwargs:
                posOpts = {
                    "left": [0.01, 0.25, 0.02, 0.5],
                    "right": [0.88, 0.25, 0.02, 0.5],
                    "bottom": [0.25, 0.15, 0.5, 0.02],
                    "top": [0.25, 0.88, 0.5, 0.02],
                }
            else:
                posOpts = {
                    "left": kwargs["posOpts"],
                    "right": kwargs["posOpts"],
                    "bottom": kwargs["posOpts"],
                    "top": kwargs["posOpts"],
                }
                del kwargs["posOpts"]

            cax = ax.figure.add_axes(posOpts[loc])

            if loc == "left":
                mpl.pyplot.subplots_adjust(left=0.18)
            elif loc == "right":
                mpl.pyplot.subplots_adjust(right=0.85)
            else:
                pass

        else:
            raise ValueError(
                'Provided loc not of type str. Options are "left", '
                '"top", "right", or "bottom"'
            )

    elif "cax" in kwargs:
        cax = kwargs["cax"]
        kwargs = {key: kwargs[key] for key in kwargs.keys() if key != "cax"}

    else:
        raise ValueError("loc or cax keywords must be specified.")

    vis_keys = list(vis_params.keys())
    if vis_params:
        if "min" in vis_params:
            vmin = vis_params["min"]
            if type(vmin) not in (int, float):
                raise ValueError("Provided min value not of scalar type.")
        else:
            vmin = 0

        if "max" in vis_params:
            vmax = vis_params["max"]
            if type(vmax) not in (int, float):
                raise ValueError("Provided max value not of scalar type.")
        else:
            vmax = 1

        if "opacity" in vis_params:
            alpha = vis_params["opacity"]
            if type(alpha) not in (int, float):
                raise ValueError("Provided opacity value of not type scalar.")
        elif "alpha" in kwargs:
            alpha = kwargs["alpha"]
        else:
            alpha = 1

        if cmap is not None:
            if discrete:
                warnings.warn(
                    'Discrete keyword used when "palette" key is '
                    "supplied with visParams, creating a continuous "
                    "colorbar."
                )

            cmap = mpl.pyplot.get_cmap(cmap)
            norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

        if "palette" in vis_keys:
            hexcodes = vis_params["palette"]
            hexcodes = [i if i[0] == "#" else "#" + i for i in hexcodes]

            if discrete:
                cmap = mpl.colors.ListedColormap(hexcodes)
                vals = np.linspace(vmin, vmax, cmap.N + 1)
                norm = mpl.colors.BoundaryNorm(vals, cmap.N)

            else:
                cmap = mpl.colors.LinearSegmentedColormap.from_list(
                    "custom", hexcodes, N=256
                )
                norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

        elif cmap is not None:
            if discrete:
                warnings.warn(
                    'discrete keyword used when "palette" key is '
                    "supplied with visParams, creating a continuous "
                    "colorbar..."
                )

            cmap = mpl.pyplot.get_cmap(cmap)
            norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

        else:
            raise ValueError(
                'cmap keyword or "palette" key in visParams must be provided'
            )

    tick_font_size = None
    if "tick_font_size" in kwargs:
        tick_font_size = kwargs.pop("tick_font_size")

    label_font_family = None
    if "label_font_family" in kwargs:
        label_font_family = kwargs.pop("label_font_family")

    label_font_size = None
    if "label_font_size" in kwargs:
        label_font_size = kwargs.pop("label_font_size")

    cb = mpl.colorbar.ColorbarBase(cax, norm=norm, alpha=alpha, cmap=cmap, **kwargs)

    if label is not None:
        if label_font_size is not None and label_font_family is not None:
            cb.set_label(label, fontsize=label_font_size, family=label_font_family)
        elif label_font_size is not None and label_font_family is None:
            cb.set_label(label, fontsize=label_font_size)
        elif label_font_size is None and label_font_family is not None:
            cb.set_label(label, family=label_font_family)
        else:
            cb.set_label(label)
    elif "bands" in vis_keys:
        cb.set_label(vis_params["bands"])

    if tick_font_size is not None:
        cb.ax.tick_params(labelsize=tick_font_size)


def _buffer_box(
    bbox: list[float] | tuple[float, float, float, float], interval: float
) -> tuple[float, float, float, float]:
    """Buffer a bounding box to the nearest multiple of interval.

    Args:
        bbox: Values specifying coordinates, Expects order to be [W,E,S,N].
        interval: Multiple at which to buffer coordianates to.

    Returns:
        Extend of buffered coordinates rounded to interval in order of [W,E,S,N].
    """
    if bbox[0] % interval != 0:
        xmin = bbox[0] - (bbox[0] % interval)
    else:
        xmin = bbox[0]

    if bbox[1] % interval != 0:
        xmax = bbox[1] + (interval - (bbox[1] % interval))
    else:
        xmax = bbox[1]

    if bbox[2] % interval != 0:
        ymin = bbox[2] - (bbox[2] % interval)
    else:
        ymin = bbox[2]

    if bbox[3] % interval != 0:
        ymax = bbox[3] + (interval - (bbox[3] % interval))
    else:
        ymax = bbox[3]

    return xmin, xmax, ymin, ymax


def bbox_to_extent(
    bbox: list[float] | tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    """Reorder a list of coordinates from [W,S,E,N] to [W,E,S,N].

    Args:
        bbox: Coordinates in the order of [W,S,E,N].

    Returns:
        Extent in the order of [W,E,S,N].
    """
    return bbox[0], bbox[2], bbox[1], bbox[3]


def add_gridlines(
    ax,
    interval: float | list[float] | None = None,
    n_ticks: int | list[int] | None = None,
    xs: list[float] | None = None,
    ys: list[float] | None = None,
    buffer_out: bool = True,
    xtick_rotation: float | str = "horizontal",
    ytick_rotation: float | str = "horizontal",
    **kwargs,
):
    """Add gridlines and format ticks to map.

    Args:
        ax (cartopy.mpl.geoaxes.GeoAxesSubplot | cartopy.mpl.geoaxes.GeoAxes): cartopy
            GeoAxesSubplot object to add the gridlines to.
        interval: Interval at which to create gridlines, Units are decimal
            degrees. Lists will be interpreted as [x_interval, y_interval]. Default =
            None.
        n_ticks: Number of gridlines to create within map extent. Lists will be
            interpreted as [nx, ny]. Default = None.
        xs: x coordinates to create gridlines. Default = None.
        ys: y coordinates to create gridlines. Default = None.
        buffer_out: Buffer out the extent to insure coordinates created cover map
            extent. Default = true.
        xtick_rotation: TODO
        ytick_rotation: TODO
        **kwargs: remaining keyword arguments are passed to gridlines()

    Raises:
        ValueError: if all interval, n_ticks, or (xs,ys) are set to None
    """
    view_extent = ax.get_extent()
    extent = view_extent

    if xs is not None:
        xmain = xs

    elif interval is not None:
        if isinstance(interval, Iterable):
            xspace = interval[0]
        else:
            xspace = interval

        if buffer_out:
            extent = _buffer_box(extent, xspace)

        xmain = np.arange(extent[0], extent[1] + xspace, xspace)

    elif n_ticks is not None:
        if isinstance(n_ticks, Iterable):
            n_x = n_ticks[0]
        else:
            n_x = n_ticks

        xmain = np.linspace(extent[0], extent[1], n_x)
    else:
        raise ValueError(
            "One of variables interval, n_ticks, or xs must be defined. "
            "If you would like default gridlines, please use `ax.gridlines()`."
        )

    if ys is not None:
        ymain = ys

    elif interval is not None:
        if isinstance(interval, Iterable):
            yspace = interval[1]
        else:
            yspace = interval

        if buffer_out:
            extent = _buffer_box(extent, yspace)

        ymain = np.arange(extent[2], extent[3] + yspace, yspace)

    elif n_ticks is not None:
        if isinstance(n_ticks, Iterable):
            n_y = n_ticks[1]
        else:
            n_y = n_ticks

        ymain = np.linspace(extent[2], extent[3], n_y)

    else:
        raise ValueError(
            "One of variables interval, n_ticks, or ys must be defined. "
            "If you would like default gridlines, please use `ax.gridlines()`."
        )

    ax.gridlines(xlocs=xmain, ylocs=ymain, **kwargs)

    xin = xmain[(xmain >= view_extent[0]) & (xmain <= view_extent[1])]
    yin = ymain[(ymain >= view_extent[2]) & (ymain <= view_extent[3])]

    # Set tick labels.
    ax.set_xticks(xin, crs=ccrs.PlateCarree())
    ax.set_yticks(yin, crs=ccrs.PlateCarree())

    ax.set_xticklabels(xin, rotation=xtick_rotation, ha="center")
    ax.set_yticklabels(yin, rotation=ytick_rotation, va="center")

    ax.xaxis.set_major_formatter(LONGITUDE_FORMATTER)
    ax.yaxis.set_major_formatter(LATITUDE_FORMATTER)


def pad_view(ax, factor: float | list[float] = 0.05) -> None:
    """Pad area around the view extent of a map, used for visual appeal.

    Args:
        ax (cartopy.mpl.geoaxes.GeoAxesSubplot | cartopy.mpl.geoaxes.GeoAxes): cartopy
            GeoAxesSubplot object to pad view extent.
        factor: Pad view extent accepts float [0-1] or a list of floats that will be
            interpreted at [xfactor, yfactor].
    """
    view_extent = ax.get_extent()

    if isinstance(factor, Iterable):
        xfactor, yfactor = factor
    else:
        xfactor, yfactor = factor, factor

    x_diff = view_extent[1] - view_extent[0]
    y_diff = view_extent[3] - view_extent[2]

    xmin = view_extent[0] - (x_diff * xfactor)
    xmax = view_extent[1] + (x_diff * xfactor)
    ymin = view_extent[2] - (y_diff * yfactor)
    ymax = view_extent[3] + (y_diff * yfactor)

    ax.set_ylim(ymin, ymax)
    ax.set_xlim(xmin, xmax)


def add_north_arrow(
    ax,
    text: str = "N",
    xy=(0.1, 0.1),
    arrow_length: float = 0.1,
    text_color: str = "black",
    arrow_color: str = "black",
    fontsize: int = 20,
    width: int = 5,
    headwidth: int = 15,
    ha: str = "center",
    va: str = "center",
):
    """Add a north arrow to the map.

    Args:
        ax (cartopy.mpl.geoaxes.GeoAxesSubplot | cartopy.mpl.geoaxes.GeoAxes): cartopy
            GeoAxesSubplot object.
        text: Text for north arrow. Defaults to "N".
        xy (tuple, optional): Location of the north arrow. Each number representing the
            percentage length of the map from the lower-left corner. Defaults to (0.1,
            0.1).
        arrow_length: Length of the north arrow. Defaults to 0.1 (10% length of the
            map).
        text_color: Text color. Defaults to "black".
        arrow_color: North arrow color. Defaults to "black".
        fontsize: Text font size. Defaults to 20.
        width: Width of the north arrow. Defaults to 5.
        headwidth: head width of the north arrow. Defaults to 15.
        ha: Horizontal alignment. Defaults to "center".
        va: Vertical alignment. Defaults to "center".
    """
    ax.annotate(
        text,
        xy=xy,
        xytext=(xy[0], xy[1] - arrow_length),
        color=text_color,
        arrowprops=dict(facecolor=arrow_color, width=width, headwidth=headwidth),
        ha=ha,
        va=va,
        fontsize=fontsize,
        xycoords=ax.transAxes,
    )


def convert_SI(val: float, unit_in: str, unit_out: str) -> float:
    """Unit converter.

    Args:
        val: The value to convert.
        unit_in: The input unit.
        unit_out: The output unit.

    Returns:
        Value after unit conversion.
    """
    SI = {
        "cm": 0.01,
        "m": 1.0,
        "km": 1000.0,
        "inch": 0.0254,
        "foot": 0.3048,
        "mile": 1609.34,
    }
    return val * SI[unit_in] / SI[unit_out]


def add_scale_bar(
    ax,
    metric_distance=4,
    unit="km",
    at_x=(0.05, 0.5),
    at_y=(0.08, 0.11),
    max_stripes=5,
    ytick_label_margins=0.25,
    fontsize=8,
    font_weight="bold",
    rotation=0,
    zorder=999,
    paddings={"xmin": 0.05, "xmax": 0.05, "ymin": 1.5, "ymax": 0.5},
    bbox_kwargs={"facecolor": "white", "edgecolor": "black", "alpha": 0.5},
):
    """Add a scale bar to the map.

    Args:
        ax (cartopy.mpl.geoaxes.GeoAxesSubplot | cartopy.mpl.geoaxes.GeoAxes): cartopy
            GeoAxesSubplot object.
        metric_distance (int | float, optional): Length in meters of each region of the
          scale bar. Defaults to 4.
        unit (str, optional): Scale bar distance unit. Defaults to "km"
        at_x (float, optional): Target axes X coordinates (0..1) of box (= left,
            right). Defaults to (0.05, 0.2).
        at_y (float, optional): Axes Y coordinates (0..1) of box (= lower,
            upper). Defaults to (0.08, 0.11).
        max_stripes (int, optional): Typical/maximum number of black+white
            regions. Defaults to 5.
        ytick_label_margins (float, optional): Location of distance labels on the Y
            axis. Defaults to 0.25.
        fontsize (int, optional): Scale bar text size. Defaults to 8.
        font_weight (str, optional): Font weight. Defaults to 'bold'.
        rotation (int, optional): Rotation of the length labels for each region of the
            scale bar. Defaults to 0.
        zorder (float, optional): z order of the text bounding box.
        paddings (dict, optional): Boundaries of the box that contains the scale bar.
        bbox_kwargs (dict, optional): Style of the box containing the scale bar.
    """

    warnings.filterwarnings("ignore")

    def _crs_coord_project(crs_target, xcoords, ycoords, crs_source):
        """Metric coordinates (x, y) from cartopy.crs_source."""

        axes_coords = crs_target.transform_points(crs_source, xcoords, ycoords)

        return axes_coords

    def _add_bbox(ax, list_of_patches, paddings={}, bbox_kwargs={}):
        """Add a box behind the scalebar.

        Code inspired by:
            https://stackoverflow.com/questions/17086847/box-around-text-in-matplotlib
        """
        zorder = list_of_patches[0].get_zorder() - 1

        xmin = min([t.get_window_extent().xmin for t in list_of_patches])
        xmax = max([t.get_window_extent().xmax for t in list_of_patches])
        ymin = min([t.get_window_extent().ymin for t in list_of_patches])
        ymax = max([t.get_window_extent().ymax for t in list_of_patches])

        xmin, ymin = ax.transData.inverted().transform((xmin, ymin))
        xmax, ymax = ax.transData.inverted().transform((xmax, ymax))

        xmin = xmin - ((xmax - xmin) * paddings["xmin"])
        ymin = ymin - ((ymax - ymin) * paddings["ymin"])

        xmax = xmax + ((xmax - xmin) * paddings["xmax"])
        ymax = ymax + ((ymax - ymin) * paddings["ymax"])

        width = xmax - xmin
        height = ymax - ymin

        # Setting xmin according to height.
        rect = patches.Rectangle(
            (xmin, ymin),
            width,
            height,
            facecolor=bbox_kwargs["facecolor"],
            edgecolor=bbox_kwargs["edgecolor"],
            alpha=bbox_kwargs["alpha"],
            transform=ax.projection,
            fill=True,
            clip_on=False,
            zorder=zorder,
        )

        ax.add_patch(rect)
        return ax

    old_proj = ax.projection
    ax.projection = ccrs.PlateCarree()

    # Set a planar (metric) projection for the centroid of a given axes projection.
    # First get centroid lon and lat coordinates.
    lon_0, lon_1, lat_0, lat_1 = ax.get_extent(ax.projection.as_geodetic())

    central_lon = np.mean([lon_0, lon_1])
    central_lat = np.mean([lat_0, lat_1])

    # Second, set the planar (metric) projection centered in the centroid of the axes.
    # Centroid coordinates must be in lon/lat.
    proj = ccrs.EquidistantConic(
        central_longitude=central_lon, central_latitude=central_lat
    )

    # Fetch axes coordinates in meters.
    x0, _, y0, y1 = ax.get_extent(proj)
    ymean = np.mean([y0, y1])

    # Set target rectangle in-visible-area (aka 'Axes') coordinates.
    axfrac_ini, _ = at_x
    ayfrac_ini, ayfrac_final = at_y

    # Choose exact X points as sensible grid ticks with Axis 'ticker' helper.
    converted_metric_distance = convert_SI(metric_distance, unit, "m")

    xcoords = []
    ycoords = []
    xlabels = []
    for i in range(0, 1 + max_stripes):
        dx = (converted_metric_distance * i) + x0
        xlabels.append(metric_distance * i)
        xcoords.append(dx)
        ycoords.append(ymean)

    xcoords = np.asanyarray(xcoords)
    ycoords = np.asanyarray(ycoords)

    # Ensure that the coordinate projection is in degrees.
    x_targets, _, _ = _crs_coord_project(ax.projection, xcoords, ycoords, proj).T
    x_targets = [x + (axfrac_ini * (lon_1 - lon_0)) for x in x_targets]

    # Set transform for plotting.
    transform = ax.projection

    # Minimum and maximum for limits.
    xl0, xl1 = x_targets[0], x_targets[-1]

    # Calculate Axes Y coordinates of box top+bottom.
    yl0, yl1 = (
        lat_0 + ay_frac * (lat_1 - lat_0) for ay_frac in [ayfrac_ini, ayfrac_final]
    )

    # Calculate Axes Y distance of ticks + label margins.
    y_margin = (yl1 - yl0) * ytick_label_margins

    # Fill 'stripes' and draw their boundaries.
    fill_colors = ["black", "white"]
    i_color = 0

    filled_boxs = []
    for xi0, xi1 in zip(x_targets[:-1], x_targets[1:]):
        filled_box = plt.fill(
            (xi0, xi1, xi1, xi0, xi0),
            (yl0, yl0, yl1, yl1, yl0),
            fill_colors[i_color],
            transform=transform,
            clip_on=False,
            zorder=zorder,
        )

        filled_boxs.append(filled_box[0])

        # Draw boundary.
        plt.plot(
            (xi0, xi1, xi1, xi0, xi0),
            (yl0, yl0, yl1, yl1, yl0),
            "black",
            clip_on=False,
            transform=transform,
            zorder=zorder,
        )

        i_color = 1 - i_color

    # adding boxes
    _add_bbox(ax, filled_boxs, bbox_kwargs=bbox_kwargs, paddings=paddings)

    # Add short tick lines.
    for x in x_targets:
        plt.plot(
            (x, x),
            (yl0, yl0 - y_margin),
            "black",
            transform=transform,
            zorder=zorder,
            clip_on=False,
        )

    # Add a scale legend unit.
    font_props = mfonts.FontProperties(size=fontsize, weight=font_weight)

    plt.text(
        0.5 * (xl0 + xl1),
        yl1 + y_margin,
        unit,
        color="black",
        verticalalignment="bottom",
        horizontalalignment="center",
        fontproperties=font_props,
        transform=transform,
        clip_on=False,
        zorder=zorder,
    )

    # add numeric labels
    for x, xlabel in zip(x_targets, xlabels):
        plt.text(
            x,
            yl0 - 2 * y_margin,
            f"{(xlabel):g}",
            verticalalignment="top",
            horizontalalignment="center",
            fontproperties=font_props,
            transform=transform,
            rotation=rotation,
            clip_on=False,
            zorder=zorder + 1,
        )

    # Adjust figure borders to ensure that the scalebar is within its limits.
    ax.projection = old_proj
    ax.get_figure().canvas.draw()


def add_scale_bar_lite(
    ax,
    length=None,
    xy=(0.5, 0.05),
    linewidth=3,
    fontsize=20,
    color="black",
    unit="km",
    ha="center",
    va="bottom",
):
    """Add a lite version of scale bar to the map.

    Reference: https://stackoverflow.com/a/50674451/2676166

    Args:
        ax (cartopy.mpl.geoaxes.GeoAxesSubplot | cartopy.mpl.geoaxes.GeoAxes): cartopy
            GeoAxesSubplot object.
        length ([type], optional): Length of the scale car. Defaults to None.
        xy (tuple, optional): Location of the north arrow. Each number representing the
            percentage length of the map from the lower-left cornor.
            Defaults to (0.1, 0.1).
        linewidth (int, optional): Line width of the scale bar. Defaults to 3.
        fontsize (int, optional): Text font size. Defaults to 20.
        color (str, optional): Color for the scale bar. Defaults to "black".
        unit (str, optional): Length unit for the scale bar. Defaults to "km".
        ha (str, optional): Horizontal alignment. Defaults to "center".
        va (str, optional): Vertical alignment. Defaults to "bottom".
    """

    allow_units = ["cm", "m", "km", "inch", "foot", "mile"]
    if unit not in allow_units:
        print(
            "The unit must be one of the following: {}".format(", ".join(allow_units))
        )
        return

    num = length

    # Get the limits of the axis in lat long.
    llx0, llx1, lly0, lly1 = ax.get_extent(ccrs.PlateCarree())
    # Make tmc horizontally centred on the middle of the map,
    # Vertically at scale bar location.
    sbllx = (llx1 + llx0) / 2
    sblly = lly0 + (lly1 - lly0) * xy[1]
    tmc = ccrs.TransverseMercator(sbllx, sblly, approx=True)
    # Get the extent of the plotted area in coordinates in meters.
    x0, x1, y0, y1 = ax.get_extent(tmc)
    # Turn the specified scalebar location into coordinates in meters.
    sbx = x0 + (x1 - x0) * xy[0]
    sby = y0 + (y1 - y0) * xy[1]

    # Calculate a scale bar length if none has been given.
    # There's probably a more pythonic way of rounding the number but this works.
    if not length:
        length = (x1 - x0) / 5000  # in km
        ndim = int(np.floor(np.log10(length)))  # Number of digits in number.
        length = round(length, -ndim)  # round to 1sf
        # Returns numbers starting with the list.

        def scale_number(x):
            if str(x)[0] in ["1", "2", "5"]:
                return int(x)
            else:
                return scale_number(x - 10**ndim)

        length = scale_number(length)
        num = length
    else:
        length = convert_SI(length, unit, "km")

    # Generate the x coordinate for the ends of the scalebar.
    bar_xs = [sbx - length * 500, sbx + length * 500]
    ax.plot(bar_xs, [sby, sby], transform=tmc, color=color, linewidth=linewidth)

    # Plot the scalebar label.
    ax.text(
        sbx,
        sby,
        str(num) + " " + unit,
        transform=tmc,
        horizontalalignment=ha,
        verticalalignment=va,
        color=color,
        fontsize=fontsize,
    )


def create_legend(
    linewidth=None,
    linestyle=None,
    color=None,
    marker=None,
    markersize=None,
    markeredgewidth=None,
    markeredgecolor=None,
    markerfacecolor=None,
    markerfacecoloralt=None,
    fillstyle=None,
    antialiased=None,
    dash_capstyle=None,
    solid_capstyle=None,
    dash_joinstyle=None,
    solid_joinstyle=None,
    pickradius=5,
    drawstyle=None,
    markevery=None,
    **kwargs,
):
    if linewidth is None and marker is None:
        raise ValueError("Either linewidth or marker must be specified.")


def add_legend(
    ax,
    legend_elements=None,
    loc="lower right",
    font_size=14,
    font_weight="normal",
    font_color="black",
    font_family=None,
    title=None,
    title_fontize=16,
    title_fontproperties=None,
    **kwargs,
):
    """Adds a legend to the map.

    The legend elements can be formatted as:

        legend_elements = [Line2D([], [], color='#00ffff', lw=2, label='Coastline'),
        Line2D([], [], marker='o', color='#A8321D', label='City',
        markerfacecolor='#A8321D', markersize=10, ls ='')]

    For more legend properties, see:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.legend.html

    Args:
        ax (cartopy.mpl.geoaxes.GeoAxesSubplot | cartopy.mpl.geoaxes.GeoAxes): Required
            cartopy GeoAxesSubplot object.
        legend_elements (list, optional): A list of legend elements. Defaults to None.
        loc (str, optional): Location of the legend, can be any of
            ['upper left', 'upper right', 'lower left', 'lower right'].
            Defaults to "lower right".
        font_size(int|string, optional): Font size. Either an absolute font size or an
            relative value of 'xx-small', 'x-small', 'small', 'medium', 'large',
            'x-large', 'xx-large'. Defaults to 14.
        font_weight(string|int, optional): Font weight. A numeric value in the range
            0-1000 or one of 'ultralight', 'light', 'normal' (default), 'regular', 'book',
            'medium', 'roman', 'semibold', 'demibold', 'demi', 'bold', 'heavy',
            'extra bold', 'black'. Defaults to 'normal'.
        font_color(str, optional): Text color. Defaults to "black".
        font_family(string, optional): Name of font family. Set to a font family like
            'SimHei' if you want to show Chinese in the legend. Defaults to None.

    Raises:
        Exception: If the legend fails to add.
    """
    if title_fontize is not None and (title_fontproperties is not None):
        raise ValueError("title_fontize and title_fontproperties cannot be both set.")
    elif title_fontize is not None:
        kwargs["title_fontsize"] = title_fontize
    elif title_fontproperties is not None:
        kwargs["title_fontproperties"] = title_fontproperties

    try:
        if legend_elements is None:
            legend_elements = [
                Line2D([], [], color="#00ffff", lw=2, label="Coastline"),
                Line2D(
                    [],
                    [],
                    marker="o",
                    color="#A8321D",
                    label="City",
                    markerfacecolor="#A8321D",
                    markersize=10,
                    ls="",
                ),
            ]
        if font_family is not None:
            fontdict = {"family": font_family, "size": font_size, "weight": font_weight}
        else:
            fontdict = {"size": font_size, "weight": font_weight}
        leg = ax.legend(
            handles=legend_elements,
            loc=loc,
            prop=fontdict,
            title=title,
            **kwargs,
        )

        # Change font color If default color is changed.
        if font_color != "black":
            for text in leg.get_texts():
                text.set_color(font_color)
    except Exception as e:
        raise Exception(e)


def get_image_collection_gif(
    ee_ic,
    out_dir,
    out_gif,
    vis_params,
    region,
    cmap=None,
    proj=None,
    fps=10,
    mp4=False,
    grid_interval=None,
    plot_title="",
    date_format="YYYY-MM-dd",
    fig_size=(10, 10),
    dpi_plot=100,
    file_format="png",
    north_arrow_dict={},
    scale_bar_dict={},
    overlay_layers=[],
    overlay_styles=[],
    colorbar_dict={},
    verbose=True,
    **kwargs,
):
    """Download all images in an image collection and generate a gif/video.

    Args:
        ee_ic (object): ee.ImageCollection.
        out_dir (str): The output directory of images and video.
        out_gif (str): The name of the gif file.
        vis_params (dict): Visualization parameters as a dictionary.
        region (list | tuple): Geospatial region of the image to render in format
            [E,S,W,N].
        fps (int, optional): Video frames per second. Defaults to 10.
        mp4 (bool, optional): Whether to create mp4 video.
        grid_interval (float | tuple[float]): Interval at which to create gridlines,
            units are decimal degrees. Lists will be interpreted a (x_interval,
            y_interval), such as (0.1, 0.1). Defaults to None.
        plot_title (str): Plot title. Defaults to "".
        date_format (str, optional): A pattern, as described at
            http://joda-time.sourceforge.net/apidocs/org/joda/time/format/DateTimeFormat.html.
            Defaults to "YYYY-MM-dd".
        fig_size (tuple, optional): Size of the figure.
        dpi_plot (int, optional): The resolution in dots per inch of the plot.
        file_format (str, optional): Either 'png' or 'jpg'. Defaults to 'png'.
        north_arrow_dict (dict, optional): Parameters for the north arrow. See
            https://geemap.org/cartoee/#geemap.cartoee.add_north_arrow.
            Defaults to {}.
        scale_bar_dict (dict, optional): Parameters for the scale bar. See
            https://geemap.org/cartoee/#geemap.cartoee.add_scale_bar.
            Defaults to {}.
        overlay_layers (list, optional): A list of Earth Engine objects to overlay on
            the map. Defaults to [].
        overlay_styles (list, optional): A list of dictionaries of visualization
            parameters for overlay layers. Defaults to [].
        colorbar_dict (dict, optional): Parameters for the colorbar. See
            https://geemap.org/cartoee/#geemap.cartoee.add_colorbar.
            Defaults to {}.
        verbose (bool, optional): Whether or not to print text when the program is
            running. Defaults to True.
        **kwargs: Additional keyword arguments are passed to the add_layer() function.
    """
    from .geemap import png_to_gif, jpg_to_gif

    out_dir = os.path.abspath(out_dir)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    out_gif = os.path.join(out_dir, out_gif)

    count = int(ee_ic.size().getInfo())
    names = ee_ic.aggregate_array("system:index").getInfo()
    images = ee_ic.toList(count)

    dates = ee_ic.aggregate_array("system:time_start")
    dates = dates.map(lambda d: ee.Date(d).format(date_format)).getInfo()

    digits = len(str(len(dates)))

    # List of file names.
    img_list = []

    for i, date in enumerate(dates):
        image = ee.Image(images.get(i))
        name = str(i + 1).zfill(digits) + "." + file_format
        out_img = os.path.join(out_dir, name)
        img_list.append(out_img)

        if verbose:
            print(f"Downloading {i+1}/{count}: {name} ...")

        # Size plot.
        fig = plt.figure(figsize=fig_size)

        fig.patch.set_facecolor("white")

        # Plot image.
        ax = get_map(image, region=region, vis_params=vis_params, cmap=cmap, proj=proj)

        # Check length of overlay layers and styles.
        if len(overlay_layers) != len(overlay_styles):
            raise ValueError(
                "The length of overlay_layers and overlay_styles must be the same."
            )

        for ee_object, style in zip(overlay_layers, overlay_styles):
            if (
                isinstance(ee_object, ee.geometry.Geometry)
                or isinstance(ee_object, ee.feature.Feature)
                or isinstance(ee_object, ee.featurecollection.FeatureCollection)
            ):
                overlay_vis_params = (
                    None  # For vector data, we can pass style parameters directly.
                )
            elif (
                isinstance(ee_object, ee.image.Image)
                or isinstance(ee_object, ee.imagecollection.ImageCollection)
                or isinstance(ee_object, ee.imagecollection.ImageCollection)
            ):
                overlay_vis_params = style  # For raster, need to pass vis_params.
                style = None
            else:
                raise ValueError(
                    "The overlay object must be an ee.Geometry, ee.Feature, "
                    "ee.FeatureCollection, ee.Image, or ee.ImageCollection."
                )

            add_layer(
                ax,
                ee_object,
                region=region,
                cmap=cmap,
                vis_params=overlay_vis_params,
                style=style,
                **kwargs,
            )

        if colorbar_dict:
            add_colorbar(ax, vis_params, **colorbar_dict)

        if grid_interval is not None:
            add_gridlines(ax, interval=grid_interval, linestyle=":")

        if len(plot_title) > 0:
            ax.set_title(label=plot_title + " " + date + "\n", fontsize=15)

        # Add scale bar.
        if len(scale_bar_dict) > 0:
            add_scale_bar_lite(ax, **scale_bar_dict)
        # Add north arrow.
        if len(north_arrow_dict) > 0:
            add_north_arrow(ax, **north_arrow_dict)

        plt.savefig(
            fname=out_img,
            dpi=dpi_plot,
            bbox_inches="tight",
            facecolor=fig.get_facecolor(),
        )

        plt.clf()
        plt.close()

    out_gif = os.path.abspath(out_gif)
    if file_format == "png":
        png_to_gif(out_dir, out_gif, fps)
    elif file_format == "jpg":
        jpg_to_gif(out_dir, out_gif, fps)
    if verbose:
        print(f"GIF saved to {out_gif}")

    if mp4:
        video_filename = out_gif.replace(".gif", ".mp4")

        try:
            import cv2
        except ImportError:
            print("Installing opencv-python ...")
            subprocess.check_call(["python", "-m", "pip", "install", "opencv-python"])
            import cv2

        output_video_file_name = os.path.join(out_dir, video_filename)

        frame = cv2.imread(img_list[0])
        height, width, _ = frame.shape
        frame_size = (width, height)
        fps_video = fps

        # Make mp4
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")

        def convert_frames_to_video(
            input_list, output_video_file_name, fps_video, frame_size
        ):
            """Convert frames to video

            Args:
                input_list (list): Downloaded Image Name List.
                output_video_file_name (str): The name of the video file in the image
                    directory.
                fps_video (int): Video frames per second.
                frame_size (tuple): Frame size.
            """
            out = cv2.VideoWriter(output_video_file_name, fourcc, fps_video, frame_size)
            num_frames = len(input_list)

            for i in range(num_frames):
                img_path = input_list[i]
                img = cv2.imread(img_path)
                out.write(img)

            out.release()
            cv2.destroyAllWindows()

        convert_frames_to_video(
            input_list=img_list,
            output_video_file_name=output_video_file_name,
            fps_video=fps_video,
            frame_size=frame_size,
        )

        if verbose:
            print(f"MP4 saved to {output_video_file_name}")


def savefig(fig, fname, dpi="figure", bbox_inches="tight", **kwargs):
    """Save figure to file. It wraps the matplotlib.pyplot.savefig() function.

    See https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html for
    more details.

    Args:
        fig (matplotlib.figure.Figure): The figure to save.
        fname (str): A path to a file, or a Python file-like object.
        dpi (int | str, optional): The resolution in dots per inch. If 'figure', use the
            figure's dpi value. Defaults to 'figure'.
        bbox_inches (str, optional): Bounding box in inches: only the given portion of
            the figure is saved.  If 'tight', try to figure out the tight bbox of the
            figure.
        kwargs (dict, optional): Additional keyword arguments are passed on to the
            savefig() method.
    """

    fig.savefig(fname=fname, dpi=dpi, bbox_inches=bbox_inches, **kwargs)
