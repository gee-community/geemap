======
geemap
======

.. image:: https://colab.research.google.com/assets/colab-badge.svg
        :target: https://gishub.org/geemap-colab

.. image:: https://binder.pangeo.io/badge_logo.svg
        :target: https://binder.pangeo.io/v2/gh/giswqs/geemap/master

.. image:: https://img.shields.io/pypi/v/geemap.svg
        :target: https://pypi.python.org/pypi/geemap

.. image:: https://img.shields.io/conda/vn/conda-forge/geemap.svg
        :target: https://anaconda.org/conda-forge/geemap

.. image:: https://pepy.tech/badge/geemap
        :target: https://pepy.tech/project/geemap

.. image:: https://github.com/giswqs/geemap/workflows/docs/badge.svg
        :target: https://giswqs.github.io/geemap

.. image:: https://img.shields.io/badge/YouTube-Channel-red   
        :target: https://www.youtube.com/c/QiushengWu

.. image:: https://img.shields.io/twitter/follow/giswqs?style=social   	
        :target: https://twitter.com/giswqs

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
        :target: https://opensource.org/licenses/MIT

.. image:: https://img.shields.io/badge/Donate-Buy%20me%20a%20coffee-yellowgreen.svg
        :target: https://www.buymeacoffee.com/giswqs

.. image:: https://joss.theoj.org/papers/91af8757c56e3fed2535fcd165137116/status.svg
        :target: https://joss.theoj.org/papers/91af8757c56e3fed2535fcd165137116

**A Python package for interactive mapping with Google Earth Engine, ipyleaflet, and ipywidgets.**

* GitHub repo: https://github.com/giswqs/geemap
* Documentation: https://giswqs.github.io/geemap
* PyPI: https://pypi.org/project/geemap/
* Conda-forge: https://anaconda.org/conda-forge/geemap
* 360+ GEE notebook examples: https://github.com/giswqs/earthengine-py-notebooks
* GEE Tutorials on YouTube: https://www.youtube.com/c/QiushengWu
* Free software: MIT license


**Contents**

- `Introduction`_
- `Features`_
- `Installation`_
- `Usage`_
- `Examples`_
- `Dependencies`_
- `Contributing`_
- `References`_
- `Credits`_


Introduction
------------

**geemap** is a Python package for interactive mapping with `Google Earth Engine <https://earthengine.google.com/>`__ (GEE), which is a cloud computing platform with a `multi-petabyte catalog <https://developers.google.com/earth-engine/datasets/>`__ of satellite imagery and geospatial datasets. During the past few years, 
GEE has become very popular in the geospatial community and it has empowered numerous environmental applications at local, regional, and global scales. GEE provides both JavaScript and Python APIs for 
making computational requests to the Earth Engine servers. Compared with the comprehensive `documentation <https://developers.google.com/earth-engine>`__ and interactive IDE (i.e., `GEE JavaScript Code Editor <https://code.earthengine.google.com/>`__) of the GEE JavaScript API, 
the GEE Python API has relatively little documentation and limited functionality for visualizing results interactively. The **geemap** Python package was created to fill this gap. It is built upon `ipyleaflet <https://github.com/jupyter-widgets/ipyleaflet>`__ and `ipywidgets <https://github.com/jupyter-widgets/ipywidgets>`__, and enables users to 
analyze and visualize Earth Engine datasets interactively within a Jupyter-based environment.

**geemap** is intended for students and researchers, who would like to utilize the Python ecosystem of diverse libraries and tools to explore Google Earth Engine. It is also designed for existing GEE users who would like to transition from the GEE JavaScript API to Python API. The automated JavaScript-to-Python `conversion module <https://github.com/giswqs/geemap/blob/master/geemap/conversion.py>`__ of the **geemap** package
can greatly reduce the time needed to convert existing GEE JavaScripts to Python scripts and Jupyter notebooks.

For video tutorials and notebook examples, please visit `<https://github.com/giswqs/geemap/tree/master/examples>`__. For complete documentation on geemap modules and methods, please visit `<https://giswqs.github.io/geemap/geemap>`_.

If you find geemap useful in your research, please consider citing the following papers to support my work. Thank you for your support.

