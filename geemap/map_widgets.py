"""Various ipywidgets that can be added to a map."""

import enum

import ee
import ipytree
import ipywidgets

from . import common
from .ee_tile_layers import EELeafletTileLayer


class Colorbar(ipywidgets.Output):
    """A matplotlib colorbar widget that can be added to the map."""

    def __init__(
        self,
        vis_params=None,
        cmap="gray",
        discrete=False,
        label=None,
        orientation="horizontal",
        transparent_bg=False,
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
            transparent_bg (bool, optional): Whether to use transparent background. Defaults to False.
            font_size (int, optional): Font size for the colorbar. Defaults to 9.
            axis_off (bool, optional): Whether to turn off the axis. Defaults to False.
            max_width (str, optional): Maximum width of the colorbar in pixels. Defaults to None.

        Raises:
            TypeError: If the vis_params is not a dictionary.
            ValueError: If the orientation is not either horizontal or vertical.
            ValueError: If the provided min value is not scalar type.
            ValueError: If the provided max value is not scalar type.
            ValueError: If the provided opacity value is not scalar type.
            ValueError: If cmap or palette is not provided.
        """

        import matplotlib  # pylint: disable=import-outside-toplevel
        import numpy  # pylint: disable=import-outside-toplevel

        if max_width is None:
            if orientation == "horizontal":
                max_width = "270px"
            else:
                max_width = "100px"

        if isinstance(vis_params, (list, tuple)):
            vis_params = {"palette": list(vis_params)}
        elif not vis_params:
            vis_params = {}

        if not isinstance(vis_params, dict):
            raise TypeError("The vis_params must be a dictionary.")

        if isinstance(kwargs.get("colors"), (list, tuple)):
            vis_params["palette"] = list(kwargs["colors"])

        width, height = self._get_dimensions(orientation, kwargs)

        vmin = vis_params.get("min", kwargs.pop("vmin", 0))
        if type(vmin) not in (int, float):
            raise TypeError("The provided min value must be scalar type.")

        vmax = vis_params.get("max", kwargs.pop("mvax", 1))
        if type(vmax) not in (int, float):
            raise TypeError("The provided max value must be scalar type.")

        alpha = vis_params.get("opacity", kwargs.pop("alpha", 1))
        if type(alpha) not in (int, float):
            raise TypeError("The provided opacity or alpha value must be type scalar.")

        if "palette" in vis_params.keys():
            hexcodes = common.to_hex_colors(common.check_cmap(vis_params["palette"]))
            if discrete:
                cmap = matplotlib.colors.ListedColormap(hexcodes)
                linspace = numpy.linspace(vmin, vmax, cmap.N + 1)
                norm = matplotlib.colors.BoundaryNorm(linspace, cmap.N)
            else:
                cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
                    "custom", hexcodes, N=256
                )
                norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
        elif cmap:
            cmap = matplotlib.pyplot.get_cmap(cmap)
            norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
        else:
            raise ValueError(
                'cmap keyword or "palette" key in vis_params must be provided.'
            )

        fig, ax = matplotlib.pyplot.subplots(figsize=(width, height))
        cb = matplotlib.colorbar.ColorbarBase(
            ax,
            norm=norm,
            alpha=alpha,
            cmap=cmap,
            orientation=orientation,
            **kwargs,
        )

        label = label or vis_params.get("bands") or kwargs.pop("caption", None)
        if label:
            cb.set_label(label, fontsize=font_size)

        if axis_off:
            ax.set_axis_off()
        ax.tick_params(labelsize=font_size)

        # Set the background color to transparent.
        if transparent_bg:
            fig.patch.set_alpha(0.0)

        super().__init__(layout=ipywidgets.Layout(width=max_width))
        with self:
            self.outputs = ()
            matplotlib.pyplot.show()

    def _get_dimensions(self, orientation, kwargs):
        default_dims = {"horizontal": (3.0, 0.3), "vertical": (0.3, 3.0)}
        if orientation in default_dims:
            default = default_dims[orientation]
            return (
                kwargs.get("width", default[0]),
                kwargs.get("height", default[1]),
            )
        raise ValueError(
            f"orientation must be one of [{', '.join(default_dims.keys())}]."
        )


class Inspector(ipywidgets.VBox):
    """Inspector widget for Earth Engine data."""

    def __init__(
        self,
        host_map,
        names=None,
        visible=True,
        decimals=2,
        opened=True,
        show_close_button=True,
    ):
        """Creates an Inspector widget for Earth Engine data.

        Args:
            host_map (geemap.Map): The map to add the inspector widget to.
            names (list, optional): The list of layer names to be inspected. Defaults to None.
            visible (bool, optional): Whether to inspect visible layers only. Defaults to True.
            decimals (int, optional): The number of decimal places to round the values. Defaults to 2.
            opened (bool, optional): Whether the inspector is opened. Defaults to True.
            show_close_button (bool, optional): Whether to show the close button. Defaults to True.
        """

        self._host_map = host_map
        if not host_map:
            raise ValueError("Must pass a valid map when creating an inspector.")

        self._names = names
        self._visible = visible
        self._decimals = decimals
        self._opened = opened

        self.on_close = None

        self._expand_point_tree = False
        self._expand_pixels_tree = True
        self._expand_objects_tree = False

        host_map.default_style = {"cursor": "crosshair"}

        left_padded_square = ipywidgets.Layout(
            width="28px", height="28px", padding="0px 0px 0px 4px"
        )

        self.toolbar_button = ipywidgets.ToggleButton(
            value=opened, tooltip="Inspector", icon="info", layout=left_padded_square
        )
        self.toolbar_button.observe(self._on_toolbar_btn_click, "value")

        close_button = ipywidgets.ToggleButton(
            value=False,
            tooltip="Close the tool",
            icon="times",
            button_style="primary",
            layout=left_padded_square,
        )
        close_button.observe(self._on_close_btn_click, "value")

        point_checkbox = self._create_checkbox("Point", self._expand_point_tree)
        pixels_checkbox = self._create_checkbox("Pixels", self._expand_pixels_tree)
        objects_checkbox = self._create_checkbox("Objects", self._expand_objects_tree)
        point_checkbox.observe(self._on_point_checkbox_changed, "value")
        pixels_checkbox.observe(self._on_pixels_checkbox_changed, "value")
        objects_checkbox.observe(self._on_objects_checkbox_changed, "value")
        self.inspector_checks = ipywidgets.HBox(
            children=[
                ipywidgets.Label(
                    "Expand", layout=ipywidgets.Layout(padding="0px 8px 0px 4px")
                ),
                point_checkbox,
                pixels_checkbox,
                objects_checkbox,
            ]
        )

        if show_close_button:
            self.toolbar_header = ipywidgets.HBox(
                children=[close_button, self.toolbar_button]
            )
        else:
            self.toolbar_header = ipywidgets.HBox(children=[self.toolbar_button])
        self.tree_output = ipywidgets.VBox(
            children=[],
            layout=ipywidgets.Layout(
                max_width="600px", max_height="300px", overflow="auto", display="block"
            ),
        )
        self._clear_inspector_output()

        host_map.on_interaction(self._on_map_interaction)
        self.toolbar_button.value = opened

        super().__init__(
            children=[self.toolbar_header, self.inspector_checks, self.tree_output]
        )

    def _create_checkbox(self, title, checked):
        layout = ipywidgets.Layout(width="auto", padding="0px 6px 0px 0px")
        return ipywidgets.Checkbox(
            description=title, indent=False, value=checked, layout=layout
        )

    def _on_map_interaction(self, **kwargs):
        latlon = kwargs.get("coordinates")
        if kwargs.get("type") == "click":
            self._on_map_click(latlon)

    def _on_map_click(self, latlon):
        if self.toolbar_button.value:
            self._host_map.default_style = {"cursor": "wait"}
            self._clear_inspector_output()

            nodes = [self._point_info(latlon)]
            pixels_node = self._pixels_info(latlon)
            if pixels_node.nodes:
                nodes.append(pixels_node)
            objects_node = self._objects_info(latlon)
            if objects_node.nodes:
                nodes.append(objects_node)

            self.tree_output.children = [ipytree.Tree(nodes=nodes)]
            self._host_map.default_style = {"cursor": "crosshair"}

    def _clear_inspector_output(self):
        self.tree_output.children = []
        self.children = []
        self.children = [self.toolbar_header, self.inspector_checks, self.tree_output]

    def _on_point_checkbox_changed(self, change):
        self._expand_point_tree = change["new"]

    def _on_pixels_checkbox_changed(self, change):
        self._expand_pixels_tree = change["new"]

    def _on_objects_checkbox_changed(self, change):
        self._expand_objects_tree = change["new"]

    def _on_toolbar_btn_click(self, change):
        if change["new"]:
            self._host_map.default_style = {"cursor": "crosshair"}
            self.children = [
                self.toolbar_header,
                self.inspector_checks,
                self.tree_output,
            ]
            self._clear_inspector_output()
        else:
            self.children = [self.toolbar_button]
            self._host_map.default_style = {"cursor": "default"}

    def _on_close_btn_click(self, change):
        if change["new"]:
            if self._host_map:
                self._host_map.default_style = {"cursor": "default"}
                self._host_map.on_interaction(self._on_map_interaction, remove=True)
            if self.on_close is not None:
                self.on_close()

    def _get_visible_map_layers(self):
        layers = {}
        if self._names is not None:
            names = [names] if isinstance(names, str) else self._names
            for name in names:
                if name in self._host_map.ee_layers:
                    layers[name] = self._host_map.ee_layers[name]
        else:
            layers = self._host_map.ee_layers
        return {k: v for k, v in layers.items() if v["ee_layer"].visible}

    def _root_node(self, title, nodes, **kwargs):
        return ipytree.Node(
            title,
            icon="archive",
            nodes=nodes,
            open_icon="plus-square",
            open_icon_style="success",
            close_icon="minus-square",
            close_icon_style="info",
            **kwargs,
        )

    def _point_info(self, latlon):
        scale = self._host_map.get_scale()
        label = f"Point ({latlon[1]:.{self._decimals}f}, {latlon[0]:.{self._decimals}f}) at {int(scale)}m/px"
        nodes = [
            ipytree.Node(f"Longitude: {latlon[1]}"),
            ipytree.Node(f"Latitude: {latlon[0]}"),
            ipytree.Node(f"Zoom Level: {self._host_map.zoom}"),
            ipytree.Node(f"Scale (approx. m/px): {scale}"),
        ]
        return self._root_node(label, nodes, opened=self._expand_point_tree)

    def _query_point(self, latlon, ee_object):
        point = ee.Geometry.Point(latlon[::-1])
        scale = self._host_map.get_scale()
        if isinstance(ee_object, ee.ImageCollection):
            ee_object = ee_object.mosaic()
        if isinstance(ee_object, ee.Image):
            return ee_object.reduceRegion(ee.Reducer.first(), point, scale).getInfo()
        return None

    def _pixels_info(self, latlon):
        if not self._visible:
            return self._root_node("Pixels", [])

        layers = self._get_visible_map_layers()
        nodes = []
        for layer_name, layer in layers.items():
            ee_object = layer["ee_object"]
            pixel = self._query_point(latlon, ee_object)
            if not pixel:
                continue
            pluralized_band = "band" if len(pixel) == 1 else "bands"
            ee_obj_type = ee_object.__class__.__name__
            label = f"{layer_name}: {ee_obj_type} ({len(pixel)} {pluralized_band})"
            layer_node = ipytree.Node(label, opened=self._expand_pixels_tree)
            for key, value in sorted(pixel.items()):
                if isinstance(value, float):
                    value = round(value, self._decimals)
                layer_node.add_node(ipytree.Node(f"{key}: {value}", icon="file"))
            nodes.append(layer_node)

        return self._root_node("Pixels", nodes)

    def _get_bbox(self, latlon):
        lat, lon = latlon
        delta = 0.005
        return ee.Geometry.BBox(lon - delta, lat - delta, lon + delta, lat + delta)

    def _objects_info(self, latlon):
        if not self._visible:
            return self._root_node("Objects", [])

        layers = self._get_visible_map_layers()
        point = ee.Geometry.Point(latlon[::-1])
        nodes = []
        for layer_name, layer in layers.items():
            ee_object = layer["ee_object"]
            if isinstance(ee_object, ee.FeatureCollection):
                geom = ee.Feature(ee_object.first()).geometry()
                bbox = self._get_bbox(latlon)
                is_point = ee.Algorithms.If(
                    geom.type().compareTo(ee.String("Point")), point, bbox
                )
                ee_object = ee_object.filterBounds(is_point).first()
                tree_node = common.get_info(
                    ee_object, layer_name, self._expand_objects_tree, True
                )
                if tree_node:
                    nodes.append(tree_node)

        return self._root_node("Objects", nodes)


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
            host_map (geemap.Map): The geemap.Map instance to be linked with the draw control.
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
        i = 0
        while i < self.count and i < len(test_geojsons):
            local_geometry = None
            test_geometry = None
            while i < self.count and i < len(test_geojsons):
                local_geometry = self.geometries[i]
                test_geometry = common.geojson_to_ee(test_geojsons[i], False)
                if test_geometry == local_geometry:
                    i += 1
                else:
                    break
            if i < self.count and test_geometry is not None:
                self.geometries[i] = test_geometry
        if self.layer is not None:
            self._redraw_layer()

    def _redraw_layer(self):
        layer = EELeafletTileLayer(
            self.collection, {"color": "blue"}, "Drawn Features", False, 0.5
        )
        if self.host_map:
            layer_index = self.host_map.find_layer_index("Drawn Features")
            if layer_index == -1:
                self.host_map.add_layer(layer)
            else:
                self.host_map.substitute(self.host_map.layers[layer_index], layer)
        self.layer = layer

    def _handle_geometry_created(self, geo_json):
        geometry = common.geojson_to_ee(geo_json, False)
        self.last_geometry = geometry
        self.last_draw_action = DrawActions.CREATED
        self.geometries.append(geometry)
        self.properties.append(None)
        self._redraw_layer()
        self._geometry_create_dispatcher(self, geometry=geometry)

    def _handle_geometry_edited(self, geo_json):
        geometry = common.geojson_to_ee(geo_json, False)
        self.last_geometry = geometry
        self.last_draw_action = DrawActions.EDITED
        self._sync_geometries()
        self._redraw_layer()
        self._geometry_edit_dispatcher(self, geometry=geometry)

    def _handle_geometry_deleted(self, geo_json):
        geometry = common.geojson_to_ee(geo_json, False)
        self.last_geometry = geometry
        self.last_draw_action = DrawActions.DELETED
        try:
            index = self.geometries.index(geometry)
        except ValueError:
            return
        if index >= 0:
            del self.geometries[index]
            del self.properties[index]
            self._redraw_layer()
            self._geometry_delete_dispatcher(self, geometry=geometry)


class LayerManager(ipywidgets.VBox):
    def __init__(self, host_map):
        """Initializes a layer manager widget.
        Args:
            host_map (geemap.Map): The geemap.Map object.
        """
        self._host_map = host_map
        if not host_map:
            raise ValueError("Must pass a valid map when creating a layer manager.")

        self._collapse_button = ipywidgets.ToggleButton(
            value=False,
            tooltip="Layer Manager",
            icon="server",
            layout=ipywidgets.Layout(
                width="28px", height="28px", padding="0px 0px 0px 4px"
            ),
        )
        self._close_button = ipywidgets.Button(
            tooltip="Close the tool",
            icon="times",
            button_style="primary",
            layout=ipywidgets.Layout(width="28px", height="28px", padding="0px"),
        )

        self._toolbar_header = ipywidgets.HBox(
            children=[self._close_button, self._collapse_button]
        )
        self._toolbar_footer = ipywidgets.VBox(children=[])

        self._collapse_button.observe(self._on_collapse_click, "value")
        self._close_button.on_click(self._on_close_click)

        self.on_close = None
        self.on_open_vis = None

        self.collapsed = False
        self.header_hidden = False
        self.close_button_hidden = False

        super().__init__([self._toolbar_header, self._toolbar_footer])

    @property
    def collapsed(self):
        return not self._collapse_button.value

    @collapsed.setter
    def collapsed(self, value):
        self._collapse_button.value = not value

    @property
    def header_hidden(self):
        return self._toolbar_header.layout.display == "none"

    @header_hidden.setter
    def header_hidden(self, value):
        self._toolbar_header.layout.display = "none" if value else "block"

    @property
    def close_button_hidden(self):
        return self._close_button.style.display == "none"

    @close_button_hidden.setter
    def close_button_hidden(self, value):
        self._close_button.style.display = "none" if value else "inline-block"

    def refresh_layers(self):
        """Recreates all the layer widgets."""
        toggle_all_layout = ipywidgets.Layout(
            height="18px", width="30ex", padding="0px 8px 25px 8px"
        )
        toggle_all_checkbox = ipywidgets.Checkbox(
            value=False,
            description="All layers on/off",
            indent=False,
            layout=toggle_all_layout,
        )
        toggle_all_checkbox.observe(self._on_all_layers_visibility_toggled, "value")

        layer_rows = [toggle_all_checkbox]
        for layer in self._host_map.layers[1:]:  # Skip the basemap.
            layer_rows.append(self._render_layer_row(layer))
        self._toolbar_footer.children = layer_rows

    def _on_close_click(self, _):
        if self.on_close:
            self.on_close()

    def _on_collapse_click(self, change):
        if change["new"]:
            self.refresh_layers()
            self.children = [self._toolbar_header, self._toolbar_footer]
        else:
            self.children = [self._collapse_button]

    def _render_layer_row(self, layer):
        visibility_checkbox = ipywidgets.Checkbox(
            value=self._compute_layer_visibility(layer),
            description=layer.name,
            indent=False,
            layout=ipywidgets.Layout(height="18px", width="140px"),
        )
        visibility_checkbox.observe(
            lambda change: self._on_layer_visibility_changed(change, layer), "value"
        )

        opacity_slider = ipywidgets.FloatSlider(
            value=self._compute_layer_opacity(layer),
            min=0,
            max=1,
            step=0.01,
            readout=False,
            layout=ipywidgets.Layout(width="80px"),
        )
        opacity_slider.observe(
            lambda change: self._on_layer_opacity_changed(change, layer), "value"
        )

        settings_button = ipywidgets.Button(
            icon="gear",
            layout=ipywidgets.Layout(width="25px", height="25px", padding="0px"),
            tooltip=layer.name,
        )
        settings_button.on_click(self._on_layer_settings_click)

        return ipywidgets.HBox(
            [visibility_checkbox, settings_button, opacity_slider],
            layout=ipywidgets.Layout(padding="0px 8px 0px 8px"),
        )

    def _compute_layer_opacity(self, layer):
        if layer in self._host_map.geojson_layers:
            opacity = layer.style.get("opacity", 1.0)
            fill_opacity = layer.style.get("fillOpacity", 1.0)
            return max(opacity, fill_opacity)
        return layer.opacity if hasattr(layer, "opacity") else 1.0

    def _compute_layer_visibility(self, layer):
        return layer.visible if hasattr(layer, "visible") else True

    def _on_layer_settings_click(self, button):
        if self.on_open_vis:
            self.on_open_vis(button.tooltip)

    def _on_all_layers_visibility_toggled(self, change):
        for layer in self._host_map.layers[1:]:  # Skip the basemap.
            if hasattr(layer, "visible"):
                layer.visible = change["new"]

    def _on_layer_opacity_changed(self, change, layer):
        if layer in self._host_map.geojson_layers:
            # For non-TileLayer, use layer.style.opacity and layer.style.fillOpacity.
            layer.style.update({"opacity": change["new"], "fillOpacity": change["new"]})
        elif hasattr(layer, "opacity"):
            layer.opacity = change["new"]

    def _on_layer_visibility_changed(self, change, layer):
        if hasattr(layer, "visible"):
            layer.visible = change["new"]

        layer_name = change["owner"].description
        if layer_name not in self._host_map.ee_layers:
            return

        layer_dict = self._host_map.ee_layers[layer_name]
        for attachment_name in ["legend", "colorbar"]:
            attachment = layer_dict.get(attachment_name, None)
            attachment_on_map = attachment in self._host_map.controls
            if change["new"] and not attachment_on_map:
                self._host_map.add(attachment)
            elif not change["new"] and attachment_on_map:
                self._host_map.remove_control(attachment)


class Basemap(ipywidgets.HBox):
    """Widget for selecting a basemap."""

    def __init__(self, host_map, basemaps, value, xyz_services):
        """Creates a widget for selecting a basemap.

        Args:
            host_map (geemap.Map): The map to add the basemap widget to.
            basemaps (list): The list of basemap names to make available for selection.
            value (str): The default value from basemaps to select.
            xyz_services (dict): A dictionary of xyz services for bounds lookup.
        """

        self._host_map = host_map
        if not host_map:
            raise ValueError("Must pass a valid map when creating a basemap widget.")

        self._xyz_services = xyz_services
        self.on_close = None

        self._dropdown = ipywidgets.Dropdown(
            options=list(basemaps),
            value=value,
            layout=ipywidgets.Layout(width="200px"),
        )
        self._dropdown.observe(self._on_dropdown_click, "value")

        close_button = ipywidgets.Button(
            icon="times",
            tooltip="Close the basemap widget",
            button_style="primary",
            layout=ipywidgets.Layout(width="32px"),
        )
        close_button.on_click(self._on_close_click)

        super().__init__([self._dropdown, close_button])

    def _on_dropdown_click(self, change):
        if change["new"]:
            basemap_name = self._dropdown.value
            if basemap_name not in self._host_map.get_layer_names():
                self._host_map.add_basemap(basemap_name)
                if basemap_name in self._xyz_services:
                    if "bounds" in self._xyz_services[basemap_name]:
                        bounds = self._xyz_services[basemap_name]["bounds"]
                        bounds = [
                            bounds[0][1],
                            bounds[0][0],
                            bounds[1][1],
                            bounds[1][0],
                        ]
                        self._host_map.zoom_to_bounds(bounds)

    def _on_close_click(self, _):
        if self.on_close:
            self.on_close()


class LayerEditor(ipywidgets.VBox):
    """Widget for displaying and editing layer visualization properties."""

    def __init__(self, host_map, layer_dict):
        """Initializes a layer editor widget.

        Args:
            host_map (geemap.Map): The geemap.Map object.
            layer_dict (dict): The layer object to edit.
        """

        self.on_close = None

        self._host_map = host_map
        if not host_map:
            raise ValueError(
                f"Must pass a valid map when creating a {self.__class__.__name__} widget."
            )

        layout = ipywidgets.Layout(width="97.5px")
        import_button = ipywidgets.Button(
            description="Import",
            button_style="primary",
            tooltip="Import vis params to notebook",
            layout=layout,
        )
        apply_button = ipywidgets.Button(
            description="Apply", tooltip="Apply vis params to the layer", layout=layout
        )
        close_button = ipywidgets.Button(
            description="Close", tooltip="Close vis params dialog", layout=layout
        )
        import_button.on_click(self._on_import_click)
        apply_button.on_click(self._on_apply_click)
        close_button.on_click(self._on_close_click)

        button_hbox = ipywidgets.HBox([import_button, apply_button, close_button])

        self._embedded_widget = ipywidgets.Label(value="Vis params are uneditable")
        if layer_dict is not None:
            self._ee_object = layer_dict["ee_object"]
            if isinstance(self._ee_object, (ee.Feature, ee.Geometry)):
                self._ee_object = ee.FeatureCollection(self._ee_object)

            self._ee_layer = layer_dict["ee_layer"]
            label = ipywidgets.Label(
                value=f"{self._ee_layer.name} visualization parameters"
            )
            if isinstance(self._ee_object, ee.FeatureCollection):
                self._embedded_widget = _VectorLayerEditor(
                    host_map=host_map, layer_dict=layer_dict
                )
            elif isinstance(self._ee_object, ee.Image):
                self._embedded_widget = _RasterLayerEditor(
                    host_map=host_map, layer_dict=layer_dict
                )

        super().__init__(
            layout=ipywidgets.Layout(
                padding="5px 5px 5px 8px",
                width="330px",
                max_height="300px",
                overflow="auto",
                display="block",
            ),
            children=[label, self._embedded_widget, button_hbox],
        )

    def _on_import_click(self, _):
        self._embedded_widget.on_import_click()

    def _on_apply_click(self, _):
        self._embedded_widget.on_apply_click()

    def _on_close_click(self, _):
        if self.on_close:
            self.on_close()


class _RasterLayerEditor(ipywidgets.VBox):
    """Widget for displaying and editing layer visualization properties for raster layers."""

    def __init__(self, host_map, layer_dict):
        """Initializes a raster layer editor widget.

        Args:
            host_map (geemap.Map): The geemap.Map object.
            layer_dict (dict): The layer object to edit.
        """
        self._host_map = host_map
        self._layer_dict = layer_dict

        self._ee_object = layer_dict["ee_object"]
        self._ee_layer = layer_dict["ee_layer"]
        self._vis_params = layer_dict["vis_params"]

        self._layer_name = self._ee_layer.name
        self._layer_opacity = self._ee_layer.opacity

        self._min_value = 0
        self._max_value = 100
        self._sel_bands = None
        self._layer_palette = []
        self._layer_gamma = 1
        self._left_value = 0
        self._right_value = 10000

        band_names = self._ee_object.bandNames().getInfo()
        self._band_count = len(band_names)

        if "min" in self._vis_params.keys():
            self._min_value = self._vis_params["min"]
            if self._min_value < self._left_value:
                self._left_value = self._min_value - self._max_value
        if "max" in self._vis_params.keys():
            self._max_value = self._vis_params["max"]
            self._right_value = 2 * self._max_value
        if "gamma" in self._vis_params.keys():
            self._layer_gamma = self._vis_params["gamma"]
        if "bands" in self._vis_params.keys():
            self._sel_bands = self._vis_params["bands"]
        if "palette" in self._vis_params.keys():
            self._layer_palette = [
                color.replace("#", "") for color in list(self._vis_params["palette"])
            ]

        # ipywidgets doesn't support horizontal radio buttons
        # (https://github.com/jupyter-widgets/ipywidgets/issues/1247). Instead,
        # use two individual radio buttons with some hackery.
        self._greyscale_radio_button = ipywidgets.RadioButtons(
            options=["1 band (Grayscale)"],
            layout={"width": "max-content", "margin": "0 15px 0 0"},
        )
        self._rgb_radio_button = ipywidgets.RadioButtons(
            options=["3 bands (RGB)"], layout={"width": "max-content"}
        )
        self._greyscale_radio_button.index = None
        self._rgb_radio_button.index = None

        band_dropdown_layout = ipywidgets.Layout(width="98px")
        self._band_1_dropdown = ipywidgets.Dropdown(
            options=band_names, value=band_names[0], layout=band_dropdown_layout
        )
        self._band_2_dropdown = ipywidgets.Dropdown(
            options=band_names, value=band_names[0], layout=band_dropdown_layout
        )
        self._band_3_dropdown = ipywidgets.Dropdown(
            options=band_names, value=band_names[0], layout=band_dropdown_layout
        )
        self._bands_hbox = ipywidgets.HBox(layout=ipywidgets.Layout(margin="0 0 6px 0"))

        self._color_picker = ipywidgets.ColorPicker(
            concise=False,
            value="#000000",
            layout=ipywidgets.Layout(width="116px"),
            style={"description_width": "initial"},
        )

        self._add_color_button = ipywidgets.Button(
            icon="plus",
            tooltip="Add a hex color string to the palette",
            layout=ipywidgets.Layout(width="32px"),
        )
        self._del_color_button = ipywidgets.Button(
            icon="minus",
            tooltip="Remove a hex color string from the palette",
            layout=ipywidgets.Layout(width="32px"),
        )
        self._reset_color_button = ipywidgets.Button(
            icon="eraser",
            tooltip="Remove all color strings from the palette",
            layout=ipywidgets.Layout(width="34px"),
        )
        self._add_color_button.on_click(self._add_color_clicked)
        self._del_color_button.on_click(self._del_color_clicked)
        self._reset_color_button.on_click(self._reset_color_clicked)

        self._classes_dropdown = ipywidgets.Dropdown(
            options=["Any"] + [str(i) for i in range(3, 13)],
            description="Classes:",
            layout=ipywidgets.Layout(width="115px"),
            style={"description_width": "initial"},
        )
        self._classes_dropdown.observe(self._classes_changed, "value")

        self._colormap_dropdown = ipywidgets.Dropdown(
            options=self._get_colormaps(),
            value=None,
            description="Colormap:",
            layout=ipywidgets.Layout(width="181px"),
            style={"description_width": "initial"},
        )
        self._colormap_dropdown.observe(self._colormap_changed, "value")

        self._palette_label = ipywidgets.Text(
            value=", ".join(self._layer_palette),
            placeholder="List of hex color code (RRGGBB)",
            description="Palette:",
            tooltip="Enter a list of hex color code (RRGGBB)",
            layout=ipywidgets.Layout(width="300px"),
            style={"description_width": "initial"},
        )

        self._value_range_slider = ipywidgets.FloatRangeSlider(
            value=[self._min_value, self._max_value],
            min=self._left_value,
            max=self._right_value,
            step=0.1,
            description="Range:",
            disabled=False,
            continuous_update=False,
            readout=True,
            readout_format=".1f",
            layout=ipywidgets.Layout(width="300px"),
            style={"description_width": "45px"},
        )

        self._opacity_slider = ipywidgets.FloatSlider(
            value=self._layer_opacity,
            min=0,
            max=1,
            step=0.01,
            description="Opacity:",
            continuous_update=False,
            readout=True,
            readout_format=".2f",
            layout=ipywidgets.Layout(width="320px"),
            style={"description_width": "50px"},
        )

        self._gamma_slider = ipywidgets.FloatSlider(
            value=self._layer_gamma,
            min=0.1,
            max=10,
            step=0.01,
            description="Gamma:",
            continuous_update=False,
            readout=True,
            readout_format=".2f",
            layout=ipywidgets.Layout(width="320px"),
            style={"description_width": "50px"},
        )

        self._legend_checkbox = ipywidgets.Checkbox(
            value=False,
            description="Legend",
            indent=False,
            layout=ipywidgets.Layout(width="70px"),
        )

        self._linear_checkbox = ipywidgets.Checkbox(
            value=True,
            description="Linear colormap",
            indent=False,
            layout=ipywidgets.Layout(width="150px"),
        )
        self._step_checkbox = ipywidgets.Checkbox(
            value=False,
            description="Step colormap",
            indent=False,
            layout=ipywidgets.Layout(width="140px"),
        )
        self._linear_checkbox.observe(self._linear_checkbox_changed, "value")
        self._step_checkbox.observe(self._step_checkbox_changed, "value")

        self._legend_title_label = ipywidgets.Text(
            value="Legend",
            description="Legend title:",
            tooltip="Enter a title for the legend",
            layout=ipywidgets.Layout(width="300px"),
            style={"description_width": "initial"},
        )

        self._legend_labels_label = ipywidgets.Text(
            value="Class 1, Class 2, Class 3",
            description="Legend labels:",
            tooltip="Enter a a list of labels for the legend",
            layout=ipywidgets.Layout(width="300px"),
            style={"description_width": "initial"},
        )

        self._colormap_hbox = ipywidgets.HBox(
            [self._linear_checkbox, self._step_checkbox]
        )
        self._legend_vbox = ipywidgets.VBox()

        self._colorbar_output = ipywidgets.Output(
            layout=ipywidgets.Layout(height="60px", max_width="300px")
        )

        self._legend_checkbox.observe(self._legend_checkbox_changed, "value")

        children = []
        if self._band_count < 3:
            self._greyscale_radio_button.index = 0
            self._band_1_dropdown.layout.width = "300px"
            self._bands_hbox.children = [self._band_1_dropdown]
            children = self._get_tool_layout(grayscale=True)
            self._legend_checkbox.value = False

            if len(self._palette_label.value) > 0 and "," in self._palette_label.value:
                colors = common.to_hex_colors(
                    [color.strip() for color in self._palette_label.value.split(",")]
                )
                self._render_colorbar(colors)
        else:
            self._rgb_radio_button.index = 0
            if (sel_bands is None) or (len(sel_bands) < 2):
                sel_bands = band_names[0:3]
            self._band_1_dropdown.value = sel_bands[0]
            self._band_2_dropdown.value = sel_bands[1]
            self._band_3_dropdown.value = sel_bands[2]
            self._bands_hbox.children = [
                self._band_1_dropdown,
                self._band_2_dropdown,
                self._band_3_dropdown,
            ]
            children = self._get_tool_layout(grayscale=False)

        self._greyscale_radio_button.observe(self._radio1_observer, names=["value"])
        self._rgb_radio_button.observe(self._radio2_observer, names=["value"])

        super().__init__(children=children)

    def _get_tool_layout(self, grayscale):
        return [
            ipywidgets.HBox([self._greyscale_radio_button, self._rgb_radio_button]),
            self._bands_hbox,
            self._value_range_slider,
            self._opacity_slider,
            self._gamma_slider,
        ] + (
            [
                ipywidgets.HBox([self._classes_dropdown, self._colormap_dropdown]),
                self._palette_label,
                self._colorbar_output,
                ipywidgets.HBox(
                    [
                        self._legend_checkbox,
                        self._color_picker,
                        self._add_color_button,
                        self._del_color_button,
                        self._reset_color_button,
                    ]
                ),
                self._legend_vbox,
            ]
            if grayscale
            else []
        )

    def _get_colormaps(self):
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        colormap_options = pyplot.colormaps()
        colormap_options.sort()
        return colormap_options

    def _render_colorbar(self, colors):
        import matplotlib  # pylint: disable=import-outside-toplevel
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        colors = common.to_hex_colors(colors)

        _, ax = pyplot.subplots(figsize=(4, 0.3))
        cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
            "custom", colors, N=256
        )
        norm = matplotlib.colors.Normalize(
            vmin=self._value_range_slider.value[0],
            vmax=self._value_range_slider.value[1],
        )
        matplotlib.colorbar.ColorbarBase(
            ax, norm=norm, cmap=cmap, orientation="horizontal"
        )

        self._palette_label.value = ", ".join(colors)

        self._colorbar_output.clear_output()
        with self._colorbar_output:
            pyplot.show()

    def _classes_changed(self, change):
        import matplotlib  # pylint: disable=import-outside-toplevel
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        if not change["new"]:
            return

        selected = change["owner"].value
        if self._colormap_dropdown.value is not None:
            n_class = None
            if selected != "Any":
                n_class = int(self._classes_dropdown.value)

            colors = pyplot.cm.get_cmap(self._colormap_dropdown.value, n_class)
            cmap_colors = [
                matplotlib.colors.rgb2hex(colors(i))[1:] for i in range(colors.N)
            ]
            self._render_colorbar(cmap_colors)

            if len(self._palette_label.value) > 0 and "," in self._palette_label.value:
                labels = [
                    f"Class {i+1}"
                    for i in range(len(self._palette_label.value.split(",")))
                ]
                self._legend_labels_label.value = ", ".join(labels)

    def _add_color_clicked(self, _):
        if self._color_picker.value is not None:
            if len(self._palette_label.value) == 0:
                self._palette_label.value = self._color_picker.value[1:]
            else:
                self._palette_label.value += ", " + self._color_picker.value[1:]

    def _del_color_clicked(self, _):
        if "," in self._palette_label.value:
            items = [item.strip() for item in self._palette_label.value.split(",")]
            self._palette_label.value = ", ".join(items[:-1])
        else:
            self._palette_label.value = ""

    def _reset_color_clicked(self, _):
        self._palette_label.value = ""

    def _linear_checkbox_changed(self, change):
        if change["new"]:
            self._step_checkbox.value = False
            self._legend_vbox.children = [self._colormap_hbox]
        else:
            self._step_checkbox.value = True

    def _step_checkbox_changed(self, change):
        if change["new"]:
            self._linear_checkbox.value = False
            if len(self._layer_palette) > 0:
                self._legend_labels_label.value = ",".join(
                    ["Class " + str(i) for i in range(1, len(self._layer_palette) + 1)]
                )
            self._legend_vbox.children = [
                self._colormap_hbox,
                self._legend_title_label,
                self._legend_labels_label,
            ]
        else:
            self._linear_checkbox.value = True

    def _colormap_changed(self, change):
        import matplotlib  # pylint: disable=import-outside-toplevel
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        if change["new"]:
            n_class = None
            if self._classes_dropdown.value != "Any":
                n_class = int(self._classes_dropdown.value)

            colors = pyplot.cm.get_cmap(self._colormap_dropdown.value, n_class)
            cmap_colors = [
                matplotlib.colors.rgb2hex(colors(i))[1:] for i in range(colors.N)
            ]
            self._render_colorbar(cmap_colors)

            if len(self._palette_label.value) > 0 and "," in self._palette_label.value:
                labels = [
                    f"Class {i+1}"
                    for i in range(len(self._palette_label.value.split(",")))
                ]
                self._legend_labels_label.value = ", ".join(labels)

    def on_import_click(self):
        vis = {}
        if self._greyscale_radio_button.index == 0:
            vis["bands"] = [self._band_1_dropdown.value]
            if len(self._palette_label.value) > 0:
                vis["palette"] = self._palette_label.value.split(",")
        else:
            vis["bands"] = [
                self._band_1_dropdown.value,
                self._band_2_dropdown.value,
                self._band_3_dropdown.value,
            ]

        vis["min"] = self._value_range_slider.value[0]
        vis["max"] = self._value_range_slider.value[1]
        vis["opacity"] = self._opacity_slider.value
        vis["gamma"] = self._gamma_slider.value

        common.create_code_cell(f"vis_params = {str(vis)}")

    def on_apply_click(self):
        vis = {}
        if self._greyscale_radio_button.index == 0:
            vis["bands"] = [self._band_1_dropdown.value]
            if len(self._palette_label.value) > 0:
                vis["palette"] = [
                    c.strip() for c in self._palette_label.value.split(",")
                ]
        else:
            vis["bands"] = [
                self._band_1_dropdown.value,
                self._band_2_dropdown.value,
                self._band_3_dropdown.value,
            ]
            vis["gamma"] = self._gamma_slider.value

        vis["min"] = self._value_range_slider.value[0]
        vis["max"] = self._value_range_slider.value[1]

        self._host_map.add_layer(
            self._ee_object, vis, self._layer_name, True, self._opacity_slider.value
        )
        self._ee_layer.visible = False

        def _remove_control(key):
            if widget := self._layer_dict.get(key, None):
                if widget in self._host_map.controls:
                    self._host_map.remove(widget)
                del self._layer_dict[key]

        if self._legend_checkbox.value:
            _remove_control("colorbar")
            if self._linear_checkbox.value:
                _remove_control("legend")

                if (
                    len(self._palette_label.value) > 0
                    and "," in self._palette_label.value
                ):
                    colors = common.to_hex_colors(
                        [
                            color.strip()
                            for color in self._palette_label.value.split(",")
                        ]
                    )

                    if hasattr(self._host_map, "colorbar"):
                        self._host_map.add_colorbar(
                            vis_params={
                                "palette": colors,
                                "min": self._value_range_slider.value[0],
                                "max": self._value_range_slider.value[1],
                            },
                            layer_name=self._layer_name,
                        )
            elif self._step_checkbox.value:
                if (
                    len(self._palette_label.value) > 0
                    and "," in self._palette_label.value
                ):
                    colors = common.to_hex_colors(
                        [
                            color.strip()
                            for color in self._palette_label.value.split(",")
                        ]
                    )
                    labels = [
                        label.strip()
                        for label in self._legend_labels_label.value.split(",")
                    ]

                    if hasattr(self._host_map, "add_legend"):
                        self._host_map.add_legend(
                            title=self._legend_title_label.value,
                            legend_keys=labels,
                            legend_colors=colors,
                            layer_name=self._layer_name,
                        )
        else:
            if self._greyscale_radio_button.index == 0 and "palette" in vis:
                self._render_colorbar(vis["palette"])
                _remove_control("colorbar")
                _remove_control("legend")

    def _legend_checkbox_changed(self, change):
        if change["new"]:
            self._linear_checkbox.value = True
            self._legend_vbox.children = [
                ipywidgets.HBox([self._linear_checkbox, self._step_checkbox]),
            ]
        else:
            self._legend_vbox.children = []

    def _radio1_observer(self, _):
        self._rgb_radio_button.unobserve(self._radio2_observer, names=["value"])
        self._rgb_radio_button.index = None
        self._rgb_radio_button.observe(self._radio2_observer, names=["value"])
        self._band_1_dropdown.layout.width = "300px"
        self._bands_hbox.children = [self._band_1_dropdown]
        self._palette_label.value = ", ".join(self._layer_palette)
        self._palette_label.disabled = False
        self._color_picker.disabled = False
        self._add_color_button.disabled = False
        self._del_color_button.disabled = False
        self._reset_color_button.disabled = False
        self.children = self._get_tool_layout(grayscale=True)

        if len(self._palette_label.value) > 0 and "," in self._palette_label.value:
            colors = [color.strip() for color in self._palette_label.value.split(",")]
            self._render_colorbar(colors)

    def _radio2_observer(self, _):
        dropdown_width = "98px"
        self._greyscale_radio_button.unobserve(self._radio1_observer, names=["value"])
        self._greyscale_radio_button.index = None
        self._greyscale_radio_button.observe(self._radio1_observer, names=["value"])
        self._band_1_dropdown.layout.width = dropdown_width
        self._bands_hbox.children = [
            self._band_1_dropdown,
            self._band_2_dropdown,
            self._band_3_dropdown,
        ]
        self._palette_label.value = ""
        self._palette_label.disabled = True
        self._color_picker.disabled = True
        self._add_color_button.disabled = True
        self._del_color_button.disabled = True
        self._reset_color_button.disabled = True
        self.children = self._get_tool_layout(grayscale=False)
        self._colorbar_output.clear_output()


class _VectorLayerEditor(ipywidgets.VBox):
    """Widget for displaying and editing layer visualization properties."""

    _POINT_SHAPES = [
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

    @property
    def _layer_name(self):
        return self._ee_layer.name

    @property
    def _layer_opacity(self):
        return self._ee_layer.opacity

    def __init__(self, host_map, layer_dict):
        """Initializes a layer manager widget.

        Args:
            host_map (geemap.Map): The geemap.Map object.
        """

        self._host_map = host_map
        if not host_map:
            raise ValueError("Must pass a valid map when creating a layer manager.")

        self._layer_dict = layer_dict

        self._ee_object = layer_dict["ee_object"]
        if isinstance(self._ee_object, (ee.Feature, ee.Geometry)):
            self._ee_object = ee.FeatureCollection(self._ee_object)

        self._ee_layer = layer_dict["ee_layer"]

        self._new_layer_name = ipywidgets.Text(
            value=f"{self._layer_name} style",
            description="New layer name:",
            style={"description_width": "initial"},
        )

        self._color_picker = ipywidgets.ColorPicker(
            concise=False,
            value="#000000",
            description="Color:",
            layout=ipywidgets.Layout(width="140px"),
            style={"description_width": "initial"},
        )

        self._color_opacity_slider = ipywidgets.FloatSlider(
            value=self._layer_opacity,
            min=0,
            max=1,
            step=0.01,
            description="Opacity:",
            continuous_update=True,
            readout=False,
            layout=ipywidgets.Layout(width="130px"),
            style={"description_width": "50px"},
        )
        self._color_opacity_slider.observe(self._color_opacity_change, names="value")

        self._color_opacity_label = ipywidgets.Label(
            style={"description_width": "initial"},
            layout=ipywidgets.Layout(padding="0px"),
        )

        self._point_size_label = ipywidgets.IntText(
            value=3,
            description="Point size:",
            layout=ipywidgets.Layout(width="110px"),
            style={"description_width": "initial"},
        )

        self._point_shape_dropdown = ipywidgets.Dropdown(
            options=self._POINT_SHAPES,
            value="circle",
            description="Point shape:",
            layout=ipywidgets.Layout(width="185px"),
            style={"description_width": "initial"},
        )

        self._line_width_label = ipywidgets.IntText(
            value=2,
            description="Line width:",
            layout=ipywidgets.Layout(width="110px"),
            style={"description_width": "initial"},
        )

        self._line_type_label = ipywidgets.Dropdown(
            options=["solid", "dotted", "dashed"],
            value="solid",
            description="Line type:",
            layout=ipywidgets.Layout(width="185px"),
            style={"description_width": "initial"},
        )

        self._fill_color_picker = ipywidgets.ColorPicker(
            concise=False,
            value="#000000",
            description="Fill Color:",
            layout=ipywidgets.Layout(width="160px"),
            style={"description_width": "initial"},
        )

        self._fill_color_opacity_slider = ipywidgets.FloatSlider(
            value=0.66,
            min=0,
            max=1,
            step=0.01,
            description="Opacity:",
            continuous_update=True,
            readout=False,
            layout=ipywidgets.Layout(width="110px"),
            style={"description_width": "50px"},
        )
        self._fill_color_opacity_slider.observe(
            self._fill_color_opacity_change, names="value"
        )

        self._fill_color_opacity_label = ipywidgets.Label(
            style={"description_width": "initial"},
            layout=ipywidgets.Layout(padding="0px"),
        )

        self._color_picker = ipywidgets.ColorPicker(
            concise=False,
            value="#000000",
            layout=ipywidgets.Layout(width="116px"),
            style={"description_width": "initial"},
        )

        self._add_color = ipywidgets.Button(
            icon="plus",
            tooltip="Add a hex color string to the palette",
            layout=ipywidgets.Layout(width="32px"),
        )
        self._del_color = ipywidgets.Button(
            icon="minus",
            tooltip="Remove a hex color string from the palette",
            layout=ipywidgets.Layout(width="32px"),
        )
        self._reset_color = ipywidgets.Button(
            icon="eraser",
            tooltip="Remove all color strings from the palette",
            layout=ipywidgets.Layout(width="34px"),
        )
        self._add_color.on_click(self._add_color_clicked)
        self._del_color.on_click(self._del_color_clicked)
        self._reset_color.on_click(self._reset_color_clicked)

        self._palette_label = ipywidgets.Text(
            value="",
            placeholder="List of hex code (RRGGBB) separated by comma",
            description="Palette:",
            tooltip="Enter a list of hex code (RRGGBB) separated by comma",
            layout=ipywidgets.Layout(width="300px"),
            style={"description_width": "initial"},
        )

        self._legend_title_label = ipywidgets.Text(
            value="Legend",
            description="Legend title:",
            tooltip="Enter a title for the legend",
            layout=ipywidgets.Layout(width="300px"),
            style={"description_width": "initial"},
        )

        self._legend_labels_label = ipywidgets.Text(
            value="Labels",
            description="Legend labels:",
            tooltip="Enter a a list of labels for the legend",
            layout=ipywidgets.Layout(width="300px"),
            style={"description_width": "initial"},
        )

        self._field_dropdown = ipywidgets.Dropdown(
            options=[],
            value=None,
            description="Field:",
            layout=ipywidgets.Layout(width="140px"),
            style={"description_width": "initial"},
        )
        self._field_dropdown.observe(self._field_changed, "value")

        self._field_values_dropdown = ipywidgets.Dropdown(
            options=[],
            value=None,
            description="Values:",
            layout=ipywidgets.Layout(width="156px"),
            style={"description_width": "initial"},
        )

        self._classes_dropdown = ipywidgets.Dropdown(
            options=["Any"] + [str(i) for i in range(3, 13)],
            description="Classes:",
            layout=ipywidgets.Layout(width="115px"),
            style={"description_width": "initial"},
        )
        self._colormap_dropdown = ipywidgets.Dropdown(
            options=["viridis"],
            value="viridis",
            description="Colormap:",
            layout=ipywidgets.Layout(width="181px"),
            style={"description_width": "initial"},
        )
        self._classes_dropdown.observe(self._classes_changed, "value")
        self._colormap_dropdown.observe(self._colormap_changed, "value")

        self._style_chk = ipywidgets.Checkbox(
            value=False,
            description="Style by attribute",
            indent=False,
            layout=ipywidgets.Layout(width="140px"),
        )
        self._legend_checkbox = ipywidgets.Checkbox(
            value=False,
            description="Legend",
            indent=False,
            layout=ipywidgets.Layout(width="70px"),
        )
        self._style_chk.observe(self._style_chk_changed, "value")
        self._legend_checkbox.observe(self._legend_chk_changed, "value")

        self._compute_label = ipywidgets.Label(value="")

        self._style_vbox = ipywidgets.VBox(
            [ipywidgets.HBox([self._style_chk, self._compute_label])]
        )

        self._colorbar_output = ipywidgets.Output(
            layout=ipywidgets.Layout(height="60px", width="100%")
        )

        is_point = common.geometry_type(self._ee_object) in ["Point", "MultiPoint"]
        self._point_size_label.disabled = not is_point
        self._point_shape_dropdown.disabled = not is_point

        super().__init__(
            children=[
                self._new_layer_name,
                ipywidgets.HBox(
                    [
                        self._color_picker,
                        self._color_opacity_slider,
                        self._color_opacity_label,
                    ]
                ),
                ipywidgets.HBox([self._point_size_label, self._point_shape_dropdown]),
                ipywidgets.HBox([self._line_width_label, self._line_type_label]),
                ipywidgets.HBox(
                    [
                        self._fill_color_picker,
                        self._fill_color_opacity_slider,
                        self._fill_color_opacity_label,
                    ]
                ),
                self._style_vbox,
            ],
        )

    def _get_vis_params(self):
        vis = {}
        vis["color"] = self._color_picker.value[1:] + str(
            hex(int(self._color_opacity_slider.value * 255))
        )[2:].zfill(2)
        if common.geometry_type(self._ee_object) in ["Point", "MultiPoint"]:
            vis["pointSize"] = self._point_size_label.value
            vis["pointShape"] = self._point_shape_dropdown.value
        vis["width"] = self._line_width_label.value
        vis["lineType"] = self._line_type_label.value
        vis["fillColor"] = self._fill_color_picker.value[1:] + str(
            hex(int(self._fill_color_opacity_slider.value * 255))
        )[2:].zfill(2)

        return vis

    def on_apply_click(self):
        self._compute_label.value = "Computing ..."

        if self._new_layer_name.value in self._host_map.ee_layers:
            old_layer = self._new_layer_name.value
            self._host_map.remove(old_layer)

        if not self._style_chk.value:
            vis = self._get_vis_params()
            self._host_map.add_layer(
                self._ee_object.style(**vis), {}, self._new_layer_name.value
            )
            self._ee_layer.visible = False

        elif (
            self._style_chk.value
            and len(self._palette_label.value) > 0
            and "," in self._palette_label.value
        ):
            try:
                colors = ee.List(
                    [
                        color.strip()
                        + str(hex(int(self._fill_color_opacity_slider.value * 255)))[
                            2:
                        ].zfill(2)
                        for color in self._palette_label.value.split(",")
                    ]
                )
                arr = (
                    self._ee_object.aggregate_array(self._field_dropdown.value)
                    .distinct()
                    .sort()
                )
                fc = self._ee_object.map(
                    lambda f: f.set(
                        {"styleIndex": arr.indexOf(f.get(self._field_dropdown.value))}
                    )
                )
                step = arr.size().divide(colors.size()).ceil()
                fc = fc.map(
                    lambda f: f.set(
                        {
                            "style": {
                                "color": self._color_picker.value[1:]
                                + str(hex(int(self._color_opacity_slider.value * 255)))[
                                    2:
                                ].zfill(2),
                                "pointSize": self._point_size_label.value,
                                "pointShape": self._point_shape_dropdown.value,
                                "width": self._line_width_label.value,
                                "lineType": self._line_type_label.value,
                                "fillColor": colors.get(
                                    ee.Number(
                                        ee.Number(f.get("styleIndex")).divide(step)
                                    ).floor()
                                ),
                            }
                        }
                    )
                )

                self._host_map.add_layer(
                    fc.style(**{"styleProperty": "style"}),
                    {},
                    f"{self._new_layer_name.value}",
                )

                if (
                    len(self._palette_label.value)
                    and self._legend_checkbox.value
                    and len(self._legend_labels_label.value) > 0
                    and hasattr(self._host_map, "add_legend")
                ):
                    legend_colors = [
                        color.strip() for color in self._palette_label.value.split(",")
                    ]
                    legend_keys = [
                        label.strip()
                        for label in self._legend_labels_label.value.split(",")
                    ]

                    if hasattr(self._host_map, "add_legend"):
                        self._host_map.add_legend(
                            title=self._legend_title_label.value,
                            legend_keys=legend_keys,
                            legend_colors=legend_colors,
                            layer_name=self._new_layer_name.value,
                        )
            except Exception as exc:
                self._compute_label.value = "Error: " + str(exc)

            self._ee_layer.visible = False
            self._compute_label.value = ""

    def _render_colorbar(self, colors):
        import matplotlib  # pylint: disable=import-outside-toplevel
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        colors = common.to_hex_colors(colors)

        _, ax = pyplot.subplots(figsize=(3, 0.3))
        cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
            "custom", colors, N=256
        )
        norm = matplotlib.colors.Normalize(vmin=0, vmax=1)
        matplotlib.colorbar.ColorbarBase(
            ax, norm=norm, cmap=cmap, orientation="horizontal"
        )

        self._palette_label.value = ", ".join(colors)
        self._colorbar_output.clear_output()
        with self._colorbar_output:
            pyplot.show()

    def _classes_changed(self, change):
        import matplotlib  # pylint: disable=import-outside-toplevel
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        if change["new"]:
            selected = change["owner"].value
            if self._colormap_dropdown.value is not None:
                n_class = None
                if selected != "Any":
                    n_class = int(self._classes_dropdown.value)

                colors = pyplot.cm.get_cmap(self._colormap_dropdown.value, n_class)
                cmap_colors = [
                    matplotlib.colors.rgb2hex(colors(i))[1:] for i in range(colors.N)
                ]
                self._render_colorbar(cmap_colors)

                if (
                    len(self._palette_label.value) > 0
                    and "," in self._palette_label.value
                ):
                    labels = [
                        f"Class {i+1}"
                        for i in range(len(self._palette_label.value.split(",")))
                    ]
                    self._legend_labels_label.value = ", ".join(labels)

    def _colormap_changed(self, change):
        import matplotlib  # pylint: disable=import-outside-toplevel
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        if change["new"]:
            n_class = None
            if self._classes_dropdown.value != "Any":
                n_class = int(self._classes_dropdown.value)

            colors = pyplot.cm.get_cmap(self._colormap_dropdown.value, n_class)
            cmap_colors = [
                matplotlib.colors.rgb2hex(colors(i))[1:] for i in range(colors.N)
            ]
            self._render_colorbar(cmap_colors)

            if len(self._palette_label.value) > 0 and "," in self._palette_label.value:
                labels = [
                    f"Class {i+1}"
                    for i in range(len(self._palette_label.value.split(",")))
                ]
                self._legend_labels_label.value = ", ".join(labels)

    def _fill_color_opacity_change(self, change):
        self._fill_color_opacity_label.value = str(change["new"])

    def _color_opacity_change(self, change):
        self._color_opacity_label.value = str(change["new"])

    def _add_color_clicked(self, _):
        if self._color_picker.value is not None:
            if len(self._palette_label.value) == 0:
                self._palette_label.value = self._color_picker.value[1:]
            else:
                self._palette_label.value += ", " + self._color_picker.value[1:]

    def _del_color_clicked(self, _):
        if "," in self._palette_label.value:
            items = [item.strip() for item in self._palette_label.value.split(",")]
            self._palette_label.value = ", ".join(items[:-1])
        else:
            self._palette_label.value = ""

    def _reset_color_clicked(self, _):
        self._palette_label.value = ""

    def _style_chk_changed(self, change):
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        if change["new"]:
            self._colorbar_output.clear_output()

            self._fill_color_picker.disabled = True
            colormap_options = pyplot.colormaps()
            colormap_options.sort()
            self._colormap_dropdown.options = colormap_options
            self._colormap_dropdown.value = "viridis"
            self._style_vbox.children = [
                ipywidgets.HBox([self._style_chk, self._compute_label]),
                ipywidgets.HBox([self._field_dropdown, self._field_values_dropdown]),
                ipywidgets.HBox([self._classes_dropdown, self._colormap_dropdown]),
                self._palette_label,
                self._colorbar_output,
                ipywidgets.HBox(
                    [
                        self._legend_checkbox,
                        self._color_picker,
                        self._add_color,
                        self._del_color,
                        self._reset_color,
                    ]
                ),
            ]
            self._compute_label.value = "Computing ..."

            self._field_dropdown.options = (
                ee.Feature(self._ee_object.first()).propertyNames().getInfo()
            )
            self._compute_label.value = ""
            self._classes_dropdown.value = "Any"
            self._legend_checkbox.value = False

        else:
            self._fill_color_picker.disabled = False
            self._style_vbox.children = [
                ipywidgets.HBox([self._style_chk, self._compute_label])
            ]
            self._compute_label.value = ""
            self._colorbar_output.clear_output()

    def _legend_chk_changed(self, change):
        if change["new"]:
            self._style_vbox.children = list(self._style_vbox.children) + [
                ipywidgets.VBox([self._legend_title_label, self._legend_labels_label])
            ]

            if len(self._palette_label.value) > 0 and "," in self._palette_label.value:
                labels = [
                    f"Class {i+1}"
                    for i in range(len(self._palette_label.value.split(",")))
                ]
                self._legend_labels_label.value = ", ".join(labels)

        else:
            self._style_vbox.children = [
                ipywidgets.HBox([self._style_chk, self._compute_label]),
                ipywidgets.HBox([self._field_dropdown, self._field_values_dropdown]),
                ipywidgets.HBox([self._classes_dropdown, self._colormap_dropdown]),
                self._palette_label,
                ipywidgets.HBox(
                    [
                        self._legend_checkbox,
                        self._color_picker,
                        self._add_color,
                        self._del_color,
                        self._reset_color,
                    ]
                ),
            ]

    def _field_changed(self, change):
        if change["new"]:
            self._compute_label.value = "Computing ..."
            options = self._ee_object.aggregate_array(
                self._field_dropdown.value
            ).getInfo()
            if options is not None:
                options = list(set(options))
                options.sort()

            self._field_values_dropdown.options = options
            self._compute_label.value = ""

    def on_import_click(self):
        vis = self._get_vis_params()
        common.create_code_cell(f"vis_params = {str(vis)}")
