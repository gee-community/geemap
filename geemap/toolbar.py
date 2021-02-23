"""Module for dealing with the toolbar.
"""
import os
import ipywidgets as widgets
from ipyleaflet import WidgetControl
from IPython.core.display import display
from ipyfilechooser import FileChooser
from .common import *


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
            old_basemap = old_basemap = m.layers[1]
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
