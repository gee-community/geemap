"""A generic Map interface and lightweight implementation."""

from collections.abc import Callable, Sequence
import enum
import logging
import math
from typing import Any, TypedDict, Type

import ee
import ipyleaflet
import ipywidgets

from . import basemaps
from . import coreutils
from . import ee_tile_layers
from . import map_widgets
from . import toolbar

_DRAWN_FEATURES_LAYER = "Drawn Features"


class DrawActions(str, enum.Enum):
    """Action types for the draw control."""

    CREATED = "created"
    EDITED = "edited"
    DELETED = "deleted"
    REMOVED_LAST = "removed-last"


class AbstractDrawControl:
    """Abstract class for the draw control."""

    host_map = None
    layer = None
    geometries = []
    properties = []
    last_geometry = None
    last_draw_action = None
    _geometry_create_dispatcher = ipywidgets.CallbackDispatcher()
    _geometry_edit_dispatcher = ipywidgets.CallbackDispatcher()
    _geometry_delete_dispatcher = ipywidgets.CallbackDispatcher()

    def __init__(self, host_map):
        """Initialize the draw control.

        Args:
            host_map (geemap.Map): The geemap.Map instance to be linked with
                the draw control.
        """

        self.host_map = host_map
        self.layer = None
        self.geometries = []
        self.properties = []
        self.last_geometry = None
        self.last_draw_action = None
        self._geometry_create_dispatcher = ipywidgets.CallbackDispatcher()
        self._geometry_edit_dispatcher = ipywidgets.CallbackDispatcher()
        self._geometry_delete_dispatcher = ipywidgets.CallbackDispatcher()
        self._bind_to_draw_control()

    @property
    def features(self) -> list[ee.Feature]:
        """Returns a list of features created from geometries and properties."""
        if self.count:
            features = []
            for i, geometry in enumerate(self.geometries):
                if i < len(self.properties):
                    property = self.properties[i]
                else:
                    property = None
                features.append(ee.Feature(geometry, property))
            return features
        else:
            return []

    @property
    def collection(self) -> ee.FeatureCollection:
        """Returns a feature collection created from features."""
        return ee.FeatureCollection(self.features if self.count else [])

    @property
    def last_feature(self) -> ee.Feature | None:
        """Returns the last feature created."""
        property = self.get_geometry_properties(self.last_geometry)
        return ee.Feature(self.last_geometry, property) if self.last_geometry else None

    @property
    def count(self) -> int:
        """Returns the number of geometries."""
        return len(self.geometries)

    def reset(self, clear_draw_control: bool = True) -> None:
        """Resets the draw controls.

        Args:
            clear_draw_control: Whether to clear the draw control.
        """
        if self.layer is not None:
            self.host_map.remove_layer(self.layer)
        self.geometries = []
        self.properties = []
        self.last_geometry = None
        self.layer = None
        if clear_draw_control:
            self._clear_draw_control()

    def remove_geometry(self, geometry: ee.Geometry) -> None:
        """Removes a geometry from the draw control.

        Args:
            geometry: The geometry to remove.
        """
        if not geometry:
            return
        try:
            index = self.geometries.index(geometry)
        except ValueError:
            return
        if index >= 0:
            del self.geometries[index]
            del self.properties[index]
            self._remove_geometry_at_index_on_draw_control(index)
            if index == self.count and geometry == self.last_geometry:
                # Treat this like an "undo" of the last drawn geometry.
                if len(self.geometries):
                    self.last_geometry = self.geometries[-1]
                else:
                    self.last_geometry = geometry
                self.last_draw_action = DrawActions.REMOVED_LAST
            if self.layer is not None:
                self._redraw_layer()

    def get_geometry_properties(self, geometry: ee.Geometry) -> dict | None:
        """Gets the properties of a geometry.

        Args:
            geometry: The geometry to get properties for.

        Returns:
            The properties of the geometry.
        """
        if not geometry:
            return None
        try:
            index = self.geometries.index(geometry)
        except ValueError:
            return None
        if index >= 0:
            return self.properties[index]
        else:
            return None

    def set_geometry_properties(self, geometry: ee.Geometry, property: dict) -> None:
        """Sets the properties of a geometry.

        Args:
            geometry: The geometry to set properties for.
            property: The properties to set.
        """
        if not geometry:
            return
        try:
            index = self.geometries.index(geometry)
        except ValueError:
            return
        if index >= 0:
            self.properties[index] = property

    def on_geometry_create(self, callback: Callable, remove: bool = False) -> None:
        """Registers a callback for geometry creation.

        Args:
            callback: The callback function.
            remove: Whether to remove the callback.
        """
        self._geometry_create_dispatcher.register_callback(callback, remove=remove)

    def on_geometry_edit(self, callback: Callable, remove: bool = False) -> None:
        """Registers a callback for geometry editing.

        Args:
            callback: The callback function.
            remove: Whether to remove the callback.
        """
        self._geometry_edit_dispatcher.register_callback(callback, remove=remove)

    def on_geometry_delete(self, callback: Callable, remove: bool = False) -> None:
        """Registers a callback for geometry deletion.

        Args:
            callback: The callback function.
            remove: Whether to remove the callback.
        """
        self._geometry_delete_dispatcher.register_callback(callback, remove=remove)

    def _bind_to_draw_control(self):
        """Set up draw control event handling like create, edit, and delete."""
        raise NotImplementedError()

    def _remove_geometry_at_index_on_draw_control(self, index: int) -> None:
        """Remove the geometry at the given index on the draw control."""
        raise NotImplementedError()

    def _clear_draw_control(self):
        """Clears the geometries from the draw control."""
        raise NotImplementedError()

    def _get_synced_geojson_from_draw_control(self):
        """Returns an up-to-date list of GeoJSON from the draw control."""
        raise NotImplementedError()

    def _sync_geometries(self) -> None:
        """Sync the local geometries with those from the draw control."""
        if not self.count:
            return
        # The current geometries from the draw_control.
        test_geojsons = self._get_synced_geojson_from_draw_control()
        self.geometries = [
            coreutils.geojson_to_ee(geo_json, geodesic=False)
            for geo_json in test_geojsons
        ]

    def _redraw_layer(self) -> None:
        """Redraws the layer on the map."""
        if not self.host_map:
            return
        # If the layer already exists, substitute it. This can avoid flickering.
        if _DRAWN_FEATURES_LAYER in self.host_map.ee_layers:
            old_layer = self.host_map.ee_layers.get(_DRAWN_FEATURES_LAYER, {})[
                "ee_layer"
            ]
            new_layer = ee_tile_layers.EELeafletTileLayer(
                self.collection,
                {"color": "blue"},
                _DRAWN_FEATURES_LAYER,
                old_layer.visible,
                0.5,
            )
            self.host_map.substitute(old_layer, new_layer)
            self.layer = self.host_map.ee_layers.get(_DRAWN_FEATURES_LAYER, {}).get(
                "ee_layer", None
            )
            self.host_map.ee_layers.get(_DRAWN_FEATURES_LAYER, {})[
                "ee_layer"
            ] = new_layer
        else:  # Otherwise, add the layer.
            self.host_map.add_layer(
                self.collection,
                {"color": "blue"},
                _DRAWN_FEATURES_LAYER,
                False,
                0.5,
            )
            self.layer = self.host_map.ee_layers.get(_DRAWN_FEATURES_LAYER, {}).get(
                "ee_layer", None
            )

    def _handle_geometry_created(self, geo_json: dict) -> None:
        """Handles the creation of a geometry.

        Args:
            geo_json: The GeoJSON representation of the geometry.
        """
        geometry = coreutils.geojson_to_ee(geo_json, geodesic=False)
        self.last_geometry = geometry
        self.last_draw_action = DrawActions.CREATED
        self.geometries.append(geometry)
        self.properties.append(None)
        self._redraw_layer()
        self._geometry_create_dispatcher(self, geometry=geometry)

    def _handle_geometry_edited(self, geo_json: dict) -> None:
        """Handles the editing of a geometry.

        Args:
            geo_json: The GeoJSON representation of the geometry.
        """
        geometry = coreutils.geojson_to_ee(geo_json, geodesic=False)
        self.last_geometry = geometry
        self.last_draw_action = DrawActions.EDITED
        self._sync_geometries()
        self._geometry_edit_dispatcher(self, geometry=geometry)

    def _handle_geometry_deleted(self, geo_json: dict) -> None:
        """Handles the deletion of a geometry.

        Args:
            geo_json: The GeoJSON representation of the geometry.
        """
        geometry = coreutils.geojson_to_ee(geo_json, geodesic=False)
        self.last_geometry = geometry
        self.last_draw_action = DrawActions.DELETED
        try:
            index = self.geometries.index(geometry)
        except ValueError:
            return
        if index >= 0:
            del self.geometries[index]
            del self.properties[index]
            if self.count:
                self._redraw_layer()
            elif _DRAWN_FEATURES_LAYER in self.host_map.ee_layers:
                # Remove drawn features layer if there are no geometries.
                self.host_map.remove_layer(_DRAWN_FEATURES_LAYER)
            self._geometry_delete_dispatcher(self, geometry=geometry)


