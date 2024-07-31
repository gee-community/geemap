"""Module for creating interactive maps with the folium library."""

# *******************************************************************************#
# This module contains extra features of the geemap package.                     #
# The geemap community will maintain the extra features.                         #
# *******************************************************************************#

import os

import ee
import folium
from box import Box
from folium import plugins


from branca.element import Figure, JavascriptLink, MacroElement
from folium.elements import JSCSSMixin
from folium.map import Layer
from jinja2 import Template

from .basemaps import xyz_to_folium
from .common import *
from .conversion import *
from .ee_tile_layers import *
from .legends import builtin_legends
from .osm import *
from .timelapse import *
from .plot import *
from . import examples


if not in_colab_shell():
    from .plot import *


basemaps = Box(xyz_to_folium(), frozen_box=True)


class Map(folium.Map):
    """The Map class inherits from folium.Map. By default, the Map will add Google Maps as the basemap. Set add_google_map = False to use OpenStreetMap as the basemap.

    Returns:
        object: folium map object.
    """

    def __init__(self, **kwargs):
        import logging

        logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)

        if "ee_initialize" not in kwargs.keys():
            kwargs["ee_initialize"] = True

        if kwargs["ee_initialize"]:
            ee_initialize()

        # Default map center location and zoom level
        latlon = [20, 0]
        zoom = 2

        # Interchangeable parameters between ipyleaflet and folium
        if "center" in kwargs.keys():
            kwargs["location"] = kwargs["center"]
            kwargs.pop("center")
        if "location" in kwargs.keys():
            latlon = kwargs["location"]
        else:
            kwargs["location"] = latlon

        if "zoom" in kwargs.keys():
            kwargs["zoom_start"] = kwargs["zoom"]
            kwargs.pop("zoom")
        if "zoom_start" in kwargs.keys():
            zoom = kwargs["zoom_start"]
        else:
            kwargs["zoom_start"] = zoom
        if "max_zoom" not in kwargs.keys():
            kwargs["max_zoom"] = 30

        if "add_google_map" not in kwargs.keys() and "basemap" not in kwargs.keys():
            kwargs["add_google_map"] = False
        if "plugin_LatLngPopup" not in kwargs.keys():
            kwargs["plugin_LatLngPopup"] = False
        if "plugin_Fullscreen" not in kwargs.keys():
            kwargs["plugin_Fullscreen"] = True
        if "plugin_Draw" not in kwargs.keys():
            kwargs["plugin_Draw"] = True
        if "Draw_export" not in kwargs.keys():
            kwargs["Draw_export"] = False
        if "plugin_MiniMap" not in kwargs.keys():
            kwargs["plugin_MiniMap"] = False
        # if "plugin_LayerControl" not in kwargs.keys():
        #     kwargs["plugin_LayerControl"] = False
        if "locate_control" not in kwargs:
            kwargs["locate_control"] = False
        if "search_control" not in kwargs:
            kwargs["search_control"] = True
        if "scale_control" in kwargs:
            kwargs["scale"] = kwargs["scale_control"]
            kwargs.pop("scale_control")

        if (
            "width" in kwargs
            and isinstance(kwargs["width"], str)
            and ("%" not in kwargs["width"])
        ):
            kwargs["width"] = float(kwargs["width"].replace("px", ""))

        height = None
        width = None

        if "height" in kwargs:
            height = kwargs.pop("height")
        else:
            height = 600

        if "width" in kwargs:
            width = kwargs.pop("width")
        else:
            width = "100%"

        super().__init__(**kwargs)
        self.baseclass = "folium"

        # The list of Earth Engine Geometry objects converted from geojson
        self.draw_features = []
        # The Earth Engine Geometry object converted from the last drawn feature
        self.draw_last_feature = None
        self.draw_layer = None
        self.user_roi = None
        self.user_rois = None
        self.search_locations = None
        self.search_loc_marker = None
        self.search_loc_geom = None

        if (height is not None) or (width is not None):
            f = folium.Figure(width=width, height=height)
            self.add_to(f)

        if kwargs.get("add_google_map"):
            basemaps["ROADMAP"].add_to(self)
        if kwargs.get("basemap"):
            basemaps[kwargs.get("basemap")].add_to(self)
        if kwargs.get("plugin_LatLngPopup"):
            folium.LatLngPopup().add_to(self)
        if kwargs.get("plugin_Fullscreen"):
            plugins.Fullscreen().add_to(self)
        if kwargs.get("plugin_Draw"):
            plugins.Draw(export=kwargs.get("Draw_export")).add_to(self)
        if kwargs.get("plugin_MiniMap"):
            plugins.MiniMap().add_to(self)
        if kwargs.get("plugin_LayerControl"):
            folium.LayerControl().add_to(self)
        if kwargs["locate_control"]:
            plugins.LocateControl().add_to(self)
        if kwargs["search_control"]:
            plugins.Geocoder(collapsed=True, position="topleft").add_to(self)

        if "plugin_LayerControl" not in kwargs:
            self.options["layersControl"] = True
        else:
            self.options["layersControl"] = kwargs["plugin_LayerControl"]

        self.fit_bounds([latlon, latlon], max_zoom=zoom)

    def setOptions(self, mapTypeId="HYBRID", styles={}, types=[]):
        """Adds Google basemap to the map.

        Args:
            mapTypeId (str, optional): A mapTypeId to set the basemap to. Can be one of "ROADMAP", "SATELLITE", "HYBRID" or "TERRAIN" to select one of the standard Google Maps API map types. Defaults to 'HYBRID'.
            styles ([type], optional): A dictionary of custom MapTypeStyle objects keyed with a name that will appear in the map's Map Type Controls. Defaults to None.
            types ([type], optional): A list of mapTypeIds to make available. If omitted, but opt_styles is specified, appends all of the style keys to the standard Google Maps API map types.. Defaults to None.
        """
        try:
            basemaps[mapTypeId].add_to(self)
        except Exception:
            raise Exception(
                "Basemap can only be one of the following: {}".format(
                    ", ".join(basemaps.keys())
                )
            )

    set_options = setOptions

    def add_basemap(
        self, basemap: Optional[str] = "HYBRID", show: Optional[bool] = True, **kwargs
    ):
        """Adds a basemap to the map.

        Args:
            basemap (str, optional): Can be one of string from ee_basemaps. Defaults to 'ROADMAP'.
        """
        import xyzservices

        try:
            map_dict = {
                "ROADMAP": "Esri.WorldStreetMap",
                "SATELLITE": "Esri.WorldImagery",
                "TERRAIN": "Esri.WorldTopoMap",
                "HYBRID": "Esri.WorldImagery",
            }

            if isinstance(basemap, str):
                if basemap.upper() in map_dict:
                    if basemap in os.environ:
                        if "name" in kwargs:
                            kwargs["name"] = basemap
                        basemap = os.environ[basemap]
                        self.add_tile_layer(tiles=basemap, **kwargs)

                    else:
                        basemap = basemap.upper()
                        basemaps[basemap].add_to(self)

                elif isinstance(basemap, xyzservices.TileProvider):
                    name = basemap.name
                    url = basemap.build_url()
                    attribution = basemap.attribution
                    if "max_zoom" in basemap.keys():
                        max_zoom = basemap["max_zoom"]
                    else:
                        max_zoom = 22
                    layer = folium.TileLayer(
                        tiles=url,
                        attr=attribution,
                        name=name,
                        max_zoom=max_zoom,
                        overlay=True,
                        control=True,
                        show=show,
                        **kwargs,
                    )

                    self.add_layer(layer)

                    arc_add_layer(url, name)

                elif basemap in basemaps:
                    bmap = basemaps[basemap]
                    bmap.show = show
                    bmap.add_to(self)
                    if isinstance(basemaps[basemap], folium.TileLayer):
                        url = basemaps[basemap].tiles
                    elif isinstance(basemaps[basemap], folium.WmsTileLayer):
                        url = basemaps[basemap].url
                    arc_add_layer(url, basemap)
                else:
                    print(
                        "Basemap can only be one of the following: {}".format(
                            ", ".join(basemaps.keys())
                        )
                    )

        except Exception:
            raise Exception(
                "Basemap can only be one of the following: {}".format(
                    ", ".join(basemaps.keys())
                )
            )

    def add_layer(
        self,
        ee_object,
        vis_params={},
        name="Layer untitled",
        shown=True,
        opacity=1.0,
        **kwargs,
    ):
        """Adds a given EE object to the map as a layer.

        Args:
            ee_object (Collection|Feature|Image|MapId): The object to add to the map.
            vis_params (dict, optional): The visualization parameters. Defaults to {}.
            name (str, optional): The name of the layer. Defaults to 'Layer untitled'.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            opacity (float, optional): The layer's opacity represented as a number between 0 and 1. Defaults to 1.
        """

        layer = EEFoliumTileLayer(ee_object, vis_params, name, shown, opacity, **kwargs)
        layer.add_to(self)
        arc_add_layer(layer.url_format, name, shown, opacity)

    addLayer = add_layer

    def _repr_mimebundle_(self, **kwargs):
        """Adds Layer control to the map. Reference: https://ipython.readthedocs.io/en/stable/config/integrating.html#MyObject._repr_mimebundle_"""
        if self.options["layersControl"]:
            self.add_layer_control()

    def set_center(self, lon, lat, zoom=10):
        """Centers the map view at a given coordinates with the given zoom level.

        Args:
            lon (float): The longitude of the center, in degrees.
            lat (float): The latitude of the center, in degrees.
            zoom (int, optional): The zoom level, from 1 to 24. Defaults to 10.
        """
        self.fit_bounds([[lat, lon], [lat, lon]], max_zoom=zoom)

        if is_arcpy():
            arc_zoom_to_extent(lon, lat, lon, lat)

    setCenter = set_center

    def zoom_to_bounds(self, bounds):
        """Zooms to a bounding box in the form of [minx, miny, maxx, maxy].

        Args:
            bounds (list | tuple): A list/tuple containing minx, miny, maxx, maxy values for the bounds.
        """
        #  The folium fit_bounds method takes lat/lon bounds in the form [[south, west], [north, east]].
        self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    def zoom_to_gdf(self, gdf):
        """Zooms to the bounding box of a GeoPandas GeoDataFrame.

        Args:
            gdf (GeoDataFrame): A GeoPandas GeoDataFrame.
        """
        bounds = gdf.total_bounds
        self.zoom_to_bounds(bounds)

    def center_object(self, ee_object, zoom=None):
        """Centers the map view on a given object.

        Args:
            ee_object (Element|Geometry): An Earth Engine object to center on a geometry, image or feature.
            zoom (int, optional): The zoom level, from 1 to 24. Defaults to None.
        """

        maxError = 0.001
        if isinstance(ee_object, ee.Geometry):
            geometry = ee_object.transform(maxError=maxError)
        else:
            try:
                geometry = ee_object.geometry(maxError=maxError).transform(
                    maxError=maxError
                )
            except Exception:
                raise Exception(
                    "ee_object must be an instance of one of ee.Geometry, ee.FeatureCollection, ee.Image, or ee.ImageCollection."
                )

        if zoom is not None:
            if not isinstance(zoom, int):
                raise Exception("Zoom must be an integer.")
            else:
                centroid = geometry.centroid(maxError=maxError).getInfo()["coordinates"]
                lat = centroid[1]
                lon = centroid[0]
                self.set_center(lon, lat, zoom)

                if is_arcpy():
                    arc_zoom_to_extent(lon, lat, lon, lat)

        else:
            coordinates = geometry.bounds(maxError).getInfo()["coordinates"][0]
            x = [c[0] for c in coordinates]
            y = [c[1] for c in coordinates]
            xmin = min(x)
            xmax = max(x)
            ymin = min(y)
            ymax = max(y)
            bounds = [[ymin, xmin], [ymax, xmax]]
            self.fit_bounds(bounds)

            if is_arcpy():
                arc_zoom_to_extent(xmin, ymin, xmax, ymax)

    centerObject = center_object

    def set_control_visibility(
        self, layerControl=True, fullscreenControl=True, latLngPopup=True
    ):
        """Sets the visibility of the controls on the map.

        Args:
            layerControl (bool, optional): Whether to show the control that allows the user to toggle layers on/off. Defaults to True.
            fullscreenControl (bool, optional): Whether to show the control that allows the user to make the map full-screen. Defaults to True.
            latLngPopup (bool, optional): Whether to show the control that pops up the Lat/lon when the user clicks on the map. Defaults to True.
        """
        if layerControl:
            folium.LayerControl().add_to(self)
        if fullscreenControl:
            plugins.Fullscreen().add_to(self)
        if latLngPopup:
            folium.LatLngPopup().add_to(self)

    setControlVisibility = set_control_visibility

    def add_layer_control(self):
        """Adds layer control to the map."""
        layer_ctrl = False
        for item in self.to_dict()["children"]:
            if item.startswith("layer_control"):
                layer_ctrl = True
                break
        if not layer_ctrl:
            folium.LayerControl().add_to(self)

    addLayerControl = add_layer_control

    def add_marker(
        self, location, popup=None, tooltip=None, icon=None, draggable=False, **kwargs
    ):
        """Adds a marker to the map. More info about marker options at https://python-visualization.github.io/folium/modules.html#folium.map.Marker.

        Args:
            location (list | tuple): The location of the marker in the format of [lat, lng].
            popup (str, optional): The popup text. Defaults to None.
            tooltip (str, optional): The tooltip text. Defaults to None.
            icon (str, optional): The icon to use. Defaults to None.
            draggable (bool, optional): Whether the marker is draggable. Defaults to False.
        """
        if isinstance(location, list):
            location = tuple(location)
        if isinstance(location, tuple):
            folium.Marker(
                location=location,
                popup=popup,
                tooltip=tooltip,
                icon=icon,
                draggable=draggable,
                **kwargs,
            ).add_to(self)

        else:
            raise TypeError("The location must be a list or a tuple.")

    def add_wms_layer(
        self,
        url,
        layers,
        name=None,
        attribution="",
        overlay=True,
        control=True,
        shown=True,
        format="image/png",
        transparent=True,
        version="1.1.1",
        styles="",
        **kwargs,
    ):
        """Add a WMS layer to the map.

        Args:
            url (str): The URL of the WMS web service.
            layers (str): Comma-separated list of WMS layers to show.
            name (str, optional): The layer name to use on the layer control. Defaults to None.
            attribution (str, optional): The attribution of the data layer. Defaults to ''.
            overlay (str, optional): Allows overlay. Defaults to True.
            control (str, optional): Adds the layer to the layer control. Defaults to True.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            format (str, optional): WMS image format (use ‘image/png’ for layers with transparency). Defaults to 'image/png'.
            transparent (bool, optional): Whether the layer shall allow transparency. Defaults to True.
            version (str, optional): Version of the WMS service to use. Defaults to "1.1.1".
            styles (str, optional): Comma-separated list of WMS styles. Defaults to "".
        """
        try:
            folium.raster_layers.WmsTileLayer(
                url=url,
                layers=layers,
                name=name,
                attr=attribution,
                overlay=overlay,
                control=control,
                show=shown,
                styles=styles,
                fmt=format,
                transparent=transparent,
                version=version,
                **kwargs,
            ).add_to(self)
        except Exception:
            raise Exception("Failed to add the specified WMS TileLayer.")

    def add_tile_layer(
        self,
        tiles="OpenStreetMap",
        name="Untitled",
        attribution=".",
        overlay=True,
        control=True,
        shown=True,
        opacity=1.0,
        API_key=None,
        **kwargs,
    ):
        """Add a XYZ tile layer to the map.

        Args:
            tiles (str): The URL of the XYZ tile service.
            name (str, optional): The layer name to use on the layer control. Defaults to 'Untitled'.
            attribution (str, optional): The attribution of the data layer. Defaults to '.'.
            overlay (str, optional): Allows overlay. Defaults to True.
            control (str, optional): Adds the layer to the layer control. Defaults to True.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            opacity (float, optional): Sets the opacity for the layer.
            API_key (str, optional): – API key for Cloudmade or Mapbox tiles. Defaults to True.
        """

        if "max_zoom" not in kwargs:
            kwargs["max_zoom"] = 100
        if "max_native_zoom" not in kwargs:
            kwargs["max_native_zoom"] = 100

        try:
            folium.raster_layers.TileLayer(
                tiles=tiles,
                name=name,
                attr=attribution,
                overlay=overlay,
                control=control,
                show=shown,
                opacity=opacity,
                API_key=API_key,
                **kwargs,
            ).add_to(self)
        except Exception:
            raise Exception("Failed to add the specified TileLayer.")

    def add_cog_layer(
        self,
        url,
        name="Untitled",
        attribution=".",
        opacity=1.0,
        shown=True,
        bands=None,
        titiler_endpoint=None,
        **kwargs,
    ):
        """Adds a COG TileLayer to the map.

        Args:
            url (str): The URL of the COG tile layer.
            name (str, optional): The layer name to use for the layer. Defaults to 'Untitled'.
            attribution (str, optional): The attribution to use. Defaults to '.'.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            bands (list, optional): A list of bands to use. Defaults to None.
            titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
        """
        tile_url = cog_tile(url, bands, titiler_endpoint, **kwargs)
        bounds = cog_bounds(url, titiler_endpoint)
        self.add_tile_layer(
            tiles=tile_url,
            name=name,
            attribution=attribution,
            opacity=opacity,
            shown=shown,
        )
        self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    def add_cog_mosaic(self, **kwargs):
        raise NotImplementedError(
            "This function is no longer supported.See https://github.com/giswqs/leafmap/issues/180."
        )

    def add_stac_layer(
        self,
        url=None,
        collection=None,
        item=None,
        assets=None,
        bands=None,
        titiler_endpoint=None,
        name="STAC Layer",
        attribution=".",
        opacity=1.0,
        shown=True,
        **kwargs,
    ):
        """Adds a STAC TileLayer to the map.

        Args:
            url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
            collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
            item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
            assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
            bands (list): A list of band names, e.g., ["SR_B7", "SR_B5", "SR_B4"]
            titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.
            name (str, optional): The layer name to use for the layer. Defaults to 'STAC Layer'.
            attribution (str, optional): The attribution to use. Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
        """
        tile_url = stac_tile(
            url, collection, item, assets, bands, titiler_endpoint, **kwargs
        )
        bounds = stac_bounds(url, collection, item, titiler_endpoint)
        self.add_tile_layer(
            url=tile_url,
            name=name,
            attribution=attribution,
            opacity=opacity,
            shown=shown,
        )
        self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    def add_raster(
        self,
        source: str,
        indexes: Optional[int] = None,
        colormap: Optional[str] = None,
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
        nodata: Optional[float] = None,
        attribution: Optional[str] = None,
        layer_name: Optional[str] = "Raster",
        array_args: Optional[Dict] = {},
        **kwargs,
    ):
        """Add a local raster dataset to the map.
            If you are using this function in JupyterHub on a remote server (e.g., Binder, Microsoft Planetary Computer) and
            if the raster does not render properly, try installing jupyter-server-proxy using `pip install jupyter-server-proxy`,
            then running the following code before calling this function. For more info, see https://bit.ly/3JbmF93.

            import os
            os.environ['LOCALTILESERVER_CLIENT_PREFIX'] = 'proxy/{port}'

        Args:
            source (str): The path to the GeoTIFF file or the URL of the Cloud Optimized GeoTIFF.
            indexes (int, optional): The band(s) to use. Band indexing starts at 1. Defaults to None.
            colormap (str, optional): The name of the colormap from `matplotlib` to use when plotting a single band. See https://matplotlib.org/stable/gallery/color/colormap_reference.html. Default is greyscale.
            vmin (float, optional): The minimum value to use when colormapping the colormap when plotting a single band. Defaults to None.
            vmax (float, optional): The maximum value to use when colormapping the colormap when plotting a single band. Defaults to None.
            nodata (float, optional): The value from the band to use to interpret as not valid data. Defaults to None.
            attribution (str, optional): Attribution for the source raster. This defaults to a message about it being a local file.. Defaults to None.
            layer_name (str, optional): The layer name to use. Defaults to 'Raster'.
            array_args (dict, optional): Additional arguments to pass to `array_to_image`. Defaults to {}.
        """

        import numpy as np
        import xarray as xr

        if isinstance(source, np.ndarray) or isinstance(source, xr.DataArray):
            source = array_to_image(source, **array_args)

        tile_layer, tile_client = get_local_tile_layer(
            source,
            indexes=indexes,
            colormap=colormap,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            attribution=attribution,
            tile_format="folium",
            layer_name=layer_name,
            return_client=True,
            **kwargs,
        )
        tile_layer.add_to(self)

        bounds = tile_client.bounds()  # [ymin, ymax, xmin, xmax]
        bounds = (
            bounds[2],
            bounds[0],
            bounds[3],
            bounds[1],
        )  # [minx, miny, maxx, maxy]
        self.zoom_to_bounds(bounds)

        arc_add_layer(tile_layer.tiles, layer_name, True, 1.0)
        arc_zoom_to_extent(bounds[0], bounds[1], bounds[2], bounds[3])

    def add_remote_tile(
        self,
        source,
        band=None,
        palette=None,
        vmin=None,
        vmax=None,
        nodata=None,
        attribution=None,
        layer_name=None,
        **kwargs,
    ):
        """Add a remote Cloud Optimized GeoTIFF (COG) to the map.

        Args:
            source (str): The path to the remote Cloud Optimized GeoTIFF.
            band (int, optional): The band to use. Band indexing starts at 1. Defaults to None.
            palette (str, optional): The name of the color palette from `palettable` to use when plotting a single band. See https://jiffyclub.github.io/palettable. Default is greyscale
            vmin (float, optional): The minimum value to use when colormapping the palette when plotting a single band. Defaults to None.
            vmax (float, optional): The maximum value to use when colormapping the palette when plotting a single band. Defaults to None.
            nodata (float, optional): The value from the band to use to interpret as not valid data. Defaults to None.
            attribution (str, optional): Attribution for the source raster. This defaults to a message about it being a local file.. Defaults to None.
            layer_name (str, optional): The layer name to use. Defaults to None.
        """
        if isinstance(source, str) and source.startswith("http"):
            self.add_raster(
                source,
                band=band,
                palette=palette,
                vmin=vmin,
                vmax=vmax,
                nodata=nodata,
                attribution=attribution,
                layer_name=layer_name,
                **kwargs,
            )
        else:
            raise Exception("The source must be a URL.")

    def add_heatmap(
        self,
        data,
        latitude="latitude",
        longitude="longitude",
        value="value",
        name="Heat map",
        radius=25,
        **kwargs,
    ):
        """Adds a heat map to the map. Reference: https://stackoverflow.com/a/54756617

        Args:
            data (str | list | pd.DataFrame): File path or HTTP URL to the input file or a list of data points in the format of [[x1, y1, z1], [x2, y2, z2]]. For example, https://raw.githubusercontent.com/giswqs/leafmap/master/examples/data/world_cities.csv
            latitude (str, optional): The column name of latitude. Defaults to "latitude".
            longitude (str, optional): The column name of longitude. Defaults to "longitude".
            value (str, optional): The column name of values. Defaults to "value".
            name (str, optional): Layer name to use. Defaults to "Heat map".
            radius (int, optional): Radius of each “point” of the heatmap. Defaults to 25.

        Raises:
            ValueError: If data is not a list.
        """
        import pandas as pd

        try:
            if isinstance(data, str):
                df = pd.read_csv(data)
                data = df[[latitude, longitude, value]].values.tolist()
            elif isinstance(data, pd.DataFrame):
                data = data[[latitude, longitude, value]].values.tolist()
            elif isinstance(data, list):
                pass
            else:
                raise ValueError("data must be a list, a DataFrame, or a file path.")

            plugins.HeatMap(data, name=name, radius=radius, **kwargs).add_to(
                folium.FeatureGroup(name=name).add_to(self)
            )
        except Exception as e:
            raise Exception(e)

    def add_legend(
        self,
        title="Legend",
        labels=None,
        colors=None,
        legend_dict=None,
        builtin_legend=None,
        opacity=1.0,
        position="bottomright",
        draggable=True,
        style={},
    ):
        """Adds a customized legend to the map. Reference: https://bit.ly/3oV6vnH.
            If you want to add multiple legends to the map, you need to set the `draggable` argument to False.

        Args:
            title (str, optional): Title of the legend. Defaults to 'Legend'. Defaults to "Legend".
            colors (list, optional): A list of legend colors. Defaults to None.
            labels (list, optional): A list of legend labels. Defaults to None.
            legend_dict (dict, optional): A dictionary containing legend items as keys and color as values.
                If provided, legend_keys and legend_colors will be ignored. Defaults to None.
            builtin_legend (str, optional): Name of the builtin legend to add to the map. Defaults to None.
            opacity (float, optional): The opacity of the legend. Defaults to 1.0.
            position (str, optional): The position of the legend, can be one of the following:
                "topleft", "topright", "bottomleft", "bottomright". Defaults to "bottomright".
            draggable (bool, optional): If True, the legend can be dragged to a new position. Defaults to True.
            style: Additional keyword arguments to style the legend, such as position, bottom, right, z-index,
                border, background-color, border-radius, padding, font-size, etc. The default style is:
                style = {
                    'position': 'fixed',
                    'z-index': '9999',
                    'border': '2px solid grey',
                    'background-color': 'rgba(255, 255, 255, 0.8)',
                    'border-radius': '5px',
                    'padding': '10px',
                    'font-size': '14px',
                    'bottom': '20px',
                    'right': '5px'
                }

        """
        content = create_legend(
            title,
            labels,
            colors,
            legend_dict,
            builtin_legend,
            opacity,
            position,
            draggable,
            style=style,
        )
        if draggable:
            from branca.element import Template, MacroElement

            content = (
                '"""\n{% macro html(this, kwargs) %}\n'
                + content
                + '\n{% endmacro %}"""'
            )

            macro = MacroElement()
            macro._template = Template(content)

            self.get_root().add_child(macro)
        else:
            self.add_html(content, position=position)

    def add_colorbar(
        self,
        vis_params,
        index=None,
        label="",
        categorical=False,
        step=None,
        background_color=None,
        **kwargs,
    ):
        """Add a colorbar to the map.

        Args:
            colors (list): The set of colors to be used for interpolation. Colors can be provided in the form: * tuples of RGBA ints between 0 and 255 (e.g: (255, 255, 0) or (255, 255, 0, 255)) * tuples of RGBA floats between 0. and 1. (e.g: (1.,1.,0.) or (1., 1., 0., 1.)) * HTML-like string (e.g: “#ffff00) * a color name or shortcut (e.g: “y” or “yellow”)
            vmin (int, optional): The minimal value for the colormap. Values lower than vmin will be bound directly to colors[0].. Defaults to 0.
            vmax (float, optional): The maximal value for the colormap. Values higher than vmax will be bound directly to colors[-1]. Defaults to 1.0.
            index (list, optional):The values corresponding to each color. It has to be sorted, and have the same length as colors. If None, a regular grid between vmin and vmax is created.. Defaults to None.
            label (str, optional): The caption for the colormap. Defaults to "".
            categorical (bool, optional): Whether or not to create a categorical colormap. Defaults to False.
            step (int, optional): The step to split the LinearColormap into a StepColormap. Defaults to None.
        """
        from box import Box
        from branca.colormap import LinearColormap

        if not isinstance(vis_params, dict):
            raise ValueError("vis_params must be a dictionary.")

        if "palette" not in vis_params:
            raise ValueError("vis_params must contain a palette.")

        if "min" not in vis_params:
            vis_params["min"] = 0
        if "max" not in vis_params:
            vis_params["max"] = 1

        colors = to_hex_colors(check_cmap(vis_params["palette"]))
        vmin = vis_params["min"]
        vmax = vis_params["max"]

        if isinstance(colors, Box):
            try:
                colors = list(colors["default"])
            except Exception as e:
                print("The provided color list is invalid.")
                raise Exception(e)

        if all(len(color) == 6 for color in colors):
            colors = ["#" + color for color in colors]

        colormap = LinearColormap(
            colors=colors, index=index, vmin=vmin, vmax=vmax, caption=label
        )

        if categorical:
            if step is not None:
                colormap = colormap.to_step(step)
            elif index is not None:
                colormap = colormap.to_step(len(index) - 1)
            else:
                colormap = colormap.to_step(3)

        if background_color is not None:
            svg_style = (
                "<style>svg {background-color: " + background_color + ";}</style>"
            )

            self.get_root().header.add_child(folium.Element(svg_style))

        self.add_child(colormap)

    add_colorbar_branca = add_colorbar

    def add_colormap(
        self,
        width=4.0,
        height=0.3,
        vmin=0,
        vmax=1.0,
        palette=None,
        vis_params=None,
        cmap="gray",
        discrete=False,
        label=None,
        label_size=10,
        label_weight="normal",
        tick_size=8,
        bg_color="white",
        orientation="horizontal",
        dpi="figure",
        transparent=False,
        position=(70, 5),
        **kwargs,
    ):
        """Add a colorbar to the map. Under the hood, it uses matplotlib to generate the colorbar, save it as a png file, and add it to the map using m.add_image().

        Args:
            width (float): Width of the colorbar in inches. Default is 4.0.
            height (float): Height of the colorbar in inches. Default is 0.3.
            vmin (float): Minimum value of the colorbar. Default is 0.
            vmax (float): Maximum value of the colorbar. Default is 1.0.
            palette (list): List of colors to use for the colorbar. It can also be a cmap name, such as ndvi, ndwi, dem, coolwarm. Default is None.
            vis_params (dict): Visualization parameters as a dictionary. See https://developers.google.com/earth-engine/guides/image_visualization for options.
            cmap (str, optional): Matplotlib colormap. Defaults to "gray". See https://matplotlib.org/3.3.4/tutorials/colors/colormaps.html#sphx-glr-tutorials-colors-colormaps-py for options.
            discrete (bool, optional): Whether to create a discrete colorbar. Defaults to False.
            label (str, optional): Label for the colorbar. Defaults to None.
            label_size (int, optional): Font size for the colorbar label. Defaults to 12.
            label_weight (str, optional): Font weight for the colorbar label, can be "normal", "bold", etc. Defaults to "normal".
            tick_size (int, optional): Font size for the colorbar tick labels. Defaults to 10.
            bg_color (str, optional): Background color for the colorbar. Defaults to "white".
            orientation (str, optional): Orientation of the colorbar, such as "vertical" and "horizontal". Defaults to "horizontal".
            dpi (float | str, optional): The resolution in dots per inch.  If 'figure', use the figure's dpi value. Defaults to "figure".
            transparent (bool, optional): Whether to make the background transparent. Defaults to False.
            position (tuple, optional): The position of the colormap in the format of (x, y),
                the percentage ranging from 0 to 100, starting from the lower-left corner. Defaults to (0, 0).
            **kwargs: Other keyword arguments to pass to matplotlib.pyplot.savefig().

        Returns:
            str: Path to the output image.
        """

        colorbar = save_colorbar(
            None,
            width,
            height,
            vmin,
            vmax,
            palette,
            vis_params,
            cmap,
            discrete,
            label,
            label_size,
            label_weight,
            tick_size,
            bg_color,
            orientation,
            dpi,
            transparent,
            show_colorbar=False,
            **kwargs,
        )

        self.add_image(colorbar, position=position)

    def add_styled_vector(
        self,
        ee_object,
        column,
        palette,
        layer_name="Untitled",
        shown=True,
        opacity=1.0,
        **kwargs,
    ):
        """Adds a styled vector to the map.

        Args:
            ee_object (object): An ee.FeatureCollection.
            column (str): The column name to use for styling.
            palette (list | dict): The palette (e.g., list of colors or a dict containing label and color pairs) to use for styling.
            layer_name (str, optional): The name to be used for the new layer. Defaults to "Untitled".
        """
        styled_vector = vector_styling(ee_object, column, palette, **kwargs)
        self.addLayer(
            styled_vector.style(**{"styleProperty": "style"}),
            {},
            layer_name,
            shown,
            opacity,
        )

    def add_shapefile(self, in_shp, layer_name="Untitled", **kwargs):
        """Adds a shapefile to the map. See https://python-visualization.github.io/folium/modules.html#folium.features.GeoJson for more info about setting style.

        Args:
            in_shp (str): The input file path to the shapefile.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".

        Raises:
            FileNotFoundError: The provided shapefile could not be found.
        """
        in_shp = os.path.abspath(in_shp)
        if not os.path.exists(in_shp):
            raise FileNotFoundError("The provided shapefile could not be found.")

        data = shp_to_geojson(in_shp)

        geo_json = folium.GeoJson(data=data, name=layer_name, **kwargs)
        geo_json.add_to(self)

    def add_geojson(
        self,
        in_geojson,
        layer_name="Untitled",
        encoding="utf-8",
        info_mode="on_hover",
        fields=None,
        **kwargs,
    ):
        """Adds a GeoJSON file to the map.

        Args:
            in_geojson (str): The input file path to the GeoJSON.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".
            encoding (str, optional): The encoding of the GeoJSON file. Defaults to "utf-8".
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            fields (list, optional): The fields to be displayed in the popup. Defaults to None.

        Raises:
            FileNotFoundError: The provided GeoJSON file could not be found.
        """
        import json
        import requests
        import random

        try:
            if isinstance(in_geojson, str):
                if in_geojson.startswith("http"):
                    in_geojson = github_raw_url(in_geojson)
                    data = requests.get(in_geojson).json()
                else:
                    in_geojson = os.path.abspath(in_geojson)
                    if not os.path.exists(in_geojson):
                        raise FileNotFoundError(
                            "The provided GeoJSON file could not be found."
                        )

                    with open(in_geojson, encoding=encoding) as f:
                        data = json.load(f)
            elif isinstance(in_geojson, dict):
                data = in_geojson
            else:
                raise TypeError("The input geojson must be a type of str or dict.")
        except Exception as e:
            raise Exception(e)

        # interchangeable parameters between ipyleaflet and folium.
        if "style_function" not in kwargs:
            if "style" in kwargs:
                style_dict = kwargs["style"]
                if isinstance(kwargs["style"], dict) and len(kwargs["style"]) > 0:
                    kwargs["style_function"] = lambda x: style_dict
                kwargs.pop("style")
            else:
                style_dict = {
                    # "stroke": True,
                    "color": "#000000",
                    "weight": 1,
                    "opacity": 1,
                    # "fill": True,
                    # "fillColor": "#ffffff",
                    "fillOpacity": 0.1,
                    # "dashArray": "9"
                    # "clickable": True,
                }
                kwargs["style_function"] = lambda x: style_dict

        if "style_callback" in kwargs:
            kwargs.pop("style_callback")

        if "hover_style" in kwargs:
            kwargs.pop("hover_style")

        if "fill_colors" in kwargs:
            fill_colors = kwargs["fill_colors"]

            def random_color(feature):
                style_dict["fillColor"] = random.choice(fill_colors)
                return style_dict

            kwargs["style_function"] = random_color
            kwargs.pop("fill_colors")

        if "highlight_function" not in kwargs:
            kwargs["highlight_function"] = lambda feat: {
                "weight": 2,
                "fillOpacity": 0.5,
            }

        tooltip = None
        popup = None
        if info_mode is not None:
            if fields is None:
                fields = list(data["features"][0]["properties"].keys())
            if info_mode == "on_hover":
                tooltip = folium.GeoJsonTooltip(fields=fields)
            elif info_mode == "on_click":
                popup = folium.GeoJsonPopup(fields=fields)

        geojson = folium.GeoJson(
            data=data, name=layer_name, tooltip=tooltip, popup=popup, **kwargs
        )
        geojson.add_to(self)

    def add_kml(
        self, in_kml, layer_name="Untitled", info_mode="on_hover", fields=None, **kwargs
    ):
        """Adds a KML file to the map.

        Args:
            in_kml (str): The input file path to the KML.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".
            info_mode (str, optional): Displays the attributes by either on_hover or on_click.
                Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            fields (list, optional): The fields to be displayed in the popup. Defaults to None.

        Raises:
            FileNotFoundError: The provided KML file could not be found.
        """

        if in_kml.startswith("http") and in_kml.endswith(".kml"):
            out_dir = os.path.abspath("./cache")
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            download_from_url(in_kml, out_dir=out_dir, unzip=False, verbose=False)
            in_kml = os.path.join(out_dir, os.path.basename(in_kml))
            if not os.path.exists(in_kml):
                raise FileNotFoundError("The downloaded kml file could not be found.")
        else:
            in_kml = os.path.abspath(in_kml)
            if not os.path.exists(in_kml):
                raise FileNotFoundError("The provided KML could not be found.")

        data = kml_to_geojson(in_kml)

        self.add_geojson(
            data, layer_name=layer_name, info_mode=info_mode, fields=fields, **kwargs
        )

    def add_gdf(
        self,
        gdf,
        layer_name="Untitled",
        zoom_to_layer=True,
        info_mode="on_hover",
        fields=None,
        **kwargs,
    ):
        """Adds a GeoPandas GeoDataFrame to the map.

        Args:
            gdf (GeoDataFrame): A GeoPandas GeoDataFrame.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".
            zoom_to_layer (bool, optional): Whether to zoom to the layer.
            info_mode (str, optional): Displays the attributes by either on_hover or on_click.
                Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            fields (list, optional): The fields to be displayed in the popup. Defaults to None.

        """

        data = gdf_to_geojson(gdf, epsg="4326")

        self.add_geojson(
            data, layer_name=layer_name, info_mode=info_mode, fields=fields, **kwargs
        )

        if zoom_to_layer:
            import numpy as np

            bounds = gdf.to_crs(epsg="4326").bounds
            west = np.min(bounds["minx"])
            south = np.min(bounds["miny"])
            east = np.max(bounds["maxx"])
            north = np.max(bounds["maxy"])
            self.fit_bounds([[south, east], [north, west]])

    def add_gdf_from_postgis(
        self, sql, con, layer_name="Untitled", zoom_to_layer=True, **kwargs
    ):
        """Adds a GeoPandas GeoDataFrameto the map.

        Args:
            sql (str): SQL query to execute in selecting entries from database, or name of the table to read from the database.
            con (sqlalchemy.engine.Engine): Active connection to the database to query.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".
            zoom_to_layer (bool, optional): Whether to zoom to the layer.

        """
        if "fill_colors" in kwargs:
            kwargs.pop("fill_colors")
        gdf = read_postgis(sql, con, **kwargs)
        data = gdf_to_geojson(gdf, epsg="4326")

        self.add_geojson(data, layer_name=layer_name, **kwargs)

        if zoom_to_layer:
            import numpy as np

            bounds = gdf.to_crs(epsg="4326").bounds
            west = np.min(bounds["minx"])
            south = np.min(bounds["miny"])
            east = np.max(bounds["maxx"])
            north = np.max(bounds["maxy"])
            self.fit_bounds([[south, east], [north, west]])

    def add_osm(
        self,
        query,
        layer_name="Untitled",
        which_result=None,
        by_osmid=False,
        buffer_dist=None,
        to_ee=False,
        geodesic=True,
        **kwargs,
    ):
        """Adds OSM data to the map.

        Args:
            query (str | dict | list): Query string(s) or structured dict(s) to geocode.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            which_result (INT, optional): Which geocoding result to use. if None, auto-select the first (Multi)Polygon or raise an error if OSM doesn't return one. to get the top match regardless of geometry type, set which_result=1. Defaults to None.
            by_osmid (bool, optional): If True, handle query as an OSM ID for lookup rather than text search. Defaults to False.
            buffer_dist (float, optional): Distance to buffer around the place geometry, in meters. Defaults to None.
            to_ee (bool, optional): Whether to convert the csv to an ee.FeatureCollection.
            geodesic (bool, optional): Whether line segments should be interpreted as spherical geodesics. If false, indicates that line segments should be interpreted as planar lines in the specified CRS. If absent, defaults to true if the CRS is geographic (including the default EPSG:4326), or to false if the CRS is projected.

        """

        gdf = osm_to_gdf(
            query, which_result=which_result, by_osmid=by_osmid, buffer_dist=buffer_dist
        )
        geojson = gdf.__geo_interface__

        if to_ee:
            fc = geojson_to_ee(geojson, geodesic=geodesic)
            self.addLayer(fc, {}, layer_name)
            self.centerObject(fc)
        else:
            self.add_geojson(geojson, layer_name=layer_name, **kwargs)
            bounds = gdf.bounds.iloc[0]
            self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    def add_osm_from_geocode(
        self,
        query,
        which_result=None,
        by_osmid=False,
        buffer_dist=None,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
    ):
        """Adds OSM data of place(s) by name or ID to the map.

        Args:
            query (str | dict | list): Query string(s) or structured dict(s) to geocode.
            which_result (int, optional): Which geocoding result to use. if None, auto-select the first (Multi)Polygon or raise an error if OSM doesn't return one. to get the top match regardless of geometry type, set which_result=1. Defaults to None.
            by_osmid (bool, optional): If True, handle query as an OSM ID for lookup rather than text search. Defaults to False.
            buffer_dist (float, optional): Distance to buffer around the place geometry, in meters. Defaults to None.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

        """

        gdf = osm_gdf_from_geocode(
            query, which_result=which_result, by_osmid=by_osmid, buffer_dist=buffer_dist
        )
        geojson = gdf.__geo_interface__

        self.add_geojson(
            geojson,
            layer_name=layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            info_mode=info_mode,
        )
        self.zoom_to_gdf(gdf)

    def add_osm_from_address(
        self,
        address,
        tags,
        dist=1000,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
    ):
        """Adds OSM entities within some distance N, S, E, W of address to the map.

        Args:
            address (str): The address to geocode and use as the central point around which to get the geometries.
            tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
            dist (int, optional): Distance in meters. Defaults to 1000.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

        """
        gdf = osm_gdf_from_address(address, tags, dist)
        geojson = gdf.__geo_interface__

        self.add_geojson(
            geojson,
            layer_name=layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            info_mode=info_mode,
        )
        self.zoom_to_gdf(gdf)

    def add_osm_from_place(
        self,
        query,
        tags,
        which_result=None,
        buffer_dist=None,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
    ):
        """Adds OSM entities within boundaries of geocodable place(s) to the map.

        Args:
            query (str | dict | list): Query string(s) or structured dict(s) to geocode.
            tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
            which_result (int, optional): Which geocoding result to use. if None, auto-select the first (Multi)Polygon or raise an error if OSM doesn't return one. to get the top match regardless of geometry type, set which_result=1. Defaults to None.
            buffer_dist (float, optional): Distance to buffer around the place geometry, in meters. Defaults to None.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

        """
        gdf = osm_gdf_from_place(query, tags, which_result, buffer_dist)
        geojson = gdf.__geo_interface__

        self.add_geojson(
            geojson,
            layer_name=layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            info_mode=info_mode,
        )
        self.zoom_to_gdf(gdf)

    def add_osm_from_point(
        self,
        center_point,
        tags,
        dist=1000,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
    ):
        """Adds OSM entities within some distance N, S, E, W of a point to the map.

        Args:
            center_point (tuple): The (lat, lng) center point around which to get the geometries.
            tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
            dist (int, optional): Distance in meters. Defaults to 1000.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

        """
        gdf = osm_gdf_from_point(center_point, tags, dist)
        geojson = gdf.__geo_interface__

        self.add_geojson(
            geojson,
            layer_name=layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            info_mode=info_mode,
        )
        self.zoom_to_gdf(gdf)

    def add_osm_from_polygon(
        self,
        polygon,
        tags,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
    ):
        """Adds OSM entities within boundaries of a (multi)polygon to the map.

        Args:
            polygon (shapely.geometry.Polygon | shapely.geometry.MultiPolygon): Geographic boundaries to fetch geometries within
            tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

        """
        gdf = osm_gdf_from_polygon(polygon, tags)
        geojson = gdf.__geo_interface__

        self.add_geojson(
            geojson,
            layer_name=layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            info_mode=info_mode,
        )
        self.zoom_to_gdf(gdf)

    def add_osm_from_bbox(
        self,
        north,
        south,
        east,
        west,
        tags,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
    ):
        """Adds OSM entities within a N, S, E, W bounding box to the map.


        Args:
            north (float): Northern latitude of bounding box.
            south (float): Southern latitude of bounding box.
            east (float): Eastern longitude of bounding box.
            west (float): Western longitude of bounding box.
            tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

        """
        gdf = osm_gdf_from_bbox(north, south, east, west, tags)
        geojson = gdf.__geo_interface__

        self.add_geojson(
            geojson,
            layer_name=layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            info_mode=info_mode,
        )
        self.zoom_to_gdf(gdf)

    def add_points_from_xy(
        self,
        data: Union[str, pd.DataFrame],
        x: Optional[str] = "longitude",
        y: Optional[str] = "latitude",
        popup: Optional[List] = None,
        min_width: Optional[int] = 100,
        max_width: Optional[int] = 200,
        layer_name: Optional[str] = "Marker Cluster",
        color_column: Optional[str] = None,
        marker_colors: Optional[List] = None,
        icon_colors: Optional[List] = ["white"],
        icon_names: Optional[List] = ["info"],
        angle: Optional[int] = 0,
        prefix: Optional[str] = "fa",
        add_legend: Optional[bool] = True,
        max_cluster_radius: Optional[int] = 80,
        **kwargs,
    ):
        """Adds a marker cluster to the map.

        Args:
            data (str | pd.DataFrame): A csv or Pandas DataFrame containing x, y, z values.
            x (str, optional): The column name for the x values. Defaults to "longitude".
            y (str, optional): The column name for the y values. Defaults to "latitude".
            popup (list, optional): A list of column names to be used as the popup. Defaults to None.
            min_width (int, optional): The minimum width of the popup. Defaults to 100.
            max_width (int, optional): The maximum width of the popup. Defaults to 200.
            layer_name (str, optional): The name of the layer. Defaults to "Marker Cluster".
            color_column (str, optional): The column name for the color values. Defaults to None.
            marker_colors (list, optional): A list of colors to be used for the markers. Defaults to None.
            icon_colors (list, optional): A list of colors to be used for the icons. Defaults to ['white'].
            icon_names (list, optional): A list of names to be used for the icons. More icons can be found
                at https://fontawesome.com/v4/icons or https://getbootstrap.com/docs/3.3/components/?utm_source=pocket_mylist. Defaults to ['info'].
            angle (int, optional): The angle of the icon. Defaults to 0.
            prefix (str, optional): The prefix states the source of the icon. 'fa' for font-awesome or 'glyphicon' for bootstrap 3. Defaults to 'fa'.
            add_legend (bool, optional): If True, a legend will be added to the map. Defaults to True.
            max_cluster_radius (int, optional): The maximum radius that a cluster will cover from the central marker (in pixels).
            **kwargs: Other keyword arguments to pass to folium.MarkerCluster(). For a list of available options,
                see https://github.com/Leaflet/Leaflet.markercluster. For example, to change the cluster radius, use options={"maxClusterRadius": 50}.
        """
        import pandas as pd

        if "maxClusterRadius" not in kwargs:
            kwargs["maxClusterRadius"] = max_cluster_radius

        color_options = [
            "red",
            "blue",
            "green",
            "purple",
            "orange",
            "darkred",
            "lightred",
            "beige",
            "darkblue",
            "darkgreen",
            "cadetblue",
            "darkpurple",
            "white",
            "pink",
            "lightblue",
            "lightgreen",
            "gray",
            "black",
            "lightgray",
        ]

        if isinstance(data, pd.DataFrame):
            df = data
        elif not data.startswith("http") and (not os.path.exists(data)):
            raise FileNotFoundError("The specified input csv does not exist.")
        else:
            df = pd.read_csv(data)

        col_names = df.columns.values.tolist()

        if color_column is not None and color_column not in col_names:
            raise ValueError(
                f"The color column {color_column} does not exist in the dataframe."
            )

        if color_column is not None:
            items = list(set(df[color_column]))
        else:
            items = None

        if color_column is not None and marker_colors is None:
            if len(items) > len(color_options):
                raise ValueError(
                    f"The number of unique values in the color column {color_column} is greater than the number of available colors."
                )
            else:
                marker_colors = color_options[: len(items)]
        elif color_column is not None and marker_colors is not None:
            if len(items) != len(marker_colors):
                raise ValueError(
                    f"The number of unique values in the color column {color_column} is not equal to the number of available colors."
                )

        if items is not None:
            if len(icon_colors) == 1:
                icon_colors = icon_colors * len(items)
            elif len(items) != len(icon_colors):
                raise ValueError(
                    f"The number of unique values in the color column {color_column} is not equal to the number of available colors."
                )

            if len(icon_names) == 1:
                icon_names = icon_names * len(items)
            elif len(items) != len(icon_names):
                raise ValueError(
                    f"The number of unique values in the color column {color_column} is not equal to the number of available colors."
                )

        if popup is None:
            popup = col_names

        if x not in col_names:
            raise ValueError(f"x must be one of the following: {', '.join(col_names)}")

        if y not in col_names:
            raise ValueError(f"y must be one of the following: {', '.join(col_names)}")

        marker_cluster = plugins.MarkerCluster(name=layer_name, **kwargs).add_to(self)

        for idx, row in df.iterrows():
            html = ""
            for p in popup:
                html = html + "<b>" + p + "</b>" + ": " + str(row[p]) + "<br>"
            popup_html = folium.Popup(html, min_width=min_width, max_width=max_width)

            if items is not None:
                index = items.index(row[color_column])
                marker_icon = folium.Icon(
                    color=marker_colors[index],
                    icon_color=icon_colors[index],
                    icon=icon_names[index],
                    angle=angle,
                    prefix=prefix,
                )
            else:
                marker_icon = None

            folium.Marker(
                location=[row[y], row[x]],
                popup=popup_html,
                icon=marker_icon,
            ).add_to(marker_cluster)

        if items is not None and add_legend:
            marker_colors = [check_color(c) for c in marker_colors]
            self.add_legend(
                title=color_column.title(), colors=marker_colors, labels=items
            )

    def add_circle_markers_from_xy(
        self,
        data,
        x="longitude",
        y="latitude",
        radius=10,
        popup=None,
        tooltip=None,
        min_width=100,
        max_width=200,
        **kwargs,
    ):
        """Adds a marker cluster to the map.

        Args:
            data (str | pd.DataFrame): A csv or Pandas DataFrame containing x, y, z values.
            x (str, optional): The column name for the x values. Defaults to "longitude".
            y (str, optional): The column name for the y values. Defaults to "latitude".
            radius (int, optional): The radius of the circle. Defaults to 10.
            popup (list, optional): A list of column names to be used as the popup. Defaults to None.
            tooltip (list, optional): A list of column names to be used as the tooltip. Defaults to None.
            min_width (int, optional): The minimum width of the popup. Defaults to 100.
            max_width (int, optional): The maximum width of the popup. Defaults to 200.

        """
        import pandas as pd

        data = github_raw_url(data)

        if isinstance(data, pd.DataFrame):
            df = data
        elif not data.startswith("http") and (not os.path.exists(data)):
            raise FileNotFoundError("The specified input csv does not exist.")
        else:
            df = pd.read_csv(data)

        col_names = df.columns.values.tolist()

        if "color" not in kwargs:
            kwargs["color"] = None
        if "fill" not in kwargs:
            kwargs["fill"] = True
        if "fill_color" not in kwargs:
            kwargs["fill_color"] = "blue"
        if "fill_opacity" not in kwargs:
            kwargs["fill_opacity"] = 0.7

        if popup is None:
            popup = col_names

        if not isinstance(popup, list):
            popup = [popup]

        if tooltip is not None:
            if not isinstance(tooltip, list):
                tooltip = [tooltip]

        if x not in col_names:
            raise ValueError(f"x must be one of the following: {', '.join(col_names)}")

        if y not in col_names:
            raise ValueError(f"y must be one of the following: {', '.join(col_names)}")

        for _ in df.itertuples():
            html = ""
            for p in popup:
                html = (
                    html
                    + "<b>"
                    + p
                    + "</b>"
                    + ": "
                    + str(eval(str("row." + p)))
                    + "<br>"
                )
            popup_html = folium.Popup(html, min_width=min_width, max_width=max_width)

            if tooltip is not None:
                html = ""
                for p in tooltip:
                    html = (
                        html
                        + "<b>"
                        + p
                        + "</b>"
                        + ": "
                        + str(eval(str("row." + p)))
                        + "<br>"
                    )

                tooltip_str = folium.Tooltip(html)
            else:
                tooltip_str = None

            folium.CircleMarker(
                location=[eval(f"row.{y}"), eval(f"row.{x}")],
                radius=radius,
                popup=popup_html,
                tooltip=tooltip_str,
                **kwargs,
            ).add_to(self)

    def add_markers_from_xy(
        self,
        data,
        x="longitude",
        y="latitude",
        popup=None,
        min_width=100,
        max_width=200,
        layer_name="Markers",
        icon=None,
        icon_shape="circle-dot",
        border_width=3,
        border_color="#0000ff",
        **kwargs,
    ):
        """Adds markers to the map from a csv or Pandas DataFrame containing x, y values.

        Args:
            data (str | pd.DataFrame): A csv or Pandas DataFrame containing x, y, z values.
            x (str, optional): The column name for the x values. Defaults to "longitude".
            y (str, optional): The column name for the y values. Defaults to "latitude".
            popup (list, optional): A list of column names to be used as the popup. Defaults to None.
            min_width (int, optional): The minimum width of the popup. Defaults to 100.
            max_width (int, optional): The maximum width of the popup. Defaults to 200.
            layer_name (str, optional): The name of the layer. Defaults to "Marker Cluster".
            icon (str, optional): The Font-Awesome icon name to use to render the marker. Defaults to None.
            icon_shape (str, optional): The shape of the marker, such as "retangle-dot", "circle-dot". Defaults to 'circle-dot'.
            border_width (int, optional): The width of the border. Defaults to 3.
            border_color (str, optional): The color of the border. Defaults to '#0000ff'.
            kwargs (dict, optional): Additional keyword arguments to pass to BeautifyIcon. See
                https://python-visualization.github.io/folium/plugins.html#folium.plugins.BeautifyIcon.

        """
        import pandas as pd
        from folium.plugins import BeautifyIcon

        layer_group = folium.FeatureGroup(name=layer_name)

        if isinstance(data, pd.DataFrame):
            df = data
        elif not data.startswith("http") and (not os.path.exists(data)):
            raise FileNotFoundError("The specified input csv does not exist.")
        else:
            df = pd.read_csv(data)

        col_names = df.columns.values.tolist()

        if popup is None:
            popup = col_names

        if x not in col_names:
            raise ValueError(f"x must be one of the following: {', '.join(col_names)}")

        if y not in col_names:
            raise ValueError(f"y must be one of the following: {', '.join(col_names)}")

        for row in df.itertuples():
            html = ""
            for p in popup:
                html = html + "<b>" + p + "</b>" + ": " + str(getattr(row, p)) + "<br>"
            popup_html = folium.Popup(html, min_width=min_width, max_width=max_width)

            marker_icon = BeautifyIcon(
                icon, icon_shape, border_width, border_color, **kwargs
            )
            folium.Marker(
                location=[getattr(row, y), getattr(row, x)],
                popup=popup_html,
                icon=marker_icon,
            ).add_to(layer_group)

        layer_group.add_to(self)

    def add_planet_by_month(
        self, year=2016, month=1, name=None, api_key=None, token_name="PLANET_API_KEY"
    ):
        """Adds a Planet global mosaic by month to the map. To get a Planet API key, see https://developers.planet.com/quickstart/apis

        Args:
            year (int, optional): The year of Planet global mosaic, must be >=2016. Defaults to 2016.
            month (int, optional): The month of Planet global mosaic, must be 1-12. Defaults to 1.
            name (str, optional): The layer name to use. Defaults to None.
            api_key (str, optional): The Planet API key. Defaults to None.
            token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        """
        layer = planet_tile_by_month(
            year, month, name, api_key, token_name, tile_format="folium"
        )
        layer.add_to(self)

    def add_planet_by_quarter(
        self, year=2016, quarter=1, name=None, api_key=None, token_name="PLANET_API_KEY"
    ):
        """Adds a Planet global mosaic by quarter to the map. To get a Planet API key, see https://developers.planet.com/quickstart/apis

        Args:
            year (int, optional): The year of Planet global mosaic, must be >=2016. Defaults to 2016.
            quarter (int, optional): The quarter of Planet global mosaic, must be 1-12. Defaults to 1.
            name (str, optional): The layer name to use. Defaults to None.
            api_key (str, optional): The Planet API key. Defaults to None.
            token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        """
        layer = planet_tile_by_quarter(
            year, quarter, name, api_key, token_name, tile_format="folium"
        )
        layer.add_to(self)

    def publish(
        self,
        name="Folium Map",
        description="",
        source_url="",
        tags=None,
        source_file=None,
        open=True,
        formatting=None,
        token=None,
        **kwargs,
    ):
        """Publish the map to datapane.com

        Args:
            name (str, optional): The document name - can include spaces, caps, symbols, etc., e.g. "Profit & Loss 2020". Defaults to "Folium Map".
            description (str, optional): A high-level description for the document, this is displayed in searches and thumbnails. Defaults to ''.
            source_url (str, optional): A URL pointing to the source code for the document, e.g. a GitHub repo or a Colab notebook. Defaults to ''.
            tags (bool, optional): A list of tags (as strings) used to categorise your document. Defaults to None.
            source_file (str, optional): Path of jupyter notebook file to upload. Defaults to None.
            open (bool, optional): Whether to open the map. Defaults to True.
            formatting (ReportFormatting, optional): Set the basic styling for your report.
            token (str, optional): The token to use to datapane to publish the map. See https://docs.datapane.com/tut-getting-started. Defaults to None.
        """
        import webbrowser
        import warnings

        if os.environ.get("USE_MKDOCS") is not None:
            return

        warnings.filterwarnings("ignore")
        try:
            import datapane as dp
        except Exception:
            webbrowser.open_new_tab("https://docs.datapane.com/")
            raise ImportError(
                "The datapane Python package is not installed. You need to install and authenticate datapane first."
            )

        if token is None:
            try:
                _ = dp.ping(verbose=False)
            except Exception as e:
                if os.environ.get("DP_TOKEN") is not None:
                    dp.login(token=os.environ.get("DP_TOKEN"))
                else:
                    raise Exception(e)
        else:
            dp.login(token)

        try:
            dp.upload_report(
                dp.Plot(self),
                name=name,
                description=description,
                source_url=source_url,
                tags=tags,
                source_file=source_file,
                open=open,
                formatting=formatting,
                **kwargs,
            )

        except Exception as e:
            raise Exception(e)

    def to_html(self, filename=None, **kwargs):
        """Exports a map as an HTML file.

        Args:
            filename (str, optional): File path to the output HTML. Defaults to None.

        Raises:
            ValueError: If it is an invalid HTML file.

        Returns:
            str: A string containing the HTML code.
        """

        if self.options["layersControl"]:
            self.add_layer_control()

        if filename is not None:
            if not filename.endswith(".html"):
                raise ValueError("The output file extension must be html.")
            filename = os.path.abspath(filename)
            out_dir = os.path.dirname(filename)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            self.save(filename, **kwargs)
        else:
            filename = os.path.abspath(random_string() + ".html")
            self.save(filename, **kwargs)
            out_html = ""
            with open(filename) as f:
                lines = f.readlines()
                out_html = "".join(lines)
            os.remove(filename)
            return out_html

    def to_streamlit(
        self,
        width=None,
        height=600,
        scrolling=False,
        add_layer_control=True,
        bidirectional=False,
        **kwargs,
    ):
        """Renders `folium.Figure` or `folium.Map` in a Streamlit app. This method is a static Streamlit Component, meaning, no information is passed back from Leaflet on browser interaction.

        Args:
            width (int, optional): Width of the map. Defaults to None.
            height (int, optional): Height of the map. Defaults to 600.
            scrolling (bool, optional): Whether to allow the map to scroll. Defaults to False.
            add_layer_control (bool, optional): Whether to add the layer control. Defaults to True.
            bidirectional (bool, optional): Whether to add bidirectional functionality to the map. The streamlit-folium package is required to use the bidirectional functionality. Defaults to False.

        Raises:
            ImportError: If streamlit is not installed.

        Returns:
            streamlit.components: components.html object.
        """

        try:
            import streamlit.components.v1 as components

            if add_layer_control:
                self.add_layer_control()

            if bidirectional:
                from streamlit_folium import st_folium

                output = st_folium(self, width=width, height=height)
                return output
            else:
                # if responsive:
                #     make_map_responsive = """
                #     <style>
                #     [title~="st.iframe"] { width: 100%}
                #     </style>
                #     """
                #     st.markdown(make_map_responsive, unsafe_allow_html=True)
                return components.html(
                    self.to_html(), width=width, height=height, scrolling=scrolling
                )

        except Exception as e:
            raise Exception(e)

    def st_map_center(self, st_component):
        """Get the center of the map.

        Args:
            st_folium (streamlit-folium): The streamlit component.

        Returns:
            tuple: The center of the map.
        """

        bounds = st_component["bounds"]
        west = bounds["_southWest"]["lng"]
        south = bounds["_southWest"]["lat"]
        east = bounds["_northEast"]["lng"]
        north = bounds["_northEast"]["lat"]
        return (south + (north - south) / 2, west + (east - west) / 2)

    def st_map_bounds(self, st_component):
        """Get the bounds of the map in the format of (miny, minx, maxy, maxx).

        Args:
            st_folium (streamlit-folium): The streamlit component.

        Returns:
            tuple: The bounds of the map.
        """

        bounds = st_component["bounds"]
        south = bounds["_southWest"]["lat"]
        west = bounds["_southWest"]["lng"]
        north = bounds["_northEast"]["lat"]
        east = bounds["_northEast"]["lng"]

        bounds = [[south, west], [north, east]]
        return bounds

    def st_fit_bounds(self):
        """Fit the map to the bounds of the map.

        Returns:
            folium.Map: The map.
        """

        try:
            import streamlit as st

            if "map_bounds" in st.session_state:
                bounds = st.session_state["map_bounds"]

                self.fit_bounds(bounds)

        except Exception as e:
            raise Exception(e)

    def st_last_draw(self, st_component):
        """Get the last draw feature of the map.

        Args:
            st_folium (streamlit-folium): The streamlit component.

        Returns:
            str: The last draw of the map.
        """

        return st_component["last_active_drawing"]

    def st_last_click(self, st_component):
        """Get the last click feature of the map.

        Args:
            st_folium (streamlit-folium): The streamlit component.

        Returns:
            str: The last click of the map.
        """

        coords = st_component["last_clicked"]
        return (coords["lat"], coords["lng"])

    def st_draw_features(self, st_component):
        """Get the draw features of the map.

        Args:
            st_folium (streamlit-folium): The streamlit component.

        Returns:
            list: The draw features of the map.
        """

        return st_component["all_drawings"]

    def add_census_data(self, wms, layer, census_dict=None, **kwargs):
        """Adds a census data layer to the map.

        Args:
            wms (str): The wms to use. For example, "Current", "ACS 2021", "Census 2020".  See the complete list at https://tigerweb.geo.census.gov/tigerwebmain/TIGERweb_wms.html
            layer (str): The layer name to add to the map.
            census_dict (dict, optional): A dictionary containing census data. Defaults to None. It can be obtained from the get_census_dict() function.
        """

        try:
            if census_dict is None:
                census_dict = get_census_dict()

            if wms not in census_dict.keys():
                raise ValueError(
                    f"The provided WMS is invalid. It must be one of {census_dict.keys()}"
                )

            layers = census_dict[wms]["layers"]
            if layer not in layers:
                raise ValueError(
                    f"The layer name is not valid. It must be one of {layers}"
                )

            url = census_dict[wms]["url"]
            if "name" not in kwargs:
                kwargs["name"] = layer
            if "attribution" not in kwargs:
                kwargs["attribution"] = "U.S. Census Bureau"
            if "format" not in kwargs:
                kwargs["format"] = "image/png"
            if "transparent" not in kwargs:
                kwargs["transparent"] = True

            self.add_wms_layer(url, layer, **kwargs)

        except Exception as e:
            raise Exception(e)

    def add_xyz_service(self, provider, **kwargs):
        """Add a XYZ tile layer to the map.

        Args:
            provider (str): A tile layer name starts with xyz or qms. For example, xyz.OpenTopoMap,

        Raises:
            ValueError: The provider is not valid. It must start with xyz or qms.
        """
        import xyzservices.providers as xyz
        from xyzservices import TileProvider

        if provider.startswith("xyz"):
            name = provider[4:]
            xyz_provider = xyz.flatten()[name]
            url = xyz_provider.build_url()
            attribution = xyz_provider.attribution
            if attribution.strip() == "":
                attribution = " "
            self.add_tile_layer(url, name, attribution)
        elif provider.startswith("qms"):
            name = provider[4:]
            qms_provider = TileProvider.from_qms(name)
            url = qms_provider.build_url()
            attribution = qms_provider.attribution
            if attribution.strip() == "":
                attribution = " "
            self.add_tile_layer(url=url, name=name, attribution=attribution)
        else:
            raise ValueError(
                f"The provider {provider} is not valid. It must start with xyz or qms."
            )

    def add_labels(
        self,
        data,
        column,
        font_size="12pt",
        font_color="black",
        font_family="arial",
        font_weight="normal",
        x="longitude",
        y="latitude",
        draggable=True,
        layer_name="Labels",
        **kwargs,
    ):
        """Adds a label layer to the map. Reference: https://python-visualization.github.io/folium/modules.html#folium.features.DivIcon

        Args:
            data (pd.DataFrame | ee.FeatureCollection): The input data to label.
            column (str): The column name of the data to label.
            font_size (str, optional): The font size of the labels. Defaults to "12pt".
            font_color (str, optional): The font color of the labels. Defaults to "black".
            font_family (str, optional): The font family of the labels. Defaults to "arial".
            font_weight (str, optional): The font weight of the labels, can be normal, bold. Defaults to "normal".
            x (str, optional): The column name of the longitude. Defaults to "longitude".
            y (str, optional): The column name of the latitude. Defaults to "latitude".
            draggable (bool, optional): Whether the labels are draggable. Defaults to True.
            layer_name (str, optional): The name of the layer. Defaults to "Labels".

        """
        import warnings
        import pandas as pd
        from folium.features import DivIcon

        warnings.filterwarnings("ignore")

        if isinstance(data, ee.FeatureCollection):
            centroids = vector_centroids(data)
            df = ee_to_df(centroids)
        elif isinstance(data, pd.DataFrame):
            df = data
        elif isinstance(data, str):
            ext = os.path.splitext(data)[1]
            if ext == ".csv":
                df = pd.read_csv(data)
            elif ext in [".geojson", ".json", ".shp", ".gpkg"]:
                try:
                    import geopandas as gpd

                    df = gpd.read_file(data)
                    df[x] = df.centroid.x
                    df[y] = df.centroid.y
                except Exception as e:
                    print("geopandas is required to read geojson.")
                    print(e)
                    return
        else:
            raise ValueError("data must be a DataFrame or an ee.FeatureCollection.")

        if column not in df.columns:
            raise ValueError(f"column must be one of {', '.join(df.columns)}.")
        if x not in df.columns:
            raise ValueError(f"column must be one of {', '.join(df.columns)}.")
        if y not in df.columns:
            raise ValueError(f"column must be one of {', '.join(df.columns)}.")

        try:
            size = int(font_size.replace("pt", ""))
        except Exception as _:
            raise ValueError("font_size must be something like '10pt'")

        layer_group = folium.FeatureGroup(name=layer_name)
        for index in df.index:
            html = f'<div style="font-size: {font_size};color:{font_color};font-family:{font_family};font-weight: {font_weight}">{df[column][index]}</div>'
            folium.Marker(
                location=[df[y][index], df[x][index]],
                icon=DivIcon(
                    icon_size=(1, 1),
                    icon_anchor=(size, size),
                    html=html,
                    **kwargs,
                ),
                draggable=draggable,
            ).add_to(layer_group)

        layer_group.add_to(self)

    def split_map(
        self,
        left_layer="TERRAIN",
        right_layer="OpenTopoMap",
        left_args={},
        right_args={},
        left_label=None,
        right_label=None,
        left_position="bottomleft",
        right_position="bottomright",
        **kwargs,
    ):
        """Adds a split-panel map.

        Args:
            left_layer (str, optional): The left tile layer. Can be a local file path, HTTP URL, or a basemap name. Defaults to 'TERRAIN'.
            right_layer (str, optional): The right tile layer. Can be a local file path, HTTP URL, or a basemap name. Defaults to 'OpenTopoMap'.
            left_args (dict, optional): The arguments for the left tile layer. Defaults to {}.
            right_args (dict, optional): The arguments for the right tile layer. Defaults to {}.
        """
        if "max_zoom" not in left_args:
            left_args["max_zoom"] = 100
        if "max_native_zoom" not in left_args:
            left_args["max_native_zoom"] = 100

        if "max_zoom" not in right_args:
            right_args["max_zoom"] = 100
        if "max_native_zoom" not in right_args:
            right_args["max_native_zoom"] = 100

        if "layer_name" not in left_args:
            left_args["layer_name"] = "Left Layer"

        if "layer_name" not in right_args:
            right_args["layer_name"] = "Right Layer"

        bounds = None

        try:
            if left_label is not None:
                left_name = left_label
            else:
                left_name = "Left Layer"

            if right_label is not None:
                right_name = right_label
            else:
                right_name = "Right Layer"

            if left_layer in basemaps.keys():
                left_layer = basemaps[left_layer]
            elif isinstance(left_layer, str):
                if left_layer.startswith("http") and left_layer.endswith(".tif"):
                    url = cog_tile(left_layer, **left_args)
                    bbox = cog_bounds(left_layer)
                    bounds = [(bbox[1], bbox[0]), (bbox[3], bbox[2])]
                    left_layer = folium.raster_layers.TileLayer(
                        tiles=url,
                        name=left_name,
                        attr=" ",
                        overlay=True,
                    )
                elif os.path.exists(left_layer):
                    left_layer, left_client = get_local_tile_layer(
                        left_layer,
                        tile_format="folium",
                        return_client=True,
                        **left_args,
                    )
                    bounds = image_bounds(left_client)

                else:
                    left_layer = folium.raster_layers.TileLayer(
                        tiles=left_layer,
                        name=left_name,
                        attr=" ",
                        overlay=True,
                        **left_args,
                    )
            elif isinstance(left_layer, folium.raster_layers.TileLayer) or isinstance(
                left_layer, folium.WmsTileLayer
            ):
                pass
            else:
                raise ValueError(
                    f"left_layer must be one of the following: {', '.join(basemaps.keys())} or a string url to a tif file."
                )

            if right_layer in basemaps.keys():
                right_layer = basemaps[right_layer]
            elif isinstance(right_layer, str):
                if right_layer.startswith("http") and right_layer.endswith(".tif"):
                    url = cog_tile(right_layer, **right_args)
                    bbox = cog_bounds(right_layer)
                    bounds = [(bbox[1], bbox[0]), (bbox[3], bbox[2])]
                    right_layer = folium.raster_layers.TileLayer(
                        tiles=url,
                        name=right_name,
                        attr=" ",
                        overlay=True,
                    )
                elif os.path.exists(right_layer):
                    right_layer, right_client = get_local_tile_layer(
                        right_layer,
                        tile_format="folium",
                        return_client=True,
                        **right_args,
                    )
                    bounds = image_bounds(right_client)
                else:
                    right_layer = folium.raster_layers.TileLayer(
                        tiles=right_layer,
                        name=right_name,
                        attr=" ",
                        overlay=True,
                        **right_args,
                    )
            elif isinstance(right_layer, folium.raster_layers.TileLayer) or isinstance(
                left_layer, folium.WmsTileLayer
            ):
                pass
            else:
                raise ValueError(
                    f"right_layer must be one of the following: {', '.join(basemaps.keys())} or a string url to a tif file."
                )

            control = folium.plugins.SideBySideLayers(
                layer_left=left_layer, layer_right=right_layer
            )
            left_layer.add_to(self)
            right_layer.add_to(self)
            control.add_to(self)

            if left_label is not None:
                if "<" not in left_label:
                    left_label = f"<h4>{left_label}</h4>"
                self.add_html(left_label, position=left_position)

            if right_label is not None:
                if "<" not in right_label:
                    right_label = f"<h4>{right_label}</h4>"
                self.add_html(right_label, position=right_position)
            if bounds is not None:
                self.fit_bounds(bounds)

        except Exception as e:
            print("The provided layers are invalid!")
            raise ValueError(e)

    def add_netcdf(
        self,
        filename,
        variables=None,
        palette=None,
        vmin=None,
        vmax=None,
        nodata=None,
        attribution=None,
        layer_name="NetCDF layer",
        shift_lon=True,
        lat="lat",
        lon="lon",
        **kwargs,
    ):
        """Generate an ipyleaflet/folium TileLayer from a netCDF file.
            If you are using this function in JupyterHub on a remote server (e.g., Binder, Microsoft Planetary Computer),
            try adding to following two lines to the beginning of the notebook if the raster does not render properly.

            import os
            os.environ['LOCALTILESERVER_CLIENT_PREFIX'] = f'{os.environ['JUPYTERHUB_SERVICE_PREFIX'].lstrip('/')}/proxy/{{port}}'

        Args:
            filename (str): File path or HTTP URL to the netCDF file.
            variables (int, optional): The variable/band names to extract data from the netCDF file. Defaults to None. If None, all variables will be extracted.
            port (str, optional): The port to use for the server. Defaults to "default".
            palette (str, optional): The name of the color palette from `palettable` to use when plotting a single band. See https://jiffyclub.github.io/palettable. Default is greyscale
            vmin (float, optional): The minimum value to use when colormapping the palette when plotting a single band. Defaults to None.
            vmax (float, optional): The maximum value to use when colormapping the palette when plotting a single band. Defaults to None.
            nodata (float, optional): The value from the band to use to interpret as not valid data. Defaults to None.
            attribution (str, optional): Attribution for the source raster. This defaults to a message about it being a local file.. Defaults to None.
            layer_name (str, optional): The layer name to use. Defaults to "netCDF layer".
            shift_lon (bool, optional): Flag to shift longitude values from [0, 360] to the range [-180, 180]. Defaults to True.
            lat (str, optional): Name of the latitude variable. Defaults to 'lat'.
            lon (str, optional): Name of the longitude variable. Defaults to 'lon'.
        """

        if in_colab_shell():
            print("The add_netcdf() function is not supported in Colab.")
            return

        tif, vars = netcdf_to_tif(
            filename, shift_lon=shift_lon, lat=lat, lon=lon, return_vars=True
        )

        if variables is None:
            if len(vars) >= 3:
                band_idx = [1, 2, 3]
            else:
                band_idx = [1]
        else:
            if not set(variables).issubset(set(vars)):
                raise ValueError(f"The variables must be a subset of {vars}.")
            else:
                band_idx = [vars.index(v) + 1 for v in variables]

        self.add_raster(
            tif,
            band=band_idx,
            palette=palette,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            attribution=attribution,
            layer_name=layer_name,
            **kwargs,
        )

    def add_data(
        self,
        data,
        column,
        colors=None,
        labels=None,
        cmap=None,
        scheme="Quantiles",
        k=5,
        add_legend=True,
        legend_title=None,
        legend_kwds=None,
        classification_kwds=None,
        style_function=None,
        highlight_function=None,
        layer_name="Untitled",
        info_mode="on_hover",
        encoding="utf-8",
        **kwargs,
    ):
        """Add vector data to the map with a variety of classification schemes.

        Args:
            data (str | pd.DataFrame | gpd.GeoDataFrame): The data to classify. It can be a filepath to a vector dataset, a pandas dataframe, or a geopandas geodataframe.
            column (str): The column to classify.
            cmap (str, optional): The name of a colormap recognized by matplotlib. Defaults to None.
            colors (list, optional): A list of colors to use for the classification. Defaults to None.
            labels (list, optional): A list of labels to use for the legend. Defaults to None.
            scheme (str, optional): Name of a choropleth classification scheme (requires mapclassify).
                Name of a choropleth classification scheme (requires mapclassify).
                A mapclassify.MapClassifier object will be used
                under the hood. Supported are all schemes provided by mapclassify (e.g.
                'BoxPlot', 'EqualInterval', 'FisherJenks', 'FisherJenksSampled',
                'HeadTailBreaks', 'JenksCaspall', 'JenksCaspallForced',
                'JenksCaspallSampled', 'MaxP', 'MaximumBreaks',
                'NaturalBreaks', 'Quantiles', 'Percentiles', 'StdMean',
                'UserDefined'). Arguments can be passed in classification_kwds.
            k (int, optional): Number of classes (ignored if scheme is None or if column is categorical). Default to 5.
            legend_kwds (dict, optional): Keyword arguments to pass to :func:`matplotlib.pyplot.legend` or `matplotlib.pyplot.colorbar`. Defaults to None.
                Keyword arguments to pass to :func:`matplotlib.pyplot.legend` or
                Additional accepted keywords when `scheme` is specified:
                fmt : string
                    A formatting specification for the bin edges of the classes in the
                    legend. For example, to have no decimals: ``{"fmt": "{:.0f}"}``.
                labels : list-like
                    A list of legend labels to override the auto-generated labblels.
                    Needs to have the same number of elements as the number of
                    classes (`k`).
                interval : boolean (default False)
                    An option to control brackets from mapclassify legend.
                    If True, open/closed interval brackets are shown in the legend.
            classification_kwds (dict, optional): Keyword arguments to pass to mapclassify. Defaults to None.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style_function (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
                style_callback is a function that takes the feature as argument and should return a dictionary of the following form:
                style_callback = lambda feat: {"fillColor": feat["properties"]["color"]}
                style is a dictionary of the following form:
                    style = {
                    "stroke": False,
                    "color": "#ff0000",
                    "weight": 1,
                    "opacity": 1,
                    "fill": True,
                    "fillColor": "#ffffff",
                    "fillOpacity": 1.0,
                    "dashArray": "9"
                    "clickable": True,
                }
            hightlight_function (function, optional): Highlighting function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
                highlight_function is a function that takes the feature as argument and should return a dictionary of the following form:
                highlight_function = lambda feat: {"fillColor": feat["properties"]["color"]}
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            encoding (str, optional): The encoding of the GeoJSON file. Defaults to "utf-8".
        """

        import warnings

        gdf, legend_dict = classify(
            data=data,
            column=column,
            cmap=cmap,
            colors=colors,
            labels=labels,
            scheme=scheme,
            k=k,
            legend_kwds=legend_kwds,
            classification_kwds=classification_kwds,
        )

        if legend_title is None:
            legend_title = column

        if "style" in kwargs:
            warnings.warn(
                "The style arguments is for ipyleaflet only. ",
                UserWarning,
            )
            kwargs.pop("style")

        if "hover_style" in kwargs:
            warnings.warn(
                "The hover_style arguments is for ipyleaflet only. ",
                UserWarning,
            )
            kwargs.pop("hover_style")

        if "style_callback" in kwargs:
            warnings.warn(
                "The style_callback arguments is for ipyleaflet only. ",
                UserWarning,
            )
            kwargs.pop("style_callback")

        if style_function is None:
            style_function = lambda feat: {
                # "stroke": False,
                # "color": "#ff0000",
                "weight": 1,
                "opacity": 1,
                # "fill": True,
                # "fillColor": "#ffffff",
                "fillOpacity": 1.0,
                # "dashArray": "9"
                # "clickable": True,
                "fillColor": feat["properties"]["color"],
            }

        if highlight_function is None:
            highlight_function = lambda feat: {
                "weight": 2,
                "fillOpacity": 0.5,
            }

        self.add_gdf(
            gdf,
            layer_name=layer_name,
            style_function=style_function,
            highlight_function=highlight_function,
            info_mode=info_mode,
            encoding=encoding,
            **kwargs,
        )
        if add_legend:
            self.add_legend(title=legend_title, legend_dict=legend_dict)

    def add_image(self, image, position=(0, 0), **kwargs):
        """Add an image to the map.

        Args:
            image (str | ipywidgets.Image): The image to add.
            position (tuple, optional): The position of the image in the format of (x, y),
                the percentage ranging from 0 to 100, starting from the lower-left corner. Defaults to (0, 0).
        """
        import base64

        if isinstance(image, str):
            if image.startswith("http"):
                html = f'<img src="{image}">'
                if isinstance(position, tuple):
                    position = "bottomright"
                self.add_html(html, position=position, **kwargs)

            elif os.path.exists(image):
                if position == "bottomleft":
                    position = (5, 5)
                elif position == "bottomright":
                    position = (80, 5)
                elif position == "topleft":
                    position = (5, 60)
                elif position == "topright":
                    position = (80, 60)

                with open(image, "rb") as lf:
                    # open in binary mode, read bytes, encode, decode obtained bytes as utf-8 string
                    b64_content = base64.b64encode(lf.read()).decode("utf-8")
                    widget = plugins.FloatImage(
                        "data:image/png;base64,{}".format(b64_content),
                        bottom=position[1],
                        left=position[0],
                    )
                    widget.add_to(self)

        else:
            raise Exception("Invalid image")

    def add_widget(self, content, position="bottomright", **kwargs):
        """Add a widget (e.g., text, HTML, figure) to the map.

        Args:
            content (str): The widget to add.
            position (str, optional): The position of the widget. Defaults to "bottomright".
        """

        from matplotlib import figure
        import base64
        from io import BytesIO

        allowed_positions = ["topleft", "topright", "bottomleft", "bottomright"]

        if position not in allowed_positions:
            raise Exception(f"position must be one of {allowed_positions}")

        try:
            if isinstance(content, str):
                widget = CustomControl(content, position=position)
                widget.add_to(self)
            elif isinstance(content, figure.Figure):
                buf = BytesIO()
                content.savefig(buf, format="png")
                buf.seek(0)
                b64_content = base64.b64encode(buf.read()).decode("utf-8")
                widget = CustomControl(
                    f"""<img src="data:image/png;base64,{b64_content}">""",
                    position=position,
                )
                widget.add_to(self)
            else:
                raise Exception("The content must be a string or a matplotlib figure")

        except Exception as e:
            raise Exception(f"Error adding widget: {e}")

    def add_html(self, html, position="bottomright", **kwargs):
        """Add HTML to the map.

        Args:
            html (str): The HTML to add.
            position (str, optional): The position of the widget. Defaults to "bottomright".
        """

        self.add_widget(html, position=position, **kwargs)

    def add_text(
        self,
        text,
        fontsize=20,
        fontcolor="black",
        bold=False,
        padding="5px",
        background=True,
        bg_color="white",
        border_radius="5px",
        position="bottomright",
        **kwargs,
    ):
        """Add text to the map.

        Args:
            text (str): The text to add.
            fontsize (int, optional): The font size. Defaults to 20.
            fontcolor (str, optional): The font color. Defaults to "black".
            bold (bool, optional): Whether to use bold font. Defaults to False.
            padding (str, optional): The padding. Defaults to "5px".
            background (bool, optional): Whether to use background. Defaults to True.
            bg_color (str, optional): The background color. Defaults to "white".
            border_radius (str, optional): The border radius. Defaults to "5px".
            position (str, optional): The position of the widget. Defaults to "bottomright".
        """

        if background:
            text = f"""<div style="font-size: {fontsize}px; color: {fontcolor}; font-weight: {'bold' if bold else 'normal'};
            padding: {padding}; background-color: {bg_color};
            border-radius: {border_radius};">{text}</div>"""
        else:
            text = f"""<div style="font-size: {fontsize}px; color: {fontcolor}; font-weight: {'bold' if bold else 'normal'};
            padding: {padding};">{text}</div>"""

        self.add_html(text, position=position, **kwargs)

    def to_gradio(self, width="100%", height="500px", **kwargs):
        """Converts the map to an HTML string that can be used in Gradio. Removes unsupported elements, such as
            attribution and any code blocks containing functions. See https://github.com/gradio-app/gradio/issues/3190

        Args:
            width (str, optional): The width of the map. Defaults to '100%'.
            height (str, optional): The height of the map. Defaults to '500px'.

        Returns:
            str: The HTML string to use in Gradio.
        """

        if isinstance(width, int):
            width = f"{width}px"
        if isinstance(height, int):
            height = f"{height}px"

        html = self.to_html()
        lines = html.split("\n")
        output = []
        skipped_lines = []
        for index, line in enumerate(lines):
            if index in skipped_lines:
                continue
            if line.lstrip().startswith('{"attribution":'):
                continue
            elif "on(L.Draw.Event.CREATED, function(e)" in line:
                for i in range(14):
                    skipped_lines.append(index + i)
            elif "L.Control.geocoder" in line:
                for i in range(5):
                    skipped_lines.append(index + i)
            elif "function(e)" in line:
                print(
                    f"Warning: The folium plotting backend does not support functions in code blocks. Please delete line {index + 1}."
                )
            else:
                output.append(line + "\n")

        return f"""<iframe style="width: {width}; height: {height}" name="result" allow="midi; geolocation; microphone; camera;
        display-capture; encrypted-media;" sandbox="allow-modals allow-forms
        allow-scripts allow-same-origin allow-popups
        allow-top-navigation-by-user-activation allow-downloads" allowfullscreen=""
        allowpaymentrequest="" frameborder="0" srcdoc='{"".join(output)}'></iframe>"""

    def remove_labels(self, **kwargs):
        """Removes a layer from the map."""
        print("The folium plotting backend does not support removing labels.")

    def basemap_demo(self):
        """A demo for using geemap basemaps."""
        print("The folium plotting backend does not support this function.")

    def set_plot_options(
        self,
        **kwargs,
    ):
        """Sets plotting options."""
        print("The folium plotting backend does not support this function.")

    def ts_inspector(
        self,
        left_ts,
        right_ts,
        left_names,
        right_names,
        left_vis={},
        right_vis={},
        width="130px",
        **kwargs,
    ):
        print("The folium plotting backend does not support this function.")

    def add_time_slider(
        self,
        ee_object,
        vis_params={},
        region=None,
        layer_name="Time series",
        labels=None,
        time_interval=1,
        position="bottomright",
        slider_length="150px",
        date_format="YYYY-MM-dd",
        opacity=1.0,
        **kwargs,
    ):
        print("The folium plotting backend does not support this function.")

    def extract_values_to_points(self, filename):
        print("The folium plotting backend does not support this function.")


