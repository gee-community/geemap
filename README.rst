======
geemap
======

.. image:: https://colab.research.google.com/assets/colab-badge.svg
        :target: https://colab.research.google.com/github/gee-community/geemap/blob/master/docs/notebooks/00_geemap_colab.ipynb

.. image:: https://mybinder.org/badge_logo.svg
        :target: https://mybinder.org/v2/gh/gee-community/geemap/master?labpath=docs%2Fnotebooks%2F00_geemap_colab.ipynb

.. image:: https://studiolab.sagemaker.aws/studiolab.svg
        :target: https://studiolab.sagemaker.aws/import/github/gee-community/geemap/blob/master/docs/notebooks/00_geemap_colab.ipynb

.. image:: https://img.shields.io/pypi/v/geemap.svg
        :target: https://pypi.python.org/pypi/geemap

.. image:: https://static.pepy.tech/badge/geemap
        :target: https://pepy.tech/project/geemap

.. image:: https://img.shields.io/badge/recipe-geemap-green.svg
        :target: https://github.com/giswqs/geemap-feedstock

.. image:: https://img.shields.io/conda/vn/conda-forge/geemap.svg
        :target: https://anaconda.org/conda-forge/geemap

.. image:: https://img.shields.io/conda/dn/conda-forge/geemap.svg
        :target: https://anaconda.org/conda-forge/geemap

.. image:: https://github.com/gee-community/geemap/workflows/docs/badge.svg
        :target: https://geemap.org

.. image:: https://img.shields.io/badge/YouTube-Channel-red   
        :target: https://youtube.com/@giswqs

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
        :target: https://opensource.org/licenses/MIT

.. image:: https://img.shields.io/badge/Donate-Buy%20me%20a%20coffee-yellowgreen.svg
        :target: https://www.buymeacoffee.com/giswqs

.. image:: https://joss.theoj.org/papers/10.21105/joss.02305/status.svg
        :target: https://joss.theoj.org/papers/10.21105/joss.02305

.. image:: https://badges.gitter.im/Join%20Chat.svg
        :target: https://matrix.to/#/#geemap:gitter.im       

**A Python package for interactive geospatial analysis and visualization with Google Earth Engine.**

* GitHub repo: https://github.com/gee-community/geemap
* Documentation: https://geemap.org
* PyPI: https://pypi.org/project/geemap/
* Conda-forge: https://anaconda.org/conda-forge/geemap
* 360+ GEE notebook examples: https://github.com/giswqs/earthengine-py-notebooks
* GEE Tutorials on YouTube: https://youtube.com/@giswqs
* Free software: MIT license

**Acknowledgment:** The geemap project is supported by the National Aeronautics and Space Administration (NASA) under Grant No. 80NSSC22K1742 issued through the `Open Source Tools, Frameworks, and Libraries 2020 Program <https://bit.ly/3RVBRcQ>`__.

**Contents**

- `Announcement`_
- `Introduction`_
- `Features`_
- `Installation`_
- `Citations`_


Announcement
------------

The book **Earth Engine and Geemap: Geospatial Data Science with Python**, written by `Qiusheng Wu <https://gishub.org>`__, has been published by Locate Press in July 2023. If you’re interested in
purchasing the book, please visit this URL: https://locatepress.com/book/gee.

.. figure:: https://images.geemap.org/book.png
   :alt: book


Introduction
------------

**Geemap** is a Python package for geospatial analysis and visualization with `Google Earth Engine <https://earthengine.google.com/>`__ (GEE), which is a cloud computing platform with a `multi-petabyte catalog <https://developers.google.com/earth-engine/datasets/>`__ of satellite imagery and geospatial datasets. During the past few years, 
GEE has become very popular in the geospatial community and it has empowered numerous environmental applications at local, regional, and global scales. GEE provides both JavaScript and Python APIs for 
making computational requests to the Earth Engine servers. Compared with the comprehensive `documentation <https://developers.google.com/earth-engine>`__ and interactive IDE (i.e., `GEE JavaScript Code Editor <https://code.earthengine.google.com/>`__) of the GEE JavaScript API, 
the GEE Python API has relatively little documentation and limited functionality for visualizing results interactively. The **geemap** Python package was created to fill this gap. It is built upon `ipyleaflet <https://github.com/jupyter-widgets/ipyleaflet>`__ and `ipywidgets <https://github.com/jupyter-widgets/ipywidgets>`__, and enables users to 
analyze and visualize Earth Engine datasets interactively within a Jupyter-based environment.

