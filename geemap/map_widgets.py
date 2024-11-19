"""Various ipywidgets that can be added to a map."""

import functools
import pathlib
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import IPython
from IPython.display import HTML, display

import anywidget
import ee
import ipywidgets
import traitlets

from . import coreutils


class TypedTuple(traitlets.Container):
    """A trait for a tuple of any length with type-checked elements."""

    klass = tuple
    _cast_types = (list,)


def _set_css_in_cell_output(info: Any) -> None:
    """Sets CSS styles in the cell output for different themes.

    Args:
        info (Any): Information passed to the function (unused).

    Returns:
        None
    """
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
            cls (Any): The class to which the theme will be applied.

        Returns:
            Any: The class with the applied theme.
        """
        original_init = cls.__init__

        @functools.wraps(cls.__init__)
        def wrapper(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self.add_class("geemap-{}".format(Theme.current_theme))

        cls.__init__ = wrapper
        return cls


@Theme.apply
class Colorbar(ipywidgets.Output):
    """A matplotlib colorbar widget that can be added to the map."""

    def __init__(
        self,
        vis_params: Optional[Union[Dict[str, Any], list, tuple]] = None,
        cmap: str = "gray",
        discrete: bool = False,
        label: Optional[str] = None,
        orientation: str = "horizontal",
        transparent_bg: bool = False,
        font_size: int = 9,
        axis_off: bool = False,
        max_width: Optional[str] = None,
        **kwargs: Any,
    ):
        """Add a matplotlib colorbar to the map.

        Args:
            vis_params (dict): Visualization parameters as a dictionary. See
                https://developers.google.com/earth-engine/guides/image_visualization # noqa
                for options.
            cmap (str, optional): Matplotlib colormap. Defaults to "gray". See
                https://matplotlib.org/3.3.4/tutorials/colors/colormaps.html#sphx-glr-tutorials-colors-colormaps-py # noqa
                for options.
            discrete (bool, optional): Whether to create a discrete colorbar.
                Defaults to False.
            label (str, optional): Label for the colorbar. Defaults to None.
            orientation (str, optional): Orientation of the colorbar, such as
                "vertical" and "horizontal". Defaults to "horizontal".
            transparent_bg (bool, optional): Whether to use transparent
                background. Defaults to False.
            font_size (int, optional): Font size for the colorbar. Defaults
                to 9.
            axis_off (bool, optional): Whether to turn off the axis. Defaults
                to False.
            max_width (str, optional): Maximum width of the colorbar in pixels.
                Defaults to None.

        Raises:
            TypeError: If the vis_params is not a dictionary.
            ValueError: If the orientation is not either horizontal or vertical.
            ValueError: If the provided min value is not convertible to float.
            ValueError: If the provided max value is not convertible to float.
            ValueError: If the provided opacity value is not convertible to float.
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
        self, orientation: str, kwargs: Dict[str, Any]
    ) -> Tuple[float, float]:
        """Get the dimensions of the colorbar based on orientation.

        Args:
            orientation (str): Orientation of the colorbar.
            kwargs (Dict[str, Any]): Additional keyword arguments.

        Returns:
            Tuple[float, float]: Width and height of the colorbar.

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
class Legend(ipywidgets.VBox):
    """A legend widget that can be added to the map."""

    ALLOWED_POSITIONS = ["topleft", "topright", "bottomleft", "bottomright"]
    DEFAULT_COLORS = ["#8DD3C7", "#FFFFB3", "#BEBADA", "#FB8072", "#80B1D3"]
    DEFAULT_KEYS = ["One", "Two", "Three", "Four", "etc"]
    DEFAULT_MAX_HEIGHT = "400px"
    DEFAULT_MAX_WIDTH = "300px"

    def __init__(
        self,
        title: str = "Legend",
        legend_dict: Optional[Dict[str, str]] = None,
        keys: Optional[List[str]] = None,
        colors: Optional[List[Union[str, tuple]]] = None,
        position: str = "bottomright",
        builtin_legend: Optional[str] = None,
        add_header: bool = True,
        widget_args: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
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
            add_header (bool, optional): Whether the legend can be closed or
                not. Defaults to True.
            widget_args (dict, optional): Additional arguments passed to the
                widget_template() function. Defaults to {}.

        Raises:
            TypeError: If the keys are not a list.
            TypeError: If the colors are not list.
            TypeError: If the colors are not a list of tuples.
            ValueError: If the legend template does not exist.
            ValueError: If a rgb value cannot to be converted to hex.
            ValueError: If the keys and colors are not the same length.
            ValueError: If the builtin_legend is not allowed.
            ValueError: If the position is not allowed.

        """
        import os  # pylint: disable=import-outside-toplevel
        import pkg_resources  # pylint: disable=import-outside-toplevel
        from .legends import builtin_legends  # pylint: disable=import-outside-toplevel

        if not widget_args:
            widget_args = {}

        pkg_dir = os.path.dirname(
            pkg_resources.resource_filename("geemap", "geemap.py")
        )
        legend_template = os.path.join(pkg_dir, "data/template/legend.html")

        if not os.path.exists(legend_template):
            raise ValueError("The legend template does not exist.")

        if legend_dict is not None:
            if not isinstance(legend_dict, dict):
                raise TypeError("The legend dict must be a dictionary.")
            else:
                keys = list(legend_dict.keys())
                colors = list(legend_dict.values())
                if all(isinstance(item, tuple) for item in colors):
                    colors = Legend.__convert_rgb_colors_to_hex(colors)

        if "labels" in kwargs:
            keys = kwargs["labels"]
            kwargs.pop("labels")

        if keys is not None:
            if not isinstance(keys, list):
                raise TypeError("The legend keys must be a list.")
        else:
            keys = Legend.DEFAULT_KEYS

        if colors is not None:
            if not isinstance(colors, list):
                raise TypeError("The legend colors must be a list.")
            elif all(isinstance(item, tuple) for item in colors):
                colors = Legend.__convert_rgb_colors_to_hex(colors)
            elif all((item.startswith("#") and len(item) == 7) for item in colors):
                pass
            elif all((len(item) == 6) for item in colors):
                pass
            else:
                raise TypeError("The legend colors must be a list of tuples.")
        else:
            colors = Legend.DEFAULT_COLORS

        if len(keys) != len(colors):
            raise ValueError("The legend keys and colors must be the same length.")

        allowed_builtin_legends = builtin_legends.keys()
        if builtin_legend is not None:
            builtin_legend_allowed = Legend.__check_if_allowed(
                builtin_legend, "builtin legend", allowed_builtin_legends
            )
            if builtin_legend_allowed:
                legend_dict = builtin_legends[builtin_legend]
                keys = list(legend_dict.keys())
                colors = list(legend_dict.values())
            if all(isinstance(item, tuple) for item in colors):
                colors = Legend.__convert_rgb_colors_to_hex(colors)

        Legend.__check_if_allowed(position, "position", Legend.ALLOWED_POSITIONS)
        header = []
        footer = []
        content = Legend.__create_legend_items(keys, colors)

        with open(legend_template) as f:
            lines = f.readlines()
            lines[3] = lines[3].replace("Legend", title)
            header = lines[:6]
            footer = lines[11:]

        legend_html = header + content + footer
        legend_text = "".join(legend_html)
        legend_output = ipywidgets.Output(layout=Legend.__create_layout(**kwargs))
        legend_widget = ipywidgets.HTML(value=legend_text)

        if add_header:
            if "show_close_button" not in widget_args:
                widget_args["show_close_button"] = False
            if "widget_icon" not in widget_args:
                widget_args["widget_icon"] = "bars"

            legend_output_widget = coreutils.widget_template(
                legend_output,
                position=position,
                display_widget=legend_widget,
                **widget_args,
            )
        else:
            legend_output_widget = legend_widget

        super().__init__(children=[legend_output_widget])

        legend_output.clear_output()
        with legend_output:
            display(legend_widget)

    def __check_if_allowed(
        value: str, value_name: str, allowed_list: List[str]
    ) -> bool:
        """Checks if a value is allowed.

        Args:
            value (str): The value to check.
            value_name (str): The name of the value.
            allowed_list (List[str]): The list of allowed values.

        Returns:
            bool: True if the value is allowed, otherwise raises a ValueError.

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

    def __convert_rgb_colors_to_hex(colors: List[tuple]) -> List[str]:
        """Converts a list of RGB colors to hex.

        Args:
            colors (List[tuple]): A list of RGB color tuples.

        Returns:
            List[str]: A list of hex color strings.

        Raises:
            ValueError: If unable to convert an RGB value to hex.
        """
        try:
            return [coreutils.rgb_to_hex(x) for x in colors]
        except:
            raise ValueError("Unable to convert rgb value to hex.")

    def __create_legend_items(keys: List[str], colors: List[str]) -> List[str]:
        """Creates HTML legend items.

        Args:
            keys (List[str]): A list of legend keys.
            colors (List[str]): A list of legend colors.

        Returns:
            List[str]: A list of HTML strings for the legend items.
        """
        legend_items = []
        for index, key in enumerate(keys):
            color = colors[index]
            if not color.startswith("#"):
                color = "#" + color
            item = "<li><span style='background:{};'></span>{}</li>\n".format(
                color, key
            )
            legend_items.append(item)
        return legend_items

    def __create_layout(**kwargs: Any) -> Dict[str, Optional[str]]:
        """Creates the layout for the legend.

        Args:
            **kwargs (Any): Additional keyword arguments for layout properties.

        Returns:
            Dict[str, Optional[str]]: A dictionary of layout properties.
        """
        height = Legend.__create_layout_property("height", None, **kwargs)

        min_height = Legend.__create_layout_property("min_height", None, **kwargs)

        if height is None:
            max_height = Legend.DEFAULT_MAX_HEIGHT
        else:
            max_height = Legend.__create_layout_property("max_height", None, **kwargs)

        width = Legend.__create_layout_property("width", None, **kwargs)

        if "min_width" not in kwargs:
            min_width = None

        if width is None:
            max_width = Legend.DEFAULT_MAX_WIDTH
        else:
            max_width = Legend.__create_layout_property(
                "max_width", Legend.DEFAULT_MAX_WIDTH, **kwargs
            )

        return {
            "height": height,
            "max_height": max_height,
            "max_width": max_width,
            "min_height": min_height,
            "min_width": min_width,
            "overflow": "scroll",
            "width": width,
        }

    def __create_layout_property(name, default_value, **kwargs):
        return default_value if name not in kwargs else kwargs[name]


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
        names: Optional[Union[str, List[str]]] = None,
        visible: bool = True,
        decimals: int = 2,
        opened: bool = True,
        show_close_button: bool = True,
    ):
        """Creates an Inspector widget for Earth Engine data.

        Args:
            host_map (geemap.Map): The map to add the inspector widget to.
            names (list, optional): The list of layer names to be inspected.
                Defaults to None.
            visible (bool, optional): Whether to inspect visible layers only.
                Defaults to True.
            decimals (int, optional): The number of decimal places to round the
                values. Defaults to 2.
            opened (bool, optional): Whether the inspector is opened. Defaults
                to True.
            show_close_button (bool, optional): Whether to show the close
                button. Defaults to True.
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
        self, widget: ipywidgets.Widget, content: Dict[str, Any], buffers: List[Any]
    ) -> None:
        del widget, buffers  # Unused
        if content.get("type") == "click" and content.get("id") == "close":
            self._on_close_btn_click()

    def _on_map_interaction(self, **kwargs: Any) -> None:
        """Handles map interaction events.

        Args:
            **kwargs (Any): The interaction event arguments.
        """
        latlon = kwargs.get("coordinates", [])
        if kwargs.get("type") == "click":
            self._on_map_click(latlon)

    def _on_map_click(self, latlon: List[float]) -> None:
        """Handles map click events.

        Args:
            latlon (List[float]): The latitude and longitude of the click event.
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

    def _get_visible_map_layers(self) -> Dict[str, Any]:
        """Gets the visible map layers.

        Returns:
            Dict[str, Any]: A dictionary of visible map layers.
        """
        layers = {}
        if self._names is not None:
            names = [names] if isinstance(names, str) else self._names
            for name in names:
                if name in self._host_map.ee_layers:
                    layers[name] = self._host_map.ee_layers[name]
        else:
            layers = self._host_map.ee_layers
        return {k: v for k, v in layers.items() if v["ee_layer"].visible}

    def _point_info(self, latlon: List[float]) -> Dict[str, Any]:
        """Gets information about a point.

        Args:
            latlon (List[float]): The latitude and longitude of the point.

        Returns:
            Dict[str, Any]: The node containing the point information.
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
        self, latlon: List[float], ee_object: ee.ComputedObject
    ) -> Optional[Dict[str, Any]]:
        """Queries a point on the map.

        Args:
            latlon (List[float]): The latitude and longitude of the point.
            ee_object (ee.ComputedObject): The Earth Engine object to query.

        Returns:
            Optional[Dict[str, Any]]: The query result.
        """
        point = ee.Geometry.Point(latlon[::-1])
        scale = self._host_map.get_scale()
        if isinstance(ee_object, ee.ImageCollection):
            ee_object = ee_object.mosaic()
        if isinstance(ee_object, ee.Image):
            return ee_object.reduceRegion(ee.Reducer.first(), point, scale).getInfo()
        return None

    def _pixel_info(self, latlon: List[float]) -> Dict[str, Any]:
        """Gets information about pixels at a point.

        Args:
            latlon (List[float]): The latitude and longitude of the point.

        Returns:
            Dict[str, Any]: The node containing the pixels information.
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

    def _get_bbox(self, latlon: List[float]) -> ee.Geometry.BBox:
        """Gets a bounding box around a point.

        Args:
            latlon (List[float]): The latitude and longitude of the point.

        Returns:
            ee.Geometry.BBox: The bounding box around the point.
        """
        lat, lon = latlon
        delta = 0.005
        return ee.Geometry.BBox(lon - delta, lat - delta, lon + delta, lat + delta)

    def _object_info(self, latlon: List[float]) -> Dict[str, Any]:
        """Gets information about objects at a point.

        Args:
            latlon (List[float]): The latitude and longitude of the point.

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

        self.opacity_link: Optional[ipywidgets.widget_link.Link] = None
        self.visibility_link: Optional[ipywidgets.widget_link.Link] = None
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

    def _on_layer_loading_changed(self, change: Dict[str, Any]) -> None:
        self.is_loading = change.get("new", False)

    def _handle_message_event(
        self, widget: ipywidgets.Widget, content: Dict[str, Any], buffers: List[Any]
    ) -> None:
        del widget, buffers  # Unused
        if content.get("type") == "click":
            self._handle_button_click(content.get("id", ""))

    @traitlets.observe("opacity")
    def _on_opacity_change(self, change: Dict[str, Any]) -> None:
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


