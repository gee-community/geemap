# Get Started

This Get Started guide is intended as a quick way to start programming with **geemap** and the Earth Engine Python API.


## Launch Jupyter notebook

    conda activate gee
    jupyter notebook

## Import libraries

    import ee
    import geemap

## Create an interactive map

    Map = geemap.Map(center=(40, -100), zoom=4)
    Map

## Add Earth Engine data

    # Add Earth Engine dataset
    dem = ee.Image('USGS/SRTMGL1_003')
    landcover = ee.Image("ESA/GLOBCOVER_L4_200901_200912_V2_3").select('landcover')
    landsat7 = ee.Image('LE7_TOA_5YEAR/1999_2003')
    states = ee.FeatureCollection("TIGER/2018/States")

## Set visualization parameters

    dem_vis = {
    'min': 0,
    'max': 4000,
    'palette': ['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']}

    landsat_vis = {
        'min': 20, 
        'max': 200,
        'bands': ['B4', 'B3', 'B2']
    }

## Display data on the map

    Map.addLayer(dem, dem_vis, 'STRM DEM', True, 0.5)
    Map.addLayer(landcover, {}, 'Land cover')
    Map.addLayer(landsat7, landsat_vis, 'Landsat 7')
    Map.addLayer(states, {}, "US States")

## Interact with the map

Once data are added to the map, you can interact with data using vairous tools, such as the drawing tools, inspector tool, plotting tool. 
Check the video below on how to use the Inspector tool to query Earth Engine interactively. 

[![geemap](http://img.youtube.com/vi/k477ksjkaXw/0.jpg)](http://www.youtube.com/watch?v=k477ksjkaXw "inspector")