class SplitControl(Layer):
    """
    Creates a SplitControl that takes two Layers and adds a sliding control with the leaflet-side-by-side plugin.
    Uses the Leaflet leaflet-side-by-side plugin https://github.com/digidem/leaflet-side-by-side Parameters.
    The source code is adapted from https://github.com/python-visualization/folium/pull/1292
    ----------
    layer_left: Layer.
        The left Layer within the side by side control.
        Must  be created and added to the map before being passed to this class.
    layer_right: Layer.
        The right Layer within the side by side control.
        Must  be created and added to the map before being passed to this class.
    name : string, default None
        The name of the Layer, as it will appear in LayerControls.
    overlay : bool, default True
        Adds the layer as an optional overlay (True) or the base layer (False).
    control : bool, default True
        Whether the Layer will be included in LayerControls.
    show: bool, default True
        Whether the layer will be shown on opening (only for overlays).
    Examples
    --------
    >>> sidebyside = SideBySideLayers(layer_left, layer_right)
    >>> sidebyside.add_to(m)
    """

    _template = Template(
        """
        {% macro script(this, kwargs) %}
            var {{ this.get_name() }} = L.control.sideBySide(
                {{ this.layer_left.get_name() }}, {{ this.layer_right.get_name() }}
            ).addTo({{ this._parent.get_name() }});
        {% endmacro %}
        """
    )

    def __init__(
        self, layer_left, layer_right, name=None, overlay=True, control=False, show=True
    ):
        super(SplitControl, self).__init__(
            name=name, overlay=overlay, control=control, show=show
        )
        self._name = "SplitControl"
        self.layer_left = layer_left
        self.layer_right = layer_right

    def render(self, **kwargs):
        super(SplitControl, self).render()

        figure = self.get_root()
        assert isinstance(figure, Figure), (
            "You cannot render this Element " "if it is not in a Figure."
        )

        figure.header.add_child(
            JavascriptLink(
                "https://raw.githack.com/digidem/leaflet-side-by-side/gh-pages/leaflet-side-by-side.js"
            ),  # noqa
            name="leaflet.sidebyside",
        )