- Wu, Q., (2020). geemap: A Python package for interactive mapping with Google Earth Engine. *The Journal of Open Source Software*, 5(51), 2305. `<https://doi.org/10.21105/joss.02305>`__ 
- Wu, Q., Lane, C. R., Li, X., Zhao, K., Zhou, Y., Clinton, N., DeVries, B., Golden, H. E., & Lang, M. W. (2019). Integrating LiDAR data and multi-temporal aerial imagery to map wetland inundation dynamics using Google Earth Engine. *Remote Sensing of Environment*, 228, 1-13. https://doi.org/10.1016/j.rse.2019.04.015 (`pdf <https://gishub.org/2019_rse>`_ | `source code <https://doi.org/10.6084/m9.figshare.8864921>`_)


Features
--------

Below is a partial list of features available for the geemap package. Please check the `examples <https://github.com/giswqs/geemap/tree/master/examples>`__ page for notebook examples, GIF animations, and video tutorials.

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

**geemap** is available on `PyPI <https://pypi.org/project/geemap/>`__. To install **geemap**, run this command in your terminal:

.. code:: python

  pip install geemap


**geemap** is also available on `conda-forge <https://anaconda.org/conda-forge/geemap>`__. If you have `Anaconda <https://www.anaconda.com/distribution/#download-section>`__ or `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`__ installed on your computer, you can create a conda Python environment to install geemap:

.. code:: python

  conda create -n gee python
  conda activate gee
  conda install mamba -c conda-forge
  mamba install geemap -c conda-forge 

Optionally, you can install `Jupyter notebook extensions <https://github.com/ipython-contrib/jupyter_contrib_nbextensions>`__, which can improve your productivity in the notebook environment. Some useful extensions include Table of Contents, Gist-it, Autopep8, Variable Inspector, etc. See this `post <https://towardsdatascience.com/jupyter-notebook-extensions-517fa69d2231>`__ for more information.       

.. code:: python

  mamba install jupyter_contrib_nbextensions -c conda-forge 


If you have installed **geemap** before and want to upgrade to the latest version, you can run the following command in your terminal:

.. code:: python

  pip install -U geemap


If you use conda, you can update geemap to the latest version by running the following command in your terminal:
  
.. code:: python

  mamba update -c conda-forge geemap


To install the development version from GitHub using `Git <https://git-scm.com/>`__, run the following command in your terminal:

.. code:: python

  pip install git+https://github.com/giswqs/geemap


To install the development version from GitHub directly within Jupyter notebook without using Git, run the following code:

.. code:: python

  import geemap
  geemap.update_package()
  

To use geemap in a Docker container, check out `ee-jupyter-contrib <https://github.com/gee-community/ee-jupyter-contrib/tree/master/docker/gcp_ai_deep_learning_platform>`__ or this `page <https://hub.docker.com/r/bkavlak/geemap>`__.


Usage
-----

**Important note:** A key difference between `ipyleaflet <https://github.com/jupyter-widgets/ipyleaflet>`__ and `folium <https://github.com/python-visualization/folium>`__ is that ipyleaflet is built upon ipywidgets and allows bidirectional
communication between the front-end and the backend enabling the use of the map to capture user input, while folium is meant for displaying
static data only (`source <https://blog.jupyter.org/interactive-gis-in-jupyter-with-ipyleaflet-52f9657fa7a>`__).
Note that `Google Colab <https://colab.research.google.com/>`__ currently does not support ipyleaflet
(`source <https://github.com/googlecolab/colabtools/issues/60#issuecomment-596225619>`__). Therefore, if you are using geemap with Google Colab, you should use
`import geemap.eefolium <https://github.com/giswqs/geemap/blob/master/geemap/eefolium.py>`__. If you are using geemap with `binder <https://mybinder.org/>`__ or a local Jupyter notebook server,
you can use `import geemap <https://github.com/giswqs/geemap/blob/master/geemap/geemap.py>`__, which provides more functionalities for capturing user input (e.g.,
mouse-clicking and moving).

More GEE Tutorials are available on my `YouTube channel <https://gishub.org/geemap>`__.

|YouTube|

.. |YouTube| image:: https://wetlands.io/file/images/youtube.png
   :target: https://gishub.org/geemap

To create an ipyleaflet-based interactive map:

.. code:: python

  import geemap
  Map = geemap.Map(center=[40,-100], zoom=4)
  Map


To create a folium-based interactive map:

.. code:: python

  import geemap.eefolium as geemap
  Map = geemap.Map(center=[40,-100], zoom=4)
  Map


To add an Earth Engine data layer to the Map:

.. code:: python

  Map.addLayer(ee_object, vis_params, name, shown, opacity)


To center the map view at a given coordinates with the given zoom level:

.. code:: python

  Map.setCenter(lon, lat, zoom)