@Theme.apply
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
    def _observe_visible(self, change: Dict[str, Any]) -> None:
        # When the `visible` property changes, propagate that change to all children.
        if (visible := change.get("new")) is not None:
            for child in self.children:
                child.visible = visible


@Theme.apply
class BasemapSelector(anywidget.AnyWidget):
    """Widget for selecting a basemap."""

    _esm = pathlib.Path(__file__).parent / "static" / "basemap_selector.js"

    # The list of basemap names to make available for selection.
    basemaps = traitlets.List([]).tag(sync=True)

    # The currently selected basemap value.
    value = traitlets.Unicode("").tag(sync=True)

    def __init__(self, basemaps: List[str], value: str):
        """Creates a widget for selecting a basemap.

        Args:
            basemaps (list): The list of basemap names to make available for selection.
            value (str): The default value from basemaps to select.
        """
        super().__init__()
        self.on_close = None
        self.on_basemap_changed = None
        self.basemaps = basemaps
        self.value = value
        self._setup_event_listeners()

    def _setup_event_listeners(self) -> None:
        self.on_msg(self._handle_message_event)

    def _handle_message_event(
        self, widget: ipywidgets.Widget, content: Dict[str, Any], buffers: List[Any]
    ) -> None:
        del widget, buffers  # Unused
        if content.get("type") == "click":
            msg_id = content.get("id", "")
            if msg_id == "close":
                self.cleanup()

    @traitlets.observe("value")
    def _observe_value(self, change: Dict[str, Any]) -> None:
        if (value := change.get("new")) is not None and self.on_basemap_changed:
            self.on_basemap_changed(value)

    def cleanup(self) -> None:
        """Cleans up the widget by calling the on_close callback if set."""
        if self.on_close:
            self.on_close()


