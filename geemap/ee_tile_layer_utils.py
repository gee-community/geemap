"""Utils and helpers for tile layers."""

import box
import ee

from . import common


def get_tile_url_format(ee_object, vis_params):
    image = _ee_object_to_image(ee_object, vis_params)
    map_id_dict = ee.Image(image).getMapId(vis_params)
    return map_id_dict["tile_fetcher"].url_format


def validate_vis_params(vis_params):
    if vis_params is None:
        return {}
    if "palette" in vis_params:
        vis_params["palette"] = _validate_palette(vis_params["palette"])
    return vis_params


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
    if isinstance(palette, box.Box):
        if "default" not in palette:
            raise ValueError("The provided palette Box object is invalid.")
        return palette["default"]
    if isinstance(palette, str):
        return common.check_cmap(palette)
    if isinstance(palette, list):
        return palette
    raise ValueError("The palette must be a list of colors, a string, or a Box object.")
