"""Main module for interactive mapping using Google Earth Engine Python API and ipyleaflet.
Keep in mind that Earth Engine functions use both camel case and snake case, such as setOptions(), setCenter(), centerObject(), addLayer().
ipyleaflet functions use snake case, such as add_tile_layer(), add_wms_layer(), add_minimap().
"""

import colour
import ee
import geocoder
import ipyleaflet
import math
import os
import time
import ipywidgets as widgets
from bqplot import pyplot as plt
from ipyfilechooser import FileChooser
from ipyleaflet import *
from ipytree import Tree, Node
from IPython.display import display
from .basemaps import ee_basemaps
from .conversion import *
from .legends import builtin_legends


def ee_initialize(token_name='EARTHENGINE_TOKEN'):
    """Authenticates Earth Engine and initialize an Earth Engine session

    """
    try:
        ee_token = os.environ.get(token_name)
        if ee_token is not None:
            credential = '{"refresh_token":"%s"}' % ee_token
            credential_file_path = os.path.expanduser("~/.config/earthengine/")
            os.makedirs(credential_file_path, exist_ok=True)
            with open(credential_file_path + 'credentials', 'w') as file:
                file.write(credential)
        elif in_colab_shell():
            if credentials_in_drive() and (not credentials_in_colab()):
                copy_credentials_to_colab()
            elif not credentials_in_colab:
                ee.Authenticate()
                if is_drive_mounted() and (not credentials_in_drive()):
                    copy_credentials_to_drive()
            else:
                if is_drive_mounted():
                    copy_credentials_to_drive()

        ee.Initialize()
    except:
        ee.Authenticate()
        ee.Initialize()