class MapDrawControl(ipyleaflet.DrawControl, AbstractDrawControl):
    """Implements the AbstractDrawControl for ipleaflet Map."""

    def __init__(self, host_map, **kwargs: Any) -> None:
        """Initialize the map draw control.

        Args:
            host_map (geemap.Map): The geemap.Map object that the control will be added to.
            **kwargs (Any): Additional keyword arguments for the DrawControl.
        """
        super().__init__(host_map=host_map, **kwargs)

    def _get_synced_geojson_from_draw_control(self) -> list[dict[str, Any]]:
        """Returns an up-to-date list of GeoJSON from the draw control."""
        return [data.copy() for data in self.data]

    def _bind_to_draw_control(self) -> None:
        """Set up draw control event handling like create, edit, and delete."""

        # Handles draw events
        def handle_draw(_, action: str, geo_json: dict[str, Any]) -> None:
            """Handles draw events.

            Args:
                _ (Any): Unused parameter.
                action: The action performed (created, edited, deleted).
                geo_json: The GeoJSON representation of the geometry.
            """
            try:
                if action == "created":
                    self._handle_geometry_created(geo_json)
                elif action == "edited":
                    self._handle_geometry_edited(geo_json)
                elif action == "deleted":
                    self._handle_geometry_deleted(geo_json)
            except Exception as e:
                self.reset(clear_draw_control=False)
                print("There was an error creating Earth Engine Feature.")
                raise Exception(e)

        self.on_draw(handle_draw)

        def handle_data_update(_):
            """Handles data update events.

            Args:
                _ (Any): Unused parameter.
            """
            self._sync_geometries()
            # Need to refresh the layer if the last action was an edit.
            if self.last_draw_action == DrawActions.EDITED:
                self._redraw_layer()

        self.observe(handle_data_update, "data")

    def _remove_geometry_at_index_on_draw_control(self, index: int) -> None:
        """Remove the geometry at the given index on the draw control.

        Args:
            index: The index of the geometry to remove.
        """
        del self.data[index]
        self.send_state(key="data")

    def _clear_draw_control(self) -> None:
        """Clears the geometries from the draw control."""
        self.data = []  # Remove all drawn features from the map.
        return self.clear()