To center the map view around an Earth Engine object:

.. code:: python

  Map.centerObject(ee_object, zoom)


To add LayerControl to a folium-based Map:

.. code:: python

  Map.addLayerControl()


To add a minimap (overview) to an ipyleaflet-based Map:

.. code:: python

  Map.add_minimap()


To add additional basemaps to the Map:

.. code:: python

  Map.add_basemap('Esri Ocean')
  Map.add_basemap('Esri National Geographic')


To add an XYZ tile layer to the Map:

.. code:: python

  url = 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
  Map.add_tile_layer(url, name='Google Map', attribution='Google')


To add a WMS layer to the Map:

.. code:: python

  naip_url = 'https://services.nationalmap.gov/arcgis/services/USGSNAIPImagery/ImageServer/WMSServer?'
  Map.add_wms_layer(url=naip_url, layers='0', name='NAIP Imagery', format='image/png', shown=True)


To convert a shapefile to Earth Engine object and add it to the Map:

.. code:: python

  ee_object = geemap.shp_to_ee(shp_file_path)
  Map.addLayer(ee_object, {}, 'Layer name')


To convert a GeoJSON file to Earth Engine object and add it to the Map:

.. code:: python

  ee_object = geemap.geojson_to_ee(geojson_file_path)
  Map.addLayer(ee_object, {}, 'Layer name')


To download an ee.FeatureCollection as a shapefile:

.. code:: python

  geemap.ee_to_csv(ee_object, filename, selectors)


To export an ee.FeatureCollection to other formats, including shp, csv, json, kml, and kmz:

.. code:: python

  geemap.ee_export_vector(ee_object, filename, selectors)


To export an ee.Image as a GeoTIFF file:

.. code:: python

  geemap.ee_export_image(ee_object, filename, scale, crs, region, file_per_band)


To export an ee.ImageCollection as GeoTIFF files:

.. code:: python

  geemap.ee_export_image_collection(ee_object, output, scale, crs, region, file_per_band)


To extract pixels from an ee.Image into a 3D numpy array:

.. code:: python

  geemap.ee_to_numpy(ee_object, bands, region, properties, default_value)


To calculate zonal statistics:

.. code:: python

  geemap.zonal_statistics(in_value_raster, in_zone_vector, out_file_path, statistics_type='MEAN')


To calculate zonal statistics by group:

.. code:: python

  geemap.zonal_statistics_by_group(in_value_raster, in_zone_vector, out_file_path, statistics_type='SUM')


To create a split-panel Map:

.. code:: python

  Map.split_map(left_layer='HYBRID', right_layer='ESRI')


To add a marker cluster to the Map:

.. code:: python

  Map.marker_cluster()
  feature_collection = ee.FeatureCollection(Map.ee_markers)


To add a customized legend to the Map:

.. code:: python

  legend_dict = {
      'one': (0, 0, 0),
      'two': (255,255,0),
      'three': (127, 0, 127)
  }
  Map.add_legend(legend_title='Legend', legend_dict=legend_dict, position='bottomright')
  Map.add_legend(builtin_legend='NLCD')


To download a GIF from an Earth Engine ImageCollection:

.. code:: python

  geemap.download_ee_video(tempCol, videoArgs, saved_gif)


To add animated text to an existing GIF image:

.. code:: python

  geemap.add_text_to_gif(in_gif, out_gif, xy=('5%', '5%'), text_sequence=1984, font_size=30, font_color='#0000ff', duration=100)


To create a colorbar for an Earth Engine image:

.. code:: python

  palette = ['blue', 'purple', 'cyan', 'green', 'yellow', 'red']
  create_colorbar(width=250, height=30, palette=palette, vertical=False,add_labels=True, font_size=20, labels=[-40, 35])


To create a Landsat timelapse animation and add it to the Map:

.. code:: python

  Map.add_landsat_ts_gif(label='Place name', start_year=1985, bands=['NIR', 'Red', 'Green'], frames_per_second=5)


To convert all GEE JavaScripts in a folder recursively to Python scripts:

.. code:: python

  from geemap.conversion import *
  js_to_python_dir(in_dir, out_dir)


To convert all GEE Python scripts in a folder recursively to Jupyter notebooks:  

.. code:: python

  from geemap.conversion import *
  template_file = get_nb_template()
  py_to_ipynb_dir(in_dir, template_file, out_dir)


To execute all Jupyter notebooks in a folder recursively and save output cells:  

.. code:: python

  from geemap.conversion import *
  execute_notebook_dir(in_dir) 