class Map(ipyleaflet.Map):
    """The Map class inherits from ipyleaflet.Map. The arguments you can pass to the Map can be found at https://ipyleaflet.readthedocs.io/en/latest/api_reference/map.html. By default, the Map will add Google Maps as the basemap. Set add_google_map = False to use OpenStreetMap as the basemap.

    Returns:
        object: ipyleaflet map object.
    """

    def __init__(self, **kwargs):

        # Authenticates Earth Engine and initializes an Earth Engine session
        ee_initialize()

        # Default map center location and zoom level
        latlon = [40, -100]
        zoom = 4

        # Interchangeable parameters between ipyleaflet and folium
        if 'location' in kwargs.keys():
            kwargs['center'] = kwargs['location']
            kwargs.pop('location')
        if 'center' in kwargs.keys():
            latlon = kwargs['center']
        else:
            kwargs['center'] = latlon

        if 'zoom_start' in kwargs.keys():
            kwargs['zoom'] = kwargs['zoom_start']
            kwargs.pop('zoom_start')
        if 'zoom' in kwargs.keys():
            zoom = kwargs['zoom']
        else:
            kwargs['zoom'] = zoom

        if 'add_google_map' not in kwargs.keys():
            kwargs['add_google_map'] = True

        if 'show_attribution' not in kwargs.keys():
            kwargs['show_attribution'] = True

        if 'scroll_wheel_zoom' not in kwargs.keys():
            kwargs['scroll_wheel_zoom'] = True

        if 'zoom_control' not in kwargs.keys():
            kwargs['zoom_control'] = True

        if 'height' not in kwargs.keys():
            kwargs['height'] = '550px'

        # Inherits the ipyleaflet Map class
        super().__init__(**kwargs)
        self.layout.height = kwargs['height']

        self.clear_controls()

        self.draw_count = 0  # The number of shapes drawn by the user using the DrawControl
        # The list of Earth Engine Geometry objects converted from geojson
        self.draw_features = []
        # The Earth Engine Geometry object converted from the last drawn feature
        self.draw_last_feature = None
        self.draw_layer = None
        self.draw_last_json = None
        self.draw_last_bounds = None
        self.user_roi = None
        self.user_rois = None

        self.roi_start = False
        self.roi_end = False
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
        self.legend_control = None

        self.ee_layers = []
        self.ee_layer_names = []
        self.ee_raster_layers = []
        self.ee_raster_layer_names = []
        self.ee_layer_dict = {}

        self.search_locations = None
        self.search_loc_marker = None
        self.search_loc_geom = None
        self.search_datasets = None
        self.screenshot = None
        self.toolbar = None
        self.toolbar_button = None

        # Adds search button and search box
        search_button = widgets.ToggleButton(
            value=False,
            tooltip='Search location/data',
            icon='globe'
        )
        search_button.layout.width = '36px'

        search_type = widgets.ToggleButtons(
            options=['name/address', 'lat-lon', 'data'],
            tooltips=['Search by place name or address',
                      'Search by lat-lon coordinates', 'Search Earth Engine data catalog']
        )
        search_type.style.button_width = '110px'

        search_box = widgets.Text(
            placeholder='Search by place name or address',
            tooltip='Search location',
        )
        search_box.layout.width = '340px'

        search_output = widgets.Output(
            layout={'max_width': '340px', 'max_height': '250px', 'overflow': 'scroll'})

        search_results = widgets.RadioButtons()

        assets_dropdown = widgets.Dropdown()
        assets_dropdown.layout.min_width = '279px'
        assets_dropdown.layout.max_width = '279px'
        assets_dropdown.options = []

        import_btn = widgets.Button(
            description='import',
            button_style='primary',
            tooltip='Click to import the selected asset',
        )
        import_btn.layout.min_width = '57px'
        import_btn.layout.max_width = '57px'

        def import_btn_clicked(b):
            if assets_dropdown.value != '':
                datasets = self.search_datasets
                dataset = datasets[assets_dropdown.index]
                dataset_uid = 'dataset_' + random_string(string_length=3)
                line1 = '{} = {}\n'.format(
                    dataset_uid, dataset['ee_id_snippet'])
                line2 = 'Map.addLayer(' + dataset_uid + \
                    ', {}, "' + dataset['id'] + '")'
                contents = ''.join([line1, line2])
                create_code_cell(contents)

        import_btn.on_click(import_btn_clicked)

        html_widget = widgets.HTML()

        def dropdown_change(change):
            dropdown_index = assets_dropdown.index
            if dropdown_index is not None and dropdown_index >= 0:
                with search_output:
                    search_output.clear_output(wait=True)
                    print('Loading ...')
                    datasets = self.search_datasets
                    dataset = datasets[dropdown_index]
                    dataset_html = ee_data_html(dataset)
                    html_widget.value = dataset_html
                    search_output.clear_output(wait=True)
                    display(html_widget)

        assets_dropdown.observe(dropdown_change, names='value')

        assets_combo = widgets.HBox()
        assets_combo.children = [import_btn, assets_dropdown]

        def search_result_change(change):
            result_index = search_results.index
            locations = self.search_locations
            location = locations[result_index]
            latlon = (location.lat, location.lng)
            self.search_loc_geom = ee.Geometry.Point(
                location.lng, location.lat)
            marker = self.search_loc_marker
            marker.location = latlon
            self.center = latlon

        search_results.observe(search_result_change, names='value')

        def search_btn_click(change):
            if change['new']:
                search_widget.children = [search_button, search_result_widget]
            else:
                search_widget.children = [search_button]
                search_result_widget.children = [search_type, search_box]

        search_button.observe(search_btn_click, 'value')

        def search_type_changed(change):
            search_box.value = ''
            search_output.clear_output()
            if change['new'] == 'name/address':
                search_box.placeholder = 'Search by place name or address, e.g., Paris'
                assets_dropdown.options = []
                search_result_widget.children = [
                    search_type, search_box, search_output]
            elif change['new'] == 'lat-lon':
                search_box.placeholder = 'Search by lat-lon, e.g., 40, -100'
                assets_dropdown.options = []
                search_result_widget.children = [
                    search_type, search_box, search_output]
            elif change['new'] == 'data':
                search_box.placeholder = 'Search GEE data catalog by keywords, e.g., elevation'
                search_result_widget.children = [
                    search_type, search_box, assets_combo, search_output]

        search_type.observe(search_type_changed, names='value')

        def search_box_callback(text):

            if text.value != '':

                if search_type.value == 'name/address':
                    g = geocode(text.value)
                elif search_type.value == 'lat-lon':
                    g = geocode(text.value, reverse=True)
                    if g is None and latlon_from_text(text.value):
                        search_output.clear_output()
                        latlon = latlon_from_text(text.value)
                        self.search_loc_geom = ee.Geometry.Point(
                            latlon[1], latlon[0])
                        if self.search_loc_marker is None:
                            marker = Marker(
                                location=latlon, draggable=False, name='Search location')
                            self.search_loc_marker = marker
                            self.add_layer(marker)
                            self.center = latlon
                        else:
                            marker = self.search_loc_marker
                            marker.location = latlon
                            self.center = latlon
                        with search_output:
                            print('No address found for {}'.format(latlon))
                        return
                elif search_type.value == 'data':
                    search_output.clear_output()
                    with search_output:
                        print('Searching ...')
                    self.default_style = {'cursor': 'wait'}
                    ee_assets = search_ee_data(text.value)
                    self.search_datasets = ee_assets
                    asset_titles = [x['title'] for x in ee_assets]
                    assets_dropdown.options = asset_titles
                    search_output.clear_output()
                    if len(ee_assets) > 0:
                        html_widget.value = ee_data_html(ee_assets[0])
                    with search_output:
                        display(html_widget)

                    self.default_style = {'cursor': 'default'}

                    return

                self.search_locations = g
                if g is not None and len(g) > 0:
                    top_loc = g[0]
                    latlon = (top_loc.lat, top_loc.lng)
                    self.search_loc_geom = ee.Geometry.Point(
                        top_loc.lng, top_loc.lat)
                    if self.search_loc_marker is None:
                        marker = Marker(
                            location=latlon, draggable=False, name='Search location')
                        self.search_loc_marker = marker
                        self.add_layer(marker)
                        self.center = latlon
                    else:
                        marker = self.search_loc_marker
                        marker.location = latlon
                        self.center = latlon
                    search_results.options = [x.address for x in g]
                    search_result_widget.children = [
                        search_type, search_box, search_output]
                    with search_output:
                        search_output.clear_output(wait=True)
                        display(search_results)
                else:
                    with search_output:
                        search_output.clear_output()
                        print('No results could be found.')

        search_box.on_submit(search_box_callback)

        search_result_widget = widgets.VBox()
        search_result_widget.children = [search_type, search_box]

        search_widget = widgets.HBox()
        search_widget.children = [search_button]
        data_control = WidgetControl(
            widget=search_widget, position='topleft')

        self.add_control(control=data_control)

        search_marker = Marker(icon=AwesomeIcon(
            name="check", marker_color='green', icon_color='darkgreen'))
        search = SearchControl(position="topleft",
                               url='https://nominatim.openstreetmap.org/search?format=json&q={s}',
                               zoom=5,
                               property_name='display_name',
                               marker=search_marker
                               )
        self.add_control(search)

        if kwargs['zoom_control']:
            self.add_control(ZoomControl(position='topleft'))

        layer_control = LayersControl(position='topright')
        self.add_control(layer_control)
        self.layer_control = layer_control

        scale = ScaleControl(position='bottomleft')
        self.add_control(scale)
        self.scale_control = scale

        fullscreen = FullScreenControl()
        self.add_control(fullscreen)
        self.fullscreen_control = fullscreen

        measure = MeasureControl(
            position='bottomleft',
            active_color='orange',
            primary_length_unit='kilometers'
        )
        self.add_control(measure)
        self.measure_control = measure

        if kwargs.get('add_google_map'):
            self.add_layer(ee_basemaps['ROADMAP'])

        if kwargs.get('show_attribution'):
            self.add_control(AttributionControl(position='bottomright'))

        draw_control = DrawControl(marker={'shapeOptions': {'color': '#0000FF'}},
                                   rectangle={'shapeOptions': {
                                       'color': '#0000FF'}},
                                   circle={'shapeOptions': {
                                       'color': '#0000FF'}},
                                   circlemarker={},
                                   )

        draw_control_lite = DrawControl(marker={},
                                        rectangle={'shapeOptions': {
                                            'color': '#0000FF'}},
                                        circle={'shapeOptions': {
                                            'color': '#0000FF'}},
                                        circlemarker={},
                                        polyline={},
                                        polygon={}
                                        )
        # Handles draw events

        def handle_draw(target, action, geo_json):
            try:
                # print(geo_json)
                # geo_json = adjust_longitude(geo_json)
                # print(geo_json)
                self.roi_start = True
                self.draw_count += 1
                geom = geojson_to_ee(geo_json, False)
                self.user_roi = geom
                feature = ee.Feature(geom)
                self.draw_last_json = geo_json
                self.draw_last_bounds = minimum_bounding_box(geo_json)
                self.draw_last_feature = feature
                self.draw_features.append(feature)
                collection = ee.FeatureCollection(self.draw_features)
                self.user_rois = collection
                ee_draw_layer = ee_tile_layer(
                    collection, {'color': 'blue'}, 'Drawn Features', True, 0.5)

                if self.draw_count == 1:
                    self.add_layer(ee_draw_layer)
                    self.draw_layer = ee_draw_layer
                else:
                    self.substitute_layer(self.draw_layer, ee_draw_layer)
                    self.draw_layer = ee_draw_layer

                draw_control.clear()

                self.roi_end = True
                self.roi_start = False
            except Exception as e:
                print(e)
                print("There was an error creating Earth Engine Feature.")
                self.draw_count = 0
                self.draw_features = []
                self.draw_last_feature = None
                self.draw_layer = None
                self.user_roi = None
                self.roi_start = False
                self.roi_end = False

        draw_control.on_draw(handle_draw)
        self.add_control(draw_control)
        self.draw_control = draw_control
        self.draw_control_lite = draw_control_lite

        # Dropdown widget for plotting
        self.plot_dropdown_control = None
        self.plot_dropdown_widget = None
        self.plot_options = {}

        self.plot_marker_cluster = MarkerCluster(name="Marker Cluster")
        self.plot_coordinates = []
        self.plot_markers = []
        self.plot_last_click = []
        self.plot_all_clicks = []

        # Adds Inspector widget
        inspector_checkbox = widgets.Checkbox(
            value=False,
            description='Inspector',
            indent=False,
            layout=widgets.Layout(height='18px')
        )
        inspector_checkbox.layout.width = '13ex'

        # Adds Plot widget
        plot_checkbox = widgets.Checkbox(
            value=False,
            description='Plotting',
            indent=False,
        )
        plot_checkbox.layout.width = '13ex'
        self.plot_checkbox = plot_checkbox

        vb = widgets.VBox(children=[inspector_checkbox, plot_checkbox])

        chk_control = WidgetControl(widget=vb, position='topright')
        self.add_control(chk_control)
        self.inspector_control = chk_control

        self.inspector_checked = inspector_checkbox.value
        self.plot_checked = plot_checkbox.value

        def inspect_chk_changed(b):
            self.inspector_checked = inspector_checkbox.value
            if not self.inspector_checked:
                output.clear_output()
        inspector_checkbox.observe(inspect_chk_changed)

        output = widgets.Output(layout={'border': '1px solid black'})
        output_control = WidgetControl(widget=output, position='topright')
        self.add_control(output_control)

        def plot_chk_changed(button):

            if button['name'] == 'value' and button['new']:
                self.plot_checked = True
                plot_dropdown_widget = widgets.Dropdown(
                    options=list(self.ee_raster_layer_names),
                )
                plot_dropdown_widget.layout.width = '18ex'
                self.plot_dropdown_widget = plot_dropdown_widget
                plot_dropdown_control = WidgetControl(
                    widget=plot_dropdown_widget, position='topright')
                self.plot_dropdown_control = plot_dropdown_control
                self.add_control(plot_dropdown_control)
                self.remove_control(self.draw_control)
                self.add_control(self.draw_control_lite)
            elif button['name'] == 'value' and (not button['new']):
                self.plot_checked = False
                plot_dropdown_widget = self.plot_dropdown_widget
                plot_dropdown_control = self.plot_dropdown_control
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
                if self.plot_marker_cluster is not None and self.plot_marker_cluster in self.layers:
                    self.remove_layer(self.plot_marker_cluster)
                self.remove_control(self.draw_control_lite)
                self.add_control(self.draw_control)

        plot_checkbox.observe(plot_chk_changed)

        tool_output = widgets.Output()
        tool_output.clear_output(wait=True)

        save_map_widget = widgets.VBox()

        save_type = widgets.ToggleButtons(
            options=['HTML', 'PNG', 'JPG'],
            tooltips=['Save the map as an HTML file',
                      'Take a screenshot and save as a PNG file',
                      'Take a screenshot and save as a JPG file']
        )

        # download_dir = os.getcwd()
        file_chooser = FileChooser(os.getcwd())
        file_chooser.default_filename = 'my_map.html'
        file_chooser.use_dir_icons = False

        ok_cancel = widgets.ToggleButtons(
            options=['OK', 'Cancel'],
            tooltips=['OK', 'Cancel'],
            button_style='primary'
        )
        ok_cancel.value = None

        def save_type_changed(change):
            ok_cancel.value = None
            # file_chooser.reset()
            file_chooser.default_path = os.getcwd()
            if change['new'] == 'HTML':
                file_chooser.default_filename = 'my_map.html'
            elif change['new'] == 'PNG':
                file_chooser.default_filename = 'my_map.png'
            elif change['new'] == 'JPG':
                file_chooser.default_filename = 'my_map.jpg'
            save_map_widget.children = [save_type, file_chooser]

        def chooser_callback(chooser):
            # file_chooser.default_path = os.getcwd()
            save_map_widget.children = [save_type, file_chooser, ok_cancel]

        def ok_cancel_clicked(change):
            if change['new'] == 'OK':
                file_path = file_chooser.selected
                ext = os.path.splitext(file_path)[1]
                if save_type.value == 'HTML' and ext.upper() == '.HTML':
                    tool_output.clear_output()
                    self.to_html(file_path)
                elif save_type.value == 'PNG' and ext.upper() == '.PNG':
                    tool_output.clear_output()
                    self.toolbar_button.value = False
                    time.sleep(1)
                    screen_capture(outfile=file_path)
                elif save_type.value == 'JPG' and ext.upper() == '.JPG':
                    tool_output.clear_output()
                    self.toolbar_button.value = False
                    time.sleep(1)
                    screen_capture(outfile=file_path)
                else:
                    label = widgets.Label(
                        value="The selected file extension does not match the selected exporting type.")
                    save_map_widget.children = [save_type, file_chooser, label]
                self.toolbar_reset()
            elif change['new'] == 'Cancel':
                tool_output.clear_output()
                self.toolbar_reset()
        save_type.observe(save_type_changed, names='value')
        ok_cancel.observe(ok_cancel_clicked, names='value')

        file_chooser.register_callback(chooser_callback)

        save_map_widget.children = [save_type, file_chooser]

        tools = {
            'mouse-pointer': 'pointer',
            'camera': 'to_image',
            'info': 'identify',
            'map-marker': 'plotting'
        }
        icons = ['mouse-pointer', 'camera', 'info', 'map-marker']
        tooltips = ['Default pointer',
                    'Save map as HTML or image', 'Inspector', 'Plotting']
        icon_width = '42px'
        icon_height = '40px'
        n_cols = 2
        n_rows = math.ceil(len(icons) / n_cols)

        toolbar_grid = widgets.GridBox(children=[widgets.ToggleButton(layout=widgets.Layout(width='auto', height='auto'),
                                                                      button_style='primary', icon=icons[i], tooltip=tooltips[i]) for i in range(len(icons))],
                                       layout=widgets.Layout(
            width='90px',
            grid_template_columns=(icon_width + ' ') * 2,
            grid_template_rows=(icon_height + ' ') * n_rows,
            grid_gap='1px 1px')
        )
        self.toolbar = toolbar_grid

        def tool_callback(change):
            if change['new']:
                current_tool = change['owner']
                for tool in toolbar_grid.children:
                    if not tool is current_tool:
                        tool.value = False
                tool = change['owner']
                if tools[tool.icon] == 'to_image':
                    with tool_output:
                        tool_output.clear_output()
                        display(save_map_widget)
            else:
                tool_output.clear_output()
                save_map_widget.children = [save_type, file_chooser]

        for tool in toolbar_grid.children:
            tool.observe(tool_callback, 'value')

        toolbar_button = widgets.ToggleButton(
            value=False,
            tooltip='Toolbar',
            icon='wrench'
        )
        toolbar_button.layout.width = '37px'
        self.toolbar_button = toolbar_button

        def toolbar_btn_click(change):
            if change['new']:
                toolbar_widget.children = [toolbar_button, toolbar_grid]
            else:
                toolbar_widget.children = [toolbar_button]
                tool_output.clear_output()
                self.toolbar_reset()

        toolbar_button.observe(toolbar_btn_click, 'value')

        toolbar_widget = widgets.VBox()
        toolbar_widget.children = [toolbar_button]
        toolbar_control = WidgetControl(
            widget=toolbar_widget, position='topright')
        self.add_control(toolbar_control)

        tool_output_control = WidgetControl(
            widget=tool_output, position='topright')
        self.add_control(tool_output_control)

        def handle_interaction(**kwargs):
            latlon = kwargs.get('coordinates')
            if kwargs.get('type') == 'click' and self.inspector_checked:
                self.default_style = {'cursor': 'wait'}

                sample_scale = self.getScale()
                layers = self.ee_layers

                with output:

                    output.clear_output(wait=True)
                    for index, ee_object in enumerate(layers):
                        xy = ee.Geometry.Point(latlon[::-1])
                        layer_names = self.ee_layer_names
                        layer_name = layer_names[index]
                        object_type = ee_object.__class__.__name__

                        try:
                            if isinstance(ee_object, ee.ImageCollection):
                                ee_object = ee_object.mosaic()
                            elif isinstance(ee_object, ee.geometry.Geometry) or isinstance(ee_object, ee.feature.Feature) \
                                    or isinstance(ee_object, ee.featurecollection.FeatureCollection):
                                ee_object = ee.FeatureCollection(ee_object)

                            if isinstance(ee_object, ee.Image):
                                item = ee_object.reduceRegion(
                                    ee.Reducer.first(), xy, sample_scale).getInfo()
                                b_name = 'band'
                                if len(item) > 1:
                                    b_name = 'bands'
                                print("{}: {} ({} {})".format(
                                    layer_name, object_type, len(item), b_name))
                                keys = item.keys()
                                for key in keys:
                                    print("  {}: {}".format(key, item[key]))
                            elif isinstance(ee_object, ee.FeatureCollection):
                                filtered = ee_object.filterBounds(xy)
                                size = filtered.size().getInfo()
                                if size > 0:
                                    first = filtered.first()
                                    props = first.toDictionary().getInfo()
                                    b_name = 'property'
                                    if len(props) > 1:
                                        b_name = 'properties'
                                    print("{}: Feature ({} {})".format(
                                        layer_name, len(props), b_name))
                                    keys = props.keys()
                                    for key in keys:
                                        print("  {}: {}".format(
                                            key, props[key]))
                        except Exception as e:
                            print(e)

                self.default_style = {'cursor': 'crosshair'}
            if kwargs.get('type') == 'click' and self.plot_checked and len(self.ee_raster_layers) > 0:
                plot_layer_name = self.plot_dropdown_widget.value
                layer_names = self.ee_raster_layer_names
                layers = self.ee_raster_layers
                index = layer_names.index(plot_layer_name)
                ee_object = layers[index]

                if isinstance(ee_object, ee.ImageCollection):
                    ee_object = ee_object.mosaic()

                try:
                    self.default_style = {'cursor': 'wait'}
                    plot_options = self.plot_options
                    sample_scale = self.getScale()
                    if'sample_scale' in plot_options.keys() and (plot_options['sample_scale'] is not None):
                        sample_scale = plot_options['sample_scale']
                    if 'title' not in plot_options.keys():
                        plot_options['title'] = plot_layer_name
                    if ('add_marker_cluster' in plot_options.keys()) and plot_options['add_marker_cluster']:
                        plot_coordinates = self.plot_coordinates
                        markers = self.plot_markers
                        marker_cluster = self.plot_marker_cluster
                        plot_coordinates.append(latlon)
                        self.plot_last_click = latlon
                        self.plot_all_clicks = plot_coordinates
                        markers.append(Marker(location=latlon))
                        marker_cluster.markers = markers
                        self.plot_marker_cluster = marker_cluster

                    band_names = ee_object.bandNames().getInfo()
                    self.chart_labels = band_names

                    if self.roi_end:
                        if self.roi_reducer_scale is None:
                            scale = ee_object.select(
                                0).projection().nominalScale()
                        else:
                            scale = self.roi_reducer_scale
                        dict_values = ee_object.reduceRegion(
                            reducer=self.roi_reducer, geometry=self.user_roi, scale=scale, bestEffort=True).getInfo()
                        self.chart_points.append(
                            self.user_roi.centroid(1).coordinates().getInfo())
                    else:
                        xy = ee.Geometry.Point(latlon[::-1])
                        dict_values = ee_object.sample(
                            xy, scale=sample_scale).first().toDictionary().getInfo()
                        self.chart_points.append(xy.coordinates().getInfo())
                    band_values = list(dict_values.values())
                    self.chart_values.append(band_values)
                    self.plot(band_names, band_values, **plot_options)
                    if plot_options['title'] == plot_layer_name:
                        del plot_options['title']
                    self.default_style = {'cursor': 'crosshair'}
                    self.roi_end = False
                except Exception as e:
                    if self.plot_widget is not None:
                        with self.plot_widget:
                            self.plot_widget.clear_output()
                            print("No data for the clicked location.")
                    else:
                        print(e)
                    self.default_style = {'cursor': 'crosshair'}
                    self.roi_end = False
        self.on_interaction(handle_interaction)

    def set_options(self, mapTypeId='HYBRID', styles=None, types=None):
        """Adds Google basemap and controls to the ipyleaflet map.

        Args:
            mapTypeId (str, optional): A mapTypeId to set the basemap to. Can be one of "ROADMAP", "SATELLITE", "HYBRID" or "TERRAIN" to select one of the standard Google Maps API map types. Defaults to 'HYBRID'.
            styles (object, optional): A dictionary of custom MapTypeStyle objects keyed with a name that will appear in the map's Map Type Controls. Defaults to None.
            types (list, optional): A list of mapTypeIds to make available. If omitted, but opt_styles is specified, appends all of the style keys to the standard Google Maps API map types.. Defaults to None.
        """
        self.clear_layers()
        self.clear_controls()
        self.scroll_wheel_zoom = True
        self.add_control(ZoomControl(position='topleft'))
        self.add_control(LayersControl(position='topright'))
        self.add_control(ScaleControl(position='bottomleft'))
        self.add_control(FullScreenControl())
        self.add_control(DrawControl())

        measure = MeasureControl(
            position='bottomleft',
            active_color='orange',
            primary_length_unit='kilometers'
        )
        self.add_control(measure)

        try:
            self.add_layer(ee_basemaps[mapTypeId])
        except Exception as e:
            print(e)
            print(
                'Google basemaps can only be one of "ROADMAP", "SATELLITE", "HYBRID" or "TERRAIN".')

    setOptions = set_options

    def add_ee_layer(self, ee_object, vis_params={}, name=None, shown=True, opacity=1.0):
        """Adds a given EE object to the map as a layer.

        Args:
            ee_object (Collection|Feature|Image|MapId): The object to add to the map.
            vis_params (dict, optional): The visualization parameters. Defaults to {}.
            name (str, optional): The name of the layer. Defaults to 'Layer N'.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            opacity (float, optional): The layer's opacity represented as a number between 0 and 1. Defaults to 1.
        """
        image = None
        if name is None:
            layer_count = len(self.layers)
            name = 'Layer ' + str(layer_count + 1)

        if not isinstance(ee_object, ee.Image) and not isinstance(ee_object, ee.ImageCollection) and not isinstance(ee_object, ee.FeatureCollection) and not isinstance(ee_object, ee.Feature) and not isinstance(ee_object, ee.Geometry):
            err_str = "\n\nThe image argument in 'addLayer' function must be an instace of one of ee.Image, ee.Geometry, ee.Feature or ee.FeatureCollection."
            raise AttributeError(err_str)

        if isinstance(ee_object, ee.geometry.Geometry) or isinstance(ee_object, ee.feature.Feature) or isinstance(ee_object, ee.featurecollection.FeatureCollection):
            features = ee.FeatureCollection(ee_object)

            width = 2

            if 'width' in vis_params:
                width = vis_params['width']

            color = '000000'

            if 'color' in vis_params:
                color = vis_params['color']

            image_fill = features.style(
                **{'fillColor': color}).updateMask(ee.Image.constant(0.5))
            image_outline = features.style(
                **{'color': color, 'fillColor': '00000000', 'width': width})

            image = image_fill.blend(image_outline)
        elif isinstance(ee_object, ee.image.Image):
            image = ee_object
        elif isinstance(ee_object, ee.imagecollection.ImageCollection):
            image = ee_object.mosaic()

        map_id_dict = ee.Image(image).getMapId(vis_params)
        tile_layer = ipyleaflet.TileLayer(
            url=map_id_dict['tile_fetcher'].url_format,
            attribution='Google Earth Engine',
            name=name,
            opacity=opacity,
            visible=True
            # visible=shown
        )

        layer = self.find_layer(name=name)
        if layer is not None:

            existing_object = self.ee_layer_dict[name]['ee_object']

            if isinstance(existing_object, ee.Image) or isinstance(existing_object, ee.ImageCollection):
                self.ee_raster_layers.remove(existing_object)
                self.ee_raster_layer_names.remove(name)
                if self.plot_dropdown_widget is not None:
                    self.plot_dropdown_widget.options = list(
                        self.ee_raster_layer_names)

            self.ee_layers.remove(existing_object)
            self.ee_layer_names.remove(name)
            self.remove_layer(layer)

        self.ee_layers.append(ee_object)
        self.ee_layer_names.append(name)
        self.ee_layer_dict[name] = {
            'ee_object': ee_object, 'ee_layer': tile_layer}

        self.add_layer(tile_layer)

        if isinstance(ee_object, ee.Image) or isinstance(ee_object, ee.ImageCollection):
            self.ee_raster_layers.append(ee_object)
            self.ee_raster_layer_names.append(name)
            if self.plot_dropdown_widget is not None:
                self.plot_dropdown_widget.options = list(
                    self.ee_raster_layer_names)

    addLayer = add_ee_layer

    def set_center(self, lon, lat, zoom=None):
        """Centers the map view at a given coordinates with the given zoom level.

        Args:
            lon (float): The longitude of the center, in degrees.
            lat (float): The latitude of the center, in degrees.
            zoom (int, optional): The zoom level, from 1 to 24. Defaults to None.
        """
        self.center = (lat, lon)
        if zoom is not None:
            self.zoom = zoom

    setCenter = set_center

    def center_object(self, ee_object, zoom=None):
        """Centers the map view on a given object.

        Args:
            ee_object (Element|Geometry): An Earth Engine object to center on - a geometry, image or feature.
            zoom (int, optional): The zoom level, from 1 to 24. Defaults to None.
        """
        lat = 0
        lon = 0
        bounds = [[lat, lon], [lat, lon]]
        if isinstance(ee_object, ee.geometry.Geometry):
            centroid = ee_object.centroid(1)
            lon, lat = centroid.getInfo()['coordinates']
            bounds = [[lat, lon], [lat, lon]]
        elif isinstance(ee_object, ee.feature.Feature):
            centroid = ee_object.geometry().centroid(1)
            lon, lat = centroid.getInfo()['coordinates']
            bounds = [[lat, lon], [lat, lon]]
        elif isinstance(ee_object, ee.featurecollection.FeatureCollection):
            centroid = ee_object.geometry().centroid()
            lon, lat = centroid.getInfo()['coordinates']
            bounds = [[lat, lon], [lat, lon]]
        elif isinstance(ee_object, ee.image.Image):
            geometry = ee_object.geometry()
            coordinates = geometry.getInfo()['coordinates'][0]
            bounds = [coordinates[0][::-1], coordinates[2][::-1]]
        elif isinstance(ee_object, ee.imagecollection.ImageCollection):
            geometry = ee_object.geometry()
            coordinates = geometry.getInfo()['coordinates'][0]
            bounds = [coordinates[0][::-1], coordinates[2][::-1]]
        else:
            bounds = [[0, 0], [0, 0]]

        lat = bounds[0][0]
        lon = bounds[0][1]

        self.setCenter(lon, lat, zoom)

    centerObject = center_object

    def get_scale(self):
        """Returns the approximate pixel scale of the current map view, in meters.

        Returns:
            float: Map resolution in meters.
        """
        zoom_level = self.zoom
        # Reference: https://blogs.bing.com/maps/2006/02/25/map-control-zoom-levels-gt-resolution
        resolution = 156543.04 * math.cos(0) / math.pow(2, zoom_level)
        return resolution

    getScale = get_scale

    def add_basemap(self, basemap='HYBRID'):
        """Adds a basemap to the map.

        Args:
            basemap (str, optional): Can be one of string from ee_basemaps. Defaults to 'HYBRID'.
        """
        try:
            self.add_layer(ee_basemaps[basemap])
        except Exception as e:
            print(e)
            print('Basemap can only be one of the following:\n  {}'.format(
                '\n  '.join(ee_basemaps.keys())))

    def find_layer(self, name):
        """Finds layer by name

        Args:
            name (str): Name of the layer to find.

        Returns:
            object: ipyleaflet layer object.
        """
        layers = self.layers

        for layer in layers:
            if layer.name == name:
                return layer

        return None

    def layer_opacity(self, name, value=1.0):
        """Changes layer opacity.

        Args:
            name (str): The name of the layer to change opacity.
            value (float, optional): The opacity value to set. Defaults to 1.0.
        """
        layer = self.find_layer(name)
        try:
            layer.opacity = value
            # layer.interact(opacity=(0, 1, 0.1))  # to change layer opacity interactively
        except Exception as e:
            print(e)

    def add_wms_layer(self, url, layers, name=None, attribution='', format='image/jpeg', transparent=False, opacity=1.0, shown=True):
        """Add a WMS layer to the map.

        Args:
            url (str): The URL of the WMS web service.
            layers (str): Comma-separated list of WMS layers to show. 
            name (str, optional): The layer name to use on the layer control. Defaults to None.
            attribution (str, optional): The attribution of the data layer. Defaults to ''.
            format (str, optional): WMS image format (use ‘image/png’ for layers with transparency). Defaults to 'image/jpeg'.
            transparent (bool, optional): If True, the WMS service will return images with transparency. Defaults to False.
            opacity (float, optional): The opacity of the layer. Defaults to 1.0.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
        """

        if name is None:
            name = str(layers)

        try:
            wms_layer = ipyleaflet.WMSLayer(
                url=url,
                layers=layers,
                name=name,
                attribution=attribution,
                format=format,
                transparent=transparent,
                opacity=opacity,
                visible=True
                # visible=shown
            )
            self.add_layer(wms_layer)
        except Exception as e:
            print(e)
            print("Failed to add the specified WMS TileLayer.")

    def add_tile_layer(self, url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', name=None, attribution='', opacity=1.0, shown=True):
        """Adds a TileLayer to the map.

        Args:
            url (str, optional): The URL of the tile layer. Defaults to 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'.
            name (str, optional): The layer name to use for the layer. Defaults to None.
            attribution (str, optional): The attribution to use. Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
        """
        try:
            tile_layer = ipyleaflet.TileLayer(
                url=url,
                name=name,
                attribution=attribution,
                opacity=opacity,
                visible=True
                # visible=shown
            )
            self.add_layer(tile_layer)
        except Exception as e:
            print(e)
            print("Failed to add the specified TileLayer.")

    def add_minimap(self, zoom=5, position="bottomright"):
        """Adds a minimap (overview) to the ipyleaflet map.

        Args:
            zoom (int, optional): Initial map zoom level. Defaults to 5.
            position (str, optional): Position of the minimap. Defaults to "bottomright".
        """
        minimap = ipyleaflet.Map(
            zoom_control=False, attribution_control=False,
            zoom=5, center=self.center, layers=[ee_basemaps['ROADMAP']]
        )
        minimap.layout.width = '150px'
        minimap.layout.height = '150px'
        link((minimap, 'center'), (self, 'center'))
        minimap_control = WidgetControl(widget=minimap, position=position)
        self.add_control(minimap_control)

    def marker_cluster(self):
        """Adds a marker cluster to the map and returns a list of ee.Feature, which can be accessed using Map.ee_marker_cluster.

        Returns:
            object: a list of ee.Feature
        """
        coordinates = []
        markers = []
        marker_cluster = MarkerCluster(name="Marker Cluster")
        self.last_click = []
        self.all_clicks = []
        self.ee_markers = []
        self.add_layer(marker_cluster)

        def handle_interaction(**kwargs):
            latlon = kwargs.get('coordinates')
            if kwargs.get('type') == 'click':
                coordinates.append(latlon)
                geom = ee.Geometry.Point(latlon[1], latlon[0])
                feature = ee.Feature(geom)
                self.ee_markers.append(feature)
                self.last_click = latlon
                self.all_clicks = coordinates
                markers.append(Marker(location=latlon))
                marker_cluster.markers = markers
            elif kwargs.get('type') == 'mousemove':
                pass
        # cursor style: https://www.w3schools.com/cssref/pr_class_cursor.asp
        self.default_style = {'cursor': 'crosshair'}
        self.on_interaction(handle_interaction)

    def set_plot_options(self, add_marker_cluster=False, sample_scale=None, plot_type=None, overlay=False, position='bottomright', min_width=None, max_width=None, min_height=None, max_height=None, **kwargs):
        """Sets plotting options.

        Args:
            add_marker_cluster (bool, optional): Whether to add a marker cluster. Defaults to False.
            sample_scale (float, optional):  A nominal scale in meters of the projection to sample in . Defaults to None.
            plot_type (str, optional): The plot type can be one of "None", "bar", "scatter" or "hist". Defaults to None.
            overlay (bool, optional): Whether to overlay plotted lines on the figure. Defaults to False.
            position (str, optional): Position of the control, can be ‘bottomleft’, ‘bottomright’, ‘topleft’, or ‘topright’. Defaults to 'bottomright'.
            min_width (int, optional): Min width of the widget (in pixels), if None it will respect the content size. Defaults to None.
            max_width (int, optional): Max width of the widget (in pixels), if None it will respect the content size. Defaults to None.
            min_height (int, optional): Min height of the widget (in pixels), if None it will respect the content size. Defaults to None.
            max_height (int, optional): Max height of the widget (in pixels), if None it will respect the content size. Defaults to None.

        """
        plot_options_dict = {}
        plot_options_dict['add_marker_cluster'] = add_marker_cluster
        plot_options_dict['sample_scale'] = sample_scale
        plot_options_dict['plot_type'] = plot_type
        plot_options_dict['overlay'] = overlay
        plot_options_dict['position'] = position
        plot_options_dict['min_width'] = min_width
        plot_options_dict['max_width'] = max_width
        plot_options_dict['min_height'] = min_height
        plot_options_dict['max_height'] = max_height

        for key in kwargs.keys():
            plot_options_dict[key] = kwargs[key]

        self.plot_options = plot_options_dict

        if add_marker_cluster and (self.plot_marker_cluster not in self.layers):
            self.add_layer(self.plot_marker_cluster)

    def plot(self, x, y, plot_type=None, overlay=False, position='bottomright', min_width=None, max_width=None, min_height=None, max_height=None, **kwargs):
        """Creates a plot based on x-array and y-array data.

        Args:
            x (numpy.ndarray or list): The x-coordinates of the plotted line.
            y (numpy.ndarray or list): The y-coordinates of the plotted line.
            plot_type (str, optional): The plot type can be one of "None", "bar", "scatter" or "hist". Defaults to None.
            overlay (bool, optional): Whether to overlay plotted lines on the figure. Defaults to False.
            position (str, optional): Position of the control, can be ‘bottomleft’, ‘bottomright’, ‘topleft’, or ‘topright’. Defaults to 'bottomright'.
            min_width (int, optional): Min width of the widget (in pixels), if None it will respect the content size. Defaults to None.
            max_width (int, optional): Max width of the widget (in pixels), if None it will respect the content size. Defaults to None.
            min_height (int, optional): Min height of the widget (in pixels), if None it will respect the content size. Defaults to None.
            max_height (int, optional): Max height of the widget (in pixels), if None it will respect the content size. Defaults to None.            

        """
        if self.plot_widget is not None:
            plot_widget = self.plot_widget
        else:
            plot_widget = widgets.Output(layout={'border': '1px solid black'})
            plot_control = WidgetControl(widget=plot_widget, position=position, min_width=min_width,
                                         max_width=max_width, min_height=min_height, max_height=max_height)
            self.plot_widget = plot_widget
            self.plot_control = plot_control
            self.add_control(plot_control)

        if max_width is None:
            max_width = 500
        if max_height is None:
            max_height = 300

        if (plot_type is None) and ('markers' not in kwargs.keys()):
            kwargs['markers'] = 'circle'

        with plot_widget:
            try:
                fig = plt.figure(1, **kwargs)
                if max_width is not None:
                    fig.layout.width = str(max_width) + 'px'
                if max_height is not None:
                    fig.layout.height = str(max_height) + 'px'

                plot_widget.clear_output(wait=True)
                if not overlay:
                    plt.clear()

                if plot_type is None:
                    if 'marker' not in kwargs.keys():
                        kwargs['marker'] = 'circle'
                    plt.plot(x, y, **kwargs)
                elif plot_type == 'bar':
                    plt.bar(x, y, **kwargs)
                elif plot_type == 'scatter':
                    plt.scatter(x, y, **kwargs)
                elif plot_type == 'hist':
                    plt.hist(y, **kwargs)
                plt.show()

            except Exception as e:
                print(e)
                print("Failed to create plot.")

    def plot_demo(self, iterations=20, plot_type=None, overlay=False, position='bottomright', min_width=None, max_width=None, min_height=None, max_height=None, **kwargs):
        """A demo of interactive plotting using random pixel coordinates.

        Args:
            iterations (int, optional): How many iterations to run for the demo. Defaults to 20.
            plot_type (str, optional): The plot type can be one of "None", "bar", "scatter" or "hist". Defaults to None.
            overlay (bool, optional): Whether to overlay plotted lines on the figure. Defaults to False.
            position (str, optional): Position of the control, can be ‘bottomleft’, ‘bottomright’, ‘topleft’, or ‘topright’. Defaults to 'bottomright'.
            min_width (int, optional): Min width of the widget (in pixels), if None it will respect the content size. Defaults to None.
            max_width (int, optional): Max width of the widget (in pixels), if None it will respect the content size. Defaults to None.
            min_height (int, optional): Min height of the widget (in pixels), if None it will respect the content size. Defaults to None.
            max_height (int, optional): Max height of the widget (in pixels), if None it will respect the content size. Defaults to None.    
        """

        import numpy as np
        import time

        if self.random_marker is not None:
            self.remove_layer(self.random_marker)

        image = ee.Image('LE7_TOA_5YEAR/1999_2003').select([0, 1, 2, 3, 4, 6])
        self.addLayer(
            image, {'bands': ['B4', 'B3', 'B2'], 'gamma': 1.4}, "LE7_TOA_5YEAR/1999_2003")
        self.setCenter(-50.078877, 25.190030, 3)
        band_names = image.bandNames().getInfo()
        band_count = len(band_names)

        latitudes = np.random.uniform(30, 48, size=iterations)
        longitudes = np.random.uniform(-121, -76, size=iterations)

        marker = Marker(location=(0, 0))
        self.random_marker = marker
        self.add_layer(marker)

        for i in range(iterations):
            try:
                coordinate = ee.Geometry.Point([longitudes[i], latitudes[i]])
                dict_values = image.sample(
                    coordinate).first().toDictionary().getInfo()
                band_values = list(dict_values.values())
                title = '{}/{}: Spectral signature at ({}, {})'.format(i+1, iterations,
                                                                       round(latitudes[i], 2), round(longitudes[i], 2))
                marker.location = (latitudes[i], longitudes[i])
                self.plot(band_names, band_values, plot_type=plot_type, overlay=overlay,
                          min_width=min_width, max_width=max_width, min_height=min_height, max_height=max_height, title=title, **kwargs)
                time.sleep(0.3)
            except Exception as e:
                print(e)

    def plot_raster(self, ee_object=None, sample_scale=None, plot_type=None, overlay=False, position='bottomright', min_width=None, max_width=None, min_height=None, max_height=None, **kwargs):
        """Interactive plotting of Earth Engine data by clicking on the map.

        Args:
            ee_object (object, optional): The ee.Image or ee.ImageCollection to sample. Defaults to None.
            sample_scale (float, optional): A nominal scale in meters of the projection to sample in. Defaults to None.
            plot_type (str, optional): The plot type can be one of "None", "bar", "scatter" or "hist". Defaults to None.
            overlay (bool, optional): Whether to overlay plotted lines on the figure. Defaults to False.
            position (str, optional): Position of the control, can be ‘bottomleft’, ‘bottomright’, ‘topleft’, or ‘topright’. Defaults to 'bottomright'.
            min_width (int, optional): Min width of the widget (in pixels), if None it will respect the content size. Defaults to None.
            max_width (int, optional): Max width of the widget (in pixels), if None it will respect the content size. Defaults to None.
            min_height (int, optional): Min height of the widget (in pixels), if None it will respect the content size. Defaults to None.
            max_height (int, optional): Max height of the widget (in pixels), if None it will respect the content size. Defaults to None.    

        """
        if self.plot_control is not None:
            del self.plot_widget
            self.remove_control(self.plot_control)

        if self.random_marker is not None:
            self.remove_layer(self.random_marker)

        plot_widget = widgets.Output(layout={'border': '1px solid black'})
        plot_control = WidgetControl(widget=plot_widget, position=position, min_width=min_width,
                                     max_width=max_width, min_height=min_height, max_height=max_height)
        self.plot_widget = plot_widget
        self.plot_control = plot_control
        self.add_control(plot_control)

        self.default_style = {'cursor': 'crosshair'}
        msg = "The plot function can only be used on ee.Image or ee.ImageCollection with more than one band."
        if (ee_object is None) and len(self.ee_raster_layers) > 0:
            ee_object = self.ee_raster_layers[-1]
            if isinstance(ee_object, ee.ImageCollection):
                ee_object = ee_object.mosaic()
        elif isinstance(ee_object, ee.ImageCollection):
            ee_object = ee_object.mosaic()
        elif not isinstance(ee_object, ee.Image):
            print(msg)
            return

        if sample_scale is None:
            sample_scale = self.getScale()

        if max_width is None:
            max_width = 500

        band_names = ee_object.bandNames().getInfo()

        coordinates = []
        markers = []
        marker_cluster = MarkerCluster(name="Marker Cluster")
        self.last_click = []
        self.all_clicks = []
        self.add_layer(marker_cluster)

        def handle_interaction(**kwargs2):
            latlon = kwargs2.get('coordinates')

            if kwargs2.get('type') == 'click':
                try:
                    coordinates.append(latlon)
                    self.last_click = latlon
                    self.all_clicks = coordinates
                    markers.append(Marker(location=latlon))
                    marker_cluster.markers = markers
                    self.default_style = {'cursor': 'wait'}
                    xy = ee.Geometry.Point(latlon[::-1])
                    dict_values = ee_object.sample(
                        xy, scale=sample_scale).first().toDictionary().getInfo()
                    band_values = list(dict_values.values())
                    self.plot(band_names, band_values, plot_type=plot_type, overlay=overlay,
                              min_width=min_width, max_width=max_width, min_height=min_height, max_height=max_height, **kwargs)
                    self.default_style = {'cursor': 'crosshair'}
                except Exception as e:
                    if self.plot_widget is not None:
                        with self.plot_widget:
                            self.plot_widget.clear_output()
                            print("No data for the clicked location.")
                    else:
                        print(e)
                    self.default_style = {'cursor': 'crosshair'}

        self.on_interaction(handle_interaction)

    def add_maker_cluster(self, event='click', add_marker=True):
        """Captures user inputs and add markers to the map.

        Args:
            event (str, optional): [description]. Defaults to 'click'.
            add_marker (bool, optional): If True, add markers to the map. Defaults to True.

        Returns:
            object: a marker cluster.
        """
        coordinates = []
        markers = []
        marker_cluster = MarkerCluster(name="Marker Cluster")
        self.last_click = []
        self.all_clicks = []
        if add_marker:
            self.add_layer(marker_cluster)

        def handle_interaction(**kwargs):
            latlon = kwargs.get('coordinates')

            if event == 'click' and kwargs.get('type') == 'click':
                coordinates.append(latlon)
                self.last_click = latlon
                self.all_clicks = coordinates
                if add_marker:
                    markers.append(Marker(location=latlon))
                    marker_cluster.markers = markers
            elif kwargs.get('type') == 'mousemove':
                pass
        # cursor style: https://www.w3schools.com/cssref/pr_class_cursor.asp
        self.default_style = {'cursor': 'crosshair'}
        self.on_interaction(handle_interaction)

    def set_control_visibility(self, layerControl=True, fullscreenControl=True, latLngPopup=True):
        """Sets the visibility of the controls on the map.

        Args:
            layerControl (bool, optional): Whether to show the control that allows the user to toggle layers on/off. Defaults to True.
            fullscreenControl (bool, optional): Whether to show the control that allows the user to make the map full-screen. Defaults to True.
            latLngPopup (bool, optional): Whether to show the control that pops up the Lat/lon when the user clicks on the map. Defaults to True.
        """
        pass

    setControlVisibility = set_control_visibility

    def add_layer_control(self):
        """Adds the layer control to the map.
        """
        pass

    addLayerControl = add_layer_control

    def split_map(self, left_layer='HYBRID', right_layer='ESRI'):
        """Adds split map.

        Args:
            left_layer (str, optional): The layer tile layer. Defaults to 'HYBRID'.
            right_layer (str, optional): The right tile layer. Defaults to 'ESRI'.
        """
        try:
            self.remove_control(self.layer_control)
            self.remove_control(self.inspector_control)
            if left_layer in ee_basemaps.keys():
                left_layer = ee_basemaps[left_layer]

            if right_layer in ee_basemaps.keys():
                right_layer = ee_basemaps[right_layer]

            control = ipyleaflet.SplitMapControl(
                left_layer=left_layer, right_layer=right_layer)
            self.add_control(control)

        except Exception as e:
            print(e)
            print('The provided layers are invalid!')

    def ts_inspector(self, left_ts, right_ts, left_names, right_names, left_vis={}, right_vis={}):
        """Creates a split-panel map for inspecting timeseries images.

        Args:
            left_ts (object): An ee.ImageCollection to show on the left panel.
            right_ts (object): An ee.ImageCollection to show on the right panel.
            left_names (list): A list of names to show under the left dropdown.
            right_names (list): A list of names to show under the right dropdown.
            left_vis (dict, optional): Visualization parameters for the left layer. Defaults to {}.
            right_vis (dict, optional): Visualization parameters for the right layer. Defaults to {}.
        """
        left_count = int(left_ts.size().getInfo())
        right_count = int(right_ts.size().getInfo())

        if left_count != len(left_names):
            print(
                'The number of images in left_ts must match the number of layer names in left_names.')
            return
        if right_count != len(right_names):
            print(
                'The number of images in right_ts must match the number of layer names in right_names.')
            return

        left_layer = TileLayer(
            url='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
            attribution='Google',
            name='Google Maps'
        )
        right_layer = TileLayer(
            url='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
            attribution='Google',
            name='Google Maps'
        )

        self.clear_controls()
        left_dropdown = widgets.Dropdown(options=left_names, value=None)
        right_dropdown = widgets.Dropdown(options=right_names, value=None)
        left_dropdown.layout.max_width = '130px'
        right_dropdown.layout.max_width = '130px'

        left_control = WidgetControl(widget=left_dropdown, position='topleft')
        right_control = WidgetControl(
            widget=right_dropdown, position='topright')

        self.add_control(control=left_control)
        self.add_control(control=right_control)

        self.add_control(ZoomControl(position='topleft'))
        self.add_control(ScaleControl(position='bottomleft'))
        self.add_control(FullScreenControl())

        def left_dropdown_change(change):
            left_dropdown_index = left_dropdown.index
            if left_dropdown_index is not None and left_dropdown_index >= 0:
                try:
                    if isinstance(left_ts, ee.ImageCollection):
                        left_image = left_ts.toList(
                            left_ts.size()).get(left_dropdown_index)
                    elif isinstance(left_ts, ee.List):
                        left_image = left_ts.get(left_dropdown_index)
                    else:
                        print('The left_ts argument must be an ImageCollection.')
                        return

                    if isinstance(left_image, ee.ImageCollection):
                        left_image = ee.Image(left_image.mosaic())
                    elif isinstance(left_image, ee.Image):
                        pass
                    else:
                        left_image = ee.Image(left_image)

                    left_image = ee_tile_layer(
                        left_image, left_vis, left_names[left_dropdown_index])
                    left_layer.url = left_image.url
                except Exception as e:
                    print(e)
                    return

        left_dropdown.observe(left_dropdown_change, names='value')

        def right_dropdown_change(change):
            right_dropdown_index = right_dropdown.index
            if right_dropdown_index is not None and right_dropdown_index >= 0:
                try:
                    if isinstance(right_ts, ee.ImageCollection):
                        right_image = right_ts.toList(
                            left_ts.size()).get(right_dropdown_index)
                    elif isinstance(right_ts, ee.List):
                        right_image = right_ts.get(right_dropdown_index)
                    else:
                        print('The left_ts argument must be an ImageCollection.')
                        return

                    if isinstance(right_image, ee.ImageCollection):
                        right_image = ee.Image(right_image.mosaic())
                    elif isinstance(right_image, ee.Image):
                        pass
                    else:
                        right_image = ee.Image(right_image)

                    right_image = ee_tile_layer(
                        right_image, right_vis, right_names[right_dropdown_index])
                    right_layer.url = right_image.url
                except Exception as e:
                    print(e)
                    return

        right_dropdown.observe(right_dropdown_change, names='value')

        try:

            split_control = ipyleaflet.SplitMapControl(
                left_layer=left_layer, right_layer=right_layer)
            self.add_control(split_control)

        except Exception as e:
            print(e)

    def basemap_demo(self):
        """A demo for using geemap basemaps.

        """
        dropdown = widgets.Dropdown(
            options=list(ee_basemaps.keys()),
            value='HYBRID',
            description='Basemaps'
        )

        def on_click(change):
            basemap_name = change['new']
            old_basemap = self.layers[-1]
            self.substitute_layer(old_basemap, ee_basemaps[basemap_name])

        dropdown.observe(on_click, 'value')
        basemap_control = WidgetControl(widget=dropdown, position='topright')
        self.remove_control(self.inspector_control)
        # self.remove_control(self.layer_control)
        self.add_control(basemap_control)

    def add_legend(self, legend_title='Legend', legend_dict=None, legend_keys=None, legend_colors=None, position='bottomright', builtin_legend=None, **kwargs):
        """Adds a customized basemap to the map.

        Args:
            legend_title (str, optional): Title of the legend. Defaults to 'Legend'.
            legend_dict (dict, optional): A dictionary containing legend items as keys and color as values. If provided, legend_keys and legend_colors will be ignored. Defaults to None.
            legend_keys (list, optional): A list of legend keys. Defaults to None.
            legend_colors (list, optional): A list of legend colors. Defaults to None.
            position (str, optional): Position of the legend. Defaults to 'bottomright'.
            builtin_legend (str, optional): Name of the builtin legend to add to the map. Defaults to None.

        """
        import pkg_resources
        from IPython.display import display
        pkg_dir = os.path.dirname(
            pkg_resources.resource_filename("geemap", "geemap.py"))
        legend_template = os.path.join(pkg_dir, 'data/template/legend.html')

        # print(kwargs['min_height'])

        if 'min_width' not in kwargs.keys():
            min_width = None
        else:
            min_wdith = kwargs['min_width']
        if 'max_width' not in kwargs.keys():
            max_width = None
        else:
            max_width = kwargs['max_width']
        if 'min_height' not in kwargs.keys():
            min_height = None
        else:
            min_height = kwargs['min_height']
        if 'max_height' not in kwargs.keys():
            max_height = None
        else:
            max_height = kwargs['max_height']
        if 'height' not in kwargs.keys():
            height = None
        else:
            height = kwargs['height']
        if 'width' not in kwargs.keys():
            width = None
        else:
            width = kwargs['width']

        if width is None:
            max_width = '300px'
        if height is None:
            max_height = '400px'

        if not os.path.exists(legend_template):
            print('The legend template does not exist.')
            return

        if legend_keys is not None:
            if not isinstance(legend_keys, list):
                print('The legend keys must be a list.')
                return
        else:
            legend_keys = ['One', 'Two', 'Three', 'Four', 'ect']

        if legend_colors is not None:
            if not isinstance(legend_colors, list):
                print('The legend colors must be a list.')
                return
            elif all(isinstance(item, tuple) for item in legend_colors):
                try:
                    legend_colors = [rgb_to_hex(x) for x in legend_colors]
                except Exception as e:
                    print(e)
            elif all((item.startswith('#') and len(item) == 7) for item in legend_colors):
                pass
            elif all((len(item) == 6) for item in legend_colors):
                pass
            else:
                print('The legend colors must be a list of tuples.')
                return
        else:
            legend_colors = ['#8DD3C7', '#FFFFB3',
                             '#BEBADA', '#FB8072', '#80B1D3']

        if len(legend_keys) != len(legend_colors):
            print('The legend keys and values must be the same length.')
            return

        allowed_builtin_legends = builtin_legends.keys()
        if builtin_legend is not None:
            # builtin_legend = builtin_legend.upper()
            if builtin_legend not in allowed_builtin_legends:
                print('The builtin legend must be one of the following: {}'.format(
                    ', '.join(allowed_builtin_legends)))
                return
            else:
                legend_dict = builtin_legends[builtin_legend]
                legend_keys = list(legend_dict.keys())
                legend_colors = list(legend_dict.values())

        if legend_dict is not None:
            if not isinstance(legend_dict, dict):
                print('The legend dict must be a dictionary.')
                return
            else:
                legend_keys = list(legend_dict.keys())
                legend_colors = list(legend_dict.values())
                if all(isinstance(item, tuple) for item in legend_colors):
                    try:
                        legend_colors = [rgb_to_hex(x) for x in legend_colors]
                    except Exception as e:
                        print(e)

        allowed_positions = ['topleft', 'topright',
                             'bottomleft', 'bottomright']
        if position not in allowed_positions:
            print('The position must be one of the following: {}'.format(
                ', '.join(allowed_positions)))
            return

        header = []
        content = []
        footer = []

        with open(legend_template) as f:
            lines = f.readlines()
            lines[3] = lines[3].replace('Legend', legend_title)
            header = lines[:6]
            footer = lines[11:]

        for index, key in enumerate(legend_keys):
            color = legend_colors[index]
            if not color.startswith('#'):
                color = '#' + color
            item = "      <li><span style='background:{};'></span>{}</li>\n".format(
                color, key)
            content.append(item)

        legend_html = header + content + footer
        legend_text = ''.join(legend_html)

        try:
            if self.legend_control is not None:
                legend_widget = self.legend_widget
                legend_widget.close()
                self.remove_control(self.legend_control)

            legend_output_widget = widgets.Output(
                layout={'border': '1px solid black', 'max_width': max_width, 'min_width': min_width, 'max_height': max_height,
                        'min_height': min_height, 'height': height, 'width': width, 'overflow': 'scroll'})
            legend_control = WidgetControl(
                widget=legend_output_widget, position=position)
            legend_widget = widgets.HTML(value=legend_text)
            with legend_output_widget:
                display(legend_widget)

            self.legend_widget = legend_output_widget
            self.legend_control = legend_control
            self.add_control(legend_control)

        except Exception as e:
            print(e)

    def image_overlay(self, url, bounds, name):
        """Overlays an image from the Internet or locally on the map.

        Args:
            url (str): http URL or local file path to the image.
            bounds (tuple): bounding box of the image in the format of (lower_left(lat, lon), upper_right(lat, lon)), such as ((13, -130), (32, -100)).
            name (str): name of the layer to show on the layer control.
        """
        from base64 import b64encode
        from PIL import Image, ImageSequence
        from io import BytesIO
        try:
            if not url.startswith('http'):

                if not os.path.exists(url):
                    print('The provided file does not exist.')
                    return

                ext = os.path.splitext(url)[1][1:]  # file extension
                image = Image.open(url)

                f = BytesIO()
                if ext.lower() == 'gif':
                    frames = []
                    # Loop over each frame in the animated image
                    for frame in ImageSequence.Iterator(image):
                        frame = frame.convert('RGBA')
                        b = BytesIO()
                        frame.save(b, format="gif")
                        frame = Image.open(b)
                        frames.append(frame)
                    frames[0].save(f, format='GIF', save_all=True,
                                   append_images=frames[1:], loop=0)
                else:
                    image.save(f, ext)

                data = b64encode(f.getvalue())
                data = data.decode('ascii')
                url = 'data:image/{};base64,'.format(ext) + data
            img = ipyleaflet.ImageOverlay(url=url, bounds=bounds, name=name)
            self.add_layer(img)
        except Exception as e:
            print(e)
            
    def video_overlay(self, url, bounds, name):
        """Overlays a video from the Internet on the map.

        Args:
            url (str): http URL of the video, such as "https://www.mapbox.com/bites/00188/patricia_nasa.webm"
            bounds (tuple): bounding box of the video in the format of (lower_left(lat, lon), upper_right(lat, lon)), such as ((13, -130), (32, -100)).
            name (str): name of the layer to show on the layer control.
        """
        try:
            video = ipyleaflet.VideoOverlay(url=url, bounds=bounds, name=name)
            self.add_layer(video)
        except Exception as e:
            print(e)

    def add_landsat_ts_gif(self, layer_name='Timelapse', roi=None, label=None, start_year=1984, end_year=2019, start_date='06-10', end_date='09-20', bands=['NIR', 'Red', 'Green'], vis_params=None, dimensions=768, frames_per_second=10, font_size=30, font_color='white', add_progress_bar=True, progress_bar_color='white', progress_bar_height=5, out_gif=None, download=False, apply_fmask=True, nd_bands=None, nd_threshold=0, nd_palette=['black', 'blue']):
        """Adds a Landsat timelapse to the map.

        Args:
            layer_name (str, optional): Layer name to show under the layer control. Defaults to 'Timelapse'.
            roi (object, optional): Region of interest to create the timelapse. Defaults to None.
            label (str, optional): A label to shown on the GIF, such as place name. Defaults to None.
            start_year (int, optional): Starting year for the timelapse. Defaults to 1984.
            end_year (int, optional): Ending year for the timelapse. Defaults to 2019.
            start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '06-10'.
            end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '09-20'.
            bands (list, optional): Three bands selected from ['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2', 'pixel_qa']. Defaults to ['NIR', 'Red', 'Green'].
            vis_params (dict, optional): Visualization parameters. Defaults to None.
            dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
            frames_per_second (int, optional): Animation speed. Defaults to 10.
            font_size (int, optional): Font size of the animated text and label. Defaults to 30.
            font_color (str, optional): Font color of the animated text and label. Defaults to 'black'.
            add_progress_bar (bool, optional): Whether to add a progress bar at the bottom of the GIF. Defaults to True.
            progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
            progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.
            out_gif (str, optional): File path to the output animated GIF. Defaults to None.
            download (bool, optional): Whether to download the gif. Defaults to False.
            apply_fmask (bool, optional): Whether to apply Fmask (Function of mask) for automated clouds, cloud shadows, snow, and water masking.
            nd_bands (list, optional): A list of names specifying the bands to use, e.g., ['Green', 'SWIR1']. The normalized difference is computed as (first − second) / (first + second). Note that negative input values are forced to 0 so that the result is confined to the range (-1, 1).  
            nd_threshold (float, optional): The threshold for extacting pixels from the normalized difference band. 
            nd_palette (str, optional): The color palette to use for displaying the normalized difference band. 

        """
        try:

            if roi is None:
                if self.draw_last_feature is not None:
                    feature = self.draw_last_feature
                    roi = feature.geometry()
                else:
                    roi = ee.Geometry.Polygon(
                        [[[-115.471773, 35.892718],
                          [-115.471773, 36.409454],
                            [-114.271283, 36.409454],
                            [-114.271283, 35.892718],
                            [-115.471773, 35.892718]]], None, False)
            elif isinstance(roi, ee.Feature) or isinstance(roi, ee.FeatureCollection):
                roi = roi.geometry()
            elif isinstance(roi, ee.Geometry):
                pass
            else:
                print('The provided roi is invalid. It must be an ee.Geometry')
                return

            geojson = ee_to_geojson(roi)
            bounds = minimum_bounding_box(geojson)
            geojson = adjust_longitude(geojson)
            roi = ee.Geometry(geojson)

            in_gif = landsat_ts_gif(roi=roi, out_gif=out_gif, start_year=start_year, end_year=end_year, start_date=start_date,
                                    end_date=end_date, bands=bands, vis_params=vis_params, dimensions=dimensions, frames_per_second=frames_per_second, apply_fmask=apply_fmask, nd_bands=nd_bands, nd_threshold=nd_threshold, nd_palette=nd_palette)
            in_nd_gif = in_gif.replace('.gif', '_nd.gif')

            print('Adding animated text to GIF ...')
            add_text_to_gif(in_gif, in_gif, xy=('2%', '2%'), text_sequence=start_year,
                            font_size=font_size, font_color=font_color, duration=int(1000 / frames_per_second), add_progress_bar=add_progress_bar, progress_bar_color=progress_bar_color, progress_bar_height=progress_bar_height)
            if nd_bands is not None:
                add_text_to_gif(in_nd_gif, in_nd_gif, xy=('2%', '2%'), text_sequence=start_year,
                                font_size=font_size, font_color=font_color, duration=int(1000 / frames_per_second), add_progress_bar=add_progress_bar, progress_bar_color=progress_bar_color, progress_bar_height=progress_bar_height)

            if label is not None:
                add_text_to_gif(in_gif, in_gif, xy=('2%', '90%'), text_sequence=label,
                                font_size=font_size, font_color=font_color, duration=int(1000 / frames_per_second), add_progress_bar=add_progress_bar, progress_bar_color=progress_bar_color, progress_bar_height=progress_bar_height)
                # if nd_bands is not None:
                #     add_text_to_gif(in_nd_gif, in_nd_gif, xy=('2%', '90%'), text_sequence=label,
                #                     font_size=font_size, font_color=font_color, duration=int(1000 / frames_per_second), add_progress_bar=add_progress_bar, progress_bar_color=progress_bar_color, progress_bar_height=progress_bar_height)

            if is_tool('ffmpeg'):
                reduce_gif_size(in_gif)
                if nd_bands is not None:
                    reduce_gif_size(in_nd_gif)

            print('Adding GIF to the map ...')
            self.image_overlay(url=in_gif, bounds=bounds, name=layer_name)
            if nd_bands is not None:
                self.image_overlay(
                    url=in_nd_gif, bounds=bounds, name=layer_name+' ND')
            print('The timelapse has been added to the map.')

            if download:
                link = create_download_link(
                    in_gif, title="Click here to download the timelapse: ")
                display(link)

        except Exception as e:
            print(e)

    def to_html(self, outfile, title='My Map', width='100%', height='880px'):
        """Saves the map as a HTML file.

        Args:
            outfile (str): The output file path to the HTML file.
            title (str, optional): The title of the HTML file. Defaults to 'My Map'.
            width (str, optional): The width of the map in pixels or percentage. Defaults to '100%'.
            height (str, optional): The height of the map in pixels. Defaults to '880px'.
        """
        try:

            if not outfile.endswith('.html'):
                print('The output file must end with .html')
                return

            out_dir = os.path.dirname(outfile)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)

            before_width = self.layout.width
            before_height = self.layout.height

            if not isinstance(width, str):
                print("width must be a string.")
                return
            elif width.endswith('px') or width.endswith('%'):
                pass
            else:
                print('width must end with px or %')
                return

            if not isinstance(height, str):
                print("height must be a string.")
                return
            elif not height.endswith('px'):
                print('height must end with px')
                return

            self.layout.width = width
            self.layout.height = height

            self.save(outfile, title=title)

            self.layout.width = before_width
            self.layout.height = before_height

        except Exception as e:
            print(e)

    def to_image(self, outfile=None, monitor=1):
        """Saves the map as a PNG or JPG image.

        Args:
            outfile (str, optional): The output file path to the image. Defaults to None.
            monitor (int, optional): The monitor to take the screenshot. Defaults to 1.
        """
        if outfile is None:
            outfile = os.path.join(os.getcwd(), 'my_map.png')

        if outfile.endswith('.png') or outfile.endswith('.jpg'):
            pass
        else:
            print('The output file must be a PNG or JPG image.')
            return

        work_dir = os.path.dirname(outfile)
        if not os.path.exists(work_dir):
            os.makedirs(work_dir)

        screenshot = screen_capture(outfile, monitor)
        self.screenshot = screenshot

    def toolbar_reset(self):
        """Reset the toolbar so that no tool is selected.
        """
        toolbar_grid = self.toolbar
        for tool in toolbar_grid.children:
            tool.value = False

    def add_raster(self, image, bands=None, layer_name=None, colormap=None, x_dim='x', y_dim='y'):
        """Adds a local raster dataset to the map.

        Args:
            image (str): The image file path.
            bands (int or list, optional): The image bands to use. It can be either a nubmer (e.g., 1) or a list (e.g., [3, 2, 1]). Defaults to None.
            layer_name (str, optional): The layer name to use for the raster. Defaults to None.
            colormap (str, optional): The name of the colormap to use for the raster, such as 'gray' and 'terrain'. More can be found at https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html. Defaults to None.
            x_dim (str, optional): The x dimension. Defaults to 'x'.
            y_dim (str, optional): The y dimension. Defaults to 'y'.
        """
        try:
            import xarray_leaflet

        except:
            # import platform
            # if platform.system() != "Windows":
            #     # install_from_github(
            #     #     url='https://github.com/davidbrochart/xarray_leaflet')
            #     check_install('xarray_leaflet')
            #     import xarray_leaflet
            # else:
            print(
                'You need to install xarray_leaflet first. See https://github.com/davidbrochart/xarray_leaflet')
            print(
                'Try the following to install xarray_leaflet: \n\nconda install -c conda-forge xarray_leaflet')
            return

        import warnings
        import numpy as np
        import rioxarray
        import xarray as xr
        import matplotlib.pyplot as plt

        warnings.simplefilter('ignore')

        if not os.path.exists(image):
            print('The image file does not exist.')
            return

        if colormap is None:
            colormap = plt.cm.inferno

        if layer_name is None:
            layer_name = 'Layer_' + random_string()

        if isinstance(colormap, str):
            colormap = plt.cm.get_cmap(name=colormap)

        da = rioxarray.open_rasterio(image, masked=True)

        # print(da.rio.nodata)

        multi_band = False
        if len(da.band) > 1:
            multi_band = True
            if bands is None:
                bands = [3, 2, 1]
        else:
            bands = 1

        if multi_band:
            da = da.rio.write_nodata(0)
        else:
            da = da.rio.write_nodata(np.nan)
        da = da.sel(band=bands)

        # crs = da.rio.crs
        # nan = da.attrs['nodatavals'][0]
        # da = da / da.max()
        # # if multi_band:
        # da = xr.where(da == nan, np.nan, da)
        # da = da.rio.write_nodata(0)
        # da = da.rio.write_crs(crs)

        if multi_band:
            layer = da.leaflet.plot(
                self, x_dim=x_dim, y_dim=y_dim, rgb_dim='band')
        else:
            layer = da.leaflet.plot(
                self, x_dim=x_dim, y_dim=y_dim, colormap=colormap)

        layer.name = layer_name

    def remove_drawn_features(self):
        """Removes user-drawn geometries from the map
        """
        if self.draw_layer is not None:
            self.remove_layer(self.draw_layer)
            self.draw_count = 0
            self.draw_features = []
            self.draw_last_feature = None
            self.draw_layer = None
            self.draw_last_json = None
            self.draw_last_bounds = None
            self.user_roi = None
            self.user_rois = None
            self.chart_values = []
            self.chart_points = []
            self.chart_labels = None

    def extract_values_to_points(self, filename):
        """Exports pixel values to a csv file based on user-drawn geometries.

        Args:
            filename (str): The output file path to the csv file or shapefile.
        """
        import csv

        filename = os.path.abspath(filename)
        allowed_formats = ['csv', 'shp']
        ext = filename[-3:]

        if ext not in allowed_formats:
            print('The output file must be one of the following: {}'.format(
                ', '.join(allowed_formats)))
            return

        out_dir = os.path.dirname(filename)
        out_csv = filename[:-3] + 'csv'
        out_shp = filename[:-3] + 'shp'
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        count = len(self.chart_points)
        out_list = []
        if count > 0:
            header = ['id', 'longitude', 'latitude'] + self.chart_labels
            out_list.append(header)

            for i in range(0, count):
                id = i + 1
                line = [id] + self.chart_points[i] + self.chart_values[i]
                out_list.append(line)

            with open(out_csv, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(out_list)

            if ext == 'csv':
                print('The csv file has been saved to: {}'.format(out_csv))
            else:
                csv_to_shp(out_csv, out_shp)
                print('The shapefile has been saved to: {}'.format(out_shp))


# The functions below are outside the Map class.

def screen_capture(outfile, monitor=1):
    """Takes a full screenshot of the selected monitor.

    Args:
        outfile (str): The output file path to the screenshot.
        monitor (int, optional): The monitor to take the screenshot. Defaults to 1.
    """
    from mss import mss

    out_dir = os.path.dirname(outfile)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if not isinstance(monitor, int):
        print('The monitor number must be an integer.')
        return

    try:
        with mss() as sct:
            sct.shot(output=outfile, mon=monitor)
            return outfile

    except Exception as e:
        print(e)


def install_from_github(url):
    """Install a package from a GitHub repository.

    Args:
        url (str): The URL of the GitHub repository.
    """

    try:
        download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        repo_name = os.path.basename(url)
        zip_url = os.path.join(url, 'archive/master.zip')
        filename = repo_name + '-master.zip'
        download_from_url(url=zip_url, out_file_name=filename,
                          out_dir=download_dir, unzip=True)

        pkg_dir = os.path.join(download_dir, repo_name + '-master')
        pkg_name = os.path.basename(url)
        work_dir = os.getcwd()
        os.chdir(pkg_dir)
        print('Installing {}...'.format(pkg_name))
        cmd = 'pip install .'
        os.system(cmd)
        os.chdir(work_dir)
        print('{} has been installed successfully.'.format(pkg_name))
        # print("\nPlease comment out 'install_from_github()' and restart the kernel to take effect:\nJupyter menu -> Kernel -> Restart & Clear Output")

    except Exception as e:
        print(e)


def rgb_to_hex(rgb=(255, 255, 255)):
    """Converts RGB to hex color. In RGB color R stands for Red, G stands for Green, and B stands for Blue, and it ranges from the decimal value of 0 – 255.

    Args:
        rgb (tuple, optional): RGB color code as a tuple of (red, green, blue). Defaults to (255, 255, 255).

    Returns:
        str: hex color code
    """
    return '%02x%02x%02x' % rgb


def hex_to_rgb(value='FFFFFF'):
    """Converts hex color to RGB color. 

    Args:
        value (str, optional): Hex color code as a string. Defaults to 'FFFFFF'.

    Returns:
        tuple: RGB color as a tuple.
    """
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i+lv//3], 16) for i in range(0, lv, lv//3))


def check_color(in_color):
    """Checks the input color and returns the corresponding hex color code.

    Args:
        in_color (str or tuple): It can be a string (e.g., 'red', '#ffff00') or tuple (e.g., (255, 127, 0)).

    Returns:
        str: A hex color code.
    """
    out_color = '#000000'  # default black color
    if isinstance(in_color, tuple) and len(in_color) == 3:
        if all(isinstance(item, int) for item in in_color):
            rescaled_color = [x / 255.0 for x in in_color]
            out_color = colour.Color(rgb=tuple(rescaled_color))
            return out_color.hex_l
        else:
            print(
                'RGB color must be a tuple with three integer values ranging from 0 to 255.')
            return
    else:
        try:
            out_color = colour.Color(in_color)
            return out_color.hex_l
        except Exception as e:
            print('The provided color is invalid. Using the default black color.')
            print(e)
            return out_color


def system_fonts(show_full_path=False):
    """Gets a list of system fonts.

        # Common font locations:
        # Linux: /usr/share/fonts/TTF/
        # Windows: C:\Windows\Fonts
        # macOS:  System > Library > Fonts

    Args:
        show_full_path (bool, optional): Whether to show the full path of each system font. Defaults to False.

    Returns:
        list: A list of system fonts.
    """
    try:
        import matplotlib.font_manager

        font_list = matplotlib.font_manager.findSystemFonts(
            fontpaths=None, fontext='ttf')
        font_list.sort()

        font_names = [os.path.basename(f) for f in font_list]
        font_names.sort()

        if show_full_path:
            return font_list
        else:
            return font_names

    except Exception as e:
        print(e)


def add_text_to_gif(in_gif, out_gif, xy=None, text_sequence=None, font_type="arial.ttf", font_size=20, font_color='#000000', add_progress_bar=True, progress_bar_color='white', progress_bar_height=5, duration=100, loop=0):
    """Adds animated text to a GIF image.

    Args:
        in_gif (str): The file path to the input GIF image.
        out_gif (str): The file path to the output GIF image.
        xy (tuple, optional): Top left corner of the text. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        text_sequence (int, str, list, optional): Text to be drawn. It can be an integer number, a string, or a list of strings. Defaults to None.
        font_type (str, optional): Font type. Defaults to "arial.ttf".
        font_size (int, optional): Font size. Defaults to 20.
        font_color (str, optional): Font color. It can be a string (e.g., 'red'), rgb tuple (e.g., (255, 127, 0)), or hex code (e.g., '#ff00ff').  Defaults to '#000000'.
        add_progress_bar (bool, optional): Whether to add a progress bar at the bottom of the GIF. Defaults to True.
        progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
        progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.
        duration (int, optional): controls how long each frame will be displayed for, in milliseconds. It is the inverse of the frame rate. Setting it to 100 milliseconds gives 10 frames per second. You can decrease the duration to give a smoother animation.. Defaults to 100.
        loop (int, optional): controls how many times the animation repeats. The default, 1, means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.

    """
    import io
    import pkg_resources
    import warnings
    from PIL import Image, ImageDraw, ImageSequence, ImageFont

    warnings.simplefilter('ignore')
    pkg_dir = os.path.dirname(
        pkg_resources.resource_filename("geemap", "geemap.py"))
    default_font = os.path.join(pkg_dir, 'data/fonts/arial.ttf')

    in_gif = os.path.abspath(in_gif)
    out_gif = os.path.abspath(out_gif)

    if not os.path.exists(in_gif):
        print('The input gif file does not exist.')
        return

    if not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

    if font_type == 'arial.ttf':
        font = ImageFont.truetype(default_font, font_size)
    else:
        try:
            font_list = system_fonts(show_full_path=True)
            font_names = [os.path.basename(f) for f in font_list]
            if (font_type in font_list) or (font_type in font_names):
                font = ImageFont.truetype(font_type, font_size)
            else:
                print(
                    'The specified font type could not be found on your system. Using the default font instead.')
                font = ImageFont.truetype(default_font, font_size)
        except Exception as e:
            print(e)
            font = ImageFont.truetype(default_font, font_size)

    color = check_color(font_color)
    progress_bar_color = check_color(progress_bar_color)

    try:
        image = Image.open(in_gif)
    except Exception as e:
        print('An error occurred while opening the gif.')
        print(e)
        return

    count = image.n_frames
    W, H = image.size
    progress_bar_widths = [i * 1.0 / count * W for i in range(1, count + 1)]
    progress_bar_shapes = [[(0, H - progress_bar_height), (x, H)]
                           for x in progress_bar_widths]

    if xy is None:
        # default text location is 5% width and 5% height of the image.
        xy = (int(0.05 * W), int(0.05 * H))
    elif (xy is not None) and (not isinstance(xy, tuple)) and (len(xy) == 2):
        print("xy must be a tuple, e.g., (10, 10), ('10%', '10%')")
        return
    elif all(isinstance(item, int) for item in xy) and (len(xy) == 2):
        x, y = xy
        if (x > 0) and (x < W) and (y > 0) and (y < H):
            pass
        else:
            print(
                'xy is out of bounds. x must be within [0, {}], and y must be within [0, {}]'.format(W, H))
            return
    elif all(isinstance(item, str) for item in xy) and (len(xy) == 2):
        x, y = xy
        if ('%' in x) and ('%' in y):
            try:
                x = int(float(x.replace('%', '')) / 100.0 * W)
                y = int(float(y.replace('%', '')) / 100.0 * H)
                xy = (x, y)
            except Exception as e:
                print(
                    "The specified xy is invalid. It must be formatted like this ('10%', '10%')")
                return
    else:
        print("The specified xy is invalid. It must be formatted like this: (10, 10) or ('10%', '10%')")
        return

    if text_sequence is None:
        text = [str(x) for x in range(1, count + 1)]
    elif isinstance(text_sequence, int):
        text = [str(x) for x in range(
            text_sequence, text_sequence + count + 1)]
    elif isinstance(text_sequence, str):
        try:
            text_sequence = int(text_sequence)
            text = [str(x) for x in range(
                text_sequence, text_sequence + count + 1)]
        except Exception as e:
            text = [text_sequence] * count
    elif isinstance(text_sequence, list) and len(text_sequence) != count:
        print('The length of the text sequence must be equal to the number ({}) of frames in the gif.'.format(count))
        return
    else:
        text = [str(x) for x in text_sequence]

    try:

        frames = []
        # Loop over each frame in the animated image
        for index, frame in enumerate(ImageSequence.Iterator(image)):
            # Draw the text on the frame
            frame = frame.convert('RGB')
            draw = ImageDraw.Draw(frame)
            # w, h = draw.textsize(text[index])
            draw.text(xy, text[index], font=font, fill=color)
            if add_progress_bar:
                draw.rectangle(
                    progress_bar_shapes[index], fill=progress_bar_color)
            del draw

            b = io.BytesIO()
            frame.save(b, format="GIF")
            frame = Image.open(b)

            frames.append(frame)
        # https://www.pythoninformer.com/python-libraries/pillow/creating-animated-gif/
        # Save the frames as a new image

        frames[0].save(out_gif, save_all=True,
                       append_images=frames[1:], duration=duration, loop=loop, optimize=True)
    except Exception as e:
        print(e)


def open_image_from_url(url):
    """Loads an image from the specified URL.

    Args:
        url (str): URL of the image.

    Returns:
        object: Image object.
    """
    from PIL import Image
    import requests
    from io import BytesIO
    from urllib.parse import urlparse

    try:

        # if url.endswith('.gif'):
        #     out_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        #     if not os.path.exists(out_dir):
        #         os.makedirs(out_dir)
        #     a = urlparse(url)
        #     out_name = os.path.basename(a.path)
        #     out_path = os.path.join(out_dir, out_name)
        #     download_from_url(url, out_name, out_dir, unzip=False)
        #     img =  Image.open(out_path)
        # else:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        print(e)


def has_transparency(img):
    """Checks whether an image has transparency.

    Args:
        img (object):  a PIL Image object.

    Returns:
        bool: True if it has transparency, False otherwise.
    """

    if img.mode == "P":
        transparent = img.info.get("transparency", -1)
        for _, index in img.getcolors():
            if index == transparent:
                return True
    elif img.mode == "RGBA":
        extrema = img.getextrema()
        if extrema[3][0] < 255:
            return True

    return False


def add_image_to_gif(in_gif, out_gif, in_image, xy=None, image_size=(80, 80), circle_mask=False):
    """Adds an image logo to a GIF image.

    Args:
        in_gif (str): Input file path to the GIF image.
        out_gif (str): Output file path to the GIF image.
        in_image (str): Input file path to the image.
        xy (tuple, optional): Top left corner of the text. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        image_size (tuple, optional): Resize image. Defaults to (80, 80).
        circle_mask (bool, optional): Whether to apply a circle mask to the image. This only works with non-png images. Defaults to False.
    """
    import io
    import warnings
    from PIL import Image, ImageDraw, ImageSequence, ImageFilter

    warnings.simplefilter('ignore')

    in_gif = os.path.abspath(in_gif)

    is_url = False
    if in_image.startswith('http'):
        is_url = True

    if not os.path.exists(in_gif):
        print('The input gif file does not exist.')
        return

    if (not is_url) and (not os.path.exists(in_image)):
        print('The provided logo file does not exist.')
        return

    if not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

    try:
        image = Image.open(in_gif)
    except Exception as e:
        print('An error occurred while opening the image.')
        print(e)
        return

    try:
        if in_image.startswith('http'):
            logo_raw_image = open_image_from_url(in_image)
        else:
            in_image = os.path.abspath(in_image)
            logo_raw_image = Image.open(in_image)
    except Exception as e:
        print(e)

    logo_raw_size = logo_raw_image.size
    image_size = min(logo_raw_size[0], image_size[0]), min(
        logo_raw_size[1], image_size[1])

    logo_image = logo_raw_image.convert('RGBA')
    logo_image.thumbnail(image_size, Image.ANTIALIAS)

    W, H = image.size
    mask_im = None

    if circle_mask:
        mask_im = Image.new("L", image_size, 0)
        draw = ImageDraw.Draw(mask_im)
        draw.ellipse((0, 0, image_size[0], image_size[1]), fill=255)

    if has_transparency(logo_raw_image):
        mask_im = logo_image.copy()

    if xy is None:
        # default logo location is 5% width and 5% height of the image.
        xy = (int(0.05 * W), int(0.05 * H))
    elif (xy is not None) and (not isinstance(xy, tuple)) and (len(xy) == 2):
        print("xy must be a tuple, e.g., (10, 10), ('10%', '10%')")
        return
    elif all(isinstance(item, int) for item in xy) and (len(xy) == 2):
        x, y = xy
        if (x > 0) and (x < W) and (y > 0) and (y < H):
            pass
        else:
            print(
                'xy is out of bounds. x must be within [0, {}], and y must be within [0, {}]'.format(W, H))
            return
    elif all(isinstance(item, str) for item in xy) and (len(xy) == 2):
        x, y = xy
        if ('%' in x) and ('%' in y):
            try:
                x = int(float(x.replace('%', '')) / 100.0 * W)
                y = int(float(y.replace('%', '')) / 100.0 * H)
                xy = (x, y)
            except Exception as e:
                print(
                    "The specified xy is invalid. It must be formatted like this ('10%', '10%')")
                return
    else:
        print("The specified xy is invalid. It must be formatted like this: (10, 10) or ('10%', '10%')")
        return

    try:

        frames = []
        for index, frame in enumerate(ImageSequence.Iterator(image)):
            frame = frame.convert('RGBA')
            frame.paste(logo_image, xy, mask_im)

            b = io.BytesIO()
            frame.save(b, format="GIF")
            frame = Image.open(b)
            frames.append(frame)

        frames[0].save(out_gif, save_all=True, append_images=frames[1:])
    except Exception as e:
        print(e)


def show_image(img_path, width=None, height=None):
    """Shows an image within Jupyter notebook.

    Args:
        img_path (str): The image file path.
        width (int, optional): Width of the image in pixels. Defaults to None.
        height (int, optional): Height of the image in pixels. Defaults to None.

    """
    from IPython.display import display

    try:
        out = widgets.Output()
        # layout={'border': '1px solid black'})
        # layout={'border': '1px solid black', 'width': str(width + 20) + 'px', 'height': str(height + 10) + 'px'},)
        out.clear_output(wait=True)
        display(out)
        with out:
            file = open(img_path, "rb")
            image = file.read()
            if (width is None) and (height is None):
                display(widgets.Image(value=image))
            elif (width is not None) and (height is not None):
                display(widgets.Image(value=image, width=width, height=height))
            else:
                print('You need set both width and height.')
                return
    except Exception as e:
        print(e)


def legend_from_ee(ee_class_table):
    """Extract legend from an Earth Engine class table on the Earth Engine Data Catalog page
    such as https://developers.google.com/earth-engine/datasets/catalog/MODIS_051_MCD12Q1

    Value	Color	Description
    0	1c0dff	Water
    1	05450a	Evergreen needleleaf forest
    2	086a10	Evergreen broadleaf forest
    3	54a708	Deciduous needleleaf forest
    4	78d203	Deciduous broadleaf forest
    5	009900	Mixed forest
    6	c6b044	Closed shrublands
    7	dcd159	Open shrublands
    8	dade48	Woody savannas
    9	fbff13	Savannas
    10	b6ff05	Grasslands
    11	27ff87	Permanent wetlands
    12	c24f44	Croplands
    13	a5a5a5	Urban and built-up
    14	ff6d4c	Cropland/natural vegetation mosaic
    15	69fff8	Snow and ice
    16	f9ffa4	Barren or sparsely vegetated
    254	ffffff	Unclassified

    Args:
        ee_class_table (str): An Earth Engine class table with triple quotes.

    Returns:
        dict: Returns a legend dictionary that can be used to create a legend.
    """
    try:
        ee_class_table = ee_class_table.strip()
        lines = ee_class_table.split('\n')[1:]

        if lines[0] == 'Value\tColor\tDescription':
            lines = lines[1:]

        legend_dict = {}
        for index, line in enumerate(lines):
            items = line.split("\t")
            items = [item.strip() for item in items]
            color = items[1]
            key = items[0] + " " + items[2]
            legend_dict[key] = color

        return legend_dict

    except Exception as e:
        print(e)


def ee_tile_layer(ee_object, vis_params={}, name='Layer untitled', shown=True, opacity=1.0):
    """Converts and Earth Engine layer to ipyleaflet TileLayer.

    Args:
        ee_object (Collection|Feature|Image|MapId): The object to add to the map.
        vis_params (dict, optional): The visualization parameters. Defaults to {}.
        name (str, optional): The name of the layer. Defaults to 'Layer untitled'.
        shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
        opacity (float, optional): The layer's opacity represented as a number between 0 and 1. Defaults to 1.
    """
    # ee_initialize()

    image = None

    if not isinstance(ee_object, ee.Image) and not isinstance(ee_object, ee.ImageCollection) and not isinstance(ee_object, ee.FeatureCollection) and not isinstance(ee_object, ee.Feature) and not isinstance(ee_object, ee.Geometry):
        err_str = "\n\nThe image argument in 'addLayer' function must be an instace of one of ee.Image, ee.Geometry, ee.Feature or ee.FeatureCollection."
        raise AttributeError(err_str)

    if isinstance(ee_object, ee.geometry.Geometry) or isinstance(ee_object, ee.feature.Feature) or isinstance(ee_object, ee.featurecollection.FeatureCollection):
        features = ee.FeatureCollection(ee_object)

        width = 2

        if 'width' in vis_params:
            width = vis_params['width']

        color = '000000'

        if 'color' in vis_params:
            color = vis_params['color']

        image_fill = features.style(
            **{'fillColor': color}).updateMask(ee.Image.constant(0.5))
        image_outline = features.style(
            **{'color': color, 'fillColor': '00000000', 'width': width})

        image = image_fill.blend(image_outline)
    elif isinstance(ee_object, ee.image.Image):
        image = ee_object
    elif isinstance(ee_object, ee.imagecollection.ImageCollection):
        image = ee_object.mosaic()

    map_id_dict = ee.Image(image).getMapId(vis_params)
    tile_layer = ipyleaflet.TileLayer(
        url=map_id_dict['tile_fetcher'].url_format,
        attribution='Google Earth Engine',
        name=name,
        opacity=opacity,
        visible=True
        # visible=shown
    )
    return tile_layer


def geojson_to_ee(geo_json, geodesic=True):
    """Converts a geojson to ee.Geometry()

    Args:
        geo_json (dict): A geojson geometry dictionary or file path.

    Returns:
        ee_object: An ee.Geometry object
    """
    # ee_initialize()

    try:

        import json

        if not isinstance(geo_json, dict) and os.path.isfile(geo_json):
            with open(os.path.abspath(geo_json)) as f:
                geo_json = json.load(f)

        if geo_json['type'] == 'FeatureCollection':
            features = ee.FeatureCollection(geo_json['features'])
            return features
        elif geo_json['type'] == 'Feature':
            geom = None
            keys = geo_json['properties']['style'].keys()
            if 'radius' in keys:  # Checks whether it is a circle
                geom = ee.Geometry(geo_json['geometry'])
                radius = geo_json['properties']['style']['radius']
                geom = geom.buffer(radius)
            elif geo_json['geometry']['type'] == 'Point':  # Checks whether it is a point
                coordinates = geo_json['geometry']['coordinates']
                longitude = coordinates[0]
                latitude = coordinates[1]
                geom = ee.Geometry.Point(longitude, latitude)
            else:
                geom = ee.Geometry(geo_json['geometry'], "", geodesic)
            return geom
        else:
            print("Could not convert the geojson to ee.Geometry()")

    except Exception as e:
        print("Could not convert the geojson to ee.Geometry()")
        print(e)


def ee_to_geojson(ee_object, out_json=None):
    """Converts Earth Engine object to geojson.

    Args:
        ee_object (object): An Earth Engine object.

    Returns:
        object: GeoJSON object.
    """
    from json import dumps
    # ee_initialize()

    try:
        if isinstance(ee_object, ee.geometry.Geometry) or isinstance(ee_object, ee.feature.Feature) or isinstance(ee_object, ee.featurecollection.FeatureCollection):
            json_object = ee_object.getInfo()
            if out_json is not None:
                out_json = os.path.abspath(out_json)
                if not os.path.exists(os.path.dirname(out_json)):
                    os.makedirs(os.path.dirname(out_json))
                geojson = open(out_json, "w")
                geojson.write(
                    dumps({"type": "FeatureCollection", "features": json_object}, indent=2) + "\n")
                geojson.close()
            return json_object
        else:
            print("Could not convert the Earth Engine object to geojson")
    except Exception as e:
        print(e)


def open_github(subdir=None):
    """Opens the GitHub repository for this package.

    Args:
        subdir (str, optional): Sub-directory of the repository. Defaults to None.
    """
    import webbrowser

    url = 'https://github.com/giswqs/geemap'

    if subdir == 'source':
        url += '/tree/master/geemap/'
    elif subdir == 'examples':
        url += '/tree/master/examples'
    elif subdir == 'tutorials':
        url += '/tree/master/tutorials'

    webbrowser.open_new_tab(url)


def clone_repo(out_dir='.', unzip=True):
    """Clones the geemap GitHub repository.

    Args:
        out_dir (str, optional): Output folder for the repo. Defaults to '.'.
        unzip (bool, optional): Whether to unzip the repository. Defaults to True.
    """
    url = 'https://github.com/giswqs/geemap/archive/master.zip'
    filename = 'geemap-master.zip'
    download_from_url(url, out_file_name=filename,
                      out_dir=out_dir, unzip=unzip)


def open_youtube():
    """Opens the YouTube tutorials for geemap.
    """
    import webbrowser

    url = 'https://www.youtube.com/playlist?list=PLAxJ4-o7ZoPccOFv1dCwvGI6TYnirRTg3'
    webbrowser.open_new_tab(url)


def api_docs():
    """Open a browser and navigate to the geemap API documentation.
    """
    import webbrowser

    url = 'https://giswqs.github.io/geemap/geemap'
    webbrowser.open_new_tab(url)


def show_youtube(id='h0pz3S6Tvx0'):
    """Displays a YouTube video within Jupyter notebooks.

    Args:
        id (str, optional): Unique ID of the video. Defaults to 'h0pz3S6Tvx0'.

    """
    from IPython.display import YouTubeVideo, display
    try:
        out = widgets.Output(
            layout={'width': '815px'})
        # layout={'border': '1px solid black', 'width': '815px'})
        out.clear_output(wait=True)
        display(out)
        with out:
            display(YouTubeVideo(id, width=800, height=450))
    except Exception as e:
        print(e)


def check_install(package):
    """Checks whether a package is installed. If not, it will install the package.

    Args:
        package (str): The name of the package to check.
    """
    import subprocess

    try:
        __import__(package)
        # print('{} is already installed.'.format(package))
    except ImportError:
        print('{} is not installed. Installing ...'.format(package))
        try:
            subprocess.check_call(["python", '-m', 'pip', 'install', package])
        except Exception as e:
            print('Failed to install {}'.format(package))
            print(e)
        print("{} has been installed successfully.".format(package))


def update_package():
    """Updates the geemap package from the geemap GitHub repository without the need to use pip or conda.
        In this way, I don't have to keep updating pypi and conda-forge with every minor update of the package.

    """
    import shutil
    try:
        download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        clone_repo(out_dir=download_dir)

        pkg_dir = os.path.join(download_dir, 'geemap-master')
        work_dir = os.getcwd()
        os.chdir(pkg_dir)

        if shutil.which('pip') is None:
            cmd = 'pip3 install .'
        else:
            cmd = 'pip install .'

        os.system(cmd)
        os.chdir(work_dir)

        print("\nPlease comment out 'geemap.update_package()' and restart the kernel to take effect:\nJupyter menu -> Kernel -> Restart & Clear Output")

    except Exception as e:
        print(e)


def csv_to_shp(in_csv, out_shp, longitude='longitude', latitude='latitude'):
    """Converts a csv file with latlon info to a point shapefile.

    Args:
        in_csv (str): The input csv file containing longitude and latitude columns.
        out_shp (str): The file path to the output shapefile.
        longitude (str, optional): The column name of the longitude column. Defaults to 'longitude'.
        latitude (str, optional): The column name of the latitude column. Defaults to 'latitude'.
    """
    import csv
    import shapefile as shp

    if not os.path.exists(in_csv):
        print('The provided CSV file does not exist.')
        return

    if not in_csv.endswith('.csv'):
        print('The input file must end with .csv')
        return

    out_dir = os.path.dirname(out_shp)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    try:
        points = shp.Writer(out_shp, shapeType=shp.POINT)
        with open(in_csv) as csvfile:
            csvreader = csv.DictReader(csvfile)
            header = csvreader.fieldnames
            [points.field(field) for field in header]
            for row in csvreader:
                points.point((float(row[longitude])), (float(row[latitude])))
                points.record(*tuple([row[f] for f in header]))

        out_prj = out_shp.replace('.shp', '.prj')
        with open(out_prj, 'w') as f:
            prj_str = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.0174532925199433]] '
            f.write(prj_str)

    except Exception as e:
        print(e)


