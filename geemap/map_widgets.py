"""Various ipywidgets that can be added to a map."""

from collections.abc import Callable
import enum
import functools
import importlib.resources
import json
import os
import pathlib
import re
from typing import Any

import IPython
from IPython.display import HTML, display

import anywidget
import ee
import ipyleaflet
import ipywidgets
import matplotlib
from matplotlib import pyplot
import numpy
import traitlets

from . import common
from . import conversion
from . import coreutils


class TypedTuple(traitlets.Container):
    """A trait for a tuple of any length with type-checked elements."""

    klass = tuple
    _cast_types = (list,)


def _set_css_in_cell_output(info: Any) -> None:
    """Sets CSS styles in the cell output for different themes.

    Args:
        info: Information passed to the function (unused).

    Returns:
        None
    """
    del info  # Unused.
    display(
        HTML(
            """
            <style>
                .geemap-dark {
                    --jp-widgets-color: white;
                    --jp-widgets-label-color: white;
                    --jp-ui-font-color1: white;
                    --jp-layout-color2: #454545;
                    background-color: #383838;
                }

                .geemap-dark .jupyter-button {
                    --jp-layout-color3: #383838;
                }

                .geemap-colab {
                    background-color: var(--colab-primary-surface-color, white);
                }

                .geemap-colab .jupyter-button {
                    --jp-layout-color3: var(--colab-primary-surface-color, white);
                }
            </style>
            """
        )
    )


try:
    IPython.get_ipython().events.register("pre_run_cell", _set_css_in_cell_output)
except AttributeError:
    pass