class MapInterface:
    """Interface for all maps."""

    class EELayerMetadata(TypedDict):
        """Metadata for layers backed by Earth Engine objects."""

        ee_object: ee.ComputedObject
        ee_layer: Any
        vis_params: dict[str, Any]

    # All layers including basemaps, GeoJSON layers, etc.
    layers: list[Any]

    # Layers backed by Earth Engine objects and keyed by layer name.
    ee_layers: dict[str, EELayerMetadata]

    # The GeoJSON layers on the map.
    geojson_layers: list[Any]

    def get_zoom(self) -> int:
        """Returns the current zoom level of the map."""
        raise NotImplementedError()

    def set_zoom(self, value: int) -> None:
        """Sets the current zoom level of the map."""
        del value  # Unused.
        raise NotImplementedError()

    def get_center(self) -> Sequence[float]:
        """Returns the current center of the map (lat, lon)."""
        raise NotImplementedError()

    def set_center(self, lon: float, lat: float, zoom: int | None = None) -> None:
        """Centers the map view at given coordinates with the given zoom level.

        Args:
            lon: Longitude of the center.
            lat: Latitude of the center.
            zoom: Zoom level to set. Defaults to None.
        """
        del lon, lat, zoom  # Unused.
        raise NotImplementedError()

    def center_object(
        self,
        ee_object: ee.ComputedObject,
        zoom: int | None = None,
        max_error: float = 0.001,
    ) -> None:
        """Centers the map view on a given object.

        Args:
            ee_object: The Earth Engine object to center on.
            zoom: Zoom level to set. Defaults to None.
            max_error: The maximum error for the geometry. Defaults to 0.001.
        """
        del ee_object, zoom, max_error  # Unused.
        raise NotImplementedError()

    def get_scale(self) -> float:
        """Returns the approximate pixel scale of the current map view in meters."""
        raise NotImplementedError()

    def get_bounds(self) -> tuple[float, float, float, float]:
        """Returns the bounds of the current map view.

        Returns:
            A tuple in the format (west, south, east, north) in degrees.
        """
        raise NotImplementedError()

    @property
    def width(self) -> str:
        """Returns the current width of the map."""
        raise NotImplementedError()

    @width.setter
    def width(self, value: str) -> None:
        """Sets the width of the map."""
        del value  # Unused.
        raise NotImplementedError()

    @property
    def height(self) -> str:
        """Returns the current height of the map."""
        raise NotImplementedError()

    @height.setter
    def height(self, value: str) -> None:
        """Sets the height of the map."""
        del value  # Unused.
        raise NotImplementedError()

    def add(self, widget: str, position: str, **kwargs: Any) -> None:
        """Adds a widget to the map.

        Args:
            widget: The widget to add.
            position: The position to place the widget.
            **kwargs: Additional keyword arguments.
        """
        del widget, position, kwargs  # Unused.
        raise NotImplementedError()

    def remove(self, widget: str) -> None:
        """Removes a widget from the map."""
        del widget  # Unused.
        raise NotImplementedError()

    def add_layer(
        self,
        ee_object: ee.ComputedObject,
        vis_params: dict[str, Any] | None = None,
        name: str | None = None,
        shown: bool = True,
        opacity: float = 1.0,
    ) -> None:
        """Adds a layer to the map.

        Args:
            ee_object: The Earth Engine object to add as a layer.
            vis_params: Visualization parameters. Defaults to None.
            name: Name of the layer. Defaults to None.
            shown: Whether the layer is shown. Defaults to True.
            opacity: Opacity of the layer. Defaults to 1.0.
        """
        del ee_object, vis_params, name, shown, opacity  # Unused.
        raise NotImplementedError()

    def remove_layer(self, layer: str) -> None:
        """Removes a layer from the map."""
        del layer  # Unused.
        raise NotImplementedError()