def shp_to_geojson(in_shp, out_json=None):
    """Converts a shapefile to GeoJSON.

    Args:
        in_shp (str): File path of the input shapefile.
        out_json (str, optional): File path of the output GeoJSON. Defaults to None.

    Returns:
        object: The json object representing the shapefile.
    """
    # check_install('pyshp')
    # ee_initialize()
    try:
        import json
        import shapefile
        in_shp = os.path.abspath(in_shp)

        if out_json is None:
            out_json = os.path.splitext(in_shp)[0] + ".json"

            if os.path.exists(out_json):
                out_json = out_json.replace('.json', '_bk.json')

        elif not os.path.exists(os.path.dirname(out_json)):
            os.makedirs(os.path.dirname(out_json))

        reader = shapefile.Reader(in_shp)
        fields = reader.fields[1:]
        field_names = [field[0] for field in fields]
        buffer = []
        for sr in reader.shapeRecords():
            atr = dict(zip(field_names, sr.record))
            geom = sr.shape.__geo_interface__
            buffer.append(dict(type="Feature", geometry=geom, properties=atr))

        from json import dumps
        geojson = open(out_json, "w")
        geojson.write(dumps({"type": "FeatureCollection",
                             "features": buffer}, indent=2) + "\n")
        geojson.close()

        with open(out_json) as f:
            json_data = json.load(f)

        return json_data

    except Exception as e:
        print(e)