class SideBySideLayers(JSCSSMixin, Layer):
    """
    Creates a SideBySideLayers that takes two Layers and adds a sliding
    control with the leaflet-side-by-side plugin.
    Uses the Leaflet leaflet-side-by-side plugin https://github.com/digidem/leaflet-side-by-side.
    Adopted from https://github.com/python-visualization/folium/pull/1292/files.
    Parameters
    ----------
    layer_left: Layer.
        The left Layer within the side by side control.
        Must be created and added to the map before being passed to this class.
    layer_right: Layer.
        The right Layer within the side by side control.
        Must be created and added to the map before being passed to this class.
    Examples
    --------
    >>> sidebyside = SideBySideLayers(layer_left, layer_right)
    >>> sidebyside.add_to(m)
    """

    _template = Template(
        """
        {% macro script(this, kwargs) %}
            var {{ this.get_name() }} = L.control.sideBySide(
                {{ this.layer_left.get_name() }}, {{ this.layer_right.get_name() }}
            ).addTo({{ this._parent.get_name() }});
        {% endmacro %}
        """
    )

    default_js = [
        (
            "leaflet.sidebyside",
            "https://cdn.jsdelivr.net/gh/digidem/leaflet-side-by-side@gh-pages/leaflet-side-by-side.min.js",
        ),
    ]

    def __init__(self, layer_left, layer_right):
        super().__init__(control=False)
        self._name = "SideBySideLayers"
        self.layer_left = layer_left
        self.layer_right = layer_right