To search Earth Engine API documentation with Jupyter notebooks:  

.. code:: python

  import geemap
  geemap.ee_search()


To publish an interactive GEE map with Jupyter notebooks:  

.. code:: python

  Map.publish(name, headline, visibility)


To add a local raster dataset to the map:  

.. code:: python

  Map.add_raster(image, bands, colormap, layer_name)
  

To get image basic properties:

.. code:: python

  geemap.image_props(image).getInfo()


To get image descriptive statistics:

.. code:: python

  geemap.image_stats(image, region, scale)


To remove all user-drawn geometries:

.. code:: python

  geemap.remove_drawn_features()


To extract pixel values based on user-drawn geometries:

.. code:: python

  geemap.extract_values_to_points(out_shp)


To load a Cloud Optimized GeoTIFF as an ee.Image:

.. code:: python

  image = geemap.load_GeoTIFF(URL)


To load a list of Cloud Optimized GeoTIFFs as an ee.ImageCollection:

.. code:: python

  collection = geemap.load_GeoTIFFs(URLs)


Examples
--------

The following examples require the geemap package, which can be installed using ``pip install geemap``. Check the `Installation`_ section for more information. More examples can be found at 
another repo: `A collection of 300+ Jupyter Python notebook examples for using Google Earth Engine with interactive mapping <https://github.com/giswqs/earthengine-py-notebooks>`__.

- `Converting GEE JavaScripts to Python scripts and Jupyter notebooks`_
- `Interactive mapping using GEE Python API and geemap`_

Converting GEE JavaScripts to Python scripts and Jupyter notebooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Launch an interactive notebook with **Google Colab**. Keep in mind that the conversion might not always work perfectly. Additional manual changes might still be needed. ``ui`` and ``chart`` are not supported. 
The source code for this automated conversion module can be found at `conversion.py <https://github.com/giswqs/geemap/blob/master/geemap/conversion.py>`__.

.. image:: https://colab.research.google.com/assets/colab-badge.svg
        :target: https://colab.research.google.com/github/giswqs/geemap/blob/master/examples/notebooks/earthengine_js_to_ipynb.ipynb


.. code:: python

        import os
        from geemap.conversion import *

        # Create a temporary working directory
        work_dir = os.path.join(os.path.expanduser('~'), 'geemap')
        # Get Earth Engine JavaScript examples. There are five examples in the geemap package folder. 
        # Change js_dir to your own folder containing your Earth Engine JavaScripts, such as js_dir = '/path/to/your/js/folder'
        js_dir = get_js_examples(out_dir=work_dir) 

        # Convert all Earth Engine JavaScripts in a folder recursively to Python scripts.
        js_to_python_dir(in_dir=js_dir, out_dir=js_dir, use_qgis=True)
        print("Python scripts saved at: {}".format(js_dir))

        # Convert all Earth Engine Python scripts in a folder recursively to Jupyter notebooks.
        nb_template = get_nb_template()  # Get the notebook template from the package folder.
        py_to_ipynb_dir(js_dir, nb_template)

        # Execute all Jupyter notebooks in a folder recursively and save the output cells.
        execute_notebook_dir(in_dir=js_dir)


.. image:: https://i.imgur.com/8bedWtl.gif



Interactive mapping using GEE Python API and geemap
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Launch an interactive notebook with **Google Colab**. Note that **Google Colab** currently does not support ipyleaflet. Therefore, you should use ``import geemap.eefolium`` instead of ``import geemap``.

.. image:: https://colab.research.google.com/assets/colab-badge.svg
        :target: https://colab.research.google.com/github/giswqs/geemap/blob/master/examples/notebooks/geemap_and_folium.ipynb

.. code:: python

        # Installs geemap package
        import subprocess

        try:
                import geemap
        except ImportError:
                print('geemap package not installed. Installing ...')
                subprocess.check_call(["python", '-m', 'pip', 'install', 'geemap'])

        # Checks whether this notebook is running on Google Colab
        try:
                import google.colab
                import geemap.eefolium as emap
        except:
                import geemap as emap

        # Authenticates and initializes Earth Engine
        import ee

        try:
                ee.Initialize()
        except Exception as e:
                ee.Authenticate()
                ee.Initialize()

        # Creates an interactive map
        Map = emap.Map(center=[40,-100], zoom=4)

        # Adds Earth Engine dataset
        image = ee.Image('USGS/SRTMGL1_003')

        # Sets visualization parameters.
        vis_params = {
                'min': 0,
                'max': 4000,
                'palette': ['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']}

        # Prints the elevation of Mount Everest.
        xy = ee.Geometry.Point([86.9250, 27.9881])
        elev = image.sample(xy, 30).first().get('elevation').getInfo()
        print('Mount Everest elevation (m):', elev)

        # Adds Earth Engine layers to Map
        Map.addLayer(image, vis_params, 'SRTM DEM', True, 0.5)
        Map.addLayer(xy, {'color': 'red'}, 'Mount Everest')
        Map.setCenter(100, 40, 4)
        # Map.centerObject(xy, 13)

        # Display the Map
        Map.addLayerControl()
        Map