def shp_to_ee(in_shp):
    """Converts a shapefile to Earth Engine objects.

    Args:
        in_shp (str): File path to a shapefile.

    Returns:
        object: Earth Engine objects representing the shapefile.
    """
    # ee_initialize()
    try:
        json_data = shp_to_geojson(in_shp)
        ee_object = geojson_to_ee(json_data)
        return ee_object
    except Exception as e:
        print(e)


def filter_polygons(ftr):
    """Converts GeometryCollection to Polygon/MultiPolygon

    Args:
        ftr (object): ee.Feature

    Returns:
        object: ee.Feature
    """
    # ee_initialize()
    geometries = ftr.geometry().geometries()
    geometries = geometries.map(lambda geo: ee.Feature(
        ee.Geometry(geo)).set('geoType',  ee.Geometry(geo).type()))

    polygons = ee.FeatureCollection(geometries).filter(
        ee.Filter.eq('geoType', 'Polygon')).geometry()
    return ee.Feature(polygons).copyProperties(ftr)


def ee_export_vector(ee_object, filename, selectors=None):
    """Exports Earth Engine FeatureCollection to other formats, including shp, csv, json, kml, and kmz.

    Args:
        ee_object (object): ee.FeatureCollection to export.
        filename (str): Output file name.
        selectors (list, optional): A list of attributes to export. Defaults to None.
    """
    import requests
    import zipfile
    # ee_initialize()

    if not isinstance(ee_object, ee.FeatureCollection):
        raise ValueError('ee_object must be an ee.FeatureCollection')

    allowed_formats = ['csv', 'geojson', 'kml', 'kmz', 'shp']
    # allowed_formats = ['csv', 'kml', 'kmz']
    filename = os.path.abspath(filename)
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:].lower()

    if filetype == 'shp':
        filename = filename.replace('.shp', '.zip')

    if not (filetype.lower() in allowed_formats):
        print('The file type must be one of the following: {}'.format(
            ', '.join(allowed_formats)))
        print('Earth Engine no longer supports downloading featureCollection as shapefile or json. \nPlease use geemap.ee_export_vector_to_drive() to export featureCollection to Google Drive.')
        raise ValueError

    if selectors is None:
        selectors = ee_object.first().propertyNames().getInfo()
        if filetype == 'csv':
            # remove .geo coordinate field
            ee_object = ee_object.select([".*"], None, False)

    if filetype == 'geojson':
        selectors = ['.geo'] + selectors

    elif not isinstance(selectors, list):
        raise ValueError(
            "selectors must be a list, such as ['attribute1', 'attribute2']")
    else:
        allowed_attributes = ee_object.first().propertyNames().getInfo()
        for attribute in selectors:
            if not (attribute in allowed_attributes):
                raise ValueError('Attributes must be one chosen from: {} '.format(
                    ', '.join(allowed_attributes)))

    try:
        print('Generating URL ...')
        url = ee_object.getDownloadURL(
            filetype=filetype, selectors=selectors, filename=name)
        print('Downloading data from {}\nPlease wait ...'.format(url))
        r = requests.get(url, stream=True)

        if r.status_code != 200:
            print('An error occurred while downloading. \n Retrying ...')
            try:
                new_ee_object = ee_object.map(filter_polygons)
                print('Generating URL ...')
                url = new_ee_object.getDownloadURL(
                    filetype=filetype, selectors=selectors, filename=name)
                print('Downloading data from {}\nPlease wait ...'.format(url))
                r = requests.get(url, stream=True)
            except Exception as e:
                print(e)
                raise ValueError

        with open(filename, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=1024):
                fd.write(chunk)
    except Exception as e:
        print('An error occurred while downloading.')
        raise ValueError(e)

    try:
        if filetype == 'shp':
            z = zipfile.ZipFile(filename)
            z.extractall(os.path.dirname(filename))
            os.remove(filename)
            filename = filename.replace('.zip', '.shp')

        print('Data downloaded to {}'.format(filename))
    except Exception as e:
        raise ValueError(e)


