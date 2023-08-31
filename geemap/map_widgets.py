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
        for layer in self._host_map.layers[1:]:
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
        for layer in self._host_map.layers:
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
