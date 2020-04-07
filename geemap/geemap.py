"""Main module for interactive mapping using Google Earth Engine Python API and ipyleaflet.
Keep in mind that Earth Engine functions use camel case, such as setOptions(), setCenter(), centerObject(), addLayer().
ipyleaflet functions use snake case, such as add_tile_layer(), add_wms_layer(), add_minimap().
"""

import ee
import ipyleaflet
import math
import os
import webbrowser
from bqplot import pyplot as plt
from ipyleaflet import *
import ipywidgets as widgets
from .basemaps import ee_basemaps


class Map(ipyleaflet.Map):
    """The Map class inherits from ipyleaflet.Map

    Args:
        ipyleaflet (object): An ipyleaflet map instance.

    Returns:
        object: ipyleaflet map object.
    """

    def __init__(self, **kwargs):

        # Authenticates Earth Engine and initialize an Earth Engine session
        try:
            ee.Initialize()
        except Exception as e:
            ee.Authenticate()
            ee.Initialize()

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

        # Inherit the ipyleaflet Map class
        super().__init__(**kwargs)
        self.scroll_wheel_zoom = True
        self.layout.height = '550px'

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

        self.add_layer(ee_basemaps['ROADMAP'])

        draw_control = DrawControl(marker={'shapeOptions': {'color': '#0000FF'}},
                                   rectangle={'shapeOptions': {
                                       'color': '#0000FF'}},
                                   circle={'shapeOptions': {
                                       'color': '#0000FF'}},
                                   circlemarker={},
                                   )

        self.draw_count = 0  # The number of shapes drawn by the user using the DrawControl
        # The list of Earth Engine Geometry objects converted from geojson
        self.draw_features = []
        # The Earth Engine Geometry object converted from the last drawn feature
        self.draw_last_feature = None
        self.draw_layer = None

        self.plot_widget = None  # The plot widget for plotting Earth Engine data
        self.plot_control = None  # The plot control for interacting plotting
        self.random_marker = None

        self.ee_layers = []
        self.ee_layer_names = []
        self.ee_raster_layers = []
        self.ee_raster_layer_names = []

        # Handles draw events
        def handle_draw(target, action, geo_json):
            try:
                self.draw_count += 1
                geom = geojson_to_ee(geo_json, False)
                feature = ee.Feature(geom)
                self.draw_last_feature = feature
                self.draw_features.append(feature)
                collection = ee.FeatureCollection(self.draw_features)
                ee_draw_layer = ee_tile_layer(
                    collection, {'color': 'blue'}, 'Drawing Features', True, 0.5)

                if self.draw_count == 1:
                    self.add_layer(ee_draw_layer)
                    self.draw_layer = ee_draw_layer
                else:
                    self.substitute_layer(self.draw_layer, ee_draw_layer)
                    self.draw_layer = ee_draw_layer

                draw_control.clear()
            except Exception as e:
                print(e)
                print("There was an error creating Earth Engine Feature.")
                self.draw_count = 0
                self.draw_features = []
                self.draw_last_feature = None
                self.draw_layer = None

        draw_control.on_draw(handle_draw)
        self.add_control(draw_control)
        self.draw_control = draw_control

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
            description='Use Inspector',
            indent=False,
            layout=widgets.Layout(height='18px')
        )
        inspector_checkbox.layout.width = '18ex'

        # Adds Plot widget
        plot_checkbox = widgets.Checkbox(
            value=False,
            description='Use Plotting',
            indent=False,
        )
        plot_checkbox.layout.width = '18ex'
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

        plot_checkbox.observe(plot_chk_changed)

        def handle_interaction(**kwargs):

            latlon = kwargs.get('coordinates')
            # print(latlon)
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
                    xy = ee.Geometry.Point(latlon[::-1])
                    dict_values = ee_object.sample(
                        xy, scale=sample_scale).first().toDictionary().getInfo()
                    band_values = list(dict_values.values())
                    self.plot(band_names, band_values, **plot_options)
                    if plot_options['title'] == plot_layer_name:
                        del plot_options['title']
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

    def set_options(self, mapTypeId='HYBRID', styles=None, types=None):
        """Adds Google basemap and controls to the ipyleaflet map.

        Args:
            mapTypeId (str, optional): A mapTypeId to set the basemap to. Can be one of "ROADMAP", "SATELLITE", "HYBRID" or "TERRAIN" to select one of the standard Google Maps API map types. Defaults to 'HYBRID'.
            styles ([type], optional): A dictionary of custom MapTypeStyle objects keyed with a name that will appear in the map's Map Type Controls. Defaults to None.
            types ([type], optional): A list of mapTypeIds to make available. If omitted, but opt_styles is specified, appends all of the style keys to the standard Google Maps API map types.. Defaults to None.
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
        self.ee_layers.append(ee_object)
        self.ee_layer_names.append(name)

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
            centroid = ee_object.centroid()
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
        """Adds layer basemap to the map.
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


