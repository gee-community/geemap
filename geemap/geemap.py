"""Main module for interactive mapping using Google Earth Engine Python API and ipyleaflet.
Keep in mind that Earth Engine functions use camel case, such as setOptions(), setCenter(), centerObject(), addLayer().
ipyleaflet functions use snake case, such as add_tile_layer(), add_wms_layer(), add_minimap().
"""

import ee
import ipyleaflet
import math
import os
import webbrowser
from ipyleaflet import *
import ipywidgets as widgets


# More WMS basemaps can be found at https://viewer.nationalmap.gov/services/
ee_basemaps = {
    'ROADMAP': TileLayer(
        url='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attribution='Google',
        name='Google Maps'   
    ),

    'SATELLITE': TileLayer(
        url='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attribution='Google',
        name='Google Satellite',
    ),

    'TERRAIN': TileLayer(
        url='https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
        attribution='Google',
        name='Google Terrain',
    ),

    'HYBRID': TileLayer(
        url='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attribution='Google',
        name='Google Satellite',
    ),

    'ESRI': TileLayer(
        url='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attribution='Esri',
        name='Esri Satellite',       
    ),

    'Esri Ocean': TileLayer(
        url='https://services.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
        attribution='Esri',
        name='Esri Ocean', 
    ),

    'Esri Satellite': TileLayer(
        url='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attribution='Esri',
        name='Esri Satellite',  
    ),

    'Esri Standard': TileLayer(
        url='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        attribution='Esri',
        name='Esri Standard',
    ),

    'Esri Terrain': TileLayer(
        url='https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}',
        attribution='Esri',
        name='Esri Terrain',
    ),

    'Esri Transportation': TileLayer(
        url='https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}',
        attribution='Esri',
        name='Esri Transportation',
    ),

    'Esri Topo World': TileLayer(
        url='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        attribution='Esri',
        name='Esri Topo World',
    ),

    'Esri National Geographic': TileLayer(
        url='http://services.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}',
        attribution='Esri',
        name='Esri National Geographic',
    ),     

    'Esri Shaded Relief': TileLayer(
        url='https://services.arcgisonline.com/arcgis/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}',
        attribution='Esri',
        name='Esri Shaded Relief',      
    ),   

    'Esri Physical Map': TileLayer(
        url='https://services.arcgisonline.com/arcgis/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}',
        attribution='Esri',
        name='Esri Physical Map',
    ),   

    'Bing VirtualEarth': TileLayer(
        url='http://ecn.t3.tiles.virtualearth.net/tiles/a{q}.jpeg?g=1',
        attribution='Microsoft',
        name='Bing VirtualEarth',
    )
}


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
        self.scroll_wheel_zoom= True
        self.layout.height = '550px'

        layer_control = LayersControl(position='topright')       
        self.add_control(layer_control)
        self.layer_control = layer_control

        scale =ScaleControl(position='bottomleft')
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

        draw_control = DrawControl(marker={'shapeOptions': {'color': '#0000FF'}},
                 rectangle={'shapeOptions': {'color': '#0000FF'}},
                 circle={'shapeOptions': {'color': '#0000FF'}},
                 circlemarker={},
                 )

        self.draw_count = 0  # The number of shapes drawn by the user using the DrawControl
        self.draw_features = [] # The list of Earth Engine Geometry objects converted from geojson
        self.draw_last_feature = None # The Earth Engine Geometry object converted from the last drawn feature

        # Handles draw events
        def handle_draw(target, action, geo_json):
            try:
                self.draw_count += 1
                geom = geojson_to_ee(geo_json, False)
                feature = ee.Feature(geom)
                self.draw_last_feature = feature
                self.draw_features.append(feature)
                collection = ee.FeatureCollection(self.draw_features)
                
                if self.draw_count > 1:
                    self.layers = self.layers[:-1]

                self.addLayer(collection, {'color': 'blue'}, 'Drawing Features', True, 0.5)
                draw_control.clear()
            except:
                print("There was an error creating Earth Engine Feature.")
                self.draw_count = 0
                self.draw_features = []
                self.draw_last_feature = None

        draw_control.on_draw(handle_draw)
        self.add_control(draw_control)
        self.draw_control = draw_control

        # Adds Inspector widget
        checkbox = widgets.Checkbox(
            value=False,
            description='Use Inspector',
            indent=False
        )
        checkbox.layout.width='18ex'
        chk_control = WidgetControl(widget=checkbox, position='topright')
        self.add_control(chk_control)
        self.inspector_control = chk_control

        self.inspector_checked = checkbox.value

        def checkbox_changed(b):
            self.inspector_checked = checkbox.value
            if not self.inspector_checked:
                output.clear_output()
        checkbox.observe(checkbox_changed)

        output = widgets.Output(layout={'border': '1px solid black'})
        output_control = WidgetControl(widget=output, position='topright')
        self.add_control(output_control)

        self.ee_layers = []
        self.ee_layer_names = []        
        self.add_layer(ee_basemaps['HYBRID']) 

        def handle_interaction(**kwargs):

            latlon = kwargs.get('coordinates')
            if kwargs.get('type') == 'click' and self.inspector_checked:
                self.default_style = {'cursor': 'wait'}

                scale = self.getScale()
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
                                item = ee_object.reduceRegion(ee.Reducer.first(), xy, scale).getInfo()
                                b_name = 'band'
                                if len(item) > 1:
                                    b_name = 'bands'
                                print("{}: {} ({} {})".format(layer_name, object_type, len(item), b_name))
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
                                    print("{}: Feature ({} {})".format(layer_name, len(props), b_name))
                                    keys = props.keys()
                                    for key in keys:
                                        print("  {}: {}".format(key, props[key]))     
                        except:
                            pass                       

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
        except:
            print('Google basemaps can only be one of "ROADMAP", "SATELLITE", "HYBRID" or "TERRAIN".')

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
            visible=shown
        )
        self.ee_layers.append(ee_object)
        self.ee_layer_names.append(name)
        self.add_layer(tile_layer)

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
        except:
            print('Basemap can only be one of the following: {}'.format(', '.join(ee_basemaps.keys())))


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
                visible=shown
            )
            self.add_layer(wms_layer)
        except:
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
                visible=shown
            )
            self.add_layer(tile_layer)
        except:
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


    def listening(self, event='click', add_marker=True):
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
                    # self.add_layer(Marker(location=latlon))
                    # self.clear_layers()
                    # self.add_layer(marker_cluster)
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

            control = ipyleaflet.SplitMapControl(left_layer=left_layer, right_layer=right_layer)
            self.add_control(control)

        except:
            print('The provided layers are invalid!')
            

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
        visible=shown
    )
    return tile_layer


def geojson_to_ee(geo_json, geodesic=True):
    """Converts a geojson to ee.Geometry()
    
    Args:
        geo_json (dict): A geojson geometry dictionary.
    
    Returns:
        ee_object: An ee.Geometry object
    """    
    try:
        geom = None
        keys = geo_json['properties']['style'].keys()
        if 'radius' in keys: # Checks whether it is a circle
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

    except:
        print("Could not convert the geojson to ee.Geometry()")


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


