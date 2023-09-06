"""Tile layers that show EE objects."""

# *******************************************************************************#
# This module contains core features features of the geemap package.             #
# The Earth Engine team and the geemap community will maintain the core features.#
# *******************************************************************************#

import box
import ee
import folium
import ipyleaflet

from . import common


def _get_tile_url_format(ee_object, vis_params):
    image = _ee_object_to_image(ee_object, vis_params)
    map_id_dict = ee.Image(image).getMapId(vis_params)
    return map_id_dict["tile_fetcher"].url_format


def _validate_vis_params(vis_params):
    if vis_params is None:
        return {}

    if not isinstance(vis_params, dict):
        raise TypeError("vis_params must be a dictionary")

    valid_dict = vis_params.copy()

    if "palette" in valid_dict:
        valid_dict["palette"] = _validate_palette(valid_dict["palette"])

    return valid_dict


def _ee_object_to_image(ee_object, vis_params):
    if isinstance(ee_object, (ee.Geometry, ee.Feature, ee.FeatureCollection)):
        features = ee.FeatureCollection(ee_object)
        color = vis_params.get("color", "000000")
        image_outline = features.style(
            **{
                "color": color,
                "fillColor": "00000000",
                "width": vis_params.get("width", 2),
            }
        )
        return (
            features.style(**{"fillColor": color})
            .updateMask(ee.Image.constant(0.5))
            .blend(image_outline)
        )
    elif isinstance(ee_object, ee.Image):
        return ee_object
    elif isinstance(ee_object, ee.ImageCollection):
        return ee_object.mosaic()
    raise AttributeError(
        f"\n\nCannot add an object of type {ee_object.__class__.__name__} to the map."
    )


def _validate_palette(palette):
    if isinstance(palette, tuple):
        palette = list(palette)
    if isinstance(palette, box.Box):
        if "default" not in palette:
            raise ValueError("The provided palette Box object is invalid.")
        return list(palette["default"])
    if isinstance(palette, str):
        return common.check_cmap(palette)
    if isinstance(palette, list):
        return palette
    raise ValueError("The palette must be a list of colors, a string, or a Box object.")


class EEFoliumTileLayer(folium.raster_layers.TileLayer):
    """A Folium raster TileLayer that shows an EE object."""

    def __init__(
        self,
        ee_object,
        vis_params=None,
        name="Layer untitled",
        shown=True,
        opacity=1.0,
        **kwargs,
    ):
        """Initialize the folium tile layer.

        Args:
            ee_object (Collection|Feature|Image|MapId): The object to add to the map.
            vis_params (dict, optional): The visualization parameters. Defaults to None.
            name (str, optional): The name of the layer. Defaults to 'Layer untitled'.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            opacity (float, optional): The layer's opacity represented as a number between 0 and 1. Defaults to 1.
        """
        self.url_format = _get_tile_url_format(
            ee_object, _validate_vis_params(vis_params)
        )
        super().__init__(
            tiles=self.url_format,
            attr="Google Earth Engine",
            name=name,
            overlay=True,
            control=True,
            show=shown,
            opacity=opacity,
            max_zoom=24,
            **kwargs,
        )


class EELeafletTileLayer(ipyleaflet.TileLayer):
    """An ipyleaflet TileLayer that shows an EE object."""

    EE_TYPES = (
        ee.Geometry,
        ee.Feature,
        ee.FeatureCollection,
        ee.Image,
        ee.ImageCollection,
    )

    def __init__(
        self,
        ee_object,
        vis_params=None,
        name="Layer untitled",
        shown=True,
        opacity=1.0,
        **kwargs,
    ):
        """Initialize the ipyleaflet tile layer.

        Args:
            ee_object (Collection|Feature|Image|MapId): The object to add to the map.
            vis_params (dict, optional): The visualization parameters. Defaults to None.
            name (str, optional): The name of the layer. Defaults to 'Layer untitled'.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            opacity (float, optional): The layer's opacity represented as a number between 0 and 1. Defaults to 1.
        """
        self.url_format = _get_tile_url_format(
            ee_object, _validate_vis_params(vis_params)
        )
        super().__init__(
            url=self.url_format,
            attribution="Google Earth Engine",
            name=name,
            opacity=opacity,
            visible=shown,
            max_zoom=24,
            **kwargs,
        )