def ee_export_vector_to_drive(ee_object, description, folder, file_format='shp', selectors=None):
    """Exports Earth Engine FeatureCollection to Google Drive. other formats, including shp, csv, json, kml, and kmz.

    Args:
        ee_object (object): ee.FeatureCollection to export.
        description (str): File name of the output file.
        folder (str): Folder name within Google Drive to save the exported file.
        file_format (str, optional): The supported file format include shp, csv, json, kml, kmz, and TFRecord. Defaults to 'shp'.
        selectors (list, optional): The list of attributes to export. Defaults to None.
    """
    if not isinstance(ee_object, ee.FeatureCollection):
        print('The ee_object must be an ee.FeatureCollection.')
        return

    allowed_formats = ['csv', 'json', 'kml', 'kmz', 'shp', 'tfrecord']
    if not (file_format.lower() in allowed_formats):
        print('The file type must be one of the following: {}'.format(
            ', '.join(allowed_formats)))
        return

    task_config = {
        'folder': folder,
        'fileFormat': file_format,
    }

    if selectors is not None:
        task_config['selectors'] = selectors
    elif (selectors is None) and (file_format.lower() == 'csv'):
        # remove .geo coordinate field
        ee_object = ee_object.select([".*"], None, False)

    print('Exporting {}...'.format(description))
    task = ee.batch.Export.table.toDrive(ee_object, description, **task_config)
    task.start()


def ee_export_geojson(ee_object, filename=None, selectors=None):
    """Exports Earth Engine FeatureCollection to geojson.

    Args:
        ee_object (object): ee.FeatureCollection to export.
        filename (str): Output file name. Defaults to None.
        selectors (list, optional): A list of attributes to export. Defaults to None.
    """
    import requests
    import zipfile
    # ee_initialize()

    if not isinstance(ee_object, ee.FeatureCollection):
        print('The ee_object must be an ee.FeatureCollection.')
        return

    if filename is None:
        out_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        filename = os.path.join(out_dir, random_string(6) + '.geojson')

    allowed_formats = ['geojson']
    filename = os.path.abspath(filename)
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:].lower()

    if not (filetype.lower() in allowed_formats):
        print('The output file type must be geojson.')
        return

    if selectors is None:
        selectors = ee_object.first().propertyNames().getInfo()
        selectors = ['.geo'] + selectors

    elif not isinstance(selectors, list):
        print("selectors must be a list, such as ['attribute1', 'attribute2']")
        return
    else:
        allowed_attributes = ee_object.first().propertyNames().getInfo()
        for attribute in selectors:
            if not (attribute in allowed_attributes):
                print('Attributes must be one chosen from: {} '.format(
                    ', '.join(allowed_attributes)))
                return

    try:
        # print('Generating URL ...')
        url = ee_object.getDownloadURL(
            filetype=filetype, selectors=selectors, filename=name)
        # print('Downloading data from {}\nPlease wait ...'.format(url))
        r = requests.get(url, stream=True)

        if r.status_code != 200:
            print('An error occurred while downloading. \n Retrying ...')
            try:
                new_ee_object = ee_object.map(filter_polygons)
                print('Generating URL ...')
                url = new_ee_object.getDownloadURL(
                    filetype=filetype, selectors=selectors, filename=name)
                print('Downloading data from {}\nPlease wait ...'.format(url))
                r = requests.get(url, stream=True)
            except Exception as e:
                print(e)

        with open(filename, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=1024):
                fd.write(chunk)
    except Exception as e:
        print('An error occurred while downloading.')
        print(e)
        return

    with open(filename) as f:
        geojson = f.read()

    return geojson


def ee_to_shp(ee_object, filename, selectors=None):
    """Downloads an ee.FeatureCollection as a shapefile.

    Args:
        ee_object (object): ee.FeatureCollection
        filename (str): The output filepath of the shapefile.
        selectors (list, optional): A list of attributes to export. Defaults to None.
    """
    # ee_initialize()
    try:
        if filename.lower().endswith('.shp'):
            ee_export_vector(ee_object=ee_object,
                             filename=filename, selectors=selectors)
        else:
            print('The filename must end with .shp')

    except Exception as e:
        print(e)


def ee_to_csv(ee_object, filename, selectors=None):
    """Downloads an ee.FeatureCollection as a CSV file.

    Args:
        ee_object (object): ee.FeatureCollection
        filename (str): The output filepath of the CSV file.
        selectors (list, optional): A list of attributes to export. Defaults to None.
    """
    # ee_initialize()
    try:
        if filename.lower().endswith('.csv'):
            ee_export_vector(ee_object=ee_object,
                             filename=filename, selectors=selectors)
        else:
            print('The filename must end with .csv')

    except Exception as e:
        print(e)


def ee_export_image(ee_object, filename, scale=None, crs=None, region=None, file_per_band=False):
    """Exports an ee.Image as a GeoTIFF.

    Args:
        ee_object (object): The ee.Image to download.
        filename (str): Output filename for the exported image.
        scale (float, optional): A default scale to use for any bands that do not specify one; ignored if crs and crs_transform is specified. Defaults to None.
        crs (str, optional): A default CRS string to use for any bands that do not explicitly specify one. Defaults to None.
        region (object, optional): A polygon specifying a region to download; ignored if crs and crs_transform is specified. Defaults to None.
        file_per_band (bool, optional): Whether to produce a different GeoTIFF per band. Defaults to False.
    """
    import requests
    import zipfile
    # ee_initialize()

    if not isinstance(ee_object, ee.Image):
        print('The ee_object must be an ee.Image.')
        return

    filename = os.path.abspath(filename)
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:].lower()
    filename_zip = filename.replace('.tif', '.zip')

    if filetype != 'tif':
        print('The filename must end with .tif')
        return

    try:
        print('Generating URL ...')
        params = {'name': name, 'filePerBand': file_per_band}
        if scale is None:
            scale = ee_object.projection().nominalScale().multiply(10)
        params['scale'] = scale
        if region is None:
            region = ee_object.geometry()
        params['region'] = region
        if crs is not None:
            params['crs'] = crs

        url = ee_object.getDownloadURL(params)
        print('Downloading data from {}\nPlease wait ...'.format(url))
        r = requests.get(url, stream=True)

        if r.status_code != 200:
            print('An error occurred while downloading.')
            return

        with open(filename_zip, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=1024):
                fd.write(chunk)

    except Exception as e:
        print('An error occurred while downloading.')
        print(e)
        return

    try:
        z = zipfile.ZipFile(filename_zip)
        z.extractall(os.path.dirname(filename))
        z.close()
        os.remove(filename_zip)

        if file_per_band:
            print('Data downloaded to {}'.format(os.path.dirname(filename)))
        else:
            print('Data downloaded to {}'.format(filename))
    except Exception as e:
        print(e)


def ee_export_image_collection(ee_object, out_dir, scale=None, crs=None, region=None, file_per_band=False):
    """Exports an ImageCollection as GeoTIFFs.

    Args:
        ee_object (object): The ee.Image to download.
        out_dir (str): The output directory for the exported images.
        scale (float, optional): A default scale to use for any bands that do not specify one; ignored if crs and crs_transform is specified. Defaults to None.
        crs (str, optional): A default CRS string to use for any bands that do not explicitly specify one. Defaults to None.
        region (object, optional): A polygon specifying a region to download; ignored if crs and crs_transform is specified. Defaults to None.
        file_per_band (bool, optional): Whether to produce a different GeoTIFF per band. Defaults to False.
    """

    import requests
    import zipfile
    # ee_initialize()

    if not isinstance(ee_object, ee.ImageCollection):
        print('The ee_object must be an ee.ImageCollection.')
        return

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    try:

        count = int(ee_object.size().getInfo())
        print("Total number of images: {}\n".format(count))

        for i in range(0, count):
            image = ee.Image(ee_object.toList(count).get(i))
            name = image.get('system:index').getInfo() + '.tif'
            filename = os.path.join(os.path.abspath(out_dir), name)
            print('Exporting {}/{}: {}'.format(i+1, count, name))
            ee_export_image(image, filename=filename, scale=scale,
                            crs=crs, region=region, file_per_band=file_per_band)
            print('\n')

    except Exception as e:
        print(e)


def ee_export_image_to_drive(ee_object, description, folder=None, region=None, scale=None, crs=None, max_pixels=1.0E13, file_format='GeoTIFF'):
    """Creates a batch task to export an Image as a raster to Google Drive.

    Args:
        ee_object (object): The image to export.
        description (str): A human-readable name of the task. 
        folder (str, optional): The Google Drive Folder that the export will reside in. Defaults to None.
        region (object, optional): A LinearRing, Polygon, or coordinates representing region to export. These may be specified as the Geometry objects or coordinates serialized as a string. If not specified, the region defaults to the viewport at the time of invocation. Defaults to None.
        scale (float, optional): Resolution in meters per pixel. Defaults to 10 times of the image resolution.
        crs (str, optional): CRS to use for the exported image.. Defaults to None.
        max_pixels (int, optional): Restrict the number of pixels in the export. Defaults to 1.0E13.
        file_format (str, optional): The string file format to which the image is exported. Currently only 'GeoTIFF' and 'TFRecord' are supported. Defaults to 'GeoTIFF'.
    """
    # ee_initialize()

    if not isinstance(ee_object, ee.Image):
        print('The ee_object must be an ee.Image.')
        return

    try:
        params = {}

        if folder is not None:
            params['driveFolder'] = folder
        if region is not None:
            params['region'] = region
        if scale is None:
            scale = ee_object.projection().nominalScale().multiply(10)
        params['scale'] = scale
        if crs is not None:
            params['crs'] = crs
        params['maxPixels'] = max_pixels
        params['fileFormat'] = file_format

        task = ee.batch.Export.image(ee_object, description, params)
        task.start()

        print('Exporting {} ...'.format(description))

    except Exception as e:
        print(e)


def ee_export_image_collection_to_drive(ee_object, descriptions=None, folder=None, region=None, scale=None, crs=None, max_pixels=1.0E13, file_format='GeoTIFF'):
    """Creates a batch task to export an ImageCollection as raster images to Google Drive.

    Args:
        ee_object (object): The image to export.
        descriptions (list): A list of human-readable names of the tasks. 
        folder (str, optional): The Google Drive Folder that the export will reside in. Defaults to None.
        region (object, optional): A LinearRing, Polygon, or coordinates representing region to export. These may be specified as the Geometry objects or coordinates serialized as a string. If not specified, the region defaults to the viewport at the time of invocation. Defaults to None.
        scale (float, optional): Resolution in meters per pixel. Defaults to 10 times of the image resolution.
        crs (str, optional): CRS to use for the exported image.. Defaults to None.
        max_pixels (int, optional): Restrict the number of pixels in the export. Defaults to 1.0E13.
        file_format (str, optional): The string file format to which the image is exported. Currently only 'GeoTIFF' and 'TFRecord' are supported. Defaults to 'GeoTIFF'.
    """
    # ee_initialize()

    if not isinstance(ee_object, ee.ImageCollection):
        print('The ee_object must be an ee.ImageCollection.')
        return

    try:
        count = int(ee_object.size().getInfo())
        print("Total number of images: {}\n".format(count))

        if (descriptions is not None) and (len(descriptions) != count):
            print('The number of descriptions is not equal to the number of images.')
            return

        if descriptions is None:
            descriptions = ee_object.aggregate_array('system:index').getInfo()

        images = ee_object.toList(count)

        for i in range(0, count):
            image = ee.Image(images.get(i))
            name = descriptions[i]
            ee_export_image_to_drive(
                image, name, folder, region, scale, crs, max_pixels, file_format)

    except Exception as e:
        print(e)


def ee_to_numpy(ee_object, bands=None, region=None, properties=None, default_value=None):
    """Extracts a rectangular region of pixels from an image into a 2D numpy array per band.

    Args:
        ee_object (object): The image to sample.
        bands (list, optional): The list of band names to extract. Please make sure that all bands have the same spatial resolution. Defaults to None. 
        region (object, optional): The region whose projected bounding box is used to sample the image. The maximum number of pixels you can export is 262,144. Resampling and reprojecting all bands to a fixed scale can be useful. Defaults to the footprint in each band.
        properties (list, optional): The properties to copy over from the sampled image. Defaults to all non-system properties.
        default_value (float, optional): A default value used when a sampled pixel is masked or outside a band's footprint. Defaults to None.

    Returns:
        array: A 3D numpy array.
    """
    import numpy as np
    if not isinstance(ee_object, ee.Image):
        print('The input must be an ee.Image.')
        return

    if region is None:
        region = ee_object.geometry()

    try:

        if bands is not None:
            ee_object = ee_object.select(bands)
        else:
            bands = ee_object.bandNames().getInfo()

        band_count = len(bands)
        band_arrs = ee_object.sampleRectangle(
            region=region, properties=properties, defaultValue=default_value)
        band_values = []

        for band in bands:
            band_arr = band_arrs.get(band).getInfo()
            band_value = np.array(band_arr)
            band_values.append(band_value)

        image = np.dstack(band_values)
        return image

    except Exception as e:
        print(e)


def download_ee_video(collection, video_args, out_gif):
    """Downloads a video thumbnail as a GIF image from Earth Engine.

    Args:
        collection (object): An ee.ImageCollection.
        video_args (object): Parameters for expring the video thumbnail.
        out_gif (str): File path to the output GIF.
    """
    import requests

    out_gif = os.path.abspath(out_gif)
    if not out_gif.endswith(".gif"):
        print('The output file must have an extension of .gif.')
        return

    if not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

    if 'region' in video_args.keys():
        roi = video_args['region']

        if not isinstance(roi, ee.Geometry):

            try:
                roi = roi.geometry()
            except Exception as e:
                print('Could not convert the provided roi to ee.Geometry')
                print(e)
                return

        video_args['region'] = roi

    try:
        print('Generating URL...')
        url = collection.getVideoThumbURL(video_args)

        print('Downloading GIF image from {}\nPlease wait ...'.format(url))
        r = requests.get(url, stream=True)

        if r.status_code != 200:
            print('An error occurred while downloading.')
            return
        else:
            with open(out_gif, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=1024):
                    fd.write(chunk)
            print('The GIF image has been saved to: {}'.format(out_gif))
    except Exception as e:
        print(e)


def zonal_statistics(in_value_raster, in_zone_vector, out_file_path, statistics_type='MEAN', scale=None, crs=None, tile_scale=1.0, **kwargs):
    """Summarizes the values of a raster within the zones of another dataset and exports the results as a csv, shp, json, kml, or kmz.

    Args:
        in_value_raster (object): An ee.Image that contains the values on which to calculate a statistic.
        in_zone_vector (object): An ee.FeatureCollection that defines the zones.
        out_file_path (str): Output file path that will contain the summary of the values in each zone. The file type can be: csv, shp, json, kml, kmz
        statistics_type (str, optional): Statistic type to be calculated. Defaults to 'MEAN'. For 'HIST', you can provide three parameters: max_buckets, min_bucket_width, and max_raw. For 'FIXED_HIST', you must provide three parameters: hist_min, hist_max, and hist_steps.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
        crs (str, optional): The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale. Defaults to None.
        tile_scale (float, optional): A scaling factor used to reduce aggregation tile size; using a larger tileScale (e.g. 2 or 4) may enable computations that run out of memory with the default. Defaults to 1.0.
    """

    if not isinstance(in_value_raster, ee.Image):
        print('The input raster must be an ee.Image.')
        return

    if not isinstance(in_zone_vector, ee.FeatureCollection):
        print('The input zone data must be an ee.FeatureCollection.')
        return

    allowed_formats = ['csv', 'json', 'kml', 'kmz', 'shp']
    filename = os.path.abspath(out_file_path)
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:].lower()

    if not (filetype in allowed_formats):
        print('The file type must be one of the following: {}'.format(
            ', '.join(allowed_formats)))
        return

    # Parameters for histogram
    # The maximum number of buckets to use when building a histogram; will be rounded up to a power of 2.
    max_buckets = None
    # The minimum histogram bucket width, or null to allow any power of 2.
    min_bucket_width = None
    # The number of values to accumulate before building the initial histogram.
    max_raw = None
    hist_min = 1.0  # The lower (inclusive) bound of the first bucket.
    hist_max = 100.0  # The upper (exclusive) bound of the last bucket.
    hist_steps = 10  # The number of buckets to use.

    if 'max_buckets' in kwargs.keys():
        max_buckets = kwargs['max_buckets']
    if 'min_bucket_width' in kwargs.keys():
        min_bucket_width = kwargs['min_bucket']
    if 'max_raw' in kwargs.keys():
        max_raw = kwargs['max_raw']

    if statistics_type.upper() == 'FIXED_HIST' and ('hist_min' in kwargs.keys()) and ('hist_max' in kwargs.keys()) and ('hist_steps' in kwargs.keys()):
        hist_min = kwargs['hist_min']
        hist_max = kwargs['hist_max']
        hist_steps = kwargs['hist_steps']
    elif statistics_type.upper() == 'FIXED_HIST':
        print('To use fixedHistogram, please provide these three parameters: hist_min, hist_max, and hist_steps.')
        return

    allowed_statistics = {
        'MEAN': ee.Reducer.mean(),
        'MAXIMUM': ee.Reducer.max(),
        'MEDIAN': ee.Reducer.median(),
        'MINIMUM': ee.Reducer.min(),
        'STD': ee.Reducer.stdDev(),
        'MIN_MAX': ee.Reducer.minMax(),
        'SUM': ee.Reducer.sum(),
        'VARIANCE': ee.Reducer.variance(),
        'HIST': ee.Reducer.histogram(maxBuckets=max_buckets, minBucketWidth=min_bucket_width, maxRaw=max_raw),
        'FIXED_HIST': ee.Reducer.fixedHistogram(hist_min, hist_max, hist_steps)
    }

    if not (statistics_type.upper() in allowed_statistics.keys()):
        print('The statistics type must be one of the following: {}'.format(
            ', '.join(list(allowed_statistics.keys()))))
        return

    if scale is None:
        scale = in_value_raster.projection().nominalScale().multiply(10)

    try:
        print('Computing statistics ...')
        result = in_value_raster.reduceRegions(
            collection=in_zone_vector, reducer=allowed_statistics[statistics_type], scale=scale, crs=crs, tileScale=tile_scale)
        ee_export_vector(result, filename)
    except Exception as e:
        print(e)


def zonal_statistics_by_group(in_value_raster, in_zone_vector, out_file_path, statistics_type='SUM', decimal_places=0, denominator=1.0, scale=None, crs=None, tile_scale=1.0):
    """Summarizes the area or percentage of a raster by group within the zones of another dataset and exports the results as a csv, shp, json, kml, or kmz.

    Args:
        in_value_raster (object): An integer Image that contains the values on which to calculate area/percentage.
        in_zone_vector (object): An ee.FeatureCollection that defines the zones.
        out_file_path (str): Output file path that will contain the summary of the values in each zone. The file type can be: csv, shp, json, kml, kmz
        statistics_type (str, optional): Can be either 'SUM' or 'PERCENTAGE' . Defaults to 'SUM'.
        decimal_places (int, optional): The number of decimal places to use. Defaults to 0.
        denominator (float, optional): To covert area units (e.g., from square meters to square kilometers). Defaults to 1.0.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
        crs (str, optional): The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale. Defaults to None.
        tile_scale (float, optional): A scaling factor used to reduce aggregation tile size; using a larger tileScale (e.g. 2 or 4) may enable computations that run out of memory with the default. Defaults to 1.0.

    """
    if not isinstance(in_value_raster, ee.Image):
        print('The input raster must be an ee.Image.')
        return

    band_count = in_value_raster.bandNames().size().getInfo()

    band_name = ''
    if band_count == 1:
        band_name = in_value_raster.bandNames().get(0)
    else:
        print('The input image can only have one band.')
        return

    band_types = in_value_raster.bandTypes().get(band_name).getInfo()
    band_type = band_types.get('precision')
    if band_type != 'int':
        print('The input image band must be integer type.')
        return

    if not isinstance(in_zone_vector, ee.FeatureCollection):
        print('The input zone data must be an ee.FeatureCollection.')
        return

    allowed_formats = ['csv', 'json', 'kml', 'kmz', 'shp']
    filename = os.path.abspath(out_file_path)
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:]

    if not (filetype.lower() in allowed_formats):
        print('The file type must be one of the following: {}'.format(
            ', '.join(allowed_formats)))
        return

    out_dir = os.path.dirname(filename)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    allowed_statistics = ['SUM', 'PERCENTAGE']
    if not (statistics_type.upper() in allowed_statistics):
        print('The statistics type can only be one of {}'.format(
            ', '.join(allowed_statistics)))
        return

    if scale is None:
        scale = in_value_raster.projection().nominalScale().multiply(10)

    try:

        print('Computing ... ')
        geometry = in_zone_vector.geometry()

        hist = in_value_raster.reduceRegion(ee.Reducer.frequencyHistogram(
        ), geometry=geometry, bestEffort=True, scale=scale)
        class_values = ee.Dictionary(hist.get(band_name)).keys().map(
            lambda v: ee.Number.parse(v)).sort()

        class_names = class_values.map(
            lambda c: ee.String('Class_').cat(ee.Number(c).format()))

        class_count = class_values.size().getInfo()
        dataset = ee.Image.pixelArea().divide(denominator).addBands(in_value_raster)

        init_result = dataset.reduceRegions(**{
            'collection': in_zone_vector,
            'reducer': ee.Reducer.sum().group(**{
                'groupField': 1,
                'groupName': 'group',
            }),
            'scale': scale
        })

        def build_dict(input_list):

            decimal_format = '%.{}f'.format(decimal_places)
            in_dict = input_list.map(lambda x: ee.Dictionary().set(ee.String('Class_').cat(
                ee.Number(ee.Dictionary(x).get('group')).format()), ee.Number.parse(ee.Number(ee.Dictionary(x).get('sum')).format(decimal_format))))
            return in_dict

        def get_keys(input_list):
            return input_list.map(lambda x: ee.String('Class_').cat(ee.Number(ee.Dictionary(x).get('group')).format()))

        def get_values(input_list):
            decimal_format = '%.{}f'.format(decimal_places)
            return input_list.map(lambda x: ee.Number.parse(ee.Number(ee.Dictionary(x).get('sum')).format(decimal_format)))

        def set_attribute(f):
            groups = ee.List(f.get('groups'))
            keys = get_keys(groups)
            values = get_values(groups)
            total_area = ee.List(values).reduce(ee.Reducer.sum())

            def get_class_values(x):
                cls_value = ee.Algorithms.If(
                    keys.contains(x), values.get(keys.indexOf(x)), 0)
                cls_value = ee.Algorithms.If(ee.String(statistics_type).compareTo(ee.String(
                    'SUM')), ee.Number(cls_value).divide(ee.Number(total_area)), cls_value)
                return cls_value

            full_values = class_names.map(lambda x: get_class_values(x))
            attr_dict = ee.Dictionary.fromLists(class_names, full_values)
            attr_dict = attr_dict.set('Class_sum', total_area)

            return f.set(attr_dict).set('groups', None)

        final_result = init_result.map(set_attribute)
        ee_export_vector(final_result, filename)

    except Exception as e:
        print(e)


def create_colorbar(width=150, height=30, palette=['blue', 'green', 'red'], add_ticks=True, add_labels=True, labels=None, vertical=False, out_file=None, font_type='arial.ttf', font_size=12, font_color='black', add_outline=True, outline_color='black'):
    """Creates a colorbar based on the provided palette.

    Args:
        width (int, optional): Width of the colorbar in pixels. Defaults to 150.
        height (int, optional): Height of the colorbar in pixels. Defaults to 30.
        palette (list, optional): Palette for the colorbar. Each color can be provided as a string (e.g., 'red'), a hex string (e.g., '#ff0000'), or an RGB tuple (255, 0, 255). Defaults to ['blue', 'green', 'red'].
        add_ticks (bool, optional): Whether to add tick markers to the colorbar. Defaults to True.
        add_labels (bool, optional): Whether to add labels to the colorbar. Defaults to True.
        labels (list, optional): A list of labels to add to the colorbar. Defaults to None.
        vertical (bool, optional): Whether to rotate the colorbar vertically. Defaults to False.
        out_file (str, optional): File path to the output colorbar in png format. Defaults to None.
        font_type (str, optional): Font type to use for labels. Defaults to 'arial.ttf'.
        font_size (int, optional): Font size to use for labels. Defaults to 12.
        font_color (str, optional): Font color to use for labels. Defaults to 'black'.
        add_outline (bool, optional): Whether to add an outline to the colorbar. Defaults to True.
        outline_color (str, optional): Color for the outline of the colorbar. Defaults to 'black'.

    Returns:
        str: File path of the output colorbar in png format.

    """
    import decimal
    import io
    import pkg_resources
    import warnings
    from colour import Color
    from PIL import Image, ImageDraw, ImageFont

    warnings.simplefilter('ignore')
    pkg_dir = os.path.dirname(
        pkg_resources.resource_filename("geemap", "geemap.py"))

    if out_file is None:
        filename = 'colorbar_' + random_string() + '.png'
        out_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        out_file = os.path.join(out_dir, filename)
    elif not out_file.endswith('.png'):
        print('The output file must end with .png')
        return
    else:
        out_file = os.path.abspath(out_file)

    if not os.path.exists(os.path.dirname(out_file)):
        os.makedirs(os.path.dirname(out_file))

    im = Image.new('RGBA', (width, height))
    ld = im.load()

    def float_range(start, stop, step):
        while start < stop:
            yield float(start)
            start += decimal.Decimal(step)

    n_colors = len(palette)
    decimal_places = 2
    rgb_colors = [Color(check_color(c)).rgb for c in palette]
    keys = [round(c, decimal_places)
            for c in list(float_range(0, 1.0001, 1.0/(n_colors - 1)))]

    heatmap = []
    for index, item in enumerate(keys):
        pair = [item, rgb_colors[index]]
        heatmap.append(pair)

    def gaussian(x, a, b, c, d=0):
        return a * math.exp(-(x - b)**2 / (2 * c**2)) + d

    def pixel(x, width=100, map=[], spread=1):
        width = float(width)
        r = sum([gaussian(x, p[1][0], p[0] * width, width/(spread*len(map)))
                 for p in map])
        g = sum([gaussian(x, p[1][1], p[0] * width, width/(spread*len(map)))
                 for p in map])
        b = sum([gaussian(x, p[1][2], p[0] * width, width/(spread*len(map)))
                 for p in map])
        return min(1.0, r), min(1.0, g), min(1.0, b)

    for x in range(im.size[0]):
        r, g, b = pixel(x, width=width, map=heatmap)
        r, g, b = [int(256*v) for v in (r, g, b)]
        for y in range(im.size[1]):
            ld[x, y] = r, g, b

    if add_outline:
        draw = ImageDraw.Draw(im)
        draw.rectangle([(0, 0), (width-1, height-1)],
                       outline=check_color(outline_color))
        del draw

    if add_ticks:
        tick_length = height * 0.1
        x = [key * width for key in keys]
        y_top = height - tick_length
        y_bottom = height
        draw = ImageDraw.Draw(im)
        for i in x:
            shape = [(i, y_top), (i, y_bottom)]
            draw.line(shape, fill='black', width=0)
        del draw

    if vertical:
        im = im.transpose(Image.ROTATE_90)

    width, height = im.size

    if labels is None:
        labels = [str(c) for c in keys]
    elif len(labels) == 2:
        try:
            lowerbound = float(labels[0])
            upperbound = float(labels[1])
            step = (upperbound - lowerbound) / (len(palette) - 1)
            labels = [str(lowerbound + c * step)
                      for c in range(0, len(palette))]
        except Exception as e:
            print(e)
            print('The labels are invalid.')
            return
    elif len(labels) == len(palette):
        labels = [str(c) for c in labels]
    else:
        print('The labels must have the same length as the palette.')
        return

    if add_labels:

        default_font = os.path.join(pkg_dir, 'data/fonts/arial.ttf')
        if font_type == 'arial.ttf':
            font = ImageFont.truetype(default_font, font_size)
        else:
            try:
                font_list = system_fonts(show_full_path=True)
                font_names = [os.path.basename(f) for f in font_list]
                if (font_type in font_list) or (font_type in font_names):
                    font = ImageFont.truetype(font_type, font_size)
                else:
                    print(
                        'The specified font type could not be found on your system. Using the default font instead.')
                    font = ImageFont.truetype(default_font, font_size)
            except Exception as e:
                print(e)
                font = ImageFont.truetype(default_font, font_size)

        font_color = check_color(font_color)

        draw = ImageDraw.Draw(im)
        w, h = draw.textsize(labels[0], font=font)

        for label in labels:
            w_tmp, h_tmp = draw.textsize(label, font)
            if w_tmp > w:
                w = w_tmp
            if h_tmp > h:
                h = h_tmp

        W, H = width + w * 2, height + h * 2
        background = Image.new('RGBA', (W, H))
        draw = ImageDraw.Draw(background)

        if vertical:
            xy = (0, h)
        else:
            xy = (w, 0)
        background.paste(im, xy, im)

        for index, label in enumerate(labels):

            w_tmp, h_tmp = draw.textsize(label, font)

            if vertical:
                spacing = 5
                x = width + spacing
                y = int(height + h - keys[index] * height - h_tmp / 2 - 1)
                draw.text((x, y), label, font=font, fill=font_color)

            else:
                x = int(keys[index] * width + w - w_tmp / 2)
                spacing = int(h * 0.05)
                y = height + spacing
                draw.text((x, y), label, font=font, fill=font_color)

        im = background.copy()

    im.save(out_file)
    return out_file


