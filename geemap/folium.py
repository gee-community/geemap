# -*- coding: utf-8 -*-

"""Main module."""

import os
import ee
import folium
from folium import plugins

# Add Earth Engine layer to folium
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
    folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Google Earth Engine',
        name=name,
        overlay=True,
        control=True,
        show=shown,
        opacity=opacity
    ).add_to(self)

folium.Map.addLayer = addLayer

# Add custom WMS tile layer to folium
def addWmsTileLayer(self, url, layers, name=None, attr='', overlay=True, control=True, show=True):
    try:
        folium.raster_layers.WmsTileLayer(
            url=url,
            layers=layers,
            attr=attr,
            name=name,
            overlay=overlay,
            control=control,
            show=show
        ).add_to(self)
    except:
        print("Failed to add the specified WMS TileLayer.")

folium.Map.addWmsTileLayer = addWmsTileLayer


# Add custom tile layer to folium
def addTileLayer(self, tiles='OpenStreetMap', name=None, attr='', overlay=True, control=True, show=True, opacity=1, API_key=None):
    try:
        folium.raster_layers.TileLayer(
            tiles=tiles,
            name=name,
            attr=attr,
            overlay=overlay,
            control=control,
            show=show,
            opacity=opacity,
            API_key=API_key
        ).add_to(self)
    except:
        print("Failed to add the specified TileLayer.")

folium.Map.addTileLayer = addTileLayer


# https://viewer.nationalmap.gov/services/
# Modifies the Google Maps basemap
# A mapTypeId to set the basemap to. Can be one of "ROADMAP", "SATELLITE", "HYBRID" or "TERRAIN" to select one of the standard Google Maps API map types
def setOptions(self, mapTypeId='HYBRID', styles={}, types=[]):
    # Add custom basemaps to folium
    basemaps = {
        'ROADMAP': folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Maps',
            overlay=True,
            control=True
        ),
        'SATELLITE': folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Satellite',
            overlay=True,
            control=True
        ),
        'TERRAIN': folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Terrain',
            overlay=True,
            control=True
        ),
        'HYBRID': folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Satellite',
            overlay=True,
            control=True
        ),
        'ESRI': folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Satellite',
            overlay=True,
            control=True
        ),
        'Esri Ocean': folium.TileLayer(
            tiles='https://services.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Ocean',
            overlay=True,
            control=True
        ),
        'Esri Satellite': folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Satellite',
            overlay=True,
            control=True
        ),
         'Esri Standard': folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Standard',
            overlay=True,
            control=True
        ),
        'Esri Terrain': folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Terrain',
            overlay=True,
            control=True
        ),
        'Esri Transportation': folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Transportation',
            overlay=True,
            control=True
        ),

        'Esri Topo World': folium.TileLayer(
            tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Topo World',
            overlay=True,
            control=True
        ),

        'Esri National Geographic': folium.TileLayer(
            tiles='http://services.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri National Geographic',
            overlay=True,
            control=True
        ),     

        'Esri Shaded Relief': folium.TileLayer(
            tiles='https://services.arcgisonline.com/arcgis/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Shaded Relief',
            overlay=True,
            control=True
        ),   

         'Esri Physical Map': folium.TileLayer(
            tiles='https://services.arcgisonline.com/arcgis/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Physical Map',
            overlay=True,
            control=True
        ),   

        'Bing VirtualEarth': folium.TileLayer(
            tiles='http://ecn.t3.tiles.virtualearth.net/tiles/a{q}.jpeg?g=1',
            attr='Microsoft',
            name='Bing VirtualEarth',
            overlay=True,
            control=True
        ),

        '3DEP Elevation': folium.WmsTileLayer(
            url='https://elevation.nationalmap.gov/arcgis/services/3DEPElevation/ImageServer/WMSServer?',
            layers = '3DEPElevation:None',
            attr='USGS',
            name='3DEP Elevation',
            overlay=True,
            control=True
        ),    

        'NAIP Imagery': folium.WmsTileLayer(
            url='https://services.nationalmap.gov/arcgis/services/USGSNAIPImagery/ImageServer/WMSServer?',
            layers = '0',
            attr='USGS',
            name='NAIP Imagery',
            overlay=True,
            control=True
        ),           
    }

    try:
        basemaps[mapTypeId].add_to(self)
    except:
        print('Basemap can only be one of "ROADMAP", "SATELLITE", "HYBRID", "TERRAIN", "NAIP", or "ESRI"')


folium.Map.setOptions = setOptions

# show the map



def setControlVisibility(self, layerControl=True, fullscreenControl=True, latLngPopup=True):

    if layerControl:
        folium.LayerControl().add_to(self)
    if fullscreenControl:
        plugins.Fullscreen().add_to(self)
    if latLngPopup:
        folium.LatLngPopup().add_to(self)


folium.Map.setControlVisibility = setControlVisibility


def setCenter(self, lon, lat, zoom=10):
    self.fit_bounds([[lat, lon], [lat, lon]], max_zoom=zoom)


folium.Map.setCenter = setCenter


def centerObject(self, ee_object, zoom=10):
    # try:

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

    self.fit_bounds(bounds, max_zoom=zoom)

    # except:
    #     print("Failed to centerObject")


folium.Map.centerObject = centerObject


if __name__ == '__main__':

    ee.Initialize()

    dem = ee.Image('USGS/SRTMGL1_003')
    # Set visualization parameters.
    vis_params = {
        'min': 0,
        'max': 4000,
        'palette': ['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']}

    # Create a folium map object.
    Map = folium.Map(location=[20, 0], zoom_start=3, height=500)

    # # Add custom basemaps
    # basemaps['Google Maps'].add_to(my_map)
    # basemaps['Google Satellite Hybrid'].add_to(my_map)

    # Add the elevation model to the map object.
    Map.addLayer(dem.updateMask(dem.gt(0)), vis_params, 'DEM')

    # Add a layer control panel to the map.
    Map.add_child(folium.LayerControl())

    # Add fullscreen button
    plugins.Fullscreen().add_to(Map)

    # Display the map.
    # display(my_map)
    Map
    print("Testing done")