# Type alias for backwards compatibility.
Basemap = BasemapSelector


@Theme.apply
class LayerEditor(ipywidgets.VBox):
    """Widget for displaying and editing layer visualization properties."""

    def __init__(self, host_map: "geemap.Map", layer_dict: Optional[Dict[str, Any]]):
        """Initializes a layer editor widget.

        Args:
            host_map (geemap.Map): The geemap.Map object.
            layer_dict (Optional[Dict[str, Any]]): The layer object to edit.
        """

        self.on_close = None

        self._host_map = host_map
        if not host_map:
            raise ValueError(
                f"Must pass a valid map when creating a {self.__class__.__name__} widget."
            )

        self._toggle_button = ipywidgets.ToggleButton(
            value=True,
            tooltip="Layer editor",
            icon="gear",
            layout=ipywidgets.Layout(
                width="28px", height="28px", padding="0px 0 0 3px"
            ),
        )
        self._toggle_button.observe(self._on_toggle_click, "value")

        self._close_button = ipywidgets.Button(
            tooltip="Close the vis params dialog",
            icon="times",
            button_style="primary",
            layout=ipywidgets.Layout(width="28px", height="28px", padding="0"),
        )
        self._close_button.on_click(self._on_close_click)

        layout = ipywidgets.Layout(width="95px")
        self._import_button = ipywidgets.Button(
            description="Import",
            button_style="primary",
            tooltip="Import vis params to notebook",
            layout=layout,
        )
        self._apply_button = ipywidgets.Button(
            description="Apply", tooltip="Apply vis params to the layer", layout=layout
        )
        self._import_button.on_click(self._on_import_click)
        self._apply_button.on_click(self._on_apply_click)

        self._label = ipywidgets.Label(
            value="Layer name",
            layout=ipywidgets.Layout(max_width="250px", padding="1px 8px 0 4px"),
        )
        self._embedded_widget = ipywidgets.Label(value="Vis params are uneditable")
        if layer_dict is not None:
            self._ee_object = layer_dict["ee_object"]
            if isinstance(self._ee_object, (ee.Feature, ee.Geometry)):
                self._ee_object = ee.FeatureCollection(self._ee_object)

            self._ee_layer = layer_dict["ee_layer"]
            self._label.value = self._ee_layer.name
            if isinstance(self._ee_object, ee.FeatureCollection):
                self._embedded_widget = _VectorLayerEditor(
                    host_map=host_map, layer_dict=layer_dict
                )
            elif isinstance(self._ee_object, ee.Image):
                self._embedded_widget = _RasterLayerEditor(
                    host_map=host_map, layer_dict=layer_dict
                )

        super().__init__(children=[])
        self._on_toggle_click({"new": True})

    def _on_toggle_click(self, change: Dict[str, Any]) -> None:
        """Handles the toggle button click event.

        Args:
            change (Dict[str, Any]): The change event arguments.
        """
        if change["new"]:
            self.children = [
                ipywidgets.HBox([self._close_button, self._toggle_button, self._label]),
                self._embedded_widget,
                ipywidgets.HBox([self._import_button, self._apply_button]),
            ]
        else:
            self.children = [
                ipywidgets.HBox([self._close_button, self._toggle_button, self._label]),
            ]

    def _on_import_click(self, _) -> None:
        """Handles the import button click event."""
        self._embedded_widget.on_import_click()

    def _on_apply_click(self, _) -> None:
        """Handles the apply button click event."""
        self._embedded_widget.on_apply_click()

    def _on_close_click(self, _) -> None:
        """Handles the close button click event."""
        if self.on_close:
            self.on_close()