class Theme:
    """Applies dynamic theme in Colab, otherwise light."""

    current_theme = "colab" if coreutils.in_colab_shell() else "light"

    @staticmethod
    def apply(cls: Any) -> Any:
        """Applies the theme to the given class.

        Args:
            cls: The class to which the theme will be applied.

        Returns:
            The class with the applied theme.
        """
        original_init = cls.__init__

        @functools.wraps(cls.__init__)
        def wrapper(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self.add_class(f"geemap-{Theme.current_theme}")

        cls.__init__ = wrapper
        return cls


@Theme.apply
class Colorbar(ipywidgets.Output):
    """A matplotlib colorbar widget that can be added to the map."""

    def __init__(
        self,
        vis_params: dict[str, Any] | list | tuple | None = None,
        cmap: str = "gray",
        discrete: bool = False,
        label: str | None = None,
        orientation: str = "horizontal",
        transparent_bg: bool = False,
        font_size: int = 9,
        axis_off: bool = False,
        max_width: str | None = None,
        **kwargs,
    ):
        """Add a matplotlib colorbar to the map.

        Args:
            vis_params: Visualization parameters as a dictionary. See
                https://developers.google.com/earth-engine/guides/image_visualization # noqa
                for options.
            cmap: Matplotlib colormap. Defaults to "gray". See
                https://matplotlib.org/3.3.4/tutorials/colors/colormaps.html#sphx-glr-tutorials-colors-colormaps-py # noqa
                for options.
            discrete: Whether to create a discrete colorbar.
                Defaults to False.
            label: Label for the colorbar. Defaults to None.
            orientation: Orientation of the colorbar, such as "vertical" and
                "horizontal". Defaults to "horizontal".
            transparent_bg: Whether to use transparent background. Defaults to False.
            font_size: Font size for the colorbar. Defaults to 9.
            axis_off: Whether to turn off the axis. Defaults to False.
            max_width: Maximum width of the colorbar in pixels.  Defaults to None.

        Raises:
            TypeError: If the vis_params is not a dictionary.
            ValueError: If the orientation is not either horizontal or vertical.
            ValueError: If the provided min value is not convertible to float.
            ValueError: If the provided max value is not convertible to float.
            ValueError: If the provided opacity value is not convertible to float.
            ValueError: If cmap or palette is not provided.
        """
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
        try:
            vmin = float(vmin)
        except ValueError as err:
            raise ValueError("The provided min value must be scalar type.")

        vmax = vis_params.get("max", kwargs.pop("vmax", 1))
        try:
            vmax = float(vmax)
        except ValueError as err:
            raise ValueError("The provided max value must be scalar type.")

        alpha = vis_params.get("opacity", kwargs.pop("alpha", 1))
        try:
            alpha = float(alpha)
        except ValueError as err:
            raise ValueError("opacity or alpha value must be scalar type.")

        if "palette" in vis_params.keys():
            hexcodes = coreutils.to_hex_colors(
                coreutils.check_cmap(vis_params["palette"])
            )
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

    def _get_dimensions(
        self, orientation: str, kwargs: dict[str, Any]
    ) -> tuple[float, float]:
        """Get the dimensions of the colorbar based on orientation.

        Args:
            orientation: Orientation of the colorbar.
            kwargs: Additional keyword arguments.

        Returns:
            Width and height of the colorbar.

        Raises:
            ValueError: If the orientation is not either horizontal or vertical.
        """
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


@Theme.apply
class Legend(anywidget.AnyWidget):
    """A legend widget that can be added to the map."""

    ALLOWED_POSITIONS = ["topleft", "topright", "bottomleft", "bottomright"]
    DEFAULT_COLORS = ["#8DD3C7", "#FFFFB3", "#BEBADA", "#FB8072", "#80B1D3"]
    DEFAULT_KEYS = ["One", "Two", "Three", "Four", "etc"]

    _esm = pathlib.Path(__file__).parent / "static" / "legend.js"

    title = traitlets.Unicode("Legend").tag(sync=True)
    legend_keys = traitlets.List([]).tag(sync=True)
    legend_colors = traitlets.List([]).tag(sync=True)
    add_header = traitlets.Bool(True).tag(sync=True)
    show_close_button = traitlets.Bool(False).tag(sync=True)

    position = "bottomright"
    host_map = None

    def __init__(
        self,
        title: str = "Legend",
        legend_dict: dict[str, str] | None = None,
        keys: list[str] | None = None,
        colors: list[str | tuple] | None = None,
        position: str = "bottomright",
        builtin_legend: str | None = None,
        add_header: bool = True,
        widget_args: dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        """Adds a customized legend to the map.

         Args:
            title: Title of the legend. Defaults to 'Legend'.
            legend_dict: A dictionary containing legend items as keys and color as
                values. If provided, keys and colors will be ignored. Defaults to None.
            keys: A list of legend keys. Defaults to None.
            colors: A list of legend colors. Defaults to None.
            position: Position of the legend. Defaults to 'bottomright'.
            builtin_legend: Name of the builtin legend to add to the map. Defaults to
                None.
            add_header: Whether the legend can be closed or not. Defaults to True.
            widget_args: Additional arguments. Only "show_close_button" is supported.

        Raises:
            TypeError: If the keys are not a list.
            TypeError: If the colors are not list.
            ValueError: If the legend template does not exist.
            ValueError: If a rgb value cannot to be converted to hex.
            ValueError: If the keys and colors are not the same length.
            ValueError: If the builtin_legend is not allowed.
            ValueError: If the position is not allowed.
        """
        super().__init__()

        from .legends import builtin_legends  # pylint: disable=import-outside-toplevel

        self.title = title
        self.position = position

        if not widget_args:
            widget_args = {}

        if legend_dict is not None:
            if not isinstance(legend_dict, dict):
                raise TypeError("The legend dict must be a dictionary.")
            self.legend_keys = list(legend_dict.keys())
            self.legend_colors = list(
                map(self._normalize_color_to_hex, legend_dict.values())
            )
        elif keys or colors:
            if "labels" in kwargs:
                self.legend_keys = kwargs.pop("labels")
            if keys is not None:
                if not isinstance(keys, list):
                    raise TypeError("The legend keys must be a list.")
                self.legend_keys = keys
            else:
                self.legend_keys = self.DEFAULT_KEYS

            if colors is not None:
                if not isinstance(colors, list):
                    raise TypeError("The legend colors must be a list.")
                self.legend_colors = list(map(self._normalize_color_to_hex, colors))
            else:
                self.legend_colors = self.DEFAULT_COLORS
            if len(self.legend_keys) != len(self.legend_colors):
                raise ValueError("The legend keys and colors must be the same length.")

        allowed_builtin_legends = builtin_legends.keys()
        if builtin_legend is not None:
            builtin_legend_allowed = self._check_if_allowed(
                builtin_legend, "builtin legend", allowed_builtin_legends
            )  # pytype: disable=wrong-arg-types
            if builtin_legend_allowed:
                legend_dict = builtin_legends[builtin_legend]
                self.legend_keys = list(legend_dict.keys())
                self.legend_colors = list(
                    map(self._normalize_color_to_hex, legend_dict.values())
                )

        self._check_if_allowed(position, "position", self.ALLOWED_POSITIONS)

        self.add_header = add_header
        if "show_close_button" in widget_args:
            self.show_close_button = widget_args["show_close_button"]
        else:
            self.show_close_button = False

        # Setup event listener.
        self.on_msg(self._handle_message_event)

    def _handle_message_event(
        self, widget: ipywidgets.Widget, content: dict[str, Any], buffers: list[Any]
    ) -> None:
        del widget, buffers  # Unused
        if content.get("type") == "click":
            msg_id = content.get("id", "")
            if msg_id == "close":
                self.cleanup()

    def cleanup(self):
        if self.host_map:
            self.host_map.remove(self)

    def _check_if_allowed(
        self, value: str, value_name: str, allowed_list: list[str]
    ) -> bool:
        """Checks if a value is allowed.

        Args:
            value: The value to check.
            value_name: The name of the value.
            allowed_list: The list of allowed values.

        Returns:
            True if the value is allowed, otherwise raises a ValueError.

        Raises:
            ValueError: If the value is not allowed.
        """
        if value not in allowed_list:
            raise ValueError(
                "The "
                + value_name
                + " must be one of the following: {}.".format(", ".join(allowed_list))
            )
        return True

    def _normalize_color_to_hex(self, color: str | tuple) -> str:
        """Converts a list of RGB colors to hex."""
        if isinstance(color, tuple):
            try:
                return f"#{coreutils.rgb_to_hex(color)}"
            except:
                raise ValueError(f"Unable to convert rgb value to hex: {color}")
        elif re.search(r"^(?:[0-9a-fA-F]{3}){1,2}(?:[0-9a-fA-F]{1,2})?$", color):
            # Add a # for hexadecimal strings of length 3 or 6, with optional
            # fourth alpha.
            return f"#{color}"
        return color


@Theme.apply
class Inspector(anywidget.AnyWidget):
    """Inspector widget for Earth Engine data."""

    _esm = pathlib.Path(__file__).parent / "static" / "inspector.js"

    hide_close_button = traitlets.Bool(False).tag(sync=True)

    expand_points = traitlets.Bool(False).tag(sync=True)
    expand_pixels = traitlets.Bool(True).tag(sync=True)
    expand_objects = traitlets.Bool(False).tag(sync=True)

    point_info = traitlets.Dict({}).tag(sync=True)
    pixel_info = traitlets.Dict({}).tag(sync=True)
    object_info = traitlets.Dict({}).tag(sync=True)

    def __init__(
        self,
        host_map: "geemap.Map",
        names: str | list[str] | None = None,
        visible: bool = True,
        decimals: int = 2,
        opened: bool = True,
        show_close_button: bool = True,
    ):
        """Creates an Inspector widget for Earth Engine data.

        Args:
            host_map: The map to add the inspector widget to.
            names: The list of layer names to be inspected.  Defaults to None.
            visible: Whether to inspect visible layers only.  Defaults to True.
            decimals: The number of decimal places to round the values. Defaults to 2.
            opened: Whether the inspector is opened. Defaults to True.
            show_close_button: Whether to show the close button. Defaults to True.
        """
        super().__init__()

        self._host_map = host_map
        if not host_map:
            raise ValueError("Must pass a valid map when creating an inspector.")

        self._names = names
        self._visible = visible
        self._decimals = decimals
        self._opened = opened
        self.hide_close_button = not show_close_button

        self.on_close = None

        host_map.default_style = {"cursor": "crosshair"}
        host_map.on_interaction(self._on_map_interaction)
        self.on_msg(self._handle_message_event)

    def cleanup(self):
        """Removes the widget from the map and performs cleanup."""
        if self._host_map:
            self._host_map.default_style = {"cursor": "default"}
            self._host_map.on_interaction(self._on_map_interaction, remove=True)
        if self.on_close is not None:
            self.on_close()

    def _handle_message_event(
        self, widget: ipywidgets.Widget, content: dict[str, Any], buffers: list[Any]
    ) -> None:
        del widget, buffers  # Unused
        if content.get("type") == "click" and content.get("id") == "close":
            self._on_close_btn_click()

    def _on_map_interaction(self, **kwargs) -> None:
        """Handles map interaction events.

        Args:
            **kwargs: The interaction event arguments.
        """
        latlon = kwargs.get("coordinates", [])
        if kwargs.get("type") == "click":
            self._on_map_click(latlon)

    def _on_map_click(self, latlon: list[float]) -> None:
        """Handles map click events.

        Args:
            latlon: The latitude and longitude of the click event.
        """
        if not latlon or len(latlon) < 2:
            return

        self._clear_inspector_output()
        self._host_map.default_style = {"cursor": "wait"}

        self.point_info = self._point_info(latlon)
        self.pixel_info = self._pixel_info(latlon)
        self.object_info = self._object_info(latlon)

        self._host_map.default_style = {"cursor": "crosshair"}

    def _clear_inspector_output(self) -> None:
        """Clears the inspector output."""
        self.point_info = {}
        self.pixel_info = {}
        self.object_info = {}

    def _on_close_btn_click(self) -> None:
        """Handles close button click events."""
        self.cleanup()

    def _get_visible_map_layers(self) -> dict[str, Any]:
        """Gets the visible map layers.

        Returns:
            A dictionary of visible map layers.
        """
        layers = {}
        if self._names is not None:
            names = (
                # pytype: disable=name-error
                [names]
                if isinstance(names, str)
                else self._names
                # pytype: enable=name-error
            )
            for name in names:
                if name in self._host_map.ee_layers:
                    layers[name] = self._host_map.ee_layers[name]
        else:
            layers = self._host_map.ee_layers
        return {k: v for k, v in layers.items() if v["ee_layer"].visible}

    def _point_info(self, latlon: list[float]) -> dict[str, Any]:
        """Gets information about a point.

        Args:
            latlon: The latitude and longitude of the point.

        Returns:
            The node containing the point information.
        """
        scale = self._host_map.get_scale()
        label = (
            f"Point ({latlon[1]:.{self._decimals}f}, "
            + f"{latlon[0]:.{self._decimals}f}) at {int(scale)}m/px"
        )
        return coreutils.new_tree_node(
            label,
            [
                coreutils.new_tree_node(f"Longitude: {latlon[1]}"),
                coreutils.new_tree_node(f"Latitude: {latlon[0]}"),
                coreutils.new_tree_node(f"Zoom Level: {self._host_map.zoom}"),
                coreutils.new_tree_node(f"Scale (approx. m/px): {scale}"),
            ],
            top_level=True,
            expanded=self.expand_points,
        )

    def _query_point(
        self, latlon: list[float], ee_object: ee.ComputedObject
    ) -> dict[str, Any] | None:
        """Queries a point on the map.

        Args:
            latlon: The latitude and longitude of the point.
            ee_object: The Earth Engine object to query.

        Returns:
            The query result.
        """
        point = ee.Geometry.Point(latlon[::-1])
        scale = self._host_map.get_scale()
        if isinstance(ee_object, ee.ImageCollection):
            ee_object = ee_object.mosaic()
        if isinstance(ee_object, ee.Image):
            return ee_object.reduceRegion(ee.Reducer.first(), point, scale).getInfo()
        return None

    def _pixel_info(self, latlon: list[float]) -> dict[str, Any]:
        """Gets information about pixels at a point.

        Args:
            latlon: The latitude and longitude of the point.

        Returns:
            The node containing the pixels information.
        """

        root = coreutils.new_tree_node("Pixels", expanded=True, top_level=True)
        if not self._visible:
            return root

        layers = self._get_visible_map_layers()
        for layer_name, layer in layers.items():
            ee_object = layer["ee_object"]
            pixel = self._query_point(latlon, ee_object)
            if not pixel:
                continue
            pluralized_band = "band" if len(pixel) == 1 else "bands"
            ee_obj_type = ee_object.__class__.__name__
            label = f"{layer_name}: {ee_obj_type} ({len(pixel)} {pluralized_band})"
            layer_node = coreutils.new_tree_node(label, expanded=self.expand_pixels)
            for key, value in sorted(pixel.items()):
                if isinstance(value, float):
                    value = round(value, self._decimals)
                layer_node["children"].append(
                    coreutils.new_tree_node(
                        f"{key}: {value}", expanded=self.expand_pixels
                    )
                )
            root["children"].append(layer_node)

        return root

    def _get_bbox(
        self, latlon: list[float]
    ) -> ee.Geometry.BBox:  # pytype: disable=invalid-annotation
        """Gets a bounding box around a point.

        Args:
            latlon: The latitude and longitude of the point.

        Returns:
            The bounding box around the point.
        """
        lat, lon = latlon
        delta = 0.005
        return ee.Geometry.BBox(lon - delta, lat - delta, lon + delta, lat + delta)

    def _object_info(self, latlon: list[float]) -> dict[str, Any]:
        """Gets information about objects at a point.

        Args:
            latlon: The latitude and longitude of the point.

        Returns:
            ipytree.Node: The node containing the objects information.
        """
        root = coreutils.new_tree_node("Objects", top_level=True, expanded=True)
        if not self._visible:
            return root

        layers = self._get_visible_map_layers()
        point = ee.Geometry.Point(latlon[::-1])
        for layer_name, layer in layers.items():
            ee_object = layer["ee_object"]
            if isinstance(ee_object, ee.FeatureCollection):
                geom = ee.Feature(ee_object.first()).geometry()
                bbox = self._get_bbox(latlon)
                is_point = ee.Algorithms.If(
                    geom.type().compareTo(ee.String("Point")), point, bbox
                )
                ee_object = ee_object.filterBounds(is_point).first()
                tree_node = coreutils.build_computed_object_tree(
                    ee_object, layer_name, self.expand_objects
                )
                if tree_node:
                    root["children"].append(tree_node)

        return root


@Theme.apply
class LayerManagerRow(anywidget.AnyWidget):
    """A layer manager row widget for geemap."""

    _esm = pathlib.Path(__file__).parent / "static" / "layer_manager_row.js"
    name = traitlets.Unicode("").tag(sync=True)
    visible = traitlets.Bool(True).tag(sync=True)
    opacity = traitlets.Float(1).tag(sync=True)
    is_loading = traitlets.Bool(False).tag(sync=True)

    def __init__(self, host_map: "core.MapInterface", layer: Any):
        super().__init__()
        self.host_map = host_map
        self.layer = layer
        if not host_map or not layer:
            raise ValueError(
                "Must pass a valid map and layer when creating a layer manager row."
            )

        self.name = layer.name
        self.visible = self._get_layer_visibility()
        self.opacity = self._get_layer_opacity()

        # pytype: disable=invalid-annotation
        self.opacity_link: ipywidgets.widget_link.Link | None = None
        self.visibility_link: ipywidgets.widget_link.Link | None = None
        # pytype: enable=invalid-annotation
        self._setup_event_listeners()

    def _can_set_up_jslink(self, obj: Any, trait: str) -> bool:
        return isinstance(obj, ipywidgets.Widget) and hasattr(obj, trait)

    def _traitlet_link_type(self) -> Callable[..., Any]:
        if coreutils.in_colab_shell():
            # TODO: jslink doesn't work in Colab before the layers are added to the map.
            # A potential workaround is calling display() on the layer before jslinking.
            return ipywidgets.link
        return ipywidgets.jslink

    def _setup_event_listeners(self) -> None:
        self.layer.observe(self._on_layer_loading_changed, "loading")
        self.on_msg(self._handle_message_event)

        link_func = self._traitlet_link_type()
        if self._can_set_up_jslink(self.layer, "opacity"):
            self.opacity_link = link_func((self.layer, "opacity"), (self, "opacity"))
        if self._can_set_up_jslink(self.layer, "visible"):
            self.visibility_link = link_func((self.layer, "visible"), (self, "visible"))

    def _on_layer_loading_changed(self, change: dict[str, Any]) -> None:
        self.is_loading = change.get("new", False)

    def _handle_message_event(
        self, widget: ipywidgets.Widget, content: dict[str, Any], buffers: list[Any]
    ) -> None:
        del widget, buffers  # Unused
        if content.get("type") == "click":
            self._handle_button_click(content.get("id", ""))

    @traitlets.observe("opacity")
    def _on_opacity_change(self, change: dict[str, Any]) -> None:
        if self._can_set_up_jslink(self.layer, "opacity"):
            return  # Return if the opacity is handled by a jslink.
        if opacity := change.get("new"):
            if self.layer in self.host_map.geojson_layers:
                # For GeoJSON layers, use style.opacity and style.fillOpacity.
                self.layer.style.update({"opacity": opacity, "fillOpacity": opacity})

    def _get_layer_opacity(self) -> float:
        if hasattr(self.layer, "opacity"):
            return self.layer.opacity
        elif self.layer in self.host_map.geojson_layers:
            opacity = self.layer.style.get("opacity", 1.0)
            fill_opacity = self.layer.style.get("fillOpacity", 1.0)
            return max(opacity, fill_opacity)
        return 1.0

    def _get_layer_visibility(self) -> bool:
        if hasattr(self.layer, "visible"):
            return self.layer.visible
        return True

    def _handle_button_click(self, msg_id: str) -> None:
        if msg_id == "settings":
            self._open_layer_editor()
        elif msg_id == "delete":
            self._delete_layer()

    def _open_layer_editor(self) -> None:
        metadata = self.host_map.ee_layers.get(self.name, None)
        self.host_map.add("layer_editor", position="bottomright", layer_dict=metadata)

    def _delete_layer(self) -> None:
        self.host_map.remove_layer(self.layer)


class LayerManager(anywidget.AnyWidget):
    """A layer manager widget for geemap."""

    _esm = pathlib.Path(__file__).parent / "static" / "layer_manager.js"

    # Whether all layers should be visible or not. Represented as a checkbox in the UI.
    visible = traitlets.Bool(True).tag(sync=True)

    # Child widgets in the container. Using a tuple here to force reassignment to update
    # the list. When a proper notifying-list trait exists, use that instead.
    children = TypedTuple(
        trait=traitlets.Instance(ipywidgets.Widget),
        help="List of widget children",
    ).tag(sync=True, **ipywidgets.widget_serialization)

    def __init__(self, host_map: "core.MapInterface"):
        super().__init__()
        self.host_map = host_map
        if not host_map:
            raise ValueError("Must pass a valid map when creating a layer manager.")

    def refresh_layers(self) -> None:
        """Refresh the layers in the layer manager.

        Uses the map interface to pull active layers. This function must be called
        whenever a layer is added or removed on the map.
        """
        self.children = list(map(self._create_row_widget, self.host_map.layers))

    def _create_row_widget(self, layer: Any) -> LayerManagerRow:
        return LayerManagerRow(self.host_map, layer)

    @traitlets.observe("visible")
    def _observe_visible(self, change: dict[str, Any]) -> None:
        # When the `visible` property changes, propagate that change to all children.
        if (visible := change.get("new")) is not None:
            for child in self.children:
                child.visible = visible


@Theme.apply
class BasemapSelector(anywidget.AnyWidget):
    """Widget for selecting a basemap."""

    _esm = pathlib.Path(__file__).parent / "static" / "basemap_selector.js"

    # The list of basemap names to make available for selection.
    basemaps = traitlets.Dict({}).tag(sync=True)

    # The currently selected basemap value.
    provider = traitlets.Unicode("").tag(sync=True)
    resource = traitlets.Unicode("").tag(sync=True)

    def __init__(self, basemaps: list[str], value: str):
        """Creates a widget for selecting a basemap.

        Args:
            basemaps: The list of basemap names to make available for selection.
            value: The default value from basemaps to select.
        """
        super().__init__()
        self.on_close = None
        self.on_basemap_changed = None
        self.basemaps = self._get_basemap_dictionary(basemaps)
        provider, resource = self._parse_basemap_name(value)
        self.provider = provider
        self.resource = resource
        self._setup_event_listeners()

    def _parse_basemap_name(self, name: str) -> tuple[str, str]:
        components = name.split(".")
        resource = ".".join(components[1:]) if len(components) > 1 else ""
        return components[0], resource

    def _get_basemap_dictionary(self, basemaps: list[str]) -> dict[str, list[str]]:
        basemaps_dict: dict[str, list[str]] = {}
        for basemap in basemaps:
            provider, resource = self._parse_basemap_name(basemap)
            provider_map = basemaps_dict.setdefault(provider, [])
            if resource:
                provider_map.append(resource)
        return basemaps_dict

    def _setup_event_listeners(self) -> None:
        self.on_msg(self._handle_message_event)

    def _handle_message_event(
        self, widget: ipywidgets.Widget, content: dict[str, Any], buffers: list[Any]
    ) -> None:
        del widget, buffers  # Unused
        if content.get("type") == "click":
            msg_id = content.get("id", "")
            if msg_id == "close":
                self.cleanup()
            if msg_id == "apply":
                self.apply_basemap()

    def apply_basemap(self) -> None:
        basemap_name = self.provider
        if self.resource:
            basemap_name = basemap_name + f".{self.resource}"
        if self.on_basemap_changed:
            self.on_basemap_changed(basemap_name)

    def cleanup(self) -> None:
        """Cleans up the widget by calling the on_close callback if set."""
        if self.on_close:
            self.on_close()


# Type alias for backwards compatibility.
Basemap = BasemapSelector


@Theme.apply
class LayerEditor(anywidget.AnyWidget):
    """Widget for displaying and editing layer visualization properties."""

    class LayerType(enum.Enum):
        """Layer types."""

        RASTER = "raster"
        VECTOR = "vector"

    _esm = pathlib.Path(__file__).parent / "static" / "layer_editor.js"

    layer_name: traitlets.Unicode = traitlets.Unicode("").tag(sync=True)
    layer_type: traitlets.Unicode = traitlets.Unicode("").tag(sync=True)
    band_names: traitlets.List = traitlets.List([]).tag(sync=True)
    colormaps: traitlets.List = traitlets.List([]).tag(sync=True)

    # Child widgets in the container. Using a tuple here to force reassignment to update
    # the list. When a proper notifying-list trait exists, use that instead.
    children = TypedTuple(
        trait=traitlets.Instance(ipywidgets.Widget),
        help="List of widget children",
    ).tag(sync=True, **ipywidgets.widget_serialization)

    def __init__(self, host_map: "geemap.Map", layer_dict: dict[str, Any] | None):
        """Initializes a layer editor widget.

        Args:
            host_map: The geemap.Map object.
            layer_dict: The layer object to edit.
        """
        super().__init__()

        self.on_close = None

        self._host_map = host_map
        if not host_map:
            raise ValueError(
                f"Must pass a valid map when creating a {self.__class__.__name__} widget."
            )

        if layer_dict is not None:
            self._ee_object = layer_dict["ee_object"]
            if isinstance(self._ee_object, (ee.Feature, ee.Geometry)):
                self._ee_object = ee.FeatureCollection(self._ee_object)

            self._ee_layer = layer_dict["ee_layer"]
            self.layer_name = self._ee_layer.name
            self.colormaps = self._get_colormaps()

            if isinstance(self._ee_object, ee.FeatureCollection):
                self.layer_type = LayerEditor.LayerType.VECTOR.value
            elif isinstance(self._ee_object, ee.Image):
                self.layer_type = LayerEditor.LayerType.RASTER.value
                self.band_names = self._ee_object.bandNames().getInfo()

        self.on_msg(self._handle_message_event)

    def _on_close_click(self) -> None:
        """Handles the close button click event."""
        if self.on_close:
            self.on_close()

    def _handle_message_event(
        self, widget: ipywidgets.Widget, content: dict[str, Any], buffers: list[Any]
    ) -> None:
        del widget, buffers  # Unused

        msg_details = content.get("detail", {})
        msg_type = content.get("type")
        msg_id = content.get("id")
        if msg_type == "click":
            if msg_id == "close":
                self._on_close_click()
            elif msg_id == "apply":
                if self.layer_type == LayerEditor.LayerType.RASTER.value:
                    self._on_apply_click_raster(msg_details)
                else:
                    self._on_apply_click_vector(msg_details)
            elif msg_id == "import":
                if self.layer_type == LayerEditor.LayerType.RASTER.value:
                    self._on_import_click_raster(msg_details)
                else:
                    self._on_import_click_vector(msg_details)
        elif msg_type == "calculate":
            response = None
            if msg_id == "band-stats":
                response = self._calculate_band_stats(msg_details)
            elif msg_id == "palette":
                response = self._calculate_palette(msg_details)
            elif msg_id == "fields":
                response = self._calculate_fields()
            elif msg_id == "field-values":
                response = self._calculate_field_values(msg_details)
            if response:
                self.send({"type": msg_type, "id": msg_id, "response": response})

    def _calculate_band_stats(self, message: dict[str, Any]) -> dict[str, Any] | None:
        (s, w), (n, e) = self._host_map.bounds
        map_bbox = ee.Geometry.BBox(west=w, south=s, east=e, north=n)

        vis_bands = set(message.get("bands", []))
        stretch = message.get("stretch", "")

        if stretch == "custom":
            return None

        stretch_params = {}
        stretch_value = int(
            # pytype: disable=attribute-error
            re.search(r"\d+", stretch).group()
            # pytype: enable=attribute-error
        )
        if stretch.startswith("percent"):
            stretch_params["percent"] = stretch_value / 100.0
        elif stretch.startswith("sigma"):
            stretch_params["sigma"] = stretch_value

        min_val, max_val = self._ee_layer.calculate_vis_minmax(
            bounds=map_bbox, bands=vis_bands, **stretch_params
        )
        return {"stretch": stretch, "min": min_val, "max": max_val}

    def _render_colorbar(
        self, colors: list[str], band_min: float, band_max: float
    ) -> None:
        if len(colors) < 2:
            self.children = []
            return

        _, ax = pyplot.subplots(figsize=(5, 0.3))
        cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
            "custom", colors, N=256
        )
        norm = matplotlib.colors.Normalize(vmin=band_min, vmax=band_max)
        ticks = numpy.linspace(band_min, band_max, 4, endpoint=True)
        matplotlib.colorbar.ColorbarBase(
            ax, norm=norm, cmap=cmap, orientation="horizontal", ticks=ticks
        )

        colorbar_output = ipywidgets.Output(
            layout=ipywidgets.Layout(height="60px", max_width="300px")
        )
        with colorbar_output:
            pyplot.show()
        self.children = [colorbar_output]

    def _calculate_palette(self, message: dict[str, Any]) -> dict[str, Any] | None:
        colormap = message.get("colormap", "")
        classes = message.get("classes", "")
        palette = message.get("palette", "")
        band_min = message.get("bandMin", 0.0)
        band_max = message.get("bandMax", 1.0)

        if colormap == "Custom":
            colors = [color.strip() for color in palette.split(",")]
            self._render_colorbar(colors, band_min, band_max)
            return {"palette": palette}

        classes = None if classes == "any" else int(classes)
        cmap = pyplot.get_cmap(colormap, classes)
        cmap_colors = [matplotlib.colors.rgb2hex(cmap(i))[1:] for i in range(cmap.N)]
        colors = coreutils.to_hex_colors(cmap_colors)

        self._render_colorbar(colors, band_min, band_max)
        return {"palette": ", ".join(colors)}

    def _calculate_fields(self) -> dict[str, Any]:
        available_fields = ee.Feature(self._ee_object.first()).propertyNames().getInfo()
        if available_fields:
            field = available_fields[0]
            values = self._calculate_field_values({"field": field})["field-values"]
            return {"fields": available_fields, "field-values": values}
        return {"fields": [], "field-values": []}

    def _calculate_field_values(self, message: dict[str, Any]) -> dict[str, Any]:
        field = message.get("field")
        options = self._ee_object.aggregate_array(field).getInfo()
        if options:
            options = list(set(options))
            options.sort()
        return {"field-values": options or []}

    def _get_colormaps(self) -> list[str]:
        """Gets the list of available colormaps."""
        colormap_options = pyplot.colormaps()
        colormap_options.sort()
        return ["Custom"] + colormap_options

    def _hex_with_opacity(self, base_color: str, opacity: float) -> str:
        """Adds opacity to a hex string (e.g. #000000 to #000000FF)."""
        return base_color[1:] + str(hex(int(opacity * 255)))[2:].zfill(2)

    def _on_import_click_vector(self, state: dict[str, Any]) -> None:
        """Handles the import button click event for vector layers."""
        vis_options = self._get_vis_params(state)
        coreutils.create_code_cell(f"style = {str(vis_options)}")
        print(f"style = {str(vis_options)}")

    def _get_vis_params(self, state: dict[str, Any]) -> dict[str, Any]:
        color = self._hex_with_opacity(
            state.get("color", ""), state.get("opacity", 1.0)
        )
        fill_opacity = state.get("fillOpacity", 0.66)
        fill_color = self._hex_with_opacity(state.pop("fillColor"), fill_opacity)
        line_width = state.get("lineWidth")
        line_type = state.get("lineType")
        point_size = state.get("pointSize", None)
        point_shape = state.get("pointShape", None)
        vis_options = {
            "color": color,
            "fillColor": fill_color,
            "width": line_width,
            "lineType": line_type,
        }
        if coreutils.geometry_type(self._ee_object) in ["Point", "MultiPoint"]:
            vis_options["pointSize"] = point_size
            vis_options["pointShape"] = point_shape
        return vis_options

    def _on_apply_click_vector(self, state: dict[str, Any]) -> None:
        """Handles the apply button click event from a vector layer."""
        if self.layer_name in self._host_map.ee_layers:
            self._host_map.remove(self._ee_layer)

        new_layer_object = None
        style_by_attribute = state.pop("shouldStyleByAttribute")
        vis_options = self._get_vis_params(state)
        if not style_by_attribute:
            new_layer_object = self._ee_object.style(**vis_options)
        else:
            fill_opacity = vis_options.get("fillOpacity", 1.0)
            colors = ee.List(
                [
                    self._hex_with_opacity(color.strip(), fill_opacity)
                    for color in state.get("palette", [])
                ]
            )
            field = state.get("field")
            arr = self._ee_object.aggregate_array(field).distinct().sort()
            fc = self._ee_object.map(
                lambda f: f.set({"styleIndex": arr.indexOf(f.get(field))})
            )
            step = arr.size().divide(colors.size()).ceil()
            fc = fc.map(
                lambda f: f.set(
                    {
                        "style": {
                            **vis_options,
                            "fillColor": colors.get(
                                ee.Number(f.get("styleIndex")).divide(step).floor()
                            ),
                        },
                    }
                )
            )
            new_layer_object = fc.style(**{"styleProperty": "style"})

        new_layer_name = state.pop("layerName")
        self._host_map.add_layer(new_layer_object, {}, new_layer_name)
        if legend := state.get("legend"):
            self._apply_legend(legend, state.get("palette"), 0.0, 1.0)

    def _on_import_click_raster(self, vis_params: dict[str, Any]) -> None:
        """Handles the import button click event for raster layers."""
        vis_params.pop("opacity", None)
        coreutils.create_code_cell(f"vis_params = {str(vis_params)}")
        print(f"vis_params = {str(vis_params)}")

    def _on_apply_click_raster(self, vis_params: dict[str, Any]) -> None:
        """Handles the apply button click event from a raster layer."""
        opacity = vis_params.pop("opacity", 1.0)
        legend = vis_params.pop("legend", {})
        self._host_map.add_layer(
            self._ee_object, vis_params, self.layer_name, True, opacity
        )
        self._ee_layer.visible = False
        if legend:
            self._apply_legend(
                legend,
                vis_params.get("palette"),
                vis_params.get("min"),
                vis_params.get("max"),
            )

    def _apply_legend(
        self,
        legend: dict[str, Any],
        palette: str | None,
        min_value: float | None,
        max_value: float | None,
    ) -> None:
        if legend.get("type") == "linear":
            if hasattr(self._host_map, "_add_colorbar"):
                # pylint: disable-next=protected-access
                self._host_map._add_colorbar(
                    vis_params={
                        "palette": palette,
                        "min": min_value,
                        "max": max_value,
                    },
                    layer_name=self.layer_name,
                )
        elif legend.get("type") == "step":
            if hasattr(self._host_map, "_add_legend"):
                # pylint: disable-next=protected-access
                self._host_map._add_legend(
                    title=legend.get("title", ""),
                    layer_name=self.layer_name,
                    keys=legend.get("labels", []),
                    colors=palette,
                )


@Theme.apply
class SearchBar(anywidget.AnyWidget):
    _esm = pathlib.Path(__file__).parent / "static" / "search_bar.js"

    # Whether the search bar is collapsed.
    collapsed = traitlets.Bool(True).tag(sync=True)

    # The currently selected tab.
    tab_index = traitlets.Int(0).tag(sync=True)

    # The stringified JSON for the location search.
    location_model = traitlets.Unicode(
        json.dumps(
            {
                "search": "",
                "results": [],
                "selected": "",
                "additional_html": "",
            }
        )
    ).tag(sync=True)

    # The stringified JSON for the dataset search.
    dataset_model = traitlets.Unicode(
        json.dumps(
            {
                "search": "",
                "results": [],
                "selected": "",
                "additional_html": "",
            }
        )
    ).tag(sync=True)

    def __init__(self, host_map, **kwargs):
        super().__init__()
        self.on_close = None
        self.host_map = host_map
        self.host_map.search_locations = None
        self.host_map.search_loc_marker = None
        self.host_map.search_loc_geom = None
        self.host_map.search_datasets = None

        self.on_msg(self.handle_message_event)

    def handle_message_event(
        self, widget: ipywidgets.Widget, content: dict[str, Any], buffers: list[Any]
    ) -> None:
        del widget, buffers  # Unused
        if content.get("type") == "click":
            msg_id = content.get("id", "")
            if msg_id == "import":
                self.import_button_clicked()
            elif msg_id == "close":
                self.cleanup()

    def cleanup(self):
        """Removes the widget from the map and performs cleanup."""
        if self.on_close is not None:
            self.on_close()

    @traitlets.observe("location_model")
    def _observe_location_model(self, change: dict[str, Any]) -> None:
        old = json.loads(change.get("old"))
        new = json.loads(change.get("new"))
        if new["search"] != old["search"]:
            if new["search"]:
                if common.latlon_from_text(new["search"]):
                    self._search_lat_lon(new["search"])
                else:
                    self._search_location(new["search"])
            else:
                self.location_model = json.dumps(
                    {
                        "search": "",
                        "results": [],
                        "selected": "",
                        "additional_html": "",
                    }
                )
                marker = self.host_map.search_loc_marker
                self.host_map.search_loc_marker = None
                self.host_map.remove(marker)

        elif new["selected"] and new["selected"] != old["selected"]:
            self._set_selected_location(new["selected"])

    @traitlets.observe("dataset_model")
    def _observe_dataset_model(self, change: dict[str, Any]) -> None:
        old = json.loads(change.get("old"))
        new = json.loads(change.get("new"))
        if new["search"] != old["search"]:
            if new["search"]:
                self._search_dataset(new["search"])
            else:
                self.dataset_model = json.dumps(
                    {
                        "search": "",
                        "results": [],
                        "selected": "",
                        "additional_html": "",
                    }
                )
        elif new["selected"] and new["selected"] != old["selected"]:
            self._select_dataset(new["selected"])

    def _search_location(self, address):
        location_model = json.loads(self.location_model)
        geoloc_results = common.geocode(address)
        self.host_map.search_locations = geoloc_results
        if geoloc_results is not None and len(geoloc_results) > 0:
            location_model["results"] = [x.address for x in geoloc_results]
            self.location_model = json.dumps(location_model)
        else:
            location_model["results"] = []
            location_model["selected"] = ""
            location_model["additional_html"] = "No results could be found."
            self.location_model = json.dumps(location_model)

    def _set_selected_location(self, address):
        locations = self.host_map.search_locations
        location = None
        for l in locations:
            if l.address == address:
                location = l
        if not location:
            return
        latlon = (location.lat, location.lng)
        self.host_map.search_loc_geom = ee.Geometry.Point(location.lng, location.lat)
        if self.host_map.search_loc_marker is None:
            marker = ipyleaflet.Marker(
                location=latlon,
                draggable=False,
                name="Search location",
            )
            self.host_map.search_loc_marker = marker
            self.host_map.add(marker)
            self.host_map.center = latlon
        else:
            marker = self.host_map.search_loc_marker
            marker.location = latlon
            self.host_map.center = latlon

    def _search_lat_lon(self, lat_lon):
        location_model = json.loads(self.location_model)
        if latlon := common.latlon_from_text(lat_lon):
            geoloc_results = common.geocode(lat_lon, reverse=True)
            if geoloc_results is not None and len(geoloc_results) > 0:
                top_loc = geoloc_results[0]
                latlon = (top_loc.lat, top_loc.lng)
                location_model["results"] = [x.address for x in geoloc_results]
                location_model["selected"] = location_model["results"][0]
                location_model["additional_html"] = ""
                self.location_model = json.dumps(location_model)
            else:
                location_model["results"] = []
                location_model["selected"] = ""
                location_model["additional_html"] = "No results could be found."
                self.location_model = json.dumps(location_model)
            self.host_map.search_loc_geom = ee.Geometry.Point(latlon[1], latlon[0])
            if self.host_map.search_loc_marker is None:
                marker = ipyleaflet.Marker(
                    location=latlon,
                    draggable=False,
                    name="Search location",
                )
                self.host_map.search_loc_marker = marker
                self.host_map.add(marker)
                self.host_map.center = latlon
            else:
                marker = self.host_map.search_loc_marker
                marker.location = latlon
                self.host_map.center = latlon
        else:
            location_model["results"] = []
            location_model["selected"] = ""
            no_results = (
                """<em style="color: red">"""
                "The lat-lon coordinates should be numbers only and"
                "<br>"
                "separated by comma or space, such as 40.2, -100.3"
                "</em>"
            )
            location_model["additional_html"] = no_results
            self.location_model = json.dumps(location_model)

    def _search_dataset(self, dataset_search):
        dataset_model = json.loads(self.dataset_model)
        dataset_model["additional_html"] = "Searching..."
        self.dataset_model = json.dumps(dataset_model)
        self.host_map.default_style = {"cursor": "wait"}
        ee_assets = common.search_ee_data(dataset_search, source="all")
        self.host_map.search_datasets = ee_assets
        asset_titles = [x["title"] for x in ee_assets]
        dataset_model["results"] = asset_titles
        dataset_model["selected"] = asset_titles[0] if asset_titles else ""
        dataset_model["additional_html"] = ""
        if len(ee_assets) > 0:
            dataset_model["additional_html"] = common.ee_data_html(ee_assets[0])
        else:
            dataset_model["additional_html"] = "No results found."
        self.dataset_model = json.dumps(dataset_model)
        self.host_map.default_style = {"cursor": "default"}

    def _select_dataset(self, dataset_title):
        dataset_model = json.loads(self.dataset_model)
        dataset_model["additional_html"] = "Loading ..."
        datasets = self.host_map.search_datasets
        dataset = None
        for d in datasets:
            if d["title"] == dataset_title:
                dataset = d
        if not dataset:
            return
        dataset_html = common.ee_data_html(dataset)
        dataset_model["additional_html"] = dataset_html
        self.dataset_model = json.dumps(dataset_model)

    def get_ee_example(self, asset_id):
        try:
            pkg_dir = str(
                # pytype: disable=attribute-error
                importlib.resources.files("geemap")
                .joinpath("geemap.py")
                .parent
                # pytype: enable=attribute-error
            )
            with open(os.path.join(pkg_dir, "data/gee_f.json"), encoding="utf-8") as f:
                functions = json.load(f)
            details = [
                dataset["code"]
                for x in functions["examples"]
                for dataset in x["contents"]
                if x["name"] == "Datasets"
                if dataset["name"] == asset_id.replace("/", "_")
            ]

            return conversion.js_snippet_to_py(
                details[0],
                add_new_cell=False,
                import_ee=False,
                import_geemap=False,
                show_map=False,
                Map=self.host_map._var_name,
            )

        except Exception as e:
            pass

    def import_button_clicked(self):
        dataset_model = json.loads(self.dataset_model)
        print(dataset_model)
        if dataset_model["selected"]:
            datasets = self.host_map.search_datasets
            dataset = None
            for d in datasets:
                if d["title"] == dataset_model["selected"]:
                    dataset = d
            if not dataset:
                return
            id_ = dataset["id"]
            code = self.get_ee_example(id_)

            if not code:
                dataset_uid = "dataset_" + coreutils.random_string(string_length=3)
                translate = {
                    "image_collection": "ImageCollection",
                    "image": "Image",
                    "table": "FeatureCollection",
                    "table_collection": "FeatureCollection",
                }
                datatype = translate[dataset["type"]]
                id_ = dataset["id"]
                line1 = f"{dataset_uid} = ee.{datatype}('{id_}')"
                action = {
                    "image_collection": f"\n{self.host_map._var_name}.addLayer({dataset_uid}, {{}}, '{id_}')",
                    "image": f"\n{self.host_map._var_name}.addLayer({dataset_uid}, {{}}, '{id_}')",
                    "table": f"\n{self.host_map._var_name}.addLayer({dataset_uid}, {{}}, '{id_}')",
                    "table_collection": f"\n{self.host_map._var_name}.addLayer({dataset_uid}, {{}}, '{id_}')",
                }
                line2 = action[dataset["type"]]
                code = [line1, line2]

            contents = "".join(code).strip()
            # coreutils.create_code_cell(contents)
            copy_success = False
            try:
                import pyperclip

                pyperclip.copy(str(contents))
                copy_success = True
            except Exception as e:
                pass
            if copy_success:
                dataset_model["additional_html"] = (
                    "<pre>"
                    "# The code has been copied to the clipboard.\n"
                    "# Press Ctrl+V in a new cell to paste it.\n"
                    f"{contents}"
                    "</pre"
                )
            else:
                dataset_model["additional_html"] = f"<pre>{contents}</pre"
            self.dataset_model = json.dumps(dataset_model)
