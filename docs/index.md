# Welcome to geemap

[![image](https://colab.research.google.com/assets/colab-badge.svg)](https://gishub.org/geemap-colab)
[![image](https://binder.pangeo.io/badge_logo.svg)](https://binder.pangeo.io/v2/gh/giswqs/geemap/master)
[![image](https://img.shields.io/pypi/v/geemap.svg)](https://pypi.python.org/pypi/geemap)
[![image](https://img.shields.io/conda/vn/conda-forge/geemap.svg)](https://anaconda.org/conda-forge/geemap)
[![image](https://pepy.tech/badge/geemap)](https://pepy.tech/project/geemap)
[![image](https://github.com/giswqs/geemap/workflows/docs/badge.svg)](https://geemap.org)
[![image](https://github.com/giswqs/geemap/workflows/build/badge.svg)](https://github.com/giswqs/geemap/actions?query=workflow%3Abuild)
[![image](https://img.shields.io/badge/YouTube-Channel-red)](https://www.youtube.com/c/QiushengWu)
[![image](https://img.shields.io/twitter/follow/giswqs?style=social)](https://twitter.com/giswqs)
[![image](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A Python package for interactive mapping with Google Earth Engine, ipyleaflet, and ipywidgets.**

* GitHub repo: <https://github.com/giswqs/geemap>
* Documentation: <https://geemap.org>
* PyPI: <https://pypi.org/project/geemap>
* Conda-forge: <https://anaconda.org/conda-forge/geemap>
* 360+ GEE notebook examples: <https://github.com/giswqs/earthengine-py-notebooks>
* GEE Tutorials on YouTube: <https://www.youtube.com/c/QiushengWu>
* Free software: [MIT license](https://opensource.org/licenses/MIT)

## Introduction

**geemap** is a Python package for interactive mapping with [Google Earth Engine](https://earthengine.google.com/) (GEE), which is a cloud computing platform with a [multi-petabyte catalog](https://developers.google.com/earth-engine/datasets/) of satellite imagery and geospatial datasets. During the past few years, GEE has become very popular in the geospatial community and it has empowered numerous environmental applications at local, regional, and global scales. GEE provides both JavaScript and Python APIs for making computational requests to the Earth Engine servers. Compared with the comprehensive [documentation](https://developers.google.com/earth-engine) and interactive IDE (i.e., [GEE JavaScript Code Editor](https://code.earthengine.google.com/)) of the GEE JavaScript API, the GEE Python API has relatively little documentation and limited functionality for visualizing results interactively. The geemap Python package was created to fill this gap. It is built upon [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet) and [ipywidgets](https://github.com/jupyter-widgets/ipywidgets), and enables users to analyze and visualize Earth Engine datasets interactively within a Jupyter-based environment.

**geemap** is intended for students and researchers, who would like to utilize the Python ecosystem of diverse libraries and tools to explore Google Earth Engine. It is also designed for existing GEE users who would like to transition from the GEE JavaScript API to Python API. The automated JavaScript-to-Python [conversion module](https://github.com/giswqs/geemap/blob/master/geemap/conversion.py) of the geemap package can greatly reduce the time needed to convert existing GEE JavaScripts to Python scripts and Jupyter notebooks.

For video tutorials and notebook examples, please visit the [examples page](https://github.com/giswqs/geemap/tree/master/examples). For complete documentation on geemap modules and methods, please visit the [API Reference](https://geemap.org/geemap/).

If you find geemap useful in your research, please consider citing the following papers to support my work. Thank you for your support.

* Wu, Q., (2020). geemap: A Python package for interactive mapping with Google Earth Engine. The Journal of Open Source Software, 5(51), 2305. <https://doi.org/10.21105/joss.02305>
* Wu, Q., Lane, C. R., Li, X., Zhao, K., Zhou, Y., Clinton, N., DeVries, B., Golden, H. E., & Lang, M. W. (2019). Integrating LiDAR data and multi-temporal aerial imagery to map wetland inundation dynamics using Google Earth Engine. Remote Sensing of Environment, 228, 1-13. <https://doi.org/10.1016/j.rse.2019.04.015> ([pdf](https://gishub.org/2019_rse) | [source code](https://doi.org/10.6084/m9.figshare.8864921))

## Key Features

Below is a partial list of features available for the geemap package. Please check the [examples](https://github.com/giswqs/geemap/tree/master/examples) page for notebook examples, GIF animations, and video tutorials.

* Convert Earth Engine JavaScripts to Python scripts and Jupyter notebooks.
* Display Earth Engine data layers for interactive mapping.
* Support Earth Engine JavaScript API-styled functions in Python, such as `Map.addLayer()`, `Map.setCenter()`, `Map.centerObject()`, `Map.setOptions()`.
* Create split-panel maps with Earth Engine data.
* Retrieve Earth Engine data interactively using the Inspector Tool.
* Interactive plotting of Earth Engine data by simply clicking on the map.
* Convert data format between GeoJSON and Earth Engine.
* Use drawing tools to interact with Earth Engine data.
* Use shapefiles with Earth Engine without having to upload data to one's GEE account.
* Export Earth Engine FeatureCollection to other formats (i.e., shp, csv, json, kml, kmz).
* Export Earth Engine Image and ImageCollection as GeoTIFF.
* Extract pixels from an Earth Engine Image into a 3D numpy array.
* Calculate zonal statistics by group.
* Add a customized legend for Earth Engine data.
* Convert Earth Engine JavaScripts to Python code directly within Jupyter notebook.
* Add animated text to GIF images generated from Earth Engine data.
* Add colorbar and images to GIF animations generated from Earth Engine data.
* Create Landsat timelapse animations with animated text using Earth Engine.
* Search places and datasets from Earth Engine Data Catalog.
* Use timeseries inspector to visualize landscape changes over time.
* Export Earth Engine maps as HTML files and PNG images.
* Search Earth Engine API documentation within Jupyter notebooks.
* Import Earth Engine assets from personal account.
* Publish interactive GEE maps directly within Jupyter notebook.
* Add local raster datasets (e.g., GeoTIFF) to the map.
* Perform image classification and accuracy assessment.
* Extract pixel values interactively and export as shapefile and csv.

## YouTube Channel

I have created a [YouTube Channel](https://www.youtube.com/c/QiushengWu) for sharing **geemap** tutorials. You can subscribe to my channel for regular updates. If there is any specific tutorial you would like to see, please submit a feature request [here](https://github.com/giswqs/geemap/issues). 

[![Earth Engine Tutorials on YouTube](https://wetlands.io/file/images/youtube.png)](https://www.youtube.com/c/QiushengWu)
