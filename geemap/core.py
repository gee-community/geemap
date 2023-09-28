"""A generic Map interface and lightweight implementation."""

import logging
import math
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type
import webbrowser

import ee
import ipyleaflet
import ipywidgets

from . import basemaps
from . import common
from . import ee_tile_layers
from . import map_widgets
from . import toolbar


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

    _BASEMAP_ALIASES: Dict[str, str] = {
        "DEFAULT": "OpenStreetMap.Mapnik",
        "ROADMAP": "Esri.WorldStreetMap",
        "SATELLITE": "Esri.WorldImagery",
        "TERRAIN": "Esri.WorldTopoMap",
        "HYBRID": "Esri.WorldImagery",
    }

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
            common.ee_initialize()

        # Listen for layers being added/removed so we can update the layer manager.
        self.observe(self._on_layers_change, "layers")

    def get_zoom(self) -> int:
        return self.zoom

    def set_zoom(self, value: int) -> None:
        self.zoom = value

    def get_center(self) -> Sequence:
        return self.center

    def get_bounds(self) -> Sequence:
        bounds = self.bounds
        return [bounds[0][0], bounds[0][1], bounds[1][0], bounds[1][1]]

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

    def _log_widget_already_present(self, widget: ipywidgets.Widget) -> None:
        logging.warning(
            "A widget of type %s is already present on the map.",
            widget.__class__,
        )

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
    ) -> Optional[Any]:
        """Finds a widget in the controls with the passed in type."""
        for widget in self.controls:
            if isinstance(widget, ipyleaflet.WidgetControl):
                if isinstance(widget.widget, widget_type):
                    return widget if return_control else widget.widget
            elif isinstance(widget, widget_type):
                return widget
        return None

    def add(self, obj: Any, position: str = "topright", **kwargs) -> None:
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
            if widget := self._find_widget_of_type(basic_control[0]):
                self._log_widget_already_present(widget)
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
        elif obj == "basemap_selector":
            self._add_basemap_selector(position, **kwargs)
        else:
            super().add(obj)
        if self._layer_manager:
            self._layer_manager.refresh_layers()

    def _on_toggle_toolbar_layers(self, is_open: bool) -> None:
        if is_open:
            if widget := self._layer_manager:
                self._log_widget_already_present(widget)
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
        if widget := self._layer_manager:
            self._log_widget_already_present(widget)
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
        if widget := self._toolbar:
            self._log_widget_already_present(widget)
            return

        toolbar_val = toolbar.Toolbar(
            self, self._toolbar_main_tools(), self._toolbar_extra_tools(), **kwargs
        )
        toolbar_val.on_layers_toggled = self._on_toggle_toolbar_layers
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_val, position=position
        )
        super().add(toolbar_control)

    def _add_inspector(self, position: str, **kwargs) -> None:
        if widget := self._inspector:
            self._log_widget_already_present(widget)
            return

        inspector = map_widgets.Inspector(self, **kwargs)
        inspector.on_close = lambda: self.remove("inspector")
        inspector_control = ipyleaflet.WidgetControl(
            widget=inspector, position=position
        )
        super().add(inspector_control)

    def _add_layer_editor(self, position: str, **kwargs) -> None:
        if widget := self._layer_editor:
            self._log_widget_already_present(widget)
            return

        widget = map_widgets.LayerEditor(self, **kwargs)
        widget.on_close = lambda: self.remove("layer_editor")
        control = ipyleaflet.WidgetControl(widget=widget, position=position)
        super().add(control)

    def _add_basemap_selector(self, position: str, **kwargs) -> None:
        if widget := self._basemap_selector:
            self._log_widget_already_present(widget)
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
            "basemap_selector": map_widgets.Basemap,
        }
        if widget_type := basic_controls.get(widget, None):
            if control := self._find_widget_of_type(widget_type, return_control=True):
                self.remove(control)
                control.close()
            return

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

    addLayer = add_layer

    def _open_help_page(self, host_map: MapInterface, selected: bool) -> None:
        del host_map  # Unused.
        if selected:
            webbrowser.open_new_tab("https://geemap.org")

    def _toolbar_main_tools(self) -> List[toolbar.Toolbar.Item]:
        return [
            toolbar.Toolbar.Item(
                icon="map",
                tooltip="Basemap selector",
                callback=lambda m, selected: m.add("basemap_selector")
                if selected
                else None,
                reset=False,
            ),
            toolbar.Toolbar.Item(
                icon="info",
                tooltip="Inspector",
                callback=lambda m, selected: m.add("inspector") if selected else None,
            ),
            toolbar.Toolbar.Item(
                icon="question", tooltip="Get help", callback=self._open_help_page
            ),
        ]

    def _toolbar_extra_tools(self) -> Optional[List[toolbar.Toolbar.Item]]:
        return None

    def _control_config(self) -> Dict[str, List[str]]:
        return {
            "topleft": ["zoom_control", "fullscreen_control"],
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
        ret_dict = {}
        for tile_info in basemaps.get_xyz_dict().values():
            tile_info["url"] = tile_info.build_url()
            ret_dict[tile_info["name"]] = tile_info
        extra_dict = {k: ret_dict[v] for k, v in self._BASEMAP_ALIASES.items()}
        return {**extra_dict, **ret_dict}

    def _get_preferred_basemap_name(self, basemap_name: str) -> str:
        """Returns the aliased basemap name."""
        try:
            return list(self._BASEMAP_ALIASES.keys())[
                list(self._BASEMAP_ALIASES.values()).index(basemap_name)
            ]
        except ValueError:
            return basemap_name

    def _on_layers_change(self, change) -> None:
        del change  # Unused.
        if self._layer_manager:
            self._layer_manager.refresh_layers()
