"""A generic Map interface and lightweight implementation."""

import enum
import logging
import math
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type

import ee
import ipyleaflet
import ipywidgets

from . import basemaps
from . import common
from . import ee_tile_layers
from . import map_widgets
from . import toolbar

_DRAWN_FEATURES_LAYER = "Drawn Features"


class DrawActions(enum.Enum):
    """Action types for the draw control.

    Args:
        enum (str): Action type.
    """

    CREATED = "created"
    EDITED = "edited"
    DELETED = "deleted"
    REMOVED_LAST = "removed-last"


class AbstractDrawControl(object):
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
    def features(self):
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
    def collection(self):
        return ee.FeatureCollection(self.features if self.count else [])

    @property
    def last_feature(self):
        property = self.get_geometry_properties(self.last_geometry)
        return ee.Feature(self.last_geometry, property) if self.last_geometry else None

    @property
    def count(self):
        return len(self.geometries)

    def reset(self, clear_draw_control=True):
        """Resets the draw controls."""
        if self.layer is not None:
            self.host_map.remove_layer(self.layer)
        self.geometries = []
        self.properties = []
        self.last_geometry = None
        self.layer = None
        if clear_draw_control:
            self._clear_draw_control()

    def remove_geometry(self, geometry):
        """Removes a geometry from the draw control."""
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

    def get_geometry_properties(self, geometry):
        """Gets the properties of a geometry."""
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

    def set_geometry_properties(self, geometry, property):
        """Sets the properties of a geometry."""
        if not geometry:
            return
        try:
            index = self.geometries.index(geometry)
        except ValueError:
            return
        if index >= 0:
            self.properties[index] = property

    def on_geometry_create(self, callback, remove=False):
        self._geometry_create_dispatcher.register_callback(callback, remove=remove)

    def on_geometry_edit(self, callback, remove=False):
        self._geometry_edit_dispatcher.register_callback(callback, remove=remove)

    def on_geometry_delete(self, callback, remove=False):
        self._geometry_delete_dispatcher.register_callback(callback, remove=remove)

    def _bind_to_draw_control(self):
        """Set up draw control event handling like create, edit, and delete."""
        raise NotImplementedError()

    def _remove_geometry_at_index_on_draw_control(self):
        """Remove the geometry at the given index on the draw control."""
        raise NotImplementedError()

    def _clear_draw_control(self):
        """Clears the geometries from the draw control."""
        raise NotImplementedError()

    def _get_synced_geojson_from_draw_control(self):
        """Returns an up-to-date list of GeoJSON from the draw control."""
        raise NotImplementedError()

    def _sync_geometries(self):
        """Sync the local geometries with those from the draw control."""
        if not self.count:
            return
        # The current geometries from the draw_control.
        test_geojsons = self._get_synced_geojson_from_draw_control()
        self.geometries = [
            common.geojson_to_ee(geo_json, geodesic=False) for geo_json in test_geojsons
        ]

    def _redraw_layer(self):
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

    def _handle_geometry_created(self, geo_json):
        geometry = common.geojson_to_ee(geo_json, geodesic=False)
        self.last_geometry = geometry
        self.last_draw_action = DrawActions.CREATED
        self.geometries.append(geometry)
        self.properties.append(None)
        self._redraw_layer()
        self._geometry_create_dispatcher(self, geometry=geometry)

    def _handle_geometry_edited(self, geo_json):
        geometry = common.geojson_to_ee(geo_json, geodesic=False)
        self.last_geometry = geometry
        self.last_draw_action = DrawActions.EDITED
        self._sync_geometries()
        self._geometry_edit_dispatcher(self, geometry=geometry)

    def _handle_geometry_deleted(self, geo_json):
        geometry = common.geojson_to_ee(geo_json, geodesic=False)
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

    def __init__(self, host_map, **kwargs):
        """Initialize the map draw control.

        Args:
            host_map (geemap.Map): The geemap.Map object that the control will be added to.
        """
        super(MapDrawControl, self).__init__(host_map=host_map, **kwargs)

    def _get_synced_geojson_from_draw_control(self):
        return [data.copy() for data in self.data]

    def _bind_to_draw_control(self):
        # Handles draw events
        def handle_draw(_, action, geo_json):
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
            self._sync_geometries()
            # Need to refresh the layer if the last action was an edit.
            if self.last_draw_action == DrawActions.EDITED:
                self._redraw_layer()

        self.observe(handle_data_update, "data")

    def _remove_geometry_at_index_on_draw_control(self, index):
        del self.data[index]
        self.send_state(key="data")

    def _clear_draw_control(self):
        self.data = []  # Remove all drawn features from the map.
        return self.clear()


