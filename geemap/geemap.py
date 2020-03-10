"""Main module."""

import os
import ee
import ipyleaflet
from ipyleaflet import *

# Create an ipyleaflet map instance
def Map(center=(40, -100), zoom=4, layers=None):
    m = ipyleaflet.Map(center=center, zoom=zoom, scroll_wheel_zoom=True)

    m.add_control(LayersControl(position='topright'))
    m.add_control(ScaleControl(position='bottomleft'))
    m.add_control(FullScreenControl())
    m.add_control(DrawControl())

    measure = MeasureControl(
        position='bottomleft',
        active_color = 'orange',
        primary_length_unit = 'kilometers'
    )
    m.add_control(measure)

    if layers is None:
        tile_layer = ipyleaflet.TileLayer(
            url='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
            attribution='Google',
            name='Google Satellite'
        )
        m.add_layer(tile_layer)
    else:
        m.add_layer(layers)

    return m


# Add Earth Engine layer to map
def addLayer(self, ee_object, vis_params={}, name='Layer untitled', shown=True, opacity=1):

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
        # visible=shown
    )
    self.add_layer(tile_layer)

ipyleaflet.Map.addLayer = addLayer


# Set map center
def setCenter(self, lon, lat, zoom=None):
    self.center = (lat, lon)
    if zoom is not None:
        self.zoom = zoom

ipyleaflet.Map.setCenter = setCenter


# Center the map based on an object
def centerObject(self, ee_object, zoom=None):

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


# Add custom WMS tile layer to map
def addWmsTileLayer(self, url, layers, name=None, attribution='', format='image/jpeg', transparent=False, opacity=1.0):

    if name is None:
        name = str(layers)

    try:
        wms_layer = ipyleaflet.WMSLayer(
            url=url,
            layers=layers,
            name=name,
            attribution=attribution,
            format=format,
            transparent =transparent,
            opacity=opacity
        )
        self.add_layer(wms_layer)
    except:
        print("Failed to add the specified WMS TileLayer.")

ipyleaflet.Map.addWmsTileLayer = addWmsTileLayer


# Add custom tile layer to map
def addTileLayer(self, url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', name=None, attribution='', opacity=1):
    try:
        tile_lyaer = ipyleaflet.TileLayer(
            url=url,
            name=name,
            attribution=attribution,
            opacity=opacity
        )
        self.add_layer(tile_lyaer)
    except:
        print("Failed to add the specified TileLayer.")

ipyleaflet.Map.addTileLayer = addTileLayer


def listening(self, event='click', add_marker=True):

    coordinates = []
    
    def handle_interaction(**kwargs):
        latlon = kwargs.get('coordinates')

        if event == 'click' and kwargs.get('type') == 'click':
            coordinates.append(latlon)
            self.last_click = latlon
            self.all_clicks = coordinates
            if add_marker:
                self.add_layer(Marker(location=latlon))
        elif kwargs.get('type') == 'mousemove':
            pass
    
    self.on_interaction(handle_interaction)

ipyleaflet.Map.listening = listening
ipyleaflet.Map.last_click = []
ipyleaflet.Map.all_clicks = []

    
if __name__ == '__main__':

    map = Map()
    map