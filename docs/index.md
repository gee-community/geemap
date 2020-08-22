# Welcome to geemap

[![image](https://colab.research.google.com/assets/colab-badge.svg)](https://gishub.org/geemap-colab)
[![image](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/giswqs/geemap/master)
[![image](https://binder.pangeo.io/badge_logo.svg)](https://binder.pangeo.io/v2/gh/giswqs/geemap/master)
[![image](https://img.shields.io/pypi/v/geemap.svg)](https://pypi.python.org/pypi/geemap)
[![image](https://img.shields.io/conda/vn/conda-forge/geemap.svg)](https://anaconda.org/conda-forge/geemap)
[![image](https://pepy.tech/badge/geemap)](https://pepy.tech/project/geemap)
[![image](https://readthedocs.org/projects/geemap/badge/?version=latest)](https://geemap.readthedocs.io/en/latest/?badge=latest)
[![image](https://img.shields.io/badge/YouTube-GEE%20Tutorials-red)](https://gishub.org/geemap)
[![image](https://img.shields.io/twitter/follow/giswqs?style=social%20%20%20%20..%20image::%20https://readthedocs.org/projects/geemap/badge/?version=latest)](https://twitter.com/giswqs)
[![image](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A Python package for interactive mapping with Google Earth Engine, ipyleaflet, and ipywidgets.**

* GitHub repo: <https://github.com/giswqs/geemap>
* Documentation: <https://geemap.readthedocs.io>
* PyPI: <https://pypi.org/project/geemap/>
* Conda-forge: <https://anaconda.org/conda-forge/geemap>
* 360+ GEE notebook examples: <https://github.com/giswqs/earthengine-py-notebooks>
* GEE Tutorials on YouTube: <https://gishub.org/geemap>
* Free software: MIT license

## Introduction

**geemap** is a Python package for interactive mapping with [Google Earth Engine](https://earthengine.google.com/) (GEE), which is a cloud computing platform with a [multi-petabyte catalog](https://developers.google.com/earth-engine/datasets/) of satellite imagery and geospatial datasets. During the past few years, GEE has become very popular in the geospatial community and it has empowered numerous environmental applications at local, regional, and global scales. GEE provides both JavaScript and Python APIs for making computational requests to the Earth Engine servers. Compared with the comprehensive [documentation](https://developers.google.com/earth-engine) and interactive IDE (i.e., [GEE JavaScript Code Editor](https://code.earthengine.google.com/)) of the GEE JavaScript API, the GEE Python API has relatively little documentation and limited functionality for visualizing results interactively. The geemap Python package was created to fill this gap. It is built upon [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet) and [ipywidgets](https://github.com/jupyter-widgets/ipywidgets), and enables users to analyze and visualize Earth Engine datasets interactively within a Jupyter-based environment.

**geemap** is intended for students and researchers, who would like to utilize the Python ecosystem of diverse libraries and tools to explore Google Earth Engine. It is also designed for existing GEE users who would like to transition from the GEE JavaScript API to Python API. The automated JavaScript-to-Python [conversion module](https://github.com/giswqs/geemap/blob/master/geemap/conversion.py) of the geemap package can greatly reduce the time needed to convert existing GEE JavaScripts to Python scripts and Jupyter notebooks.

For video tutorials and notebook examples, please visit <https://github.com/giswqs/geemap/tree/master/examples>. For complete documentation on geemap modules and methods, please visit <https://geemap.readthedocs.io/en/latest/source/geemap.html>.

If you find geemap useful in your research, please consider citing the following papers to support my work. Thank you for your support.

* Wu, Q., (2020). geemap: A Python package for interactive mapping with Google Earth Engine. The Journal of Open Source Software, 5(51), 2305. <https://doi.org/10.21105/joss.02305>
* Wu, Q., Lane, C. R., Li, X., Zhao, K., Zhou, Y., Clinton, N., DeVries, B., Golden, H. E., & Lang, M. W. (2019). Integrating LiDAR data and multi-temporal aerial imagery to map wetland inundation dynamics using Google Earth Engine. Remote Sensing of Environment, 228, 1-13. <https://doi.org/10.1016/j.rse.2019.04.015> ([pdf](https://gishub.org/2019_rse) | [source code](https://doi.org/10.6084/m9.figshare.8864921))

## Key Features

Below is a partial list of features available for the geemap package. Please check the [examples](https://github.com/giswqs/geemap/tree/master/examples) page for notebook examples, GIF animations, and video tutorials.

* Automated conversion from Earth Engine JavaScripts to Python scripts and Jupyter notebooks.
* Displaying Earth Engine data layers for interactive mapping.
* Supporting Earth Engine JavaScript API-styled functions in Python, such as `Map.addLayer()`, `Map.setCenter()`, `Map.centerObject()`, `Map.setOptions()`.
* Creating split-panel maps with Earth Engine data.
* Retrieving Earth Engine data interactively using the Inspector Tool.
* Interactive plotting of Earth Engine data by simply clicking on the map.
* Converting data format between GeoJSON and Earth Engine.
* Using drawing tools to interact with Earth Engine data.
* Using shapefiles with Earth Engine without having to upload data to one's GEE account.
* Exporting Earth Engine FeatureCollection to other formats (i.e., shp, csv, json, kml, kmz) using only one line of code.
* Exporting Earth Engine Image and ImageCollection as GeoTIFF.
* Extracting pixels from an Earth Engine Image into a 3D numpy array.
* Calculating zonal statistics by group (e.g., calculating land over composition of each state/country).
* Adding a customized legend for Earth Engine data.
* Converting Earth Engine JavaScripts to Python code directly within Jupyter notebook.
* Adding animated text to GIF images generated from Earth Engine data.
* Adding colorbar and images to GIF animations generated from Earth Engine data.
* Creating Landsat timelapse animations with animated text using Earth Engine.
* Searching places and datasets from Earth Engine Data Catalog.
* Using timeseries inspector to visualize landscape changes over time.
* Exporting Earth Engine maps as HTML files and PNG images.
* Searching Earth Engine API documentation within Jupyter notebooks.
* Importing Earth Engine assets from personal account.
* Publishing interactive GEE maps directly within Jupyter notebook.
* Adding local raster datasets (e.g., GeoTIFF) to the map.
* Performing image classification and accuracy assessment.
* Extracting pixel values interactively.