def naip_timeseries(roi=None, start_year=2009, end_year=2018):
    """Creates NAIP annual timeseries

    Args:
        roi (object, optional): An ee.Geometry representing the region of interest. Defaults to None.
        start_year (int, optional): Starting year for the timeseries. Defaults to2009.
        end_year (int, optional): Ending year for the timeseries. Defaults to 2018.

    Returns:
        object: An ee.ImageCollection representing annual NAIP imagery.
    """
    # ee_initialize()
    try:

        def get_annual_NAIP(year):
            try:
                collection = ee.ImageCollection('USDA/NAIP/DOQQ')
                if roi is not None:
                    collection = collection.filterBounds(roi)
                start_date = ee.Date.fromYMD(year, 1, 1)
                end_date = ee.Date.fromYMD(year, 12, 31)
                naip = collection.filterDate(start_date, end_date) \
                    .filter(ee.Filter.listContains("system:band_names", "N"))
                naip = ee.Image(ee.ImageCollection(naip).mosaic())
                return naip
            except Exception as e:
                print(e)

        years = ee.List.sequence(start_year, end_year)
        collection = years.map(get_annual_NAIP)
        return collection

    except Exception as e:
        print(e)


def sentinel2_timeseries(roi=None, start_year=2015, end_year=2019, start_date='01-01', end_date='12-31'):
    """Generates an annual Sentinel 2 ImageCollection. This algorithm is adapted from https://gist.github.com/jdbcode/76b9ac49faf51627ebd3ff988e10adbc. A huge thank you to Justin Braaten for sharing his fantastic work.
       Images include both level 1C and level 2A imagery.
    Args:

        roi (object, optional): Region of interest to create the timelapse. Defaults to None.
        start_year (int, optional): Starting year for the timelapse. Defaults to 2015.
        end_year (int, optional): Ending year for the timelapse. Defaults to 2019.
        start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '01-01'.
        end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '12-31'.
    Returns:
        object: Returns an ImageCollection containing annual Sentinel 2 images.
    """
    ################################################################################

    ################################################################################
    # Input and output parameters.
    import re
    import datetime

    # ee_initialize()

    if roi is None:
        # roi = ee.Geometry.Polygon(
        #     [[[-180, -80],
        #       [-180, 80],
        #         [180, 80],
        #         [180, -80],
        #         [-180, -80]]], None, False)
        roi = ee.Geometry.Polygon(
            [[[-115.471773, 35.892718],
              [-115.471773, 36.409454],
                [-114.271283, 36.409454],
                [-114.271283, 35.892718],
                [-115.471773, 35.892718]]], None, False)

    if not isinstance(roi, ee.Geometry):

        try:
            roi = roi.geometry()
        except Exception as e:
            print('Could not convert the provided roi to ee.Geometry')
            print(e)
            return

    # Adjusts longitudes less than -180 degrees or greater than 180 degrees.
    geojson = ee_to_geojson(roi)
    geojson = adjust_longitude(geojson)
    roi = ee.Geometry(geojson)

    ################################################################################
    # Setup vars to get dates.
    if isinstance(start_year, int) and (start_year >= 2015) and (start_year <= 2020):
        pass
    else:
        print('The start year must be an integer >= 2015.')
        return

    if isinstance(end_year, int) and (end_year >= 2015) and (end_year <= 2020):
        pass
    else:
        print('The end year must be an integer <= 2020.')
        return

    if re.match("[0-9]{2}\-[0-9]{2}", start_date) and re.match("[0-9]{2}\-[0-9]{2}", end_date):
        pass
    else:
        print('The start data and end date must be month-day, such as 06-10, 09-20')
        return

    try:
        datetime.datetime(int(start_year), int(
            start_date[:2]), int(start_date[3:5]))
        datetime.datetime(int(end_year), int(end_date[:2]), int(end_date[3:5]))
    except Exception as e:
        print('The input dates are invalid.')
        print(e)
        return

    try:
        start_test = datetime.datetime(int(start_year), int(
            start_date[:2]), int(start_date[3:5]))
        end_test = datetime.datetime(
            int(end_year), int(end_date[:2]), int(end_date[3:5]))
        if start_test > end_test:
            raise ValueError('Start date must be prior to end date')
    except Exception as e:
        print(e)
        return

    def days_between(d1, d2):
        d1 = datetime.datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)

    n_days = days_between(str(start_year) + '-' + start_date,
                          str(start_year) + '-' + end_date)
    start_month = int(start_date[:2])
    start_day = int(start_date[3:5])
    start_date = str(start_year) + '-' + start_date
    end_date = str(end_year) + '-' + end_date

    # Define a collection filter by date, bounds, and quality.
    def colFilter(col, aoi):  # , startDate, endDate):
        return(col.filterBounds(aoi))

    # Get Sentinel 2 collections, both Level-1C (top of atmophere) and Level-2A (surface reflectance)
    MSILCcol = ee.ImageCollection('COPERNICUS/S2')
    MSI2Acol = ee.ImageCollection('COPERNICUS/S2_SR')

    # Define a collection filter by date, bounds, and quality.
    def colFilter(col, roi, start_date, end_date):
        return(col
               .filterBounds(roi)
               .filterDate(start_date, end_date))
        # .filter('CLOUD_COVER < 5')
        # .filter('GEOMETRIC_RMSE_MODEL < 15')
        # .filter('IMAGE_QUALITY == 9 || IMAGE_QUALITY_OLI == 9'))

    # Function to get and rename bands of interest from MSI
    def renameMSI(img):
        return(img.select(
            ['B2', 'B3', 'B4', 'B5', 'B6', 'B7',
                'B8', 'B8A', 'B11', 'B12', 'QA60'],
            ['Blue', 'Green', 'Red', 'Red Edge 1', 'Red Edge 2', 'Red Edge 3', 'NIR', 'Red Edge 4', 'SWIR1', 'SWIR2', 'QA60']))

    # Add NBR for LandTrendr segmentation.

    def calcNbr(img):
        return(img.addBands(img.normalizedDifference(['NIR', 'SWIR2'])
                            .multiply(-10000).rename('NBR')).int16())

    # Define function to mask out clouds and cloud shadows in images.
    # Use CFmask band included in USGS Landsat SR image product.

    def fmask(img):
        cloudOpaqueBitMask = 1 << 10
        cloudCirrusBitMask = 1 << 11
        qa = img.select('QA60')
        mask = qa.bitwiseAnd(cloudOpaqueBitMask).eq(0) \
            .And(qa.bitwiseAnd(cloudCirrusBitMask).eq(0))
        return(img.updateMask(mask))

    # Define function to prepare MSI images.
    def prepMSI(img):
        orig = img
        img = renameMSI(img)
        img = fmask(img)
        return(ee.Image(img.copyProperties(orig, orig.propertyNames()))
               .resample('bicubic'))

    # Get annual median collection.
    def getAnnualComp(y):
        startDate = ee.Date.fromYMD(
            ee.Number(y), ee.Number(start_month), ee.Number(start_day))
        endDate = startDate.advance(ee.Number(n_days), 'day')

        # Filter collections and prepare them for merging.
        MSILCcoly = colFilter(MSILCcol, roi, startDate, endDate).map(prepMSI)
        MSI2Acoly = colFilter(MSI2Acol, roi, startDate, endDate).map(prepMSI)

        # Merge the collections.
        col = MSILCcoly.merge(MSI2Acoly)

        yearImg = col.median()
        nBands = yearImg.bandNames().size()
        yearImg = ee.Image(ee.Algorithms.If(
            nBands,
            yearImg,
            dummyImg))
        return(calcNbr(yearImg)
               .set({'year': y, 'system:time_start': startDate.millis(), 'nBands': nBands}))

    ################################################################################

    # Make a dummy image for missing years.
    bandNames = ee.List(['Blue', 'Green', 'Red', 'Red Edge 1',
                         'Red Edge 2', 'Red Edge 3', 'NIR',
                         'Red Edge 4', 'SWIR1', 'SWIR2', 'QA60'])
    fillerValues = ee.List.repeat(0, bandNames.size())
    dummyImg = ee.Image.constant(fillerValues).rename(bandNames) \
        .selfMask().int16()

    ################################################################################
    # Get a list of years
    years = ee.List.sequence(start_year, end_year)

    ################################################################################
    # Make list of annual image composites.
    imgList = years.map(getAnnualComp)

    # Convert image composite list to collection
    imgCol = ee.ImageCollection.fromImages(imgList)

    imgCol = imgCol.map(lambda img: img.clip(roi))

    return imgCol


def landsat_timeseries(roi=None, start_year=1984, end_year=2020, start_date='06-10', end_date='09-20', apply_fmask=True):
    """Generates an annual Landsat ImageCollection. This algorithm is adapted from https://gist.github.com/jdbcode/76b9ac49faf51627ebd3ff988e10adbc. A huge thank you to Justin Braaten for sharing his fantastic work.

    Args:
        roi (object, optional): Region of interest to create the timelapse. Defaults to None.
        start_year (int, optional): Starting year for the timelapse. Defaults to 1984.
        end_year (int, optional): Ending year for the timelapse. Defaults to 2020.
        start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '06-10'.
        end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '09-20'.
        apply_fmask (bool, optional): Whether to apply Fmask (Function of mask) for automated clouds, cloud shadows, snow, and water masking.
    Returns:
        object: Returns an ImageCollection containing annual Landsat images.
    """

    ################################################################################
    # Input and output parameters.
    import re
    import datetime

    if roi is None:
        roi = ee.Geometry.Polygon(
            [[[-115.471773, 35.892718],
              [-115.471773, 36.409454],
                [-114.271283, 36.409454],
                [-114.271283, 35.892718],
                [-115.471773, 35.892718]]], None, False)

    if not isinstance(roi, ee.Geometry):

        try:
            roi = roi.geometry()
        except Exception as e:
            print('Could not convert the provided roi to ee.Geometry')
            print(e)
            return

    ################################################################################

    # Setup vars to get dates.
    if isinstance(start_year, int) and (start_year >= 1984) and (start_year < 2020):
        pass
    else:
        print('The start year must be an integer >= 1984.')
        return

    if isinstance(end_year, int) and (end_year > 1984) and (end_year <= 2020):
        pass
    else:
        print('The end year must be an integer <= 2020.')
        return

    if re.match("[0-9]{2}\-[0-9]{2}", start_date) and re.match("[0-9]{2}\-[0-9]{2}", end_date):
        pass
    else:
        print('The start date and end date must be month-day, such as 06-10, 09-20')
        return

    try:
        datetime.datetime(int(start_year), int(
            start_date[:2]), int(start_date[3:5]))
        datetime.datetime(int(end_year), int(end_date[:2]), int(end_date[3:5]))
    except Exception as e:
        print('The input dates are invalid.')
        return

    def days_between(d1, d2):
        d1 = datetime.datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)

    n_days = days_between(str(start_year) + '-' + start_date,
                          str(start_year) + '-' + end_date)
    start_month = int(start_date[:2])
    start_day = int(start_date[3:5])
    start_date = str(start_year) + '-' + start_date
    end_date = str(end_year) + '-' + end_date

    # Define a collection filter by date, bounds, and quality.
    def colFilter(col, aoi):  # , startDate, endDate):
        return(col.filterBounds(aoi))

    # Landsat collection preprocessingEnabled
    # Get Landsat surface reflectance collections for OLI, ETM+ and TM sensors.
    LC08col = ee.ImageCollection('LANDSAT/LC08/C01/T1_SR')
    LE07col = ee.ImageCollection('LANDSAT/LE07/C01/T1_SR')
    LT05col = ee.ImageCollection('LANDSAT/LT05/C01/T1_SR')
    LT04col = ee.ImageCollection('LANDSAT/LT04/C01/T1_SR')

    # Define a collection filter by date, bounds, and quality.
    def colFilter(col, roi, start_date, end_date):
        return(col
               .filterBounds(roi)
               .filterDate(start_date, end_date))
        # .filter('CLOUD_COVER < 5')
        # .filter('GEOMETRIC_RMSE_MODEL < 15')
        # .filter('IMAGE_QUALITY == 9 || IMAGE_QUALITY_OLI == 9'))

    # Function to get and rename bands of interest from OLI.
    def renameOli(img):
        return(img.select(
            ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'pixel_qa'],
            ['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2', 'pixel_qa']))

    # Function to get and rename bands of interest from ETM+.
    def renameEtm(img):
        return(img.select(
            ['B1', 'B2', 'B3', 'B4', 'B5', 'B7', 'pixel_qa'],
            ['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2', 'pixel_qa']))

    # Add NBR for LandTrendr segmentation.
    def calcNbr(img):
        return(img.addBands(img.normalizedDifference(['NIR', 'SWIR2'])
                            .multiply(-10000).rename('NBR')).int16())

    # Define function to mask out clouds and cloud shadows in images.
    # Use CFmask band included in USGS Landsat SR image product.
    def fmask(img):
        cloudShadowBitMask = 1 << 3
        cloudsBitMask = 1 << 5
        qa = img.select('pixel_qa')
        mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0) \
            .And(qa.bitwiseAnd(cloudsBitMask).eq(0))
        return(img.updateMask(mask))

    # Define function to prepare OLI images.
    def prepOli(img):
        orig = img
        img = renameOli(img)
        if apply_fmask:
            img = fmask(img)
        return (ee.Image(img.copyProperties(orig, orig.propertyNames()))
                .resample('bicubic'))

    # Define function to prepare ETM+ images.
    def prepEtm(img):
        orig = img
        img = renameEtm(img)
        if apply_fmask:
            img = fmask(img)
        return(ee.Image(img.copyProperties(orig, orig.propertyNames()))
               .resample('bicubic'))

    # Get annual median collection.
    def getAnnualComp(y):
        startDate = ee.Date.fromYMD(
            ee.Number(y), ee.Number(start_month), ee.Number(start_day))
        endDate = startDate.advance(ee.Number(n_days), 'day')

        # Filter collections and prepare them for merging.
        LC08coly = colFilter(LC08col, roi, startDate, endDate).map(prepOli)
        LE07coly = colFilter(LE07col, roi, startDate, endDate).map(prepEtm)
        LT05coly = colFilter(LT05col, roi, startDate, endDate).map(prepEtm)
        LT04coly = colFilter(LT04col, roi, startDate, endDate).map(prepEtm)

        # Merge the collections.
        col = LC08coly.merge(LE07coly).merge(LT05coly).merge(LT04coly)

        yearImg = col.median()
        nBands = yearImg.bandNames().size()
        yearImg = ee.Image(ee.Algorithms.If(
            nBands,
            yearImg,
            dummyImg))
        return(calcNbr(yearImg)
               .set({'year': y, 'system:time_start': startDate.millis(), 'nBands': nBands}))

    ################################################################################

    # Make a dummy image for missing years.
    bandNames = ee.List(['Blue', 'Green', 'Red', 'NIR',
                         'SWIR1', 'SWIR2', 'pixel_qa'])
    fillerValues = ee.List.repeat(0, bandNames.size())
    dummyImg = ee.Image.constant(fillerValues).rename(bandNames) \
        .selfMask().int16()

    ################################################################################
    # Get a list of years
    years = ee.List.sequence(start_year, end_year)

    ################################################################################
    # Make list of annual image composites.
    imgList = years.map(getAnnualComp)

    # Convert image composite list to collection
    imgCol = ee.ImageCollection.fromImages(imgList)

    imgCol = imgCol.map(lambda img: img.clip(
        roi).set({'coordinates': roi.coordinates()}))

    return imgCol

    # ################################################################################
    # # Run LandTrendr.
    # lt = ee.Algorithms.TemporalSegmentation.LandTrendr(
    #     timeSeries=imgCol.select(['NBR', 'SWIR1', 'NIR', 'Green']),
    #     maxSegments=10,
    #     spikeThreshold=0.7,
    #     vertexCountOvershoot=3,
    #     preventOneYearRecovery=True,
    #     recoveryThreshold=0.5,
    #     pvalThreshold=0.05,
    #     bestModelProportion=0.75,
    #     minObservationsNeeded=6)

    # ################################################################################
    # # Get fitted imagery. This starts export tasks.
    # def getYearStr(year):
    #     return(ee.String('yr_').cat(ee.Algorithms.String(year).slice(0,4)))

    # yearsStr = years.map(getYearStr)

    # r = lt.select(['SWIR1_fit']).arrayFlatten([yearsStr]).toShort()
    # g = lt.select(['NIR_fit']).arrayFlatten([yearsStr]).toShort()
    # b = lt.select(['Green_fit']).arrayFlatten([yearsStr]).toShort()

    # for i, c in zip([r, g, b], ['r', 'g', 'b']):
    #     descr = 'mamore-river-'+c
    #     name = 'users/user/'+descr
    #     print(name)
    #     task = ee.batch.Export.image.toAsset(
    #     image=i,
    #     region=roi.getInfo()['coordinates'],
    #     assetId=name,
    #     description=descr,
    #     scale=30,
    #     crs='EPSG:3857',
    #     maxPixels=1e13)
    #     task.start()


def landsat_ts_gif(roi=None, out_gif=None, start_year=1984, end_year=2019, start_date='06-10', end_date='09-20', bands=['NIR', 'Red', 'Green'], vis_params=None, dimensions=768, frames_per_second=10, apply_fmask=True, nd_bands=None, nd_threshold=0, nd_palette=['black', 'blue']):
    """Generates a Landsat timelapse GIF image. This function is adapted from https://emaprlab.users.earthengine.app/view/lt-gee-time-series-animator. A huge thank you to Justin Braaten for sharing his fantastic work.

    Args:
        roi (object, optional): Region of interest to create the timelapse. Defaults to None.
        out_gif (str, optional): File path to the output animated GIF. Defaults to None.
        start_year (int, optional): Starting year for the timelapse. Defaults to 1984.
        end_year (int, optional): Ending year for the timelapse. Defaults to 2019.
        start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '06-10'.
        end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '09-20'.
        bands (list, optional): Three bands selected from ['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2', 'pixel_qa']. Defaults to ['NIR', 'Red', 'Green'].
        vis_params (dict, optional): Visualization parameters. Defaults to None.
        dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 10.
        apply_fmask (bool, optional): Whether to apply Fmask (Function of mask) for automated clouds, cloud shadows, snow, and water masking.
        nd_bands (list, optional): A list of names specifying the bands to use, e.g., ['Green', 'SWIR1']. The normalized difference is computed as (first − second) / (first + second). Note that negative input values are forced to 0 so that the result is confined to the range (-1, 1).  
        nd_threshold (float, optional): The threshold for extacting pixels from the normalized difference band. 
        nd_palette (list, optional): The color palette to use for displaying the normalized difference band. 

    Returns:
        str: File path to the output GIF image.
    """

    # ee_initialize()

    if roi is None:
        roi = ee.Geometry.Polygon(
            [[[-115.471773, 35.892718],
              [-115.471773, 36.409454],
                [-114.271283, 36.409454],
                [-114.271283, 35.892718],
                [-115.471773, 35.892718]]], None, False)
    elif isinstance(roi, ee.Feature) or isinstance(roi, ee.FeatureCollection):
        roi = roi.geometry()
    elif isinstance(roi, ee.Geometry):
        pass
    else:
        print('The provided roi is invalid. It must be an ee.Geometry')
        return

    if out_gif is None:
        out_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        filename = 'landsat_ts_' + random_string() + '.gif'
        out_gif = os.path.join(out_dir, filename)
    elif not out_gif.endswith('.gif'):
        print('The output file must end with .gif')
        return
    # elif not os.path.isfile(out_gif):
    #     print('The output file must be a file')
    #     return
    else:
        out_gif = os.path.abspath(out_gif)
        out_dir = os.path.dirname(out_gif)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    allowed_bands = ['Blue', 'Green', 'Red',
                     'NIR', 'SWIR1', 'SWIR2', 'pixel_qa']

    if len(bands) == 3 and all(x in allowed_bands for x in bands):
        pass
    else:
        raise Exception('You can only select 3 bands from the following: {}'.format(
            ', '.join(allowed_bands)))

    if nd_bands is not None:
        if len(nd_bands) == 2 and all(x in allowed_bands[:-1] for x in nd_bands):
            pass
        else:
            raise Exception('You can only select two bands from the following: {}'.format(
                ', '.join(allowed_bands[:-1])))

    try:
        col = landsat_timeseries(
            roi, start_year, end_year, start_date, end_date, apply_fmask)

        if vis_params is None:
            vis_params = {}
            vis_params['bands'] = bands
            vis_params['min'] = 0
            vis_params['max'] = 4000
            vis_params['gamma'] = [1, 1, 1]

        video_args = vis_params.copy()
        video_args['dimensions'] = dimensions
        video_args['region'] = roi
        video_args['framesPerSecond'] = frames_per_second
        video_args['crs'] = 'EPSG:3857'

        if 'bands' not in video_args.keys():
            video_args['bands'] = bands

        if 'min' not in video_args.keys():
            video_args['min'] = 0

        if 'max' not in video_args.keys():
            video_args['max'] = 4000

        if 'gamma' not in video_args.keys():
            video_args['gamma'] = [1, 1, 1]

        download_ee_video(col, video_args, out_gif)

        if nd_bands is not None:
            nd_images = landsat_ts_norm_diff(
                col, bands=nd_bands, threshold=nd_threshold)
            out_nd_gif = out_gif.replace('.gif', '_nd.gif')
            landsat_ts_norm_diff_gif(nd_images, out_gif=out_nd_gif, vis_params=None,
                                     palette=nd_palette, dimensions=dimensions, frames_per_second=frames_per_second)

        return out_gif

    except Exception as e:
        print(e)


def minimum_bounding_box(geojson):
    """Gets the minimum bounding box for a geojson polygon.

    Args:
        geojson (dict): A geojson dictionary.

    Returns:
        tuple: Returns a tuple containing the minimum bounding box in the format of (lower_left(lat, lon), upper_right(lat, lon)), such as ((13, -130), (32, -120)).
    """
    coordinates = []
    try:
        if 'geometry' in geojson.keys():
            coordinates = geojson['geometry']['coordinates'][0]
        else:
            coordinates = geojson['coordinates'][0]

        lower_left = min([x[1] for x in coordinates]), min(
            [x[0] for x in coordinates])  # (lat, lon)
        upper_right = max([x[1] for x in coordinates]), max([x[0]
                                                             for x in coordinates])  # (lat, lon)
        bounds = (lower_left, upper_right)
        return bounds
    except Exception as e:
        # print(e)
        return None


def geocode(location, max_rows=10, reverse=False):
    """Search location by address and lat/lon coordinates.

    Args:
        location (str): Place name or address
        max_rows (int, optional): Maximum number of records to return. Defaults to 10.
        reverse (bool, optional): Search place based on coordinates. Defaults to False.

    Returns:
        list: Returns a list of locations.
    """
    if not isinstance(location, str):
        print('The location must be a string.')
        return None

    if not reverse:

        locations = []
        addresses = set()
        g = geocoder.arcgis(location, maxRows=max_rows)

        for result in g:
            address = result.address
            if not address in addresses:
                addresses.add(address)
                locations.append(result)

        if len(locations) > 0:
            return locations
        else:
            return None

    else:
        try:
            if ',' in location:
                latlon = [float(x) for x in location.split(',')]
            elif ' ' in location:
                latlon = [float(x) for x in location.split(' ')]
            else:
                print(
                    'The lat-lon coordinates should be numbers only and separated by comma or space, such as 40.2, -100.3')
                return
            g = geocoder.arcgis(latlon, method='reverse')
            locations = []
            addresses = set()

            for result in g:
                address = result.address
                if not address in addresses:
                    addresses.add(address)
                    locations.append(result)

            if len(locations) > 0:
                return locations
            else:
                return None

        except Exception as e:
            print(e)
            return None