class CustomControl(MacroElement):
    """Put any HTML on the map as a Leaflet Control.
    Adopted from https://github.com/python-visualization/folium/pull/1662

    """

    _template = Template(
        """
        {% macro script(this, kwargs) %}
        L.Control.CustomControl = L.Control.extend({
            onAdd: function(map) {
                let div = L.DomUtil.create('div');
                div.innerHTML = `{{ this.html }}`;
                return div;
            },
            onRemove: function(map) {
                // Nothing to do here
            }
        });
        L.control.customControl = function(opts) {
            return new L.Control.CustomControl(opts);
        }
        L.control.customControl(
            { position: "{{ this.position }}" }
        ).addTo({{ this._parent.get_name() }});
        {% endmacro %}
    """
    )

    def __init__(self, html, position="bottomleft"):
        def escape_backticks(text):
            """Escape backticks so text can be used in a JS template."""
            import re

            return re.sub(r"(?<!\\)`", r"\`", text)

        super().__init__()
        self.html = escape_backticks(html)
        self.position = position


class FloatText(MacroElement):
    """Adds a floating image in HTML canvas on top of the map."""

    _template = Template(
        """
            {% macro header(this,kwargs) %}
                <style>
                    #{{this.get_name()}} {
                        position:absolute;
                        bottom:{{this.bottom}}%;
                        left:{{this.left}}%;
                        }
                </style>
            {% endmacro %}

            {% macro html(this, kwargs) %}

            <!doctype html>
            <html lang="en">
            <head>
            </head>
            <body>

            <div id='{{this.get_name()}}' class='{{this.get_name()}}'
                style='position: absolute; z-index:9999; border:2px solid grey; background-color:rgba(255, 255, 255, 0.8);
                border-radius:5px; padding: 5px; font-size:14px; '>

            <div class='text'>{{this.text}}</div>
            </div>

            </body>
            </html>

            <style type='text/css'>
            .{{this.get_name()}} .text {
                text-align: left;
                margin-bottom: 0px;
                font-size: 90%;
                float: left;
                }
            </style>
            {% endmacro %}
            """
    )

    def __init__(self, text, bottom=75, left=75):
        super(FloatText, self).__init__()
        self._name = "FloatText"
        self.text = text
        self.bottom = bottom
        self.left = left


