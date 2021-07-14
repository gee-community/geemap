"""Module for dealing with the toolbar.
"""
import os

import ee
import ipyevents
import ipyleaflet
import ipywidgets as widgets
from ipyfilechooser import FileChooser
from IPython.core.display import display

from .common import *


def tool_template(m=None):

    widget_width = "250px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="gear",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    checkbox = widgets.Checkbox(
        description="Checkbox",
        indent=False,
        layout=widgets.Layout(padding=padding, width=widget_width),
    )

    dropdown = widgets.Dropdown(
        options=["Option 1", "Option 2", "Option 3"],
        value=None,
        description="Dropdown:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style={"description_width": "initial"},
    )

    int_slider = widgets.IntSlider(
        min=1,
        max=100,
        description="Int Slider: ",
        readout=False,
        continuous_update=True,
        layout=widgets.Layout(width="220px", padding=padding),
        style={"description_width": "initial"},
    )

    int_slider_label = widgets.Label()
    widgets.jslink((int_slider, "value"), (int_slider_label, "value"))

    float_slider = widgets.FloatSlider(
        min=1,
        max=100,
        description="Float Slider: ",
        readout=False,
        continuous_update=True,
        layout=widgets.Layout(width="220px", padding=padding),
        style={"description_width": "initial"},
    )

    float_slider_label = widgets.Label()
    widgets.jslink((float_slider, "value"), (float_slider_label, "value"))

    color = widgets.ColorPicker(
        concise=False,
        description="Color:",
        value="white",
        style={"description_width": "initial"},
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    text = widgets.Text(
        value="",
        description="Textbox:",
        placeholder="Placeholder",
        style={"description_width": "initial"},
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    textarea = widgets.Textarea(
        placeholder="Placeholder",
        layout=widgets.Layout(width=widget_width),
    )

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Apply", "Reset", "Close"],
        tooltips=["Apply", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "80px"

    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        checkbox,
        widgets.HBox([int_slider, int_slider_label]),
        widgets.HBox([float_slider, float_slider_label]),
        dropdown,
        text,
        color,
        textarea,
        buttons,
        output,
    ]

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
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Apply":
            with output:
                output.clear_output()
                print("Running ...")
        elif change["new"] == "Reset":
            textarea.value = ""
            output.clear_output()
        elif change["new"] == "Close":
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = True
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add_control(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget


def open_data_widget(m):
    """A widget for opening local vector/raster data.

    Args:
        m (object): geemap.Map
    """
    tool_output = widgets.Output()
    tool_output_ctrl = ipyleaflet.WidgetControl(widget=tool_output, position="topright")

    if m.tool_output_ctrl is not None and m.tool_output_ctrl in m.controls:
        m.remove_control(m.tool_output_ctrl)

    file_type = widgets.ToggleButtons(
        options=["Shapefile", "GeoJSON", "Vector", "CSV", "GeoTIFF"],
        tooltips=[
            "Open a shapefile",
            "Open a GeoJSON file",
            "Open a vector dataset",
            "Create points from CSV",
            "Open a vector dataset",
            "Open a GeoTIFF",
        ],
    )
    file_type.style.button_width = "88px"

    file_chooser = FileChooser(os.getcwd())
    file_chooser.filter_pattern = "*.shp"
    file_chooser.use_dir_icons = True

    style = {"description_width": "initial"}
    layer_name = widgets.Text(
        value="Shapefile",
        description="Enter a layer name:",
        tooltip="Enter a layer name for the selected file",
        style=style,
        layout=widgets.Layout(width="454px", padding="0px 0px 0px 5px"),
    )

    longitude = widgets.Dropdown(
        options=[],
        value=None,
        description="Longitude:",
        layout=widgets.Layout(width="149px", padding="0px 0px 0px 5px"),
        style={"description_width": "initial"},
    )

    latitude = widgets.Dropdown(
        options=[],
        value=None,
        description="Latitude:",
        layout=widgets.Layout(width="149px", padding="0px 0px 0px 5px"),
        style={"description_width": "initial"},
    )

    label = widgets.Dropdown(
        options=[],
        value=None,
        description="Label:",
        layout=widgets.Layout(width="149px", padding="0px 0px 0px 5px"),
        style={"description_width": "initial"},
    )

    csv_widget = widgets.HBox()

    convert_bool = widgets.Checkbox(
        description="Convert to ee.FeatureCollection?",
        indent=False,
        layout=widgets.Layout(padding="0px 0px 0px 5px"),
    )
    convert_hbox = widgets.HBox([convert_bool])

    ok_cancel = widgets.ToggleButtons(
        value=None,
        options=["Apply", "Reset", "Close"],
        tooltips=["Apply", "Reset", "Close"],
        button_style="primary",
    )
    # ok_cancel.style.button_width = "133px"

    bands = widgets.Text(
        value="1",
        description="Bands:",
        tooltip="Enter a list of band indices",
        style=style,
        layout=widgets.Layout(width="110px"),
    )

    colormap = widgets.Dropdown(
        options=[],
        value=None,
        description="colormap:",
        layout=widgets.Layout(width="172px"),
        style=style,
    )

    x_dim = widgets.Text(
        value="x",
        description="x_dim:",
        tooltip="The x dimension",
        style=style,
        layout=widgets.Layout(width="80px"),
    )

    y_dim = widgets.Text(
        value="y",
        description="y_dim:",
        tooltip="The xydimension",
        style=style,
        layout=widgets.Layout(width="80px"),
    )

    raster_options = widgets.HBox()

    main_widget = widgets.VBox(
        [
            file_type,
            file_chooser,
            csv_widget,
            layer_name,
            convert_hbox,
            raster_options,
            ok_cancel,
        ]
    )

    tool_output.clear_output()
    with tool_output:
        display(main_widget)

    # def chooser_callback(chooser):
    #     if len(layer_name.value) == 0 and file_chooser.selected is not None:
    #         layer_name.value = os.path.splitext(file_chooser.selected_filename)[0]

    def bands_changed(change):
        if change["new"] and "," in change["owner"].value:
            colormap.value = None
            colormap.disabled = True
        else:
            colormap.disabled = False

    bands.observe(bands_changed, "value")

    def chooser_callback(chooser):
        if file_type.value == "CSV":
            import pandas as pd

            df = pd.read_csv(file_chooser.selected)
            col_names = df.columns.values.tolist()
            longitude.options = col_names
            latitude.options = col_names
            label.options = col_names

            if "longitude" in col_names:
                longitude.value = "longitude"
            if "latitude" in col_names:
                latitude.value = "latitude"
            if "name" in col_names:
                label.value = "name"

    file_chooser.register_callback(chooser_callback)

    def file_type_changed(change):
        ok_cancel.value = None
        file_chooser.default_path = os.getcwd()
        file_chooser.reset()
        layer_name.value = file_type.value
        csv_widget.children = []

        if change["new"] == "Shapefile":
            file_chooser.filter_pattern = "*.shp"
            raster_options.children = []
            convert_hbox.children = [convert_bool]
        elif change["new"] == "GeoJSON":
            file_chooser.filter_pattern = "*.geojson"
            raster_options.children = []
            convert_hbox.children = [convert_bool]
        elif change["new"] == "Vector":
            file_chooser.filter_pattern = "*.*"
            raster_options.children = []
            convert_hbox.children = [convert_bool]
        elif change["new"] == "CSV":
            file_chooser.filter_pattern = ["*.csv", "*.CSV"]
            csv_widget.children = [longitude, latitude, label]
            raster_options.children = []
            convert_hbox.children = [convert_bool]
        elif change["new"] == "GeoTIFF":
            import matplotlib.pyplot as plt

            file_chooser.filter_pattern = "*.tif"
            colormap.options = plt.colormaps()
            colormap.value = "terrain"
            raster_options.children = [bands, colormap, x_dim, y_dim]
            convert_hbox.children = []

    def ok_cancel_clicked(change):
        if change["new"] == "Apply":
            m.default_style = {"cursor": "wait"}
            file_path = file_chooser.selected

            if file_path is not None:
                ext = os.path.splitext(file_path)[1]
                with tool_output:
                    if ext.lower() == ".shp":
                        if convert_bool.value:
                            ee_object = shp_to_ee(file_path)
                            m.addLayer(ee_object, {}, layer_name.value)
                        else:
                            m.add_shapefile(
                                file_path, style=None, layer_name=layer_name.value
                            )
                    elif ext.lower() == ".geojson":
                        if convert_bool.value:
                            ee_object = geojson_to_ee(file_path)
                            m.addLayer(ee_object, {}, layer_name.value)
                        else:
                            m.add_geojson(
                                file_path, style=None, layer_name=layer_name.value
                            )

                    elif ext.lower() == ".csv":
                        if convert_bool.value:
                            ee_object = csv_to_ee(
                                file_path, latitude.value, longitude.value
                            )
                            m.addLayer(ee_object, {}, layer_name.value)
                        else:
                            m.add_xy_data(
                                file_path,
                                x=longitude.value,
                                y=latitude.value,
                                label=label.value,
                                layer_name=layer_name.value,
                            )

                    elif ext.lower() == ".tif":
                        sel_bands = [int(b.strip()) for b in bands.value.split(",")]
                        m.add_raster(
                            image=file_path,
                            bands=sel_bands,
                            layer_name=layer_name.value,
                            colormap=colormap.value,
                            x_dim=x_dim.value,
                            y_dim=y_dim.value,
                        )
                    else:
                        m.add_vector(file_path, style=None, layer_name=layer_name.value)
            else:
                print("Please select a file to open.")

            m.toolbar_reset()
            m.default_style = {"cursor": "default"}

        elif change["new"] == "Reset":
            file_chooser.reset()
            tool_output.clear_output()
            with tool_output:
                display(main_widget)
            m.toolbar_reset()
        elif change["new"] == "Close":
            if m.tool_output_ctrl is not None and m.tool_output_ctrl in m.controls:
                m.remove_control(m.tool_output_ctrl)
                m.tool_output_ctrl = None
                m.toolbar_reset()

        ok_cancel.value = None

    file_type.observe(file_type_changed, names="value")
    ok_cancel.observe(ok_cancel_clicked, names="value")
    # file_chooser.register_callback(chooser_callback)

    m.add_control(tool_output_ctrl)
    m.tool_output_ctrl = tool_output_ctrl


def change_basemap(m):
    """Widget for change basemaps.

    Args:
        m (object): geemap.Map()
    """
    from .basemaps import _ee_basemaps

    dropdown = widgets.Dropdown(
        options=list(_ee_basemaps.keys()),
        value="ROADMAP",
        layout=widgets.Layout(width="200px")
        # description="Basemaps",
    )

    close_btn = widgets.Button(
        icon="times",
        tooltip="Close the basemap widget",
        button_style="primary",
        layout=widgets.Layout(width="32px"),
    )

    basemap_widget = widgets.HBox([dropdown, close_btn])

    def on_click(change):
        basemap_name = change["new"]

        if len(m.layers) == 1:
            old_basemap = m.layers[0]
        else:
            old_basemap = m.layers[1]
        m.substitute_layer(old_basemap, _ee_basemaps[basemap_name])

    dropdown.observe(on_click, "value")

    def close_click(change):
        m.toolbar_reset()
        if m.basemap_ctrl is not None and m.basemap_ctrl in m.controls:
            m.remove_control(m.basemap_ctrl)
        basemap_widget.close()

    close_btn.on_click(close_click)

    basemap_control = ipyleaflet.WidgetControl(
        widget=basemap_widget, position="topright"
    )
    m.add_control(basemap_control)
    m.basemap_ctrl = basemap_control


def convert_js2py(m):
    """A widget for converting Earth Engine JavaScript to Python.

    Args:
        m (object): geemap.Map
    """

    full_widget = widgets.VBox(layout=widgets.Layout(width="465px", height="350px"))

    text_widget = widgets.Textarea(
        placeholder="Paste your Earth Engine JavaScript into this textbox and click the Convert button below to convert the Javascript to Python",
        layout=widgets.Layout(width="455px", height="310px"),
    )

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Convert", "Clear", "Close"],
        tooltips=["Convert", "Clear", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "142px"

    def button_clicked(change):
        if change["new"] == "Convert":
            from .conversion import create_new_cell, js_snippet_to_py

            if len(text_widget.value) > 0:
                out_lines = js_snippet_to_py(
                    text_widget.value,
                    add_new_cell=False,
                    import_ee=False,
                    import_geemap=False,
                    show_map=False,
                )
                if len(out_lines) > 0 and len(out_lines[0].strip()) == 0:
                    out_lines = out_lines[1:]
                text_widget.value = "".join(out_lines)
                create_code_cell(text_widget.value)

        elif change["new"] == "Clear":
            text_widget.value = ""
        elif change["new"] == "Close":
            m.toolbar_reset()
            if m.convert_ctrl is not None and m.convert_ctrl in m.controls:
                m.remove_control(m.convert_ctrl)
            full_widget.close()
        buttons.value = None

    buttons.observe(button_clicked, "value")

    full_widget.children = [text_widget, buttons]
    widget_control = ipyleaflet.WidgetControl(widget=full_widget, position="topright")
    m.add_control(widget_control)
    m.convert_ctrl = widget_control


def collect_samples(m):

    full_widget = widgets.VBox()
    layout = widgets.Layout(width="100px")
    prop_label = widgets.Label(
        value="Property",
        layout=widgets.Layout(display="flex", justify_content="center", width="100px"),
    )
    value_label = widgets.Label(
        value="Value",
        layout=widgets.Layout(display="flex", justify_content="center", width="100px"),
    )
    color_label = widgets.Label(
        value="Color",
        layout=widgets.Layout(display="flex", justify_content="center", width="100px"),
    )

    prop_text1 = widgets.Text(layout=layout, placeholder="Required")
    value_text1 = widgets.Text(layout=layout, placeholder="Integer")
    prop_text2 = widgets.Text(layout=layout, placeholder="Optional")
    value_text2 = widgets.Text(layout=layout, placeholder="String")

    color = widgets.ColorPicker(
        concise=False,
        value="#3388ff",
        layout=layout,
        style={"description_width": "initial"},
    )

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Apply", "Clear", "Close"],
        tooltips=["Apply", "Clear", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "99px"

    def button_clicked(change):
        if change["new"] == "Apply":

            if len(color.value) != 7:
                color.value = "#3388ff"
            draw_control = ipyleaflet.DrawControl(
                marker={"shapeOptions": {"color": color.value}, "repeatMode": True},
                rectangle={"shapeOptions": {"color": color.value}, "repeatMode": True},
                polygon={"shapeOptions": {"color": color.value}, "repeatMode": True},
                circlemarker={},
                polyline={},
                edit=False,
                remove=False,
            )

            controls = []
            old_draw_control = None
            for control in m.controls:
                if isinstance(control, ipyleaflet.DrawControl):
                    controls.append(draw_control)
                    old_draw_control = control

                else:
                    controls.append(control)

            m.controls = tuple(controls)
            old_draw_control.close()
            m.draw_control = draw_control

            train_props = {}

            if prop_text1.value != "" and value_text1.value != "":
                try:
                    _ = int(value_text1.value)
                except Exception as _:
                    value_text1.placeholder = "Integer only"
                    value_text1.value = ""
                    return
                train_props[prop_text1.value] = int(value_text1.value)
            if prop_text2.value != "" and value_text2.value != "":
                train_props[prop_text2.value] = value_text2.value
            if color.value != "":
                train_props["color"] = color.value

            # Handles draw events
            def handle_draw(target, action, geo_json):
                from .geemap import ee_tile_layer

                try:
                    geom = geojson_to_ee(geo_json, False)
                    m.user_roi = geom

                    if len(train_props) > 0:
                        feature = ee.Feature(geom, train_props)
                    else:
                        feature = ee.Feature(geom)
                    m.draw_last_json = geo_json
                    m.draw_last_feature = feature
                    if action == "deleted" and len(m.draw_features) > 0:
                        m.draw_features.remove(feature)
                        m.draw_count -= 1
                    else:
                        m.draw_features.append(feature)
                        m.draw_count += 1
                    collection = ee.FeatureCollection(m.draw_features)
                    m.user_rois = collection
                    ee_draw_layer = ee_tile_layer(
                        collection, {"color": "blue"}, "Drawn Features", False, 0.5
                    )
                    draw_layer_index = m.find_layer_index("Drawn Features")

                    if draw_layer_index == -1:
                        m.add_layer(ee_draw_layer)
                        m.draw_layer = ee_draw_layer
                    else:
                        m.substitute_layer(m.draw_layer, ee_draw_layer)
                        m.draw_layer = ee_draw_layer

                except Exception as e:
                    m.draw_count = 0
                    m.draw_features = []
                    m.draw_last_feature = None
                    m.draw_layer = None
                    m.user_roi = None
                    m.roi_start = False
                    m.roi_end = False
                    print("There was an error creating Earth Engine Feature.")
                    raise Exception(e)

            draw_control.on_draw(handle_draw)

        elif change["new"] == "Clear":
            prop_text1.value = ""
            value_text1.value = ""
            prop_text2.value = ""
            value_text2.value = ""
            color.value = "#3388ff"
        elif change["new"] == "Close":
            m.toolbar_reset()
            if m.training_ctrl is not None and m.training_ctrl in m.controls:
                m.remove_control(m.training_ctrl)
            full_widget.close()
        buttons.value = None

    buttons.observe(button_clicked, "value")

    full_widget.children = [
        widgets.HBox([prop_label, value_label, color_label]),
        widgets.HBox([prop_text1, value_text1, color]),
        widgets.HBox([prop_text2, value_text2, color]),
        buttons,
    ]

    widget_control = ipyleaflet.WidgetControl(widget=full_widget, position="topright")
    m.add_control(widget_control)
    m.training_ctrl = widget_control


def get_tools_dict():

    import pandas as pd
    import pkg_resources

    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
    toolbox_csv = os.path.join(pkg_dir, "data/template/toolbox.csv")

    df = pd.read_csv(toolbox_csv).set_index("index")
    tools_dict = df.to_dict("index")

    return tools_dict


def tool_gui(tool_dict, max_width="420px", max_height="600px"):
    """Create a GUI for a tool based on the tool dictionary.

    Args:
        tool_dict (dict): The dictionary containing the tool info.
        max_width (str, optional): The max width of the tool dialog.
        max_height (str, optional): The max height of the tool dialog.

    Returns:
        object: An ipywidget object representing the tool interface.
    """
    tool_widget = widgets.VBox(
        layout=widgets.Layout(max_width=max_width, max_height=max_height)
    )
    children = []
    args = {}
    required_inputs = []
    style = {"description_width": "initial"}
    max_width = str(int(max_width.replace("px", "")) - 10) + "px"

    header_width = str(int(max_width.replace("px", "")) - 104) + "px"
    header = widgets.Label(
        value=f'Current Tool: {tool_dict["label"]}',
        style=style,
        layout=widgets.Layout(width=header_width),
    )
    code_btn = widgets.Button(
        description="View Code", layout=widgets.Layout(width="100px")
    )

    children.append(widgets.HBox([header, code_btn]))

    desc = widgets.Textarea(
        value=f'Description: {tool_dict["description"]}',
        layout=widgets.Layout(width="410px", max_width=max_width),
        disabled=True,
    )
    children.append(desc)

    # params = tool_dict["parameters"]
    # for param in params:
    #     items = params[param]
    #     required = ""
    #     if items["optional"] == "false":
    #         required = "*"
    #         required_inputs.append(param)
    #     label = items["name"] + required
    #     param_type = items["parameter_type"]
    #     default_value = None

    #     if (items["default_value"] != "null") and (len(items["default_value"]) > 0):
    #         if "false" in items["default_value"]:
    #             default_value = False
    #         elif "true" in items["default_value"]:
    #             default_value = True
    #         else:
    #             default_value = items["default_value"].replace('"', "")

    #     layout = widgets.Layout(width="500px", max_width=max_width)

    #     if isinstance(param_type, str):
    #         # display(data_types[param_type])

    #         if param_type == "Boolean":
    #             var_widget = widgets.Checkbox(
    #                 description=label, style=style, layout=layout, value=default_value
    #             )
    #         elif param_type in [
    #             "Directory",
    #             "ExistingFile",
    #             "ExistingFileOrFloat",
    #             "FileList",
    #             "NewFile",
    #         ]:
    #             var_widget = FileChooser(title=label)
    #         else:
    #             var_widget = widgets.Text(description=label, style=style, layout=layout)
    #             if default_value is not None:
    #                 var_widget.value = str(default_value)

    #         args[param] = var_widget

    #         children.append(var_widget)
    #     elif isinstance(param_type, dict):

    #         if "OptionList" in param_type:
    #             var_widget = widgets.Dropdown(
    #                 options=param_type["OptionList"],
    #                 description=label,
    #                 style=style,
    #                 layout=layout,
    #             )
    #         elif list(param_type.keys())[0] in [
    #             "Directory",
    #             "ExistingFile",
    #             "ExistingFileOrFloat",
    #             "FileList",
    #             "NewFile",
    #         ]:
    #             var_widget = FileChooser(title=label)
    #         else:
    #             var_widget = FileChooser(title=label)
    #         args[param] = var_widget

    #         children.append(var_widget)

    run_btn = widgets.Button(description="Run", layout=widgets.Layout(width="100px"))
    cancel_btn = widgets.Button(
        description="Cancel", layout=widgets.Layout(width="100px")
    )
    help_btn = widgets.Button(description="Help", layout=widgets.Layout(width="100px"))
    import_btn = widgets.Button(
        description="Import",
        tooltip="Import the script to a new cell",
        layout=widgets.Layout(width="98px"),
    )
    tool_output = widgets.Output(layout=widgets.Layout(max_height="200px"))
    children.append(widgets.HBox([run_btn, cancel_btn, help_btn, import_btn]))
    children.append(tool_output)
    tool_widget.children = children

    def run_button_clicked(b):
        tool_output.clear_output()

        required_params = required_inputs.copy()
        args2 = []
        for arg in args:

            line = ""
            if isinstance(args[arg], FileChooser):
                if arg in required_params and args[arg].selected is None:
                    with tool_output:
                        print(f"Please provide inputs for required parameters.")
                        break
                elif arg in required_params:
                    required_params.remove(arg)
                if arg == "i":
                    line = f"-{arg}={args[arg].selected}"
                else:
                    line = f"--{arg}={args[arg].selected}"
            elif isinstance(args[arg], widgets.Text):
                if arg in required_params and len(args[arg].value) == 0:
                    with tool_output:
                        print(f"Please provide inputs for required parameters.")
                        break
                elif arg in required_params:
                    required_params.remove(arg)
                if args[arg].value is not None and len(args[arg].value) > 0:
                    line = f"--{arg}={args[arg].value}"
            elif isinstance(args[arg], widgets.Checkbox):
                line = f"--{arg}={args[arg].value}"
            args2.append(line)

        if len(required_params) == 0:
            with tool_output:
                # wbt.run_tool(tool_dict["name"], args2)
                pass

    def help_button_clicked(b):
        import webbrowser

        tool_output.clear_output()
        with tool_output:
            html = widgets.HTML(
                value=f'<a href={tool_dict["link"]} target="_blank">{tool_dict["link"]}</a>'
            )
            display(html)
        webbrowser.open_new_tab(tool_dict["link"])

    def code_button_clicked(b):
        import webbrowser

        with tool_output:
            html = widgets.HTML(
                value=f'<a href={tool_dict["link"]} target="_blank">{tool_dict["link"]}</a>'
            )
            display(html)
        webbrowser.open_new_tab(tool_dict["link"])

    def cancel_btn_clicked(b):
        tool_output.clear_output()

    def import_button_clicked(b):
        tool_output.clear_output()

        content = []

        create_code_cell("\n".join(content))

    import_btn.on_click(import_button_clicked)
    run_btn.on_click(run_button_clicked)
    help_btn.on_click(help_button_clicked)
    code_btn.on_click(code_button_clicked)
    cancel_btn.on_click(cancel_btn_clicked)

    return tool_widget


def build_toolbox(tools_dict, max_width="1080px", max_height="600px"):
    """Build the GEE toolbox.

    Args:
        tools_dict (dict): A dictionary containing information for all tools.
        max_width (str, optional): The maximum width of the widget.
        max_height (str, optional): The maximum height of the widget.

    Returns:
        object: An ipywidget representing the toolbox.
    """
    left_widget = widgets.VBox(layout=widgets.Layout(min_width="175px"))
    center_widget = widgets.VBox(
        layout=widgets.Layout(min_width="200px", max_width="200px")
    )
    right_widget = widgets.Output(
        layout=widgets.Layout(width="630px", max_height=max_height)
    )
    full_widget = widgets.HBox(
        [left_widget, center_widget, right_widget],
        layout=widgets.Layout(max_width=max_width, max_height=max_height),
    )

    search_widget = widgets.Text(
        placeholder="Search tools ...", layout=widgets.Layout(width="170px")
    )
    label_widget = widgets.Label(layout=widgets.Layout(width="170px"))
    label_widget.value = f"{len(tools_dict)} Available Tools"
    close_btn = widgets.Button(
        description="Close Toolbox", icon="close", layout=widgets.Layout(width="170px")
    )

    categories = {}
    categories["All Tools"] = []
    for key in tools_dict.keys():
        category = tools_dict[key]["category"]
        if category not in categories.keys():
            categories[category] = []
        categories[category].append(tools_dict[key]["name"])
        categories["All Tools"].append(tools_dict[key]["name"])

    options = list(categories.keys())
    all_tools = categories["All Tools"]
    all_tools.sort()
    category_widget = widgets.Select(
        options=options, layout=widgets.Layout(width="170px", height="165px")
    )
    tools_widget = widgets.Select(
        options=[], layout=widgets.Layout(width="195px", height="400px")
    )

    def category_selected(change):
        if change["new"]:
            selected = change["owner"].value
            options = categories[selected]
            options.sort()
            tools_widget.options = options
            label_widget.value = f"{len(options)} Available Tools"

    category_widget.observe(category_selected, "value")

    def tool_selected(change):
        if change["new"]:
            selected = change["owner"].value
            tool_dict = tools_dict[selected]
            with right_widget:
                right_widget.clear_output()
                display(tool_gui(tool_dict, max_height=max_height))

    tools_widget.observe(tool_selected, "value")

    def search_changed(change):
        if change["new"]:
            keyword = change["owner"].value
            if len(keyword) > 0:
                selected_tools = []
                for tool in all_tools:
                    if keyword.lower() in tool.lower():
                        selected_tools.append(tool)
                if len(selected_tools) > 0:
                    tools_widget.options = selected_tools
                label_widget.value = f"{len(selected_tools)} Available Tools"
        else:
            tools_widget.options = all_tools
            label_widget.value = f"{len(tools_dict)} Available Tools"

    search_widget.observe(search_changed, "value")

    def close_btn_clicked(b):
        full_widget.close()

    close_btn.on_click(close_btn_clicked)

    category_widget.value = list(categories.keys())[0]
    tools_widget.options = all_tools
    left_widget.children = [category_widget, search_widget, label_widget, close_btn]
    center_widget.children = [tools_widget]

    return full_widget


def timelapse(m=None):
    """Creates timelapse animations.

    Args:
        m (geemap.Map, optional): A geemap Map instance. Defaults to None.

    Returns:
        ipywidgets: The interactive GUI.
    """
    if m is not None:
        m.add_basemap("HYBRID")

    widget_width = "350px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    style = {"description_width": "initial"}

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="gear",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    collection = widgets.Dropdown(
        options=[
            "Landsat TM-ETM-OLI Surface Reflectance",
            "Sentinel-2AB Surface Reflectance",
            "MODIS",
        ],
        value="Landsat TM-ETM-OLI Surface Reflectance",
        description="Collection:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    title = widgets.Text(
        value="Timelapse",
        description="Title:",
        style=style,
        layout=widgets.Layout(width="181px", padding=padding),
    )

    bands = widgets.Dropdown(
        description="RGB:",
        options=[
            "Red/Green/Blue",
            "NIR/Red/Green",
            "SWIR2/SWIR1/NIR",
            "NIR/SWIR1/Red",
            "SWIR2/NIR/Red",
            "SWIR2/SWIR1/Red",
            "SWIR1/NIR/Blue",
            "NIR/SWIR1/Blue",
            "SWIR2/NIR/Green",
            "SWIR1/NIR/Red",
        ],
        value="NIR/Red/Green",
        style=style,
        layout=widgets.Layout(width="165px", padding=padding),
    )

    speed = widgets.IntSlider(
        description="Frames/sec:",
        tooltip="Frames per second",
        value=10,
        min=1,
        max=30,
        readout=False,
        style=style,
        layout=widgets.Layout(width="142px", padding=padding),
    )

    speed_label = widgets.Label(
        layout=widgets.Layout(width="20px", padding=padding),
    )
    widgets.jslink((speed, "value"), (speed_label, "value"))

    cloud = widgets.Checkbox(
        value=True,
        description="Apply fmask (remove clouds, shadows, snow)",
        tooltip="Apply fmask (remove clouds, shadows, snow)",
        style=style,
    )

    start_year = widgets.IntSlider(
        description="Start Year:",
        value=1984,
        min=1984,
        max=2021,
        readout=False,
        style=style,
        layout=widgets.Layout(width="138px", padding=padding),
    )

    start_year_label = widgets.Label()
    widgets.jslink((start_year, "value"), (start_year_label, "value"))

    end_year = widgets.IntSlider(
        description="End Year:",
        value=2020,
        min=1984,
        max=2021,
        readout=False,
        style=style,
        layout=widgets.Layout(width="138px", padding=padding),
    )
    end_year_label = widgets.Label()
    widgets.jslink((end_year, "value"), (end_year_label, "value"))

    start_month = widgets.IntSlider(
        description="Start Month:",
        value=5,
        min=1,
        max=12,
        readout=False,
        style=style,
        layout=widgets.Layout(width="145px", padding=padding),
    )

    start_month_label = widgets.Label(
        layout=widgets.Layout(width="20px", padding=padding),
    )
    widgets.jslink((start_month, "value"), (start_month_label, "value"))

    end_month = widgets.IntSlider(
        description="End Month:",
        value=10,
        min=1,
        max=12,
        readout=False,
        style=style,
        layout=widgets.Layout(width="155px", padding=padding),
    )

    end_month_label = widgets.Label()
    widgets.jslink((end_month, "value"), (end_month_label, "value"))

    font_size = widgets.IntSlider(
        description="Font size:",
        value=30,
        min=10,
        max=50,
        readout=False,
        style=style,
        layout=widgets.Layout(width="152px", padding=padding),
    )

    font_size_label = widgets.Label()
    widgets.jslink((font_size, "value"), (font_size_label, "value"))

    font_color = widgets.ColorPicker(
        concise=False,
        description="Font color:",
        value="white",
        style=style,
        layout=widgets.Layout(width="170px", padding=padding),
    )

    progress_bar_color = widgets.ColorPicker(
        concise=False,
        description="Progress bar:",
        value="blue",
        style=style,
        layout=widgets.Layout(width="180px", padding=padding),
    )

    # Normalized Satellite Indices: https://www.usna.edu/Users/oceano/pguth/md_help/html/norm_sat.htm

    nd_options = [
        "Vegetation Index (NDVI)",
        "Water Index (NDWI)",
        "Modified Water Index (MNDWI)",
        "Snow Index (NDSI)",
        "Soil Index (NDSI)",
        "Burn Ratio (NBR)",
        "Customized",
    ]
    nd_indices = widgets.Dropdown(
        options=nd_options,
        value=None,
        description="Normalized Difference Index:",
        style=style,
        layout=widgets.Layout(width="347px", padding=padding),
    )

    first_band = widgets.Dropdown(
        description="1st band:",
        options=["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2"],
        value=None,
        style=style,
        layout=widgets.Layout(width="171px", padding=padding),
    )

    second_band = widgets.Dropdown(
        description="2nd band:",
        options=["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2"],
        value=None,
        style=style,
        layout=widgets.Layout(width="172px", padding=padding),
    )

    nd_threshold = widgets.FloatSlider(
        value=0,
        min=-1,
        max=1,
        step=0.01,
        description="Threshold:",
        orientation="horizontal",
        readout=False,
        style=style,
        layout=widgets.Layout(width="159px", padding=padding),
    )

    nd_threshold_label = widgets.Label(
        layout=widgets.Layout(width="35px", padding=padding),
    )
    widgets.jslink((nd_threshold, "value"), (nd_threshold_label, "value"))

    nd_color = widgets.ColorPicker(
        concise=False,
        description="Color:",
        value="blue",
        style=style,
        layout=widgets.Layout(width="145px", padding=padding),
    )

    def nd_index_change(change):
        if nd_indices.value == "Vegetation Index (NDVI)":
            first_band.value = "NIR"
            second_band.value = "Red"
        elif nd_indices.value == "Water Index (NDWI)":
            first_band.value = "NIR"
            second_band.value = "SWIR1"
        elif nd_indices.value == "Modified Water Index (MNDWI)":
            first_band.value = "Green"
            second_band.value = "SWIR1"
        elif nd_indices.value == "Snow Index (NDSI)":
            first_band.value = "Green"
            second_band.value = "SWIR1"
        elif nd_indices.value == "Soil Index (NDSI)":
            first_band.value = "SWIR1"
            second_band.value = "NIR"
        elif nd_indices.value == "Burn Ratio (NBR)":
            first_band.value = "NIR"
            second_band.value = "SWIR2"
        elif nd_indices.value == "Customized":
            first_band.value = None
            second_band.value = None

    nd_indices.observe(nd_index_change, names="value")

    button_width = "113px"
    create_gif = widgets.Button(
        description="Create timelapse",
        button_style="primary",
        tooltip="Click to create timelapse",
        style=style,
        layout=widgets.Layout(padding="0px", width=button_width),
    )

    def submit_clicked(b):

        if start_year.value > end_year.value:
            print("The end year must be great than the start year.")
            return
        if start_month.value > end_month.value:
            print("The end month must be great than the start month.")
            return
        if start_year.value == end_year.value:
            add_progress_bar = False
        else:
            add_progress_bar = True

        start_date = str(start_month.value).zfill(2) + "-01"
        end_date = str(end_month.value).zfill(2) + "-30"

        with output:
            print("Computing... Please wait...")

        nd_bands = None
        if (first_band.value is not None) and (second_band.value is not None):
            nd_bands = [first_band.value, second_band.value]

        temp_output = widgets.Output()

        if m is not None:

            out_dir = os.path.expanduser("~/Downloads")
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)

            out_gif = os.path.join(out_dir, "timelapse_" + random_string(3) + ".gif")

            with temp_output:
                temp_output.clear_output()
                m.add_landsat_ts_gif(
                    roi=m.user_roi,
                    label=title.value,
                    start_year=start_year.value,
                    end_year=end_year.value,
                    start_date=start_date,
                    end_date=end_date,
                    bands=bands.value.split("/"),
                    font_color=font_color.value,
                    frames_per_second=speed.value,
                    font_size=font_size.value,
                    add_progress_bar=add_progress_bar,
                    progress_bar_color=progress_bar_color.value,
                    out_gif=out_gif,
                    apply_fmask=cloud.value,
                    nd_bands=nd_bands,
                    nd_threshold=nd_threshold.value,
                    nd_palette=["black", nd_color.value],
                )
                if m.user_roi is not None:
                    m.centerObject(m.user_roi)

            with output:
                print("The timelapse has been added to the map.")
                link = create_download_link(
                    out_gif,
                    title="Click here to download: ",
                )
                display(link)
                if nd_bands is not None:
                    link_nd = create_download_link(
                        out_gif.replace(".gif", "_nd.gif"),
                        title="Click here to download: ",
                    )
                    display(link_nd)

    create_gif.on_click(submit_clicked)

    reset_btn = widgets.Button(
        description="Reset",
        button_style="primary",
        style=style,
        layout=widgets.Layout(padding="0px", width=button_width),
    )

    def reset_btn_click(change):
        output.clear_output()

    reset_btn.on_click(reset_btn_click)

    close_btn = widgets.Button(
        description="Close",
        button_style="primary",
        style=style,
        layout=widgets.Layout(padding="0px", width=button_width),
    )

    def close_click(change):
        if m is not None:
            m.toolbar_reset()
            if m.tool_control is not None and m.tool_control in m.controls:
                m.remove_control(m.tool_control)
                m.tool_control = None
        toolbar_widget.close()

    close_btn.on_click(close_click)

    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        collection,
        widgets.HBox([title, bands]),
        widgets.HBox([speed, speed_label, progress_bar_color]),
        widgets.HBox([start_year, start_year_label, end_year, end_year_label]),
        widgets.HBox([start_month, start_month_label, end_month, end_month_label]),
        widgets.HBox([font_size, font_size_label, font_color]),
        cloud,
        nd_indices,
        widgets.HBox([first_band, second_band]),
        widgets.HBox([nd_threshold, nd_threshold_label, nd_color]),
        widgets.HBox([create_gif, reset_btn, close_btn]),
        output,
    ]

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
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                m.toolbar_reset()
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    toolbar_button.value = True
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add_control(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget


def time_slider(m=None):
    """Creates a time slider for visualizing any ee.ImageCollection.

    Args:
        m (geemap.Map, optional): A geemap Map instance. Defaults to None.

    Returns:
        ipywidgets: The interactive GUI.
    """
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    widget_width = "350px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    style = {"description_width": "initial"}

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="fast-forward",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    col_options_dict = {
        "Landsat TM-ETM-OLI Surface Reflectance": {
            "min": 0,
            "max": 4000,
            "bands": ["NIR", "Red", "Green"],
            "start_year": 1984,
            "end_year": 2021,
            "bandnames": ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2", "pixel_qa"],
        },
        "MOD13A2.006 Terra Vegetation Indices": {
            "min": 0,
            "max": 9000,
            "start_year": 2000,
            "end_year": 2021,
            "palette": [
                "FFFFFF",
                "CE7E45",
                "DF923D",
                "F1B555",
                "FCD163",
                "99B718",
                "74A901",
                "66A000",
                "529400",
                "3E8601",
                "207401",
                "056201",
                "004C00",
                "023B01",
                "012E01",
                "011D01",
                "011301",
            ],
        },
        "Sentinel-2 Surface Relectance": {
            "min": 0,
            "max": 4000,
            "bands": ["NIR", "Red", "Green"],
            "start_year": 2015,
            "end_year": 2021,
            "bandnames": [
                "Blue",
                "Green",
                "Red",
                "Red Edge 1",
                "Red Edge 2",
                "Red Edge 3",
                "NIR",
                "Red Edge 4",
                "SWIR1",
                "SWIR2",
                "QA60",
            ],
        },
        "USDA NAIP Imagery": {
            "min": 0,
            "max": 255,
            "bands": ["R", "G", "B"],
            "start_year": 2003,
            "end_year": 2021,
            "bandnames": ["R", "G", "B", "N"],
        },
    }

    col_options = list(col_options_dict.keys())

    if m is not None:
        col_options += m.ee_raster_layer_names

    collection = widgets.Dropdown(
        options=col_options,
        value=col_options[0],
        description="Time series:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    region = widgets.Dropdown(
        options=["User-drawn ROI"] + m.ee_vector_layer_names,
        value="User-drawn ROI",
        description="Region:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    dropdown_width = "97px"
    landsat_bands = ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2", "pixel_qa"]
    band1_dropdown = widgets.Dropdown(
        options=landsat_bands,
        value="NIR",
        layout=widgets.Layout(width=dropdown_width),
    )
    band2_dropdown = widgets.Dropdown(
        options=landsat_bands,
        value="Red",
        layout=widgets.Layout(width=dropdown_width),
    )
    band3_dropdown = widgets.Dropdown(
        options=landsat_bands,
        value="Green",
        layout=widgets.Layout(width=dropdown_width),
    )

    bands_label = widgets.Label("Bands:", layout=widgets.Layout(padding=padding))
    bands_hbox = widgets.HBox(
        [bands_label, band1_dropdown, band2_dropdown, band3_dropdown]
    )

    vis = widgets.Text(
        value="",
        description="Vis min value:",
        placeholder="{'min': 0, 'max': 1, 'palette': ['red', 'blue']}",
        style=style,
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    vis_min = widgets.Text(
        value="0",
        description="Vis min value:",
        style=style,
        layout=widgets.Layout(width="172px", padding=padding),
    )

    vis_max = widgets.Text(
        value="4000",
        description="Vis max value:",
        style=style,
        layout=widgets.Layout(width="172px", padding=padding),
    )

    opacity = widgets.FloatSlider(
        value=1,
        min=0,
        max=1,
        step=0.01,
        description="Opacity:",
        continuous_update=True,
        readout=False,
        readout_format=".2f",
        layout=widgets.Layout(width="130px", padding=padding),
        style={"description_width": "50px"},
    )

    opacity_label = widgets.Label(layout=widgets.Layout(width="40px", padding=padding))
    widgets.jslink((opacity, "value"), (opacity_label, "value"))

    gamma = widgets.FloatSlider(
        value=1,
        min=0.1,
        max=10,
        step=0.01,
        description="Gamma:",
        continuous_update=True,
        readout=False,
        readout_format=".2f",
        layout=widgets.Layout(width="123px", padding=padding),
        style={"description_width": "50px"},
    )

    gamma_label = widgets.Label(layout=widgets.Layout(width="40px", padding=padding))
    widgets.jslink((gamma, "value"), (gamma_label, "value"))

    color_picker = widgets.ColorPicker(
        concise=False,
        value="#000000",
        layout=widgets.Layout(width="97px"),
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
        layout=widgets.Layout(width="150px", padding=padding),
        style={"description_width": "initial"},
    )

    colormap = widgets.Dropdown(
        options=plt.colormaps(),
        value=None,
        description="Colormap:",
        layout=widgets.Layout(width="195px", padding=padding),
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

                vmin = 0
                vmax = 1
                try:
                    if vis_min.value != "":
                        vmin = float(vis_min.value)
                    if vis_max.value != "":
                        vmax = float(vis_max.value)
                except Exception as _:
                    pass

                norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
                mpl.colorbar.ColorbarBase(
                    ax, norm=norm, cmap=cmap, orientation="horizontal"
                )

                palette.value = ", ".join([color for color in cmap_colors])

                if m.colorbar_widget is None:
                    m.colorbar_widget = widgets.Output(
                        layout=widgets.Layout(height="60px")
                    )

                if m.colorbar_ctrl is None:
                    m.colorbar_ctrl = ipyleaflet.WidgetControl(
                        widget=m.colorbar_widget, position="bottomright"
                    )
                    m.add_control(m.colorbar_ctrl)

                colorbar_output = m.colorbar_widget
                with colorbar_output:
                    colorbar_output.clear_output()
                    plt.show()

    classes.observe(classes_changed, "value")

    palette = widgets.Text(
        value="",
        placeholder="",
        description="Palette:",
        tooltip="Enter a list of hex color code (RRGGBB)",
        layout=widgets.Layout(width="137px", padding=padding),
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

    def colormap_changed(change):
        if change["new"]:

            n_class = None
            if classes.value != "Any":
                n_class = int(classes.value)

            colors = plt.cm.get_cmap(colormap.value, n_class)
            cmap_colors = [mpl.colors.rgb2hex(colors(i))[1:] for i in range(colors.N)]

            _, ax = plt.subplots(figsize=(6, 0.4))
            cmap = mpl.colors.LinearSegmentedColormap.from_list(
                "custom", to_hex_colors(cmap_colors), N=256
            )

            vmin = 0
            vmax = 1
            try:
                if vis_min.value != "":
                    vmin = float(vis_min.value)
                if vis_max.value != "":
                    vmax = float(vis_max.value)
            except Exception as _:
                pass

            norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
            mpl.colorbar.ColorbarBase(
                ax, norm=norm, cmap=cmap, orientation="horizontal"
            )

            palette.value = ", ".join(cmap_colors)

            if m.colorbar_widget is None:
                m.colorbar_widget = widgets.Output(layout=widgets.Layout(height="60px"))

            if m.colorbar_ctrl is None:
                m.colorbar_ctrl = ipyleaflet.WidgetControl(
                    widget=m.colorbar_widget, position="bottomright"
                )
                m.add_control(m.colorbar_ctrl)

            colorbar_output = m.colorbar_widget
            with colorbar_output:
                colorbar_output.clear_output()
                plt.show()

    colormap.observe(colormap_changed, "value")

    palette_vbox = widgets.VBox()

    labels = widgets.Text(
        value=", ".join([str(i) for i in range(1984, 2021)]),
        description="Labels:",
        style=style,
        layout=widgets.Layout(width="150px", padding=padding),
    )

    speed = widgets.FloatSlider(
        description="Speed (sec):",
        tooltip="Time interval in seconds",
        value=1,
        min=0.1,
        max=10,
        readout=False,
        style=style,
        layout=widgets.Layout(width="160px", padding=padding),
    )

    speed_label = widgets.Label(
        layout=widgets.Layout(width="25px", padding=padding),
    )
    widgets.jslink((speed, "value"), (speed_label, "value"))

    prebuilt_options = widgets.VBox()

    cloud = widgets.Checkbox(
        value=True,
        description="Apply fmask (remove clouds, shadows, snow)",
        tooltip="Apply fmask (remove clouds, shadows, snow)",
        style=style,
    )

    start_year = widgets.IntSlider(
        description="Start Year:",
        value=1984,
        min=1984,
        max=2021,
        readout=False,
        style=style,
        layout=widgets.Layout(width="138px", padding=padding),
    )

    def year_change(change):
        if change["new"]:

            if collection.value != "MOD13A2.006 Terra Vegetation Indices":

                labels.value = ", ".join(
                    str(i)
                    for i in range(int(start_year.value), int(end_year.value) + 1)
                )
            else:
                modis_labels = []
                for i in range(int(start_year.value), int(end_year.value) + 1):
                    for j in range(1, 13):
                        modis_labels.append(str(i) + "-" + str(j).zfill(2))
                labels.value = ", ".join(modis_labels)

    start_year.observe(year_change, "value")

    start_year_label = widgets.Label()
    widgets.jslink((start_year, "value"), (start_year_label, "value"))

    end_year = widgets.IntSlider(
        description="End Year:",
        value=2020,
        min=1984,
        max=2021,
        readout=False,
        style=style,
        layout=widgets.Layout(width="138px", padding=padding),
    )

    end_year.observe(year_change, "value")

    end_year_label = widgets.Label()
    widgets.jslink((end_year, "value"), (end_year_label, "value"))

    start_month = widgets.IntSlider(
        description="Start Month:",
        value=1,
        min=1,
        max=12,
        readout=False,
        style=style,
        layout=widgets.Layout(width="145px", padding=padding),
    )

    start_month_label = widgets.Label(
        layout=widgets.Layout(width="20px", padding=padding),
    )
    widgets.jslink((start_month, "value"), (start_month_label, "value"))

    end_month = widgets.IntSlider(
        description="End Month:",
        value=12,
        min=1,
        max=12,
        readout=False,
        style=style,
        layout=widgets.Layout(width="155px", padding=padding),
    )

    end_month_label = widgets.Label()
    widgets.jslink((end_month, "value"), (end_month_label, "value"))

    prebuilt_options.children = [
        widgets.HBox([start_year, start_year_label, end_year, end_year_label]),
        widgets.HBox([start_month, start_month_label, end_month, end_month_label]),
        cloud,
    ]

    button_width = "113px"
    apply_btn = widgets.Button(
        description="Apply",
        button_style="primary",
        tooltip="Apply the settings to activate the time slider",
        style=style,
        layout=widgets.Layout(padding="0px", width=button_width),
    )

    def submit_clicked(b):

        output.clear_output()
        with output:
            if start_year.value > end_year.value:
                print("The end year must be great than the start year.")
                return
            if start_month.value > end_month.value:
                print("The end month must be great than the start month.")
                return

        if m is not None:

            roi = None
            if region.value == "User-drawn ROI" and (m.user_roi is not None):
                roi = m.user_roi
            elif region.value == "User-drawn ROI" and (m.user_roi is None):
                with output:
                    print("Use the Drawing tool to create an ROI.")
                    return
            elif region.value in m.ee_layer_dict:
                roi = m.ee_layer_dict[region.value]["ee_object"]

            with output:
                print("Computing... Please wait...")

            layer_labels = None
            vis_params = {}

            try:
                if vis_min.value != "":
                    vis_params["min"] = float(vis_min.value)

                if vis_max.value != "":
                    vis_params["max"] = float(vis_max.value)

                vis_params["opacity"] = float(opacity.value)

                if len(bands_hbox.children) > 0 and (
                    band1_dropdown.value
                    and band2_dropdown.value
                    and band3_dropdown.value
                ):
                    vis_params["bands"] = [
                        band1_dropdown.value,
                        band2_dropdown.value,
                        band3_dropdown.value,
                    ]
                    vis_params["gamma"] = float(gamma.value)

                if len(palette_vbox.children) > 0:
                    if "," in palette.value:
                        vis_params["palette"] = [
                            i.strip() for i in palette.value.split(",")
                        ]
                    elif len(palette.value) > 0:
                        vis_params["palette"] = palette.value.strip()

            except Exception as _:
                with output:
                    print("The vis parmas are invalid.")
                    return

            if labels.value != "" and "," in labels.value:
                try:
                    layer_labels = [i.strip() for i in labels.value.split(",")]
                except Exception as e:
                    raise ValueError(e)

            if collection.value in m.ee_raster_layer_names:
                layer = m.ee_layer_dict[collection.value]
                ee_object = layer["ee_object"]
            elif collection.value in col_options_dict:
                start_date = str(start_month.value).zfill(2) + "-01"
                end_date = str(end_month.value).zfill(2) + "-30"

                if collection.value == "Landsat TM-ETM-OLI Surface Reflectance":
                    ee_object = landsat_timeseries(
                        roi,
                        int(start_year.value),
                        int(end_year.value),
                        start_date,
                        end_date,
                        cloud.value,
                    )
                elif collection.value == "MOD13A2.006 Terra Vegetation Indices":
                    ee_object = modis_timeseries(
                        roi=roi,
                        start_year=int(start_year.value),
                        end_year=int(end_year.value),
                        start_date=start_date,
                        end_date=end_date,
                    )

                elif collection.value == "Sentinel-2 Surface Relectance":
                    ee_object = sentinel2_timeseries(
                        roi,
                        int(start_year.value),
                        int(end_year.value),
                        start_date,
                        end_date,
                        cloud.value,
                    )
                elif collection.value == "USDA NAIP Imagery":

                    if int(start_year.value) < 2009 and (
                        band1_dropdown.value == "N"
                        or band2_dropdown.value == "N"
                        or band3_dropdown.value == "N"
                    ):
                        with output:
                            output.clear_output()
                            print("4-band NAIP imagery not available before 2009.")
                            return

                    ee_object = naip_timeseries(roi, start_year.value, end_year.value)

            m.add_time_slider(
                ee_object,
                region=roi,
                vis_params=vis_params,
                labels=layer_labels,
                time_interval=speed.value,
            )

            output.clear_output()

            if m.colorbar_ctrl is not None:
                m.remove_control(m.colorbar_ctrl)
                m.colorbar_ctrl = None

    apply_btn.on_click(submit_clicked)

    reset_btn = widgets.Button(
        description="Reset",
        button_style="primary",
        style=style,
        layout=widgets.Layout(padding="0px", width=button_width),
    )

    def reset_btn_click(change):
        output.clear_output()
        collection.value = col_options[0]
        region.value = "User-drawn ROI"
        vis.value = ""
        labels.value = "1, 2, 3"
        speed.value = 1

        if m.colorbar_ctrl is not None:
            m.remove_control(m.colorbar_ctrl)
            m.colorbar_ctrl = None

    reset_btn.on_click(reset_btn_click)

    close_btn = widgets.Button(
        description="Close",
        button_style="primary",
        style=style,
        layout=widgets.Layout(padding="0px", width=button_width),
    )

    def close_click(change):
        if m is not None:
            m.toolbar_reset()
            if m.tool_control is not None and m.tool_control in m.controls:
                m.remove_control(m.tool_control)
                m.tool_control = None

            if m.colorbar_ctrl is not None:
                m.remove_control(m.colorbar_ctrl)
                m.colorbar_ctrl = None
        toolbar_widget.close()

    close_btn.on_click(close_click)

    def collection_changed(change):

        if change["new"]:
            selected = change["owner"].value
            if selected in m.ee_layer_dict:
                prebuilt_options.children = []
                labels.value = ""
                region.value = None

                ee_object = m.ee_layer_dict[selected]["ee_object"]
                vis_params = m.ee_layer_dict[selected]["vis_params"]
                if isinstance(ee_object, ee.Image):
                    palette_vbox.children = [
                        widgets.HBox([classes, colormap]),
                        widgets.HBox(
                            [palette, color_picker, add_color, del_color, reset_color]
                        ),
                    ]
                    bands_hbox.children = []

                elif isinstance(ee_object, ee.ImageCollection):

                    first = ee.Image(ee_object.first())
                    band_names = first.bandNames().getInfo()
                    band_count = len(band_names)

                    if band_count > 2:
                        band1_dropdown.options = band_names
                        band2_dropdown.options = band_names
                        band3_dropdown.options = band_names

                        band1_dropdown.value = band_names[2]
                        band2_dropdown.value = band_names[1]
                        band3_dropdown.value = band_names[0]

                        palette_vbox.children = []
                        bands_hbox.children = [
                            bands_label,
                            band1_dropdown,
                            band2_dropdown,
                            band3_dropdown,
                        ]

                    else:
                        palette_vbox.children = [
                            widgets.HBox([classes, colormap]),
                            widgets.HBox(
                                [
                                    palette,
                                    color_picker,
                                    add_color,
                                    del_color,
                                    reset_color,
                                ]
                            ),
                        ]
                        bands_hbox.children = []

                if "min" in vis_params:
                    vis_min.value = str(vis_params["min"])
                if "max" in vis_params:
                    vis_max.value = str(vis_params["max"])
                if "opacity" in vis_params:
                    opacity.value = str(vis_params["opacity"])
                if "gamma" in vis_params:
                    if isinstance(vis_params["gamma"], list):
                        gamma.value = str(vis_params["gamma"][0])
                    else:
                        gamma.value = str(vis_params["gamma"])
                if "palette" in vis_params:
                    palette.value = ", ".join(vis_params["palette"])

            else:
                prebuilt_options.children = [
                    widgets.HBox(
                        [start_year, start_year_label, end_year, end_year_label]
                    ),
                    widgets.HBox(
                        [start_month, start_month_label, end_month, end_month_label]
                    ),
                    cloud,
                ]

                if selected == "MOD13A2.006 Terra Vegetation Indices":
                    palette_vbox.children = [
                        widgets.HBox([classes, colormap]),
                        widgets.HBox(
                            [
                                palette,
                                color_picker,
                                add_color,
                                del_color,
                                reset_color,
                            ]
                        ),
                    ]
                    bands_hbox.children = []

                    palette.value = ", ".join(col_options_dict[selected]["palette"])
                    modis_labels = []
                    for i in range(int(start_year.value), int(end_year.value) + 1):
                        for j in range(1, 13):
                            modis_labels.append(str(i) + "-" + str(j).zfill(2))
                    labels.value = ", ".join(modis_labels)

                else:
                    bands_hbox.children = [
                        bands_label,
                        band1_dropdown,
                        band2_dropdown,
                        band3_dropdown,
                    ]

                    bandnames = col_options_dict[selected]["bandnames"]
                    band1_dropdown.options = bandnames
                    band2_dropdown.options = bandnames
                    band3_dropdown.options = bandnames

                if (
                    selected == "Landsat TM-ETM-OLI Surface Reflectance"
                    or selected == "Sentinel-2 Surface Relectance"
                ):
                    band1_dropdown.value = bandnames[2]
                    band2_dropdown.value = bandnames[1]
                    band3_dropdown.value = bandnames[0]
                    palette_vbox.children = []
                elif selected == "USDA NAIP Imagery":
                    band1_dropdown.value = bandnames[0]
                    band2_dropdown.value = bandnames[1]
                    band3_dropdown.value = bandnames[2]
                    palette_vbox.children = []

                labels.value = ", ".join(
                    str(i)
                    for i in range(int(start_year.value), int(end_year.value) + 1)
                )

                start_year.min = col_options_dict[selected]["start_year"]
                start_year.max = col_options_dict[selected]["end_year"]
                start_year.value = start_year.min
                end_year.min = col_options_dict[selected]["start_year"]
                end_year.max = col_options_dict[selected]["end_year"]
                end_year.value = end_year.max
                vis_min.value = str(col_options_dict[selected]["min"])
                vis_max.value = str(col_options_dict[selected]["max"])

                if selected == "MOD13A2.006 Terra Vegetation Indices":
                    start_year.value = "2001"
                    end_year.value = "2020"
                elif selected == "USDA NAIP Imagery":
                    start_year.value = "2009"
                    end_year.value = "2019"

    collection.observe(collection_changed, "value")

    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        collection,
        region,
        bands_hbox,
        widgets.HBox([vis_min, vis_max]),
        widgets.HBox([opacity, opacity_label, gamma, gamma_label]),
        palette_vbox,
        widgets.HBox([labels, speed, speed_label]),
        prebuilt_options,
        widgets.HBox([apply_btn, reset_btn, close_btn]),
        output,
    ]

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
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                m.toolbar_reset()
            toolbar_widget.close()

            if m.colorbar_ctrl is not None:
                m.remove_control(m.colorbar_ctrl)
                m.colorbar_ctrl = None

    close_button.observe(close_btn_click, "value")

    toolbar_button.value = True
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add_control(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget


def plot_transect(m=None):

    from bqplot import pyplot as plt

    widget_width = "250px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Show or hide the toolbar",
        icon="line-chart",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    layer = widgets.Dropdown(
        options=["Option 1", "Option 2", "Option 3"],
        value=None,
        description="Image:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style={"description_width": "initial"},
    )

    band = widgets.Dropdown(
        options=["Option 1", "Option 2", "Option 3"],
        value=None,
        description="Band:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style={"description_width": "initial"},
    )

    reducer = widgets.Dropdown(
        options=["mean", "median", "min", "max", "mode", "sum", "stdDev", "variance"],
        value="mean",
        description="Stats:",
        layout=widgets.Layout(width="120px", padding=padding),
        style={"description_width": "initial"},
    )

    segments = widgets.IntText(
        value="100",
        description="Segments:",
        placeholder="Number of segments",
        style={"description_width": "initial"},
        layout=widgets.Layout(width="126px", padding=padding),
    )

    dist_interval = widgets.Text(
        value="",
        description="Distance interval (m):",
        placeholder="Optional",
        style={"description_width": "initial"},
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    title = widgets.Text(
        value="",
        description="Plot title:",
        placeholder="Plot title",
        style={"description_width": "initial"},
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    xlabel = widgets.Text(
        value="",
        description="xlabel:",
        placeholder="x-axis",
        style={"description_width": "initial"},
        layout=widgets.Layout(width="123px", padding=padding),
    )

    ylabel = widgets.Text(
        value="",
        description="ylabel:",
        placeholder="y-axis",
        style={"description_width": "initial"},
        layout=widgets.Layout(width="123px", padding=padding),
    )

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Plot", "Reset", "Close"],
        tooltips=["Plot transect", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "80px"

    output = widgets.Output(
        layout=widgets.Layout(max_width="500px", max_height="265px", padding=padding)
    )

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        layer,
        band,
        widgets.HBox([reducer, segments]),
        dist_interval,
        title,
        widgets.HBox([xlabel, ylabel]),
        buttons,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    if m is not None:
        layer.options = m.ee_raster_layer_names
        if len(layer.options) > 0:
            image = m.ee_layer_dict[layer.value]["ee_object"]
            if isinstance(image, ee.ImageCollection):
                image = image.toBands()
            band.options = image.bandNames().getInfo()

        transect_control = ipyleaflet.WidgetControl(
            widget=output, position="bottomright"
        )
        m.add_control(transect_control)
        m.transect_control = transect_control

    def layer_changed(change):
        if change["new"]:
            if m is not None:
                image = m.ee_layer_dict[layer.value]["ee_object"]
                if isinstance(image, ee.ImageCollection):
                    image = image.toBands()
                band.options = image.bandNames().getInfo()

    layer.observe(layer_changed, "value")

    def handle_toolbar_event(event):

        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                if m.transect_control is not None and m.transect_control in m.controls:
                    m.remove_control(m.transect_control)
                    m.transect_control = None
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Plot":
            with output:
                output.clear_output()
                if m is not None:
                    if m.user_roi is not None:
                        line = m.user_roi
                        geom_type = line.type().getInfo()
                        if geom_type != "LineString":
                            print("Use drawing tool to draw a line")
                        else:
                            image = m.ee_layer_dict[layer.value]["ee_object"]
                            if isinstance(image, ee.ImageCollection):
                                image = image.toBands()
                            image = image.select([band.value])
                            if dist_interval.value == "":
                                dist = None
                            else:
                                dist = float(dist_interval.value)

                            print("Computing ...")
                            df = extract_transect(
                                image,
                                line,
                                reducer.value,
                                int(segments.value),
                                dist,
                                to_pandas=True,
                            )
                            output.clear_output()
                            fig = plt.figure(title=title.value)
                            fig.layout.width = output.layout.max_width
                            fig.layout.height = output.layout.max_height
                            plt.plot(df["distance"], df[reducer.value])
                            plt.xlabel(xlabel.value)
                            plt.ylabel(ylabel.value)
                            plt.show()
                    else:
                        print("Use drawing tool to draw a line")
        elif change["new"] == "Reset":
            output.clear_output()
        elif change["new"] == "Close":
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                if m.transect_control is not None and m.transect_control in m.controls:
                    m.remove_control(m.transect_control)
                    m.transect_control = None
            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = True
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add_control(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget


def sankee_gui(m=None):

    import sankee

    widget_width = "250px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="random",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    region = widgets.Dropdown(
        options=["User-drawn ROI"],
        value="User-drawn ROI",
        description="Region:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style={"description_width": "initial"},
    )

    def region_changed(change):
        if change["new"] == "Las Vegas":
            if m is not None:
                las_vegas = ee.Geometry.Polygon(
                    [
                        [
                            [-115.01184401606046, 36.24170785506492],
                            [-114.98849806879484, 36.29928186470082],
                            [-115.25628981684171, 36.35238941394592],
                            [-115.34692702387296, 36.310348922031565],
                            [-115.37988600824796, 36.160811202271944],
                            [-115.30298171137296, 36.03653336474891],
                            [-115.25628981684171, 36.05207884201088],
                            [-115.26590285395109, 36.226199908103695],
                            [-115.19174513910734, 36.25499793268206],
                        ]
                    ]
                )
                m.addLayer(las_vegas, {}, "Las Vegas")
                m.centerObject(las_vegas, 10)

    region.observe(region_changed, "value")

    dataset = widgets.Dropdown(
        options=[
            "NLCD - National Land Cover Database",
            "MCD12Q1 - MODIS Global Land Cover",
            "CGLS - Copernicus Global Land Cover",
            "LCMS - Land Change Monitoring System",
        ],
        value="NLCD - National Land Cover Database",
        description="Dataset:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style={"description_width": "initial"},
    )

    NLCD_options = ["2001", "2004", "2006", "2008", "2011", "2013", "2016"]
    MODIS_options = [str(y) for y in range(2001, 2020)]
    CGLS_options = [str(y) for y in range(2015, 2020)]
    LCMS_options = [str(y) for y in range(1985, 2021)]

    before = widgets.Dropdown(
        options=NLCD_options,
        value="2001",
        description="Before:",
        layout=widgets.Layout(width="123px", padding=padding),
        style={"description_width": "initial"},
    )

    after = widgets.Dropdown(
        options=NLCD_options,
        value="2016",
        description="After:",
        layout=widgets.Layout(width="123px", padding=padding),
        style={"description_width": "initial"},
    )

    def dataset_changed(change):
        if change["new"] == "NLCD - National Land Cover Database":
            before.options = NLCD_options
            after.options = NLCD_options
            before.value = NLCD_options[0]
            after.value = NLCD_options[-1]
        elif change["new"] == "MCD12Q1 - MODIS Global Land Cover":
            before.options = MODIS_options
            after.options = MODIS_options
            before.value = MODIS_options[0]
            after.value = MODIS_options[-1]
        elif change["new"] == "CGLS - Copernicus Global Land Cover":
            before.options = CGLS_options
            after.options = CGLS_options
            before.value = CGLS_options[0]
            after.value = CGLS_options[-1]
        elif change["new"] == "LCMS - Land Change Monitoring System":
            before.options = LCMS_options
            after.options = LCMS_options
            before.value = LCMS_options[0]
            after.value = LCMS_options[-1]

    dataset.observe(dataset_changed, "value")

    dataset_template = {
        "NLCD - National Land Cover Database": sankee.datasets.NLCD2016,
        "MCD12Q1 - MODIS Global Land Cover": sankee.datasets.MODIS_LC_TYPE1,
        "CGLS - Copernicus Global Land Cover": sankee.datasets.CGLS_LC100,
        "LCMS - Land Change Monitoring System": sankee.datasets.LCMS_LC,
    }

    band_name = {
        "NLCD - National Land Cover Database": "landcover",
        "MCD12Q1 - MODIS Global Land Cover": "LC_Type1",
        "CGLS - Copernicus Global Land Cover": "discrete_classification",
        "LCMS - Land Change Monitoring System": "Land_Cover",
    }

    samples = widgets.IntText(
        value=1000,
        description="Samples:",
        placeholder="The number of samples points to randomly generate for characterizing all images",
        style={"description_width": "initial"},
        layout=widgets.Layout(width="133px", padding=padding),
    )

    classes = widgets.IntText(
        value=6,
        description="Classes:",
        style={"description_width": "initial"},
        layout=widgets.Layout(width="113px", padding=padding),
    )

    title = widgets.Text(
        value="Land Cover Change",
        description="Title:",
        style={"description_width": "initial"},
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Apply", "Reset", "Close"],
        tooltips=["Apply", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "80px"

    output = widgets.Output(layout=widgets.Layout(padding=padding))

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        region,
        dataset,
        widgets.HBox([before, after]),
        widgets.HBox([samples, classes]),
        title,
        buttons,
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    if m is not None:
        if "Las Vegas" not in m.ee_vector_layer_names:
            region.options = ["User-drawn ROI", "Las Vegas"] + m.ee_vector_layer_names
        else:
            region.options = ["User-drawn ROI"] + m.ee_vector_layer_names

        plot_close_btn = widgets.Button(
            tooltip="Close the plot",
            icon="times",
            layout=widgets.Layout(
                height="28px", width="28px", padding="0px 0px 0px 0px"
            ),
        )

        def plot_close_btn_clicked(b):
            plot_widget.children = []

        plot_close_btn.on_click(plot_close_btn_clicked)

        plot_reset_btn = widgets.Button(
            tooltip="Reset the plot",
            icon="home",
            layout=widgets.Layout(
                height="28px", width="28px", padding="0px 0px 0px 0px"
            ),
        )

        def plot_reset_btn_clicked(b):

            m.sankee_plot.update_layout(
                width=600,
                height=250,
                margin=dict(l=10, r=10, b=10, t=50, pad=5),
            )
            with plot_output:
                plot_output.clear_output()
                display(m.sankee_plot)

        plot_reset_btn.on_click(plot_reset_btn_clicked)

        plot_fullscreen_btn = widgets.Button(
            tooltip="Fullscreen the plot",
            icon="arrows-alt",
            layout=widgets.Layout(
                height="28px", width="28px", padding="0px 0px 0px 0px"
            ),
        )

        def plot_fullscreen_btn_clicked(b):

            m.sankee_plot.update_layout(
                width=1030,
                height=int(m.layout.height[:-2]) - 60,
                margin=dict(l=10, r=10, b=10, t=50, pad=5),
            )
            with plot_output:
                plot_output.clear_output()
                display(m.sankee_plot)

        plot_fullscreen_btn.on_click(plot_fullscreen_btn_clicked)

        width_btn = widgets.Button(
            tooltip="Change plot width",
            icon="arrows-h",
            layout=widgets.Layout(
                height="28px", width="28px", padding="0px 0px 0px 0px"
            ),
        )

        def width_btn_clicked(b):
            m.sankee_plot.update_layout(
                width=1030,
                margin=dict(l=10, r=10, b=10, t=50, pad=5),
            )
            with plot_output:
                plot_output.clear_output()
                display(m.sankee_plot)

        width_btn.on_click(width_btn_clicked)

        height_btn = widgets.Button(
            tooltip="Change plot height",
            icon="arrows-v",
            layout=widgets.Layout(
                height="28px", width="28px", padding="0px 0px 0px 0px"
            ),
        )

        def height_btn_clicked(b):
            m.sankee_plot.update_layout(
                height=int(m.layout.height[:-2]) - 60,
                margin=dict(l=10, r=10, b=10, t=50, pad=5),
            )
            with plot_output:
                plot_output.clear_output()
                display(m.sankee_plot)

        height_btn.on_click(height_btn_clicked)

        width_slider = widgets.IntSlider(
            value=600,
            min=400,
            max=1030,
            step=10,
            description="",
            readout=False,
            continuous_update=False,
            layout=widgets.Layout(width="100px", padding=padding),
            style={"description_width": "initial"},
        )

        width_slider_label = widgets.Label(
            layout=widgets.Layout(padding="0px 10px 0px 0px")
        )
        widgets.jslink((width_slider, "value"), (width_slider_label, "value"))

        def width_changed(change):
            if change["new"]:

                m.sankee_plot.update_layout(
                    width=width_slider.value,
                    margin=dict(l=10, r=10, b=10, t=50, pad=5),
                )
                with plot_output:
                    plot_output.clear_output()
                    display(m.sankee_plot)

        width_slider.observe(width_changed, "value")

        height_slider = widgets.IntSlider(
            value=250,
            min=200,
            max=int(m.layout.height[:-2]) - 60,
            step=10,
            description="",
            readout=False,
            continuous_update=False,
            layout=widgets.Layout(width="100px", padding=padding),
            style={"description_width": "initial"},
        )

        height_slider_label = widgets.Label()
        widgets.jslink((height_slider, "value"), (height_slider_label, "value"))

        def height_changed(change):
            if change["new"]:

                m.sankee_plot.update_layout(
                    height=height_slider.value,
                    margin=dict(l=10, r=10, b=10, t=50, pad=5),
                )
                with plot_output:
                    plot_output.clear_output()
                    display(m.sankee_plot)

        height_slider.observe(height_changed, "value")

        plot_output = widgets.Output()

        plot_widget = widgets.VBox([plot_output])

        sankee_control = ipyleaflet.WidgetControl(
            widget=plot_widget, position="bottomright"
        )
        m.add_control(sankee_control)
        m.sankee_control = sankee_control

    def handle_toolbar_event(event):

        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                if m.sankee_control is not None and m.sankee_control in m.controls:
                    m.remove_control(m.sankee_control)
                    m.sankee_control = None
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Apply":
            with output:
                output.clear_output()
                plot_output.clear_output()
                print("Running ...")

            if m is not None:
                exclude_classes = []

                if "NLCD" in dataset.value:
                    before_img = ee.Image(f"USGS/NLCD/NLCD{before.value}")
                    after_img = ee.Image(f"USGS/NLCD/NLCD{after.value}")
                    vis_params = {}
                elif "MODIS" in dataset.value:
                    before_img = ee.Image(f"MODIS/006/MCD12Q1/{before.value}_01_01")
                    after_img = ee.Image(f"MODIS/006/MCD12Q1/{after.value}_01_01")
                    vis_params = {
                        "min": 1.0,
                        "max": 17.0,
                        "palette": [
                            "05450a",
                            "086a10",
                            "54a708",
                            "78d203",
                            "009900",
                            "c6b044",
                            "dcd159",
                            "dade48",
                            "fbff13",
                            "b6ff05",
                            "27ff87",
                            "c24f44",
                            "a5a5a5",
                            "ff6d4c",
                            "69fff8",
                            "f9ffa4",
                            "1c0dff",
                        ],
                    }
                elif "CGLS" in dataset.value:
                    before_img = ee.Image(
                        f"COPERNICUS/Landcover/100m/Proba-V-C3/Global/{before.value}"
                    )
                    after_img = ee.Image(
                        f"COPERNICUS/Landcover/100m/Proba-V-C3/Global/{after.value}"
                    )
                    vis_params = {}
                elif "LCMS" in dataset.value:
                    before_img = ee.Image(
                        f"USFS/GTAC/LCMS/v2020-5/LCMS_CONUS_v2020-5_{before.value}"
                    )
                    after_img = ee.Image(
                        f"USFS/GTAC/LCMS/v2020-5/LCMS_CONUS_v2020-5_{after.value}"
                    )
                    vis_params = {}
                    # LCMS Land Cover class 15 is a no data mask and should be excluded
                    exclude_classes.append(15)

                img_list = [before_img, after_img]
                label_list = [before.value, after.value]

                image1 = before_img.select(band_name[dataset.value])
                image2 = after_img.select(band_name[dataset.value])

                if region.value != "User-drawn ROI" or (
                    region.value == "User-drawn ROI" and m.user_roi is not None
                ):

                    if region.value == "User-drawn ROI":
                        geom = m.user_roi
                        image1 = image1.clip(geom)
                        image2 = image2.clip(geom)
                    else:
                        roi_object = m.ee_layer_dict[region.value]["ee_object"]
                        if region.value == "Las Vegas":
                            m.centerObject(roi_object, 10)
                        if isinstance(roi_object, ee.Geometry):
                            geom = roi_object
                            image1 = image1.clip(geom)
                            image2 = image2.clip(geom)
                        else:
                            roi_object = ee.FeatureCollection(roi_object)
                            image1 = image1.clipToCollection(roi_object)
                            image2 = image2.clipToCollection(roi_object)
                            geom = roi_object.geometry()

                    if len(title.value) > 0:
                        plot_title = title.value
                    else:
                        plot_title = None
                    m.default_style = {"cursor": "wait"}
                    plot = sankee.sankify(
                        img_list,
                        geom,
                        label_list,
                        dataset_template[dataset.value],
                        max_classes=classes.value,
                        n=int(samples.value),
                        title=plot_title,
                        exclude=exclude_classes,
                    )

                    output.clear_output()
                    plot_output.clear_output()
                    with plot_output:
                        plot.update_layout(
                            width=600,
                            height=250,
                            margin=dict(l=10, r=10, b=10, t=50, pad=5),
                        )
                        plot_widget.children = [
                            widgets.HBox(
                                [
                                    plot_close_btn,
                                    plot_reset_btn,
                                    plot_fullscreen_btn,
                                    width_btn,
                                    width_slider,
                                    width_slider_label,
                                    height_btn,
                                    height_slider,
                                    height_slider_label,
                                ]
                            ),
                            plot_output,
                        ]
                        display(plot)

                    m.sankee_plot = plot
                    m.addLayer(image1, vis_params, before.value)
                    m.addLayer(image2, vis_params, after.value)
                    m.default_style = {"cursor": "default"}

                else:
                    with output:
                        output.clear_output()
                        print("Draw a polygon on the map.")

        elif change["new"] == "Reset":
            output.clear_output()
            plot_output.clear_output()
            plot_widget.children = []

        elif change["new"] == "Close":
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                if m.sankee_control is not None and m.sankee_control in m.controls:
                    m.remove_control(m.sankee_control)
                    m.sankee_control = None
            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = True
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add_control(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget


def split_basemaps(
    m, layers_dict=None, left_name=None, right_name=None, width="120px", **kwargs
):

    from .basemaps import basemap_tiles

    controls = m.controls
    layers = m.layers
    m.layers = [m.layers[0]]
    m.clear_controls()

    add_zoom = True
    add_fullscreen = True

    if layers_dict is None:
        layers_dict = {}
        keys = dict(basemap_tiles).keys()
        for key in keys:
            if isinstance(basemap_tiles[key], ipyleaflet.WMSLayer):
                pass
            else:
                layers_dict[key] = basemap_tiles[key]

    keys = list(layers_dict.keys())
    if left_name is None:
        left_name = keys[0]
    if right_name is None:
        right_name = keys[-1]

    left_layer = layers_dict[left_name]
    right_layer = layers_dict[right_name]

    control = ipyleaflet.SplitMapControl(left_layer=left_layer, right_layer=right_layer)
    m.add_control(control)

    left_dropdown = widgets.Dropdown(
        options=keys, value=left_name, layout=widgets.Layout(width=width)
    )

    left_control = ipyleaflet.WidgetControl(widget=left_dropdown, position="topleft")
    m.add_control(left_control)

    right_dropdown = widgets.Dropdown(
        options=keys, value=right_name, layout=widgets.Layout(width=width)
    )

    right_control = ipyleaflet.WidgetControl(widget=right_dropdown, position="topright")
    m.add_control(right_control)

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        # button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    def close_btn_click(change):
        if change["new"]:
            m.controls = controls
            m.layers = layers

    close_button.observe(close_btn_click, "value")
    close_control = ipyleaflet.WidgetControl(
        widget=close_button, position="bottomright"
    )
    m.add_control(close_control)

    if add_zoom:
        m.add_control(ipyleaflet.ZoomControl())
    if add_fullscreen:
        m.add_control(ipyleaflet.FullScreenControl())
    m.add_control(ipyleaflet.ScaleControl(position="bottomleft"))

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
