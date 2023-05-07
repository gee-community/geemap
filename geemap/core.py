"""This is a core module for using the Earth Engine Python API with ipyleaflet.
"""

import os

import ee
import ipyevents
import ipyleaflet
import ipywidgets as widgets

from box import Box
from bqplot import pyplot as plt
from ipyfilechooser import FileChooser
from IPython.display import display
from ipytree import Node, Tree
from .basemaps import xyz_to_leaflet
from .common import *
from .conversion import *
from .timelapse import *
from .plot import *

from . import examples

basemaps = Box(xyz_to_leaflet(), frozen_box=True)


class Map(ipyleaflet.Map):
    """The Map class inherits from ipyleaflet.Map. The arguments you can pass to the Map
        can be found at https://ipyleaflet.readthedocs.io/en/latest/map_and_basemaps/map.html.
        By default, the Map will add Google Maps as the basemap. Set add_google_map = False
        to use OpenStreetMap as the basemap.

    Returns:
        object: ipyleaflet map object.
    """

    def __init__(self, **kwargs):
        # Authenticates Earth Engine and initializes an Earth Engine session
        if "ee_initialize" not in kwargs.keys():
            kwargs["ee_initialize"] = True

        if kwargs["ee_initialize"]:
            ee_initialize()

        # Default map center location (lat, lon) and zoom level
        center = [20, 0]
        zoom = 2

        # Set map width and height
        if "height" not in kwargs.keys():
            kwargs["height"] = "600px"
        elif isinstance(kwargs["height"], int):
            kwargs["height"] = str(kwargs["height"]) + "px"
        if "width" in kwargs.keys() and isinstance(kwargs["width"], int):
            kwargs["width"] = str(kwargs["width"]) + "px"

        # Set map center location and zoom level
        if "center" not in kwargs.keys():
            kwargs["center"] = center
        if "zoom" not in kwargs.keys():
            kwargs["zoom"] = zoom
        if "max_zoom" not in kwargs.keys():
            kwargs["max_zoom"] = 24

        # Enable scroll wheel zoom by default
        if "scroll_wheel_zoom" not in kwargs.keys():
            kwargs["scroll_wheel_zoom"] = True

        # Add Google Maps as the default basemap
        if "add_google_map" not in kwargs.keys() and "basemap" not in kwargs.keys():
            kwargs["add_google_map"] = True

        # Users can also specify any basemap from the basemap module, such as OpenTopoMap
        if (
            "basemap" in kwargs.keys()
            and isinstance(kwargs["basemap"], str)
            and kwargs["basemap"] in basemaps.keys()
        ):
            kwargs["basemap"] = basemaps[kwargs["basemap"]]

        # Available controls. The first two are custom controls. The rest are native ipyleaflet controls.
        controls = [
            "data_ctrl",
            "toolbar_ctrl",
            "zoom_ctrl",
            "fullscreen_ctrl",
            "draw_ctrl",
            "search_ctrl",
            "measure_ctrl",
            "scale_ctrl",
            "layer_ctrl",
            "attribution_ctrl",
        ]

        if "lite_mode" not in kwargs.keys():
            kwargs["lite_mode"] = False
        # Hide all controls if lite_mode is True
        if kwargs["lite_mode"]:
            for control in controls:
                kwargs[control] = False

        # Controls to be displayed by default
        for control in controls:
            if control not in kwargs.keys():
                if control in ["search_ctrl", "layer_ctrl"]:
                    kwargs[control] = False
                else:
                    kwargs[control] = True

        # Inherits the ipyleaflet Map class
        super().__init__(**kwargs)
        self.layout.height = kwargs["height"]
        if "width" in kwargs:
            self.layout.width = kwargs["width"]

        # sandbox path for Voila app to restrict access to system directories.
        if "sandbox_path" in kwargs:
            self.sandbox_path = kwargs["sandbox_path"]
        elif os.environ.get("SANDBOX_PATH") is not None:
            self.sandbox_path = os.environ.get("SANDBOX_PATH")
        else:
            self.sandbox_path = None

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

        self.search_locations = None
        self.search_loc_marker = None
        self.search_loc_geom = None
        self.search_datasets = None
        self.screenshot = None
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

        search_marker = ipyleaflet.Marker(
            icon=ipyleaflet.AwesomeIcon(
                name="check", marker_color="green", icon_color="darkgreen"
            )
        )
        search = ipyleaflet.SearchControl(
            position="topleft",
            url="https://nominatim.openstreetmap.org/search?format=json&q={s}",
            zoom=5,
            property_name="display_name",
            marker=search_marker,
        )
        if kwargs.get("search_ctrl"):
            self.add_control(search)

        if kwargs.get("zoom_ctrl"):
            self.add_control(ipyleaflet.ZoomControl(position="topleft"))

        if kwargs.get("layer_ctrl"):
            layer_control = ipyleaflet.LayersControl(position="topright")
            self.layer_control = layer_control
            self.add_control(layer_control)

        if kwargs.get("scale_ctrl"):
            scale = ipyleaflet.ScaleControl(position="bottomleft")
            self.scale_control = scale
            self.add_control(scale)

        if kwargs.get("fullscreen_ctrl"):
            fullscreen = ipyleaflet.FullScreenControl()
            self.fullscreen_control = fullscreen
            self.add_control(fullscreen)

        if kwargs.get("measure_ctrl"):
            measure = ipyleaflet.MeasureControl(
                position="bottomleft",
                active_color="orange",
                primary_length_unit="kilometers",
            )
            self.measure_control = measure
            self.add_control(measure)

        if kwargs.get("add_google_map"):
            self.add_layer(basemaps["ROADMAP"])

        if kwargs.get("attribution_ctrl"):
            self.add_control(ipyleaflet.AttributionControl(position="bottomright"))

        draw_control = ipyleaflet.DrawControl(
            marker={"shapeOptions": {"color": "#3388ff"}},
            rectangle={"shapeOptions": {"color": "#3388ff"}},
            circle={"shapeOptions": {"color": "#3388ff"}},
            circlemarker={},
            edit=True,
            remove=True,
        )

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
                    self.add_layer(ee_draw_layer)
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
        if kwargs.get("draw_ctrl"):
            self.add_control(draw_control)
        self.draw_control = draw_control
        self.draw_control_lite = draw_control_lite

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
        self.inspector_checked = False

        inspector_output = widgets.Output(
            layout={
                "border": "1px solid black",
                "max_width": "600px",
                "max_height": "530px",
                "overflow": "auto",
            }
        )
        inspector_output_control = ipyleaflet.WidgetControl(
            widget=inspector_output,
            position="topright",
        )
        tool_output = widgets.Output()
        self.tool_output = tool_output
        tool_output.clear_output(wait=True)
        save_map_widget = widgets.VBox()

        save_type = widgets.ToggleButtons(
            options=["HTML", "PNG", "JPG"],
            tooltips=[
                "Save the map as an HTML file",
                "Take a screenshot and save as a PNG file",
                "Take a screenshot and save as a JPG file",
            ],
        )

        file_chooser = FileChooser(os.getcwd(), sandbox_path=self.sandbox_path)
        file_chooser.default_filename = "my_map.html"
        file_chooser.use_dir_icons = True

        ok_cancel = widgets.ToggleButtons(
            value=None,
            options=["OK", "Cancel"],
            tooltips=["OK", "Cancel"],
            button_style="primary",
        )

        def save_type_changed(change):
            ok_cancel.value = None
            # file_chooser.reset()
            file_chooser.default_path = os.getcwd()
            if change["new"] == "HTML":
                file_chooser.default_filename = "my_map.html"
            elif change["new"] == "PNG":
                file_chooser.default_filename = "my_map.png"
            elif change["new"] == "JPG":
                file_chooser.default_filename = "my_map.jpg"
            save_map_widget.children = [save_type, file_chooser]

        def chooser_callback(chooser):
            save_map_widget.children = [save_type, file_chooser, ok_cancel]

        def ok_cancel_clicked(change):
            import time

            if change["new"] == "OK":
                file_path = file_chooser.selected
                ext = os.path.splitext(file_path)[1]
                if save_type.value == "HTML" and ext.upper() == ".HTML":
                    tool_output.clear_output()
                    self.to_html(file_path)
                elif save_type.value == "PNG" and ext.upper() == ".PNG":
                    tool_output.clear_output()
                    self.toolbar_button.value = False
                    time.sleep(1)
                    screen_capture(filename=file_path)
                elif save_type.value == "JPG" and ext.upper() == ".JPG":
                    tool_output.clear_output()
                    self.toolbar_button.value = False
                    time.sleep(1)
                    screen_capture(filename=file_path)
                else:
                    label = widgets.Label(
                        value="The selected file extension does not match the selected exporting type."
                    )
                    save_map_widget.children = [save_type, file_chooser, label]
                self.toolbar_reset()
            elif change["new"] == "Cancel":
                tool_output.clear_output()
                self.toolbar_reset()

        save_type.observe(save_type_changed, names="value")
        ok_cancel.observe(ok_cancel_clicked, names="value")

        file_chooser.register_callback(chooser_callback)

        save_map_widget.children = [save_type, file_chooser]

        tools = {
            "info": {"name": "inspector", "tooltip": "Inspector"},
            "bar-chart": {"name": "plotting", "tooltip": "Plotting"},
            "camera": {
                "name": "to_image",
                "tooltip": "Save map as HTML or image",
            },
            "eraser": {
                "name": "eraser",
                "tooltip": "Remove all drawn features",
            },
            "folder-open": {
                "name": "open_data",
                "tooltip": "Open local vector/raster data",
            },
            # "cloud-download": {
            #     "name": "export_data",
            #     "tooltip": "Export Earth Engine data",
            # },
            "retweet": {
                "name": "convert_js",
                "tooltip": "Convert Earth Engine JavaScript to Python",
            },
            "gears": {
                "name": "whitebox",
                "tooltip": "WhiteboxTools for local geoprocessing",
            },
            "google": {
                "name": "geetoolbox",
                "tooltip": "GEE Toolbox for cloud computing",
            },
            "map": {
                "name": "basemap",
                "tooltip": "Change basemap",
            },
            "globe": {
                "name": "timelapse",
                "tooltip": "Create timelapse",
            },
            "fast-forward": {
                "name": "timeslider",
                "tooltip": "Activate timeslider",
            },
            "hand-o-up": {
                "name": "draw",
                "tooltip": "Collect training samples",
            },
            "line-chart": {
                "name": "transect",
                "tooltip": "Creating and plotting transects",
            },
            "random": {
                "name": "sankee",
                "tooltip": "Sankey plots",
            },
            "adjust": {
                "name": "planet",
                "tooltip": "Planet imagery",
            },
            "info-circle": {
                "name": "cog-inspector",
                "tooltip": "Get COG/STAC pixel value",
            },
            "spinner": {
                "name": "placehold2",
                "tooltip": "This is a placehold",
            },
            "question": {
                "name": "help",
                "tooltip": "Get help",
            },
        }

        # if kwargs["use_voila"]:
        #     voila_tools = ["camera", "folder-open", "cloud-download", "gears"]

        #     for item in voila_tools:
        #         if item in tools.keys():
        #             del tools[item]

        icons = list(tools.keys())
        tooltips = [item["tooltip"] for item in list(tools.values())]

        icon_width = "32px"
        icon_height = "32px"
        n_cols = 3
        # n_rows = math.ceil(len(icons) / n_cols)
        n_rows = -int(-(len(icons) / n_cols))

        toolbar_grid = widgets.GridBox(
            children=[
                widgets.ToggleButton(
                    layout=widgets.Layout(
                        width="auto", height="auto", padding="0px 0px 0px 4px"
                    ),
                    button_style="primary",
                    icon=icons[i],
                    tooltip=tooltips[i],
                )
                for i in range(len(icons))
            ],
            layout=widgets.Layout(
                width="109px",
                grid_template_columns=(icon_width + " ") * n_cols,
                grid_template_rows=(icon_height + " ") * n_rows,
                grid_gap="1px 1px",
                padding="5px",
            ),
        )
        self.toolbar = toolbar_grid

        def tool_callback(change):
            if change["new"]:
                current_tool = change["owner"]
                for tool in toolbar_grid.children:
                    if tool is not current_tool:
                        tool.value = False
                tool = change["owner"]
                tool_name = tools[tool.icon]["name"]
                if tool_name == "to_image":
                    if tool_output_control not in self.controls:
                        self.add_control(tool_output_control)
                    with tool_output:
                        tool_output.clear_output()
                        display(save_map_widget)
                elif tool_name == "eraser":
                    self.remove_drawn_features()
                    tool.value = False
                elif tool_name == "inspector":
                    self.inspector_checked = tool.value
                    if not self.inspector_checked:
                        inspector_output.clear_output()
                elif tool_name == "plotting":
                    self.plot_checked = True
                    plot_dropdown_widget = widgets.Dropdown(
                        options=list(self.ee_raster_layer_names),
                    )
                    plot_dropdown_widget.layout.width = "18ex"
                    self.plot_dropdown_widget = plot_dropdown_widget
                    plot_dropdown_control = ipyleaflet.WidgetControl(
                        widget=plot_dropdown_widget, position="topright"
                    )
                    self.plot_dropdown_control = plot_dropdown_control
                    self.add_control(plot_dropdown_control)
                    if self.draw_control in self.controls:
                        self.remove_control(self.draw_control)
                    self.add_control(self.draw_control_lite)
                elif tool_name == "open_data":
                    from .toolbar import open_data_widget

                    open_data_widget(self)
                elif tool_name == "convert_js":
                    from .toolbar import convert_js2py

                    convert_js2py(self)
                elif tool_name == "whitebox":
                    import whiteboxgui.whiteboxgui as wbt

                    tools_dict = wbt.get_wbt_dict()
                    wbt_toolbox = wbt.build_toolbox(
                        tools_dict,
                        max_width="800px",
                        max_height="500px",
                        sandbox_path=self.sandbox_path,
                    )
                    wbt_control = ipyleaflet.WidgetControl(
                        widget=wbt_toolbox, position="bottomright"
                    )
                    self.whitebox = wbt_control
                    self.add_control(wbt_control)
                elif tool_name == "geetoolbox":
                    from .toolbar import build_toolbox, get_tools_dict

                    tools_dict = get_tools_dict()
                    gee_toolbox = build_toolbox(
                        tools_dict, max_width="800px", max_height="500px"
                    )
                    geetoolbox_control = ipyleaflet.WidgetControl(
                        widget=gee_toolbox, position="bottomright"
                    )
                    self.geetoolbox = geetoolbox_control
                    self.add_control(geetoolbox_control)

                elif tool_name == "basemap":
                    from .toolbar import change_basemap

                    change_basemap(self)
                elif tool_name == "timelapse":
                    from .toolbar import timelapse_gui

                    timelapse_gui(self)
                    self.toolbar_reset()
                elif tool_name == "timeslider":
                    from .toolbar import time_slider

                    time_slider(self)
                    self.toolbar_reset()
                elif tool_name == "draw":
                    from .toolbar import collect_samples

                    self.training_ctrl = None
                    collect_samples(self)
                elif tool_name == "transect":
                    from .toolbar import plot_transect

                    plot_transect(self)
                elif tool_name == "sankee":
                    from .toolbar import sankee_gui

                    sankee_gui(self)
                elif tool_name == "planet":
                    from .toolbar import split_basemaps

                    split_basemaps(self, layers_dict=planet_tiles())
                    self.toolbar_reset()
                elif tool_name == "cog-inspector":
                    from .toolbar import inspector_gui

                    inspector_gui(self)

                elif tool_name == "help":
                    import webbrowser

                    webbrowser.open_new_tab("https://geemap.org")
                    current_tool.value = False
            else:
                tool = change["owner"]
                tool_name = tools[tool.icon]["name"]
                if tool_name == "to_image":
                    tool_output.clear_output()
                    save_map_widget.children = [save_type, file_chooser]
                    if tool_output_control in self.controls:
                        self.remove_control(tool_output_control)
                if tool_name == "inspector":
                    inspector_output.clear_output()
                    self.inspector_checked = False
                    if inspector_output_control in self.controls:
                        self.remove_control(inspector_output_control)
                elif tool_name == "plotting":
                    self.plot_checked = False
                    plot_dropdown_widget = self.plot_dropdown_widget
                    plot_dropdown_control = self.plot_dropdown_control
                    if plot_dropdown_control in self.controls:
                        self.remove_control(plot_dropdown_control)
                    del plot_dropdown_widget
                    del plot_dropdown_control
                    if self.plot_control in self.controls:
                        plot_control = self.plot_control
                        plot_widget = self.plot_widget
                        self.remove_control(plot_control)
                        self.plot_control = None
                        self.plot_widget = None
                        del plot_control
                        del plot_widget
                    if (
                        self.plot_marker_cluster is not None
                        and self.plot_marker_cluster in self.layers
                    ):
                        self.remove_layer(self.plot_marker_cluster)
                    if self.draw_control_lite in self.controls:
                        self.remove_control(self.draw_control_lite)
                    self.add_control(self.draw_control)
                elif tool_name == "whitebox":
                    if self.whitebox is not None and self.whitebox in self.controls:
                        self.remove_control(self.whitebox)
                elif tool_name == "convert_js":
                    if (
                        self.convert_ctrl is not None
                        and self.convert_ctrl in self.controls
                    ):
                        self.remove_control(self.convert_ctrl)

        for tool in toolbar_grid.children:
            tool.observe(tool_callback, "value")

        toolbar_button = widgets.ToggleButton(
            value=False,
            tooltip="Toolbar",
            icon="wrench",
            layout=widgets.Layout(
                width="28px", height="28px", padding="0px 0px 0px 4px"
            ),
        )
        self.toolbar_button = toolbar_button

        layers_button = widgets.ToggleButton(
            value=False,
            tooltip="Layers",
            icon="server",
            layout=widgets.Layout(height="28px", width="72px"),
        )

        toolbar_widget = widgets.VBox()
        toolbar_widget.children = [toolbar_button]
        toolbar_header = widgets.HBox()
        toolbar_header.children = [layers_button, toolbar_button]
        toolbar_footer = widgets.VBox()
        toolbar_footer.children = [toolbar_grid]

        toolbar_event = ipyevents.Event(
            source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
        )

        def handle_toolbar_event(event):
            if event["type"] == "mouseenter":
                toolbar_widget.children = [toolbar_header, toolbar_footer]
            elif event["type"] == "mouseleave":
                if not toolbar_button.value:
                    toolbar_widget.children = [toolbar_button]
                    toolbar_button.value = False
                    layers_button.value = False

        toolbar_event.on_dom_event(handle_toolbar_event)

        def toolbar_btn_click(change):
            if change["new"]:
                layers_button.value = False
                toolbar_widget.children = [toolbar_header, toolbar_footer]
            else:
                if not layers_button.value:
                    toolbar_widget.children = [toolbar_button]

        toolbar_button.observe(toolbar_btn_click, "value")

        def layers_btn_click(change):
            if change["new"]:
                layers_hbox = []
                all_layers_chk = widgets.Checkbox(
                    value=False,
                    description="All layers on/off",
                    indent=False,
                    layout=widgets.Layout(height="18px", padding="0px 8px 25px 8px"),
                )
                all_layers_chk.layout.width = "30ex"
                layers_hbox.append(all_layers_chk)

                def all_layers_chk_changed(change):
                    if change["new"]:
                        for layer in self.layers:
                            if hasattr(layer, "visible"):
                                layer.visible = True
                    else:
                        for layer in self.layers:
                            if hasattr(layer, "visible"):
                                layer.visible = False

                all_layers_chk.observe(all_layers_chk_changed, "value")

                layers = [
                    lyr
                    for lyr in self.layers[1:]
                    # if (
                    #     isinstance(lyr, ipyleaflet.TileLayer)
                    #     or isinstance(lyr, ipyleaflet.WMSLayer)
                    # )
                ]

                # if the layers contain unsupported layers (e.g., GeoJSON, GeoData), adds the ipyleaflet built-in LayerControl
                if len(layers) < (len(self.layers) - 1):
                    if self.layer_control is None:
                        layer_control = ipyleaflet.LayersControl(position="topright")
                        self.layer_control = layer_control
                    if self.layer_control not in self.controls:
                        self.add_control(self.layer_control)

                # for non-TileLayer, use layer.style={'opacity':0, 'fillOpacity': 0} to turn layer off.
                for layer in layers:
                    visible = True
                    if hasattr(layer, "visible"):
                        visible = layer.visible
                    layer_chk = widgets.Checkbox(
                        value=visible,
                        description=layer.name,
                        indent=False,
                        layout=widgets.Layout(height="18px"),
                    )
                    layer_chk.layout.width = "25ex"

                    if layer in self.geojson_layers:
                        try:
                            opacity = max(
                                layer.style["opacity"], layer.style["fillOpacity"]
                            )
                        except KeyError:
                            opacity = 1.0
                    else:
                        if hasattr(layer, "opacity"):
                            opacity = layer.opacity

                    layer_opacity = widgets.FloatSlider(
                        value=opacity,
                        min=0,
                        max=1,
                        step=0.01,
                        readout=False,
                        layout=widgets.Layout(width="80px"),
                    )
                    layer_settings = widgets.ToggleButton(
                        icon="gear",
                        tooltip=layer.name,
                        layout=widgets.Layout(
                            width="25px", height="25px", padding="0px 0px 0px 5px"
                        ),
                    )

                    def layer_opacity_changed(change):
                        if change["new"]:
                            layer.style = {
                                "opacity": change["new"],
                                "fillOpacity": change["new"],
                            }

                    def layer_vis_on_click(change):
                        if change["new"]:
                            layer_name = change["owner"].tooltip
                            # if layer_name in self.ee_raster_layer_names:
                            if layer_name in self.ee_layer_names:
                                layer_dict = self.ee_layer_dict[layer_name]

                                if self.vis_widget is not None:
                                    self.vis_widget = None
                                self.vis_widget = self.create_vis_widget(layer_dict)
                                if self.vis_control in self.controls:
                                    self.remove_control(self.vis_control)
                                    self.vis_control = None
                                vis_control = ipyleaflet.WidgetControl(
                                    widget=self.vis_widget, position="topright"
                                )
                                self.add_control((vis_control))
                                self.vis_control = vis_control
                            else:
                                if self.vis_widget is not None:
                                    self.vis_widget = None
                                if self.vis_control is not None:
                                    if self.vis_control in self.controls:
                                        self.remove_control(self.vis_control)
                                    self.vis_control = None
                            change["owner"].value = False

                    layer_settings.observe(layer_vis_on_click, "value")

                    def layer_chk_changed(change):
                        layer_name = change["owner"].description
                        if layer_name in self.ee_layer_names:
                            if change["new"]:
                                if "legend" in self.ee_layer_dict[layer_name].keys():
                                    legend = self.ee_layer_dict[layer_name]["legend"]
                                    if legend not in self.controls:
                                        self.add_control(legend)
                                if "colorbar" in self.ee_layer_dict[layer_name].keys():
                                    colorbar = self.ee_layer_dict[layer_name][
                                        "colorbar"
                                    ]
                                    if colorbar not in self.controls:
                                        self.add_control(colorbar)
                            else:
                                if "legend" in self.ee_layer_dict[layer_name].keys():
                                    legend = self.ee_layer_dict[layer_name]["legend"]
                                    if legend in self.controls:
                                        self.remove_control(legend)
                                if "colorbar" in self.ee_layer_dict[layer_name].keys():
                                    colorbar = self.ee_layer_dict[layer_name][
                                        "colorbar"
                                    ]
                                    if colorbar in self.controls:
                                        self.remove_control(colorbar)

                    layer_chk.observe(layer_chk_changed, "value")

                    if hasattr(layer, "visible"):
                        widgets.jslink((layer_chk, "value"), (layer, "visible"))

                    if layer in self.geojson_layers:
                        layer_opacity.observe(layer_opacity_changed, "value")
                    elif hasattr(layer, "opacity"):
                        widgets.jsdlink((layer_opacity, "value"), (layer, "opacity"))
                    hbox = widgets.HBox(
                        [layer_chk, layer_settings, layer_opacity],
                        layout=widgets.Layout(padding="0px 8px 0px 8px"),
                    )
                    layers_hbox.append(hbox)

                toolbar_footer.children = layers_hbox
                toolbar_button.value = False
            else:
                toolbar_footer.children = [toolbar_grid]

        layers_button.observe(layers_btn_click, "value")
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if kwargs.get("toolbar_ctrl"):
            self.add_control(toolbar_control)
            self.toolbar_ctrl = toolbar_control

        tool_output_control = ipyleaflet.WidgetControl(
            widget=tool_output, position="topright"
        )
        # self.add_control(tool_output_control)

        expand_label = widgets.Label(
            "Expand   ",
            layout=widgets.Layout(padding="0px 0px 0px 4px"),
        )

        expand_point = widgets.Checkbox(
            description="Point",
            indent=False,
            value=self._expand_point,
            layout=widgets.Layout(width="65px"),
        )

        expand_pixels = widgets.Checkbox(
            description="Pixels",
            indent=False,
            value=self._expand_pixels,
            layout=widgets.Layout(width="65px"),
        )

        expand_objects = widgets.Checkbox(
            description="Objects",
            indent=False,
            value=self._expand_objects,
            layout=widgets.Layout(width="70px"),
        )

        def expand_point_changed(change):
            self._expand_point = change["new"]

        def expand_pixels_changed(change):
            self._expand_pixels = change["new"]

        def expand_objects_changed(change):
            self._expand_objects = change["new"]

        expand_point.observe(expand_point_changed, "value")
        expand_pixels.observe(expand_pixels_changed, "value")
        expand_objects.observe(expand_objects_changed, "value")

        inspector_checks = widgets.HBox()
        inspector_checks.children = [
            expand_label,
            widgets.Label(""),
            expand_point,
            expand_pixels,
            expand_objects,
        ]

        def handle_interaction(**kwargs):
            latlon = kwargs.get("coordinates")
            if kwargs.get("type") == "click" and self.inspector_checked:
                self.default_style = {"cursor": "wait"}
                if inspector_output_control not in self.controls:
                    self.add_control(inspector_output_control)
                sample_scale = self.getScale()
                layers = self.ee_layers

                with inspector_output:
                    inspector_output.clear_output(wait=True)
                    display(inspector_checks)
                    display(self.inspector(latlon))

                self.default_style = {"cursor": "crosshair"}
            if (
                kwargs.get("type") == "click"
                and self.plot_checked
                and len(self.ee_raster_layers) > 0
            ):
                plot_layer_name = self.plot_dropdown_widget.value
                layer_names = self.ee_raster_layer_names
                layers = self.ee_raster_layers
                index = layer_names.index(plot_layer_name)
                ee_object = layers[index]

                if isinstance(ee_object, ee.ImageCollection):
                    ee_object = ee_object.mosaic()

                try:
                    self.default_style = {"cursor": "wait"}
                    plot_options = self.plot_options
                    sample_scale = self.getScale()
                    if "sample_scale" in plot_options.keys() and (
                        plot_options["sample_scale"] is not None
                    ):
                        sample_scale = plot_options["sample_scale"]
                    if "title" not in plot_options.keys():
                        plot_options["title"] = plot_layer_name
                    if ("add_marker_cluster" in plot_options.keys()) and plot_options[
                        "add_marker_cluster"
                    ]:
                        plot_coordinates = self.plot_coordinates
                        markers = self.plot_markers
                        marker_cluster = self.plot_marker_cluster
                        plot_coordinates.append(latlon)
                        self.plot_last_click = latlon
                        self.plot_all_clicks = plot_coordinates
                        markers.append(ipyleaflet.Marker(location=latlon))
                        marker_cluster.markers = markers
                        self.plot_marker_cluster = marker_cluster

                    band_names = ee_object.bandNames().getInfo()
                    if any(len(name) > 3 for name in band_names):
                        band_names = list(range(1, len(band_names) + 1))

                    self.chart_labels = band_names

                    if self.roi_end:
                        if self.roi_reducer_scale is None:
                            scale = ee_object.select(0).projection().nominalScale()
                        else:
                            scale = self.roi_reducer_scale
                        dict_values_tmp = ee_object.reduceRegion(
                            reducer=self.roi_reducer,
                            geometry=self.user_roi,
                            scale=scale,
                            bestEffort=True,
                        ).getInfo()
                        b_names = ee_object.bandNames().getInfo()
                        dict_values = dict(
                            zip(b_names, [dict_values_tmp[b] for b in b_names])
                        )
                        self.chart_points.append(
                            self.user_roi.centroid(1).coordinates().getInfo()
                        )
                    else:
                        xy = ee.Geometry.Point(latlon[::-1])
                        dict_values_tmp = (
                            ee_object.sample(xy, scale=sample_scale)
                            .first()
                            .toDictionary()
                            .getInfo()
                        )
                        b_names = ee_object.bandNames().getInfo()
                        dict_values = dict(
                            zip(b_names, [dict_values_tmp[b] for b in b_names])
                        )
                        self.chart_points.append(xy.coordinates().getInfo())
                    band_values = list(dict_values.values())
                    self.chart_values.append(band_values)
                    self.plot(band_names, band_values, **plot_options)
                    if plot_options["title"] == plot_layer_name:
                        del plot_options["title"]
                    self.default_style = {"cursor": "crosshair"}
                    self.roi_end = False
                except Exception as e:
                    if self.plot_widget is not None:
                        with self.plot_widget:
                            self.plot_widget.clear_output()
                            print("No data for the clicked location.")
                    else:
                        print(e)
                    self.default_style = {"cursor": "crosshair"}
                    self.roi_end = False

        self.on_interaction(handle_interaction)