def delete_dp_report(name):
    """Deletes a datapane report.

    Args:
        name (str): Name of the report to delete.
    """
    try:
        import datapane as dp

        reports = dp.Report.list()
        items = list(reports)
        names = list(map(lambda item: item["name"], items))
        if name in names:
            report = dp.Report.get(name)
            url = report.blocks[0]["url"]
            # print(f'Deleting {url}...')
            dp.Report.delete(dp.Report.by_id(url))
    except Exception as e:
        print(e)
        return


def delete_dp_reports():
    """Deletes all datapane reports."""
    try:
        import datapane as dp

        reports = dp.Report.list()
        for item in reports:
            print(item["name"])
            report = dp.Report.get(item["name"])
            url = report.blocks[0]["url"]
            print(f"Deleting {url}...")
            dp.Report.delete(dp.Report.by_id(url))
    except Exception as e:
        print(e)
        return


def ee_tile_layer(
    ee_object, vis_params={}, name="Layer untitled", shown=True, opacity=1.0, **kwargs
):
    """Converts and Earth Engine layer to ipyleaflet TileLayer.

    Args:
        ee_object (Collection|Feature|Image|MapId): The object to add to the map.
        vis_params (dict, optional): The visualization parameters. Defaults to {}.
        name (str, optional): The name of the layer. Defaults to 'Layer untitled'.
        shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
        opacity (float, optional): The layer's opacity represented as a number between 0 and 1. Defaults to 1.
    """

    image = None

    if (
        not isinstance(ee_object, ee.Image)
        and not isinstance(ee_object, ee.ImageCollection)
        and not isinstance(ee_object, ee.FeatureCollection)
        and not isinstance(ee_object, ee.Feature)
        and not isinstance(ee_object, ee.Geometry)
    ):
        err_str = "\n\nThe image argument in 'addLayer' function must be an instance of one of ee.Image, ee.Geometry, ee.Feature or ee.FeatureCollection."
        raise AttributeError(err_str)

    if (
        isinstance(ee_object, ee.geometry.Geometry)
        or isinstance(ee_object, ee.feature.Feature)
        or isinstance(ee_object, ee.featurecollection.FeatureCollection)
    ):
        features = ee.FeatureCollection(ee_object)

        width = 2

        if "width" in vis_params:
            width = vis_params["width"]

        color = "000000"

        if "color" in vis_params:
            color = vis_params["color"]

        image_fill = features.style(**{"fillColor": color}).updateMask(
            ee.Image.constant(0.5)
        )
        image_outline = features.style(
            **{"color": color, "fillColor": "00000000", "width": width}
        )

        image = image_fill.blend(image_outline)
    elif isinstance(ee_object, ee.image.Image):
        image = ee_object
    elif isinstance(ee_object, ee.imagecollection.ImageCollection):
        image = ee_object.mosaic()

    if "palette" in vis_params:
        if isinstance(vis_params["palette"], Box):
            try:
                vis_params["palette"] = vis_params["palette"]["default"]
            except Exception as e:
                print("The provided palette is invalid.")
                raise Exception(e)
        elif isinstance(vis_params["palette"], str):
            vis_params["palette"] = check_cmap(vis_params["palette"])
        elif not isinstance(vis_params["palette"], list):
            raise ValueError(
                "The palette must be a list of colors or a string or a Box object."
            )

    map_id_dict = ee.Image(image).getMapId(vis_params)
    tile_layer = folium.raster_layers.TileLayer(
        tiles=map_id_dict["tile_fetcher"].url_format,
        attr="Google Earth Engine",
        name=name,
        overlay=True,
        control=True,
        opacity=opacity,
        show=shown,
        max_zoom=24,
        **kwargs,
    )
    return tile_layer


