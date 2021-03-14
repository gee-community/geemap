"""Module for dealing with the toolbar.
"""
import ee
import os
import ipyevents
import ipywidgets as widgets
from ipyleaflet import WidgetControl, DrawControl
from IPython.core.display import display
from ipyfilechooser import FileChooser
from .common import *


def tool_template(m):

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
            m.toolbar_reset()
            if m.tool_control is not None and m.tool_control in m.controls:
                m.remove_control(m.tool_control)
                m.tool_control = None
                toolbar_widget.close()
        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_control = WidgetControl(widget=toolbar_widget, position="topright")

    if toolbar_control not in m.controls:
        m.add_control(toolbar_control)
        m.tool_control = toolbar_control

    toolbar_button.value = True


def open_data_widget(m):
    """A widget for opening local vector/raster data.

    Args:
        m (object): geemap.Map
    """
    tool_output = widgets.Output()
    tool_output_ctrl = WidgetControl(widget=tool_output, position="topright")

    if m.tool_output_ctrl is not None and m.tool_output_ctrl in m.controls:
        m.remove_control(m.tool_output_ctrl)

    file_type = widgets.ToggleButtons(
        options=["Shapefile", "GeoJSON", "GeoTIFF"],
        tooltips=[
            "Open a shapefile",
            "Open a GeoJSON file",
            "Open a GeoTIFF",
        ],
    )

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
        [file_type, file_chooser, layer_name, convert_hbox, raster_options, ok_cancel]
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

    def file_type_changed(change):
        ok_cancel.value = None
        file_chooser.default_path = os.getcwd()
        file_chooser.reset()
        layer_name.value = file_type.value
        if change["new"] == "Shapefile":
            file_chooser.filter_pattern = "*.shp"
            raster_options.children = []
            convert_hbox.children = [convert_bool]
        elif change["new"] == "GeoJSON":
            file_chooser.filter_pattern = "*.geojson"
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
                            m.centerObject(ee_object)
                        else:
                            m.add_shapefile(
                                file_path, style=None, layer_name=layer_name.value
                            )
                    elif ext.lower() == ".geojson":
                        if convert_bool.value:
                            ee_object = geojson_to_ee(file_path)
                            m.addLayer(ee_object, {}, layer_name.value)
                            m.centerObject(ee_object)
                        else:
                            m.add_geojson(
                                file_path, style=None, layer_name=layer_name.value
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

    basemap_control = WidgetControl(widget=basemap_widget, position="topright")
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
            from .conversion import js_snippet_to_py, create_new_cell

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
    widget_control = WidgetControl(widget=full_widget, position="topright")
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
            draw_control = DrawControl(
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
                if isinstance(control, DrawControl):
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

    widget_control = WidgetControl(widget=full_widget, position="topright")
    m.add_control(widget_control)
    m.training_ctrl = widget_control