class Map(ipyleaflet.Map, MapInterface):
    """The Map class inherits the ipyleaflet Map class.

    Args:
        center (list, optional): Center of the map (lat, lon). Defaults to [0, 0].
        zoom (int, optional): Zoom level of the map. Defaults to 2.
        height (str, optional): Height of the map. Defaults to "600px".
        width (str, optional): Width of the map. Defaults to "100%".

    Returns:
        ipyleaflet: ipyleaflet map object.
    """

    _KWARG_DEFAULTS: dict[str, Any] = {
        "center": [0, 0],
        "zoom": 2,
        "zoom_control": False,
        "attribution_control": False,
        "ee_initialize": True,
        "scroll_wheel_zoom": True,
    }

    _BASEMAP_ALIASES: dict[str, list[str]] = {
        "DEFAULT": ["Google.Roadmap", "OpenStreetMap.Mapnik"],
        "ROADMAP": ["Google.Roadmap", "Esri.WorldStreetMap"],
        "SATELLITE": ["Google.Satellite", "Esri.WorldImagery"],
        "TERRAIN": ["Google.Terrain", "Esri.WorldTopoMap"],
        "HYBRID": ["Google.Hybrid", "Esri.WorldImagery"],
    }

    _USER_AGENT_PREFIX = "geemap-core"

    @property
    def width(self) -> str:
        """Returns the current width of the map."""
        return self.layout.width

    @width.setter
    def width(self, value: str) -> None:
        """Sets the width of the map."""
        self.layout.width = value

    @property
    def height(self) -> str:
        """Returns the current height of the map."""
        return self.layout.height

    @height.setter
    def height(self, value: str) -> None:
        """Sets the height of the map."""
        self.layout.height = value

    @property
    def _toolbar(self) -> toolbar.Toolbar | None:
        """Finds the toolbar widget in the map controls.

        Returns:
            The toolbar widget if found, else None.
        """
        return self._find_widget_of_type(toolbar.Toolbar)

    @property
    def _inspector(self) -> map_widgets.Inspector | None:
        """Finds the inspector widget in the map controls.

        Returns:
            The inspector widget if found, else None.
        """
        return self._find_widget_of_type(map_widgets.Inspector)

    @property
    def _search_bar(self) -> map_widgets.SearchBar | None:
        """Finds the search bar widget in the map controls.

        Returns:
            The search bar widget if found, else None.
        """
        return self._find_widget_of_type(map_widgets.SearchBar)

    @property
    def _draw_control(self) -> MapDrawControl | None:
        """The draw control widget in the map controls."""
        return self._find_widget_of_type(
            MapDrawControl
        )  # pytype: disable=bad-return-type

    @property
    def _layer_manager(self) -> map_widgets.LayerManager | None:
        """Finds the layer manager widget in the map controls.

        Returns:
            The layer manager widget if found, else None.
        """
        return self._find_widget_of_type(map_widgets.LayerManager)

    @property
    def _layer_editor(self) -> map_widgets.LayerEditor | None:
        """Finds the layer editor widget in the map controls.

        Returns:
            The layer editor widget if found, else None.
        """
        return self._find_widget_of_type(map_widgets.LayerEditor)

    @property
    def _basemap_selector(self) -> map_widgets.BasemapSelector | None:
        """Finds the basemap selector widget in the map controls.

        Returns:
            The basemap selector widget if found, else None.
        """
        return self._find_widget_of_type(map_widgets.BasemapSelector)

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the map with given keyword arguments.

        Args:
            **kwargs: Additional keyword arguments for the map.
        """
        self._available_basemaps = self._get_available_basemaps()

        # Use the first basemap in the list of available basemaps.
        if "basemap" not in kwargs:
            kwargs["basemap"] = next(iter(self._available_basemaps.values()))
        elif "basemap" in kwargs and isinstance(kwargs["basemap"], str):
            if kwargs["basemap"] in self._available_basemaps:
                kwargs["basemap"] = self._available_basemaps.get(kwargs["basemap"])

        if "width" in kwargs:
            self.width: str = kwargs.pop("width", "100%")
        self.height: str = kwargs.pop("height", "600px")

        self.ee_layers: dict[str, dict[str, Any]] = {}
        self.geojson_layers: list[Any] = []

        kwargs = self._apply_kwarg_defaults(kwargs)
        super().__init__(**kwargs)

        # Add a container to layout the layer manager and toolbar side-by-side.
        self.top_right_layout_box = ipywidgets.GridBox(
            layout=ipywidgets.Layout(
                grid_template_columns="auto auto",  # Two columns
                grid_gap="0px 10px",  # 0px row gap, 10px column gap
            ),
        )
        self.top_right_layout_box.layout.overflow = "visible"
        self.top_right_control = ipyleaflet.WidgetControl(
            widget=self.top_right_layout_box, position="topright", transparent_bg=True
        )
        super().add(self.top_right_control)

        for position, widgets in self._control_config().items():
            for widget in widgets:
                self.add(widget, position=position)

        # Authenticate and initialize EE.
        if kwargs.get("ee_initialize", True):
            coreutils.ee_initialize(user_agent_prefix=self._USER_AGENT_PREFIX)

        # Listen for layers being added/removed so we can update the layer manager.
        self.observe(self._on_layers_change, "layers")

    def get_zoom(self) -> int:
        """Returns the current zoom level of the map."""
        return self.zoom

    def set_zoom(self, value: int) -> None:
        """Sets the current zoom level of the map."""
        self.zoom = value

    def get_center(self) -> Sequence[float]:
        """Returns the current center of the map (lat, lon)."""
        return self.center

    def get_bounds(
        self, as_geojson: bool = False
    ) -> Sequence:  # pytype: disable=signature-mismatch
        """Returns the bounds of the current map view.

        Args:
            as_geojson: If true, returns map bounds as GeoJSON. Defaults to False.

        Returns:
            [west, south, east, north] in degrees or a GeoJSON dictionary.
        """
        bounds = self.bounds
        if not bounds:
            raise RuntimeError(
                "Map bounds are undefined. Please display the " "map then try again."
            )
        # ipyleaflet returns bounds in the format [[south, west], [north, east]].
        # https://ipyleaflet.readthedocs.io/en/latest/map_and_basemaps/map.html#ipyleaflet.Map.fit_bounds
        coords = [bounds[0][1], bounds[0][0], bounds[1][1], bounds[1][0]]

        if as_geojson:
            return ee.Geometry.BBox(*coords).getInfo()
        return coords

    def get_scale(self) -> float:
        """Returns the approximate pixel scale of the current map view in meters."""
        # Reference:
        # - https://blogs.bing.com/maps/2006/02/25/map-control-zoom-levels-gt-resolution
        # - https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Resolution_and_Scale
        center_lat = self.center[0]
        center_lat_cos = math.cos(math.radians(center_lat))
        return 156543.04 * center_lat_cos / math.pow(2, self.zoom)

    def set_center(self, lon: float, lat: float, zoom: int | None = None) -> None:
        """Centers the map view at given coordinates with the given zoom level.

        Args:
            lon: Longitude of the center.
            lat: Latitude of the center.
            zoom: Zoom level to set. Defaults to None.
        """
        self.center = (lat, lon)
        if zoom is not None:
            self.zoom = zoom

    def _get_geometry(
        self, ee_object: ee.ComputedObject, max_error: float
    ) -> ee.Geometry:
        """Returns the geometry for an arbitrary EE object.

        Args:
            ee_object: The Earth Engine object.
            max_error: The maximum error for the geometry transformation.

        Returns:
            Geometry of the Earth Engine object.
        """
        if isinstance(ee_object, ee.Geometry):
            return ee_object
        try:
            return ee_object.geometry(maxError=max_error)
        except Exception as exc:
            raise Exception(
                "ee_object must be one of ee.Geometry, ee.FeatureCollection, ee.Image, "
                "or ee.ImageCollection."
            ) from exc

    def center_object(
        self,
        ee_object: ee.ComputedObject,
        zoom: int | None = None,
        max_error: float = 0.001,
    ) -> None:
        """Centers the map view on a given object.

        Args:
            ee_object: The Earth Engine object to center on.
            zoom: Zoom level to set. Defaults to None.
            max_error: The maximum error for the geometry. Defaults to 0.001.
        """
        geometry = self._get_geometry(ee_object, max_error).transform(
            maxError=max_error
        )
        if zoom is None:
            coordinates = geometry.bounds(maxError=max_error).getInfo()["coordinates"][
                0
            ]
            x_vals = [c[0] for c in coordinates]
            y_vals = [c[1] for c in coordinates]
            self.fit_bounds([[min(y_vals), min(x_vals)], [max(y_vals), max(x_vals)]])
        else:
            if not isinstance(zoom, int):
                raise ValueError("Zoom must be an integer.")
            centroid = geometry.centroid(maxError=max_error).getInfo()["coordinates"]
            self.set_center(centroid[0], centroid[1], zoom)

    def _find_widget_of_type(
        self, widget_type: type[ipywidgets.Widget], return_control: bool = False
    ) -> ipywidgets.Widget | None:
        """Finds a widget in the controls with the passed in type.

        Args:
            widget_type: The type of the widget to find.
            return_control: Whether to return the control itself. Defaults to False.

        Returns:
            The widget if found, else None.
        """
        for widget in self.controls:
            if isinstance(widget, ipyleaflet.WidgetControl):
                if isinstance(widget.widget, widget_type):
                    return widget if return_control else widget.widget
            elif isinstance(widget, widget_type):
                return widget
        if self.top_right_layout_box:
            for child in self.top_right_layout_box.children:
                if isinstance(child, widget_type):
                    return child
        return None

    def add(
        self, obj: Any, position: str = "", **kwargs: Any
    ) -> None:  # pytype: disable=signature-mismatch
        """Adds a widget or control to the map.

        Args:
            obj: The object to add to the map.
            position: The position to place the widget. Defaults to "".
            **kwargs: Additional keyword arguments.
        """
        if not position:
            for default_position, widgets in self._control_config().items():
                if obj in widgets:
                    position = default_position
            if not position:
                position = "topright"

        # Basic controls:
        #   - can only be added to the map once,
        #   - have a constructor that takes a position arg, and
        #   - don't need to be stored as instance vars.
        basic_controls = {
            "zoom_control": (ipyleaflet.ZoomControl, {}),
            "fullscreen_control": (ipyleaflet.FullScreenControl, {}),
            "scale_control": (ipyleaflet.ScaleControl, {"metric": True}),
            "attribution_control": (ipyleaflet.AttributionControl, {}),
        }
        if obj in basic_controls:
            basic_control = basic_controls[obj]
            # Check if widget is already on the map.
            if self._find_widget_of_type(basic_control[0]):
                return
            new_kwargs = {**basic_control[1], **kwargs}
            super().add(basic_control[0](position=position, **new_kwargs))
        elif obj == "search_control":
            self._add_search_control(position, **kwargs)
        elif obj == "toolbar":
            self._add_toolbar(position, **kwargs)
        elif obj == "inspector":
            self._add_inspector(position, **kwargs)
        elif obj == "layer_manager":
            self._add_layer_manager(position, **kwargs)
        elif obj == "layer_editor":
            self._add_layer_editor(position, **kwargs)
        elif obj == "draw_control":
            self._add_draw_control(position, **kwargs)
        elif obj == "basemap_selector":
            self._add_basemap_selector(position, **kwargs)
        else:
            super().add(obj)

    def _add_layer_manager(self, position: str, **kwargs: Any) -> None:
        """Adds a layer manager to the map.

        Args:
            position: The position to place the layer manager.
            **kwargs: Additional keyword arguments.
        """
        if self._layer_manager:
            return

        layer_manager = map_widgets.LayerManager(self, **kwargs)
        layer_manager.on_close = lambda: self.remove("layer_manager")
        layer_manager.refresh_layers()
        if position == "topright" and self.top_right_layout_box:
            current_children = self.top_right_layout_box.children
            self.top_right_layout_box.children = (layer_manager,) + current_children
        else:
            super().add(
                ipyleaflet.WidgetControl(widget=layer_manager, position=position)
            )

    def _add_toolbar(self, position: str, **kwargs: Any) -> None:
        """Adds a toolbar to the map.

        Args:
            position: The position to place the toolbar.
            **kwargs: Additional keyword arguments.
        """
        if self._toolbar:
            return

        toolbar_val = toolbar.Toolbar(
            self,
            self._toolbar_main_tools(),
            self._toolbar_extra_tools(),
        )
        if position == "topright" and self.top_right_layout_box:
            current_children = self.top_right_layout_box.children
            self.top_right_layout_box.children = current_children + (toolbar_val,)
        else:
            super().add(ipyleaflet.WidgetControl(widget=toolbar_val, position=position))

    def _add_inspector(self, position: str, **kwargs: Any) -> None:
        """Adds an inspector to the map.

        Args:
            position: The position to place the inspector.
            **kwargs: Additional keyword arguments.
        """
        if self._inspector:
            return

        inspector = map_widgets.Inspector(self, **kwargs)
        inspector.on_close = lambda: self.remove("inspector")
        inspector_control = ipyleaflet.WidgetControl(
            widget=inspector, position=position, transparent_bg=True
        )
        super().add(inspector_control)

    def _add_search_control(self, position: str, **kwargs: Any) -> None:
        """Adds a search bar to the map.

        Args:
            position: The position to place the inspector.
            **kwargs: Additional keyword arguments.
        """
        if self._search_bar:
            return
        widget = map_widgets.SearchBar(self, **kwargs)
        widget.on_close = lambda: self.remove("search_control")
        control = ipyleaflet.WidgetControl(
            widget=widget, position=position, transparent_bg=True
        )
        super().add(control)

    def _add_layer_editor(self, position: str, **kwargs: Any) -> None:
        """Adds a layer editor to the map.

        Args:
            position: The position to place the layer editor.
            **kwargs: Additional keyword arguments.
        """
        if self._layer_editor:
            return

        widget = map_widgets.LayerEditor(self, **kwargs)
        widget.on_close = lambda: self.remove("layer_editor")
        control = ipyleaflet.WidgetControl(
            widget=widget, position=position, transparent_bg=True
        )
        super().add(control)

    def _add_draw_control(self, position: str = "topleft", **kwargs: Any) -> None:
        """Adds a draw control to the map.

        Args:
            position: The position of the draw control. Defaults to "topleft".
            **kwargs: Additional keyword arguments.
        """
        if self._draw_control:
            return
        default_args = dict(
            marker={"shapeOptions": {"color": "#3388ff"}},
            rectangle={"shapeOptions": {"color": "#3388ff"}},
            circlemarker={},
            edit=True,
            remove=True,
        )
        control = MapDrawControl(
            host_map=self,
            position=position,
            **{**default_args, **kwargs},
        )
        super().add(control)

    def get_draw_control(self) -> MapDrawControl | None:
        """Gets the draw control of the map.

        Returns:
            The draw control if it exists, otherwise None.
        """
        return self._draw_control

    def _add_basemap_selector(self, position: str, **kwargs: Any) -> None:
        """Adds a basemap selector to the map.

        Args:
            position: The position to place the basemap selector.
            **kwargs: Additional keyword arguments.
        """
        if self._basemap_selector:
            return

        basemap_names = kwargs.pop("basemaps", list(self._available_basemaps.keys()))

        default_value_for_selector = None
        if self.layers:
            first_layer_name = getattr(self.layers[0], "name", "")
            if first_layer_name:
                default_value_for_selector = self._get_preferred_basemap_name(
                    first_layer_name
                )
            elif self._available_basemaps:
                default_value_for_selector = self._get_preferred_basemap_name(
                    next(iter(self._available_basemaps.keys()))
                )
            else:
                default_value_for_selector = "DEFAULT"

        elif self._available_basemaps:
            first_available_key = next(iter(self._available_basemaps.keys()))
            default_value_for_selector = self._get_preferred_basemap_name(
                first_available_key
            )
        else:
            default_value_for_selector = "DEFAULT"

        value = kwargs.pop("value", default_value_for_selector)
        basemap = map_widgets.BasemapSelector(basemap_names, value, **kwargs)
        basemap.on_close = lambda: self.remove("basemap_selector")
        basemap.on_basemap_changed = self._replace_basemap
        basemap_control = ipyleaflet.WidgetControl(
            widget=basemap, position=position, transparent_bg=True
        )
        super().add(basemap_control)

    def remove(self, widget: Any) -> None:  # pytype: disable=signature-mismatch
        """Removes a widget from the map."""
        basic_controls = {
            "search_control": map_widgets.SearchBar,
            "zoom_control": ipyleaflet.ZoomControl,
            "fullscreen_control": ipyleaflet.FullScreenControl,
            "scale_control": ipyleaflet.ScaleControl,
            "attribution_control": ipyleaflet.AttributionControl,
            "toolbar": toolbar.Toolbar,
            "inspector": map_widgets.Inspector,
            "layer_manager": map_widgets.LayerManager,
            "layer_editor": map_widgets.LayerEditor,
            "draw_control": MapDrawControl,
            "basemap_selector": map_widgets.BasemapSelector,
        }
        widget_type = basic_controls.get(widget, None)

        # First, try removing the widget from any layout boxes.
        child_to_remove = None
        for child in self.top_right_layout_box.children:
            if child == widget or isinstance(child, type(widget_type)):
                child_to_remove = child
        if child_to_remove:
            self.top_right_layout_box.children = [
                x for x in self.top_right_layout_box.children if x != child_to_remove
            ]

        if widget_type:
            if control := self._find_widget_of_type(widget_type, return_control=True):
                self.remove(control)
                control.close()
            return

        if hasattr(widget, "name") and widget.name in self.ee_layers:
            self.ee_layers.pop(widget.name)

        if ee_layer := self.ee_layers.pop(widget, None):
            tile_layer = ee_layer.get("ee_layer", None)
            if tile_layer is not None:
                self.remove_layer(tile_layer)
            if legend := ee_layer.get("legend", None):
                self.remove(legend)
            if colorbar := ee_layer.get("colorbar", None):
                self.remove(colorbar)
            return

        super().remove(widget)
        if isinstance(widget, ipywidgets.Widget):
            widget.close()

    def add_layer(
        self,
        ee_object: ee.ComputedObject,
        vis_params: dict[str, Any] | None = None,
        name: str | None = None,
        shown: bool = True,
        opacity: float = 1.0,
    ) -> None:
        """Adds a layer to the map.

        Args:
            ee_object: The Earth Engine object to add.
            vis_params: Visualization parameters. Defaults to None.
            name: The name of the layer. Defaults to None.
            shown: Whether the layer is shown. Defaults to True.
            opacity: The opacity of the layer. Defaults to 1.0.
        """
        # Call super if not an EE object.
        if not isinstance(ee_object, ee_tile_layers.EELeafletTileLayer.EE_TYPES):
            super().add_layer(ee_object)
            return

        if vis_params is None:
            vis_params = {}
        if name is None:
            name = f"Layer {len(self.ee_layers) + 1}"

        if isinstance(ee_object, ee.ImageCollection):
            ee_object = ee_object.mosaic()
        tile_layer = ee_tile_layers.EELeafletTileLayer(
            ee_object, vis_params, name, shown, opacity
        )

        # Remove the layer if it already exists.
        self.remove(name)

        self.ee_layers[name] = {
            "ee_object": ee_object,
            "ee_layer": tile_layer,
            "vis_params": vis_params,
        }
        super().add(tile_layer)

    def _add_legend(
        self,
        title: str = "Legend",
        legend_dict: dict[str, str] | None = None,
        keys: list[Any] | None = None,
        colors: list[Any] | None = None,
        position: str = "bottomright",
        builtin_legend: str | None = None,
        layer_name: str | None = None,
        add_header: bool = True,
        widget_args: dict[Any, Any] | None = None,
        **kwargs: Any,
    ) -> ipyleaflet.WidgetControl:
        """Adds a customized legend to the map.

        Args:
            title: Title of the legend. Defaults to 'Legend'.
            legend_dict: A dictionary containing legend items as keys and color as
                values. If provided, keys and colors will be ignored. Defaults to None.
            keys: A list of legend keys. Defaults to None.
            colors: A list of legend colors. Defaults to None.
            position: Position of the legend. Defaults to 'bottomright'.
            builtin_legend: Name of the builtin legend to add to the map.
                Defaults to None.
            layer_name: The associated layer for the legend.
                Defaults to None.
            add_header: Whether the legend can be closed or not.
                Defaults to True.
            widget_args: Additional arguments passed to widget_template().
                Defaults to {}.
        """
        legend = map_widgets.Legend(
            title,
            legend_dict,
            keys,
            colors,
            position,
            builtin_legend,
            add_header,
            widget_args,
            **kwargs,
        )
        legend.host_map = self
        control = ipyleaflet.WidgetControl(
            widget=legend, position=position, transparent_bg=True
        )
        if layer := self.ee_layers.get(layer_name, None):
            if old_legend := layer.pop("legend", None):
                self.remove(old_legend)
            layer["legend"] = control

        super().add(control)
        return control

    def _add_colorbar(
        self,
        vis_params: dict[str, Any] | None = None,
        cmap: str = "gray",
        discrete: bool = False,
        label: str | None = None,
        orientation: str = "horizontal",
        position: str = "bottomright",
        transparent_bg: bool = False,
        layer_name: str | None = None,
        font_size: int = 9,
        axis_off: bool = False,
        max_width: str | None = None,
        **kwargs: Any,
    ) -> ipyleaflet.WidgetControl:
        """Add a matplotlib colorbar to the map.

        Args:
            vis_params: Visualization parameters as a dictionary. See
                https://developers.google.com/earth-engine/guides/image_visualization for
                options.
            cmap: Matplotlib colormap. Defaults to "gray". See
                https://matplotlib.org/3.3.4/tutorials/colors/colormaps.html#sphx-glr-tutorials-colors-colormaps-py
                for options.
            discrete: Whether to create a discrete colorbar. Defaults to False.
            label: Label for the colorbar. Defaults to None.
            orientation: Orientation of the colorbar, such as "vertical" and
                "horizontal". Defaults to "horizontal".
            position: Position of the colorbar on the map. It can be one of: topleft,
                topright, bottomleft, and bottomright. Defaults to "bottomright".
            transparent_bg: Whether to use transparent background. Defaults to False.
            layer_name: The layer name associated with the colorbar. Defaults to None.
            font_size: Font size for the colorbar. Defaults to 9.
            axis_off: Whether to turn off the axis. Defaults to False.
            max_width: Maximum width of the colorbar in pixels. Defaults to None.

        Raises:
            TypeError: If the vis_params is not a dictionary.
            ValueError: If the orientation is not either horizontal or vertical.
            TypeError: If the provided min value is not scalar type.
            TypeError: If the provided max value is not scalar type.
            TypeError: If the provided opacity value is not scalar type.
            TypeError: If cmap or palette is not provided.
        """
        colorbar = map_widgets.Colorbar(
            vis_params,
            cmap,
            discrete,
            label,
            orientation,
            transparent_bg,
            font_size,
            axis_off,
            max_width,
            **kwargs,
        )
        control = ipyleaflet.WidgetControl(widget=colorbar, position=position)
        if layer := self.ee_layers.get(layer_name, None):
            if old_colorbar := layer.pop("colorbar", None):
                self.remove(old_colorbar)
            layer["colorbar"] = control

        super().add(control)
        return control

    def _open_help_page(
        self, host_map: "MapInterface", selected: bool, item: toolbar.ToolbarItem
    ) -> None:
        """Opens the help page.

        Args:
            host_map: The host map.
            selected: Whether the item is selected.
            item: The toolbar item.
        """
        del host_map, item  # Unused.
        if selected:
            coreutils.open_url("https://geemap.org")

    def _toolbar_main_tools(self) -> list[toolbar.ToolbarItem]:
        """Returns the main tools for the toolbar."""

        @toolbar._cleanup_toolbar_item
        def inspector_tool_callback(
            map: Map, selected: bool, item: toolbar.ToolbarItem
        ):
            del selected, item  # Unused.
            map.add("inspector")
            return map._inspector

        @toolbar._cleanup_toolbar_item
        def basemap_tool_callback(map: Map, selected: bool, item: toolbar.ToolbarItem):
            del selected, item  # Unused.
            map.add("basemap_selector")
            return map._basemap_selector

        return [
            toolbar.ToolbarItem(
                icon="map",
                tooltip="Basemap selector",
                callback=basemap_tool_callback,
            ),
            toolbar.ToolbarItem(
                icon="point_scan",
                tooltip="Inspector",
                callback=inspector_tool_callback,
            ),
            toolbar.ToolbarItem(
                icon="question_mark",
                tooltip="Get help",
                callback=self._open_help_page,
                reset=True,
            ),
        ]

    def _toolbar_extra_tools(self) -> list[toolbar.ToolbarItem]:
        """Returns the extra tools for the toolbar."""
        return []

    def _control_config(self) -> dict[str, list[str]]:
        """Returns the control configuration."""
        return {
            "topleft": [
                "search_control",
                "zoom_control",
                "fullscreen_control",
                "draw_control",
            ],
            "bottomleft": ["scale_control", "measure_control"],
            "topright": ["toolbar", "layer_manager"],
            "bottomright": ["attribution_control"],
        }

    def _apply_kwarg_defaults(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Applies default values to keyword arguments.

        Args:
            kwargs: The keyword arguments.

        Returns:
            The keyword arguments with default values applied.
        """
        ret_kwargs = {}
        for kwarg, default in self._KWARG_DEFAULTS.items():
            ret_kwargs[kwarg] = kwargs.pop(kwarg, default)
        ret_kwargs.update(kwargs)
        return ret_kwargs

    def _replace_basemap(self, basemap_name: str) -> None:
        """Replaces the current basemap with a new one.

        Args:
            basemap_name: The name of the new basemap.
        """
        basemap = self._available_basemaps.get(basemap_name, None)
        if basemap is None:
            logging.warning("Invalid basemap selected: %s", basemap_name)
            return
        new_layer = ipyleaflet.TileLayer(
            url=basemap["url"],
            name=basemap["name"],
            max_zoom=basemap.get("max_zoom", 24),
            attribution=basemap.get("attribution", None),
        )
        if not self.layers:
            self.add_layer(new_layer)
        elif len(self.layers) == 1:
            # TODO check if this quirk/bug is still present:
            # substitute_layer is broken when the map has a single layer.
            self.clear_layers()
            self.add_layer(new_layer)
        else:
            self.substitute_layer(self.layers[0], new_layer)

    def _get_available_basemaps(self) -> dict[str, Any]:
        """Gets the available basemaps.

        Returns:
            Dict[str, Any]: The available basemaps.
        """
        tile_providers = list(basemaps.get_xyz_dict().values())
        if coreutils.get_google_maps_api_key():
            tile_providers = tile_providers + list(
                basemaps.get_google_map_tile_providers().values()
            )

        ret_dict = {}
        for tile_info in tile_providers:
            tile_info["url"] = tile_info.build_url()
            tile_info["max_zoom"] = 30
            ret_dict[tile_info["name"]] = tile_info

        # Each alias needs to point to a single map. For each alias, pick the
        # first aliased map in `self._BASEMAP_ALIASES`.
        aliased_maps = {}
        for alias, maps in self._BASEMAP_ALIASES.items():
            for map_name in maps:
                if provider := ret_dict.get(map_name):
                    aliased_maps[alias] = provider
                    break
        return {**aliased_maps, **ret_dict}  # pytype: disable=bad-return-type

    def _get_preferred_basemap_name(self, basemap_name: str) -> str:
        """Returns the aliased basemap name.

        Args:
            basemap_name: The name of the basemap.

        Returns:
            The aliased basemap name if it exists, otherwise the original basemap name.
        """
        reverse_aliases = {}
        for alias, maps in self._BASEMAP_ALIASES.items():
            for map_name in maps:
                if map_name not in reverse_aliases:
                    reverse_aliases[map_name] = alias
        return reverse_aliases.get(basemap_name, basemap_name)

    def _on_layers_change(self, change: Any) -> None:
        """Handles changes in layers.

        Args:
            change: The change event.
        """
        del change  # Unused.
        if self._layer_manager:
            self._layer_manager.refresh_layers()

    # Keep the following three camelCase methods for backwards compatibility.
    addLayer = add_layer
    centerObject = center_object
    setCenter = set_center
    getBounds = get_bounds
