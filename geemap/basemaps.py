"""Module for basemaps. Each basemap is defined as item in the ee_basemaps dictionary. For example, to access Google basemaps, use the following:

ee_basemaps['ROADMAP'], ee_basemaps['SATELLITE'], ee_basemaps['HYBRID'].

More WMS basemaps can be found at the following websites:

1. USGS National Map: https://viewer.nationalmap.gov/services/

2. MRLC NLCD Land Cover data: https://viewer.nationalmap.gov/services/

3. FWS NWI Wetlands data: https://www.fws.gov/wetlands/Data/Web-Map-Services.html

"""

from ipyleaflet import TileLayer, WMSLayer, basemaps, basemap_to_tiles


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

    'FWS NWI Wetlands': WMSLayer(
        url='https://www.fws.gov/wetlands/arcgis/services/Wetlands/MapServer/WMSServer?',
        layers='1',
        name='FWS NWI Wetlands',
        attribution='FWS',
        format= 'image/png',
        transparent=True,
    ),

    'FWS NWI Wetlands Raster': WMSLayer(
        url='https://www.fws.gov/wetlands/arcgis/services/Wetlands_Raster/ImageServer/WMSServer?',
        layers='0',
        name='FWS NWI Wetlands Raster',
        attribution='FWS',
        format= 'image/png',
        transparent=True,
    ),

   'Google Maps': TileLayer(
        url='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attribution='Google',
        name='Google Maps'   
    ),

    'Google Satellite': TileLayer(
        url='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attribution='Google',
        name='Google Satellite',
    ),

    'Google Terrain': TileLayer(
        url='https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
        attribution='Google',
        name='Google Terrain',
    ),

    'Google Satellite Hybrid': TileLayer(
        url='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attribution='Google',
        name='Google Satellite',
    ),

    'NLCD 2016 CONUS Land Cover': WMSLayer(
        url='https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2016_Land_Cover_L48/wms?',
        layers='NLCD_2016_Land_Cover_L48',
        name='NLCD 2016 CONUS Land Cover',
        attribution='MRLC',
        format= 'image/png',
        transparent=True,
    ),     

    'NLCD 2013 CONUS Land Cover': WMSLayer(
        url='https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2013_Land_Cover_L48/wms?',
        layers='NLCD_2013_Land_Cover_L48',
        name='NLCD 2013 CONUS Land Cover',
        attribution='MRLC',
        format= 'image/png',
        transparent=True,
    ),   

    'NLCD 2011 CONUS Land Cover': WMSLayer(
        url='https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2011_Land_Cover_L48/wms?',
        layers='NLCD_2011_Land_Cover_L48',
        name='NLCD 2011 CONUS Land Cover',
        attribution='MRLC',
        format= 'image/png',
        transparent=True,
    ),   

    'NLCD 2008 CONUS Land Cover': WMSLayer(
        url='https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2008_Land_Cover_L48/wms?',
        layers='NLCD_2008_Land_Cover_L48',
        name='NLCD 2008 CONUS Land Cover',
        attribution='MRLC',
        format= 'image/png',
        transparent=True,
    ),   

    'NLCD 2006 CONUS Land Cover': WMSLayer(
        url='https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2006_Land_Cover_L48/wms?',
        layers='NLCD_2006_Land_Cover_L48',
        name='NLCD 2006 CONUS Land Cover',
        attribution='MRLC',
        format= 'image/png',
        transparent=True,
    ), 

    'NLCD 2004 CONUS Land Cover': WMSLayer(
        url='https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2004_Land_Cover_L48/wms?',
        layers='NLCD_2004_Land_Cover_L48',
        name='NLCD 2004 CONUS Land Cover',
        attribution='MRLC',
        format= 'image/png',
        transparent=True,
    ), 

    'NLCD 2001 CONUS Land Cover': WMSLayer(
        url='https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2001_Land_Cover_L48/wms?',
        layers='NLCD_2001_Land_Cover_L48',
        name='NLCD 2001 CONUS Land Cover',
        attribution='MRLC',
        format= 'image/png',
        transparent=True,
    ), 

    'USGS NAIP Imagery': WMSLayer(
        url='https://services.nationalmap.gov/arcgis/services/USGSNAIPImagery/ImageServer/WMSServer?',
        layers='0',
        name='USGS NAIP Imagery',
        attribution='USGS',
        format= 'image/png',
        transparent=True,
    ),

    'USGS Hydrography': WMSLayer(
        url='https://basemap.nationalmap.gov/arcgis/services/USGSHydroCached/MapServer/WMSServer?',
        layers='0',
        name='USGS Hydrography',
        attribution='USGS',
        format= 'image/png',
        transparent=True,
    ),

    'USGS 3DEP Elevation': WMSLayer(
        url='https://elevation.nationalmap.gov/arcgis/services/3DEPElevation/ImageServer/WMSServer?',
        layers='3DEPElevation:None',
        name='USGS 3DEP Elevation',
        attribution='USGS',
        format= 'image/png',
        transparent=True,
    )

}

# Adds ipyleaflet basemaps 
for item in basemaps.values():
    try:
        name = item['name']
        basemap = 'basemaps.{}'.format(name)
        ee_basemaps[name] = basemap_to_tiles(eval(basemap))
    except:
        for sub_item in item:
            name = item[sub_item]['name']
            basemap = 'basemaps.{}'.format(name)
            basemap = basemap.replace('Mids', 'Modis')
            ee_basemaps[name] = basemap_to_tiles(eval(basemap))

