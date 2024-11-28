"""Main module for interactive mapping using Google Earth Engine Python API and ipyleaflet.
Keep in mind that Earth Engine functions use both camel case and snake case,
such as setOptions(), setCenter(), centerObject(), addLayer().
ipyleaflet functions use snake case, such as add_tile_layer(), add_wms_layer(), add_minimap().
"""

# *******************************************************************************#
# This module contains core features and extra features of the geemap package.   #
# The Earth Engine team and the geemap community will maintain the core features.#
# The geemap community will maintain the extra features.                         #
# The core features include classes and functions below until the line # ******* #
# *******************************************************************************#

import os
import warnings
from typing import List, Dict, Any, Optional, Union

import ee
import ipyleaflet
import ipywidgets as widgets

from box import Box
from bqplot import pyplot as plt

from IPython.display import display
from .basemaps import get_xyz_dict, xyz_to_leaflet
from .common import *
from .conversion import *
from .ee_tile_layers import *
from . import core
from . import map_widgets
from . import toolbar
from .plot import *
from .timelapse import *
from .legends import builtin_legends
from . import examples


basemaps = Box(xyz_to_leaflet(), frozen_box=True)


class Map(core.Map):
    """The Map class inherits the core Map class. The arguments you can pass to the Map initialization
        can be found at https://ipyleaflet.readthedocs.io/en/latest/map_and_basemaps/map.html.
        By default, the Map will add Google Maps as the basemap. Set add_google_map = False
        to use OpenStreetMap as the basemap.

    Returns:
        object: ipyleaflet map object.
    """

    # Map attributes for drawing features
    @property
    def draw_control(self) -> Any:
        """Gets the draw control.

        Returns:
            Any: The draw control.
        """
        return self.get_draw_control()

    @property
    def draw_control_lite(self) -> Any:
        """Gets the lite version of the draw control.

        Returns:
            Any: The lite draw control.
        """
        return self.get_draw_control()

    @property
    def draw_features(self) -> List[Any]:
        """Gets the drawn features.

        Returns:
            List[Any]: The list of drawn features.
        """
        return self._draw_control.features if self._draw_control else []

    @property
    def draw_last_feature(self) -> Optional[Any]:
        """Gets the last drawn feature.

        Returns:
            Optional[Any]: The last drawn feature.
        """
        return self._draw_control.last_feature if self._draw_control else None

    @property
    def draw_layer(self) -> Optional[Any]:
        """Gets the draw layer.

        Returns:
            Optional[Any]: The draw layer.
        """
        return self._draw_control.layer if self._draw_control else None

    @property
    def user_roi(self) -> Optional[Any]:
        """Gets the user region of interest.

        Returns:
            Optional[Any]: The user region of interest.
        """
        return self._draw_control.last_geometry if self._draw_control else None

    @property
    def user_rois(self) -> Optional[Any]:
        """Gets the user regions of interest.

        Returns:
            Optional[Any]: The user regions of interest.
        """
        return self._draw_control.collection if self._draw_control else None

    def __init__(self, **kwargs):
        """Initialize a map object. The following additional parameters can be
            passed in addition to the ipyleaflet.Map parameters:

        Args:
            ee_initialize (bool, optional): Whether or not to initialize ee. Defaults to True.
            center (list, optional): Center of the map (lat, lon). Defaults to [20, 0].
            zoom (int, optional): Zoom level of the map. Defaults to 2.
            height (str, optional): Height of the map. Defaults to "600px".
            width (str, optional): Width of the map. Defaults to "100%".
            basemap (str, optional): Name of the basemap to add to the map.
                Defaults to "ROADMAP". Other options include "ROADMAP", "SATELLITE", "TERRAIN".
            add_google_map (bool, optional): Whether to add Google Maps to the map. Defaults to True.
            sandbox_path (str, optional): The path to a sandbox folder for voila web app. Defaults to None.
            lite_mode (bool, optional): Whether to enable lite mode, which only displays
                zoom control on the map. Defaults to False.
            data_ctrl (bool, optional): Whether to add the data control to the map. Defaults to True.
            zoom_ctrl (bool, optional): Whether to add the zoom control to the map. Defaults to True.
            fullscreen_ctrl (bool, optional): Whether to add the fullscreen control to the map. Defaults to True.
            search_ctrl (bool, optional): Whether to add the search control to the map. Defaults to True.
            draw_ctrl (bool, optional): Whether to add the draw control to the map. Defaults to True.
            scale_ctrl (bool, optional): Whether to add the scale control to the map. Defaults to True.
            measure_ctrl (bool, optional): Whether to add the measure control to the map. Defaults to True.
            toolbar_ctrl (bool, optional): Whether to add the toolbar control to the map. Defaults to True.
            layer_ctrl (bool, optional): Whether to add the layer control to the map. Defaults to False.
            attribution_ctrl (bool, optional): Whether to add the attribution control to the map. Defaults to True.
            **kwargs: Additional keyword arguments for ipyleaflet.Map.
        """
        warnings.filterwarnings("ignore")

        if isinstance(kwargs.get("height"), int):
            kwargs["height"] = str(kwargs["height"]) + "px"
        if isinstance(kwargs.get("width"), int):
            kwargs["width"] = str(kwargs["width"]) + "px"

        if "max_zoom" not in kwargs:
            kwargs["max_zoom"] = 24

        self._xyz_dict = get_xyz_dict()

        self.baseclass = "ipyleaflet"
        self._USER_AGENT_PREFIX = "geemap"
        self.kwargs = kwargs
        super().__init__(**kwargs)
        self._var_name = "Map"  # The Map variable name for converting JS to Python

        if kwargs.get("height"):
            self.layout.height = kwargs.get("height")

        # sandbox path for Voila app to restrict access to system directories.
        if "sandbox_path" not in kwargs:
            self.sandbox_path = None
        else:
            if os.path.exists(os.path.abspath(kwargs["sandbox_path"])):
                self.sandbox_path = kwargs["sandbox_path"]
            else:
                print("The sandbox path is invalid.")
                self.sandbox_path = None

        # Add Google Maps as the default basemap
        if kwargs.get("add_google_map", False):
            self.add_basemap("ROADMAP")

        # ipyleaflet built-in layer control
        self.layer_control = None

        if "ee_initialize" not in kwargs:
            kwargs["ee_initialize"] = True

        # Default reducer to use
        if kwargs["ee_initialize"]:
            self.roi_reducer = ee.Reducer.mean()
        self.roi_reducer_scale = None

    def _control_config(self) -> Dict[str, List[str]]:
        """Configures the map controls based on the provided arguments.

        Returns:
            Dict[str, List[str]]: The configuration of map controls.
        """
        if self.kwargs.get("lite_mode"):
            return {"topleft": ["zoom_control"]}

        topleft = []
        bottomleft = []
        topright = []
        bottomright = []

        for control in ["data_ctrl", "zoom_ctrl", "fullscreen_ctrl", "draw_ctrl"]:
            if self.kwargs.get(control, True):
                topleft.append(control)

        for control in ["scale_ctrl", "measure_ctrl"]:
            if self.kwargs.get(control, True):
                bottomleft.append(control)

        for control in ["toolbar_ctrl"]:
            if self.kwargs.get(control, True):
                topright.append(control)

        for control in ["attribution_control"]:
            if self.kwargs.get(control, True):
                bottomright.append(control)

        return {
            "topleft": topleft,
            "bottomleft": bottomleft,
            "topright": topright,
            "bottomright": bottomright,
        }

    @property
    def ee_layer_names(self) -> List[str]:
        """Gets the names of the EE layers.

        Returns:
            List[str]: The names of the EE layers.
        """
        warnings.warn(
            "ee_layer_names is deprecated. Use ee_layers.keys() instead.",
            DeprecationWarning,
        )
        return list(self.ee_layers.keys())

    @property
    def ee_layer_dict(self) -> Dict[str, Any]:
        """Gets the dictionary of EE layers.

        Returns:
            Dict[str, Any]: The dictionary of EE layers.
        """
        warnings.warn(
            "ee_layer_dict is deprecated. Use ee_layers instead.", DeprecationWarning
        )
        return self.ee_layers

    @property
    def ee_raster_layer_names(self) -> List[str]:
        """Gets the names of the EE raster layers.

        Returns:
            List[str]: The names of the EE raster layers.
        """
        warnings.warn(
            "ee_raster_layer_names is deprecated. Use self.ee_raster_layers.keys() instead.",
            DeprecationWarning,
        )
        return list(self.ee_raster_layers.keys())

    @property
    def ee_vector_layer_names(self) -> List[str]:
        """Gets the names of the EE vector layers.

        Returns:
            List[str]: The names of the EE vector layers.
        """
        warnings.warn(
            "ee_vector_layer_names is deprecated. Use self.ee_vector_layers.keys() instead.",
            DeprecationWarning,
        )
        return list(self.ee_vector_layers.keys())

    @property
    def ee_raster_layers(self) -> Dict[str, Any]:
        """Gets the dictionary of EE raster layers.

        Returns:
            Dict[str, Any]: The dictionary of EE raster layers.
        """
        return dict(filter(self._raster_filter, self.ee_layers.items()))

    @property
    def ee_vector_layers(self) -> Dict[str, Any]:
        """Gets the dictionary of EE vector layers.

        Returns:
            Dict[str, Any]: The dictionary of EE vector layers.
        """
        return dict(filter(self._vector_filter, self.ee_layers.items()))

    def _raster_filter(self, pair: Tuple[str, Dict[str, Any]]) -> bool:
        """Filters the raster layers.

        Args:
            pair (Tuple[str, Dict[str, Any]]): The layer pair to filter.

        Returns:
            bool: True if the layer is a raster layer, False otherwise.
        """
        return isinstance(pair[1]["ee_object"], (ee.Image, ee.ImageCollection))

    def _vector_filter(self, pair: Tuple[str, Dict[str, Any]]) -> bool:
        """Filters the vector layers.

        Args:
            pair (Tuple[str, Dict[str, Any]]): The layer pair to filter.

        Returns:
            bool: True if the layer is a vector layer, False otherwise.
        """
        return isinstance(
            pair[1]["ee_object"], (ee.Geometry, ee.Feature, ee.FeatureCollection)
        )

    def add(
        self, obj: Union[str, Any], position: str = "topright", **kwargs: Any
    ) -> None:
        """Adds a layer or control to the map.

        Args:
            obj (Union[str, Any]): The layer or control to add to the map.
            position (str, optional): The position of the control on the map. Defaults to "topright".
            **kwargs: Additional keyword arguments.
        """
        if isinstance(obj, str):
            basemap = check_basemap(obj)
            if basemap in basemaps.keys():
                super().add(get_basemap(basemap))
                return

        if not isinstance(obj, str):
            super().add(obj, position=position, **kwargs)
            return

        obj = obj.lower()

        backward_compatibilities = {
            "zoom_ctrl": "zoom_control",
            "fullscreen_ctrl": "fullscreen_control",
            "scale_ctrl": "scale_control",
            "toolbar_ctrl": "toolbar",
            "draw_ctrl": "draw_control",
        }
        obj = backward_compatibilities.get(obj, obj)

        if obj == "data_ctrl":
            data_widget = toolbar.SearchDataGUI(self)
            data_control = ipyleaflet.WidgetControl(
                widget=data_widget, position=position
            )
            self.add(data_control)
        elif obj == "search_ctrl":
            self.add_search_control(position=position)
        elif obj == "measure_ctrl":
            measure = ipyleaflet.MeasureControl(
                position=position,
                active_color="orange",
                primary_length_unit="kilometers",
            )
            self.add(measure, position=position)
        elif obj == "layer_ctrl":
            layer_control = ipyleaflet.LayersControl(position=position)
            self.add(layer_control, position=position)
        else:
            super().add(obj, position=position, **kwargs)

    def add_controls(
        self, controls: Union[List[Any], Any], position: str = "topleft"
    ) -> None:
        """Adds a list of controls to the map.

        Args:
            controls (Union[List[Any], Any]): A list of controls or a single
                control to add to the map.
            position (str, optional): The position of the controls on the map.
                Defaults to "topleft".
        """
        if not isinstance(controls, list):
            controls = [controls]
        for control in controls:
            self.add(control, position)

    def set_options(self, mapTypeId: str = "HYBRID", **kwargs: Any) -> None:
        """Adds Google basemap and controls to the ipyleaflet map.

        Args:
            mapTypeId (str, optional): A mapTypeId to set the basemap to. Can be
                one of "ROADMAP", "SATELLITE", "HYBRID" or "TERRAIN" to select
                one of the standard Google Maps API map types. Defaults to 'HYBRID'.
            **kwargs: Additional keyword arguments.
        """

        try:
            self.add(mapTypeId)
        except Exception:
            raise ValueError(
                'Google basemaps can only be one of "ROADMAP", "SATELLITE", "HYBRID" or "TERRAIN".'
            )

    setOptions = set_options

    def add_ee_layer(
        self,
        ee_object: Union[
            ee.FeatureCollection, ee.Feature, ee.Image, ee.ImageCollection
        ],
        vis_params: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        shown: bool = True,
        opacity: float = 1.0,
    ) -> None:
        """Adds a given EE object to the map as a layer.

        Args:
            ee_object (Union[ee.FeatureCollection, ee.Feature, ee.Image, ee.ImageCollection]):
                The object to add to the map.
            vis_params (Optional[Dict[str, Any]], optional): The visualization parameters.
                Defaults to {}.
            name (Optional[str], optional): The name of the layer. Defaults to 'Layer N'.
            shown (bool, optional): A flag indicating whether the layer should be on by
                default. Defaults to True.
            opacity (float, optional): The layer's opacity represented as a number
                between 0 and 1. Defaults to 1.
        """
        has_plot_dropdown = (
            hasattr(self, "_plot_dropdown_widget")
            and self._plot_dropdown_widget is not None
        )

        ee_layer = self.ee_layers.get(name, {})
        layer = ee_layer.get("ee_layer", None)
        if layer is not None:
            if isinstance(ee_layer["ee_object"], (ee.Image, ee.ImageCollection)):
                if has_plot_dropdown:
                    self._plot_dropdown_widget.options = list(
                        self.ee_raster_layers.keys()
                    )

        super().add_layer(ee_object, vis_params, name, shown, opacity)

        if isinstance(ee_object, (ee.Image, ee.ImageCollection)):
            if has_plot_dropdown:
                self._plot_dropdown_widget.options = list(self.ee_raster_layers.keys())

        tile_layer = self.ee_layers.get(name, {}).get("ee_layer", None)
        if tile_layer:
            arc_add_layer(tile_layer.url_format, name, shown, opacity)

    addLayer = add_ee_layer

    def remove_ee_layer(self, name: str) -> None:
        """Removes an Earth Engine layer.

        Args:
            name (str): The name of the Earth Engine layer to remove.
        """
        if name in self.ee_layers:
            ee_layer = self.ee_layers[name]["ee_layer"]
            self.ee_layers.pop(name, None)
            if ee_layer in self.layers:
                self.remove_layer(ee_layer)

    def set_center(self, lon: float, lat: float, zoom: Optional[int] = None) -> None:
        """Centers the map view at a given coordinates with the given zoom level.

        Args:
            lon (float): The longitude of the center, in degrees.
            lat (float): The latitude of the center, in degrees.
            zoom (Optional[int], optional): The zoom level, from 1 to 24. Defaults to None.
        """
        super().set_center(lon, lat, zoom)
        if is_arcpy():
            arc_zoom_to_extent(lon, lat, lon, lat)

    setCenter = set_center

    def center_object(
        self, ee_object: Union[ee.Element, ee.Geometry], zoom: Optional[int] = None
    ) -> None:
        """Centers the map view on a given object.

        Args:
            ee_object (Union[ee.Element, ee.Geometry]): An Earth Engine object to
                center on a geometry, image or feature.
            zoom (Optional[int], optional): The zoom level, from 1 to 24. Defaults to None.
        """
        super().center_object(ee_object, zoom)
        if is_arcpy():
            bds = self.bounds
            arc_zoom_to_extent(bds[0][1], bds[0][0], bds[1][1], bds[1][0])

    centerObject = center_object

    def zoom_to_bounds(
        self, bounds: Union[List[float], Tuple[float, float, float, float]]
    ) -> None:
        """Zooms to a bounding box in the form of [minx, miny, maxx, maxy].

        Args:
            bounds (Union[List[float], Tuple[float, float, float, float]]): A
                list/tuple containing minx, miny, maxx, maxy values for the bounds.
        """
        #  The ipyleaflet fit_bounds method takes lat/lon bounds in the form [[south, west], [north, east]].
        self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    def get_scale(self) -> float:
        """Returns the approximate pixel scale of the current map view, in meters.

        Returns:
            float: Map resolution in meters.
        """
        return super().get_scale()

    getScale = get_scale

    def add_basemap(
        self,
        basemap: Optional[str] = "ROADMAP",
        show: Optional[bool] = True,
        **kwargs: Any,
    ) -> None:
        """Adds a basemap to the map.

        Args:
            basemap (Optional[str], optional): Can be one of the strings from basemaps.
                Defaults to 'ROADMAP'.
            show (Optional[bool], optional): Whether the basemap is visible or not.
                Defaults to True.
            **kwargs: Additional keyword arguments for the TileLayer.
        """
        import xyzservices

        try:
            layer_names = self.get_layer_names()

            if isinstance(basemap, str):
                for map_name, tile_provider in self._available_basemaps.items():
                    if basemap.upper() == map_name.upper():
                        basemap = tile_provider
                        break

            if isinstance(basemap, xyzservices.TileProvider):
                name = basemap.name
                url = basemap.build_url()
                attribution = basemap.attribution
                if "max_zoom" in basemap.keys():
                    max_zoom = basemap["max_zoom"]
                else:
                    max_zoom = 30
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
            elif basemap.startswith("http"):
                self.add_tile_layer(url=basemap, shown=show, **kwargs)
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

    def get_layer_names(self) -> List[str]:
        """Gets layer names as a list.

        Returns:
            List[str]: A list of layer names.
        """
        layer_names = []

        for layer in list(self.layers):
            if len(layer.name) > 0:
                layer_names.append(layer.name)

        return layer_names

    def find_layer(self, name: str) -> Optional[ipyleaflet.Layer]:
        """Finds a layer by name.

        Args:
            name (str): Name of the layer to find.

        Returns:
            Optional[ipyleaflet.Layer]: The ipyleaflet layer object if found, else None.
        """
        layers = self.layers

        for layer in layers:
            if layer.name == name:
                return layer

        return None

    def show_layer(self, name: str, show: bool = True) -> None:
        """Shows or hides a layer on the map.

        Args:
            name (str): Name of the layer to show/hide.
            show (bool, optional): Whether to show or hide the layer. Defaults to True.
        """
        layer = self.find_layer(name)

        if layer is not None:
            layer.visible = show

    def find_layer_index(self, name: str) -> int:
        """Finds the index of a layer by name.

        Args:
            name (str): Name of the layer to find.

        Returns:
            int: Index of the layer with the specified name, or -1 if not found.
        """
        layers = self.layers

        for index, layer in enumerate(layers):
            if layer.name == name:
                return index

        return -1

    def layer_opacity(self, name: str, opacity: float = 1.0) -> None:
        """Changes the opacity of a layer.

        Args:
            name (str): The name of the layer to change opacity.
            opacity (float, optional): The opacity value to set. Defaults to 1.0.
        """
        layer = self.find_layer(name)
        try:
            layer.opacity = opacity
        except Exception as e:
            raise Exception(e)

    def add_tile_layer(
        self,
        url: str = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        name: str = "Untitled",
        attribution: str = "",
        opacity: float = 1.0,
        shown: bool = True,
        **kwargs: Any,
    ) -> None:
        """Adds a TileLayer to the map.

        Args:
            url (str, optional): The URL of the tile layer. Defaults to
                'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'.
            name (str, optional): The layer name to use for the layer. Defaults to 'Untitled'.
            attribution (str, optional): The attribution to use. Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.0.
            shown (bool, optional): A flag indicating whether the layer should
                be on by default. Defaults to True.
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

    def set_plot_options(
        self,
        add_marker_cluster: bool = False,
        sample_scale: Optional[float] = None,
        plot_type: Optional[str] = None,
        overlay: bool = False,
        position: str = "bottomright",
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_height: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """Sets plotting options.

        Args:
            add_marker_cluster (bool, optional): Whether to add a marker cluster.
                Defaults to False.
            sample_scale (float, optional):  A nominal scale in meters of the
                projection to sample in . Defaults to None.
            plot_type (str, optional): The plot type can be one of "None", "bar",
                "scatter" or "hist". Defaults to None.
            overlay (bool, optional): Whether to overlay plotted lines on the figure.
                Defaults to False.
            position (str, optional): Position of the control, can be ‘bottomleft’,
                ‘bottomright’, ‘topleft’, or ‘topright’. Defaults to 'bottomright'.
            min_width (int, optional): Min width of the widget (in pixels),
                if None it will respect the content size. Defaults to None.
            max_width (int, optional): Max width of the widget (in pixels),
                if None it will respect the content size. Defaults to None.
            min_height (int, optional): Min height of the widget (in pixels),
                if None it will respect the content size. Defaults to None.
            max_height (int, optional): Max height of the widget (in pixels),
                if None it will respect the content size. Defaults to None.

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

        for key in kwargs:
            plot_options_dict[key] = kwargs[key]

        self._plot_options = plot_options_dict

        if not hasattr(self, "_plot_marker_cluster"):
            self._plot_marker_cluster = ipyleaflet.MarkerCluster(name="Marker Cluster")

        if add_marker_cluster and (self._plot_marker_cluster not in self.layers):
            self.add(self._plot_marker_cluster)

    def plot(
        self,
        x: Union[List[float], Any],
        y: Union[List[float], Any],
        plot_type: Optional[str] = None,
        overlay: bool = False,
        position: str = "bottomright",
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_height: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
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
        if hasattr(self, "_plot_widget") and self._plot_widget is not None:
            plot_widget = self._plot_widget
        else:
            plot_widget = widgets.Output(
                layout={"border": "1px solid black", "max_width": "500px"}
            )
            plot_control = ipyleaflet.WidgetControl(
                widget=plot_widget,
                position=position,
                min_width=min_width,
                max_width=max_width,
                min_height=min_height,
                max_height=max_height,
            )
            self._plot_widget = plot_widget
            self._plot_control = plot_control
            self.add(plot_control)

        if max_width is None:
            max_width = 500
        if max_height is None:
            max_height = 300

        if (plot_type is None) and ("markers" not in kwargs):
            kwargs["markers"] = "circle"

        with plot_widget:
            try:
                fig = plt.figure(1, **kwargs)
                if max_width is not None:
                    fig.layout.width = str(max_width) + "px"
                if max_height is not None:
                    fig.layout.height = str(max_height) + "px"

                plot_widget.outputs = ()
                if not overlay:
                    plt.clear()

                if plot_type is None:
                    if "marker" not in kwargs:
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

    def add_layer_control(self, position: str = "topright") -> None:
        """Adds a layer control to the map.

        Args:
            position (str, optional): The position of the layer control on the map.
                Defaults to "topright".
        """
        if self.layer_control is None:
            layer_control = ipyleaflet.LayersControl(position=position)
            self.add(layer_control)

    addLayerControl = add_layer_control

    def add_legend(
        self,
        title: str = "Legend",
        legend_dict: Optional[Dict[str, str]] = None,
        keys: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        position: str = "bottomright",
        builtin_legend: Optional[str] = None,
        layer_name: Optional[str] = None,
        add_header: bool = True,
        widget_args: Dict[str, Any] = {},
        **kwargs: Any,
    ) -> None:
        """Adds a customized basemap to the map.

        Args:
            title (str, optional): Title of the legend. Defaults to 'Legend'.
            legend_dict (dict, optional): A dictionary containing legend items
                as keys and color as values. If provided, keys and
                colors will be ignored. Defaults to None.
            keys (list, optional): A list of legend keys. Defaults to None.
            colors (list, optional): A list of legend colors. Defaults to None.
            position (str, optional): Position of the legend. Defaults to
                'bottomright'.
            builtin_legend (str, optional): Name of the builtin legend to add
                to the map. Defaults to None.
            layer_name (str, optional): The associated layer for the legend.
                Defaults to None.
            add_header (bool, optional): Whether the legend can be closed or
                not. Defaults to True.
            widget_args (dict, optional): Additional arguments passed to the
                widget_template() function. Defaults to {}.
        """
        try:
            legend = self._add_legend(
                title,
                legend_dict,
                keys,
                colors,
                position,
                builtin_legend,
                layer_name,
                add_header,
                widget_args,
                **kwargs,
            )
            self._legend = legend
            if not hasattr(self, "legends"):
                self.legends = [legend]
            else:
                self.legends.append(legend)
        except Exception as e:
            raise Exception(e)

    def add_colorbar(
        self,
        vis_params: Optional[Dict[str, Any]] = None,
        cmap: str = "gray",
        discrete: bool = False,
        label: Optional[str] = None,
        orientation: str = "horizontal",
        position: str = "bottomright",
        transparent_bg: bool = False,
        layer_name: Optional[str] = None,
        font_size: int = 9,
        axis_off: bool = False,
        max_width: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
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
            max_width (str, optional): Maximum width of the colorbar in pixels. Defaults to None.

        Raises:
            TypeError: If the vis_params is not a dictionary.
            ValueError: If the orientation is not either horizontal or vertical.
            TypeError: If the provided min value is not scalar type.
            TypeError: If the provided max value is not scalar type.
            TypeError: If the provided opacity value is not scalar type.
            TypeError: If cmap or palette is not provided.
        """

        colorbar = self._add_colorbar(
            vis_params,
            cmap,
            discrete,
            label,
            orientation,
            position,
            transparent_bg,
            layer_name,
            font_size,
            axis_off,
            max_width,
            **kwargs,
        )
        self._colorbar = colorbar
        if not hasattr(self, "colorbars"):
            self.colorbars = [colorbar]
        else:
            self.colorbars.append(colorbar)

    def remove_colorbar(self) -> None:
        """Removes the colorbar from the map."""
        if hasattr(self, "_colorbar") and self._colorbar is not None:
            self.remove_control(self._colorbar)

    def remove_colorbars(self) -> None:
        """Removes all colorbars from the map."""
        for layer in self.ee_layers.values():
            if widget := layer.pop("colorbar", None):
                self.remove(widget)
        if hasattr(self, "colorbars"):
            for colorbar in self.colorbars:
                if colorbar in self.controls:
                    self.remove_control(colorbar)

    def remove_legend(self) -> None:
        """Removes the legend from the map."""
        if hasattr(self, "_legend") and self._legend is not None:
            if self._legend in self.controls:
                self.remove_control(self._legend)

    def remove_legends(self) -> None:
        """Removes all legends from the map."""
        for layer in self.ee_layers.values():
            if widget := layer.pop("legend", None):
                self.remove(widget)
        if hasattr(self, "legends"):
            for legend in self.legends:
                if legend in self.controls:
                    self.remove_control(legend)

    def create_vis_widget(self, layer_dict: Dict[str, Any]) -> None:
        """Creates a GUI for changing layer visualization parameters interactively.

        Args:
            layer_dict (Dict[str, Any]): A dictionary containing information about
                the layer. It is an element from Map.ee_layers.
        """
        self._add_layer_editor(position="topright", layer_dict=layer_dict)

    def add_inspector(
        self,
        names: Optional[Union[str, List[str]]] = None,
        visible: bool = True,
        decimals: int = 2,
        position: str = "topright",
        opened: bool = True,
        show_close_button: bool = True,
    ) -> None:
        """Add the Inspector GUI to the map.

        Args:
            names (str | list, optional): The names of the layers to be included. Defaults to None.
            visible (bool, optional): Whether to inspect visible layers only. Defaults to True.
            decimals (int, optional): The number of decimal places to round the coordinates. Defaults to 2.
            position (str, optional): The position of the Inspector GUI. Defaults to "topright".
            opened (bool, optional): Whether the control is opened. Defaults to True.
        """
        super()._add_inspector(
            position,
            names=names,
            visible=visible,
            decimals=decimals,
            opened=opened,
            show_close_button=show_close_button,
        )

    def add_layer_manager(
        self,
        position: str = "topright",
        opened: bool = True,
        show_close_button: bool = True,
    ) -> None:
        """Add the Layer Manager to the map.

        Args:
            position (str, optional): The position of the Layer Manager. Defaults to "topright".
            opened (bool, optional): Whether the control is opened. Defaults to True.
            show_close_button (bool, optional): Whether to show the close button. Defaults to True.
        """
        super()._add_layer_manager(position)
        if layer_manager := self._layer_manager:
            layer_manager.collapsed = not opened
            layer_manager.close_button_hidden = not show_close_button

    def _on_basemap_changed(self, basemap_name: str) -> None:
        """Handles the event when the basemap is changed.

        Args:
            basemap_name (str): The name of the new basemap.
        """
        if basemap_name not in self.get_layer_names():
            self.add_basemap(basemap_name)
            if basemap_name in self._xyz_dict:
                if "bounds" in self._xyz_dict[basemap_name]:
                    bounds = self._xyz_dict[basemap_name]["bounds"]
                    bounds = [bounds[0][1], bounds[0][0], bounds[1][1], bounds[1][0]]
                    self.zoom_to_bounds(bounds)

    def add_basemap_widget(self, position: str = "topright") -> None:
        """Add the Basemap GUI to the map.

        Args:
            position (str, optional): The position of the Basemap GUI. Defaults to "topright".
        """
        super()._add_basemap_selector(position=position)

    def add_draw_control(self, position: str = "topleft") -> None:
        """Add a draw control to the map.

        Args:
            position (str, optional): The position of the draw control. Defaults to "topleft".
        """
        super().add("draw_control", position=position)

    def add_draw_control_lite(self, position: str = "topleft") -> None:
        """Add a lite version draw control to the map for the plotting tool.

        Args:
            position (str, optional): The position of the draw control. Defaults to "topleft".
        """
        super().add(
            "draw_control",
            position=position,
            marker={},
            rectangle={"shapeOptions": {"color": "#3388ff"}},
            circle={"shapeOptions": {"color": "#3388ff"}},
            circlemarker={},
            polyline={},
            polygon={},
            edit=False,
            remove=False,
        )

    def add_toolbar(self, position: str = "topright", **kwargs: Any) -> None:
        """Add a toolbar to the map.

        Args:
            position (str, optional): The position of the toolbar. Defaults to "topright".
            **kwargs: Additional keyword arguments.
        """
        self.add("toolbar", position, **kwargs)

    def _toolbar_main_tools(self) -> Any:
        """Gets the main tools for the toolbar.

        Returns:
            Any: The main tools for the toolbar.
        """
        return toolbar.main_tools

    def _toolbar_extra_tools(self) -> Any:
        """Gets the extra tools for the toolbar.

        Returns:
            Any: The extra tools for the toolbar.
        """
        return toolbar.extra_tools

    def add_plot_gui(self, position: str = "topright", **kwargs: Any) -> None:
        """Adds the plot widget to the map.

        Args:
            position (str, optional): Position of the widget. Defaults to "topright".
            **kwargs: Additional keyword arguments.
        """
        from .toolbar import ee_plot_gui

        ee_plot_gui(self, position, **kwargs)

    def add_gui(
        self,
        name: str,
        position: str = "topright",
        opened: bool = True,
        show_close_button: bool = True,
        **kwargs: Any,
    ) -> None:
        """Add a GUI to the map.

        Args:
            name (str): The name of the GUI. Options include "layer_manager",
                "inspector", "plot", and "timelapse".
            position (str, optional): The position of the GUI. Defaults to "topright".
            opened (bool, optional): Whether the GUI is opened. Defaults to True.
            show_close_button (bool, optional): Whether to show the close button.
                Defaults to True.
            **kwargs: Additional keyword arguments.
        """
        name = name.lower()
        if name == "layer_manager":
            self.add_layer_manager(position, opened, show_close_button, **kwargs)
        elif name == "inspector":
            self.add_inspector(
                position=position,
                opened=opened,
                show_close_button=show_close_button,
                **kwargs,
            )
        elif name == "plot":
            self.add_plot_gui(position, **kwargs)
        elif name == "timelapse":
            from .toolbar import timelapse_gui

            timelapse_gui(self, **kwargs)

    # ******************************************************************************#
    # The classes and functions above are the core features of the geemap package.  #
    # The Earth Engine team and the geemap community will maintain these features.  #
    # ******************************************************************************#

    # ******************************************************************************#
    # The classes and functions below are the extra features of the geemap package. #
    # The geemap community will maintain these features.                            #
    # ******************************************************************************#

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

    def zoom_to_gdf(self, gdf):
        """Zooms to the bounding box of a GeoPandas GeoDataFrame.

        Args:
            gdf (GeoDataFrame): A GeoPandas GeoDataFrame.
        """
        bounds = gdf.total_bounds
        self.zoom_to_bounds(bounds)

    def get_bounds(self, asGeoJSON=False):
        """Returns the bounds of the current map view, as a list in the format [west, south, east, north] in degrees.

        Args:
            asGeoJSON (bool, optional): If true, returns map bounds as GeoJSON. Defaults to False.

        Returns:
            list | dict: A list in the format [west, south, east, north] in degrees.
        """
        return super().get_bounds(as_geo_json=asGeoJSON)

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

        if hasattr(self, "random_marker") and self.random_marker is not None:
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
        if hasattr(self, "_plot_control") and self._plot_control is not None:
            del self._plot_widget
            if self._plot_control in self.controls:
                self.remove_control(self._plot_control)

        if hasattr(self, "random_marker") and self.random_marker is not None:
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
        self._plot_widget = plot_widget
        self._plot_control = plot_control
        self.add(plot_control)

        self.default_style = {"cursor": "crosshair"}
        msg = "The plot function can only be used on ee.Image or ee.ImageCollection with more than one band."
        if (ee_object is None) and len(self.ee_raster_layers) > 0:
            ee_object = self.ee_raster_layers.values()[-1]["ee_object"]
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
                    if self._plot_widget is not None:
                        with self._plot_widget:
                            self._plot_widget.outputs = ()
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

    def split_map(
        self,
        left_layer="OpenTopoMap",
        right_layer="Esri.WorldTopoMap",
        zoom_control=True,
        fullscreen_control=True,
        layer_control=True,
        add_close_button=False,
        close_button_position="topright",
        left_label=None,
        right_label=None,
        left_position="bottomleft",
        right_position="bottomright",
        widget_layout=None,
        **kwargs,
    ):
        """Adds split map.

        Args:
            left_layer (str, optional): The layer tile layer. Defaults to 'OpenTopoMap'.
            right_layer (str, optional): The right tile layer. Defaults to 'Esri.WorldTopoMap'.
            zoom_control (bool, optional): Whether to show the zoom control. Defaults to True.
            fullscreen_control (bool, optional): Whether to show the full screen control. Defaults to True.
            layer_control (bool, optional): Whether to show the layer control. Defaults to True.
            add_close_button (bool, optional): Whether to add a close button. Defaults to False.
            close_button_position (str, optional): The position of the close button. Defaults to 'topright'.
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
            # self.dragging = False

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
                if left_label is not None:
                    self.remove_control(left_control)

                if right_label is not None:
                    self.remove_control(right_control)

                if change["new"]:
                    self.controls = controls
                    self.layers = layers[:-1]
                    self.add(layers[-1])

                # self.dragging = True

            close_button.observe(close_btn_click, "value")
            close_control = ipyleaflet.WidgetControl(
                widget=close_button, position=close_button_position
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
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
            attribution="Esri",
            name="Esri.WorldStreetMap",
        )
        right_layer = ipyleaflet.TileLayer(
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
            attribution="Esri",
            name="Esri.WorldStreetMap",
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

                    left_image = EELeafletTileLayer(
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

                    right_image = EELeafletTileLayer(
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
            # self.dragging = False

            if add_close_button:
                self.add(close_control)

        except Exception as e:
            raise Exception(e)

    def basemap_demo(self):
        """A demo for using geemap basemaps."""
        self.add_basemap_widget()

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

        if "width" in kwargs:
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
            output.outputs = ()
            display(colormap)

        self._colorbar = colormap_ctrl
        self.add(colormap_ctrl)

        if not hasattr(self, "colorbars"):
            self.colorbars = [colormap_ctrl]
        else:
            self.colorbars.append(colormap_ctrl)

        if layer_name in self.ee_layers:
            self.ee_layers[layer_name]["colorbar"] = colormap_ctrl

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
            nd_threshold (float, optional): The threshold for extracting pixels from the normalized difference band.
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
        if hasattr(self, "_toolbar"):
            self._toolbar.reset()

    def add_raster(
        self,
        source,
        indexes=None,
        colormap=None,
        vmin=None,
        vmax=None,
        nodata=None,
        attribution=None,
        layer_name="Raster",
        zoom_to_layer=True,
        visible=True,
        array_args={},
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
            vmin (float, optional): The minimum value to use when colormapping the palette when plotting a single band. Defaults to None.
            vmax (float, optional): The maximum value to use when colormapping the palette when plotting a single band. Defaults to None.
            nodata (float, optional): The value from the band to use to interpret as not valid data. Defaults to None.
            attribution (str, optional): Attribution for the source raster. This defaults to a message about it being a local file.. Defaults to None.
            layer_name (str, optional): The layer name to use. Defaults to 'Raster'.
            zoom_to_layer (bool, optional): Whether to zoom to the extent of the layer. Defaults to True.
            visible (bool, optional): Whether the layer is visible. Defaults to True.
            array_args (dict, optional): Additional arguments to pass to `array_to_memory_file` when reading the raster. Defaults to {}.
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
            layer_name=layer_name,
            return_client=True,
            **kwargs,
        )
        tile_layer.visible = visible

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
        params = {
            "tile_layer": tile_layer,
            "tile_client": tile_client,
            "indexes": indexes,
            "band_names": tile_client.band_names,
            "bounds": bounds,
            "type": "LOCAL",
        }
        self.cog_layer_dict[layer_name] = params

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

    def remove_draw_control(self):
        """Removes the draw control from the map"""
        self.remove("draw_control")

    def remove_drawn_features(self):
        """Removes user-drawn geometries from the map"""
        if self._draw_control is not None:
            self._draw_control.reset()
        if "Drawn Features" in self.ee_layers:
            self.ee_layers.pop("Drawn Features")

    def remove_last_drawn(self):
        """Removes last user-drawn geometry from the map"""
        if self._draw_control is not None:
            if self._draw_control.count == 1:
                self.remove_drawn_features()
            elif self._draw_control.count:
                self._draw_control.remove_geometry(self._draw_control.geometries[-1])
                if hasattr(self, "_chart_values"):
                    self._chart_values = self._chart_values[:-1]
                if hasattr(self, "_chart_points"):
                    self._chart_points = self._chart_points[:-1]
                # self._chart_labels = None

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

        count = len(self._chart_points)
        out_list = []
        if count > 0:
            header = ["id", "latitude", "longitude"] + self._chart_labels
            out_list.append(header)

            for i in range(0, count):
                id = i + 1
                line = [id] + self._chart_points[i] + self._chart_values[i]
                out_list.append(line)

            with open(out_csv, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(out_list)

            if ext == "csv":
                print(f"The csv file has been saved to: {out_csv}")
            else:
                csv_to_shp(out_csv, out_shp)
                print(f"The shapefile has been saved to: {out_shp}")

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
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            opacity (float, optional): The opacity of the layer. Defaults to 1.0.
        """
        if isinstance(palette, str):
            from .colormaps import get_palette

            count = ee_object.size().getInfo()
            palette = get_palette(palette, count)

        styled_vector = vector_styling(ee_object, column, palette, **kwargs)
        self.addLayer(
            styled_vector.style(**{"styleProperty": "style"}),
            {},
            layer_name,
            shown,
            opacity,
        )

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
            if layer_name not in self.ee_layers:
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

        if layer_name not in self.ee_layers:
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
            if layer_name not in self.ee_layers:
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
                title=color_column.title(), colors=marker_colors, keys=items
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

    def add_widget(
        self,
        content,
        position="bottomright",
        add_header=False,
        opened=True,
        show_close_button=True,
        widget_icon="gear",
        close_button_icon="times",
        widget_args={},
        close_button_args={},
        display_widget=None,
        **kwargs,
    ):
        """Add a widget (e.g., text, HTML, figure) to the map.

        Args:
            content (str | ipywidgets.Widget | object): The widget to add.
            position (str, optional): The position of the widget. Defaults to "bottomright".
            add_header (bool, optional): Whether to add a header with close buttons to the widget. Defaults to False.
            opened (bool, optional): Whether to open the toolbar. Defaults to True.
            show_close_button (bool, optional): Whether to show the close button. Defaults to True.
            widget_icon (str, optional): The icon name for the toolbar button. Defaults to 'gear'.
            close_button_icon (str, optional): The icon name for the close button. Defaults to "times".
            widget_args (dict, optional): Additional arguments to pass to the toolbar button. Defaults to {}.
            close_button_args (dict, optional): Additional arguments to pass to the close button. Defaults to {}.
            display_widget (ipywidgets.Widget, optional): The widget to be displayed when the toolbar is clicked.
            **kwargs: Additional arguments to pass to the HTML or Output widgets
        """

        allowed_positions = ["topleft", "topright", "bottomleft", "bottomright"]

        if position not in allowed_positions:
            raise Exception(f"position must be one of {allowed_positions}")

        if "layout" not in kwargs:
            kwargs["layout"] = widgets.Layout(padding="0px 4px 0px 4px")
        try:
            if add_header:
                if isinstance(content, str):
                    widget = widgets.HTML(value=content, **kwargs)
                else:
                    widget = content

                widget_template(
                    widget,
                    opened,
                    show_close_button,
                    widget_icon,
                    close_button_icon,
                    widget_args,
                    close_button_args,
                    display_widget,
                    self,
                    position,
                )
            else:
                if isinstance(content, str):
                    widget = widgets.HTML(value=content, **kwargs)
                else:
                    widget = widgets.Output(**kwargs)
                    with widget:
                        display(content)
                control = ipyleaflet.WidgetControl(widget=widget, position=position)
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

        self.add_widget(image, position=position, **kwargs)

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

    def layer_to_image(
        self,
        layer_name: str,
        output: Optional[str] = None,
        crs: str = "EPSG:3857",
        scale: Optional[int] = None,
        region: Optional[ee.Geometry] = None,
        vis_params: Optional[Dict] = None,
        **kwargs: Any,
    ) -> None:
        """
        Converts a specific layer from Earth Engine to an image file.

        Args:
            layer_name (str): The name of the layer to convert.
            output (str): The output file path for the image. Defaults to None.
            crs (str, optional): The coordinate reference system (CRS) of the output image. Defaults to "EPSG:3857".
            scale (int, optional): The scale of the output image. Defaults to None.
            region (ee.Geometry, optional): The region of interest for the conversion. Defaults to None.
            vis_params (dict, optional): The visualization parameters. Defaults to None.
            **kwargs: Additional keyword arguments to pass to the `download_ee_image` function.

        Returns:
            None
        """

        if region is None:
            b = self.bounds
            west, south, east, north = b[0][1], b[0][0], b[1][1], b[1][0]
            region = ee.Geometry.BBox(west, south, east, north)

        if scale is None:
            scale = int(self.get_scale())

        if layer_name not in self.ee_layers.keys():
            raise ValueError(f"Layer {layer_name} does not exist.")

        if output is None:
            output = layer_name + ".tif"

        layer = self.ee_layers[layer_name]
        ee_object = layer["ee_object"]

        if vis_params is None:
            vis_params = layer["vis_params"]

        image = ee_object.visualize(**vis_params)
        if not output.endswith(".tif"):
            geotiff = output + ".tif"
        else:
            geotiff = output
        download_ee_image(image, geotiff, region, crs=crs, scale=scale, **kwargs)

        if not output.endswith(".tif"):
            geotiff_to_image(geotiff, output)
            os.remove(geotiff)


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
    return EELeafletTileLayer(ee_object, vis_params, name, shown, opacity)


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
    # m.dragging = False

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
            if basemap["type"] in ["xyz", "normal", "grau"]:
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