**Geemap** is intended for students and researchers, who would like to utilize the Python ecosystem of diverse libraries and tools to explore Google Earth Engine. It is also designed for existing GEE users who would like to transition from the GEE JavaScript API to Python API. The automated JavaScript-to-Python `conversion module <https://github.com/gee-community/geemap/blob/master/geemap/conversion.py>`__ of the **geemap** package
can greatly reduce the time needed to convert existing GEE JavaScripts to Python scripts and Jupyter notebooks.

For video tutorials and notebook examples, please visit `<https://geemap.org/tutorials>`__. For complete documentation on geemap modules and methods, please visit `<https://geemap.org/geemap>`_.

If you find geemap useful in your research, please consider citing the following papers to support my work. Thank you for your support.

- Wu, Q., (2020). geemap: A Python package for interactive mapping with Google Earth Engine. *The Journal of Open Source Software*, 5(51), 2305. `<https://doi.org/10.21105/joss.02305>`__ 
- Wu, Q., Lane, C. R., Li, X., Zhao, K., Zhou, Y., Clinton, N., DeVries, B., Golden, H. E., & Lang, M. W. (2019). Integrating LiDAR data and multi-temporal aerial imagery to map wetland inundation dynamics using Google Earth Engine. *Remote Sensing of Environment*, 228, 1-13. https://doi.org/10.1016/j.rse.2019.04.015 (`pdf <https://gishub.org/2019_rse>`_ | `source code <https://doi.org/10.6084/m9.figshare.8864921>`_)

Check out the geemap workshop presented at the GeoPython Conference 2021. This workshop gives a comprehensive introduction to the key features of geemap. 

.. image:: https://img.youtube.com/vi/wGjpjh9IQ5I/0.jpg
        :target: https://www.youtube.com/watch?v=wGjpjh9IQ5I

Features
--------

Below is a partial list of features available for the geemap package. Please check the `examples <https://github.com/gee-community/geemap/tree/master/examples>`__ page for notebook examples, GIF animations, and video tutorials.

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


Installation
------------

To use **geemap**, you must first `sign up <https://earthengine.google.com/signup/>`__ for a `Google Earth Engine <https://earthengine.google.com/>`__ account.

.. image:: https://i.imgur.com/ng0FzUT.png
        :target: https://earthengine.google.com

**Geemap** is available on `PyPI <https://pypi.org/project/geemap/>`__. To install **geemap**, run this command in your terminal:

.. code:: python

  pip install geemap


**Geemap** is also available on `conda-forge <https://anaconda.org/conda-forge/geemap>`__. If you have `Anaconda <https://www.anaconda.com/distribution/#download-section>`__ or `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`__ installed on your computer, you can create a conda Python environment to install geemap:

.. code:: python

  conda create -n gee python=3.10
  conda activate gee
  conda install -n base mamba -c conda-forge
  mamba install geemap -c conda-forge 

If you have installed **geemap** before and want to upgrade to the latest version, you can run the following command in your terminal:

.. code:: python

  pip install -U geemap


If you use conda, you can update geemap to the latest version by running the following command in your terminal:
  
.. code:: python

  conda update -c conda-forge geemap


To install the development version from GitHub using `Git <https://git-scm.com/>`__, run the following command in your terminal:

.. code:: python

  pip install git+https://github.com/gee-community/geemap


To install the development version from GitHub directly within Jupyter notebook without using Git, run the following code:

.. code:: python

  import geemap
  geemap.update_package()
  
Citations
---------

To support my work, please consider citing the following articles:

- **Wu, Q.**, (2020). geemap: A Python package for interactive mapping with Google Earth Engine. *The Journal of Open Source Software*, 5(51), 2305. https://doi.org/10.21105/joss.02305 
- **Wu, Q.**, Lane, C. R., Li, X., Zhao, K., Zhou, Y., Clinton, N., DeVries, B., Golden, H. E., & Lang, M. W. (2019). Integrating LiDAR data and multi-temporal aerial imagery to map wetland inundation dynamics using Google Earth Engine. *Remote Sensing of Environment*, 228, 1-13. https://doi.org/10.1016/j.rse.2019.04.015 (`pdf <https://gishub.org/2019_rse>`_ | `source code <https://doi.org/10.6084/m9.figshare.8864921>`_)