def _tokenize_legend_colors(string: str, delimiter: str = ",") -> List[str]:
    """Tokenizes a string of legend colors.

    Args:
        string (str): The string of legend colors.
        delimiter (str, optional): The delimiter used to split the string. Defaults to ",".

    Returns:
        List[str]: A list of hex color strings.
    """
    return coreutils.to_hex_colors([c.strip() for c in string.split(delimiter)])


def _tokenize_legend_labels(string: str, delimiter: str = ",") -> List[str]:
    """Tokenizes a string of legend labels.

    Args:
        string (str): The string of legend labels.
        delimiter (str, optional): The delimiter used to split the string. Defaults to ",".

    Returns:
        List[str]: A list of legend labels.
    """
    return [l.strip() for l in string.split(delimiter)]


@Theme.apply
class _RasterLayerEditor(ipywidgets.VBox):
    """Widget for displaying and editing layer visualization properties for raster layers."""

    def __init__(self, host_map: "geemap.Map", layer_dict: Dict[str, Any]):
        """Initializes a raster layer editor widget.

        Args:
            host_map (geemap.Map): The geemap.Map object.
            layer_dict (Dict[str, Any]): The layer object to edit.
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
            if isinstance(self._vis_params["gamma"], list):
                self._layer_gamma = self._vis_params["gamma"][0]
            else:
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
        self._grayscale_radio_button = ipywidgets.RadioButtons(
            options=["1 band (Grayscale)"],
            layout={"width": "max-content", "margin": "0 16px 0 0"},
        )
        self._rgb_radio_button = ipywidgets.RadioButtons(
            options=["3 bands (RGB)"], layout={"width": "max-content"}
        )
        self._grayscale_radio_button.index = None
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

        self._stretch_dropdown = ipywidgets.Dropdown(
            options={
                "Custom": {},
                "1 σ": {"sigma": 1},
                "2 σ": {"sigma": 2},
                "3 σ": {"sigma": 3},
                "90%": {"percent": 0.90},
                "98%": {"percent": 0.98},
                "100%": {"percent": 1.0},
            },
            description="Stretch:",
            layout=ipywidgets.Layout(width="260px"),
            style={"description_width": "initial"},
        )

        self._stretch_button = ipywidgets.Button(
            disabled=True,
            tooltip="Re-calculate stretch",
            layout=ipywidgets.Layout(width="36px"),
            icon="refresh",
        )
        self._stretch_dropdown.observe(self._value_stretch_changed, names="value")
        self._stretch_button.on_click(self._update_stretch)

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

        # ipywidgets doesn't support horizontal radio buttons
        # (https://github.com/jupyter-widgets/ipywidgets/issues/1247). Instead,
        # use two individual radio buttons with some hackery.
        self._palette_radio_button = ipywidgets.RadioButtons(
            options=["Palette"],
            layout={"width": "max-content", "margin": "2px 16px 0px 2px"},
        )
        self._gamma_radio_button = ipywidgets.RadioButtons(
            options=["Gamma"],
            layout={"width": "max-content"},
        )
        self._gamma_radio_button.index = None
        self._palette_radio_button.index = None

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

        self._stretch_hbox = ipywidgets.HBox(
            [self._stretch_dropdown, self._stretch_button]
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
            self._grayscale_radio_button.index = 0
            self._band_1_dropdown.layout.width = "300px"
            self._bands_hbox.children = [self._band_1_dropdown]
            if "palette" in self._vis_params:
                self._palette_radio_button.index = 0
            elif "gamma" in self._vis_params:
                self._gamma_radio_button.index = 0
            else:
                # Palette takes precedence.
                self._palette_radio_button.index = 0
            palette_selected = self._palette_radio_button.index == 0
            children = self._set_toolbar_layout(
                grayscale=True, palette=palette_selected
            )
            self._legend_checkbox.value = False

            if self._palette_label.value and "," in self._palette_label.value:
                colors = coreutils.to_hex_colors(
                    [color.strip() for color in self._palette_label.value.split(",")]
                )
                self._render_colorbar(colors)
        else:
            self._rgb_radio_button.index = 0
            sel_bands = self._sel_bands
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
            # We never show the palette in RGB mode.
            children = self._set_toolbar_layout(grayscale=False, palette=False)

        self._grayscale_radio_button.observe(
            self._grayscale_radio_observer, names=["value"]
        )
        self._rgb_radio_button.observe(self._rgb_radio_observer, names=["value"])
        self._gamma_radio_button.observe(self._gamma_radio_observer, names=["value"])
        self._palette_radio_button.observe(
            self._palette_radio_observer, names=["value"]
        )

        super().__init__(
            layout=ipywidgets.Layout(
                padding="5px 0px 5px 8px",  # top, right, bottom, left
                # width="330px",
                max_height="305px",
                overflow="auto",
                display="block",
            ),
            children=children,
        )

    def _value_stretch_changed(self, value: Dict[str, Any]) -> None:
        """Apply the selected stretch option and update widget states.

        Args:
            value (Dict[str, Any]): The change event dictionary containing the new value.
        """
        stretch_option = value["new"]

        if stretch_option:
            self._stretch_button.disabled = False
            self._value_range_slider.disabled = True
            self._update_stretch()
        else:
            self._stretch_button.disabled = True
            self._value_range_slider.disabled = False

    def _update_stretch(self, *args: Any) -> None:
        """Calculate and set the range slider by applying stretch parameters."""
        stretch_params = self._stretch_dropdown.value

        (s, w), (n, e) = self._host_map.bounds
        map_bbox = ee.Geometry.BBox(west=w, south=s, east=e, north=n)
        vis_bands = set((b.value for b in self._bands_hbox.children))
        min_val, max_val = self._ee_layer.calculate_vis_minmax(
            bounds=map_bbox, bands=vis_bands, **stretch_params
        )

        # Update in the correct order to avoid setting an invalid range
        if min_val > self._value_range_slider.max:
            self._value_range_slider.max = max_val
            self._value_range_slider.min = min_val
        else:
            self._value_range_slider.min = min_val
            self._value_range_slider.max = max_val

        self._value_range_slider.value = [min_val, max_val]

    def _set_toolbar_layout(
        self, grayscale: bool, palette: bool
    ) -> List[ipywidgets.Widget]:
        """Sets the layout of the toolbar based on grayscale and palette options.

        Args:
            grayscale (bool): Whether the grayscale option is selected.
            palette (bool): Whether the palette option is selected.

        Returns:
            List[ipywidgets.Widget]: The list of toolbar widgets.
        """
        tools = [
            ipywidgets.HBox([self._grayscale_radio_button, self._rgb_radio_button]),
            self._bands_hbox,
            self._stretch_hbox,
            self._value_range_slider,
            self._opacity_slider,
        ]
        if grayscale:
            inner_tools = []
            # These options are only available in grayscale.
            inner_tools.append(
                ipywidgets.HBox([self._palette_radio_button, self._gamma_radio_button])
            )
            # Show palette options if palette is selected, otherwise show gamma option.
            if palette:
                inner_tools += [
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
            else:
                inner_tools.append(self._gamma_slider)
            tools.append(
                ipywidgets.VBox(
                    inner_tools,
                    layout=ipywidgets.Layout(
                        border="1px solid lightgray", margin="0 8px 0 0"
                    ),
                    padding="10px",
                )
            )
        else:
            # Palette option is not available in RGB mode.
            tools.append(self._gamma_slider)
        return tools

    def _get_colormaps(self) -> List[str]:
        """Gets the list of available colormaps.

        Returns:
            List[str]: The list of colormap names.
        """
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        colormap_options = pyplot.colormaps()
        colormap_options.sort()
        return colormap_options

    def _render_colorbar(self, colors: List[str]) -> None:
        """Renders a colorbar with the given colors.

        Args:
            colors (List[str]): The list of colors to use in the colorbar.
        """
        import matplotlib  # pylint: disable=import-outside-toplevel
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        colors = coreutils.to_hex_colors(colors)

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

    def _classes_changed(self, change: Dict[str, Any]) -> None:
        """Handles changes to the classes dropdown.

        Args:
            change (Dict[str, Any]): The change event dictionary.
        """
        import matplotlib  # pylint: disable=import-outside-toplevel
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        if not change["new"]:
            return

        selected = change["owner"].value
        if self._colormap_dropdown.value is not None:
            n_class = None
            if selected != "Any":
                n_class = int(self._classes_dropdown.value)

            colors = pyplot.get_cmap(self._colormap_dropdown.value, n_class)
            cmap_colors = [
                matplotlib.colors.rgb2hex(colors(i))[1:] for i in range(colors.N)
            ]
            self._render_colorbar(cmap_colors)

            if self._palette_label.value and "," in self._palette_label.value:
                labels = [
                    f"Class {i+1}"
                    for i in range(len(self._palette_label.value.split(",")))
                ]
                self._legend_labels_label.value = ", ".join(labels)

    def _add_color_clicked(self, _) -> None:
        """Handles the add color button click event."""
        if self._color_picker.value is not None:
            if self._palette_label.value:
                self._palette_label.value += ", " + self._color_picker.value[1:]
            else:
                self._palette_label.value = self._color_picker.value[1:]

    def _del_color_clicked(self, _) -> None:
        """Handles the delete color button click event."""
        if "," in self._palette_label.value:
            items = [item.strip() for item in self._palette_label.value.split(",")]
            self._palette_label.value = ", ".join(items[:-1])
        else:
            self._palette_label.value = ""

    def _reset_color_clicked(self, _) -> None:
        """Handles the reset color button click event."""
        self._palette_label.value = ""

    def _linear_checkbox_changed(self, change: Dict[str, Any]) -> None:
        """Handles changes to the linear checkbox.

        Args:
            change (Dict[str, Any]): The change event dictionary.
        """
        if change["new"]:
            self._step_checkbox.value = False
            self._legend_vbox.children = [self._colormap_hbox]
        else:
            self._step_checkbox.value = True

    def _step_checkbox_changed(self, change: Dict[str, Any]) -> None:
        """Handles changes to the step checkbox.

        Args:
            change (Dict[str, Any]): The change event dictionary.
        """
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

    def _colormap_changed(self, change: Dict[str, Any]) -> None:
        """Handles changes to the colormap dropdown.

        Args:
            change (Dict[str, Any]): The change event dictionary.
        """
        import matplotlib  # pylint: disable=import-outside-toplevel
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        if change["new"]:
            n_class = None
            if self._classes_dropdown.value != "Any":
                n_class = int(self._classes_dropdown.value)

            colors = pyplot.get_cmap(self._colormap_dropdown.value, n_class)
            cmap_colors = [
                matplotlib.colors.rgb2hex(colors(i))[1:] for i in range(colors.N)
            ]
            self._render_colorbar(cmap_colors)

            if self._palette_label.value and "," in self._palette_label.value:
                labels = [
                    f"Class {i+1}"
                    for i in range(len(self._palette_label.value.split(",")))
                ]
                self._legend_labels_label.value = ", ".join(labels)

    def _get_vis_params_from_selection(self) -> Dict[str, Any]:
        """Gets the visualization parameters from the current selection.

        Returns:
            Dict[str, Any]: The visualization parameters.
        """
        vis = {}
        if self._grayscale_radio_button.index == 0:
            vis["bands"] = [self._band_1_dropdown.value]
            if self._palette_radio_button.index == 0:
                if self._palette_label.value:
                    vis["palette"] = [
                        c.strip() for c in self._palette_label.value.split(",")
                    ]
            else:
                vis["gamma"] = self._gamma_slider.value
        else:
            vis["bands"] = [
                self._band_1_dropdown.value,
                self._band_2_dropdown.value,
                self._band_3_dropdown.value,
            ]
            vis["gamma"] = self._gamma_slider.value

        vis["min"] = self._value_range_slider.value[0]
        vis["max"] = self._value_range_slider.value[1]
        return vis

    def on_import_click(self) -> None:
        """Handles the import button click event."""
        vis = self._get_vis_params_from_selection()

        coreutils.create_code_cell(f"vis_params = {str(vis)}")
        print(f"vis_params = {str(vis)}")

    def on_apply_click(self) -> None:
        """Handles the apply button click event."""
        vis = self._get_vis_params_from_selection()
        self._host_map.add_layer(
            self._ee_object, vis, self._layer_name, True, self._opacity_slider.value
        )
        self._ee_layer.visible = False

        if self._legend_checkbox.value:
            palette_str = self._palette_label.value
            if self._linear_checkbox.value:
                if palette_str:
                    colors = _tokenize_legend_colors(palette_str)
                    if hasattr(self._host_map, "_add_colorbar"):
                        # pylint: disable-next=protected-access
                        self._host_map._add_colorbar(
                            vis_params={
                                "palette": colors,
                                "min": self._value_range_slider.value[0],
                                "max": self._value_range_slider.value[1],
                            },
                            layer_name=self._layer_name,
                        )
            elif self._step_checkbox.value:
                labels_str = self._legend_labels_label.value
                if palette_str and labels_str:
                    colors = _tokenize_legend_colors(palette_str)
                    labels = _tokenize_legend_labels(labels_str)
                    if hasattr(self._host_map, "_add_legend"):
                        # pylint: disable-next=protected-access
                        self._host_map._add_legend(
                            title=self._legend_title_label.value,
                            layer_name=self._layer_name,
                            keys=labels,
                            colors=colors,
                        )
        else:
            if self._grayscale_radio_button.index == 0 and "palette" in vis:
                self._render_colorbar(vis["palette"])

    def _legend_checkbox_changed(self, change: Dict[str, Any]) -> None:
        """Handles changes to the legend checkbox.

        Args:
            change (Dict[str, Any]): The change event dictionary.
        """
        if change["new"]:
            self._linear_checkbox.value = True
            self._legend_vbox.children = [
                ipywidgets.HBox([self._linear_checkbox, self._step_checkbox]),
            ]
        else:
            self._legend_vbox.children = []

    def _render_grayscale_rgb_selection(self, grayscale: bool) -> None:
        """Renders the grayscale or RGB selection.

        Args:
            grayscale (bool): Whether the grayscale option is selected.
        """
        if grayscale:
            self._rgb_radio_button.unobserve(self._rgb_radio_observer, names=["value"])
            self._rgb_radio_button.index = None
            self._rgb_radio_button.observe(self._rgb_radio_observer, names=["value"])
            self._band_1_dropdown.layout.width = "300px"
            self._bands_hbox.children = [self._band_1_dropdown]
        else:
            self._grayscale_radio_button.unobserve(
                self._grayscale_radio_observer, names=["value"]
            )
            self._grayscale_radio_button.index = None
            self._grayscale_radio_button.observe(
                self._grayscale_radio_observer, names=["value"]
            )
            self._band_1_dropdown.layout.width = "98px"
            self._bands_hbox.children = [
                self._band_1_dropdown,
                self._band_2_dropdown,
                self._band_3_dropdown,
            ]

    def _enable_palette(self, enabled: bool) -> None:
        """Enables or disables the palette options.

        Args:
            enabled (bool): Whether to enable the palette options.
        """
        if enabled and not self._palette_label.value:
            # Only set this if it hasn't been overridden. Note that if no
            # palette was originally set, then this will be left blank here.
            self._palette_label.value = ", ".join(self._layer_palette)
        self._palette_label.disabled = not enabled
        self._color_picker.disabled = not enabled
        self._add_color_button.disabled = not enabled
        self._del_color_button.disabled = not enabled
        self._reset_color_button.disabled = not enabled

    def _render_palette(self, enabled: bool) -> None:
        """Renders the palette if enabled.

        Args:
            enabled (bool): Whether to render the palette.
        """
        if enabled:
            if self._palette_label.value and "," in self._palette_label.value:
                colors = [
                    color.strip() for color in self._palette_label.value.split(",")
                ]
                self._render_colorbar(colors)
        else:
            self._colorbar_output.clear_output()

    def _grayscale_radio_observer(self, _) -> None:
        """Observer for the grayscale radio button."""
        self._render_grayscale_rgb_selection(True)
        self._enable_palette(True)
        palette_selected = self._palette_radio_button.index == 0
        self._render_palette(palette_selected)
        self.children = self._set_toolbar_layout(
            grayscale=True, palette=palette_selected
        )

    def _rgb_radio_observer(self, _) -> None:
        """Observer for the RGB radio button."""
        self._render_grayscale_rgb_selection(False)
        self._enable_palette(False)
        self._render_palette(False)
        self.children = self._set_toolbar_layout(grayscale=False, palette=False)

    def _render_gamma_palette_selection(self, gamma: bool) -> None:
        """Renders the gamma or palette selection.

        Args:
            gamma (bool): Whether the gamma option is selected.
        """
        if gamma:
            self._palette_radio_button.unobserve(
                self._palette_radio_observer, names=["value"]
            )
            self._palette_radio_button.index = None
            self._palette_radio_button.observe(
                self._palette_radio_observer, names=["value"]
            )
        else:
            self._gamma_radio_button.unobserve(
                self._gamma_radio_observer, names=["value"]
            )
            self._gamma_radio_button.index = None
            self._gamma_radio_button.observe(
                self._gamma_radio_observer, names=["value"]
            )

    def _gamma_radio_observer(self, _) -> None:
        """Observer for the gamma radio button."""
        self._render_gamma_palette_selection(True)
        self._enable_palette(False)
        self._render_palette(False)
        grayscale = self._grayscale_radio_button.index == 0
        self.children = self._set_toolbar_layout(grayscale=grayscale, palette=False)

    def _palette_radio_observer(self, _) -> None:
        """Observer for the palette radio button."""
        self._render_gamma_palette_selection(False)
        self._enable_palette(True)
        self._render_palette(True)
        grayscale = self._grayscale_radio_button.index == 0
        self.children = self._set_toolbar_layout(grayscale=grayscale, palette=True)


@Theme.apply
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
    def _layer_name(self) -> str:
        """Returns the name of the layer."""
        return self._ee_layer.name

    @property
    def _layer_opacity(self) -> float:
        """Returns the opacity of the layer."""
        return self._ee_layer.opacity

    def __init__(self, host_map: "geemap.Map", layer_dict: Dict[str, Any]):
        """Initializes a layer manager widget.

        Args:
            host_map (geemap.Map): The geemap.Map object.
            layer_dict (Dict[str, Any]): The layer object to edit.
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
            layout=ipywidgets.Layout(height="60px", width="300px")
        )

        is_point = coreutils.geometry_type(self._ee_object) in ["Point", "MultiPoint"]
        self._point_size_label.disabled = not is_point
        self._point_shape_dropdown.disabled = not is_point

        super().__init__(
            layout=ipywidgets.Layout(
                padding="5px 5px 5px 8px",
                # width="330px",
                max_height="250px",
                overflow="auto",
                display="block",
            ),
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

    def _get_vis_params(self) -> Dict[str, Any]:
        """Gets the visualization parameters for the layer.

        Returns:
            Dict[str, Any]: The visualization parameters.
        """
        vis = {}
        vis["color"] = self._color_picker.value[1:] + str(
            hex(int(self._color_opacity_slider.value * 255))
        )[2:].zfill(2)
        if coreutils.geometry_type(self._ee_object) in ["Point", "MultiPoint"]:
            vis["pointSize"] = self._point_size_label.value
            vis["pointShape"] = self._point_shape_dropdown.value
        vis["width"] = self._line_width_label.value
        vis["lineType"] = self._line_type_label.value
        vis["fillColor"] = self._fill_color_picker.value[1:] + str(
            hex(int(self._fill_color_opacity_slider.value * 255))
        )[2:].zfill(2)

        return vis

    def on_apply_click(self) -> None:
        """Handles the apply button click event."""
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
            self._compute_label.value = ""

        elif (
            self._style_chk.value
            and self._palette_label.value
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

                palette_str = self._palette_label.value
                labels_str = self._legend_labels_label.value
                if self._legend_checkbox.value and palette_str and labels_str:
                    colors = _tokenize_legend_colors(palette_str)
                    labels = _tokenize_legend_labels(labels_str)
                    if hasattr(self._host_map, "_add_legend"):
                        # pylint: disable-next=protected-access
                        self._host_map._add_legend(
                            title=self._legend_title_label.value,
                            layer_name=self._new_layer_name.value,
                            keys=labels,
                            colors=colors,
                        )
            except Exception as exc:
                self._compute_label.value = "Error: " + str(exc)

            self._ee_layer.visible = False
            self._compute_label.value = ""

    def _render_colorbar(self, colors: List[str]) -> None:
        """Renders a colorbar with the given colors.

        Args:
            colors (List[str]): The list of colors to use in the colorbar.
        """
        import matplotlib  # pylint: disable=import-outside-toplevel
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        colors = coreutils.to_hex_colors(colors)

        _, ax = pyplot.subplots(figsize=(4, 0.3))
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

    def _classes_changed(self, change: Dict[str, Any]) -> None:
        """Handles changes to the classes dropdown.

        Args:
            change (Dict[str, Any]): The change event dictionary.
        """
        import matplotlib  # pylint: disable=import-outside-toplevel
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        if change["new"]:
            selected = change["owner"].value
            if self._colormap_dropdown.value is not None:
                n_class = None
                if selected != "Any":
                    n_class = int(self._classes_dropdown.value)

                colors = pyplot.get_cmap(self._colormap_dropdown.value, n_class)
                cmap_colors = [
                    matplotlib.colors.rgb2hex(colors(i))[1:] for i in range(colors.N)
                ]
                self._render_colorbar(cmap_colors)

                if self._palette_label.value and "," in self._palette_label.value:
                    labels = [
                        f"Class {i+1}"
                        for i in range(len(self._palette_label.value.split(",")))
                    ]
                    self._legend_labels_label.value = ", ".join(labels)

    def _colormap_changed(self, change: Dict[str, Any]) -> None:
        """Handles changes to the colormap dropdown.

        Args:
            change (Dict[str, Any]): The change event dictionary.
        """
        import matplotlib  # pylint: disable=import-outside-toplevel
        from matplotlib import pyplot  # pylint: disable=import-outside-toplevel

        if change["new"]:
            n_class = None
            if self._classes_dropdown.value != "Any":
                n_class = int(self._classes_dropdown.value)

            colors = pyplot.get_cmap(self._colormap_dropdown.value, n_class)
            cmap_colors = [
                matplotlib.colors.rgb2hex(colors(i))[1:] for i in range(colors.N)
            ]
            self._render_colorbar(cmap_colors)

            if self._palette_label.value and "," in self._palette_label.value:
                labels = [
                    f"Class {i+1}"
                    for i in range(len(self._palette_label.value.split(",")))
                ]
                self._legend_labels_label.value = ", ".join(labels)

    def _fill_color_opacity_change(self, change: Dict[str, Any]) -> None:
        """Handles changes to the fill color opacity slider.

        Args:
            change (Dict[str, Any]): The change event dictionary.
        """
        self._fill_color_opacity_label.value = str(change["new"])

    def _color_opacity_change(self, change: Dict[str, Any]) -> None:
        """Handles changes to the color opacity slider.

        Args:
            change (Dict[str, Any]): The change event dictionary.
        """
        self._color_opacity_label.value = str(change["new"])

    def _add_color_clicked(self, _) -> None:
        """Handles the add color button click event."""
        if self._color_picker.value is not None:
            if self._palette_label.value:
                self._palette_label.value += ", " + self._color_picker.value[1:]
            else:
                self._palette_label.value = self._color_picker.value[1:]

    def _del_color_clicked(self, _) -> None:
        """Handles the delete color button click event."""
        if "," in self._palette_label.value:
            items = [item.strip() for item in self._palette_label.value.split(",")]
            self._palette_label.value = ", ".join(items[:-1])
        else:
            self._palette_label.value = ""

    def _reset_color_clicked(self, _) -> None:
        """Handles the reset color button click event."""
        self._palette_label.value = ""

    def _style_chk_changed(self, change: Dict[str, Any]) -> None:
        """Handles changes to the style checkbox.

        Args:
            change (Dict[str, Any]): The change event dictionary.
        """
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

    def _legend_chk_changed(self, change: Dict[str, Any]) -> None:
        """Handles changes to the legend checkbox.

        Args:
            change (Dict[str, Any]): The change event dictionary.
        """
        if change["new"]:
            self._style_vbox.children = list(self._style_vbox.children) + [
                ipywidgets.VBox([self._legend_title_label, self._legend_labels_label])
            ]

            if self._palette_label.value and "," in self._palette_label.value:
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

    def _field_changed(self, change: Dict[str, Any]) -> None:
        """Handles changes to the field dropdown.

        Args:
            change (Dict[str, Any]): The change event dictionary.
        """
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

    def on_import_click(self) -> None:
        """Handles the import button click event."""
        vis = self._get_vis_params()
        coreutils.create_code_cell(f"style = {str(vis)}")
        print(f"style = {str(vis)}")
