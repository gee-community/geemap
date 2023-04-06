---
title: "geemap: A Python package for interactive mapping with Google Earth Engine"
tags:
    - Python
    - Google Earth Engine
    - ipyleaflet
    - mapping
    - Jupyter notebook
authors:
    - name: Qiusheng Wu
      orcid: 0000-0001-5437-4073
      affiliation: "1"
affiliations:
    - name: Department of Geography, University of Tennessee, Knoxville, TN 37996, United States
      index: 1
date: 21 May 2020
bibliography: paper.bib
---

# Summary

**geemap** is a Python package for interactive mapping with [Google Earth Engine](https://earthengine.google.com/) (GEE),
which is a cloud computing platform with a [multi-petabyte catalog](https://developers.google.com/earth-engine/datasets/)
of satellite imagery and geospatial datasets (e.g., Landsat, Sentinel, MODIS, NAIP) [@Gorelick2017]. During the past few years,
GEE has become very popular in the geospatial community and it has empowered numerous environmental applications at local, regional,
and global scales. Some of the notable environmental applications include mapping global forest change [@Hansen2013],
global urban change [@Liu2020], global surface water change [@Pekel2016], wetland inundation dynamics [@Wu2019], vegetation
phenology [@Li2019], and time series analysis [@Kennedy2018].

GEE provides both JavaScript and Python APIs for making computational requests to the Earth Engine servers.
Compared with the comprehensive [documentation](https://earthengine.google.com/) and interactive IDE
(i.e., [GEE JavaScript Code Editor](https://code.earthengine.google.com/)) of the GEE JavaScript API, the
GEE Python API lacks good documentation and lacks functionality for visualizing results interactively.
The **geemap** Python package is created to fill this gap. It is built upon
[ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet) and [ipywidgets](https://github.com/jupyter-widgets/ipywidgets),
enabling GEE users to analyze and visualize Earth Engine datasets interactively with Jupyter notebooks.

# geemap Audience

**geemap** is intended for students and researchers who would like to utilize the Python ecosystem of diverse libraries and
tools to explore Google Earth Engine. It is also designed for existing GEE users who would like to transition from the GEE
JavaScript API to a Python API. The automated JavaScript-to-Python [conversion module](https://github.com/gee-community/geemap/blob/master/geemap/conversion.py)
of the **geemap** package can greatly reduce the time needed to convert existing GEE JavaScripts to Python scripts and Jupyter notebooks.

# geemap Functionality

The interactive mapping functionality of the **geemap** package is built upon [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet) and [folium](https://github.com/python-visualization/folium), both of which rely on Jupyter notebooks for creating interactive maps. A key difference between ipyleaflet and folium is that ipyleaflet is built upon ipywidgets and allows bidirectional communication between the frontend and the backend, enabling the use of the map to capture user input, while folium is meant for displaying static data only [@QuantStack2019]. It should be noted that [Google Colab](https://colab.research.google.com/) currently does not support ipyleaflet. Therefore, if one wants to use **geemap** on Google Colab, one should `import geemap.foliumap as geemap`, which provides limited interactive mapping functionality. To utilize the full interactive mapping functionality of **geemap**, one should `import geemap` on a local computer or secured server with Jupyter notebook installed.

The key functionality of **geemap** is organized into several modules:

-   [geemap](https://geemap.readthedocs.io/en/latest/source/geemap.html#module-geemap.geemap): the main module for interactive mapping with Google Earth Engine, ipyleaflet, and ipywidgets.

-   [foliumap](https://geemap.readthedocs.io/en/latest/source/geemap.html#module-geemap.foliumap): a module for interactive mapping with Earth Engine and folium. It is designed for users to run geemap with Google Colab.

-   [conversion](https://geemap.readthedocs.io/en/latest/source/geemap.html#module-geemap.conversion): utilities for automatically converting Earth Engine JavaScripts to Python scripts and Jupyter notebooks.

-   [basemaps](https://geemap.readthedocs.io/en/latest/source/geemap.html#module-geemap.basemaps): a module for adding various XYZ and WMS tiled basemaps.

-   [legends](https://geemap.readthedocs.io/en/latest/source/geemap.html#module-geemap.legends): a module for adding customized legends to interactive maps.

# geemap Tutorials

Various tutorials and documentation are available for using **geemap**, including:

-   [20+ video tutorials with corresponding notebook examples](https://github.com/gee-community/geemap/tree/master/examples)
-   [360+ Jupyter notebook examples for using Google Earth Engine](https://github.com/giswqs/earthengine-py-notebooks)
-   [Complete documentation on geemap modules and methods](https://geemap.readthedocs.io/en/latest/source/geemap.html)

# Acknowledgements

The author would like to thank the developers of ipyleaflet and ipywidgets, which empower the interactive mapping functionality of **geemap**, including [Martin Renou](https://github.com/martinRenou), [Sylvain Corlay](https://github.com/SylvainCorlay), and [David Brochart](https://github.com/davidbrochart). The author would also like to acknowledge source code contributions from [Justin Braaten](https://github.com/jdbcode), [Cesar Aybar](https://github.com/csaybar), [Oliver Burdekin](https://github.com/Ojaybee), [Diego Garcia Diaz](https://github.com/Digdgeo), and [Stephan Büttig](https://twitter.com/stephan_buettig).

# References
