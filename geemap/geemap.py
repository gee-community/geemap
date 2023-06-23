"""Main module for interactive mapping using Google Earth Engine Python API and ipyleaflet.
Keep in mind that Earth Engine functions use both camel case and snake case, 
such as setOptions(), setCenter(), centerObject(), addLayer().
ipyleaflet functions use snake case, such as add_tile_layer(), add_wms_layer(), add_minimap().
"""

import os

import ee
import ipyleaflet
import ipywidgets as widgets

from box import Box
from bqplot import pyplot as plt

from IPython.display import display
from .basemaps import xyz_to_leaflet
from .common import *
from .conversion import *
from .timelapse import *
from .plot import *

from . import examples


basemaps = Box(xyz_to_leaflet(), frozen_box=True)


class Map(ipyleaflet.Map):
    """The Map class inherits from ipyleaflet.Map. The arguments you can pass to the Map can
        be found at https://ipyleaflet.readthedocs.io/en/latest/map_and_basemaps/map.html.
        By default, the Map will add Google Maps as the basemap. Set add_google_map = False
        to use OpenStreetMap as the basemap.

    Returns:
        object: ipyleaflet map object.
    """

    def __init__(self, **kwargs):
        import warnings

        warnings.filterwarnings("ignore")

        # Authenticates Earth Engine and initializes an Earth Engine session
        if "ee_initialize" not in kwargs.keys():
            kwargs["ee_initialize"] = True

        if kwargs["ee_initialize"]:
            ee_initialize()

        # Default map center center (lat, lon) and zoom level
        center = [20, 0]
        zoom = 2

        # Set map width and height
        if "height" not in kwargs.keys():
            kwargs["height"] = "600px"
        elif isinstance(kwargs["height"], int):
            kwargs["height"] = str(kwargs["height"]) + "px"
        if "width" in kwargs.keys() and isinstance(kwargs["width"], int):
            kwargs["width"] = str(kwargs["width"]) + "px"

        # Convert folium params to ipyleaflet params
        if "location" in kwargs.keys():
            kwargs["center"] = kwargs["location"]
            kwargs.pop("location")
        if "zoom_start" in kwargs.keys():
            kwargs["zoom"] = kwargs["zoom_start"]
            kwargs.pop("zoom_start")

        # Set map center and zoom level
        if "center" not in kwargs.keys():
            kwargs["center"] = center
        if "zoom" not in kwargs.keys():
            kwargs["zoom"] = zoom
        if "max_zoom" not in kwargs.keys():
            kwargs["max_zoom"] = 24

        # Add Google Maps as the default basemap
        if "add_google_map" not in kwargs.keys() and "basemap" not in kwargs.keys():
            kwargs["add_google_map"] = True

        # Enable scroll wheel zoom by default
        if "scroll_wheel_zoom" not in kwargs.keys():
            kwargs["scroll_wheel_zoom"] = True

        # Whether to use lite mode, which contains only the zoom control.
        if "lite_mode" not in kwargs.keys():
            kwargs["lite_mode"] = False
        if kwargs["lite_mode"]:
            kwargs["data_ctrl"] = False
            kwargs["zoom_ctrl"] = True
            kwargs["fullscreen_ctrl"] = False
            kwargs["draw_ctrl"] = False
            kwargs["search_ctrl"] = False
            kwargs["measure_ctrl"] = False
            kwargs["scale_ctrl"] = False
            kwargs["layer_ctrl"] = False
            kwargs["toolbar_ctrl"] = False
            kwargs["attribution_ctrl"] = False

        # Default controls to use
        if "data_ctrl" not in kwargs.keys():
            kwargs["data_ctrl"] = True
        if "zoom_ctrl" not in kwargs.keys():
            kwargs["zoom_ctrl"] = True
        if "fullscreen_ctrl" not in kwargs.keys():
            kwargs["fullscreen_ctrl"] = True
        if "draw_ctrl" not in kwargs.keys():
            kwargs["draw_ctrl"] = True
        if "search_ctrl" not in kwargs.keys():
            kwargs["search_ctrl"] = False
        if "measure_ctrl" not in kwargs.keys():
            kwargs["measure_ctrl"] = True
        if "scale_ctrl" not in kwargs.keys():
            kwargs["scale_ctrl"] = True
        if "layer_ctrl" not in kwargs.keys():
            kwargs["layer_ctrl"] = False
        if "toolbar_ctrl" not in kwargs.keys():
            kwargs["toolbar_ctrl"] = True
        if "attribution_ctrl" not in kwargs.keys():
            kwargs["attribution_ctrl"] = True
        if "use_voila" not in kwargs.keys():
            kwargs["use_voila"] = False

        # Use any basemap available through the basemap module, such as 'ROADMAP', 'OpenTopoMap'
        if "basemap" in kwargs:
            if isinstance(kwargs["basemap"], str):
                kwargs["basemap"] = get_basemap(kwargs["basemap"])

        # Disable some widgets if using Voila
        if os.environ.get("USE_VOILA") is not None:
            kwargs["use_voila"] = True

        # Inherits the ipyleaflet Map class
        super().__init__(**kwargs)
        self.baseclass = "ipyleaflet"
        self.layout.height = kwargs["height"]
        if "width" in kwargs:
            self.layout.width = kwargs["width"]

        # sandbox path for Voila app to restrict access to system directories.
        if "sandbox_path" not in kwargs:
            if os.environ.get("USE_VOILA") is not None:
                self.sandbox_path = os.getcwd()
            else:
                self.sandbox_path = None
        else:
            if os.path.exists(os.path.abspath(kwargs["sandbox_path"])):
                self.sandbox_path = kwargs["sandbox_path"]
            else:
                print("The sandbox path is invalid.")
                self.sandbox_path = None

        # Remove all default controls
        self.clear_controls()

        # The number of shapes drawn by the user using the DrawControl
        self.draw_count = 0
        # The list of Earth Engine Geometry objects converted from geojson
        self.draw_features = []
        # The Earth Engine Geometry object converted from the last drawn feature
        self.draw_last_feature = None
        self.draw_layer = None
        self.draw_last_json = None
        self.draw_last_bounds = None
        self.user_roi = None
        self.user_rois = None
        self.last_ee_data = None
        self.last_ee_layer = None
        self.geojson_layers = []

        self.roi_start = False
        self.roi_end = False

        # Default reducer to use
        if kwargs["ee_initialize"]:
            self.roi_reducer = ee.Reducer.mean()
        self.roi_reducer_scale = None

        # List for storing pixel values and locations based on user-drawn geometries.
        self.chart_points = []
        self.chart_values = []
        self.chart_labels = None

        self.plot_widget = None  # The plot widget for plotting Earth Engine data
        self.plot_control = None  # The plot control for interacting plotting
        self.random_marker = None

        self.legend_widget = None
        self.legend = None
        self.colorbar = None

        self.ee_layers = []
        self.ee_layer_names = []
        self.ee_raster_layers = []
        self.ee_raster_layer_names = []
        self.ee_vector_layers = []
        self.ee_vector_layer_names = []
        self.ee_layer_dict = {}

        self.toolbar = None
        self.toolbar_button = None
        self.vis_control = None
        self.vis_widget = None
        self.colorbar_ctrl = None
        self.colorbar_widget = None
        self.tool_output = None
        self.tool_output_ctrl = None
        self.layer_control = None
        self.convert_ctrl = None
        self.toolbar_ctrl = None
        self._expand_point = False
        self._expand_pixels = True
        self._expand_objects = False

        if kwargs.get("data_ctrl"):
            from .toolbar import search_data_gui

            search_data_gui(self)

        if kwargs.get("search_ctrl"):
            self.add_search_control()

        if kwargs.get("zoom_ctrl"):
            self.add(ipyleaflet.ZoomControl(position="topleft"))

        if kwargs.get("layer_ctrl"):
            layer_control = ipyleaflet.LayersControl(position="topright")
            self.layer_control = layer_control
            self.add(layer_control)

        if kwargs.get("scale_ctrl"):
            scale = ipyleaflet.ScaleControl(position="bottomleft")
            self.scale_control = scale
            self.add(scale)

        if kwargs.get("fullscreen_ctrl"):
            fullscreen = ipyleaflet.FullScreenControl()
            self.fullscreen_control = fullscreen
            self.add(fullscreen)

        if kwargs.get("measure_ctrl"):
            measure = ipyleaflet.MeasureControl(
                position="bottomleft",
                active_color="orange",
                primary_length_unit="kilometers",
            )
            self.measure_control = measure
            self.add(measure)

        if kwargs.get("add_google_map"):
            self.add("ROADMAP")

        if kwargs.get("attribution_ctrl"):
            self.add(ipyleaflet.AttributionControl(position="bottomright"))

        if kwargs.get("draw_ctrl"):
            self.add_draw_control()

        # Dropdown widget for plotting
        self.plot_dropdown_control = None
        self.plot_dropdown_widget = None
        self.plot_options = {}
        self.plot_marker_cluster = ipyleaflet.MarkerCluster(name="Marker Cluster")
        self.plot_coordinates = []
        self.plot_markers = []
        self.plot_last_click = []
        self.plot_all_clicks = []
        self.plot_checked = False

        tool_output = widgets.Output()
        self.tool_output = tool_output
        tool_output.clear_output(wait=True)

        if kwargs.get("toolbar_ctrl"):
            self.add_toolbar()

    def add(self, object):
        """Adds a layer or control to the map.

        Args:
            layer (object): The layer or control to add to the map.
        """
        if isinstance(object, str):
            if object in basemaps.keys():
                object = get_basemap(object)

        super().add(object)

        if hasattr(self, "layer_manager_widget"):
            self.update_layer_manager()

    def set_options(self, mapTypeId="HYBRID", styles=None, types=None):
        """Adds Google basemap and controls to the ipyleaflet map.

        Args:
            mapTypeId (str, optional): A mapTypeId to set the basemap to. Can be one of "ROADMAP", "SATELLITE",
                "HYBRID" or "TERRAIN" to select one of the standard Google Maps API map types. Defaults to 'HYBRID'.
            styles (object, optional): A dictionary of custom MapTypeStyle objects keyed with a name
                that will appear in the map's Map Type Controls. Defaults to None.
            types (list, optional): A list of mapTypeIds to make available. If omitted, but opt_styles is specified,
                appends all of the style keys to the standard Google Maps API map types.. Defaults to None.
        """
        self.clear_layers()
        self.clear_controls()
        self.scroll_wheel_zoom = True
        self.add(ipyleaflet.ZoomControl(position="topleft"))
        self.add(ipyleaflet.LayersControl(position="topright"))
        self.add(ipyleaflet.ScaleControl(position="bottomleft"))
        self.add(ipyleaflet.FullScreenControl())
        self.add(ipyleaflet.DrawControl())

        measure = ipyleaflet.MeasureControl(
            position="bottomleft",
            active_color="orange",
            primary_length_unit="kilometers",
        )
        self.add(measure)

        try:
            self.add(mapTypeId)
        except Exception:
            raise ValueError(
                'Google basemaps can only be one of "ROADMAP", "SATELLITE", "HYBRID" or "TERRAIN".'
            )

    setOptions = set_options

    def add_ee_layer(
        self, ee_object, vis_params={}, name=None, shown=True, opacity=1.0
    ):
        """Adds a given EE object to the map as a layer.

        Args:
            ee_object (Collection|Feature|Image|MapId): The object to add to the map.
            vis_params (dict, optional): The visualization parameters. Defaults to {}.
            name (str, optional): The name of the layer. Defaults to 'Layer N'.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            opacity (float, optional): The layer's opacity represented as a number between 0 and 1. Defaults to 1.
        """

        image = None

        if vis_params is None:
            vis_params = {}

        if name is None:
            layer_count = len(self.layers)
            name = "Layer " + str(layer_count + 1)

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
            if isinstance(vis_params["palette"], tuple):
                vis_params["palette"] = list(vis_params["palette"])
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
        url = map_id_dict["tile_fetcher"].url_format
        tile_layer = ipyleaflet.TileLayer(
            url=url,
            attribution="Google Earth Engine",
            name=name,
            opacity=opacity,
            visible=shown,
            max_zoom=24,
        )

        layer = self.find_layer(name=name)
        if layer is not None:
            existing_object = self.ee_layer_dict[name]["ee_object"]

            if isinstance(existing_object, ee.Image) or isinstance(
                existing_object, ee.ImageCollection
            ):
                self.ee_raster_layers.remove(existing_object)
                self.ee_raster_layer_names.remove(name)
                if self.plot_dropdown_widget is not None:
                    self.plot_dropdown_widget.options = list(self.ee_raster_layer_names)
            elif (
                isinstance(ee_object, ee.Geometry)
                or isinstance(ee_object, ee.Feature)
                or isinstance(ee_object, ee.FeatureCollection)
            ):
                self.ee_vector_layers.remove(existing_object)
                self.ee_vector_layer_names.remove(name)

            self.ee_layers.remove(existing_object)
            self.ee_layer_names.remove(name)
            self.remove_layer(layer)

        self.ee_layers.append(ee_object)
        if name not in self.ee_layer_names:
            self.ee_layer_names.append(name)
        self.ee_layer_dict[name] = {
            "ee_object": ee_object,
            "ee_layer": tile_layer,
            "vis_params": vis_params,
        }

        self.add(tile_layer)
        self.last_ee_layer = self.ee_layer_dict[name]
        self.last_ee_data = self.ee_layer_dict[name]["ee_object"]

        if isinstance(ee_object, ee.Image) or isinstance(ee_object, ee.ImageCollection):
            self.ee_raster_layers.append(ee_object)
            self.ee_raster_layer_names.append(name)
            if self.plot_dropdown_widget is not None:
                self.plot_dropdown_widget.options = list(self.ee_raster_layer_names)
        elif (
            isinstance(ee_object, ee.Geometry)
            or isinstance(ee_object, ee.Feature)
            or isinstance(ee_object, ee.FeatureCollection)
        ):
            self.ee_vector_layers.append(ee_object)
            self.ee_vector_layer_names.append(name)

        arc_add_layer(url, name, shown, opacity)

    addLayer = add_ee_layer

    def remove_ee_layer(self, name):
        """Removes an Earth Engine layer.

        Args:
            name (str): The name of the Earth Engine layer to remove.
        """
        if name in self.ee_layer_dict:
            ee_object = self.ee_layer_dict[name]["ee_object"]
            ee_layer = self.ee_layer_dict[name]["ee_layer"]
            if name in self.ee_raster_layer_names:
                self.ee_raster_layer_names.remove(name)
                self.ee_raster_layers.remove(ee_object)
            elif name in self.ee_vector_layer_names:
                self.ee_vector_layer_names.remove(name)
                self.ee_vector_layers.remove(ee_object)
            self.ee_layers.remove(ee_object)
            self.ee_layer_names.remove(name)
            if ee_layer in self.layers:
                self.remove_layer(ee_layer)

    def draw_layer_on_top(self):
        """Move user-drawn feature layer to the top of all layers."""
        draw_layer_index = self.find_layer_index(name="Drawn Features")
        if draw_layer_index > -1 and draw_layer_index < (len(self.layers) - 1):
            layers = list(self.layers)
            layers = (
                layers[0:draw_layer_index]
                + layers[(draw_layer_index + 1) :]
                + [layers[draw_layer_index]]
            )
            self.layers = layers

    def set_center(self, lon, lat, zoom=None):
        """Centers the map view at a given coordinates with the given zoom level.

        Args:
            lon (float): The longitude of the center, in degrees.
            lat (float): The latitude of the center, in degrees.
            zoom (int, optional): The zoom level, from 1 to 24. Defaults to None.
        """
        self.center = (lat, lon)
        if zoom is not None:
            self.zoom = zoom

        if is_arcpy():
            arc_zoom_to_extent(lon, lat, lon, lat)

    setCenter = set_center

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

    def zoom_to_me(self, zoom=14, add_marker=True):
        """Zoom to the current device location.

        Args:
            zoom (int, optional): Zoom level. Defaults to 14.
            add_marker (bool, optional): Whether to add a marker of the current device location. Defaults to True.
        """
        lat, lon = get_current_latlon()
        self.set_center(lon, lat, zoom)

        if add_marker:
            marker = ipyleaflet.Marker(
                location=(lat, lon),
                draggable=False,
                name="Device location",
            )
            self.add(marker)

    def zoom_to_bounds(self, bounds):
        """Zooms to a bounding box in the form of [minx, miny, maxx, maxy].

        Args:
            bounds (list | tuple): A list/tuple containing minx, miny, maxx, maxy values for the bounds.
        """
        #  The ipyleaflet fit_bounds method takes lat/lon bounds in the form [[south, west], [north, east]].
        self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    def zoom_to_gdf(self, gdf):
        """Zooms to the bounding box of a GeoPandas GeoDataFrame.

        Args:
            gdf (GeoDataFrame): A GeoPandas GeoDataFrame.
        """
        bounds = gdf.total_bounds
        self.zoom_to_bounds(bounds)

    def get_scale(self):
        """Returns the approximate pixel scale of the current map view, in meters.

        Returns:
            float: Map resolution in meters.
        """
        import math

        zoom_level = self.zoom
        # Reference: https://blogs.bing.com/maps/2006/02/25/map-control-zoom-levels-gt-resolution
        resolution = 156543.04 * math.cos(0) / math.pow(2, zoom_level)
        return resolution

    getScale = get_scale

    def get_bounds(self, asGeoJSON=False):
        """Returns the bounds of the current map view, as a list in the format [west, south, east, north] in degrees.

        Args:
            asGeoJSON (bool, optional): If true, returns map bounds as GeoJSON. Defaults to False.

        Returns:
            list | dict: A list in the format [west, south, east, north] in degrees.
        """
        bounds = self.bounds
        coords = [bounds[0][1], bounds[0][0], bounds[1][1], bounds[1][0]]

        if asGeoJSON:
            return ee.Geometry.BBox(
                bounds[0][1], bounds[0][0], bounds[1][1], bounds[1][0]
            ).getInfo()
        else:
            return coords

    getBounds = get_bounds

    def add_basemap(self, basemap="HYBRID", show=True, **kwargs):
        """Adds a basemap to the map.

        Args:
            basemap (str, optional): Can be one of string from basemaps. Defaults to 'HYBRID'.
            visible (bool, optional): Whether the basemap is visible or not. Defaults to True.
            **kwargs: Keyword arguments for the TileLayer.
        """
        import xyzservices

        try:
            layer_names = self.get_layer_names()

            if isinstance(basemap, xyzservices.TileProvider):
                name = basemap.name
                url = basemap.build_url()
                attribution = basemap.attribution
                if "max_zoom" in basemap.keys():
                    max_zoom = basemap["max_zoom"]
                else:
                    max_zoom = 22
                layer = ipyleaflet.TileLayer(
                    url=url,
                    name=name,
                    max_zoom=max_zoom,
                    attribution=attribution,
                    visible=show,
                    **kwargs,
                )
                self.add(layer)
                arc_add_layer(url, name)
            elif basemap in basemaps and basemaps[basemap].name not in layer_names:
                self.add(basemap)
                self.layers[-1].visible = show
                arc_add_layer(basemaps[basemap].url, basemap)
            elif basemap in basemaps and basemaps[basemap].name in layer_names:
                print(f"{basemap} has been already added before.")
            else:
                print(
                    "Basemap can only be one of the following:\n  {}".format(
                        "\n  ".join(basemaps.keys())
                    )
                )

        except Exception as e:
            raise ValueError(
                "Basemap can only be one of the following:\n  {}".format(
                    "\n  ".join(basemaps.keys())
                )
            )

    def get_layer_names(self):
        """Gets layer names as a list.

        Returns:
            list: A list of layer names.
        """
        layer_names = []

        for layer in list(self.layers):
            if len(layer.name) > 0:
                layer_names.append(layer.name)

        return layer_names

    def add_marker(self, location, **kwargs):
        """Adds a marker to the map. More info about marker at https://ipyleaflet.readthedocs.io/en/latest/api_reference/marker.html.

        Args:
            location (list | tuple): The location of the marker in the format of [lat, lng].

            **kwargs: Keyword arguments for the marker.
        """
        if isinstance(location, list):
            location = tuple(location)
        if isinstance(location, tuple):
            marker = ipyleaflet.Marker(location=location, **kwargs)
            self.add(marker)
        else:
            raise TypeError("The location must be a list or a tuple.")

    def find_layer(self, name):
        """Finds layer by name

        Args:
            name (str): Name of the layer to find.

        Returns:
            object: ipyleaflet layer object.
        """
        layers = self.layers

        for layer in layers:
            if layer.name == name:
                return layer

        return None

    def show_layer(self, name, show=True):
        """Shows or hides a layer on the map.

        Args:
            name (str): Name of the layer to show/hide.
            show (bool, optional): Whether to show or hide the layer. Defaults to True.
        """
        layer = self.find_layer(name)

        if layer is not None:
            layer.visible = show

    def find_layer_index(self, name):
        """Finds layer index by name

        Args:
            name (str): Name of the layer to find.

        Returns:
            int: Index of the layer with the specified name
        """
        layers = self.layers

        for index, layer in enumerate(layers):
            if layer.name == name:
                return index

        return -1

    def layer_opacity(self, name, opacity=1.0):
        """Changes layer opacity.

        Args:
            name (str): The name of the layer to change opacity.
            opacity (float, optional): The opacity value to set. Defaults to 1.0.
        """
        layer = self.find_layer(name)
        try:
            layer.opacity = opacity
        except Exception as e:
            raise Exception(e)

    def add_wms_layer(
        self,
        url,
        layers,
        name=None,
        attribution="",
        format="image/png",
        transparent=True,
        opacity=1.0,
        shown=True,
        **kwargs,
    ):
        """Add a WMS layer to the map.

        Args:
            url (str): The URL of the WMS web service.
            layers (str): Comma-separated list of WMS layers to show.
            name (str, optional): The layer name to use on the layer control. Defaults to None.
            attribution (str, optional): The attribution of the data layer. Defaults to ''.
            format (str, optional): WMS image format (use ‘image/png’ for layers with transparency). Defaults to 'image/png'.
            transparent (bool, optional): If True, the WMS service will return images with transparency. Defaults to True.
            opacity (float, optional): The opacity of the layer. Defaults to 1.0.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
        """

        if name is None:
            name = str(layers)

        try:
            wms_layer = ipyleaflet.WMSLayer(
                url=url,
                layers=layers,
                name=name,
                attribution=attribution,
                format=format,
                transparent=transparent,
                opacity=opacity,
                visible=shown,
                **kwargs,
            )
            self.add(wms_layer)

        except Exception as e:
            print("Failed to add the specified WMS TileLayer.")
            raise Exception(e)

    def add_tile_layer(
        self,
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        name="Untitled",
        attribution="",
        opacity=1.0,
        shown=True,
        **kwargs,
    ):
        """Adds a TileLayer to the map.

        Args:
            url (str, optional): The URL of the tile layer. Defaults to 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'.
            name (str, optional): The layer name to use for the layer. Defaults to 'Untitled'.
            attribution (str, optional): The attribution to use. Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
        """

        if "max_zoom" not in kwargs:
            kwargs["max_zoom"] = 100
        if "max_native_zoom" not in kwargs:
            kwargs["max_native_zoom"] = 100

        try:
            tile_layer = ipyleaflet.TileLayer(
                url=url,
                name=name,
                attribution=attribution,
                opacity=opacity,
                visible=shown,
                **kwargs,
            )
            self.add(tile_layer)

        except Exception as e:
            print("Failed to add the specified TileLayer.")
            raise Exception(e)

    def add_cog_layer(
        self,
        url,
        name="Untitled",
        attribution="",
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
            attribution (str, optional): The attribution to use. Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            bands (list, optional): A list of bands to use for the layer. Defaults to None.
            titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
            **kwargs: Arbitrary keyword arguments, including bidx, expression, nodata, unscale, resampling, rescale, color_formula, colormap, colormap_name, return_mask. See https://developmentseed.org/titiler/endpoints/cog/ and https://cogeotiff.github.io/rio-tiler/colormap/. To select a certain bands, use bidx=[1, 2, 3]
        """
        tile_url = cog_tile(url, bands, titiler_endpoint, **kwargs)
        bounds = cog_bounds(url, titiler_endpoint)
        self.add_tile_layer(tile_url, name, attribution, opacity, shown)
        self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

        if not hasattr(self, "cog_layer_dict"):
            self.cog_layer_dict = {}

        params = {
            "url": url,
            "titizer_endpoint": titiler_endpoint,
            "bounds": bounds,
            "type": "COG",
        }
        self.cog_layer_dict[name] = params

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
        attribution="",
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
            titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "https://planetarycomputer.microsoft.com/api/data/v1", "planetary-computer", "pc". Defaults to None.
            name (str, optional): The layer name to use for the layer. Defaults to 'STAC Layer'.
            attribution (str, optional): The attribution to use. Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
        """
        tile_url = stac_tile(
            url, collection, item, assets, bands, titiler_endpoint, **kwargs
        )
        bounds = stac_bounds(url, collection, item, titiler_endpoint)
        self.add_tile_layer(tile_url, name, attribution, opacity, shown)
        self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

        if not hasattr(self, "cog_layer_dict"):
            self.cog_layer_dict = {}

        if assets is None and bands is not None:
            assets = bands

        params = {
            "url": url,
            "collection": collection,
            "item": item,
            "assets": assets,
            "bounds": bounds,
            "titiler_endpoint": titiler_endpoint,
            "type": "STAC",
        }

        self.cog_layer_dict[name] = params

    def add_minimap(self, zoom=5, position="bottomright"):
        """Adds a minimap (overview) to the ipyleaflet map.

        Args:
            zoom (int, optional): Initial map zoom level. Defaults to 5.
            position (str, optional): Position of the minimap. Defaults to "bottomright".
        """
        minimap = ipyleaflet.Map(
            zoom_control=False,
            attribution_control=False,
            zoom=zoom,
            center=self.center,
            layers=[get_basemap("ROADMAP")],
        )
        minimap.layout.width = "150px"
        minimap.layout.height = "150px"
        ipyleaflet.link((minimap, "center"), (self, "center"))
        minimap_control = ipyleaflet.WidgetControl(widget=minimap, position=position)
        self.add(minimap_control)

    def marker_cluster(self):
        """Adds a marker cluster to the map and returns a list of ee.Feature, which can be accessed using Map.ee_marker_cluster.

        Returns:
            object: a list of ee.Feature
        """
        coordinates = []
        markers = []
        marker_cluster = ipyleaflet.MarkerCluster(name="Marker Cluster")
        self.last_click = []
        self.all_clicks = []
        self.ee_markers = []
        self.add(marker_cluster)

        def handle_interaction(**kwargs):
            latlon = kwargs.get("coordinates")
            if kwargs.get("type") == "click":
                coordinates.append(latlon)
                geom = ee.Geometry.Point(latlon[1], latlon[0])
                feature = ee.Feature(geom)
                self.ee_markers.append(feature)
                self.last_click = latlon
                self.all_clicks = coordinates
                markers.append(ipyleaflet.Marker(location=latlon))
                marker_cluster.markers = markers
            elif kwargs.get("type") == "mousemove":
                pass

        # cursor style: https://www.w3schools.com/cssref/pr_class_cursor.asp
        self.default_style = {"cursor": "crosshair"}
        self.on_interaction(handle_interaction)

    def set_plot_options(
        self,
        add_marker_cluster=False,
        sample_scale=None,
        plot_type=None,
        overlay=False,
        position="bottomright",
        min_width=None,
        max_width=None,
        min_height=None,
        max_height=None,
        **kwargs,
    ):
        """Sets plotting options.

        Args:
            add_marker_cluster (bool, optional): Whether to add a marker cluster. Defaults to False.
            sample_scale (float, optional):  A nominal scale in meters of the projection to sample in . Defaults to None.
            plot_type (str, optional): The plot type can be one of "None", "bar", "scatter" or "hist". Defaults to None.
            overlay (bool, optional): Whether to overlay plotted lines on the figure. Defaults to False.
            position (str, optional): Position of the control, can be ‘bottomleft’, ‘bottomright’, ‘topleft’, or ‘topright’. Defaults to 'bottomright'.
            min_width (int, optional): Min width of the widget (in pixels), if None it will respect the content size. Defaults to None.
            max_width (int, optional): Max width of the widget (in pixels), if None it will respect the content size. Defaults to None.
            min_height (int, optional): Min height of the widget (in pixels), if None it will respect the content size. Defaults to None.
            max_height (int, optional): Max height of the widget (in pixels), if None it will respect the content size. Defaults to None.

        """
        plot_options_dict = {}
        plot_options_dict["add_marker_cluster"] = add_marker_cluster
        plot_options_dict["sample_scale"] = sample_scale
        plot_options_dict["plot_type"] = plot_type
        plot_options_dict["overlay"] = overlay
        plot_options_dict["position"] = position
        plot_options_dict["min_width"] = min_width
        plot_options_dict["max_width"] = max_width
        plot_options_dict["min_height"] = min_height
        plot_options_dict["max_height"] = max_height

        for key in kwargs.keys():
            plot_options_dict[key] = kwargs[key]

        self.plot_options = plot_options_dict

        if add_marker_cluster and (self.plot_marker_cluster not in self.layers):
            self.add(self.plot_marker_cluster)

    def plot(
        self,
        x,
        y,
        plot_type=None,
        overlay=False,
        position="bottomright",
        min_width=None,
        max_width=None,
        min_height=None,
        max_height=None,
        **kwargs,
    ):
        """Creates a plot based on x-array and y-array data.

        Args:
            x (numpy.ndarray or list): The x-coordinates of the plotted line.
            y (numpy.ndarray or list): The y-coordinates of the plotted line.
            plot_type (str, optional): The plot type can be one of "None", "bar", "scatter" or "hist". Defaults to None.
            overlay (bool, optional): Whether to overlay plotted lines on the figure. Defaults to False.
            position (str, optional): Position of the control, can be ‘bottomleft’, ‘bottomright’, ‘topleft’, or ‘topright’. Defaults to 'bottomright'.
            min_width (int, optional): Min width of the widget (in pixels), if None it will respect the content size. Defaults to None.
            max_width (int, optional): Max width of the widget (in pixels), if None it will respect the content size. Defaults to None.
            min_height (int, optional): Min height of the widget (in pixels), if None it will respect the content size. Defaults to None.
            max_height (int, optional): Max height of the widget (in pixels), if None it will respect the content size. Defaults to None.

        """
        if self.plot_widget is not None:
            plot_widget = self.plot_widget
        else:
            plot_widget = widgets.Output(layout={"border": "1px solid black"})
            plot_control = ipyleaflet.WidgetControl(
                widget=plot_widget,
                position=position,
                min_width=min_width,
                max_width=max_width,
                min_height=min_height,
                max_height=max_height,
            )
            self.plot_widget = plot_widget
            self.plot_control = plot_control
            self.add(plot_control)

        if max_width is None:
            max_width = 500
        if max_height is None:
            max_height = 300

        if (plot_type is None) and ("markers" not in kwargs.keys()):
            kwargs["markers"] = "circle"

        with plot_widget:
            try:
                fig = plt.figure(1, **kwargs)
                if max_width is not None:
                    fig.layout.width = str(max_width) + "px"
                if max_height is not None:
                    fig.layout.height = str(max_height) + "px"

                plot_widget.clear_output(wait=True)
                if not overlay:
                    plt.clear()

                if plot_type is None:
                    if "marker" not in kwargs.keys():
                        kwargs["marker"] = "circle"
                    plt.plot(x, y, **kwargs)
                elif plot_type == "bar":
                    plt.bar(x, y, **kwargs)
                elif plot_type == "scatter":
                    plt.scatter(x, y, **kwargs)
                elif plot_type == "hist":
                    plt.hist(y, **kwargs)
                plt.show()

            except Exception as e:
                print("Failed to create plot.")
                raise Exception(e)

    def plot_demo(
        self,
        iterations=20,
        plot_type=None,
        overlay=False,
        position="bottomright",
        min_width=None,
        max_width=None,
        min_height=None,
        max_height=None,
        **kwargs,
    ):
        """A demo of interactive plotting using random pixel coordinates.

        Args:
            iterations (int, optional): How many iterations to run for the demo. Defaults to 20.
            plot_type (str, optional): The plot type can be one of "None", "bar", "scatter" or "hist". Defaults to None.
            overlay (bool, optional): Whether to overlay plotted lines on the figure. Defaults to False.
            position (str, optional): Position of the control, can be ‘bottomleft’, ‘bottomright’, ‘topleft’, or ‘topright’. Defaults to 'bottomright'.
            min_width (int, optional): Min width of the widget (in pixels), if None it will respect the content size. Defaults to None.
            max_width (int, optional): Max width of the widget (in pixels), if None it will respect the content size. Defaults to None.
            min_height (int, optional): Min height of the widget (in pixels), if None it will respect the content size. Defaults to None.
            max_height (int, optional): Max height of the widget (in pixels), if None it will respect the content size. Defaults to None.
        """

        import numpy as np
        import time

        if self.random_marker is not None:
            self.remove_layer(self.random_marker)

        image = ee.Image("LANDSAT/LE7_TOA_5YEAR/1999_2003").select([0, 1, 2, 3, 4, 6])
        self.addLayer(
            image,
            {"bands": ["B4", "B3", "B2"], "gamma": 1.4},
            "LANDSAT/LE7_TOA_5YEAR/1999_2003",
        )
        self.setCenter(-50.078877, 25.190030, 3)
        band_names = image.bandNames().getInfo()
        # band_count = len(band_names)

        latitudes = np.random.uniform(30, 48, size=iterations)
        longitudes = np.random.uniform(-121, -76, size=iterations)

        marker = ipyleaflet.Marker(location=(0, 0))
        self.random_marker = marker
        self.add(marker)

        for i in range(iterations):
            try:
                coordinate = ee.Geometry.Point([longitudes[i], latitudes[i]])
                dict_values = image.sample(coordinate).first().toDictionary().getInfo()
                band_values = list(dict_values.values())
                title = "{}/{}: Spectral signature at ({}, {})".format(
                    i + 1,
                    iterations,
                    round(latitudes[i], 2),
                    round(longitudes[i], 2),
                )
                marker.location = (latitudes[i], longitudes[i])
                self.plot(
                    band_names,
                    band_values,
                    plot_type=plot_type,
                    overlay=overlay,
                    min_width=min_width,
                    max_width=max_width,
                    min_height=min_height,
                    max_height=max_height,
                    title=title,
                    **kwargs,
                )
                time.sleep(0.3)
            except Exception as e:
                raise Exception(e)

    def plot_raster(
        self,
        ee_object=None,
        sample_scale=None,
        plot_type=None,
        overlay=False,
        position="bottomright",
        min_width=None,
        max_width=None,
        min_height=None,
        max_height=None,
        **kwargs,
    ):
        """Interactive plotting of Earth Engine data by clicking on the map.

        Args:
            ee_object (object, optional): The ee.Image or ee.ImageCollection to sample. Defaults to None.
            sample_scale (float, optional): A nominal scale in meters of the projection to sample in. Defaults to None.
            plot_type (str, optional): The plot type can be one of "None", "bar", "scatter" or "hist". Defaults to None.
            overlay (bool, optional): Whether to overlay plotted lines on the figure. Defaults to False.
            position (str, optional): Position of the control, can be ‘bottomleft’, ‘bottomright’, ‘topleft’, or ‘topright’. Defaults to 'bottomright'.
            min_width (int, optional): Min width of the widget (in pixels), if None it will respect the content size. Defaults to None.
            max_width (int, optional): Max width of the widget (in pixels), if None it will respect the content size. Defaults to None.
            min_height (int, optional): Min height of the widget (in pixels), if None it will respect the content size. Defaults to None.
            max_height (int, optional): Max height of the widget (in pixels), if None it will respect the content size. Defaults to None.

        """
        if self.plot_control is not None:
            del self.plot_widget
            if self.plot_control in self.controls:
                self.remove_control(self.plot_control)

        if self.random_marker is not None:
            self.remove_layer(self.random_marker)

        plot_widget = widgets.Output(layout={"border": "1px solid black"})
        plot_control = ipyleaflet.WidgetControl(
            widget=plot_widget,
            position=position,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
        )
        self.plot_widget = plot_widget
        self.plot_control = plot_control
        self.add(plot_control)

        self.default_style = {"cursor": "crosshair"}
        msg = "The plot function can only be used on ee.Image or ee.ImageCollection with more than one band."
        if (ee_object is None) and len(self.ee_raster_layers) > 0:
            ee_object = self.ee_raster_layers[-1]
            if isinstance(ee_object, ee.ImageCollection):
                ee_object = ee_object.mosaic()
        elif isinstance(ee_object, ee.ImageCollection):
            ee_object = ee_object.mosaic()
        elif not isinstance(ee_object, ee.Image):
            print(msg)
            return

        if sample_scale is None:
            sample_scale = self.getScale()

        if max_width is None:
            max_width = 500

        band_names = ee_object.bandNames().getInfo()

        coordinates = []
        markers = []
        marker_cluster = ipyleaflet.MarkerCluster(name="Marker Cluster")
        self.last_click = []
        self.all_clicks = []
        self.add(marker_cluster)

        def handle_interaction(**kwargs2):
            latlon = kwargs2.get("coordinates")

            if kwargs2.get("type") == "click":
                try:
                    coordinates.append(latlon)
                    self.last_click = latlon
                    self.all_clicks = coordinates
                    markers.append(ipyleaflet.Marker(location=latlon))
                    marker_cluster.markers = markers
                    self.default_style = {"cursor": "wait"}
                    xy = ee.Geometry.Point(latlon[::-1])
                    dict_values = (
                        ee_object.sample(xy, scale=sample_scale)
                        .first()
                        .toDictionary()
                        .getInfo()
                    )
                    band_values = list(dict_values.values())
                    self.plot(
                        band_names,
                        band_values,
                        plot_type=plot_type,
                        overlay=overlay,
                        min_width=min_width,
                        max_width=max_width,
                        min_height=min_height,
                        max_height=max_height,
                        **kwargs,
                    )
                    self.default_style = {"cursor": "crosshair"}
                except Exception as e:
                    if self.plot_widget is not None:
                        with self.plot_widget:
                            self.plot_widget.clear_output()
                            print("No data for the clicked location.")
                    else:
                        print(e)
                    self.default_style = {"cursor": "crosshair"}

        self.on_interaction(handle_interaction)

    def add_marker_cluster(self, event="click", add_marker=True):
        """Captures user inputs and add markers to the map.

        Args:
            event (str, optional): [description]. Defaults to 'click'.
            add_marker (bool, optional): If True, add markers to the map. Defaults to True.

        Returns:
            object: a marker cluster.
        """
        coordinates = []
        markers = []
        marker_cluster = ipyleaflet.MarkerCluster(name="Marker Cluster")
        self.last_click = []
        self.all_clicks = []
        if add_marker:
            self.add(marker_cluster)

        def handle_interaction(**kwargs):
            latlon = kwargs.get("coordinates")

            if event == "click" and kwargs.get("type") == "click":
                coordinates.append(latlon)
                self.last_click = latlon
                self.all_clicks = coordinates
                if add_marker:
                    markers.append(ipyleaflet.Marker(location=latlon))
                    marker_cluster.markers = markers
            elif kwargs.get("type") == "mousemove":
                pass

        # cursor style: https://www.w3schools.com/cssref/pr_class_cursor.asp
        self.default_style = {"cursor": "crosshair"}
        self.on_interaction(handle_interaction)

    def set_control_visibility(
        self, layerControl=True, fullscreenControl=True, latLngPopup=True
    ):
        """Sets the visibility of the controls on the map.

        Args:
            layerControl (bool, optional): Whether to show the control that allows the user to toggle layers on/off. Defaults to True.
            fullscreenControl (bool, optional): Whether to show the control that allows the user to make the map full-screen. Defaults to True.
            latLngPopup (bool, optional): Whether to show the control that pops up the Lat/lon when the user clicks on the map. Defaults to True.
        """
        pass

    setControlVisibility = set_control_visibility

    def add_layer_control(self):
        """Adds the layer control to the map."""
        if self.layer_control is None:
            layer_control = ipyleaflet.LayersControl(position="topright")
            self.layer_control = layer_control
            self.add(layer_control)

    addLayerControl = add_layer_control

    def split_map(
        self,
        left_layer="HYBRID",
        right_layer="ROADMAP",
        zoom_control=True,
        fullscreen_control=True,
        layer_control=True,
        add_close_button=False,
        left_label=None,
        right_label=None,
        left_position="bottomleft",
        right_position="bottomright",
        widget_layout=None,
        **kwargs,
    ):
        """Adds split map.

        Args:
            left_layer (str, optional): The layer tile layer. Defaults to 'HYBRID'.
            right_layer (str, optional): The right tile layer. Defaults to 'ROADMAP'.
            zoom_control (bool, optional): Whether to show the zoom control. Defaults to True.
            fullscreen_control (bool, optional): Whether to show the full screen control. Defaults to True.
            layer_control (bool, optional): Whether to show the layer control. Defaults to True.
            add_close_button (bool, optional): Whether to add a close button. Defaults to False.
            left_label (str, optional): The label for the left map. Defaults to None.
            right_label (str, optional): The label for the right map. Defaults to None.
            left_position (str, optional): The position of the left label. Defaults to 'bottomleft'.
            right_position (str, optional): The position of the right label. Defaults to 'bottomright'.
            widget_layout (str, optional): The layout of the label widget, such as ipywidgets.Layout(padding="0px 4px 0px 4px"). Defaults to None.
            kwargs: Other arguments for ipyleaflet.TileLayer.
        """
        if "max_zoom" not in kwargs:
            kwargs["max_zoom"] = 100
        if "max_native_zoom" not in kwargs:
            kwargs["max_native_zoom"] = 100
        try:
            controls = self.controls
            layers = self.layers
            self.clear_controls()

            if zoom_control:
                self.add(ipyleaflet.ZoomControl())
            if fullscreen_control:
                self.add(ipyleaflet.FullScreenControl())

            if left_label is not None:
                left_name = left_label
            else:
                left_name = "Left Layer"

            if right_label is not None:
                right_name = right_label
            else:
                right_name = "Right Layer"

            if "attribution" not in kwargs:
                kwargs["attribution"] = " "

            if left_layer in basemaps.keys():
                left_layer = get_basemap(left_layer)
            elif isinstance(left_layer, str):
                if left_layer.startswith("http") and left_layer.endswith(".tif"):
                    url = cog_tile(left_layer)
                    left_layer = ipyleaflet.TileLayer(
                        url=url,
                        name=left_name,
                        **kwargs,
                    )
                else:
                    left_layer = ipyleaflet.TileLayer(
                        url=left_layer,
                        name=left_name,
                        **kwargs,
                    )
            elif isinstance(left_layer, ipyleaflet.TileLayer):
                pass
            else:
                raise ValueError(
                    f"left_layer must be one of the following: {', '.join(basemaps.keys())} or a string url to a tif file."
                )

            if right_layer in basemaps.keys():
                right_layer = get_basemap(right_layer)
            elif isinstance(right_layer, str):
                if right_layer.startswith("http") and right_layer.endswith(".tif"):
                    url = cog_tile(right_layer)
                    right_layer = ipyleaflet.TileLayer(
                        url=url,
                        name=right_name,
                        **kwargs,
                    )
                else:
                    right_layer = ipyleaflet.TileLayer(
                        url=right_layer,
                        name=right_name,
                        **kwargs,
                    )
            elif isinstance(right_layer, ipyleaflet.TileLayer):
                pass
            else:
                raise ValueError(
                    f"right_layer must be one of the following: {', '.join(basemaps.keys())} or a string url to a tif file."
                )

            control = ipyleaflet.SplitMapControl(
                left_layer=left_layer, right_layer=right_layer
            )

            self.add(control)
            self.dragging = False

            if left_label is not None:
                if widget_layout is None:
                    widget_layout = widgets.Layout(padding="0px 4px 0px 4px")
                left_widget = widgets.HTML(value=left_label, layout=widget_layout)

                left_control = ipyleaflet.WidgetControl(
                    widget=left_widget, position=left_position
                )
                self.add(left_control)

            if right_label is not None:
                if widget_layout is None:
                    widget_layout = widgets.Layout(padding="0px 4px 0px 4px")
                right_widget = widgets.HTML(value=right_label, layout=widget_layout)
                right_control = ipyleaflet.WidgetControl(
                    widget=right_widget, position=right_position
                )
                self.add(right_control)

            close_button = widgets.ToggleButton(
                value=False,
                tooltip="Close split-panel map",
                icon="times",
                layout=widgets.Layout(
                    height="28px", width="28px", padding="0px 0px 0px 4px"
                ),
            )

            def close_btn_click(change):
                if change["new"]:
                    self.controls = controls
                    self.layers = layers[:-1]
                    self.add(layers[-1])

                if left_label is not None:
                    self.remove_control(left_control)

                if right_label is not None:
                    self.remove_control(right_control)

            close_button.observe(close_btn_click, "value")
            close_control = ipyleaflet.WidgetControl(
                widget=close_button, position="bottomright"
            )

            if add_close_button:
                self.add(close_control)

            if layer_control:
                self.addLayerControl()

        except Exception as e:
            print("The provided layers are invalid!")
            raise ValueError(e)

    def ts_inspector(
        self,
        left_ts,
        left_names=None,
        left_vis={},
        left_index=0,
        right_ts=None,
        right_names=None,
        right_vis=None,
        right_index=-1,
        width="130px",
        date_format="YYYY-MM-dd",
        add_close_button=False,
        **kwargs,
    ):
        """Creates a split-panel map for inspecting timeseries images.

        Args:
            left_ts (object): An ee.ImageCollection to show on the left panel.
            left_names (list): A list of names to show under the left dropdown.
            left_vis (dict, optional): Visualization parameters for the left layer. Defaults to {}.
            left_index (int, optional): The index of the left layer to show. Defaults to 0.
            right_ts (object): An ee.ImageCollection to show on the right panel.
            right_names (list): A list of names to show under the right dropdown.
            right_vis (dict, optional): Visualization parameters for the right layer. Defaults to {}.
            right_index (int, optional): The index of the right layer to show. Defaults to -1.
            width (str, optional): The width of the dropdown list. Defaults to '130px'.
            date_format (str, optional): The date format to show in the dropdown. Defaults to 'YYYY-MM-dd'.
            add_close_button (bool, optional): Whether to show the close button. Defaults to False.
        """
        controls = self.controls
        layers = self.layers

        if left_names is None:
            left_names = image_dates(left_ts, date_format=date_format).getInfo()

        if right_ts is None:
            right_ts = left_ts

        if right_names is None:
            right_names = left_names

        if right_vis is None:
            right_vis = left_vis

        left_count = int(left_ts.size().getInfo())
        right_count = int(right_ts.size().getInfo())

        if left_count != len(left_names):
            print(
                "The number of images in left_ts must match the number of layer names in left_names."
            )
            return
        if right_count != len(right_names):
            print(
                "The number of images in right_ts must match the number of layer names in right_names."
            )
            return

        left_layer = ipyleaflet.TileLayer(
            url="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
            attribution="Google",
            name="Google Maps",
        )
        right_layer = ipyleaflet.TileLayer(
            url="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
            attribution="Google",
            name="Google Maps",
        )

        self.clear_controls()
        left_dropdown = widgets.Dropdown(options=left_names, value=None)
        right_dropdown = widgets.Dropdown(options=right_names, value=None)
        left_dropdown.layout.max_width = width
        right_dropdown.layout.max_width = width

        left_control = ipyleaflet.WidgetControl(
            widget=left_dropdown, position="topleft"
        )
        right_control = ipyleaflet.WidgetControl(
            widget=right_dropdown, position="topright"
        )

        self.add(left_control)
        self.add(right_control)

        self.add(ipyleaflet.ZoomControl(position="topleft"))
        self.add(ipyleaflet.ScaleControl(position="bottomleft"))
        self.add(ipyleaflet.FullScreenControl())

        def left_dropdown_change(change):
            left_dropdown_index = left_dropdown.index
            if left_dropdown_index is not None and left_dropdown_index >= 0:
                try:
                    if isinstance(left_ts, ee.ImageCollection):
                        left_image = left_ts.toList(left_ts.size()).get(
                            left_dropdown_index
                        )
                    elif isinstance(left_ts, ee.List):
                        left_image = left_ts.get(left_dropdown_index)
                    else:
                        print("The left_ts argument must be an ImageCollection.")
                        return

                    if isinstance(left_image, ee.ImageCollection):
                        left_image = ee.Image(left_image.mosaic())
                    elif isinstance(left_image, ee.Image):
                        pass
                    else:
                        left_image = ee.Image(left_image)

                    left_image = ee_tile_layer(
                        left_image, left_vis, left_names[left_dropdown_index]
                    )
                    left_layer.url = left_image.url
                except Exception as e:
                    print(e)
                    return

        left_dropdown.observe(left_dropdown_change, names="value")

        def right_dropdown_change(change):
            right_dropdown_index = right_dropdown.index
            if right_dropdown_index is not None and right_dropdown_index >= 0:
                try:
                    if isinstance(right_ts, ee.ImageCollection):
                        right_image = right_ts.toList(left_ts.size()).get(
                            right_dropdown_index
                        )
                    elif isinstance(right_ts, ee.List):
                        right_image = right_ts.get(right_dropdown_index)
                    else:
                        print("The left_ts argument must be an ImageCollection.")
                        return

                    if isinstance(right_image, ee.ImageCollection):
                        right_image = ee.Image(right_image.mosaic())
                    elif isinstance(right_image, ee.Image):
                        pass
                    else:
                        right_image = ee.Image(right_image)

                    right_image = ee_tile_layer(
                        right_image,
                        right_vis,
                        right_names[right_dropdown_index],
                    )
                    right_layer.url = right_image.url
                except Exception as e:
                    print(e)
                    return

        right_dropdown.observe(right_dropdown_change, names="value")

        if left_index is not None:
            left_dropdown.value = left_names[left_index]
        if right_index is not None:
            right_dropdown.value = right_names[right_index]

        close_button = widgets.ToggleButton(
            value=False,
            tooltip="Close the tool",
            icon="times",
            # button_style="primary",
            layout=widgets.Layout(
                height="28px", width="28px", padding="0px 0px 0px 4px"
            ),
        )

        def close_btn_click(change):
            if change["new"]:
                self.controls = controls
                self.clear_layers()
                self.layers = layers

        close_button.observe(close_btn_click, "value")
        close_control = ipyleaflet.WidgetControl(
            widget=close_button, position="bottomright"
        )

        try:
            split_control = ipyleaflet.SplitMapControl(
                left_layer=left_layer, right_layer=right_layer
            )
            self.add(split_control)
            self.dragging = False

            if add_close_button:
                self.add(close_control)

        except Exception as e:
            raise Exception(e)

    def basemap_demo(self):
        """A demo for using geemap basemaps."""
        dropdown = widgets.Dropdown(
            options=list(basemaps.keys()),
            value="HYBRID",
            description="Basemaps",
        )

        def on_click(change):
            basemap_name = change["new"]
            old_basemap = self.layers[-1]
            self.substitute_layer(old_basemap, get_basemap(basemaps[basemap_name]))

        dropdown.observe(on_click, "value")
        basemap_control = ipyleaflet.WidgetControl(widget=dropdown, position="topright")
        self.add(basemap_control)

    def add_legend(
        self,
        title="Legend",
        legend_dict=None,
        labels=None,
        colors=None,
        position="bottomright",
        builtin_legend=None,
        layer_name=None,
        **kwargs,
    ):
        """Adds a customized basemap to the map.

        Args:
            title (str, optional): Title of the legend. Defaults to 'Legend'.
            legend_dict (dict, optional): A dictionary containing legend items as keys and color as values. If provided, legend_keys and legend_colors will be ignored. Defaults to None.
            labels (list, optional): A list of legend keys. Defaults to None.
            colors (list, optional): A list of legend colors. Defaults to None.
            position (str, optional): Position of the legend. Defaults to 'bottomright'.
            builtin_legend (str, optional): Name of the builtin legend to add to the map. Defaults to None.
            layer_name (str, optional): Layer name of the legend to be associated with. Defaults to None.

        """
        from IPython.display import display
        import pkg_resources
        from .legends import builtin_legends

        pkg_dir = os.path.dirname(
            pkg_resources.resource_filename("geemap", "geemap.py")
        )
        legend_template = os.path.join(pkg_dir, "data/template/legend.html")

        if "min_width" not in kwargs.keys():
            min_width = None
        if "max_width" not in kwargs.keys():
            max_width = None
        else:
            max_width = kwargs["max_width"]
        if "min_height" not in kwargs.keys():
            min_height = None
        else:
            min_height = kwargs["min_height"]
        if "max_height" not in kwargs.keys():
            max_height = None
        else:
            max_height = kwargs["max_height"]
        if "height" not in kwargs.keys():
            height = None
        else:
            height = kwargs["height"]
        if "width" not in kwargs.keys():
            width = None
        else:
            width = kwargs["width"]

        if width is None:
            max_width = "300px"
        if height is None:
            max_height = "400px"

        if not os.path.exists(legend_template):
            print("The legend template does not exist.")
            return

        if labels is not None:
            if not isinstance(labels, list):
                print("The legend keys must be a list.")
                return
        else:
            labels = ["One", "Two", "Three", "Four", "etc"]

        if colors is not None:
            if not isinstance(colors, list):
                print("The legend colors must be a list.")
                return
            elif all(isinstance(item, tuple) for item in colors):
                try:
                    colors = [rgb_to_hex(x) for x in colors]
                except Exception as e:
                    print(e)
            elif all((item.startswith("#") and len(item) == 7) for item in colors):
                pass
            elif all((len(item) == 6) for item in colors):
                pass
            else:
                print("The legend colors must be a list of tuples.")
                return
        else:
            colors = [
                "#8DD3C7",
                "#FFFFB3",
                "#BEBADA",
                "#FB8072",
                "#80B1D3",
            ]

        if len(labels) != len(colors):
            print("The legend keys and values must be the same length.")
            return

        allowed_builtin_legends = builtin_legends.keys()
        if builtin_legend is not None:
            if builtin_legend not in allowed_builtin_legends:
                print(
                    "The builtin legend must be one of the following: {}".format(
                        ", ".join(allowed_builtin_legends)
                    )
                )
                return
            else:
                legend_dict = builtin_legends[builtin_legend]
                labels = list(legend_dict.keys())
                colors = list(legend_dict.values())

        if legend_dict is not None:
            if not isinstance(legend_dict, dict):
                print("The legend dict must be a dictionary.")
                return
            else:
                labels = list(legend_dict.keys())
                colors = list(legend_dict.values())
                if all(isinstance(item, tuple) for item in colors):
                    try:
                        colors = [rgb_to_hex(x) for x in colors]
                    except Exception as e:
                        print(e)

        allowed_positions = [
            "topleft",
            "topright",
            "bottomleft",
            "bottomright",
        ]
        if position not in allowed_positions:
            print(
                "The position must be one of the following: {}".format(
                    ", ".join(allowed_positions)
                )
            )
            return

        header = []
        content = []
        footer = []

        with open(legend_template) as f:
            lines = f.readlines()
            lines[3] = lines[3].replace("Legend", title)
            header = lines[:6]
            footer = lines[11:]

        for index, key in enumerate(labels):
            color = colors[index]
            if not color.startswith("#"):
                color = "#" + color
            item = "      <li><span style='background:{};'></span>{}</li>\n".format(
                color, key
            )
            content.append(item)

        legend_html = header + content + footer
        legend_text = "".join(legend_html)

        try:
            legend_output_widget = widgets.Output(
                layout={
                    # "border": "1px solid black",
                    "max_width": max_width,
                    "min_width": min_width,
                    "max_height": max_height,
                    "min_height": min_height,
                    "height": height,
                    "width": width,
                    "overflow": "scroll",
                }
            )
            legend_control = ipyleaflet.WidgetControl(
                widget=legend_output_widget, position=position
            )
            legend_widget = widgets.HTML(value=legend_text)
            with legend_output_widget:
                display(legend_widget)

            self.legend_widget = legend_output_widget
            self.legend_control = legend_control
            self.add(legend_control)

            if not hasattr(self, "legends"):
                setattr(self, "legends", [legend_control])
            else:
                self.legends.append(legend_control)

            if layer_name in self.ee_layer_names:
                self.ee_layer_dict[layer_name]["legend"] = legend_control

        except Exception as e:
            raise Exception(e)

    def add_colorbar(
        self,
        vis_params=None,
        cmap="gray",
        discrete=False,
        label=None,
        orientation="horizontal",
        position="bottomright",
        transparent_bg=False,
        layer_name=None,
        font_size=9,
        axis_off=False,
        **kwargs,
    ):
        """Add a matplotlib colorbar to the map

        Args:
            vis_params (dict): Visualization parameters as a dictionary. See https://developers.google.com/earth-engine/guides/image_visualization for options.
            cmap (str, optional): Matplotlib colormap. Defaults to "gray". See https://matplotlib.org/3.3.4/tutorials/colors/colormaps.html#sphx-glr-tutorials-colors-colormaps-py for options.
            discrete (bool, optional): Whether to create a discrete colorbar. Defaults to False.
            label (str, optional): Label for the colorbar. Defaults to None.
            orientation (str, optional): Orientation of the colorbar, such as "vertical" and "horizontal". Defaults to "horizontal".
            position (str, optional): Position of the colorbar on the map. It can be one of: topleft, topright, bottomleft, and bottomright. Defaults to "bottomright".
            transparent_bg (bool, optional): Whether to use transparent background. Defaults to False.
            layer_name (str, optional): The layer name associated with the colorbar. Defaults to None.
            font_size (int, optional): Font size for the colorbar. Defaults to 9.
            axis_off (bool, optional): Whether to turn off the axis. Defaults to False.

        Raises:
            TypeError: If the vis_params is not a dictionary.
            ValueError: If the orientation is not either horizontal or vertical.
            ValueError: If the provided min value is not scalar type.
            ValueError: If the provided max value is not scalar type.
            ValueError: If the provided opacity value is not scalar type.
            ValueError: If cmap or palette is not provided.
        """
        import matplotlib as mpl
        import matplotlib.pyplot as plt
        import numpy as np

        if isinstance(vis_params, list):
            vis_params = {"palette": vis_params}
        elif isinstance(vis_params, tuple):
            vis_params = {"palette": list(vis_params)}
        elif vis_params is None:
            vis_params = {}

        if "colors" in kwargs and isinstance(kwargs["colors"], list):
            vis_params["palette"] = kwargs["colors"]

        if "colors" in kwargs and isinstance(kwargs["colors"], tuple):
            vis_params["palette"] = list(kwargs["colors"])

        if "vmin" in kwargs:
            vis_params["min"] = kwargs["vmin"]
            del kwargs["vmin"]

        if "vmax" in kwargs:
            vis_params["max"] = kwargs["vmax"]
            del kwargs["vmax"]

        if "caption" in kwargs:
            label = kwargs["caption"]
            del kwargs["caption"]

        if not isinstance(vis_params, dict):
            raise TypeError("The vis_params must be a dictionary.")

        if orientation not in ["horizontal", "vertical"]:
            raise ValueError("The orientation must be either horizontal or vertical.")

        if orientation == "horizontal":
            width, height = 3.0, 0.3
        else:
            width, height = 0.3, 3.0

        if "width" in kwargs:
            width = kwargs["width"]
            kwargs.pop("width")

        if "height" in kwargs:
            height = kwargs["height"]
            kwargs.pop("height")

        vis_keys = list(vis_params.keys())

        if "min" in vis_params:
            vmin = vis_params["min"]
            if type(vmin) not in (int, float):
                raise ValueError("The provided min value must be scalar type.")
        else:
            vmin = 0

        if "max" in vis_params:
            vmax = vis_params["max"]
            if type(vmax) not in (int, float):
                raise ValueError("The provided max value must be scalar type.")
        else:
            vmax = 1

        if "opacity" in vis_params:
            alpha = vis_params["opacity"]
            if type(alpha) not in (int, float):
                raise ValueError("The provided opacity value must be type scalar.")
        elif "alpha" in kwargs:
            alpha = kwargs["alpha"]
        else:
            alpha = 1

        if cmap is not None:
            cmap = mpl.pyplot.get_cmap(cmap)
            norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

        if "palette" in vis_keys:
            hexcodes = to_hex_colors(check_cmap(vis_params["palette"]))
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
            cmap = mpl.pyplot.get_cmap(cmap)
            norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

        else:
            raise ValueError(
                'cmap keyword or "palette" key in vis_params must be provided.'
            )

        _, ax = plt.subplots(figsize=(width, height))
        cb = mpl.colorbar.ColorbarBase(
            ax, norm=norm, alpha=alpha, cmap=cmap, orientation=orientation, **kwargs
        )

        if label is not None:
            cb.set_label(label, fontsize=font_size)
        elif "bands" in vis_keys:
            cb.set_label(vis_params["bands"], fontsize=font_size)

        if axis_off:
            ax.set_axis_off()
        ax.tick_params(labelsize=font_size)

        output = widgets.Output()
        colormap_ctrl = ipyleaflet.WidgetControl(
            widget=output,
            position=position,
            transparent_bg=transparent_bg,
        )
        with output:
            output.clear_output()
            plt.show()

        self.colorbar = colormap_ctrl
        if layer_name in self.ee_layer_names:
            if "colorbar" in self.ee_layer_dict[layer_name]:
                self.remove_control(self.ee_layer_dict[layer_name]["colorbar"])
            self.ee_layer_dict[layer_name]["colorbar"] = colormap_ctrl
        if not hasattr(self, "colorbars"):
            self.colorbars = [colormap_ctrl]
        else:
            self.colorbars.append(colormap_ctrl)

        self.add(colormap_ctrl)

    def add_colorbar_branca(
        self,
        colors,
        vmin=0,
        vmax=1.0,
        index=None,
        caption="",
        categorical=False,
        step=None,
        height="45px",
        transparent_bg=False,
        position="bottomright",
        layer_name=None,
        **kwargs,
    ):
        """Add a branca colorbar to the map.

        Args:
            colors (list): The set of colors to be used for interpolation. Colors can be provided in the form: * tuples of RGBA ints between 0 and 255 (e.g: (255, 255, 0) or (255, 255, 0, 255)) * tuples of RGBA floats between 0. and 1. (e.g: (1.,1.,0.) or (1., 1., 0., 1.)) * HTML-like string (e.g: “#ffff00) * a color name or shortcut (e.g: “y” or “yellow”)
            vmin (int, optional): The minimal value for the colormap. Values lower than vmin will be bound directly to colors[0].. Defaults to 0.
            vmax (float, optional): The maximal value for the colormap. Values higher than vmax will be bound directly to colors[-1]. Defaults to 1.0.
            index (list, optional):The values corresponding to each color. It has to be sorted, and have the same length as colors. If None, a regular grid between vmin and vmax is created.. Defaults to None.
            caption (str, optional): The caption for the colormap. Defaults to "".
            categorical (bool, optional): Whether or not to create a categorical colormap. Defaults to False.
            step (int, optional): The step to split the LinearColormap into a StepColormap. Defaults to None.
            height (str, optional): The height of the colormap widget. Defaults to "45px".
            transparent_bg (bool, optional): Whether to use transparent background for the colormap widget. Defaults to True.
            position (str, optional): The position for the colormap widget. Defaults to "bottomright".
            layer_name (str, optional): Layer name of the colorbar to be associated with. Defaults to None.

        """
        from branca.colormap import LinearColormap

        output = widgets.Output()
        output.layout.height = height

        if "width" in kwargs.keys():
            output.layout.width = kwargs["width"]

        if isinstance(colors, Box):
            try:
                colors = list(colors["default"])
            except Exception as e:
                print("The provided color list is invalid.")
                raise Exception(e)

        if all(len(color) == 6 for color in colors):
            colors = ["#" + color for color in colors]

        colormap = LinearColormap(
            colors=colors, index=index, vmin=vmin, vmax=vmax, caption=caption
        )

        if categorical:
            if step is not None:
                colormap = colormap.to_step(step)
            elif index is not None:
                colormap = colormap.to_step(len(index) - 1)
            else:
                colormap = colormap.to_step(3)

        colormap_ctrl = ipyleaflet.WidgetControl(
            widget=output,
            position=position,
            transparent_bg=transparent_bg,
            **kwargs,
        )
        with output:
            output.clear_output()
            display(colormap)

        self.colorbar = colormap_ctrl
        self.add(colormap_ctrl)

        if not hasattr(self, "colorbars"):
            self.colorbars = [colormap_ctrl]
        else:
            self.colorbars.append(colormap_ctrl)

        if layer_name in self.ee_layer_names:
            self.ee_layer_dict[layer_name]["colorbar"] = colormap_ctrl

    def remove_colorbar(self):
        """Remove colorbar from the map."""
        if self.colorbar is not None:
            self.remove_control(self.colorbar)

    def remove_colorbars(self):
        """Remove all colorbars from the map."""
        if hasattr(self, "colorbars"):
            for colorbar in self.colorbars:
                if colorbar in self.controls:
                    self.remove_control(colorbar)

    def remove_legend(self):
        """Remove legend from the map."""
        if self.legend is not None:
            if self.legend in self.controls:
                self.remove_control(self.legend)

    def remove_legends(self):
        """Remove all legends from the map."""
        if hasattr(self, "legends"):
            for legend in self.legends:
                if legend in self.controls:
                    self.remove_control(legend)

    def image_overlay(self, url, bounds, name):
        """Overlays an image from the Internet or locally on the map.

        Args:
            url (str): http URL or local file path to the image.
            bounds (tuple): bounding box of the image in the format of (lower_left(lat, lon), upper_right(lat, lon)), such as ((13, -130), (32, -100)).
            name (str): name of the layer to show on the layer control.
        """
        from base64 import b64encode
        from io import BytesIO

        from PIL import Image, ImageSequence

        try:
            if not url.startswith("http"):
                if not os.path.exists(url):
                    print("The provided file does not exist.")
                    return

                ext = os.path.splitext(url)[1][1:]  # file extension
                image = Image.open(url)

                f = BytesIO()
                if ext.lower() == "gif":
                    frames = []
                    # Loop over each frame in the animated image
                    for frame in ImageSequence.Iterator(image):
                        frame = frame.convert("RGBA")
                        b = BytesIO()
                        frame.save(b, format="gif")
                        frame = Image.open(b)
                        frames.append(frame)
                    frames[0].save(
                        f,
                        format="GIF",
                        save_all=True,
                        append_images=frames[1:],
                        loop=0,
                    )
                else:
                    image.save(f, ext)

                data = b64encode(f.getvalue())
                data = data.decode("ascii")
                url = "data:image/{};base64,".format(ext) + data
            img = ipyleaflet.ImageOverlay(url=url, bounds=bounds, name=name)
            self.add(img)
        except Exception as e:
            print(e)

    def video_overlay(self, url, bounds, name="Video"):
        """Overlays a video from the Internet on the map.

        Args:
            url (str): http URL of the video, such as "https://www.mapbox.com/bites/00188/patricia_nasa.webm"
            bounds (tuple): bounding box of the video in the format of (lower_left(lat, lon), upper_right(lat, lon)), such as ((13, -130), (32, -100)).
            name (str): name of the layer to show on the layer control.
        """
        try:
            video = ipyleaflet.VideoOverlay(url=url, bounds=bounds, name=name)
            self.add(video)
        except Exception as e:
            print(e)

    def add_landsat_ts_gif(
        self,
        layer_name="Timelapse",
        roi=None,
        label=None,
        start_year=1984,
        end_year=2021,
        start_date="06-10",
        end_date="09-20",
        bands=["NIR", "Red", "Green"],
        vis_params=None,
        dimensions=768,
        frames_per_second=10,
        font_size=30,
        font_color="white",
        add_progress_bar=True,
        progress_bar_color="white",
        progress_bar_height=5,
        out_gif=None,
        download=False,
        apply_fmask=True,
        nd_bands=None,
        nd_threshold=0,
        nd_palette=["black", "blue"],
    ):
        """Adds a Landsat timelapse to the map.

        Args:
            layer_name (str, optional): Layer name to show under the layer control. Defaults to 'Timelapse'.
            roi (object, optional): Region of interest to create the timelapse. Defaults to None.
            label (str, optional): A label to show on the GIF, such as place name. Defaults to None.
            start_year (int, optional): Starting year for the timelapse. Defaults to 1984.
            end_year (int, optional): Ending year for the timelapse. Defaults to 2021.
            start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '06-10'.
            end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '09-20'.
            bands (list, optional): Three bands selected from ['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2', 'pixel_qa']. Defaults to ['NIR', 'Red', 'Green'].
            vis_params (dict, optional): Visualization parameters. Defaults to None.
            dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
            frames_per_second (int, optional): Animation speed. Defaults to 10.
            font_size (int, optional): Font size of the animated text and label. Defaults to 30.
            font_color (str, optional): Font color of the animated text and label. Defaults to 'black'.
            add_progress_bar (bool, optional): Whether to add a progress bar at the bottom of the GIF. Defaults to True.
            progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
            progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.
            out_gif (str, optional): File path to the output animated GIF. Defaults to None.
            download (bool, optional): Whether to download the gif. Defaults to False.
            apply_fmask (bool, optional): Whether to apply Fmask (Function of mask) for automated clouds, cloud shadows, snow, and water masking.
            nd_bands (list, optional): A list of names specifying the bands to use, e.g., ['Green', 'SWIR1']. The normalized difference is computed as (first − second) / (first + second). Note that negative input values are forced to 0 so that the result is confined to the range (-1, 1).
            nd_threshold (float, optional): The threshold for extacting pixels from the normalized difference band.
            nd_palette (str, optional): The color palette to use for displaying the normalized difference band.

        """
        try:
            if roi is None:
                if self.draw_last_feature is not None:
                    feature = self.draw_last_feature
                    roi = feature.geometry()
                else:
                    roi = ee.Geometry.Polygon(
                        [
                            [
                                [-115.471773, 35.892718],
                                [-115.471773, 36.409454],
                                [-114.271283, 36.409454],
                                [-114.271283, 35.892718],
                                [-115.471773, 35.892718],
                            ]
                        ],
                        None,
                        False,
                    )
            elif isinstance(roi, ee.Feature) or isinstance(roi, ee.FeatureCollection):
                roi = roi.geometry()
            elif isinstance(roi, ee.Geometry):
                pass
            else:
                print("The provided roi is invalid. It must be an ee.Geometry")
                return

            geojson = ee_to_geojson(roi)
            bounds = minimum_bounding_box(geojson)
            geojson = adjust_longitude(geojson)
            roi = ee.Geometry(geojson)

            in_gif = landsat_timelapse(
                roi=roi,
                out_gif=out_gif,
                start_year=start_year,
                end_year=end_year,
                start_date=start_date,
                end_date=end_date,
                bands=bands,
                vis_params=vis_params,
                dimensions=dimensions,
                frames_per_second=frames_per_second,
                apply_fmask=apply_fmask,
                nd_bands=nd_bands,
                nd_threshold=nd_threshold,
                nd_palette=nd_palette,
                font_size=font_size,
                font_color=font_color,
                progress_bar_color=progress_bar_color,
                progress_bar_height=progress_bar_height,
            )
            in_nd_gif = in_gif.replace(".gif", "_nd.gif")

            if nd_bands is not None:
                add_text_to_gif(
                    in_nd_gif,
                    in_nd_gif,
                    xy=("2%", "2%"),
                    text_sequence=start_year,
                    font_size=font_size,
                    font_color=font_color,
                    duration=int(1000 / frames_per_second),
                    add_progress_bar=add_progress_bar,
                    progress_bar_color=progress_bar_color,
                    progress_bar_height=progress_bar_height,
                )

            if label is not None:
                add_text_to_gif(
                    in_gif,
                    in_gif,
                    xy=("2%", "90%"),
                    text_sequence=label,
                    font_size=font_size,
                    font_color=font_color,
                    duration=int(1000 / frames_per_second),
                    add_progress_bar=add_progress_bar,
                    progress_bar_color=progress_bar_color,
                    progress_bar_height=progress_bar_height,
                )
                # if nd_bands is not None:
                #     add_text_to_gif(in_nd_gif, in_nd_gif, xy=('2%', '90%'), text_sequence=label,
                #                     font_size=font_size, font_color=font_color, duration=int(1000 / frames_per_second), add_progress_bar=add_progress_bar, progress_bar_color=progress_bar_color, progress_bar_height=progress_bar_height)

            if is_tool("ffmpeg"):
                reduce_gif_size(in_gif)
                if nd_bands is not None:
                    reduce_gif_size(in_nd_gif)

            print("Adding GIF to the map ...")
            self.image_overlay(url=in_gif, bounds=bounds, name=layer_name)
            if nd_bands is not None:
                self.image_overlay(
                    url=in_nd_gif, bounds=bounds, name=layer_name + " ND"
                )
            print("The timelapse has been added to the map.")

            if download:
                link = create_download_link(
                    in_gif,
                    title="Click here to download the Landsat timelapse: ",
                )
                display(link)
                if nd_bands is not None:
                    link2 = create_download_link(
                        in_nd_gif,
                        title="Click here to download the Normalized Difference Index timelapse: ",
                    )
                    display(link2)

        except Exception as e:
            raise Exception(e)

    def to_html(
        self,
        filename=None,
        title="My Map",
        width="100%",
        height="880px",
        add_layer_control=True,
        **kwargs,
    ):
        """Saves the map as an HTML file.

        Args:
            filename (str, optional): The output file path to the HTML file.
            title (str, optional): The title of the HTML file. Defaults to 'My Map'.
            width (str, optional): The width of the map in pixels or percentage. Defaults to '100%'.
            height (str, optional): The height of the map in pixels. Defaults to '880px'.
            add_layer_control (bool, optional): Whether to add the LayersControl. Defaults to True.

        """
        try:
            save = True
            if filename is not None:
                if not filename.endswith(".html"):
                    raise ValueError("The output file extension must be html.")
                filename = os.path.abspath(filename)
                out_dir = os.path.dirname(filename)
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
            else:
                filename = os.path.abspath(random_string() + ".html")
                save = False

            if add_layer_control and self.layer_control is None:
                layer_control = ipyleaflet.LayersControl(position="topright")
                self.layer_control = layer_control
                self.add(layer_control)

            before_width = self.layout.width
            before_height = self.layout.height

            if not isinstance(width, str):
                print("width must be a string.")
                return
            elif width.endswith("px") or width.endswith("%"):
                pass
            else:
                print("width must end with px or %")
                return

            if not isinstance(height, str):
                print("height must be a string.")
                return
            elif not height.endswith("px"):
                print("height must end with px")
                return

            self.layout.width = width
            self.layout.height = height

            self.save(filename, title=title, **kwargs)

            self.layout.width = before_width
            self.layout.height = before_height

            if not save:
                out_html = ""
                with open(filename) as f:
                    lines = f.readlines()
                    out_html = "".join(lines)
                os.remove(filename)
                return out_html

        except Exception as e:
            raise Exception(e)

    def to_image(self, filename=None, monitor=1):
        """Saves the map as a PNG or JPG image.

        Args:
            filename (str, optional): The output file path to the image. Defaults to None.
            monitor (int, optional): The monitor to take the screenshot. Defaults to 1.
        """
        self.screenshot = None

        if filename is None:
            filename = os.path.join(os.getcwd(), "my_map.png")

        if filename.endswith(".png") or filename.endswith(".jpg"):
            pass
        else:
            print("The output file must be a PNG or JPG image.")
            return

        work_dir = os.path.dirname(filename)
        if not os.path.exists(work_dir):
            os.makedirs(work_dir)

        screenshot = screen_capture(filename, monitor)
        self.screenshot = screenshot

    def toolbar_reset(self):
        """Reset the toolbar so that no tool is selected."""
        toolbar_grid = self.toolbar
        for tool in toolbar_grid.children:
            tool.value = False

    def add_raster(
        self,
        source,
        band=None,
        palette=None,
        vmin=None,
        vmax=None,
        nodata=None,
        attribution=None,
        layer_name="Local COG",
        zoom_to_layer=True,
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
            band (int, optional): The band to use. Band indexing starts at 1. Defaults to None.
            palette (str, optional): The name of the color palette from `palettable` to use when plotting a single band. See https://jiffyclub.github.io/palettable. Default is greyscale
            vmin (float, optional): The minimum value to use when colormapping the palette when plotting a single band. Defaults to None.
            vmax (float, optional): The maximum value to use when colormapping the palette when plotting a single band. Defaults to None.
            nodata (float, optional): The value from the band to use to interpret as not valid data. Defaults to None.
            attribution (str, optional): Attribution for the source raster. This defaults to a message about it being a local file.. Defaults to None.
            layer_name (str, optional): The layer name to use. Defaults to 'Local COG'.
            zoom_to_layer (bool, optional): Whether to zoom to the extent of the layer. Defaults to True.
        """

        tile_layer, tile_client = get_local_tile_layer(
            source,
            band=band,
            palette=palette,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            attribution=attribution,
            layer_name=layer_name,
            return_client=True,
            **kwargs,
        )

        self.add(tile_layer)

        bounds = tile_client.bounds()  # [ymin, ymax, xmin, xmax]
        bounds = (
            bounds[2],
            bounds[0],
            bounds[3],
            bounds[1],
        )  # [minx, miny, maxx, maxy]
        if zoom_to_layer:
            self.zoom_to_bounds(bounds)

        arc_add_layer(tile_layer.url, layer_name, True, 1.0)
        if zoom_to_layer:
            arc_zoom_to_extent(bounds[0], bounds[1], bounds[2], bounds[3])

        if not hasattr(self, "cog_layer_dict"):
            self.cog_layer_dict = {}
        band_names = list(tile_client.metadata()["bands"].keys())
        params = {
            "tile_layer": tile_layer,
            "tile_client": tile_client,
            "band": band,
            "band_names": band_names,
            "bounds": bounds,
            "type": "LOCAL",
        }
        self.cog_layer_dict[layer_name] = params

    add_local_tile = add_raster

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

    def remove_drawn_features(self):
        """Removes user-drawn geometries from the map"""
        if self.draw_layer is not None:
            self.remove_layer(self.draw_layer)
            self.draw_count = 0
            self.draw_features = []
            self.draw_last_feature = None
            self.draw_layer = None
            self.draw_last_json = None
            self.draw_last_bounds = None
            self.user_roi = None
            self.user_rois = None
            self.chart_values = []
            self.chart_points = []
            self.chart_labels = None
        if self.draw_control is not None:
            self.draw_control.clear()

    def remove_last_drawn(self):
        """Removes user-drawn geometries from the map"""
        if self.draw_layer is not None:
            collection = ee.FeatureCollection(self.draw_features[:-1])
            ee_draw_layer = ee_tile_layer(
                collection, {"color": "blue"}, "Drawn Features", True, 0.5
            )
            if self.draw_count == 1:
                self.remove_drawn_features()
            else:
                self.substitute_layer(self.draw_layer, ee_draw_layer)
                self.draw_layer = ee_draw_layer
                self.draw_count -= 1
                self.draw_features = self.draw_features[:-1]
                self.draw_last_feature = self.draw_features[-1]
                self.draw_layer = ee_draw_layer
                self.draw_last_json = None
                self.draw_last_bounds = None
                self.user_roi = ee.Feature(
                    collection.toList(collection.size()).get(
                        collection.size().subtract(1)
                    )
                ).geometry()
                self.user_rois = collection
                self.chart_values = self.chart_values[:-1]
                self.chart_points = self.chart_points[:-1]
                # self.chart_labels = None

    def extract_values_to_points(self, filename):
        """Exports pixel values to a csv file based on user-drawn geometries.

        Args:
            filename (str): The output file path to the csv file or shapefile.
        """
        import csv

        filename = os.path.abspath(filename)
        allowed_formats = ["csv", "shp"]
        ext = filename[-3:]

        if ext not in allowed_formats:
            print(
                "The output file must be one of the following: {}".format(
                    ", ".join(allowed_formats)
                )
            )
            return

        out_dir = os.path.dirname(filename)
        out_csv = filename[:-3] + "csv"
        out_shp = filename[:-3] + "shp"
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        count = len(self.chart_points)
        out_list = []
        if count > 0:
            header = ["id", "longitude", "latitude"] + self.chart_labels
            out_list.append(header)

            for i in range(0, count):
                id = i + 1
                line = [id] + self.chart_points[i] + self.chart_values[i]
                out_list.append(line)

            with open(out_csv, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(out_list)

            if ext == "csv":
                print(f"The csv file has been saved to: {out_csv}")
            else:
                csv_to_shp(out_csv, out_shp)
                print(f"The shapefile has been saved to: {out_shp}")

    def create_vis_widget(self, layer_dict):
        """Create a GUI for changing layer visualization parameters interactively.

        Args:
            layer_dict (dict): A dict containning information about the layer. It is an element from Map.ee_layer_dict.

        Returns:
            object: An ipywidget.
        """

        import matplotlib as mpl
        import matplotlib.pyplot as plt

        ee_object = layer_dict["ee_object"]

        if isinstance(ee_object, ee.Geometry) or isinstance(ee_object, ee.Feature):
            ee_object = ee.FeatureCollection(ee_object)

        ee_layer = layer_dict["ee_layer"]
        vis_params = layer_dict["vis_params"]

        layer_name = ee_layer.name
        layer_opacity = ee_layer.opacity

        band_names = None
        min_value = 0
        max_value = 100
        sel_bands = None
        layer_palette = []
        layer_gamma = 1
        left_value = 0
        right_value = 10000

        self.colorbar_widget = widgets.Output(layout=widgets.Layout(height="60px"))
        self.colorbar_ctrl = ipyleaflet.WidgetControl(
            widget=self.colorbar_widget, position="bottomright"
        )
        self.add(self.colorbar_ctrl)

        # def vdir(obj):  # Get branca colormap list
        #     return [x for x in dir(obj) if not x.startswith("_")]

        if isinstance(ee_object, ee.Image):
            band_names = ee_object.bandNames().getInfo()
            band_count = len(band_names)

            if "min" in vis_params.keys():
                min_value = vis_params["min"]
                if min_value < left_value:
                    left_value = min_value - max_value
            if "max" in vis_params.keys():
                max_value = vis_params["max"]
                right_value = 2 * max_value
            if "gamma" in vis_params.keys():
                layer_gamma = vis_params["gamma"]
            if "bands" in vis_params.keys():
                sel_bands = vis_params["bands"]
            if "palette" in vis_params.keys():
                layer_palette = [
                    color.replace("#", "") for color in list(vis_params["palette"])
                ]

            vis_widget = widgets.VBox(
                layout=widgets.Layout(padding="5px 5px 5px 8px", width="330px")
            )
            label = widgets.Label(value=f"{layer_name} visualization parameters")

            radio1 = widgets.RadioButtons(
                options=["1 band (Grayscale)"], layout={"width": "max-content"}
            )
            radio2 = widgets.RadioButtons(
                options=["3 bands (RGB)"], layout={"width": "max-content"}
            )
            radio1.index = None
            radio2.index = None

            dropdown_width = "98px"
            band1_dropdown = widgets.Dropdown(
                options=band_names,
                value=band_names[0],
                layout=widgets.Layout(width=dropdown_width),
            )
            band2_dropdown = widgets.Dropdown(
                options=band_names,
                value=band_names[0],
                layout=widgets.Layout(width=dropdown_width),
            )
            band3_dropdown = widgets.Dropdown(
                options=band_names,
                value=band_names[0],
                layout=widgets.Layout(width=dropdown_width),
            )

            bands_hbox = widgets.HBox()

            legend_chk = widgets.Checkbox(
                value=False,
                description="Legend",
                indent=False,
                layout=widgets.Layout(width="70px"),
            )

            color_picker = widgets.ColorPicker(
                concise=False,
                value="#000000",
                layout=widgets.Layout(width="116px"),
                style={"description_width": "initial"},
            )

            add_color = widgets.Button(
                icon="plus",
                tooltip="Add a hex color string to the palette",
                layout=widgets.Layout(width="32px"),
            )

            del_color = widgets.Button(
                icon="minus",
                tooltip="Remove a hex color string from the palette",
                layout=widgets.Layout(width="32px"),
            )

            reset_color = widgets.Button(
                icon="eraser",
                tooltip="Remove all color strings from the palette",
                layout=widgets.Layout(width="34px"),
            )

            classes = widgets.Dropdown(
                options=["Any"] + [str(i) for i in range(3, 13)],
                description="Classes:",
                layout=widgets.Layout(width="115px"),
                style={"description_width": "initial"},
            )

            colormap_options = plt.colormaps()
            colormap_options.sort()
            colormap = widgets.Dropdown(
                options=colormap_options,
                value=None,
                description="Colormap:",
                layout=widgets.Layout(width="181px"),
                style={"description_width": "initial"},
            )

            def classes_changed(change):
                if change["new"]:
                    selected = change["owner"].value
                    if colormap.value is not None:
                        n_class = None
                        if selected != "Any":
                            n_class = int(classes.value)

                        colors = plt.cm.get_cmap(colormap.value, n_class)
                        cmap_colors = [
                            mpl.colors.rgb2hex(colors(i))[1:] for i in range(colors.N)
                        ]

                        _, ax = plt.subplots(figsize=(6, 0.4))
                        cmap = mpl.colors.LinearSegmentedColormap.from_list(
                            "custom", to_hex_colors(cmap_colors), N=256
                        )
                        norm = mpl.colors.Normalize(
                            vmin=value_range.value[0], vmax=value_range.value[1]
                        )
                        mpl.colorbar.ColorbarBase(
                            ax, norm=norm, cmap=cmap, orientation="horizontal"
                        )

                        palette.value = ", ".join([color for color in cmap_colors])

                        if self.colorbar_widget is None:
                            self.colorbar_widget = widgets.Output(
                                layout=widgets.Layout(height="60px")
                            )

                        if self.colorbar_ctrl is None:
                            self.colorbar_ctrl = ipyleaflet.WidgetControl(
                                widget=self.colorbar_widget, position="bottomright"
                            )
                            self.add(self.colorbar_ctrl)

                        colorbar_output = self.colorbar_widget
                        with colorbar_output:
                            colorbar_output.clear_output()
                            plt.show()

                        if len(palette.value) > 0 and "," in palette.value:
                            labels = [
                                f"Class {i+1}"
                                for i in range(len(palette.value.split(",")))
                            ]
                            legend_labels.value = ", ".join(labels)

            classes.observe(classes_changed, "value")

            palette = widgets.Text(
                value=", ".join(layer_palette),
                placeholder="List of hex color code (RRGGBB)",
                description="Palette:",
                tooltip="Enter a list of hex color code (RRGGBB)",
                layout=widgets.Layout(width="300px"),
                style={"description_width": "initial"},
            )

            def add_color_clicked(b):
                if color_picker.value is not None:
                    if len(palette.value) == 0:
                        palette.value = color_picker.value[1:]
                    else:
                        palette.value += ", " + color_picker.value[1:]

            def del_color_clicked(b):
                if "," in palette.value:
                    items = [item.strip() for item in palette.value.split(",")]
                    palette.value = ", ".join(items[:-1])
                else:
                    palette.value = ""

            def reset_color_clicked(b):
                palette.value = ""

            add_color.on_click(add_color_clicked)
            del_color.on_click(del_color_clicked)
            reset_color.on_click(reset_color_clicked)

            spacer = widgets.Label(layout=widgets.Layout(width="5px"))
            v_spacer = widgets.Label(layout=widgets.Layout(height="5px"))
            radio_btn = widgets.HBox([radio1, spacer, spacer, spacer, radio2])

            value_range = widgets.FloatRangeSlider(
                value=[min_value, max_value],
                min=left_value,
                max=right_value,
                step=0.1,
                description="Range:",
                disabled=False,
                continuous_update=False,
                readout=True,
                readout_format=".1f",
                layout=widgets.Layout(width="300px"),
                style={"description_width": "45px"},
            )

            range_hbox = widgets.HBox([value_range, spacer])

            opacity = widgets.FloatSlider(
                value=layer_opacity,
                min=0,
                max=1,
                step=0.01,
                description="Opacity:",
                continuous_update=False,
                readout=True,
                readout_format=".2f",
                layout=widgets.Layout(width="320px"),
                style={"description_width": "50px"},
            )

            gamma = widgets.FloatSlider(
                value=layer_gamma,
                min=0.1,
                max=10,
                step=0.01,
                description="Gamma:",
                continuous_update=False,
                readout=True,
                readout_format=".2f",
                layout=widgets.Layout(width="320px"),
                style={"description_width": "50px"},
            )

            legend_chk = widgets.Checkbox(
                value=False,
                description="Legend",
                indent=False,
                layout=widgets.Layout(width="70px"),
            )

            linear_chk = widgets.Checkbox(
                value=True,
                description="Linear colormap",
                indent=False,
                layout=widgets.Layout(width="150px"),
            )

            step_chk = widgets.Checkbox(
                value=False,
                description="Step colormap",
                indent=False,
                layout=widgets.Layout(width="140px"),
            )

            legend_title = widgets.Text(
                value="Legend",
                description="Legend title:",
                tooltip="Enter a title for the legend",
                layout=widgets.Layout(width="300px"),
                style={"description_width": "initial"},
            )

            legend_labels = widgets.Text(
                value="Class 1, Class 2, Class 3",
                description="Legend labels:",
                tooltip="Enter a a list of labels for the legend",
                layout=widgets.Layout(width="300px"),
                style={"description_width": "initial"},
            )

            colormap_hbox = widgets.HBox([linear_chk, step_chk])
            legend_vbox = widgets.VBox()

            def linear_chk_changed(change):
                if change["new"]:
                    step_chk.value = False
                    legend_vbox.children = [colormap_hbox]
                else:
                    step_chk.value = True

            def step_chk_changed(change):
                if change["new"]:
                    linear_chk.value = False
                    if len(layer_palette) > 0:
                        legend_labels.value = ",".join(
                            [
                                "Class " + str(i)
                                for i in range(1, len(layer_palette) + 1)
                            ]
                        )
                    legend_vbox.children = [
                        colormap_hbox,
                        legend_title,
                        legend_labels,
                    ]
                else:
                    linear_chk.value = True

            linear_chk.observe(linear_chk_changed, "value")
            step_chk.observe(step_chk_changed, "value")

            def colormap_changed(change):
                if change["new"]:
                    n_class = None
                    if classes.value != "Any":
                        n_class = int(classes.value)

                    colors = plt.cm.get_cmap(colormap.value, n_class)
                    cmap_colors = [
                        mpl.colors.rgb2hex(colors(i))[1:] for i in range(colors.N)
                    ]

                    _, ax = plt.subplots(figsize=(6, 0.4))
                    cmap = mpl.colors.LinearSegmentedColormap.from_list(
                        "custom", to_hex_colors(cmap_colors), N=256
                    )
                    norm = mpl.colors.Normalize(
                        vmin=value_range.value[0], vmax=value_range.value[1]
                    )
                    mpl.colorbar.ColorbarBase(
                        ax, norm=norm, cmap=cmap, orientation="horizontal"
                    )

                    palette.value = ", ".join(cmap_colors)

                    if self.colorbar_widget is None:
                        self.colorbar_widget = widgets.Output(
                            layout=widgets.Layout(height="60px")
                        )

                    if self.colorbar_ctrl is None:
                        self.colorbar_ctrl = ipyleaflet.WidgetControl(
                            widget=self.colorbar_widget, position="bottomright"
                        )
                        self.add(self.colorbar_ctrl)

                    colorbar_output = self.colorbar_widget
                    with colorbar_output:
                        colorbar_output.clear_output()
                        plt.show()
                        # display(colorbar)

                    if len(palette.value) > 0 and "," in palette.value:
                        labels = [
                            f"Class {i+1}" for i in range(len(palette.value.split(",")))
                        ]
                        legend_labels.value = ", ".join(labels)

            colormap.observe(colormap_changed, "value")

            btn_width = "97.5px"
            import_btn = widgets.Button(
                description="Import",
                button_style="primary",
                tooltip="Import vis params to notebook",
                layout=widgets.Layout(width=btn_width),
            )

            apply_btn = widgets.Button(
                description="Apply",
                tooltip="Apply vis params to the layer",
                layout=widgets.Layout(width=btn_width),
            )

            close_btn = widgets.Button(
                description="Close",
                tooltip="Close vis params diaglog",
                layout=widgets.Layout(width=btn_width),
            )

            def import_btn_clicked(b):
                vis = {}
                if radio1.index == 0:
                    vis["bands"] = [band1_dropdown.value]
                    if len(palette.value) > 0:
                        vis["palette"] = palette.value.split(",")
                else:
                    vis["bands"] = [
                        band1_dropdown.value,
                        band2_dropdown.value,
                        band3_dropdown.value,
                    ]

                vis["min"] = value_range.value[0]
                vis["max"] = value_range.value[1]
                vis["opacity"] = opacity.value
                vis["gamma"] = gamma.value

                create_code_cell(f"vis_params = {str(vis)}")

            def apply_btn_clicked(b):
                vis = {}
                if radio1.index == 0:
                    vis["bands"] = [band1_dropdown.value]
                    if len(palette.value) > 0:
                        vis["palette"] = [c.strip() for c in palette.value.split(",")]
                else:
                    vis["bands"] = [
                        band1_dropdown.value,
                        band2_dropdown.value,
                        band3_dropdown.value,
                    ]
                    vis["gamma"] = gamma.value

                vis["min"] = value_range.value[0]
                vis["max"] = value_range.value[1]

                self.addLayer(ee_object, vis, layer_name, True, opacity.value)
                ee_layer.visible = False

                if legend_chk.value:
                    if (
                        self.colorbar_ctrl is not None
                        and self.colorbar_ctrl in self.controls
                    ):
                        self.remove_control(self.colorbar_ctrl)
                        self.colorbar_ctrl.close()
                        self.colorbar_widget.close()

                    if (
                        "colorbar" in layer_dict.keys()
                        and layer_dict["colorbar"] in self.controls
                    ):
                        self.remove_control(layer_dict["colorbar"])
                        layer_dict["colorbar"] = None

                    if linear_chk.value:
                        if (
                            "legend" in layer_dict.keys()
                            and layer_dict["legend"] in self.controls
                        ):
                            self.remove_control(layer_dict["legend"])
                            layer_dict["legend"] = None

                        if len(palette.value) > 0 and "," in palette.value:
                            colors = to_hex_colors(
                                [color.strip() for color in palette.value.split(",")]
                            )

                            self.add_colorbar(
                                vis_params={
                                    "palette": colors,
                                    "min": value_range.value[0],
                                    "max": value_range.value[1],
                                },
                                layer_name=layer_name,
                            )
                    elif step_chk.value:
                        if len(palette.value) > 0 and "," in palette.value:
                            colors = to_hex_colors(
                                [color.strip() for color in palette.value.split(",")]
                            )
                            labels = [
                                label.strip()
                                for label in legend_labels.value.split(",")
                            ]

                            self.add_legend(
                                title=legend_title.value,
                                legend_keys=labels,
                                legend_colors=colors,
                                layer_name=layer_name,
                            )
                else:
                    if radio1.index == 0 and "palette" in vis:
                        self.colorbar_widget.clear_output()
                        with self.colorbar_widget:
                            _, ax = plt.subplots(figsize=(6, 0.4))
                            colors = to_hex_colors(vis["palette"])
                            cmap = mpl.colors.LinearSegmentedColormap.from_list(
                                "custom", colors, N=256
                            )
                            norm = mpl.colors.Normalize(
                                vmin=vis["min"], vmax=vis["max"]
                            )
                            mpl.colorbar.ColorbarBase(
                                ax, norm=norm, cmap=cmap, orientation="horizontal"
                            )
                            plt.show()

                        if (
                            "colorbar" in layer_dict.keys()
                            and layer_dict["colorbar"] in self.controls
                        ):
                            self.remove_control(layer_dict["colorbar"])
                            layer_dict["colorbar"] = None
                        if (
                            "legend" in layer_dict.keys()
                            and layer_dict["legend"] in self.controls
                        ):
                            self.remove_control(layer_dict["legend"])
                            layer_dict["legend"] = None

            def close_btn_clicked(b):
                if self.vis_control in self.controls:
                    self.remove_control(self.vis_control)
                    self.vis_control = None
                    self.vis_widget.close()

                if (
                    self.colorbar_ctrl is not None
                    and self.colorbar_ctrl in self.controls
                ):
                    self.remove_control(self.colorbar_ctrl)
                    self.colorbar_ctrl = None
                    self.colorbar_widget.close()

            import_btn.on_click(import_btn_clicked)
            apply_btn.on_click(apply_btn_clicked)
            close_btn.on_click(close_btn_clicked)

            color_hbox = widgets.HBox(
                [legend_chk, color_picker, add_color, del_color, reset_color]
            )
            btn_hbox = widgets.HBox([import_btn, apply_btn, close_btn])

            gray_box = [
                label,
                radio_btn,
                bands_hbox,
                v_spacer,
                range_hbox,
                opacity,
                gamma,
                widgets.HBox([classes, colormap]),
                palette,
                color_hbox,
                legend_vbox,
                btn_hbox,
            ]

            rgb_box = [
                label,
                radio_btn,
                bands_hbox,
                v_spacer,
                range_hbox,
                opacity,
                gamma,
                btn_hbox,
            ]

            def legend_chk_changed(change):
                if change["new"]:
                    linear_chk.value = True
                    legend_vbox.children = [
                        widgets.HBox([linear_chk, step_chk]),
                        # legend_title,
                        # legend_labels,
                    ]
                else:
                    legend_vbox.children = []

            legend_chk.observe(legend_chk_changed, "value")

            if band_count < 3:
                radio1.index = 0
                band1_dropdown.layout.width = "300px"
                bands_hbox.children = [band1_dropdown]
                vis_widget.children = gray_box
                legend_chk.value = False

                if len(palette.value) > 0 and "," in palette.value:
                    import matplotlib as mpl
                    import matplotlib.pyplot as plt

                    colors = to_hex_colors(
                        [color.strip() for color in palette.value.split(",")]
                    )

                    self.colorbar_widget.clear_output()
                    with self.colorbar_widget:
                        _, ax = plt.subplots(figsize=(6, 0.4))
                        cmap = mpl.colors.LinearSegmentedColormap.from_list(
                            "custom", colors, N=256
                        )
                        norm = mpl.colors.Normalize(
                            vmin=value_range.value[0], vmax=value_range.value[1]
                        )
                        mpl.colorbar.ColorbarBase(
                            ax, norm=norm, cmap=cmap, orientation="horizontal"
                        )
                        plt.show()

            else:
                radio2.index = 0
                if (sel_bands is None) or (len(sel_bands) < 2):
                    sel_bands = band_names[0:3]
                band1_dropdown.value = sel_bands[0]
                band2_dropdown.value = sel_bands[1]
                band3_dropdown.value = sel_bands[2]
                bands_hbox.children = [
                    band1_dropdown,
                    band2_dropdown,
                    band3_dropdown,
                ]
                vis_widget.children = rgb_box

            def radio1_observer(sender):
                radio2.unobserve(radio2_observer, names=["value"])
                radio2.index = None
                radio2.observe(radio2_observer, names=["value"])
                band1_dropdown.layout.width = "300px"
                bands_hbox.children = [band1_dropdown]
                palette.value = ", ".join(layer_palette)
                palette.disabled = False
                color_picker.disabled = False
                add_color.disabled = False
                del_color.disabled = False
                reset_color.disabled = False
                vis_widget.children = gray_box

                if len(palette.value) > 0 and "," in palette.value:
                    colors = [color.strip() for color in palette.value.split(",")]

                    _, ax = plt.subplots(figsize=(6, 0.4))
                    cmap = mpl.colors.LinearSegmentedColormap.from_list(
                        "custom", to_hex_colors(colors), N=256
                    )
                    norm = mpl.colors.Normalize(vmin=0, vmax=1)
                    mpl.colorbar.ColorbarBase(
                        ax, norm=norm, cmap=cmap, orientation="horizontal"
                    )

                    self.colorbar_widget = widgets.Output(
                        layout=widgets.Layout(height="60px")
                    )
                    self.colorbar_ctrl = ipyleaflet.WidgetControl(
                        widget=self.colorbar_widget, position="bottomright"
                    )

                    if self.colorbar_ctrl not in self.controls:
                        self.add(self.colorbar_ctrl)

                    self.colorbar_widget.clear_output()
                    with self.colorbar_widget:
                        plt.show()

            def radio2_observer(sender):
                radio1.unobserve(radio1_observer, names=["value"])
                radio1.index = None
                radio1.observe(radio1_observer, names=["value"])
                band1_dropdown.layout.width = dropdown_width
                bands_hbox.children = [
                    band1_dropdown,
                    band2_dropdown,
                    band3_dropdown,
                ]
                palette.value = ""
                palette.disabled = True
                color_picker.disabled = True
                add_color.disabled = True
                del_color.disabled = True
                reset_color.disabled = True
                vis_widget.children = rgb_box

                if (
                    self.colorbar_ctrl is not None
                    and self.colorbar_ctrl in self.controls
                ):
                    self.remove_control(self.colorbar_ctrl)
                    self.colorbar_ctrl.close()
                    self.colorbar_widget.close()

            radio1.observe(radio1_observer, names=["value"])
            radio2.observe(radio2_observer, names=["value"])

            return vis_widget

        elif isinstance(ee_object, ee.FeatureCollection):
            vis_widget = widgets.VBox(
                layout=widgets.Layout(padding="5px 5px 5px 8px", width="330px")
            )
            label = widgets.Label(value=f"{layer_name} visualization parameters")

            new_layer_name = widgets.Text(
                value=f"{layer_name} style",
                description="New layer name:",
                style={"description_width": "initial"},
            )

            color = widgets.ColorPicker(
                concise=False,
                value="#000000",
                description="Color:",
                layout=widgets.Layout(width="140px"),
                style={"description_width": "initial"},
            )

            color_opacity = widgets.FloatSlider(
                value=layer_opacity,
                min=0,
                max=1,
                step=0.01,
                description="Opacity:",
                continuous_update=True,
                readout=False,
                #             readout_format=".2f",
                layout=widgets.Layout(width="130px"),
                style={"description_width": "50px"},
            )

            color_opacity_label = widgets.Label(
                style={"description_width": "initial"},
                layout=widgets.Layout(padding="0px"),
            )

            def color_opacity_change(change):
                color_opacity_label.value = str(change["new"])

            color_opacity.observe(color_opacity_change, names="value")

            # widgets.jslink((color_opacity, "value"), (color_opacity_label, "value"))

            point_size = widgets.IntText(
                value=3,
                description="Point size:",
                layout=widgets.Layout(width="110px"),
                style={"description_width": "initial"},
            )

            point_shape_options = [
                "circle",
                "square",
                "diamond",
                "cross",
                "plus",
                "pentagram",
                "hexagram",
                "triangle",
                "triangle_up",
                "triangle_down",
                "triangle_left",
                "triangle_right",
                "pentagon",
                "hexagon",
                "star5",
                "star6",
            ]
            point_shape = widgets.Dropdown(
                options=point_shape_options,
                value="circle",
                description="Point shape:",
                layout=widgets.Layout(width="185px"),
                style={"description_width": "initial"},
            )

            line_width = widgets.IntText(
                value=2,
                description="Line width:",
                layout=widgets.Layout(width="110px"),
                style={"description_width": "initial"},
            )

            line_type = widgets.Dropdown(
                options=["solid", "dotted", "dashed"],
                value="solid",
                description="Line type:",
                layout=widgets.Layout(width="185px"),
                style={"description_width": "initial"},
            )

            fill_color = widgets.ColorPicker(
                concise=False,
                value="#000000",
                description="Fill Color:",
                layout=widgets.Layout(width="160px"),
                style={"description_width": "initial"},
            )

            fill_color_opacity = widgets.FloatSlider(
                value=0.66,
                min=0,
                max=1,
                step=0.01,
                description="Opacity:",
                continuous_update=True,
                readout=False,
                #             readout_format=".2f",
                layout=widgets.Layout(width="110px"),
                style={"description_width": "50px"},
            )

            fill_color_opacity_label = widgets.Label(
                style={"description_width": "initial"},
                layout=widgets.Layout(padding="0px"),
            )

            def fill_color_opacity_change(change):
                fill_color_opacity_label.value = str(change["new"])

            fill_color_opacity.observe(fill_color_opacity_change, names="value")

            # widgets.jslink(
            #     (fill_color_opacity, "value"),
            #     (fill_color_opacity_label, "value"),
            # )

            color_picker = widgets.ColorPicker(
                concise=False,
                value="#000000",
                layout=widgets.Layout(width="116px"),
                style={"description_width": "initial"},
            )
            add_color = widgets.Button(
                icon="plus",
                tooltip="Add a hex color string to the palette",
                layout=widgets.Layout(width="32px"),
            )
            del_color = widgets.Button(
                icon="minus",
                tooltip="Remove a hex color string from the palette",
                layout=widgets.Layout(width="32px"),
            )
            reset_color = widgets.Button(
                icon="eraser",
                tooltip="Remove all color strings from the palette",
                layout=widgets.Layout(width="34px"),
            )

            palette = widgets.Text(
                value="",
                placeholder="List of hex code (RRGGBB) separated by comma",
                description="Palette:",
                tooltip="Enter a list of hex code (RRGGBB) separated by comma",
                layout=widgets.Layout(width="300px"),
                style={"description_width": "initial"},
            )

            legend_title = widgets.Text(
                value="Legend",
                description="Legend title:",
                tooltip="Enter a title for the legend",
                layout=widgets.Layout(width="300px"),
                style={"description_width": "initial"},
            )

            legend_labels = widgets.Text(
                value="Labels",
                description="Legend labels:",
                tooltip="Enter a a list of labels for the legend",
                layout=widgets.Layout(width="300px"),
                style={"description_width": "initial"},
            )

            def add_color_clicked(b):
                if color_picker.value is not None:
                    if len(palette.value) == 0:
                        palette.value = color_picker.value[1:]
                    else:
                        palette.value += ", " + color_picker.value[1:]

            def del_color_clicked(b):
                if "," in palette.value:
                    items = [item.strip() for item in palette.value.split(",")]
                    palette.value = ", ".join(items[:-1])
                else:
                    palette.value = ""

            def reset_color_clicked(b):
                palette.value = ""

            add_color.on_click(add_color_clicked)
            del_color.on_click(del_color_clicked)
            reset_color.on_click(reset_color_clicked)

            field = widgets.Dropdown(
                options=[],
                value=None,
                description="Field:",
                layout=widgets.Layout(width="140px"),
                style={"description_width": "initial"},
            )

            field_values = widgets.Dropdown(
                options=[],
                value=None,
                description="Values:",
                layout=widgets.Layout(width="156px"),
                style={"description_width": "initial"},
            )

            classes = widgets.Dropdown(
                options=["Any"] + [str(i) for i in range(3, 13)],
                description="Classes:",
                layout=widgets.Layout(width="115px"),
                style={"description_width": "initial"},
            )

            colormap = widgets.Dropdown(
                options=["viridis"],
                value="viridis",
                description="Colormap:",
                layout=widgets.Layout(width="181px"),
                style={"description_width": "initial"},
            )

            def classes_changed(change):
                if change["new"]:
                    selected = change["owner"].value
                    if colormap.value is not None:
                        n_class = None
                        if selected != "Any":
                            n_class = int(classes.value)

                        colors = plt.cm.get_cmap(colormap.value, n_class)
                        cmap_colors = [
                            mpl.colors.rgb2hex(colors(i))[1:] for i in range(colors.N)
                        ]

                        _, ax = plt.subplots(figsize=(6, 0.4))
                        cmap = mpl.colors.LinearSegmentedColormap.from_list(
                            "custom", to_hex_colors(cmap_colors), N=256
                        )
                        norm = mpl.colors.Normalize(vmin=0, vmax=1)
                        mpl.colorbar.ColorbarBase(
                            ax, norm=norm, cmap=cmap, orientation="horizontal"
                        )

                        palette.value = ", ".join([color for color in cmap_colors])

                        if self.colorbar_widget is None:
                            self.colorbar_widget = widgets.Output(
                                layout=widgets.Layout(height="60px")
                            )

                        if self.colorbar_ctrl is None:
                            self.colorbar_ctrl = ipyleaflet.WidgetControl(
                                widget=self.colorbar_widget, position="bottomright"
                            )
                            self.add(self.colorbar_ctrl)

                        colorbar_output = self.colorbar_widget
                        with colorbar_output:
                            colorbar_output.clear_output()
                            plt.show()

                        if len(palette.value) > 0 and "," in palette.value:
                            labels = [
                                f"Class {i+1}"
                                for i in range(len(palette.value.split(",")))
                            ]
                            legend_labels.value = ", ".join(labels)

            classes.observe(classes_changed, "value")

            def colormap_changed(change):
                if change["new"]:
                    n_class = None
                    if classes.value != "Any":
                        n_class = int(classes.value)

                    colors = plt.cm.get_cmap(colormap.value, n_class)
                    cmap_colors = [
                        mpl.colors.rgb2hex(colors(i))[1:] for i in range(colors.N)
                    ]

                    _, ax = plt.subplots(figsize=(6, 0.4))
                    cmap = mpl.colors.LinearSegmentedColormap.from_list(
                        "custom", to_hex_colors(cmap_colors), N=256
                    )
                    norm = mpl.colors.Normalize(vmin=0, vmax=1)
                    mpl.colorbar.ColorbarBase(
                        ax, norm=norm, cmap=cmap, orientation="horizontal"
                    )

                    palette.value = ", ".join(cmap_colors)

                    if self.colorbar_widget is None:
                        self.colorbar_widget = widgets.Output(
                            layout=widgets.Layout(height="60px")
                        )

                    if self.colorbar_ctrl is None:
                        self.colorbar_ctrl = ipyleaflet.WidgetControl(
                            widget=self.colorbar_widget, position="bottomright"
                        )
                        self.add(self.colorbar_ctrl)

                    colorbar_output = self.colorbar_widget
                    with colorbar_output:
                        colorbar_output.clear_output()
                        plt.show()
                        # display(colorbar)

                    if len(palette.value) > 0 and "," in palette.value:
                        labels = [
                            f"Class {i+1}" for i in range(len(palette.value.split(",")))
                        ]
                        legend_labels.value = ", ".join(labels)

            colormap.observe(colormap_changed, "value")

            btn_width = "97.5px"
            import_btn = widgets.Button(
                description="Import",
                button_style="primary",
                tooltip="Import vis params to notebook",
                layout=widgets.Layout(width=btn_width),
            )

            apply_btn = widgets.Button(
                description="Apply",
                tooltip="Apply vis params to the layer",
                layout=widgets.Layout(width=btn_width),
            )

            close_btn = widgets.Button(
                description="Close",
                tooltip="Close vis params diaglog",
                layout=widgets.Layout(width=btn_width),
            )

            style_chk = widgets.Checkbox(
                value=False,
                description="Style by attribute",
                indent=False,
                layout=widgets.Layout(width="140px"),
            )

            legend_chk = widgets.Checkbox(
                value=False,
                description="Legend",
                indent=False,
                layout=widgets.Layout(width="70px"),
            )
            compute_label = widgets.Label(value="")

            style_vbox = widgets.VBox([widgets.HBox([style_chk, compute_label])])

            def style_chk_changed(change):
                if change["new"]:
                    if (
                        self.colorbar_ctrl is not None
                        and self.colorbar_ctrl in self.controls
                    ):
                        self.remove_control(self.colorbar_ctrl)
                        self.colorbar_ctrl.close()
                        self.colorbar_widget.close()

                    self.colorbar_widget = widgets.Output(
                        layout=widgets.Layout(height="60px")
                    )
                    self.colorbar_ctrl = ipyleaflet.WidgetControl(
                        widget=self.colorbar_widget, position="bottomright"
                    )
                    self.add(self.colorbar_ctrl)
                    fill_color.disabled = True
                    colormap_options = plt.colormaps()
                    colormap_options.sort()
                    colormap.options = colormap_options
                    colormap.value = "viridis"
                    style_vbox.children = [
                        widgets.HBox([style_chk, compute_label]),
                        widgets.HBox([field, field_values]),
                        widgets.HBox([classes, colormap]),
                        palette,
                        widgets.HBox(
                            [
                                legend_chk,
                                color_picker,
                                add_color,
                                del_color,
                                reset_color,
                            ]
                        ),
                    ]
                    compute_label.value = "Computing ..."

                    field.options = (
                        ee.Feature(ee_object.first()).propertyNames().getInfo()
                    )
                    compute_label.value = ""
                    classes.value = "Any"
                    legend_chk.value = False

                else:
                    fill_color.disabled = False
                    style_vbox.children = [widgets.HBox([style_chk, compute_label])]
                    compute_label.value = ""
                    if (
                        self.colorbar_ctrl is not None
                        and self.colorbar_ctrl in self.controls
                    ):
                        self.remove_control(self.colorbar_ctrl)
                        self.colorbar_ctrl = None
                        self.colorbar_widget = None
                    # legend_chk.value = False

            style_chk.observe(style_chk_changed, "value")

            def legend_chk_changed(change):
                if change["new"]:
                    style_vbox.children = list(style_vbox.children) + [
                        widgets.VBox([legend_title, legend_labels])
                    ]

                    if len(palette.value) > 0 and "," in palette.value:
                        labels = [
                            f"Class {i+1}" for i in range(len(palette.value.split(",")))
                        ]
                        legend_labels.value = ", ".join(labels)

                else:
                    style_vbox.children = [
                        widgets.HBox([style_chk, compute_label]),
                        widgets.HBox([field, field_values]),
                        widgets.HBox([classes, colormap]),
                        palette,
                        widgets.HBox(
                            [
                                legend_chk,
                                color_picker,
                                add_color,
                                del_color,
                                reset_color,
                            ]
                        ),
                    ]

            legend_chk.observe(legend_chk_changed, "value")

            def field_changed(change):
                if change["new"]:
                    compute_label.value = "Computing ..."
                    options = ee_object.aggregate_array(field.value).getInfo()
                    if options is not None:
                        options = list(set(options))
                        options.sort()

                    field_values.options = options
                    compute_label.value = ""

            field.observe(field_changed, "value")

            def get_vis_params():
                vis = {}
                vis["color"] = color.value[1:] + str(
                    hex(int(color_opacity.value * 255))
                )[2:].zfill(2)
                if geometry_type(ee_object) in ["Point", "MultiPoint"]:
                    vis["pointSize"] = point_size.value
                    vis["pointShape"] = point_shape.value
                vis["width"] = line_width.value
                vis["lineType"] = line_type.value
                vis["fillColor"] = fill_color.value[1:] + str(
                    hex(int(fill_color_opacity.value * 255))
                )[2:].zfill(2)

                return vis

            def import_btn_clicked(b):
                vis = get_vis_params()
                create_code_cell(f"vis_params = {str(vis)}")

            def apply_btn_clicked(b):
                compute_label.value = "Computing ..."

                if new_layer_name.value in self.ee_layer_names:
                    old_layer = new_layer_name.value

                    if "legend" in self.ee_layer_dict[old_layer].keys():
                        legend = self.ee_layer_dict[old_layer]["legend"]
                        if legend in self.controls:
                            self.remove_control(legend)
                        legend.close()
                    if "colorbar" in self.ee_layer_dict[old_layer].keys():
                        colorbar = self.ee_layer_dict[old_layer]["colorbar"]
                        if colorbar in self.controls:
                            self.remove_control(colorbar)
                        colorbar.close()

                if not style_chk.value:
                    vis = get_vis_params()
                    self.addLayer(ee_object.style(**vis), {}, new_layer_name.value)
                    ee_layer.visible = False

                elif (
                    style_chk.value and len(palette.value) > 0 and "," in palette.value
                ):
                    try:
                        colors = ee.List(
                            [
                                color.strip()
                                + str(hex(int(fill_color_opacity.value * 255)))[
                                    2:
                                ].zfill(2)
                                for color in palette.value.split(",")
                            ]
                        )
                        arr = ee_object.aggregate_array(field.value).distinct().sort()
                        fc = ee_object.map(
                            lambda f: f.set(
                                {"styleIndex": arr.indexOf(f.get(field.value))}
                            )
                        )
                        step = arr.size().divide(colors.size()).ceil()
                        fc = fc.map(
                            lambda f: f.set(
                                {
                                    "style": {
                                        "color": color.value[1:]
                                        + str(hex(int(color_opacity.value * 255)))[
                                            2:
                                        ].zfill(2),
                                        "pointSize": point_size.value,
                                        "pointShape": point_shape.value,
                                        "width": line_width.value,
                                        "lineType": line_type.value,
                                        "fillColor": colors.get(
                                            ee.Number(
                                                ee.Number(f.get("styleIndex")).divide(
                                                    step
                                                )
                                            ).floor()
                                        ),
                                    }
                                }
                            )
                        )

                        self.addLayer(
                            fc.style(**{"styleProperty": "style"}),
                            {},
                            f"{new_layer_name.value}",
                        )

                        if (
                            len(palette.value)
                            and legend_chk.value
                            and len(legend_labels.value) > 0
                        ):
                            legend_colors = [
                                color.strip() for color in palette.value.split(",")
                            ]
                            legend_keys = [
                                label.strip()
                                for label in legend_labels.value.split(",")
                            ]
                            self.add_legend(
                                title=legend_title.value,
                                legend_keys=legend_keys,
                                legend_colors=legend_colors,
                                layer_name=new_layer_name.value,
                            )
                    except Exception as e:
                        compute_label.value = "Error: " + str(e)
                    ee_layer.visible = False
                    compute_label.value = ""

            def close_btn_clicked(b):
                self.remove_control(self.vis_control)
                self.vis_control.close()
                self.vis_widget.close()

                if (
                    self.colorbar_ctrl is not None
                    and self.colorbar_ctrl in self.controls
                ):
                    self.remove_control(self.colorbar_ctrl)
                    self.colorbar_ctrl.close()
                    self.colorbar_widget.close()

            import_btn.on_click(import_btn_clicked)
            apply_btn.on_click(apply_btn_clicked)
            close_btn.on_click(close_btn_clicked)

            vis_widget.children = [
                label,
                new_layer_name,
                widgets.HBox([color, color_opacity, color_opacity_label]),
                widgets.HBox([point_size, point_shape]),
                widgets.HBox([line_width, line_type]),
                widgets.HBox(
                    [fill_color, fill_color_opacity, fill_color_opacity_label]
                ),
                style_vbox,
                widgets.HBox([import_btn, apply_btn, close_btn]),
            ]

            if geometry_type(ee_object) in ["Point", "MultiPoint"]:
                point_size.disabled = False
                point_shape.disabled = False
            else:
                point_size.disabled = True
                point_shape.disabled = True

            return vis_widget

    def add_styled_vector(
        self, ee_object, column, palette, layer_name="Untitled", **kwargs
    ):
        """Adds a styled vector to the map.

        Args:
            ee_object (object): An ee.FeatureCollection.
            column (str): The column name to use for styling.
            palette (list | dict): The palette (e.g., list of colors or a dict containing label and color pairs) to use for styling.
            layer_name (str, optional): The name to be used for the new layer. Defaults to "Untitled".
        """
        if isinstance(palette, str):
            from .colormaps import get_palette

            count = ee_object.size().getInfo()
            palette = get_palette(palette, count)

        styled_vector = vector_styling(ee_object, column, palette, **kwargs)
        self.addLayer(styled_vector.style(**{"styleProperty": "style"}), {}, layer_name)

    def add_shp(
        self,
        in_shp,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
        encoding="utf-8",
    ):
        """Adds a shapefile to the map.

        Args:
            in_shp (str): The input file path to the shapefile.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            encoding (str, optional): The encoding of the shapefile. Defaults to "utf-8".

        Raises:
            FileNotFoundError: The provided shapefile could not be found.
        """
        in_shp = os.path.abspath(in_shp)
        if not os.path.exists(in_shp):
            raise FileNotFoundError("The provided shapefile could not be found.")

        geojson = shp_to_geojson(in_shp)
        self.add_geojson(
            geojson,
            layer_name,
            style,
            hover_style,
            style_callback,
            fill_colors,
            info_mode,
            encoding,
        )

    add_shapefile = add_shp

    def add_geojson(
        self,
        in_geojson,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
        encoding="utf-8",
    ):
        """Adds a GeoJSON file to the map.

        Args:
            in_geojson (str | dict): The file path or http URL to the input GeoJSON or a dictionary containing the geojson.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            encoding (str, optional): The encoding of the GeoJSON file. Defaults to "utf-8".

        Raises:
            FileNotFoundError: The provided GeoJSON file could not be found.
        """
        import json
        import random
        import requests
        import warnings

        warnings.filterwarnings("ignore")

        style_callback_only = False

        if len(style) == 0 and style_callback is not None:
            style_callback_only = True

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

        if not style:
            style = {
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
        elif "weight" not in style:
            style["weight"] = 1

        if not hover_style:
            hover_style = {"weight": style["weight"] + 1, "fillOpacity": 0.5}

        def random_color(feature):
            return {
                "color": "black",
                "fillColor": random.choice(fill_colors),
            }

        toolbar_button = widgets.ToggleButton(
            value=True,
            tooltip="Toolbar",
            icon="info",
            layout=widgets.Layout(
                width="28px", height="28px", padding="0px 0px 0px 4px"
            ),
        )

        close_button = widgets.ToggleButton(
            value=False,
            tooltip="Close the tool",
            icon="times",
            # button_style="primary",
            layout=widgets.Layout(
                height="28px", width="28px", padding="0px 0px 0px 4px"
            ),
        )

        html = widgets.HTML()
        html.layout.margin = "0px 10px 0px 10px"
        html.layout.max_height = "250px"
        html.layout.max_width = "250px"

        output_widget = widgets.VBox(
            [widgets.HBox([toolbar_button, close_button]), html]
        )
        info_control = ipyleaflet.WidgetControl(
            widget=output_widget, position="bottomright"
        )

        if info_mode in ["on_hover", "on_click"]:
            self.add(info_control)

        def toolbar_btn_click(change):
            if change["new"]:
                close_button.value = False
                output_widget.children = [
                    widgets.VBox([widgets.HBox([toolbar_button, close_button]), html])
                ]
            else:
                output_widget.children = [widgets.HBox([toolbar_button, close_button])]

        toolbar_button.observe(toolbar_btn_click, "value")

        def close_btn_click(change):
            if change["new"]:
                toolbar_button.value = False
                if info_control in self.controls:
                    self.remove_control(info_control)
                output_widget.close()

        close_button.observe(close_btn_click, "value")

        def update_html(feature, **kwargs):
            value = [
                "<b>{}: </b>{}<br>".format(prop, feature["properties"][prop])
                for prop in feature["properties"].keys()
            ][:-1]

            value = """{}""".format("".join(value))
            html.value = value

        if style_callback is None:
            style_callback = random_color

        if style_callback_only:
            geojson = ipyleaflet.GeoJSON(
                data=data,
                hover_style=hover_style,
                style_callback=style_callback,
                name=layer_name,
            )
        else:
            geojson = ipyleaflet.GeoJSON(
                data=data,
                style=style,
                hover_style=hover_style,
                style_callback=style_callback,
                name=layer_name,
            )

        if info_mode == "on_hover":
            geojson.on_hover(update_html)
        elif info_mode == "on_click":
            geojson.on_click(update_html)

        self.add(geojson)
        self.geojson_layers.append(geojson)

        if not hasattr(self, "json_layer_dict"):
            self.json_layer_dict = {}

        params = {
            "data": geojson,
            "style": style,
            "hover_style": hover_style,
            "style_callback": style_callback,
        }
        self.json_layer_dict[layer_name] = params

    def add_kml(
        self,
        in_kml,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
    ):
        """Adds a GeoJSON file to the map.

        Args:
            in_kml (str): The input file path to the KML.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

        Raises:
            FileNotFoundError: The provided KML file could not be found.
        """

        if isinstance(in_kml, str) and in_kml.startswith("http"):
            in_kml = github_raw_url(in_kml)
            in_kml = download_file(in_kml)

        in_kml = os.path.abspath(in_kml)
        if not os.path.exists(in_kml):
            raise FileNotFoundError("The provided KML file could not be found.")
        self.add_vector(
            in_kml,
            layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            info_mode=info_mode,
        )

    def add_vector(
        self,
        filename,
        layer_name="Untitled",
        to_ee=False,
        bbox=None,
        mask=None,
        rows=None,
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
        encoding="utf-8",
        **kwargs,
    ):
        """Adds any geopandas-supported vector dataset to the map.

        Args:
            filename (str): Either the absolute or relative path to the file or URL to be opened, or any object with a read() method (such as an open file or StringIO).
            layer_name (str, optional): The layer name to use. Defaults to "Untitled".
            to_ee (bool, optional): Whether to convert the GeoJSON to ee.FeatureCollection. Defaults to False.
            bbox (tuple | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter features by given bounding box, GeoSeries, GeoDataFrame or a shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with mask. Defaults to None.
            mask (dict | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter for features that intersect with the given dict-like geojson geometry, GeoSeries, GeoDataFrame or shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with bbox. Defaults to None.
            rows (int or slice, optional): Load in specific rows by passing an integer (first n rows) or a slice() object.. Defaults to None.
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            encoding (str, optional): The encoding to use to read the file. Defaults to "utf-8".

        """
        if not filename.startswith("http"):
            filename = os.path.abspath(filename)
        else:
            filename = github_raw_url(filename)
        if to_ee:
            fc = vector_to_ee(
                filename,
                bbox=bbox,
                mask=mask,
                rows=rows,
                geodesic=True,
                **kwargs,
            )

            self.addLayer(fc, {}, layer_name)
        else:
            ext = os.path.splitext(filename)[1].lower()
            if ext == ".shp":
                self.add_shapefile(
                    filename,
                    layer_name,
                    style,
                    hover_style,
                    style_callback,
                    fill_colors,
                    info_mode,
                    encoding,
                )
            elif ext in [".json", ".geojson"]:
                self.add_geojson(
                    filename,
                    layer_name,
                    style,
                    hover_style,
                    style_callback,
                    fill_colors,
                    info_mode,
                    encoding,
                )
            else:
                geojson = vector_to_geojson(
                    filename,
                    bbox=bbox,
                    mask=mask,
                    rows=rows,
                    epsg="4326",
                    **kwargs,
                )

                self.add_geojson(
                    geojson,
                    layer_name,
                    style,
                    hover_style,
                    style_callback,
                    fill_colors,
                    info_mode,
                    encoding,
                )

    def add_osm(
        self,
        query,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
        which_result=None,
        by_osmid=False,
        buffer_dist=None,
        to_ee=False,
        geodesic=True,
    ):
        """Adds OSM data to the map.

        Args:
            query (str | dict | list): Query string(s) or structured dict(s) to geocode.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
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
            self.zoomToObject(fc)
        else:
            self.add_geojson(
                geojson,
                layer_name=layer_name,
                style=style,
                hover_style=hover_style,
                style_callback=style_callback,
                fill_colors=fill_colors,
                info_mode=info_mode,
            )
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
        from .osm import osm_gdf_from_geocode

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
        from .osm import osm_gdf_from_address

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
        from .osm import osm_gdf_from_place

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
        from .osm import osm_gdf_from_point

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
        from .osm import osm_gdf_from_polygon

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
        from .osm import osm_gdf_from_bbox

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

    def add_osm_from_view(
        self,
        tags,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
    ):
        """Adds OSM entities within the current map view to the map.

        Args:
            tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".

        """
        from .osm import osm_gdf_from_bbox

        bounds = self.bounds
        if len(bounds) == 0:
            bounds = (
                (40.74824858675827, -73.98933637940563),
                (40.75068694343106, -73.98364473187601),
            )
        north, south, east, west = (
            bounds[1][0],
            bounds[0][0],
            bounds[1][1],
            bounds[0][1],
        )

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

    def add_gdf(
        self,
        gdf,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
        zoom_to_layer=True,
        encoding="utf-8",
    ):
        """Adds a GeoDataFrame to the map.

        Args:
            gdf (GeoDataFrame): A GeoPandas GeoDataFrame.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            zoom_to_layer (bool, optional): Whether to zoom to the layer.
            encoding (str, optional): The encoding of the GeoDataFrame. Defaults to "utf-8".
        """

        data = gdf_to_geojson(gdf, epsg="4326")

        self.add_geojson(
            data,
            layer_name,
            style,
            hover_style,
            style_callback,
            fill_colors,
            info_mode,
            encoding,
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
        self,
        sql,
        con,
        layer_name="Untitled",
        style={},
        hover_style={},
        style_callback=None,
        fill_colors=["black"],
        info_mode="on_hover",
        zoom_to_layer=True,
        **kwargs,
    ):
        """Reads a PostGIS database and returns data as a GeoDataFrame to be added to the map.

        Args:
            sql (str): SQL query to execute in selecting entries from database, or name of the table to read from the database.
            con (sqlalchemy.engine.Engine): Active connection to the database to query.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            zoom_to_layer (bool, optional): Whether to zoom to the layer.
        """
        gdf = read_postgis(sql, con, **kwargs)
        gdf = gdf.to_crs("epsg:4326")
        self.add_gdf(
            gdf,
            layer_name,
            style,
            hover_style,
            style_callback,
            fill_colors,
            info_mode,
            zoom_to_layer,
        )

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
        """Adds a time slider to the map.

        Args:
            ee_object (ee.Image | ee.ImageCollection): The Image or ImageCollection to visualize.
            vis_params (dict, optional): Visualization parameters to use for visualizing image. Defaults to {}.
            region (ee.Geometry | ee.FeatureCollection): The region to visualize.
            layer_name (str, optional): The layer name to be used. Defaults to "Time series".
            labels (list, optional): The list of labels to be used for the time series. Defaults to None.
            time_interval (int, optional): Time interval in seconds. Defaults to 1.
            position (str, optional): Position to place the time slider, can be any of ['topleft', 'topright', 'bottomleft', 'bottomright']. Defaults to "bottomright".
            slider_length (str, optional): Length of the time slider. Defaults to "150px".
            date_format (str, optional): The date format to use. Defaults to 'YYYY-MM-dd'.
            opacity (float, optional): The opacity of layers. Defaults to 1.0.

        Raises:
            TypeError: If the ee_object is not ee.Image | ee.ImageCollection.
        """
        import threading

        if isinstance(ee_object, ee.Image):
            if region is not None:
                if isinstance(region, ee.Geometry):
                    ee_object = ee_object.clip(region)
                elif isinstance(region, ee.FeatureCollection):
                    ee_object = ee_object.clipToCollection(region)
            if layer_name not in self.ee_raster_layer_names:
                self.addLayer(ee_object, {}, layer_name, False, opacity)
            band_names = ee_object.bandNames()
            ee_object = ee.ImageCollection(
                ee_object.bandNames().map(lambda b: ee_object.select([b]))
            )

            if labels is not None:
                if len(labels) != int(ee_object.size().getInfo()):
                    raise ValueError(
                        "The length of labels must be equal to the number of bands in the image."
                    )
            else:
                labels = band_names.getInfo()

        elif isinstance(ee_object, ee.ImageCollection):
            if region is not None:
                if isinstance(region, ee.Geometry):
                    ee_object = ee_object.map(lambda img: img.clip(region))
                elif isinstance(region, ee.FeatureCollection):
                    ee_object = ee_object.map(lambda img: img.clipToCollection(region))

            if labels is not None:
                if len(labels) != int(ee_object.size().getInfo()):
                    raise ValueError(
                        "The length of labels must be equal to the number of images in the ImageCollection."
                    )
            else:
                labels = (
                    ee_object.aggregate_array("system:time_start")
                    .map(lambda d: ee.Date(d).format(date_format))
                    .getInfo()
                )
        else:
            raise TypeError("The ee_object must be an ee.Image or ee.ImageCollection")

        # if labels is not None:
        #     size = len(labels)
        # else:
        #     size = ee_object.size().getInfo()
        #     labels = [str(i) for i in range(1, size + 1)]

        first = ee.Image(ee_object.first())

        if layer_name not in self.ee_raster_layer_names:
            self.addLayer(ee_object.toBands(), {}, layer_name, False, opacity)
        self.addLayer(first, vis_params, "Image X", True, opacity)

        slider = widgets.IntSlider(
            min=1,
            max=len(labels),
            readout=False,
            continuous_update=False,
            layout=widgets.Layout(width=slider_length),
        )
        label = widgets.Label(
            value=labels[0], layout=widgets.Layout(padding="0px 5px 0px 5px")
        )

        play_btn = widgets.Button(
            icon="play",
            tooltip="Play the time slider",
            button_style="primary",
            layout=widgets.Layout(width="32px"),
        )

        pause_btn = widgets.Button(
            icon="pause",
            tooltip="Pause the time slider",
            button_style="primary",
            layout=widgets.Layout(width="32px"),
        )

        close_btn = widgets.Button(
            icon="times",
            tooltip="Close the time slider",
            button_style="primary",
            layout=widgets.Layout(width="32px"),
        )

        play_chk = widgets.Checkbox(value=False)

        slider_widget = widgets.HBox([slider, label, play_btn, pause_btn, close_btn])

        def play_click(b):
            import time

            play_chk.value = True

            def work(slider):
                while play_chk.value:
                    if slider.value < len(labels):
                        slider.value += 1
                    else:
                        slider.value = 1
                    time.sleep(time_interval)

            thread = threading.Thread(target=work, args=(slider,))
            thread.start()

        def pause_click(b):
            play_chk.value = False

        play_btn.on_click(play_click)
        pause_btn.on_click(pause_click)

        def slider_changed(change):
            self.default_style = {"cursor": "wait"}
            index = slider.value - 1
            label.value = labels[index]
            image = ee.Image(ee_object.toList(ee_object.size()).get(index))
            if layer_name not in self.ee_raster_layer_names:
                self.addLayer(ee_object.toBands(), {}, layer_name, False, opacity)
            self.addLayer(image, vis_params, "Image X", True, opacity)
            self.default_style = {"cursor": "default"}

        slider.observe(slider_changed, "value")

        def close_click(b):
            play_chk.value = False
            self.toolbar_reset()
            self.remove_ee_layer("Image X")
            self.remove_ee_layer(layer_name)

            if self.slider_ctrl is not None and self.slider_ctrl in self.controls:
                self.remove_control(self.slider_ctrl)
            slider_widget.close()

        close_btn.on_click(close_click)

        slider_ctrl = ipyleaflet.WidgetControl(widget=slider_widget, position=position)
        self.add(slider_ctrl)
        self.slider_ctrl = slider_ctrl

    def add_xy_data(
        self,
        in_csv,
        x="longitude",
        y="latitude",
        label=None,
        layer_name="Marker cluster",
        to_ee=False,
    ):
        """Adds points from a CSV file containing lat/lon information and display data on the map.

        Args:
            in_csv (str): The file path to the input CSV file.
            x (str, optional): The name of the column containing longitude coordinates. Defaults to "longitude".
            y (str, optional): The name of the column containing latitude coordinates. Defaults to "latitude".
            label (str, optional): The name of the column containing label information to used for marker popup. Defaults to None.
            layer_name (str, optional): The layer name to use. Defaults to "Marker cluster".
            to_ee (bool, optional): Whether to convert the csv to an ee.FeatureCollection.

        Raises:
            FileNotFoundError: The specified input csv does not exist.
            ValueError: The specified x column does not exist.
            ValueError: The specified y column does not exist.
            ValueError: The specified label column does not exist.
        """
        import pandas as pd

        if not in_csv.startswith("http") and (not os.path.exists(in_csv)):
            raise FileNotFoundError("The specified input csv does not exist.")

        df = pd.read_csv(in_csv)
        col_names = df.columns.values.tolist()

        if x not in col_names:
            raise ValueError(f"x must be one of the following: {', '.join(col_names)}")

        if y not in col_names:
            raise ValueError(f"y must be one of the following: {', '.join(col_names)}")

        if label is not None and (label not in col_names):
            raise ValueError(
                f"label must be one of the following: {', '.join(col_names)}"
            )

        self.default_style = {"cursor": "wait"}

        if to_ee:
            fc = csv_to_ee(in_csv, latitude=y, longitude=x)
            self.addLayer(fc, {}, layer_name)

        else:
            points = list(zip(df[y], df[x]))

            if label is not None:
                labels = df[label]
                markers = [
                    ipyleaflet.Marker(
                        location=point,
                        draggable=False,
                        popup=widgets.HTML(str(labels[index])),
                    )
                    for index, point in enumerate(points)
                ]
            else:
                markers = [
                    ipyleaflet.Marker(location=point, draggable=False)
                    for point in points
                ]

            marker_cluster = ipyleaflet.MarkerCluster(markers=markers, name=layer_name)
            self.add(marker_cluster)

        self.default_style = {"cursor": "default"}

    def add_points_from_xy(
        self,
        data,
        x="longitude",
        y="latitude",
        popup=None,
        layer_name="Marker Cluster",
        color_column=None,
        marker_colors=None,
        icon_colors=["white"],
        icon_names=["info"],
        spin=False,
        add_legend=True,
        **kwargs,
    ):
        """Adds a marker cluster to the map.

        Args:
            data (str | pd.DataFrame): A csv or Pandas DataFrame containing x, y, z values.
            x (str, optional): The column name for the x values. Defaults to "longitude".
            y (str, optional): The column name for the y values. Defaults to "latitude".
            popup (list, optional): A list of column names to be used as the popup. Defaults to None.
            layer_name (str, optional): The name of the layer. Defaults to "Marker Cluster".
            color_column (str, optional): The column name for the color values. Defaults to None.
            marker_colors (list, optional): A list of colors to be used for the markers. Defaults to None.
            icon_colors (list, optional): A list of colors to be used for the icons. Defaults to ['white'].
            icon_names (list, optional): A list of names to be used for the icons. More icons can be found at https://fontawesome.com/v4/icons. Defaults to ['info'].
            spin (bool, optional): If True, the icon will spin. Defaults to False.
            add_legend (bool, optional): If True, a legend will be added to the map. Defaults to True.

        """
        import pandas as pd

        data = github_raw_url(data)

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

        df = points_from_xy(df, x, y)

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

        if "geometry" in col_names:
            col_names.remove("geometry")

        if popup is not None:
            if isinstance(popup, str) and (popup not in col_names):
                raise ValueError(
                    f"popup must be one of the following: {', '.join(col_names)}"
                )
            elif isinstance(popup, list) and (
                not all(item in col_names for item in popup)
            ):
                raise ValueError(
                    f"All popup items must be select from: {', '.join(col_names)}"
                )
        else:
            popup = col_names

        df["x"] = df.geometry.x
        df["y"] = df.geometry.y

        points = list(zip(df["y"], df["x"]))

        if popup is not None:
            if isinstance(popup, str):
                labels = df[popup]

                markers = []
                for index, point in enumerate(points):
                    if items is not None:
                        marker_color = marker_colors[
                            items.index(df[color_column][index])
                        ]
                        icon_name = icon_names[items.index(df[color_column][index])]
                        icon_color = icon_colors[items.index(df[color_column][index])]
                        marker_icon = ipyleaflet.AwesomeIcon(
                            name=icon_name,
                            marker_color=marker_color,
                            icon_color=icon_color,
                            spin=spin,
                        )
                    else:
                        marker_icon = None

                    marker = ipyleaflet.Marker(
                        location=point,
                        draggable=False,
                        popup=widgets.HTML(str(labels[index])),
                        icon=marker_icon,
                    )
                    markers.append(marker)

            elif isinstance(popup, list):
                labels = []
                for i in range(len(points)):
                    label = ""
                    for item in popup:
                        label = (
                            label
                            + "<b>"
                            + str(item)
                            + "</b>"
                            + ": "
                            + str(df[item][i])
                            + "<br>"
                        )
                    labels.append(label)
                df["popup"] = labels

                markers = []
                for index, point in enumerate(points):
                    if items is not None:
                        marker_color = marker_colors[
                            items.index(df[color_column][index])
                        ]
                        icon_name = icon_names[items.index(df[color_column][index])]
                        icon_color = icon_colors[items.index(df[color_column][index])]
                        marker_icon = ipyleaflet.AwesomeIcon(
                            name=icon_name,
                            marker_color=marker_color,
                            icon_color=icon_color,
                            spin=spin,
                        )
                    else:
                        marker_icon = None

                    marker = ipyleaflet.Marker(
                        location=point,
                        draggable=False,
                        popup=widgets.HTML(labels[index]),
                        icon=marker_icon,
                    )
                    markers.append(marker)

        else:
            markers = []
            for point in points:
                if items is not None:
                    marker_color = marker_colors[items.index(df[color_column][index])]
                    icon_name = icon_names[items.index(df[color_column][index])]
                    icon_color = icon_colors[items.index(df[color_column][index])]
                    marker_icon = ipyleaflet.AwesomeIcon(
                        name=icon_name,
                        marker_color=marker_color,
                        icon_color=icon_color,
                        spin=spin,
                    )
                else:
                    marker_icon = None

                marker = ipyleaflet.Marker(
                    location=point, draggable=False, icon=marker_icon
                )
                markers.append(marker)

        marker_cluster = ipyleaflet.MarkerCluster(markers=markers, name=layer_name)
        self.add(marker_cluster)

        if items is not None and add_legend:
            marker_colors = [check_color(c) for c in marker_colors]
            self.add_legend(
                title=color_column.title(), colors=marker_colors, labels=items
            )

        self.default_style = {"cursor": "default"}

    def add_circle_markers_from_xy(
        self,
        data,
        x="longitude",
        y="latitude",
        radius=10,
        popup=None,
        **kwargs,
    ):
        """Adds a marker cluster to the map. For a list of options, see https://ipyleaflet.readthedocs.io/en/latest/api_reference/circle_marker.html

        Args:
            data (str | pd.DataFrame): A csv or Pandas DataFrame containing x, y, z values.
            x (str, optional): The column name for the x values. Defaults to "longitude".
            y (str, optional): The column name for the y values. Defaults to "latitude".
            radius (int, optional): The radius of the circle. Defaults to 10.
            popup (list, optional): A list of column names to be used as the popup. Defaults to None.

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

        if popup is None:
            popup = col_names

        if not isinstance(popup, list):
            popup = [popup]

        if x not in col_names:
            raise ValueError(f"x must be one of the following: {', '.join(col_names)}")

        if y not in col_names:
            raise ValueError(f"y must be one of the following: {', '.join(col_names)}")

        for row in df.itertuples():
            html = ""
            for p in popup:
                html = html + "<b>" + p + "</b>" + ": " + str(getattr(row, p)) + "<br>"
            popup_html = widgets.HTML(html)

            marker = ipyleaflet.CircleMarker(
                location=[getattr(row, y), getattr(row, x)],
                radius=radius,
                popup=popup_html,
                **kwargs,
            )
            super().add(marker)

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
        layer = planet_tile_by_month(year, month, name, api_key, token_name)
        self.add(layer)

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
        layer = planet_tile_by_quarter(year, quarter, name, api_key, token_name)
        self.add(layer)

    def to_streamlit(self, width=None, height=600, scrolling=False, **kwargs):
        """Renders map figure in a Streamlit app.

        Args:
            width (int, optional): Width of the map. Defaults to None.
            height (int, optional): Height of the map. Defaults to 600.
            responsive (bool, optional): Whether to make the map responsive. Defaults to True.
            scrolling (bool, optional): If True, show a scrollbar when the content is larger than the iframe. Otherwise, do not show a scrollbar. Defaults to False.

        Returns:
            streamlit.components: components.html object.
        """

        try:
            import streamlit.components.v1 as components

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

    def add_point_layer(
        self, filename, popup=None, layer_name="Marker Cluster", **kwargs
    ):
        """Adds a point layer to the map with a popup attribute.

        Args:
            filename (str): str, http url, path object or file-like object. Either the absolute or relative path to the file or URL to be opened, or any object with a read() method (such as an open file or StringIO)
            popup (str | list, optional): Column name(s) to be used for popup. Defaults to None.
            layer_name (str, optional): A layer name to use. Defaults to "Marker Cluster".

        Raises:
            ValueError: If the specified column name does not exist.
            ValueError: If the specified column names do not exist.
        """
        import warnings

        warnings.filterwarnings("ignore")
        check_package(name="geopandas", URL="https://geopandas.org")
        import geopandas as gpd

        self.default_style = {"cursor": "wait"}

        if not filename.startswith("http"):
            filename = os.path.abspath(filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".kml":
            gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
            gdf = gpd.read_file(filename, driver="KML", **kwargs)
        else:
            gdf = gpd.read_file(filename, **kwargs)
        df = gdf.to_crs(epsg="4326")
        col_names = df.columns.values.tolist()
        if popup is not None:
            if isinstance(popup, str) and (popup not in col_names):
                raise ValueError(
                    f"popup must be one of the following: {', '.join(col_names)}"
                )
            elif isinstance(popup, list) and (
                not all(item in col_names for item in popup)
            ):
                raise ValueError(
                    f"All popup items must be select from: {', '.join(col_names)}"
                )

        df["x"] = df.geometry.x
        df["y"] = df.geometry.y

        points = list(zip(df["y"], df["x"]))

        if popup is not None:
            if isinstance(popup, str):
                labels = df[popup]
                markers = [
                    ipyleaflet.Marker(
                        location=point,
                        draggable=False,
                        popup=widgets.HTML(str(labels[index])),
                    )
                    for index, point in enumerate(points)
                ]
            elif isinstance(popup, list):
                labels = []
                for i in range(len(points)):
                    label = ""
                    for item in popup:
                        label = label + str(item) + ": " + str(df[item][i]) + "<br>"
                    labels.append(label)
                df["popup"] = labels

                markers = [
                    ipyleaflet.Marker(
                        location=point,
                        draggable=False,
                        popup=widgets.HTML(labels[index]),
                    )
                    for index, point in enumerate(points)
                ]

        else:
            markers = [
                ipyleaflet.Marker(location=point, draggable=False) for point in points
            ]

        marker_cluster = ipyleaflet.MarkerCluster(markers=markers, name=layer_name)
        self.add(marker_cluster)

        self.default_style = {"cursor": "default"}

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
            self.add_tile_layer(url, name, attribution)
        else:
            raise ValueError(
                f"The provider {provider} is not valid. It must start with xyz or qms."
            )

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
        """Adds a heat map to the map. Reference: https://ipyleaflet.readthedocs.io/en/latest/api_reference/heatmap.html

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
        from ipyleaflet import Heatmap

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

            heatmap = Heatmap(locations=data, radius=radius, name=name, **kwargs)
            self.add(heatmap)

        except Exception as e:
            raise Exception(e)

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
        """Adds a label layer to the map. Reference: https://ipyleaflet.readthedocs.io/en/latest/api_reference/divicon.html

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
            layer_name (str, optional): Layer name to use. Defaults to "Labels".

        """
        import warnings
        import pandas as pd

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
                except Exception as _:
                    print("geopandas is required to read geojson.")
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
        except:
            raise ValueError("font_size must be something like '10pt'")

        labels = []
        for index in df.index:
            html = f'<div style="font-size: {font_size};color:{font_color};font-family:{font_family};font-weight: {font_weight}">{df[column][index]}</div>'
            marker = ipyleaflet.Marker(
                location=[df[y][index], df[x][index]],
                icon=ipyleaflet.DivIcon(
                    icon_size=(1, 1),
                    icon_anchor=(size, size),
                    html=html,
                    **kwargs,
                ),
                draggable=draggable,
            )
            labels.append(marker)
        layer_group = ipyleaflet.LayerGroup(layers=labels, name=layer_name)
        self.add(layer_group)
        self.labels = layer_group

    def remove_labels(self):
        """Removes all labels from the map."""
        if hasattr(self, "labels"):
            self.remove_layer(self.labels)
            delattr(self, "labels")

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

    def add_velocity(
        self,
        data,
        zonal_speed,
        meridional_speed,
        latitude_dimension="lat",
        longitude_dimension="lon",
        level_dimension="lev",
        level_index=0,
        time_index=0,
        velocity_scale=0.01,
        max_velocity=20,
        display_options={},
        name="Velocity",
    ):
        """Add a velocity layer to the map.

        Args:
            data (str | xr.Dataset): The data to use for the velocity layer. It can be a file path to a NetCDF file or an xarray Dataset.
            zonal_speed (str): Name of the zonal speed in the dataset. See https://en.wikipedia.org/wiki/Zonal_and_meridional_flow.
            meridional_speed (str): Name of the meridional speed in the dataset. See https://en.wikipedia.org/wiki/Zonal_and_meridional_flow.
            latitude_dimension (str, optional): Name of the latitude dimension in the dataset. Defaults to 'lat'.
            longitude_dimension (str, optional): Name of the longitude dimension in the dataset. Defaults to 'lon'.
            level_dimension (str, optional): Name of the level dimension in the dataset. Defaults to 'lev'.
            level_index (int, optional): The index of the level dimension to display. Defaults to 0.
            time_index (int, optional): The index of the time dimension to display. Defaults to 0.
            velocity_scale (float, optional): The scale of the velocity. Defaults to 0.01.
            max_velocity (int, optional): The maximum velocity to display. Defaults to 20.
            display_options (dict, optional): The display options for the velocity layer. Defaults to {}. See https://bit.ly/3uf8t6w.
            name (str, optional): Layer name to use . Defaults to 'Velocity'.

        Raises:
            ImportError: If the xarray package is not installed.
            ValueError: If the data is not a NetCDF file or an xarray Dataset.
        """
        try:
            import xarray as xr
            from ipyleaflet.velocity import Velocity
        except ImportError:
            raise ImportError(
                "The xarray package is required to add a velocity layer. "
                "Please install it with `pip install xarray`."
            )

        if isinstance(data, str):
            if data.startswith("http"):
                data = download_file(data)
            ds = xr.open_dataset(data)

        elif isinstance(data, xr.Dataset):
            ds = data
        else:
            raise ValueError("The data must be a file path or xarray dataset.")

        coords = list(ds.coords.keys())

        # Rasterio does not handle time or levels. So we must drop them
        if "time" in coords:
            ds = ds.isel(time=time_index, drop=True)

        params = {level_dimension: level_index}
        if level_dimension in coords:
            ds = ds.isel(drop=True, **params)

        wind = Velocity(
            data=ds,
            zonal_speed=zonal_speed,
            meridional_speed=meridional_speed,
            latitude_dimension=latitude_dimension,
            longitude_dimension=longitude_dimension,
            velocity_scale=velocity_scale,
            max_velocity=max_velocity,
            display_options=display_options,
            name=name,
        )
        self.add(wind)

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
        layer_name="Untitled",
        style=None,
        hover_style=None,
        style_callback=None,
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
            style (dict, optional): A dictionary specifying the style to be used. Defaults to None.
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
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
                hover_style is a dictionary of the following form:
                    hover_style = {"weight": style["weight"] + 1, "fillOpacity": 0.5}
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
                style_callback is a function that takes the feature as argument and should return a dictionary of the following form:
                style_callback = lambda feat: {"fillColor": feat["properties"]["color"]}
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            encoding (str, optional): The encoding of the GeoJSON file. Defaults to "utf-8".
        """

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

        if style is None:
            style = {
                # "stroke": False,
                # "color": "#ff0000",
                "weight": 1,
                "opacity": 1,
                # "fill": True,
                # "fillColor": "#ffffff",
                "fillOpacity": 1.0,
                # "dashArray": "9"
                # "clickable": True,
            }
            if colors is not None:
                style["color"] = "#000000"

        if hover_style is None:
            hover_style = {"weight": style["weight"] + 1, "fillOpacity": 0.5}

        if style_callback is None:
            style_callback = lambda feat: {"fillColor": feat["properties"]["color"]}

        self.add_gdf(
            gdf,
            layer_name=layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            info_mode=info_mode,
            encoding=encoding,
            **kwargs,
        )
        if add_legend:
            self.add_legend(title=legend_title, legend_dict=legend_dict)

    def user_roi_coords(self, decimals=4):
        """Return the bounding box of the ROI as a list of coordinates.

        Args:
            decimals (int, optional): Number of decimals to round the coordinates to. Defaults to 4.
        """
        return bbox_coords(self.user_roi, decimals=decimals)

    def _point_info(self, latlon, decimals=3, return_node=False):
        """Create the ipytree widget for displaying the mouse clicking info.

        Args:
            latlon (list | tuple): The coordinates (lat, lon) of the point.
            decimals (int, optional): Number of decimals to round the coordinates to. Defaults to 3.
            return_node (bool, optional): If True, return the ipytree node.
                Otherwise, return the ipytree tree widget. Defaults to False.

        Returns:
            ipytree.Node | ipytree.Tree: The ipytree node or tree widget.
        """
        from ipytree import Node, Tree

        point_nodes = [
            Node(f"Longitude: {latlon[1]}"),
            Node(f"Latitude: {latlon[0]}"),
            Node(f"Zoom Level: {self.zoom}"),
            Node(f"Scale (approx. m/px): {self.get_scale()}"),
        ]
        label = f"Point ({latlon[1]:.{decimals}f}, {latlon[0]:.{decimals}f}) at {int(self.get_scale())}m/px"
        root_node = Node(
            label, nodes=point_nodes, icon="map", opened=self._expand_point
        )

        root_node.open_icon = "plus-square"
        root_node.open_icon_style = "success"
        root_node.close_icon = "minus-square"
        root_node.close_icon_style = "info"

        if return_node:
            return root_node
        else:
            return Tree(nodes=[root_node])

    def _pixels_info(
        self, latlon, names=None, visible=True, decimals=2, return_node=False
    ):
        """Create the ipytree widget for displaying the pixel values at the mouse clicking point.

        Args:
            latlon (list | tuple): The coordinates (lat, lon) of the point.
            names (str | list, optional): The names of the layers to be included. Defaults to None.
            visible (bool, optional): Whether to inspect visible layers only. Defaults to True.
            decimals (int, optional): Number of decimals to round the pixel values. Defaults to 2.
            return_node (bool, optional): If True, return the ipytree node.
                Otherwise, return the ipytree tree widget. Defaults to False.

        Returns:
            ipytree.Node | ipytree.Tree: The ipytree node or tree widget.
        """
        from ipytree import Node, Tree

        if names is not None:
            if isinstance(names, str):
                names = [names]
            layers = {}
            for name in names:
                if name in self.ee_layer_names:
                    layers[name] = self.ee_layer_dict[name]
        else:
            layers = self.ee_layer_dict
        xy = ee.Geometry.Point(latlon[::-1])
        sample_scale = self.getScale()

        root_node = Node("Pixels", icon="archive")

        nodes = []

        for layer in layers:
            layer_name = layer
            ee_object = layers[layer]["ee_object"]
            object_type = ee_object.__class__.__name__

            if visible:
                if not self.ee_layer_dict[layer_name]["ee_layer"].visible:
                    continue

            try:
                if isinstance(ee_object, ee.ImageCollection):
                    ee_object = ee_object.mosaic()

                if isinstance(ee_object, ee.Image):
                    item = ee_object.reduceRegion(
                        ee.Reducer.first(), xy, sample_scale
                    ).getInfo()
                    b_name = "band"
                    if len(item) > 1:
                        b_name = "bands"

                    label = f"{layer_name}: {object_type} ({len(item)} {b_name})"
                    layer_node = Node(label, opened=self._expand_pixels)

                    keys = sorted(item.keys())
                    for key in keys:
                        value = item[key]
                        if isinstance(value, float):
                            value = round(value, decimals)
                        layer_node.add_node(Node(f"{key}: {value}", icon="file"))

                    nodes.append(layer_node)
            except:
                pass

        root_node.nodes = nodes

        root_node.open_icon = "plus-square"
        root_node.open_icon_style = "success"
        root_node.close_icon = "minus-square"
        root_node.close_icon_style = "info"

        if return_node:
            return root_node
        else:
            return Tree(nodes=[root_node])

    def _objects_info(self, latlon, names=None, visible=True, return_node=False):
        """Create the ipytree widget for displaying the Earth Engine objects at the mouse clicking point.

        Args:
            latlon (list | tuple): The coordinates (lat, lon) of the point.
            names (str | list, optional): The names of the layers to be included. Defaults to None.
            visible (bool, optional): Whether to inspect visible layers only. Defaults to True.
            return_node (bool, optional): If True, return the ipytree node.
                Otherwise, return the ipytree tree widget. Defaults to False.

        Returns:
            ipytree.Node | ipytree.Tree: The ipytree node or tree widget.
        """
        from ipytree import Node, Tree

        if names is not None:
            if isinstance(names, str):
                names = [names]
            layers = {}
            for name in names:
                if name in self.ee_layer_names:
                    layers[name] = self.ee_layer_dict[name]
        else:
            layers = self.ee_layer_dict

        xy = ee.Geometry.Point(latlon[::-1])
        root_node = Node("Objects", icon="archive")

        nodes = []

        for layer in layers:
            layer_name = layer
            ee_object = layers[layer]["ee_object"]

            if visible:
                if not self.ee_layer_dict[layer_name]["ee_layer"].visible:
                    continue

            if isinstance(ee_object, ee.FeatureCollection):
                # Check geometry type
                geom_type = ee.Feature(ee_object.first()).geometry().type()
                lat, lon = latlon
                delta = 0.005
                bbox = ee.Geometry.BBox(
                    lon - delta,
                    lat - delta,
                    lon + delta,
                    lat + delta,
                )
                # Create a bounding box to filter points
                xy = ee.Algorithms.If(
                    geom_type.compareTo(ee.String("Point")),
                    xy,
                    bbox,
                )

                ee_object = ee_object.filterBounds(xy).first()

            try:
                node = get_info(
                    ee_object, layer_name, opened=self._expand_objects, return_node=True
                )
                nodes.append(node)
            except:
                pass

        root_node.nodes = nodes

        root_node.open_icon = "plus-square"
        root_node.open_icon_style = "success"
        root_node.close_icon = "minus-square"
        root_node.close_icon_style = "info"

        if return_node:
            return root_node
        else:
            return Tree(nodes=[root_node])

    def inspect(self, latlon):
        """Create the Inspector GUI.

        Args:
            latlon (list | tuple): The coordinates (lat, lon) of the point.
        Returns:
            ipytree.Tree: The ipytree tree widget for the Inspector GUI.
        """
        from ipytree import Tree

        tree = Tree()
        nodes = []
        point_node = self._point_info(latlon, return_node=True)
        nodes.append(point_node)
        pixels_node = self._pixels_info(latlon, return_node=True)
        if pixels_node.nodes:
            nodes.append(pixels_node)
        objects_node = self._objects_info(latlon, return_node=True)
        if objects_node.nodes:
            nodes.append(objects_node)
        tree.nodes = nodes
        return tree

    def add_inspector(
        self, names=None, visible=True, decimals=2, position="topright", opened=True
    ):
        """Add the Inspector GUI to the map.

        Args:
            names (str | list, optional): The names of the layers to be included. Defaults to None.
            visible (bool, optional): Whether to inspect visible layers only. Defaults to True.
            decimals (int, optional): The number of decimal places to round the coordinates. Defaults to 2.
            position (str, optional): The position of the Inspector GUI. Defaults to "topright".
            opened (bool, optional): Whether the control is opened. Defaults to True.

        """
        from .toolbar import ee_inspector_gui

        ee_inspector_gui(self, names, visible, decimals, position, opened)

    def add_layer_manager(self, position="topright", opened=True):
        """Add the Layer Manager to the map.

        Args:
            position (str, optional): The position of the Layer Manager. Defaults to "topright".
        """
        from .toolbar import layer_manager_gui

        layer_manager_gui(self, position, opened)

    def update_layer_manager(self):
        """Update the Layer Manager."""
        from .toolbar import layer_manager_gui

        self.layer_manager_widget.children = layer_manager_gui(self, return_widget=True)

    def add_widget(self, content, position="bottomright", **kwargs):
        """Add a widget (e.g., text, HTML, figure) to the map.

        Args:
            content (str | ipywidgets.Widget | object): The widget to add.
            position (str, optional): The position of the widget. Defaults to "bottomright".
            **kwargs: Other keyword arguments for ipywidgets.HTML().
        """

        allowed_positions = ["topleft", "topright", "bottomleft", "bottomright"]

        if position not in allowed_positions:
            raise Exception(f"position must be one of {allowed_positions}")

        if "layout" not in kwargs:
            kwargs["layout"] = widgets.Layout(padding="0px 4px 0px 4px")
        try:
            if isinstance(content, str):
                widget = widgets.HTML(value=content, **kwargs)
                control = ipyleaflet.WidgetControl(widget=widget, position=position)
            else:
                output = widgets.Output(**kwargs)
                with output:
                    display(content)
                control = ipyleaflet.WidgetControl(widget=output, position=position)
            self.add(control)

        except Exception as e:
            raise Exception(f"Error adding widget: {e}")

    def add_image(self, image, position="bottomright", **kwargs):
        """Add an image to the map.

        Args:
            image (str | ipywidgets.Image): The image to add.
            position (str, optional): The position of the image, can be one of "topleft",
                "topright", "bottomleft", "bottomright". Defaults to "bottomright".

        """

        if isinstance(image, str):
            if image.startswith("http"):
                image = widgets.Image(value=requests.get(image).content, **kwargs)
            elif os.path.exists(image):
                with open(image, "rb") as f:
                    image = widgets.Image(value=f.read(), **kwargs)
        elif isinstance(image, widgets.Image):
            pass
        else:
            raise Exception("Invalid image")

        self.add_widget(image, position=position)

    def add_html(self, html, position="bottomright", **kwargs):
        """Add HTML to the map.

        Args:
            html (str): The HTML to add.
            position (str, optional): The position of the HTML, can be one of "topleft",
                "topright", "bottomleft", "bottomright". Defaults to "bottomright".
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

        print(
            "The ipyleaflet plotting backend does not support this function. Please use the folium backend instead."
        )

    def add_search_control(
        self,
        marker=None,
        url=None,
        zoom=5,
        property_name="display_name",
        position="topleft",
    ):
        """Add a search control to the map.

        Args:
            marker (ipyleaflet.Marker, optional): The marker to use. Defaults to None.
            url (str, optional): The URL to use for the search. Defaults to None.
            zoom (int, optional): The zoom level to use. Defaults to 5.
            property_name (str, optional): The property name to use. Defaults to "display_name".
            position (str, optional): The position of the widget. Defaults to "topleft".
        """
        if marker is None:
            marker = ipyleaflet.Marker(
                icon=ipyleaflet.AwesomeIcon(
                    name="check", marker_color="green", icon_color="darkgreen"
                )
            )

        if url is None:
            url = "https://nominatim.openstreetmap.org/search?format=json&q={s}"
        search = ipyleaflet.SearchControl(
            position=position,
            url=url,
            zoom=zoom,
            property_name=property_name,
            marker=marker,
        )
        self.add(search)

    def add_draw_control(self):
        """Add a draw control to the map"""

        draw_control = ipyleaflet.DrawControl(
            marker={"shapeOptions": {"color": "#3388ff"}},
            rectangle={"shapeOptions": {"color": "#3388ff"}},
            circle={"shapeOptions": {"color": "#3388ff"}},
            circlemarker={},
            edit=True,
            remove=True,
        )

        # Handles draw events
        def handle_draw(target, action, geo_json):
            try:
                self.roi_start = True
                geom = geojson_to_ee(geo_json, False)
                self.user_roi = geom
                feature = ee.Feature(geom)
                self.draw_last_json = geo_json
                self.draw_last_feature = feature
                if action == "deleted" and len(self.draw_features) > 0:
                    self.draw_features.remove(feature)
                    self.draw_count -= 1
                else:
                    self.draw_features.append(feature)
                    self.draw_count += 1
                collection = ee.FeatureCollection(self.draw_features)
                self.user_rois = collection
                ee_draw_layer = ee_tile_layer(
                    collection, {"color": "blue"}, "Drawn Features", False, 0.5
                )
                draw_layer_index = self.find_layer_index("Drawn Features")

                if draw_layer_index == -1:
                    self.add(ee_draw_layer)
                    self.draw_layer = ee_draw_layer
                else:
                    self.substitute_layer(self.draw_layer, ee_draw_layer)
                    self.draw_layer = ee_draw_layer
                self.roi_end = True
                self.roi_start = False
            except Exception as e:
                self.draw_count = 0
                self.draw_features = []
                self.draw_last_feature = None
                self.draw_layer = None
                self.user_roi = None
                self.roi_start = False
                self.roi_end = False
                print("There was an error creating Earth Engine Feature.")
                raise Exception(e)

        draw_control.on_draw(handle_draw)
        self.add(draw_control)
        self.draw_control = draw_control

    def add_draw_control_lite(self):
        """Add a lite version draw control to the map for the plotting tool."""

        draw_control_lite = ipyleaflet.DrawControl(
            marker={},
            rectangle={"shapeOptions": {"color": "#3388ff"}},
            circle={"shapeOptions": {"color": "#3388ff"}},
            circlemarker={},
            polyline={},
            polygon={},
            edit=False,
            remove=False,
        )
        self.draw_control_lite = draw_control_lite

    def add_toolbar(self, position="topright", **kwargs):
        from .toolbar import main_toolbar

        main_toolbar(self, position, **kwargs)

    def add_plot_gui(self, position="topright", **kwargs):
        """Adds the plot widget to the map.

        Args:
            position (str, optional): Position of the widget. Defaults to "topright".
        """

        from .toolbar import ee_plot_gui

        ee_plot_gui(self, position, **kwargs)


# The functions below are outside the Map class.


class ImageOverlay(ipyleaflet.ImageOverlay):
    """ImageOverlay class.

    Args:
        url (str): http URL or local file path to the image.
        bounds (tuple): bounding box of the image in the format of (lower_left(lat, lon), upper_right(lat, lon)), such as ((13, -130), (32, -100)).
        name (str): The name of the layer.
    """

    def __init__(self, **kwargs):
        from base64 import b64encode
        from PIL import Image, ImageSequence
        from io import BytesIO

        try:
            url = kwargs.get("url")
            if not url.startswith("http"):
                url = os.path.abspath(url)
                if not os.path.exists(url):
                    raise FileNotFoundError("The provided file does not exist.")

                ext = os.path.splitext(url)[1][1:]  # file extension
                image = Image.open(url)

                f = BytesIO()
                if ext.lower() == "gif":
                    frames = []
                    # Loop over each frame in the animated image
                    for frame in ImageSequence.Iterator(image):
                        frame = frame.convert("RGBA")
                        b = BytesIO()
                        frame.save(b, format="gif")
                        frame = Image.open(b)
                        frames.append(frame)
                    frames[0].save(
                        f,
                        format="GIF",
                        save_all=True,
                        append_images=frames[1:],
                        loop=0,
                    )
                else:
                    image.save(f, ext)

                data = b64encode(f.getvalue())
                data = data.decode("ascii")
                url = "data:image/{};base64,".format(ext) + data
                kwargs["url"] = url
        except Exception as e:
            raise Exception(e)

        super().__init__(**kwargs)


def ee_tile_layer(
    ee_object, vis_params={}, name="Layer untitled", shown=True, opacity=1.0
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
    tile_layer = ipyleaflet.TileLayer(
        url=map_id_dict["tile_fetcher"].url_format,
        attribution="Google Earth Engine",
        name=name,
        opacity=opacity,
        visible=shown,
    )
    return tile_layer


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
    """Create linked maps of Earth Engine data layers.

    Args:
        rows (int, optional): The number of rows of maps to create. Defaults to 2.
        cols (int, optional): The number of columns of maps to create. Defaults to 2.
        height (str, optional): The height of each map in pixels. Defaults to "400px".
        ee_objects (list, optional): The list of Earth Engine objects to use for each map. Defaults to [].
        vis_params (list, optional): The list of visualization parameters to use for each map. Defaults to [].
        labels (list, optional): The list of labels to show on the map. Defaults to [].
        label_position (str, optional): The position of the label, can be [topleft, topright, bottomleft, bottomright]. Defaults to "topright".

    Raises:
        ValueError: If the length of ee_objects is not equal to rows*cols.
        ValueError: If the length of vis_params is not equal to rows*cols.
        ValueError: If the length of labels is not equal to rows*cols.

    Returns:
        ipywidget: A GridspecLayout widget.
    """
    grid = widgets.GridspecLayout(rows, cols, grid_gap="0px")
    count = rows * cols

    maps = []

    if len(ee_objects) > 0:
        if len(ee_objects) == 1:
            ee_objects = ee_objects * count
        elif len(ee_objects) < count:
            raise ValueError(f"The length of ee_objects must be equal to {count}.")

    if len(vis_params) > 0:
        if len(vis_params) == 1:
            vis_params = vis_params * count
        elif len(vis_params) < count:
            raise ValueError(f"The length of vis_params must be equal to {count}.")

    if len(labels) > 0:
        if len(labels) == 1:
            labels = labels * count
        elif len(labels) < count:
            raise ValueError(f"The length of labels must be equal to {count}.")

    for i in range(rows):
        for j in range(cols):
            index = i * rows + j
            m = Map(
                height=height,
                lite_mode=True,
                add_google_map=False,
                layout=widgets.Layout(margin="0px", padding="0px"),
                **kwargs,
            )

            if len(ee_objects) > 0:
                m.addLayer(ee_objects[index], vis_params[index], labels[index])

            if len(labels) > 0:
                label = widgets.Label(
                    labels[index], layout=widgets.Layout(padding="0px 5px 0px 5px")
                )
                control = ipyleaflet.WidgetControl(
                    widget=label, position=label_position
                )
                m.add(control)

            maps.append(m)
            widgets.jslink((maps[0], "center"), (m, "center"))
            widgets.jslink((maps[0], "zoom"), (m, "zoom"))

            output = widgets.Output()
            with output:
                display(m)
            grid[i, j] = output

    return grid


def ts_inspector(
    layers_dict=None,
    left_name=None,
    right_name=None,
    width="120px",
    center=[40, -100],
    zoom=4,
    **kwargs,
):
    """Creates a time series inspector.

    Args:
        layers_dict (dict, optional): A dictionary of layers to be shown on the map. Defaults to None.
        left_name (str, optional): A name for the left layer. Defaults to None.
        right_name (str, optional): A name for the right layer. Defaults to None.
        width (str, optional): Width of the dropdown list. Defaults to "120px".
        center (list, optional): Center of the map. Defaults to [40, -100].
        zoom (int, optional): Zoom level of the map. Defaults to 4.

    Returns:
        leafmap.Map: The Map instance.
    """
    import ipywidgets as widgets

    add_zoom = True
    add_fullscreen = True

    if "toolbar_control" not in kwargs:
        kwargs["toolbar_control"] = False
    if "draw_control" not in kwargs:
        kwargs["draw_control"] = False
    if "measure_control" not in kwargs:
        kwargs["measure_control"] = False
    if "zoom_control" not in kwargs:
        kwargs["zoom_control"] = False
    else:
        add_zoom = kwargs["zoom_control"]
    if "fullscreen_control" not in kwargs:
        kwargs["fullscreen_control"] = False
    else:
        add_fullscreen = kwargs["fullscreen_control"]

    if layers_dict is None:
        layers_dict = {}
        keys = dict(basemaps).keys()
        for key in keys:
            if basemaps[key]["type"] == "wms":
                pass
            else:
                layers_dict[key] = basemaps[key]

    keys = list(layers_dict.keys())
    if left_name is None:
        left_name = keys[0]
    if right_name is None:
        right_name = keys[-1]

    left_layer = layers_dict[left_name]
    right_layer = layers_dict[right_name]

    m = Map(center=center, zoom=zoom, **kwargs)
    control = ipyleaflet.SplitMapControl(left_layer=left_layer, right_layer=right_layer)
    m.add(control)
    m.dragging = False

    left_dropdown = widgets.Dropdown(
        options=keys, value=left_name, layout=widgets.Layout(width=width)
    )

    left_control = ipyleaflet.WidgetControl(widget=left_dropdown, position="topleft")
    m.add(left_control)

    right_dropdown = widgets.Dropdown(
        options=keys, value=right_name, layout=widgets.Layout(width=width)
    )

    right_control = ipyleaflet.WidgetControl(widget=right_dropdown, position="topright")
    m.add(right_control)

    if add_zoom:
        m.add(ipyleaflet.ZoomControl())
    if add_fullscreen:
        m.add(ipyleaflet.FullScreenControl())

    split_control = None
    for ctrl in m.controls:
        if isinstance(ctrl, ipyleaflet.SplitMapControl):
            split_control = ctrl
            break

    def left_change(change):
        split_control.left_layer.url = layers_dict[left_dropdown.value].url

    left_dropdown.observe(left_change, "value")

    def right_change(change):
        split_control.right_layer.url = layers_dict[right_dropdown.value].url

    right_dropdown.observe(right_change, "value")

    return m


def get_basemap(name):
    """Gets a basemap tile layer by name.

    Args:
        name (str): The name of the basemap.

    Returns:
        ipylealfet.TileLayer | ipyleaflet.WMSLayer: The basemap layer.
    """

    if isinstance(name, str):
        if name in basemaps.keys():
            basemap = basemaps[name]
            if basemap["type"] == "xyz":
                layer = ipyleaflet.TileLayer(
                    url=basemap["url"],
                    name=basemap["name"],
                    max_zoom=24,
                    attribution=basemap["attribution"],
                )
            elif basemap["type"] == "wms":
                layer = ipyleaflet.WMSLayer(
                    url=basemap["url"],
                    layers=basemap["layers"],
                    name=basemap["name"],
                    attribution=basemap["attribution"],
                    format=basemap["format"],
                    transparent=basemap["transparent"],
                )
            return layer
        else:
            raise ValueError(
                "Basemap must be a string. Please choose from: "
                + str(list(basemaps.keys()))
            )
    else:
        raise ValueError(
            "Basemap must be a string. Please choose from: "
            + str(list(basemaps.keys()))
        )
