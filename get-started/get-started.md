# Get Started

This Get Started guide is intended as a quick way to start programming with **geemap** and the Earth Engine Python API.

## Plotting backends

**Geemap** has six plotting backends, including [folium](https://github.com/python-visualization/folium), [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet), [plotly](https://plotly.com/), [pydeck](https://deckgl.readthedocs.io/en/latest/), [kepler.gl](https://docs.kepler.gl/docs/keplergl-jupyter), and [heremap](https://github.com/heremaps/here-map-widget-for-jupyter). An interactive map created using one of the plotting backends can be displayed in a Jupyter environment, such as Google Colab, Jupyter Notebook, and JupyterLab. By default, `import geemap` will use the `ipyleaflet` plotting backend.

The six plotting backends do not offer equal functionality. The `ipyleaflet` plotting backend provides the richest interactive functionality, including the custom toolset for loading, analyzing, and visualizing geospatial data interactively without coding. For example, users can add vector data (e.g., GeoJSON, Shapefile, KML, GeoDataFrame) and raster data (e.g., GeoTIFF, Cloud Optimized GeoTIFF [COG]) to the map with a few clicks (see Figure 1). Users can also perform geospatial analysis using the WhiteboxTools GUI with 468 geoprocessing tools directly within the map interface (see Figure 2). Other interactive functionality (e.g., split-panel map, linked map, time slider, time-series inspector) can also be useful for visualizing geospatial data. The `ipyleaflet` package is built upon `ipywidgets` and allows bidirectional communication between the front-end and the backend enabling the use of the map to capture user input ([source](https://blog.jupyter.org/interactive-gis-in-jupyter-with-ipyleaflet-52f9657fa7a)). In contrast, `folium` has relatively limited interactive functionality. It is meant for displaying static data only. Note that the aforementioned custom toolset and interactive functionality are not available for other plotting backends. Compared with `ipyleaflet` and `folium`, the `pydeck`, `kepler.gl`, and `heremap` plotting backend provides some unique 3D mapping functionality. An [API key](https://developer.here.com/documentation/identity-access-management/dev_guide/topics/dev-apikey.html) from the [Here Developer Portal](https://developer.here.com/) is required to use `heremap`.

To choose a specific plotting backend, use one of the following:

-   `import geemap.geemap as geemap`
-   `import geemap.foliumap as geemap`
-   `import geemap.deck as geemap`
-   `import geemap.kepler as geemap`
-   `import geemap.plotlymap as geemap`
-   `import geemap.heremap as geemap`

## Launch Jupyter notebook

```bash
conda activate gee
jupyter notebook
```

## Import libraries

```python
import ee
import geemap
```

## Create an interactive map

```python
Map = geemap.Map(center=(40, -100), zoom=4)
Map
```

## Use basemaps

Basemaps can be added to the map using the `add_basemap()` function. The default basemap is `OpenStreetMap`.

```python
Map = geemap.Map()
Map.add_basemap("Esri.WorldImagery")
Map.add_basemap("OpenTopoMap")
Map
```

All Google basemaps have been removed from the geemap since [v0.26.0](https://geemap.org/changelog/#v0270-sep-21-2023) to comply with Google Maps' terms of service. Users can choose to add Google basemaps at their own risks by setting environment variables as follows. If no env variables are detected, Esri basemaps will be used.

```python
import os

os.environ["ROADMAP"] = 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
os.environ["SATELLITE"] = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
os.environ["TERRAIN"] = 'https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}'
os.environ["HYBRID"] = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}'

Map = geemap.Map()
Map.add_basemap("HYBRID")
Map
```

## Add Earth Engine data

```python
dem = ee.Image('USGS/SRTMGL1_003')
landcover = ee.Image("ESA/GLOBCOVER_L4_200901_200912_V2_3").select('landcover')
landsat7 = ee.Image('LANDSAT/LE7_TOA_5YEAR/1999_2003')
states = ee.FeatureCollection("TIGER/2018/States")
```

## Set visualization parameters

```python
dem_vis = {
'min': 0,
'max': 4000,
'palette': ['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']}

landsat_vis = {
    'min': 20,
    'max': 200,
    'bands': ['B4', 'B3', 'B2']
}
```

## Display data on the map

```python
Map.addLayer(dem, dem_vis, 'SRTM DEM', True, 0.5)
Map.addLayer(landcover, {}, 'Land cover')
Map.addLayer(landsat7, landsat_vis, 'Landsat 7')
Map.addLayer(states, {}, "US States")
```

## Interact with the map

Once data are added to the map, you can interact with data using various tools, such as the drawing tools, inspector tool, plotting tool.
Check the video below on how to use the Inspector tool to query Earth Engine interactively.

[![geemap](https://img.youtube.com/vi/k477ksjkaXw/0.jpg)](https://www.youtube.com/watch?v=k477ksjkaXw "inspector")