def is_latlon_valid(location):
    """Checks whether a pair of coordinates is valid.

    Args:
        location (str): A pair of latlon coordinates separated by comma or space.

    Returns:
        bool: Returns True if valid.
    """
    latlon = []
    if ',' in location:
        latlon = [float(x) for x in location.split(',')]
    elif ' ' in location:
        latlon = [float(x) for x in location.split(' ')]
    else:
        print(
            'The coordinates should be numbers only and separated by comma or space, such as 40.2, -100.3')
        return False

    try:
        lat, lon = float(latlon[0]), float(latlon[1])
        if lat >= -90 and lat <= 90 and lon >= -180 and lat <= 180:
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


def latlon_from_text(location):
    """Extracts latlon from text.

    Args:
        location (str): A pair of latlon coordinates separated by comma or space.

    Returns:
        bool: Returns (lat, lon) if valid.
    """
    latlon = []
    try:
        if ',' in location:
            latlon = [float(x) for x in location.split(',')]
        elif ' ' in location:
            latlon = [float(x) for x in location.split(' ')]
        else:
            print(
                'The lat-lon coordinates should be numbers only and separated by comma or space, such as 40.2, -100.3')
            return None

        lat, lon = latlon[0], latlon[1]
        if lat >= -90 and lat <= 90 and lon >= -180 and lat <= 180:
            return lat, lon
        else:
            return None

    except Exception as e:
        print(e)
        print('The lat-lon coordinates should be numbers only and separated by comma or space, such as 40.2, -100.3')
        return None


def search_ee_data(keywords):
    """Searches Earth Engine data catalog.

    Args:
        keywords (str): Keywords to search for can be id, provider, tag and so on

    Returns:
        list: Returns a lit of assets.
    """
    try:
        cmd = 'geeadd search --keywords "{}"'.format(str(keywords))
        output = os.popen(cmd).read()
        start_index = output.index('[')
        assets = eval(output[start_index:])

        results = []
        for asset in assets:
            asset_dates = asset['start_date'] + ' - ' + asset['end_date']
            asset_snippet = asset['ee_id_snippet']
            start_index = asset_snippet.index("'") + 1
            end_index = asset_snippet.index("'", start_index)
            asset_id = asset_snippet[start_index:end_index]

            asset['dates'] = asset_dates
            asset['id'] = asset_id
            asset['uid'] = asset_id.replace('/', '_')
            # asset['url'] = 'https://developers.google.com/earth-engine/datasets/catalog/' + asset['uid']
            # asset['thumbnail'] = 'https://mw1.google.com/ges/dd/images/{}_sample.png'.format(
            #     asset['uid'])
            results.append(asset)

        return results

    except Exception as e:
        print(e)
        

def ee_data_thumbnail(asset_id):
    """Retrieves the thumbnail URL of an Earth Engine asset.

    Args:
        asset_id (str): An Earth Engine asset id.

    Returns:
        str: An http url of the thumbnail.
    """
    import requests
    import urllib
    from bs4 import BeautifulSoup

    asset_uid = asset_id.replace('/', '_')
    asset_url = "https://developers.google.com/earth-engine/datasets/catalog/{}".format(
        asset_uid)
    thumbnail_url = 'https://mw1.google.com/ges/dd/images/{}_sample.png'.format(
        asset_uid)

    r = requests.get(thumbnail_url)

    try:
        if r.status_code != 200:
            html_page = urllib.request.urlopen(asset_url)
            soup = BeautifulSoup(html_page, features="html.parser")

            for img in soup.findAll('img'):
                if 'sample.png' in img.get('src'):
                    thumbnail_url = img.get('src')
                    return thumbnail_url

        return thumbnail_url
    except Exception as e:
        print(e)


def ee_data_html(asset):
    """Generates HTML from an asset to be used in the HTML widget.

    Args:
        asset (dict): A dictionary containing an Earth Engine asset.

    Returns:
        str: A string containing HTML.
    """
    template = '''
        <html>
        <body>
            <h3>asset_title</h3>
            <h4>Dataset Availability</h4>
                <p style="margin-left: 40px">asset_dates</p>
            <h4>Earth Engine Snippet</h4>
                <p style="margin-left: 40px">ee_id_snippet</p>
            <h4>Earth Engine Data Catalog</h4>
                <p style="margin-left: 40px"><a href="asset_url" target="_blank">asset_id</a></p>
            <h4>Dataset Thumbnail</h4>
                <img src="thumbnail_url">
        </body>
        </html>
    '''

    try:

        text = template.replace('asset_title', asset['title'])
        text = text.replace('asset_dates', asset['dates'])
        text = text.replace('ee_id_snippet', asset['ee_id_snippet'])
        text = text.replace('asset_id', asset['id'])
        text = text.replace('asset_url', asset['asset_url'])
        # asset['thumbnail'] = ee_data_thumbnail(asset['id'])
        text = text.replace('thumbnail_url', asset['thumbnail_url'])

        return text

    except Exception as e:
        print(e)


def create_code_cell(code='', where='below'):
    """Creates a code cell in the IPython Notebook.

    Args:
        code (str, optional): Code to fill the new code cell with. Defaults to ''.
        where (str, optional): Where to add the new code cell. It can be one of the following: above, below, at_bottom. Defaults to 'below'.
    """

    import base64
    from IPython.display import Javascript, display
    encoded_code = (base64.b64encode(str.encode(code))).decode()
    display(Javascript("""
        var code = IPython.notebook.insert_cell_{0}('code');
        code.set_text(atob("{1}"));
    """.format(where, encoded_code)))


def ee_api_to_csv(outfile=None):
    """Extracts Earth Engine API documentation from https://developers.google.com/earth-engine/api_docs as a csv file.

    Args:
        outfile (str, optional): The output file path to a csv file. Defaults to None.
    """
    import csv
    import requests
    from bs4 import BeautifulSoup

    pkg_dir = os.path.dirname(
        pkg_resources.resource_filename("geemap", "geemap.py"))
    data_dir = os.path.join(pkg_dir, 'data')
    template_dir = os.path.join(data_dir, 'template')
    csv_file = os.path.join(template_dir, 'ee_api_docs.csv')

    if outfile is None:
        outfile = csv_file
    else:
        if not outfile.endswith('.csv'):
            print('The output file must end with .csv')
            return
        else:
            out_dir = os.path.dirname(outfile)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)

    url = 'https://developers.google.com/earth-engine/api_docs'

    try:

        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')

        names = []
        descriptions = []
        functions = []
        returns = []
        arguments = []
        types = []
        details = []

        names = [h2.text for h2 in soup.find_all('h2')]
        descriptions = [
            h2.next_sibling.next_sibling.text for h2 in soup.find_all('h2')]
        func_tables = soup.find_all('table', class_='blue')
        functions = [func_table.find(
            'code').text for func_table in func_tables]
        returns = [func_table.find_all(
            'td')[1].text for func_table in func_tables]

        detail_tables = []
        tables = soup.find_all('table', class_='blue')

        for table in tables:
            item = table.next_sibling
            if item.attrs == {'class': ['details']}:
                detail_tables.append(item)
            else:
                detail_tables.append("")

        for detail_table in detail_tables:
            if detail_table != '':
                items = [item.text for item in detail_table.find_all('code')]
            else:
                items = ""
            arguments.append(items)

        for detail_table in detail_tables:
            if detail_table != '':
                items = [item.text for item in detail_table.find_all('td')]
                items = items[1::3]
            else:
                items = ""
            types.append(items)

        for detail_table in detail_tables:
            if detail_table != '':
                items = [item.text for item in detail_table.find_all('p')]
            else:
                items = ""
            details.append(items)

        csv_file = open(outfile, 'w', encoding='utf-8')
        csv_writer = csv.writer(csv_file, delimiter='\t')

        csv_writer.writerow(
            ['name', 'description', 'function', 'returns', 'argument', 'type', 'details'])

        for i in range(len(names)):
            name = names[i]
            description = descriptions[i]
            function = functions[i]
            return_type = returns[i]
            argument = '|'.join(arguments[i])
            argu_type = '|'.join(types[i])
            detail = '|'.join(details[i])

            csv_writer.writerow(
                [name, description, function, return_type, argument, argu_type, detail])

        csv_file.close()

    except Exception as e:
        print(e)


def read_api_csv():
    """Extracts Earth Engine API from a csv file and returns a dictionary containing information about each function.

    Returns:
        dict: The dictionary containing information about each function, including name, description, function form, return type, arguments, html. 
    """
    import copy
    import csv

    pkg_dir = os.path.dirname(
        pkg_resources.resource_filename("geemap", "geemap.py"))
    data_dir = os.path.join(pkg_dir, 'data')
    template_dir = os.path.join(data_dir, 'template')
    csv_file = os.path.join(template_dir, 'ee_api_docs.csv')
    html_file = os.path.join(template_dir, 'ee_api_docs.html')

    with open(html_file) as f:
        in_html_lines = f.readlines()

    api_dict = {}

    with open(csv_file, 'r', encoding='utf-8') as f:
        csv_reader = csv.DictReader(f, delimiter='\t')

        for line in csv_reader:

            out_html_lines = copy.copy(in_html_lines)
            out_html_lines[65] = in_html_lines[65].replace(
                'function_name', line['name'])
            out_html_lines[66] = in_html_lines[66].replace(
                'function_description', line.get('description'))
            out_html_lines[74] = in_html_lines[74].replace(
                'function_usage', line.get('function'))
            out_html_lines[75] = in_html_lines[75].replace(
                'function_returns', line.get('returns'))

            arguments = line.get('argument')
            types = line.get('type')
            details = line.get('details')

            if '|' in arguments:
                argument_items = arguments.split('|')
            else:
                argument_items = [arguments]

            if '|' in types:
                types_items = types.split('|')
            else:
                types_items = [types]

            if '|' in details:
                details_items = details.split('|')
            else:
                details_items = [details]

            out_argument_lines = []

            for index in range(len(argument_items)):
                in_argument_lines = in_html_lines[87:92]
                in_argument_lines[1] = in_argument_lines[1].replace(
                    'function_argument', argument_items[index])
                in_argument_lines[2] = in_argument_lines[2].replace(
                    'function_type', types_items[index])
                in_argument_lines[3] = in_argument_lines[3].replace(
                    'function_details', details_items[index])
                out_argument_lines.append("".join(in_argument_lines))

            out_html_lines = out_html_lines[:87] + \
                out_argument_lines + out_html_lines[92:]

            contents = ''.join(out_html_lines)

            api_dict[line['name']] = {
                'description': line.get('description'),
                'function': line.get('function'),
                'returns': line.get('returns'),
                'argument': line.get('argument'),
                'type': line.get('type'),
                'details': line.get('details'),
                'html': contents
            }

    return api_dict


def ee_function_tree(name):
    """Construct the tree structure based on an Earth Engine function. For example, the function "ee.Algorithms.FMask.matchClouds" will return a list ["ee.Algorithms", "ee.Algorithms.FMask", "ee.Algorithms.FMask.matchClouds"]

    Args:
        name (str): The name of the Earth Engine function

    Returns:
        list: The list for parent functions.
    """
    func_list = []
    try:
        items = name.split('.')
        if items[0] == 'ee':
            for i in range(2, len(items) + 1):
                func_list.append('.'.join(items[0:i]))
        else:
            for i in range(1, len(items) + 1):
                func_list.append('.'.join(items[0:i]))

        return func_list
    except Exception as e:
        print(e)
        print('The provided function name is invalid.')


def build_api_tree(api_dict, output_widget, layout_width='100%'):
    """Builds an Earth Engine API tree view.

    Args:
        api_dict (dict): The dictionary containing information about each Earth Engine API function.
        output_widget (object): An Output widget.
        layout_width (str, optional): The percentage width of the widget. Defaults to '100%'.

    Returns:
        tuple: Returns a tuple containing two items: a tree Output widget and a tree dictionary.
    """
    import warnings
    warnings.filterwarnings('ignore')

    tree = Tree()
    tree_dict = {}

    names = api_dict.keys()

    def handle_click(event):
        if event['new']:
            name = event['owner'].name
            values = api_dict[name]

            with output_widget:
                output_widget.clear_output()
                html_widget = widgets.HTML(value=values['html'])
                display(html_widget)

    for name in names:
        func_list = ee_function_tree(name)
        first = func_list[0]

        if first not in tree_dict.keys():
            tree_dict[first] = Node(first)
            tree_dict[first].opened = False
            tree.add_node(tree_dict[first])

        for index, func in enumerate(func_list):
            if index > 0:
                if func not in tree_dict.keys():
                    node = tree_dict[func_list[index - 1]]
                    node.opened = False
                    tree_dict[func] = Node(func)
                    node.add_node(tree_dict[func])

                    if index == len(func_list) - 1:
                        node = tree_dict[func_list[index]]
                        node.icon = 'file'
                        node.observe(handle_click, 'selected')

    return tree, tree_dict


def search_api_tree(keywords, api_tree):
    """Search Earth Engine API and return functions containing the specified keywords

    Args:
        keywords (str): The keywords to search for.
        api_tree (dict): The dictionary containing the Earth Engine API tree.

    Returns:
        object: An ipytree object/widget.
    """
    import warnings
    warnings.filterwarnings('ignore')

    sub_tree = Tree()

    for key in api_tree.keys():
        if keywords in key:
            sub_tree.add_node(api_tree[key])

    return sub_tree


def ee_search(asset_limit=100):
    """Search Earth Engine API and user assets. If you received a warning (IOPub message rate exceeded) in Jupyter notebook, you can relaunch Jupyter notebook using the following command:
        jupyter notebook --NotebookApp.iopub_msg_rate_limit=10000

    Args:
        asset_limit (int, optional): The number of assets to display for each asset type, i.e., Image, ImageCollection, and FeatureCollection. Defaults to 100.
    """

    import warnings
    warnings.filterwarnings('ignore')

    class Flags:
        def __init__(self, repos=None, docs=None, assets=None, docs_dict=None, asset_dict=None, asset_import=None):
            self.repos = repos
            self.docs = docs
            self.assets = assets
            self.docs_dict = docs_dict
            self.asset_dict = asset_dict
            self.asset_import = asset_import

    flags = Flags()

    search_type = widgets.ToggleButtons(
        options=['Scripts', 'Docs', 'Assets'],
        tooltips=['Search Earth Engine Scripts',
                  'Search Earth Engine API', 'Search Earth Engine Assets'],
        button_style='primary'
    )
    search_type.style.button_width = '100px'

    search_box = widgets.Text(
        placeholder='Filter scripts...', value='Loading...')
    search_box.layout.width = '310px'

    tree_widget = widgets.Output()

    left_widget = widgets.VBox()
    right_widget = widgets.VBox()
    output_widget = widgets.Output()
    output_widget.layout.max_width = '650px'

    search_widget = widgets.HBox()
    search_widget.children = [left_widget, right_widget]
    display(search_widget)

    repo_tree, repo_output, _ = build_repo_tree()
    left_widget.children = [search_type, repo_tree]
    right_widget.children = [repo_output]

    flags.repos = repo_tree
    search_box.value = ''

    def search_type_changed(change):
        search_box.value = ''

        output_widget.clear_output()
        tree_widget.clear_output()
        if change['new'] == 'Scripts':
            search_box.placeholder = 'Filter scripts...'
            left_widget.children = [search_type, repo_tree]
            right_widget.children = [repo_output]
        elif change['new'] == 'Docs':
            search_box.placeholder = 'Filter methods...'
            search_box.value = 'Loading...'
            left_widget.children = [search_type, search_box, tree_widget]
            right_widget.children = [output_widget]
            if flags.docs is None:
                api_dict = read_api_csv()
                ee_api_tree, tree_dict = build_api_tree(
                    api_dict, output_widget)
                flags.docs = ee_api_tree
                flags.docs_dict = tree_dict
            else:
                ee_api_tree = flags.docs
            with tree_widget:
                tree_widget.clear_output()
                display(ee_api_tree)
                right_widget.children = [output_widget]
            search_box.value = ''
        elif change['new'] == 'Assets':
            search_box.placeholder = 'Filter assets...'
            left_widget.children = [search_type, search_box, tree_widget]
            right_widget.children = [output_widget]
            search_box.value = 'Loading...'
            if flags.assets is None:
                asset_tree, asset_widget, asset_dict = build_asset_tree(
                    limit=asset_limit)
                flags.assets = asset_tree
                flags.asset_dict = asset_dict
                flags.asset_import = asset_widget

            with tree_widget:
                tree_widget.clear_output()
                display(flags.assets)
            right_widget.children = [flags.asset_import]
            search_box.value = ''

    search_type.observe(search_type_changed, names='value')

    def search_box_callback(text):

        if search_type.value == 'Docs':
            with tree_widget:
                if text.value == '':
                    print('Loading...')
                    tree_widget.clear_output(wait=True)
                    display(flags.docs)
                else:
                    tree_widget.clear_output()
                    print('Searching...')
                    tree_widget.clear_output(wait=True)
                    sub_tree = search_api_tree(text.value, flags.docs_dict)
                    display(sub_tree)
        elif search_type.value == 'Assets':
            with tree_widget:
                if text.value == '':
                    print('Loading...')
                    tree_widget.clear_output(wait=True)
                    display(flags.assets)
                else:
                    tree_widget.clear_output()
                    print('Searching...')
                    tree_widget.clear_output(wait=True)
                    sub_tree = search_api_tree(text.value, flags.asset_dict)
                    display(sub_tree)

    search_box.on_submit(search_box_callback)


def ee_user_id():
    """Gets Earth Engine account user id.

    Returns:
        str: A string containing the user id.
    """
    # ee_initialize()
    roots = ee.data.getAssetRoots()
    if len(roots) == 0:
        return None
    else:
        root = ee.data.getAssetRoots()[0]
        user_id = root['id'].replace("projects/earthengine-legacy/assets/", "")
        return user_id


def build_asset_tree(limit=100):

    import warnings
    import geeadd.ee_report as geeadd
    warnings.filterwarnings('ignore')

    # ee_initialize()

    tree = Tree(multiple_selection=False)
    tree_dict = {}
    asset_types = {}

    asset_icons = {
        'FOLDER': 'folder',
        'TABLE': 'table',
        'IMAGE': 'image',
        'IMAGE_COLLECTION': 'file'
    }

    info_widget = widgets.HBox()

    import_btn = widgets.Button(
        description='import',
        button_style='primary',
        tooltip='Click to import the selected asset',
        disabled=True
    )
    import_btn.layout.min_width = '57px'
    import_btn.layout.max_width = '57px'

    path_widget = widgets.Text()
    path_widget.layout.min_width = '500px'
    # path_widget.disabled = True

    info_widget.children = [import_btn, path_widget]

    user_id = ee_user_id()
    if user_id is None:
        print('Your GEE account does not have any assets. Please create a repository at https://code.earthengine.google.com')
        return

    user_path = 'projects/earthengine-legacy/assets/' + user_id
    root_node = Node(user_id)
    root_node.opened = True
    tree_dict[user_id] = root_node
    tree.add_node(root_node)

    collection_list, table_list, image_list, folder_paths = geeadd.fparse(
        user_path)
    collection_list = collection_list[:limit]
    table_list = table_list[:limit]
    image_list = image_list[:limit]
    folder_paths = folder_paths[:limit]
    folders = [p[35:] for p in folder_paths[1:]]

    asset_type = 'FOLDER'
    for folder in folders:
        bare_folder = folder.replace(user_id + '/', '')
        if folder not in tree_dict.keys():
            node = Node(bare_folder)
            node.opened = False
            node.icon = asset_icons[asset_type]
            root_node.add_node(node)
            tree_dict[folder] = node
            asset_types[folder] = asset_type

    def import_btn_clicked(b):
        if path_widget.value != '':
            dataset_uid = 'dataset_' + random_string(string_length=3)
            layer_name = path_widget.value.split('/')[-1][:-2:]
            line1 = '{} = {}\n'.format(
                dataset_uid, path_widget.value)
            line2 = 'Map.addLayer(' + dataset_uid + \
                ', {}, "' + layer_name + '")'
            contents = ''.join([line1, line2])
            create_code_cell(contents)

    import_btn.on_click(import_btn_clicked)

    def handle_click(event):
        if event['new']:
            cur_node = event['owner']
            for key in tree_dict.keys():
                if cur_node is tree_dict[key]:
                    if asset_types[key] == 'IMAGE':
                        path_widget.value = "ee.Image('{}')".format(key)
                    elif asset_types[key] == 'IMAGE_COLLECTION':
                        path_widget.value = "ee.ImageCollection('{}')".format(
                            key)
                    elif asset_types[key] == 'TABLE':
                        path_widget.value = "ee.FeatureCollection('{}')".format(
                            key)
                    if import_btn.disabled:
                        import_btn.disabled = False
                    break

    assets = [collection_list, image_list, table_list]
    for index, asset_list in enumerate(assets):
        if index == 0:
            asset_type = 'IMAGE_COLLECTION'
        elif index == 1:
            asset_type = 'IMAGE'
        else:
            asset_type = 'TABLE'

        for asset in asset_list:
            items = asset.split('/')
            parent = '/'.join(items[:-1])
            child = items[-1]
            parent_node = tree_dict[parent]
            child_node = Node(child)
            child_node.icon = asset_icons[asset_type]
            parent_node.add_node(child_node)
            tree_dict[asset] = child_node
            asset_types[asset] = asset_type
            child_node.observe(handle_click, 'selected')

    return tree, info_widget, tree_dict


def build_repo_tree(out_dir=None, name='gee_repos'):
    """Builds a repo tree for GEE account.

    Args:
        out_dir (str): The output directory for the repos. Defaults to None.
        name (str, optional): The output name for the repo directory. Defaults to 'gee_repos'.

    Returns:
        tuple: Returns a tuple containing a tree widget, an output widget, and a tree dictionary containing nodes.
    """
    import warnings
    warnings.filterwarnings('ignore')

    if out_dir is None:
        out_dir = os.path.join(os.path.expanduser('~'))

    repo_dir = os.path.join(out_dir, name)
    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)

    URLs = {
        # 'Owner': 'https://earthengine.googlesource.com/{}/default'.format(ee_user_id()),
        'Writer': '',
        'Reader': 'https://github.com/giswqs/geemap',
        'Examples': 'https://github.com/giswqs/earthengine-py-examples',
        'Archive': 'https://earthengine.googlesource.com/EGU2017-EE101'
    }

    user_id = ee_user_id()
    if user_id is not None:
        URLs['Owner'] = 'https://earthengine.googlesource.com/{}/default'.format(
            ee_user_id())

    path_widget = widgets.Text(
        placeholder='Enter the link to a Git repository here...')
    path_widget.layout.width = '475px'
    clone_widget = widgets.Button(
        description='Clone', button_style='primary', tooltip='Clone the repository to folder.')
    info_widget = widgets.HBox()

    groups = ['Owner', 'Writer', 'Reader', 'Examples', 'Archive']
    for group in groups:
        group_dir = os.path.join(repo_dir, group)
        if not os.path.exists(group_dir):
            os.makedirs(group_dir)

    example_dir = os.path.join(repo_dir, 'Examples/earthengine-py-examples')
    if not os.path.exists(example_dir):
        clone_github_repo(URLs['Examples'], out_dir=example_dir)

    left_widget, right_widget, tree_dict = file_browser(
        in_dir=repo_dir, add_root_node=False, search_description='Filter scripts...', use_import=True, return_sep_widgets=True)
    info_widget.children = [right_widget]

    def handle_folder_click(event):
        if event['new']:
            url = ''
            selected = event['owner']
            if selected.name in URLs.keys():
                url = URLs[selected.name]

            path_widget.value = url
            clone_widget.disabled = False
            info_widget.children = [path_widget, clone_widget]
        else:
            info_widget.children = [right_widget]

    for group in groups:
        dirname = os.path.join(repo_dir, group)
        node = tree_dict[dirname]
        node.observe(handle_folder_click, 'selected')

    def handle_clone_click(b):

        url = path_widget.value
        default_dir = os.path.join(repo_dir, 'Examples')
        if url == '':
            path_widget.value = 'Please enter a valid URL to the repository.'
        else:
            for group in groups:
                key = os.path.join(repo_dir, group)
                node = tree_dict[key]
                if node.selected:
                    default_dir = key
            try:
                path_widget.value = 'Cloning...'
                clone_dir = os.path.join(default_dir, os.path.basename(url))
                if 'github.com' in url:
                    clone_github_repo(url, out_dir=clone_dir)
                elif 'googlesource' in url:
                    clone_google_repo(url, out_dir=clone_dir)
                path_widget.value = 'Cloned to {}'.format(clone_dir)
                clone_widget.disabled = True
            except Exception as e:
                path_widget.value = 'An error occurred when trying to clone the repository ' + \
                    str(e)
                clone_widget.disabled = True

    clone_widget.on_click(handle_clone_click)

    return left_widget, info_widget, tree_dict