def st_map_center(lat, lon):
    """Returns the map center coordinates for a given latitude and longitude. If the system variable 'map_center' exists, it is used. Otherwise, the default is returned.

    Args:
        lat (float): Latitude.
        lon (float): Longitude.

    Raises:
        Exception: If streamlit is not installed.

    Returns:
        list: The map center coordinates.
    """
    try:
        import streamlit as st

        if "map_center" in st.session_state:
            return st.session_state["map_center"]
        else:
            return [lat, lon]

    except Exception as e:
        raise Exception(e)


def st_save_bounds(st_component):
    """Saves the map bounds to the session state.

    Args:
        map (folium.folium.Map): The map to save the bounds from.
    """
    try:
        import streamlit as st

        if st_component is not None:
            bounds = st_component["bounds"]
            south = bounds["_southWest"]["lat"]
            west = bounds["_southWest"]["lng"]
            north = bounds["_northEast"]["lat"]
            east = bounds["_northEast"]["lng"]

            bounds = [[south, west], [north, east]]
            center = [south + (north - south) / 2, west + (east - west) / 2]

            st.session_state["map_bounds"] = bounds
            st.session_state["map_center"] = center
    except Exception as e:
        raise Exception(e)


def linked_maps(
    rows=2,
    cols=2,
    height="400px",
    ee_objects=[],
    vis_params=[],
    labels=[],
    label_position="topright",
    **kwargs,
):
    print("The folium plotting backend does not support this function.")