.. image:: https://i.imgur.com/7NMQw6I.gif

Dependencies
------------

* `bqplot <https://github.com/bloomberg/bqplot>`__
* `colour <https://github.com/vaab/colour>`__
* `dulwich <https://github.com/dulwich/dulwich>`__
* `earthengine-api <https://github.com/google/earthengine-api>`__
* `folium <https://github.com/python-visualization/folium>`__
* `geeadd <https://github.com/samapriya/gee_asset_manager_addon>`__
* `geocoder <https://github.com/DenisCarriere/geocoder>`__
* `ipyfilechooser <https://github.com/crahan/ipyfilechooser>`__
* `ipyleaflet <https://github.com/jupyter-widgets/ipyleaflet>`__
* `ipynb-py-convert <https://github.com/kiwi0fruit/ipynb-py-convert>`__
* `ipytree <https://github.com/QuantStack/ipytree>`__
* `ipywidgets <https://github.com/jupyter-widgets/ipywidgets>`__
* `mss <https://github.com/BoboTiG/python-mss>`__
* `pillow <https://github.com/python-pillow/Pillow>`__
* `pyshp <https://github.com/GeospatialPython/pyshp>`__
* `xarray-leaflet <https://github.com/davidbrochart/xarray_leaflet>`__



Contributing
------------
Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

Report Bugs
^^^^^^^^^^^

Report bugs at https://github.com/giswqs/geemap/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
^^^^^^^^

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
^^^^^^^^^^^^^^^^^^

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
^^^^^^^^^^^^^^^^^^^

geemap could always use more documentation, whether as part of the
official geemap docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
^^^^^^^^^^^^^^^

The best way to send feedback is to file an issue at https://github.com/giswqs/geemap/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
^^^^^^^^^^^^

Ready to contribute? Here's how to set up `geemap` for local development.

1. Fork the `geemap` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/geemap.git

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development::

    $ mkvirtualenv geemap
    $ cd geemap/
    $ python setup.py develop

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass flake8 and the
   tests, including testing other Python versions with tox::

    $ flake8 geemap tests
    $ python setup.py test or pytest
    $ tox

   To get flake8 and tox, just pip install them into your virtualenv.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
^^^^^^^^^^^^^^^^^^^^^^^

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for Python 3.6, 3.7 and 3.8, and for PyPy. Check
   https://travis-ci.com/giswqs/geemap/pull_requests
   and make sure that the tests pass for all supported Python versions.

Tips
^^^^

To run a subset of tests::


    $ python -m unittest tests.test_geemap
    

Deploying
^^^^^^^^^

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed (including an entry in HISTORY.rst).
Then run::

$ bump2version patch # possible: major / minor / patch
$ git push
$ git push --tags

Travis will then deploy to PyPI if tests pass.


References
----------

To support my work, please consider citing the following articles:

- **Wu, Q.**, (2020). geemap: A Python package for interactive mapping with Google Earth Engine. *The Journal of Open Source Software*, 5(51), 2305. https://doi.org/10.21105/joss.02305 
- **Wu, Q.**, Lane, C. R., Li, X., Zhao, K., Zhou, Y., Clinton, N., DeVries, B., Golden, H. E., & Lang, M. W. (2019). Integrating LiDAR data and multi-temporal aerial imagery to map wetland inundation dynamics using Google Earth Engine. *Remote Sensing of Environment*, 228, 1-13. https://doi.org/10.1016/j.rse.2019.04.015 (`pdf <https://gishub.org/2019_rse>`_ | `source code <https://doi.org/10.6084/m9.figshare.8864921>`_)


Credits
-------

This package was created with `Cookiecutter <https://github.com/audreyr/cookiecutter>`__ and the `audreyr/cookiecutter-pypackage <https://github.com/audreyr/cookiecutter-pypackage>`__ project template.