def file_browser(in_dir=None, show_hidden=False, add_root_node=True, search_description=None, use_import=False, return_sep_widgets=False):
    """Creates a simple file browser and text editor.

    Args:
        in_dir (str, optional): The input directory. Defaults to None, which will use the current working directory.
        show_hidden (bool, optional): Whether to show hidden files/folders. Defaults to False.
        add_root_node (bool, optional): Whether to add the input directory as a root node. Defaults to True.
        search_description (str, optional): The description of the search box. Defaults to None.
        use_import (bool, optional): Whether to show the import button. Defaults to False.
        return_sep_widgets (bool, optional): Whether to return the results as separate widgets. Defaults to False.

    Returns:
        object: An ipywidget.
    """
    import platform
    if in_dir is None:
        in_dir = os.getcwd()

    if not os.path.exists(in_dir):
        print('The provided directory does not exist.')
        return
    elif not os.path.isdir(in_dir):
        print('The provided path is not a valid directory.')
        return

    sep = '/'
    if platform.system() == "Windows":
        sep = '\\'

    if in_dir.endswith(sep):
        in_dir = in_dir[:-1]

    full_widget = widgets.HBox()
    left_widget = widgets.VBox()

    right_widget = widgets.VBox()

    import_btn = widgets.Button(
        description='import', button_style='primary', tooltip='import the content to a new cell', disabled=True)
    import_btn.layout.width = '70px'
    path_widget = widgets.Text()
    path_widget.layout.min_width = '400px'
    # path_widget.layout.max_width = '400px'
    save_widget = widgets.Button(
        description='Save', button_style='primary', tooltip='Save edits to file.', disabled=True)
    info_widget = widgets.HBox()
    info_widget.children = [path_widget, save_widget]
    if use_import:
        info_widget.children = [import_btn, path_widget, save_widget]

    text_widget = widgets.Textarea()
    text_widget.layout.width = '630px'
    text_widget.layout.height = '600px'

    right_widget.children = [info_widget, text_widget]
    full_widget.children = [left_widget]

    if search_description is None:
        search_description = 'Search files/folders...'
    search_box = widgets.Text(placeholder=search_description)
    search_box.layout.width = '310px'
    tree_widget = widgets.Output()
    tree_widget.layout.max_width = '310px'
    tree_widget.overflow = 'auto'

    left_widget.children = [search_box, tree_widget]

    tree = Tree(multiple_selection=False)
    tree_dict = {}

    def on_button_clicked(b):
        content = text_widget.value
        out_file = path_widget.value

        out_dir = os.path.dirname(out_file)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        with open(out_file, 'w') as f:
            f.write(content)

        text_widget.disabled = True
        text_widget.value = 'The content has been saved successfully.'
        save_widget.disabled = True
        path_widget.disabled = True

        if (out_file not in tree_dict.keys()) and (out_dir in tree_dict.keys()):
            node = Node(os.path.basename(out_file))
            tree_dict[out_file] = node
            parent_node = tree_dict[out_dir]
            parent_node.add_node(node)

    save_widget.on_click(on_button_clicked)

    def import_btn_clicked(b):
        if (text_widget.value != '') and (path_widget.value.endswith('.py')):
            create_code_cell(text_widget.value)

    import_btn.on_click(import_btn_clicked)

    def search_box_callback(text):

        with tree_widget:
            if text.value == '':
                print('Loading...')
                tree_widget.clear_output(wait=True)
                display(tree)
            else:
                tree_widget.clear_output()
                print('Searching...')
                tree_widget.clear_output(wait=True)
                sub_tree = search_api_tree(text.value, tree_dict)
                display(sub_tree)
    search_box.on_submit(search_box_callback)

    def handle_file_click(event):
        if event['new']:
            cur_node = event['owner']
            for key in tree_dict.keys():
                if (cur_node is tree_dict[key]) and (os.path.isfile(key)):
                    if key.endswith('.py'):
                        import_btn.disabled = False
                    else:
                        import_btn.disabled = True
                    try:
                        with open(key) as f:
                            content = f.read()
                            text_widget.value = content
                            text_widget.disabled = False
                            path_widget.value = key
                            path_widget.disabled = False
                            save_widget.disabled = False
                            full_widget.children = [left_widget, right_widget]
                    except Exception as e:
                        path_widget.value = key
                        path_widget.disabled = True
                        save_widget.disabled = True
                        text_widget.disabled = True
                        text_widget.value = 'Failed to open {}.'.format(
                            cur_node.name) + '\n\n' + str(e)
                        full_widget.children = [left_widget, right_widget]
                        return
                    break

    def handle_folder_click(event):
        if event['new']:
            full_widget.children = [left_widget]
            text_widget.value = ''

    if add_root_node:
        root_name = in_dir.split(sep)[-1]
        root_node = Node(root_name)
        tree_dict[in_dir] = root_node
        tree.add_node(root_node)
        root_node.observe(handle_folder_click, 'selected')

    for root, d_names, f_names in os.walk(in_dir):

        if not show_hidden:
            folders = root.split(sep)
            for folder in folders:
                if folder.startswith('.'):
                    continue
            for d_name in d_names:
                if d_name.startswith('.'):
                    d_names.remove(d_name)
            for f_name in f_names:
                if f_name.startswith('.'):
                    f_names.remove(f_name)

        d_names.sort()
        f_names.sort()

        if (not add_root_node) and (root == in_dir):
            for d_name in d_names:
                node = Node(d_name)
                tree_dict[os.path.join(in_dir, d_name)] = node
                tree.add_node(node)
                node.opened = False
                node.observe(handle_folder_click, 'selected')

        if (root != in_dir) and (root not in tree_dict.keys()):
            name = root.split(sep)[-1]
            dir_name = os.path.dirname(root)
            parent_node = tree_dict[dir_name]
            node = Node(name)
            tree_dict[root] = node
            parent_node.add_node(node)
            node.observe(handle_folder_click, 'selected')

        if len(f_names) > 0:
            parent_node = tree_dict[root]
            parent_node.opened = False
            for f_name in f_names:
                node = Node(f_name)
                node.icon = 'file'
                full_path = os.path.join(root, f_name)
                tree_dict[full_path] = node
                parent_node.add_node(node)
                node.observe(handle_file_click, 'selected')

    with tree_widget:
        tree_widget.clear_output()
        display(tree)

    if return_sep_widgets:
        return left_widget, right_widget, tree_dict
    else:
        return full_widget


def check_git_install():
    """Checks if Git is installed.

    Returns:
        bool: Returns True if Git is installed, otherwise returns False.
    """
    import webbrowser

    cmd = 'git --version'
    output = os.popen(cmd).read()

    if 'git version' in output:
        return True
    else:
        url = 'https://git-scm.com/downloads'
        print(
            "Git is not installed. Please download Git from {} and install it.".format(url))
        webbrowser.open_new_tab(url)
        return False


def clone_github_repo(url, out_dir):
    """Clones a GitHub repository.

    Args:
        url (str): The link to the GitHub repository
        out_dir (str): The output directory for the cloned repository. 
    """

    import zipfile

    repo_name = os.path.basename(url)
    # url_zip = os.path.join(url, 'archive/master.zip')
    url_zip = url + '/archive/master.zip'

    if os.path.exists(out_dir):
        print(
            'The specified output directory already exists. Please choose a new directory.')
        return

    parent_dir = os.path.dirname(out_dir)
    out_file_path = os.path.join(parent_dir, repo_name + '.zip')

    try:
        urllib.request.urlretrieve(url_zip, out_file_path)
    except:
        print("The provided URL is invalid. Please double check the URL.")
        return

    with zipfile.ZipFile(out_file_path, "r") as zip_ref:
        zip_ref.extractall(parent_dir)

    src = out_file_path.replace('.zip', '-master')
    os.rename(src, out_dir)
    os.remove(out_file_path)


def clone_github_repo2(url, out_dir=None):
    """Clones a GitHub repository.

    Args:
        url (str): The link to the GitHub repository
        out_dir (str, optional): The output directory for the cloned repository. Defaults to None.
    """
    check_install('dulwich')
    from dulwich import porcelain

    repo_name = os.path.basename(url)

    if out_dir is None:
        out_dir = os.path.join(os.getcwd(), repo_name)

    if not os.path.exists(os.path.dirname(out_dir)):
        os.makedirs(os.path.dirname(out_dir))

    if os.path.exists(out_dir):
        print(
            'The specified output directory already exists. Please choose a new directory.')
        return

    try:
        porcelain.clone(url, out_dir)
    except Exception as e:
        print('Failed to clone the repository.')
        print(e)


def clone_google_repo(url, out_dir=None):
    """Clones an Earth Engine repository from https://earthengine.googlesource.com, such as https://earthengine.googlesource.com/users/google/datasets

    Args:
        url (str): The link to the Earth Engine repository
        out_dir (str, optional): The output directory for the cloned repository. Defaults to None.
    """
    repo_name = os.path.basename(url)

    if out_dir is None:
        out_dir = os.path.join(os.getcwd(), repo_name)

    if not os.path.exists(os.path.dirname(out_dir)):
        os.makedirs(os.path.dirname(out_dir))

    if os.path.exists(out_dir):
        print(
            'The specified output directory already exists. Please choose a new directory.')
        return

    if check_git_install():

        cmd = 'git clone "{}" "{}"'.format(url, out_dir)
        os.popen(cmd).read()


def reduce_gif_size(in_gif, out_gif=None):
    """Reduces a GIF image using ffmpeg.

    Args:
        in_gif (str): The input file path to the GIF image.
        out_gif (str, optional): The output file path to the GIF image. Defaults to None.
    """
    import ffmpeg
    import shutil

    if not is_tool('ffmpeg'):
        print('ffmpeg is not installed on your computer.')
        return

    if not os.path.exists(in_gif):
        print('The input gif file does not exist.')
        return

    if out_gif is None:
        out_gif = in_gif
    elif not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

    if in_gif == out_gif:
        tmp_gif = in_gif.replace('.gif', '_tmp.gif')
        shutil.copyfile(in_gif, tmp_gif)
        stream = ffmpeg.input(tmp_gif)
        stream = ffmpeg.output(stream, in_gif).overwrite_output()
        ffmpeg.run(stream)
        os.remove(tmp_gif)

    else:
        stream = ffmpeg.input(in_gif)
        stream = ffmpeg.output(stream, out_gif).overwrite_output()
        ffmpeg.run(stream)


def upload_to_imgur(in_gif):
    """Uploads an image to imgur.com

    Args:
        in_gif (str): The file path to the image.
    """
    import subprocess

    pkg_name = 'imgur-uploader'
    if not is_tool(pkg_name):
        check_install(pkg_name)

    try:
        IMGUR_API_ID = os.environ.get('IMGUR_API_ID', None)
        IMGUR_API_SECRET = os.environ.get('IMGUR_API_SECRET', None)
        credentials_path = os.path.join(os.path.expanduser(
            '~'), '.config/imgur_uploader/uploader.cfg')

        if ((IMGUR_API_ID is not None) and (IMGUR_API_SECRET is not None)) or os.path.exists(credentials_path):

            proc = subprocess.Popen(
                ['imgur-uploader', in_gif], stdout=subprocess.PIPE)
            for i in range(0, 2):
                line = proc.stdout.readline()
                print(line.rstrip().decode("utf-8"))
            # while True:
            #     line = proc.stdout.readline()
            #     if not line:
            #         break
            #     print(line.rstrip().decode("utf-8"))
        else:
            print('Imgur API credentials could not be found. Please check https://pypi.org/project/imgur-uploader/ for instructions on how to get Imgur API credentials')
            return

    except Exception as e:
        print(e)


def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""

    from shutil import which

    return which(name) is not None


def image_props(img, date_format='YYYY-MM-dd'):
    """Gets image properties.

    Args:
        img (ee.Image): The input image.
        date_format (str, optional): The output date format. Defaults to 'YYYY-MM-dd HH:mm:ss'.

    Returns:
        dd.Dictionary: The dictionary containing image properties.
    """
    if not isinstance(img, ee.Image):
        print('The input object must be an ee.Image')
        return

    keys = img.propertyNames().remove('system:footprint').remove('system:bands')
    values = keys.map(lambda p: img.get(p))

    bands = img.bandNames()
    scales = bands.map(lambda b: img.select([b]).projection().nominalScale())
    scale = ee.Algorithms.If(scales.distinct().size().gt(
        1), ee.Dictionary.fromLists(bands.getInfo(), scales), scales.get(0))
    image_date = ee.Date(img.get('system:time_start')).format(date_format)
    time_start = ee.Date(img.get('system:time_start')
                         ).format('YYYY-MM-dd HH:mm:ss')
    # time_end = ee.Date(img.get('system:time_end')).format('YYYY-MM-dd HH:mm:ss')
    time_end = ee.Algorithms.If(ee.List(img.propertyNames()).contains('system:time_end'), ee.Date(
        img.get('system:time_end')).format('YYYY-MM-dd HH:mm:ss'), time_start)
    asset_size = ee.Number(img.get('system:asset_size')).divide(
        1e6).format().cat(ee.String(' MB'))

    props = ee.Dictionary.fromLists(keys, values)
    props = props.set('system:time_start', time_start)
    props = props.set('system:time_end', time_end)
    props = props.set('system:asset_size', asset_size)
    props = props.set('NOMINAL_SCALE', scale)
    props = props.set('IMAGE_DATE', image_date)

    return props


def image_stats(img, region=None, scale=None):
    """Gets image descriptive statistics.

    Args:
        img (ee.Image): The input image to calculate descriptive statistics.
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.

    Returns:
        ee.Dictionary: A dictionary containing the description statistics of the input image.
    """
    import geemap.utils as utils

    if not isinstance(img, ee.Image):
        print('The input object must be an ee.Image')
        return

    stat_types = ['min', 'max', 'mean', 'std', 'sum']

    image_min = utils.image_min_value(img, region, scale)
    image_max = utils.image_max_value(img, region, scale)
    image_mean = utils.image_mean_value(img, region, scale)
    image_std = utils.image_std_value(img, region, scale)
    image_sum = utils.image_sum_value(img, region, scale)

    stat_results = ee.List(
        [image_min, image_max, image_mean, image_std, image_sum])

    stats = ee.Dictionary.fromLists(stat_types, stat_results)

    return stats


def date_sequence(start, end, unit, date_format='YYYY-MM-dd'):
    """Creates a date sequence.

    Args:
        start (str): The start date, e.g., '2000-01-01'.
        end (str): The end date, e.g., '2000-12-31'.
        unit (str): One of 'year', 'month' 'week', 'day', 'hour', 'minute', or 'second'.
        date_format (str, optional): A pattern, as described at http://joda-time.sourceforge.net/apidocs/org/joda/time/format/DateTimeFormat.html. Defaults to 'YYYY-MM-dd'.

    Returns:
        ee.List: A list of date sequence.
    """
    start_date = ee.Date(start)
    end_date = ee.Date(end)
    count = ee.Number(end_date.difference(start_date, unit)).toInt()
    num_seq = ee.List.sequence(0, count)
    date_seq = num_seq.map(
        lambda d: start_date.advance(d, unit).format(date_format))
    return date_seq


def adjust_longitude(in_fc):
    """Adjusts longitude if it is less than -180 or greater than 180.

    Args:
        in_fc (dict): The input dictionary containing coordinates.

    Returns:
        dict: A dictionary containing the converted longitudes
    """
    try:

        keys = in_fc.keys()

        if 'geometry' in keys:

            coordinates = in_fc['geometry']['coordinates']

            if in_fc['geometry']['type'] == 'Point':
                longitude = coordinates[0]
                if longitude < - 180:
                    longitude = 360 + longitude
                elif longitude > 180:
                    longitude = longitude - 360
                in_fc['geometry']['coordinates'][0] = longitude

            elif in_fc['geometry']['type'] == 'Polygon':
                for index1, item in enumerate(coordinates):
                    for index2, element in enumerate(item):
                        longitude = element[0]
                        if longitude < - 180:
                            longitude = 360 + longitude
                        elif longitude > 180:
                            longitude = longitude - 360
                        in_fc['geometry']['coordinates'][index1][index2][0] = longitude

            elif in_fc['geometry']['type'] == 'LineString':
                for index, element in enumerate(coordinates):
                    longitude = element[0]
                    if longitude < - 180:
                        longitude = 360 + longitude
                    elif longitude > 180:
                        longitude = longitude - 360
                    in_fc['geometry']['coordinates'][index][0] = longitude

        elif 'type' in keys:

            coordinates = in_fc['coordinates']

            if in_fc['type'] == 'Point':
                longitude = coordinates[0]
                if longitude < - 180:
                    longitude = 360 + longitude
                elif longitude > 180:
                    longitude = longitude - 360
                in_fc['coordinates'][0] = longitude

            elif in_fc['type'] == 'Polygon':
                for index1, item in enumerate(coordinates):
                    for index2, element in enumerate(item):
                        longitude = element[0]
                        if longitude < - 180:
                            longitude = 360 + longitude
                        elif longitude > 180:
                            longitude = longitude - 360
                        in_fc['coordinates'][index1][index2][0] = longitude

            elif in_fc['type'] == 'LineString':
                for index, element in enumerate(coordinates):
                    longitude = element[0]
                    if longitude < - 180:
                        longitude = 360 + longitude
                    elif longitude > 180:
                        longitude = longitude - 360
                    in_fc['coordinates'][index][0] = longitude

        return in_fc

    except Exception as e:
        print(e)
        return None


def set_proxy(port=1080, ip='http://127.0.0.1'):
    """Sets proxy if needed. This is only needed for countries where Google services are not available.

    Args:
        port (int, optional): The proxy port number. Defaults to 1080.
        ip (str, optional): The IP address. Defaults to 'http://127.0.0.1'.
    """
    import os
    import requests

    try:

        if not ip.startswith('http'):
            ip = 'http://' + ip
        proxy = '{}:{}'.format(ip, port)

        os.environ['HTTP_PROXY'] = proxy
        os.environ['HTTPS_PROXY'] = proxy

        a = requests.get('https://earthengine.google.com/')

        if a.status_code != 200:
            print(
                'Failed to connect to Earth Engine. Please double check the port number and ip address.')

    except Exception as e:
        print(e)


def in_colab_shell():
    """Tests if the code is being executed within Google Colab."""
    try:
        import google.colab  # pylint: disable=unused-variable
        return True
    except ImportError:
        return False


def is_drive_mounted():
    """Checks whether Google Drive is mounted in Google Colab.

    Returns:
        bool: Returns True if Google Drive is mounted, False otherwise.
    """
    drive_path = '/content/drive/My Drive'
    if os.path.exists(drive_path):
        return True
    else:
        return False


def credentials_in_drive():
    """Checks if the ee credentials file exists in Google Drive.

    Returns:
        bool: Returns True if Google Drive is mounted, False otherwise.
    """
    credentials_path = '/content/drive/My Drive/.config/earthengine/credentials'
    if os.path.exists(credentials_path):
        return True
    else:
        return False


def credentials_in_colab():
    """Checks if the ee credentials file exists in Google Colab.

    Returns:
        bool: Returns True if Google Drive is mounted, False otherwise.
    """
    credentials_path = '/root/.config/earthengine/credentials'
    if os.path.exists(credentials_path):
        return True
    else:
        return False


def copy_credentials_to_drive():
    """Copies ee credentials from Google Colab to Google Drive.
    """
    import shutil
    src = '/root/.config/earthengine/credentials'
    dst = '/content/drive/My Drive/.config/earthengine/credentials'

    wd = os.path.dirname(dst)
    if not os.path.exists(wd):
        os.makedirs(wd)

    shutil.copyfile(src, dst)


def copy_credentials_to_colab():
    """Copies ee credentials from Google Drive to Google Colab.
    """
    import shutil
    src = '/content/drive/My Drive/.config/earthengine/credentials'
    dst = '/root/.config/earthengine/credentials'

    wd = os.path.dirname(dst)
    if not os.path.exists(wd):
        os.makedirs(wd)

    shutil.copyfile(src, dst)


def create_download_link(filename, title="Click here to download: "):
    """Downloads a file from voila. Adopted from https://github.com/voila-dashboards/voila/issues/578

    Args:
        filename (str): The file path to the file to download
        title (str, optional): str. Defaults to "Click here to download: ".

    Returns:
        str: HTML download URL.
    """
    import base64
    from IPython.display import HTML
    data = open(filename, "rb").read()
    b64 = base64.b64encode(data)
    payload = b64.decode()
    basename = os.path.basename(filename)
    html = '<a download="{filename}" href="data:text/csv;base64,{payload}" style="color:#0000FF;" target="_blank">{title}</a>'
    html = html.format(payload=payload, title=title +
                       f' {basename}', filename=basename)
    return HTML(html)


def edit_download_html(htmlWidget, filename, title="Click here to download: "):
    """Downloads a file from voila. Adopted from https://github.com/voila-dashboards/voila/issues/578#issuecomment-617668058

    Args:
        htmlWidget (object): The HTML widget to display the URL.
        filename (str): File path to download. 
        title (str, optional): Download description. Defaults to "Click here to download: ".
    """

    from IPython.display import HTML
    import ipywidgets as widgets
    import base64

    # Change widget html temperarily to a font-awesome spinner
    htmlWidget.value = "<i class=\"fa fa-spinner fa-spin fa-2x fa-fw\"></i><span class=\"sr-only\">Loading...</span>"

    # Process raw data
    data = open(filename, "rb").read()
    b64 = base64.b64encode(data)
    payload = b64.decode()

    basename = os.path.basename(filename)

    # Create and assign html to widget
    html = '<a download="{filename}" href="data:text/csv;base64,{payload}" target="_blank">{title}</a>'
    htmlWidget.value = html.format(
        payload=payload, title=title+basename, filename=basename)

    # htmlWidget = widgets.HTML(value = '')
    # htmlWidget


def load_GeoTIFF(URL):
    """Loads a Cloud Optimized GeoTIFF (COG) as an Image. Only Google Cloud Storage is supported. The URL can be one of the following formats:
    Option 1: gs://pdd-stac/disasters/hurricane-harvey/0831/20170831_172754_101c_3B_AnalyticMS.tif
    Option 2: https://storage.googleapis.com/pdd-stac/disasters/hurricane-harvey/0831/20170831_172754_101c_3B_AnalyticMS.tif
    Option 3: https://storage.cloud.google.com/gcp-public-data-landsat/LC08/01/044/034/LC08_L1TP_044034_20131228_20170307_01_T1/LC08_L1TP_044034_20131228_20170307_01_T1_B5.TIF

    Args:
        URL (str): The Cloud Storage URL of the GeoTIFF to load.

    Returns:
        ee.Image: an Earth Engine image.
    """

    uri = URL.strip()

    if uri.startswith('https://storage.googleapis.com/'):
        uri = uri.replace('https://storage.googleapis.com/', 'gs://')
    elif uri.startswith('https://storage.cloud.google.com/'):
        uri = uri.replace('https://storage.cloud.google.com/', 'gs://')

    if not uri.startswith('gs://'):
        raise Exception(
            'Invalid GCS URL: {}. Expected something of the form "gs://bucket/path/to/object.tif".'.format(uri))

    if not uri.lower().endswith('.tif'):
        raise Exception(
            'Invalid GCS URL: {}. Expected something of the form "gs://bucket/path/to/object.tif".'.format(uri))

    cloud_image = ee.Image.loadGeoTIFF(uri)
    return cloud_image


def load_GeoTIFFs(URLs):
    """Loads a list of Cloud Optimized GeoTIFFs (COG) as an ImageCollection. URLs is a list of URL, which can be one of the following formats:
    Option 1: gs://pdd-stac/disasters/hurricane-harvey/0831/20170831_172754_101c_3B_AnalyticMS.tif
    Option 2: https://storage.googleapis.com/pdd-stac/disasters/hurricane-harvey/0831/20170831_172754_101c_3B_AnalyticMS.tif
    Option 3: https://storage.cloud.google.com/gcp-public-data-landsat/LC08/01/044/034/LC08_L1TP_044034_20131228_20170307_01_T1/LC08_L1TP_044034_20131228_20170307_01_T1_B5.TIF

    Args:
        URLs (list): A list of Cloud Storage URL of the GeoTIFF to load.

    Returns:
        ee.ImageCollection: An Earth Engine ImageCollection.
    """

    if not isinstance(URLs, list):
        raise Exception('The URLs argument must be a list.')

    URIs = []
    for URL in URLs:
        uri = URL.strip()

        if uri.startswith('https://storage.googleapis.com/'):
            uri = uri.replace('https://storage.googleapis.com/', 'gs://')
        elif uri.startswith('https://storage.cloud.google.com/'):
            uri = uri.replace('https://storage.cloud.google.com/', 'gs://')

        if not uri.startswith('gs://'):
            raise Exception(
                'Invalid GCS URL: {}. Expected something of the form "gs://bucket/path/to/object.tif".'.format(uri))

        if not uri.lower().endswith('.tif'):
            raise Exception(
                'Invalid GCS URL: {}. Expected something of the form "gs://bucket/path/to/object.tif".'.format(uri))

        URIs.append(uri)

    URIs = ee.List(URIs)
    collection = URIs.map(lambda uri: ee.Image.loadGeoTIFF(uri))
    return ee.ImageCollection(collection)


def landsat_ts_norm_diff(collection, bands=['Green', 'SWIR1'], threshold=0):
    """Computes a normalized difference index based on a Landsat timeseries.

    Args:
        collection (ee.ImageCollection): A Landsat timeseries.
        bands (list, optional): The bands to use for computing normalized difference. Defaults to ['Green', 'SWIR1'].
        threshold (float, optional): The threshold to extract features. Defaults to 0.

    Returns:
        ee.ImageCollection: An ImageCollection containing images with values greater than the specified threshold. 
    """
    nd_images = collection.map(lambda img: img.normalizedDifference(
        bands).gt(threshold).copyProperties(img, img.propertyNames()))
    return nd_images


def landsat_ts_norm_diff_gif(collection, out_gif=None, vis_params=None, palette=['black', 'blue'], dimensions=768, frames_per_second=10):
    """[summary]

    Args:
        collection (ee.ImageCollection): The normalized difference Landsat timeseires.
        out_gif (str, optional): File path to the output animated GIF. Defaults to None.
        vis_params (dict, optional): Visualization parameters. Defaults to None.
        palette (list, optional): The palette to use for visualizing the timelapse. Defaults to ['black', 'blue']. The first color in the list is the background color.
        dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 10.

    Returns:
        str: File path to the output animated GIF.
    """
    coordinates = ee.Image(collection.first()).get('coordinates')
    roi = ee.Geometry.Polygon(coordinates, None, False)

    if out_gif is None:
        out_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        filename = 'landsat_ts_nd_' + random_string() + '.gif'
        out_gif = os.path.join(out_dir, filename)
    elif not out_gif.endswith('.gif'):
        raise Exception('The output file must end with .gif')

    bands = ['nd']
    if vis_params is None:
        vis_params = {}
        vis_params['bands'] = bands
        vis_params['palette'] = palette

    video_args = vis_params.copy()
    video_args['dimensions'] = dimensions
    video_args['region'] = roi
    video_args['framesPerSecond'] = frames_per_second
    video_args['crs'] = 'EPSG:3857'

    if 'bands' not in video_args.keys():
        video_args['bands'] = bands

    download_ee_video(collection, video_args, out_gif)

    return out_gif
