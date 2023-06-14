"""An ipyleaflet TileLayer that shows an EE object."""

import ipyleaflet

from . import ee_tile_layer_utils


class EeLeafletTileLayer(ipyleaflet.TileLayer):
    """An ipyleaflet TileLayer that shows an EE object."""

    url_format = None
    vis_params = None

    def __init__(
        self,
        ee_object,
        vis_params=None,
        name="Layer untitled",
        shown=True,
        opacity=1.0,
        **kwargs,
    ):
        """Args:
        ee_object (Collection|Feature|Image|MapId): The object to add to the map.
        vis_params (dict, optional): The visualization parameters. Defaults to None.
        name (str, optional): The name of the layer. Defaults to 'Layer untitled'.
        shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
        opacity (float, optional): The layer's opacity represented as a number between 0 and 1. Defaults to 1.
        """
        self.vis_params = ee_tile_layer_utils.validate_vis_params(vis_params)
        self.url_format = ee_tile_layer_utils.get_tile_url_format(ee_object, vis_params)
        super().__init__(
            url=self.url_format,
            attribution="Google Earth Engine",
            name=name,
            opacity=opacity,
            visible=shown,
            max_zoom=24,
            **kwargs,
        )