class MapInterface:
    """Interface for all maps."""

    # The layers on the map.
    ee_layers: Dict[str, Dict[str, Any]]

    # The GeoJSON layers on the map.
    geojson_layers: List[Any]

    def get_zoom(self) -> int:
        """Returns the current zoom level of the map."""
        raise NotImplementedError()

    def set_zoom(self, value: int) -> None:
        """Sets the current zoom level of the map."""
        del value  # Unused.
        raise NotImplementedError()

    def get_center(self) -> Sequence:
        """Returns the current center of the map (lat, lon)."""
        raise NotImplementedError()

    def set_center(self, lon: float, lat: float, zoom: Optional[int] = None) -> None:
        """Centers the map view at a given coordinates with the given zoom level."""
        del lon, lat, zoom  # Unused.
        raise NotImplementedError()

    def center_object(
        self, ee_object: ee.ComputedObject, zoom: Optional[int] = None
    ) -> None:
        """Centers the map view on a given object."""
        del ee_object, zoom  # Unused.
        raise NotImplementedError()

    def get_scale(self) -> float:
        """Returns the approximate pixel scale of the current map view, in meters."""
        raise NotImplementedError()

    def get_bounds(self) -> Tuple[float]:
        """Returns the bounds of the current map view.

        Returns:
            list: A list in the format [west, south, east, north] in degrees.
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

    def add(self, widget: str, position: str, **kwargs) -> None:
        """Adds a widget to the map."""
        del widget, position, kwargs  # Unused.
        raise NotImplementedError()

    def remove(self, widget: str) -> None:
        """Removes a widget to the map."""
        del widget  # Unused.
        raise NotImplementedError()

    def add_layer(
        self,
        ee_object: ee.ComputedObject,
        vis_params: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        shown: bool = True,
        opacity: float = 1.0,
    ) -> None:
        """Adds a layer to the map."""
        del ee_object, vis_params, name, shown, opacity  # Unused.
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

    _KWARG_DEFAULTS: Dict[str, Any] = {
        "center": [0, 0],
        "zoom": 2,
        "zoom_control": False,
        "attribution_control": False,
        "ee_initialize": True,
        "scroll_wheel_zoom": True,
    }

    _BASEMAP_ALIASES: Dict[str, List[str]] = {
        "DEFAULT": ["Google.Roadmap", "OpenStreetMap.Mapnik"],
        "ROADMAP": ["Google.Roadmap", "Esri.WorldStreetMap"],
        "SATELLITE": ["Google.Satellite", "Esri.WorldImagery"],
        "TERRAIN": ["Google.Terrain", "Esri.WorldTopoMap"],
        "HYBRID": ["Google.Hybrid", "Esri.WorldImagery"],
    }

    _USER_AGENT_PREFIX = "geemap-core"

    @property
    def width(self) -> str:
        return self.layout.width

    @width.setter
    def width(self, value: str) -> None:
        self.layout.width = value

    @property
    def height(self) -> str:
        return self.layout.height

    @height.setter
    def height(self, value: str) -> None:
        self.layout.height = value

    @property
    def _toolbar(self) -> Optional[toolbar.Toolbar]:
        return self._find_widget_of_type(toolbar.Toolbar)

    @property
    def _inspector(self) -> Optional[map_widgets.Inspector]:
        return self._find_widget_of_type(map_widgets.Inspector)

    @property
    def _draw_control(self) -> MapDrawControl:
        return self._find_widget_of_type(MapDrawControl)

    @property
    def _layer_manager(self) -> Optional[map_widgets.LayerManager]:
        if toolbar_widget := self._toolbar:
            if isinstance(toolbar_widget.accessory_widget, map_widgets.LayerManager):
                return toolbar_widget.accessory_widget
        return self._find_widget_of_type(map_widgets.LayerManager)

    @property
    def _layer_editor(self) -> Optional[map_widgets.LayerEditor]:
        return self._find_widget_of_type(map_widgets.LayerEditor)

    @property
    def _basemap_selector(self) -> Optional[map_widgets.Basemap]:
        return self._find_widget_of_type(map_widgets.Basemap)

    def __init__(self, **kwargs):
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

        self.ee_layers: Dict[str, Dict[str, Any]] = {}
        self.geojson_layers: List[Any] = []

        kwargs = self._apply_kwarg_defaults(kwargs)
        super().__init__(**kwargs)

        for position, widgets in self._control_config().items():
            for widget in widgets:
                self.add(widget, position=position)

        # Authenticate and initialize EE.
        if kwargs.get("ee_initialize", True):
            common.ee_initialize(user_agent_prefix=self._USER_AGENT_PREFIX)

        # Listen for layers being added/removed so we can update the layer manager.
        self.observe(self._on_layers_change, "layers")

    def get_zoom(self) -> int:
        return self.zoom

    def set_zoom(self, value: int) -> None:
        self.zoom = value

    def get_center(self) -> Sequence:
        return self.center

    def get_bounds(self, as_geojson: bool = False) -> Sequence:
        """Returns the bounds of the current map view.

        Args:
            as_geojson (bool, optional): If true, returns map bounds as
                GeoJSON. Defaults to False.

        Returns:
            list|dict: A list in the format [west, south, east, north] in
                degrees or a GeoJSON dictionary.
        """
        bounds = self.bounds
        if not bounds:
            raise RuntimeError(
                "Map bounds are undefined. Please display the " "map then try again."
            )
        # ipyleaflet returns bounds in the format [[south, west], [north, east]]
        # https://ipyleaflet.readthedocs.io/en/latest/map_and_basemaps/map.html#ipyleaflet.Map.fit_bounds
        coords = [bounds[0][1], bounds[0][0], bounds[1][1], bounds[1][0]]

        if as_geojson:
            return ee.Geometry.BBox(*coords).getInfo()
        return coords

    def get_scale(self) -> float:
        # Reference:
        # - https://blogs.bing.com/maps/2006/02/25/map-control-zoom-levels-gt-resolution
        # - https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Resolution_and_Scale
        center_lat = self.center[0]
        center_lat_cos = math.cos(math.radians(center_lat))
        return 156543.04 * center_lat_cos / math.pow(2, self.zoom)

    def set_center(self, lon: float, lat: float, zoom: Optional[int] = None) -> None:
        self.center = (lat, lon)
        if zoom is not None:
            self.zoom = zoom

    def _get_geometry(
        self, ee_object: ee.ComputedObject, max_error: float
    ) -> ee.Geometry:
        """Returns the geometry for an arbitrary EE object."""
        if isinstance(ee_object, ee.Geometry):
            return ee_object
        try:
            return ee_object.geometry(maxError=max_error)
        except Exception as exc:
            raise Exception(
                "ee_object must be one of ee.Geometry, ee.FeatureCollection, ee.Image, or ee.ImageCollection."
            ) from exc

    def center_object(
        self, ee_object: ee.ComputedObject, zoom: Optional[int] = None
    ) -> None:
        max_error = 0.001
        geometry = self._get_geometry(ee_object, max_error).transform(
            maxError=max_error
        )
        if zoom is None:
            coordinates = geometry.bounds(max_error).getInfo()["coordinates"][0]
            x_vals = [c[0] for c in coordinates]
            y_vals = [c[1] for c in coordinates]
            self.fit_bounds([[min(y_vals), min(x_vals)], [max(y_vals), max(x_vals)]])
        else:
            if not isinstance(zoom, int):
                raise ValueError("Zoom must be an integer.")
            centroid = geometry.centroid(maxError=max_error).getInfo()["coordinates"]
            self.set_center(centroid[0], centroid[1], zoom)

    def _find_widget_of_type(
        self, widget_type: Type, return_control: bool = False
    ) -> Optional[ipywidgets.Widget]:
        """Finds a widget in the controls with the passed in type."""
        for widget in self.controls:
            if isinstance(widget, ipyleaflet.WidgetControl):
                if isinstance(widget.widget, widget_type):
                    return widget if return_control else widget.widget
            elif isinstance(widget, widget_type):
                return widget
        return None

    def add(self, obj: Any, position: str = "", **kwargs) -> None:
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
        basic_controls: Dict[str, Tuple[ipyleaflet.Control, Dict[str, Any]]] = {
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

    def _on_toggle_toolbar_layers(self, is_open: bool) -> None:
        if is_open:
            if self._layer_manager:
                return

            def _on_open_vis(layer_name: str) -> None:
                layer = self.ee_layers.get(layer_name, None)
                self._add_layer_editor(position="bottomright", layer_dict=layer)

            layer_manager = map_widgets.LayerManager(self)
            layer_manager.header_hidden = True
            layer_manager.close_button_hidden = True
            layer_manager.on_open_vis = _on_open_vis
            self._toolbar.accessory_widget = layer_manager
        else:
            self._toolbar.accessory_widget = None
            self.remove("layer_manager")

    def _add_layer_manager(self, position: str, **kwargs) -> None:
        if self._layer_manager:
            return

        def _on_open_vis(layer_name: str) -> None:
            layer = self.ee_layers.get(layer_name, None)
            self._add_layer_editor(position="bottomright", layer_dict=layer)

        layer_manager = map_widgets.LayerManager(self, **kwargs)
        layer_manager.on_close = lambda: self.remove("layer_manager")
        layer_manager.on_open_vis = _on_open_vis
        layer_manager_control = ipyleaflet.WidgetControl(
            widget=layer_manager, position=position
        )
        super().add(layer_manager_control)

    def _add_toolbar(self, position: str, **kwargs) -> None:
        if self._toolbar:
            return

        toolbar_val = toolbar.Toolbar(
            self, self._toolbar_main_tools(), self._toolbar_extra_tools(), **kwargs
        )
        toolbar_val.on_layers_toggled = self._on_toggle_toolbar_layers
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_val, position=position
        )
        super().add(toolbar_control)
        # Enable the layer manager by default.
        toolbar_val.toggle_layers(True)

    def _add_inspector(self, position: str, **kwargs) -> None:
        if self._inspector:
            return

        inspector = map_widgets.Inspector(self, **kwargs)
        inspector.on_close = lambda: self.remove("inspector")
        inspector_control = ipyleaflet.WidgetControl(
            widget=inspector, position=position
        )
        super().add(inspector_control)

    def _add_layer_editor(self, position: str, **kwargs) -> None:
        if self._layer_editor:
            return

        widget = map_widgets.LayerEditor(self, **kwargs)
        widget.on_close = lambda: self.remove("layer_editor")
        control = ipyleaflet.WidgetControl(widget=widget, position=position)
        super().add(control)

    def _add_draw_control(self, position="topleft", **kwargs) -> None:
        """Add a draw control to the map

        Args:
            position (str, optional): The position of the draw control. Defaults to "topleft".
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

    def get_draw_control(self) -> Optional[MapDrawControl]:
        return self._draw_control

    def _add_basemap_selector(self, position: str, **kwargs) -> None:
        if self._basemap_selector:
            return

        basemap_names = kwargs.pop("basemaps", list(self._available_basemaps.keys()))
        value = kwargs.pop(
            "value", self._get_preferred_basemap_name(self.layers[0].name)
        )
        basemap = map_widgets.Basemap(basemap_names, value, **kwargs)
        basemap.on_close = lambda: self.remove("basemap_selector")
        basemap.on_basemap_changed = self._replace_basemap
        basemap_control = ipyleaflet.WidgetControl(widget=basemap, position=position)
        super().add(basemap_control)

    def remove(self, widget: Any) -> None:
        """Removes a widget to the map."""

        basic_controls: Dict[str, ipyleaflet.Control] = {
            "zoom_control": ipyleaflet.ZoomControl,
            "fullscreen_control": ipyleaflet.FullScreenControl,
            "scale_control": ipyleaflet.ScaleControl,
            "attribution_control": ipyleaflet.AttributionControl,
            "toolbar": toolbar.Toolbar,
            "inspector": map_widgets.Inspector,
            "layer_manager": map_widgets.LayerManager,
            "layer_editor": map_widgets.LayerEditor,
            "draw_control": MapDrawControl,
            "basemap_selector": map_widgets.Basemap,
        }
        if widget_type := basic_controls.get(widget, None):
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
        vis_params: Dict[str, Any] = None,
        name: Optional[str] = None,
        shown: bool = True,
        opacity: float = 1.0,
    ) -> None:
        """Adds a layer to the map."""

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
        legend_dict: Dict[str, str] = None,
        keys: List[Any] = None,
        colors: List[Any] = None,
        position: str = "bottomright",
        builtin_legend: str = None,
        layer_name: str = None,
        add_header: bool = True,
        widget_args: Dict[Any, Any] = None,
        **kwargs,
    ):
        """Adds a customized legend to the map.

        Args:
            title (str, optional): Title of the legend. Defaults to 'Legend'.
            legend_dict (dict, optional): A dictionary containing legend items
                as keys and color as values. If provided, keys and colors will
                be ignored. Defaults to None.
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
        control = ipyleaflet.WidgetControl(widget=legend, position=position)
        if layer := self.ee_layers.get(layer_name, None):
            if old_legend := layer.pop("legend", None):
                self.remove(old_legend)
            layer["legend"] = control

        super().add(control)
        return control

    def _add_colorbar(
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
        max_width=None,
        **kwargs,
    ):
        """Add a matplotlib colorbar to the map.

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
        self, host_map: MapInterface, selected: bool, item: toolbar.Toolbar.Item
    ) -> None:
        del host_map, item  # Unused.
        if selected:
            common.open_url("https://geemap.org")

    def _toolbar_main_tools(self) -> List[toolbar.Toolbar.Item]:
        @toolbar._cleanup_toolbar_item
        def inspector_tool_callback(
            map: Map, selected: bool, item: toolbar.Toolbar.Item
        ):
            del selected, item  # Unused.
            map.add("inspector")
            return map._inspector

        @toolbar._cleanup_toolbar_item
        def basemap_tool_callback(map: Map, selected: bool, item: toolbar.Toolbar.Item):
            del selected, item  # Unused.
            map.add("basemap_selector")
            return map._basemap_selector

        return [
            toolbar.Toolbar.Item(
                icon="map",
                tooltip="Basemap selector",
                callback=basemap_tool_callback,
                reset=False,
            ),
            toolbar.Toolbar.Item(
                icon="info",
                tooltip="Inspector",
                callback=inspector_tool_callback,
                reset=False,
            ),
            toolbar.Toolbar.Item(
                icon="question", tooltip="Get help", callback=self._open_help_page
            ),
        ]

    def _toolbar_extra_tools(self) -> Optional[List[toolbar.Toolbar.Item]]:
        return None

    def _control_config(self) -> Dict[str, List[str]]:
        return {
            "topleft": ["zoom_control", "fullscreen_control", "draw_control"],
            "bottomleft": ["scale_control", "measure_control"],
            "topright": ["toolbar"],
            "bottomright": ["attribution_control"],
        }

    def _apply_kwarg_defaults(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        ret_kwargs = {}
        for kwarg, default in self._KWARG_DEFAULTS.items():
            ret_kwargs[kwarg] = kwargs.pop(kwarg, default)
        ret_kwargs.update(kwargs)
        return ret_kwargs

    def _replace_basemap(self, basemap_name: str) -> None:
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
        # substitute_layer is broken when the map has a single layer.
        if len(self.layers) == 1:
            self.clear_layers()
            self.add_layer(new_layer)
        else:
            self.substitute_layer(self.layers[0], new_layer)

    def _get_available_basemaps(self) -> Dict[str, Any]:
        """Convert xyz tile services to a dictionary of basemaps."""
        tile_providers = list(basemaps.get_xyz_dict().values())
        if common.get_google_maps_api_key():
            tile_providers = tile_providers + list(
                basemaps.get_google_map_tile_providers().values()
            )

        ret_dict = {}
        for tile_info in tile_providers:
            tile_info["url"] = tile_info.build_url()
            ret_dict[tile_info["name"]] = tile_info

        # Each alias needs to point to a single map. For each alias, pick the
        # first aliased map in `self._BASEMAP_ALIASES`.
        aliased_maps = {}
        for alias, maps in self._BASEMAP_ALIASES.items():
            for map_name in maps:
                if provider := ret_dict.get(map_name):
                    aliased_maps[alias] = provider
                    break
        return {**aliased_maps, **ret_dict}

    def _get_preferred_basemap_name(self, basemap_name: str) -> str:
        """Returns the aliased basemap name."""
        reverse_aliases = {}
        for alias, maps in self._BASEMAP_ALIASES.items():
            for map_name in maps:
                if map_name not in reverse_aliases:
                    reverse_aliases[map_name] = alias
        return reverse_aliases.get(basemap_name, basemap_name)

    def _on_layers_change(self, change) -> None:
        del change  # Unused.
        if self._layer_manager:
            self._layer_manager.refresh_layers()

    # Keep the following three camelCase methods for backwards compatibility.
    addLayer = add_layer
    centerObject = center_object
    setCenter = set_center
    getBounds = get_bounds