def ee_tile_layer(ee_object, vis_params={}, name='Layer untitled', shown=True, opacity=1.0):
    """Converts and Earth Engine layer to ipyleaflet TileLayer.

    Args:
        ee_object (Collection|Feature|Image|MapId): The object to add to the map.
        vis_params (dict, optional): The visualization parameters. Defaults to {}.
        name (str, optional): The name of the layer. Defaults to 'Layer untitled'.
        shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
        opacity (float, optional): The layer's opacity represented as a number between 0 and 1. Defaults to 1.
    """

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
        image = ee_object.median()

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
    url = 'https://github.com/giswqs/geemap'

    if subdir == 'source':
        url += '/tree/master/geemap/'
    elif subdir == 'examples':
        url += '/tree/master/examples'
    elif subdir == 'tutorials':
        url += '/tree/master/tutorials'

    webbrowser.open_new_tab(url)


def check_install(package):
    """Checks whether a package is installed. If not, it will install the package.

    Args:
        package (str): The name of the package to check.
    """
    import subprocess

    try:
        __import__(package)
        print('{} is already installed.'.format(package))
    except ImportError:
        print('{} is not installed. Installing ...'.format(package))
        try:
            subprocess.check_call(["python", '-m', 'pip', 'install', package])
        except Exception as e:
            print('Failed to install {}'.format(package))
            print(e)
        print("{} has been installed successfully.".format(package))


def shp_to_geojson(in_shp, out_json=None):
    """Converts a shapefile to GeoJSON.

    Args:
        in_shp (str): File path of the input shapefile.
        out_json (str, optional): File path of the output GeoJSON. Defaults to None.

    Returns:
        object: The json object representing the shapefile.
    """
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

    if not isinstance(ee_object, ee.FeatureCollection):
        print('The ee_object must be an ee.FeatureCollection.')
        return

    allowed_formats = ['csv', 'json', 'kml', 'kmz', 'shp']
    filename = os.path.abspath(filename)
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:]
    filename_shp = filename

    if filetype == 'shp':
        filename = filename.replace('.shp', '.zip')

    if not (filetype in allowed_formats):
        print('The file type must be one of the following: {}'.format(
            ', '.join(allowed_formats)))
        return

    if selectors is None:
        selectors = ee_object.first().propertyNames().getInfo()
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

        with open(filename, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=1024):
                fd.write(chunk)
    except Exception as e:
        print('An error occurred while downloading.')
        print(e)

    try:
        if filetype == 'shp':
            z = zipfile.ZipFile(filename)
            z.extractall(os.path.dirname(filename))
            os.remove(filename)
            filename = filename.replace('.zip', '.shp')

        print('Data downloaded to {}'.format(filename))
    except Exception as e:
        print(e)


def ee_to_shp(ee_object, filename, selectors=None):
    """Downloads an ee.FeatureCollection as a shapefile.

    Args:
        ee_object (object): ee.FeatureCollection
        filename (str): The output filepath of the shapefile.
        selectors (list, optional): A list of attributes to export. Defaults to None.
    """
    try:
        if  filename.endswith('.shp'):
            ee_export_vector(ee_object=ee_object, filename=filename, selectors=selectors)
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
    try:
        if  filename.endswith('.csv'):
            ee_export_vector(ee_object=ee_object, filename=filename, selectors=selectors)
        else:
            print('The filename must end with .csv')
        
    except Exception as e:
        print(e)