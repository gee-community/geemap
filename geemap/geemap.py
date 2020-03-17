"""Main module for interactive mapping using Google Earth Engine Python API and ipyleaflet.
Keep in mind that Earth Engine functions use camel case, such as setOptions(), setCenter(), centerObject(), addLayer().
ipyleaflet functions use snake case, such as add_tile_layer(), add_wms_layer(), add_minimap().
"""

import os
import ee
import ipyleaflet
from ipyleaflet import *

# Google basemaps
ee_basemaps = {
    'ROADMAP': TileLayer(
        url='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        name='Google Map',
        attribution='Google'
    ),
    'SATELLITE': TileLayer(
        url='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        name='Google Satellite',
        attribution='Google'
    ),
    'HYBRID': TileLayer(
        url='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        name='Google Satellite',
        attribution='Google'
    ),
    'TERRAIN': TileLayer(
        url='https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
        name='Google Terrain',
        attribution='Google'
    )
}


def Map(center=(40, -100), zoom=4, layers=['HYBRID']):
    """Creates an interactive ipyleaflet map. If you want more options, use ipyleaflet.Map() to create a map. 
    
    Args:
        center (tuple, optional): Initial geographic center of the map. Defaults to (40, -100).
        zoom (int, optional): Initial map zoom level. Defaults to 4.
        layers (list, optional): Tuple of layers. Defaults to ['HYBRID'].
    
    Returns:
        object: An ipyleaflet map instance.
    """    
    m = ipyleaflet.Map(center=center, zoom=zoom, scroll_wheel_zoom=True)

    m.add_control(LayersControl(position='topright'))
    m.add_control(ScaleControl(position='bottomleft'))
    m.add_control(FullScreenControl())
    m.add_control(DrawControl())

    measure = MeasureControl(
        position='bottomleft',
        active_color='orange',
        primary_length_unit='kilometers'
    )
    m.add_control(measure)

    for layer in layers:
        if layer in ee_basemaps.keys():
            m.add_layer(ee_basemaps[layer])
        else:
            print("Layer name {} is invalid. It must be one of these values: {}".format(
                layer, ", ".join(ee_basemaps.keys())))

    return m


def setOptions(self, mapTypeId='HYBRID', styles=None, types=None):
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

ipyleaflet.Map.setOptions = setOptions


def addLayer(self, ee_object, vis_params={}, name=None, shown=True, opacity=1.0):
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
        image = ee_object.median()

    map_id_dict = ee.Image(image).getMapId(vis_params)
    tile_layer = ipyleaflet.TileLayer(
        url=map_id_dict['tile_fetcher'].url_format,
        attribution='Google Earth Engine',
        name=name,
        opacity=opacity,
        visible=shown
    )
    self.add_layer(tile_layer)


ipyleaflet.Map.addLayer = addLayer


def setCenter(self, lon, lat, zoom=None):
    """Centers the map view at a given coordinates with the given zoom level.
    
    Args:
        lon (float): The longitude of the center, in degrees.
        lat (float): The latitude of the center, in degrees.
        zoom (int, optional): The zoom level, from 1 to 24. Defaults to None.
    """    
    self.center = (lat, lon)
    if zoom is not None:
        self.zoom = zoom

ipyleaflet.Map.setCenter = setCenter


def centerObject(self, ee_object, zoom=None):
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

    self.setCenter(lon, lat, zoom)

ipyleaflet.Map.centerObject = centerObject


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

ipyleaflet.Map.add_wms_layer = add_wms_layer


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


ipyleaflet.Map.add_tile_layer = add_tile_layer


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


def add_minimap(self, zoom=5, position="bottomright"):
    """Adds a minimap (overview) to the ipyleaflet map.
    
    Args:
        zoom (int, optional): Initial map zoom level. Defaults to 5.
        position (str, optional): Position of the minimap. Defaults to "bottomright".
    """
    minimap = ipyleaflet.Map(
        zoom_control=False, attribution_control=False,
        zoom=5, center=self.center, layers=[ee_basemaps['Google Map']]
    )
    minimap.layout.width = '150px'
    minimap.layout.height = '150px'
    link((minimap, 'center'), (self, 'center'))
    minimap_control = WidgetControl(widget=minimap, position=position)
    self.add_control(minimap_control)

ipyleaflet.Map.add_minimap = add_minimap


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

    return marker_cluster


ipyleaflet.Map.listening = listening
ipyleaflet.Map.last_click = []
ipyleaflet.Map.all_clicks = []


if __name__ == '__main__':

    map = Map()
    map
