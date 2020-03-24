======
geemap
======

.. image:: https://colab.research.google.com/assets/colab-badge.svg
        :target: https://gishub.org/geemap-colab
        
.. image:: https://mybinder.org/badge_logo.svg
        :target: https://mybinder.org/v2/gh/giswqs/geemap/master

.. image:: https://binder.pangeo.io/badge_logo.svg
        :target: https://binder.pangeo.io/v2/gh/giswqs/geemap/master

.. image:: https://img.shields.io/pypi/v/geemap.svg
        :target: https://pypi.python.org/pypi/geemap

.. image:: https://img.shields.io/conda/vn/conda-forge/geemap.svg
        :target: https://anaconda.org/conda-forge/geemap

.. image:: https://pepy.tech/badge/geemap
        :target: https://pepy.tech/project/geemap

.. image:: https://img.shields.io/travis/giswqs/geemap.svg
        :target: https://travis-ci.com/giswqs/geemap

.. image:: https://readthedocs.org/projects/geemap/badge/?version=latest
        :target: https://geemap.readthedocs.io/en/latest/?badge=latest

.. image:: https://img.shields.io/twitter/follow/giswqs?style=social   
        :target: https://twitter.com/giswqs

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
        :target: https://opensource.org/licenses/MIT


Authors: Dr. Qiusheng Wu (https://wetlands.io)

A Python package for interactive mapping with Google Earth Engine, ipyleaflet, and ipywidgets.

* GitHub repo: https://github.com/giswqs/geemap
* Documentation: https://geemap.readthedocs.io
* PyPI: https://pypi.org/project/geemap/
* 360+ GEE notebook examples: https://github.com/giswqs/earthengine-py-notebooks
* Free software: MIT license


**Contents**

- `Features`_
- `Installation`_
- `Usage`_
- `Examples`_
- `Dependencies`_
- `Reporting Bugs`_
- `Credits`_



Features
--------

* Automatically converts Earth Engine JavaScripts to Python scripts and Jupyter Notebooks.
* Adds Earth Engine tile layers to ipyleaflet map for interactive mapping.
* Supports Earth Engine JavaScript API functions in Python, such as ``Map.addLayer()``, ``Map.setCenter()``, ``Map.centerObject()``, ``Map.setOptions()``.
* Captures user input and query Earth Engine objects.
* Plots charts based on Earth Engine data.


Installation
------------

The **geemap** Python package is built upon the `ipyleaflet <https://github.com/jupyter-widgets/ipyleaflet>`__ and `folium <https://github.com/python-visualization/folium>`__ packages and
implements several methods for interacting with Earth Engine data layers, such as ``Map.addLayer()``, ``Map.setCenter()``, and ``Map.centerObject()``.



To install **geemap**, run this command in your terminal:

.. code:: python

  pip install geemap


**geemap** is also available on `conda-forge <https://anaconda.org/conda-forge/geemap>`__. If you have Anaconda_ or Miniconda_ installed on your computer, you can create a conda Python environment to install geemap:

.. code:: python

  conda create -n gee python
  conda activate gee
  conda install -c conda-forge geemap


If you have installed **geemap** before and want to upgrade to the latest version, you can run the following command in your terminal:

.. code:: python

  pip install -U geemap
  

To install the development version from GitHub, run the following command in your terminal:

.. code:: python

  pip install git+https://github.com/giswqs/geemap
  

.. _Anaconda: https://www.anaconda.com/distribution/#download-section
.. _Miniconda: https://docs.conda.io/en/latest/miniconda.html


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

To create an ipyleaflet-based interactive map:

.. code:: python

  import geemap
  Map = geemap.Map(center=[40,-100], zoom=4)
  Map


To create a folium-based interactive map:

.. code:: python

  import geemap.eefolium as emap
  Map = emap.Map(center=[40,-100], zoom=4)
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


Examples
--------

The following examples require the geemap package, which can be installed using ``pip install geemap``. Check the `Installation`_ section for more information. More examples can be found at 
another repo: `A collection of 300+ Jupyter Python notebook examples for using Google Earth Engine with interactive mapping <https://github.com/giswqs/earthengine-py-notebooks>`__.

- `Converting GEE JavaScripts to Python scripts and Jupyter notebooks`_
- `Interactive mapping using GEE Python API and geemap`_

Converting GEE JavaScripts to Python scripts and Jupyter notebooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Launch an interactive notebook with **Google Colab**, **mybinder.org**, or **binder.pangeo.io**. Keep in mind that the conversion might not always work perfectly. Additional manual changes might still be needed. ``ui`` and ``chart`` are not supported. 
The source code for this automated conversion module can be found at `conversion.py`_.

.. image:: https://colab.research.google.com/assets/colab-badge.svg
        :target: https://colab.research.google.com/github/giswqs/geemap/blob/master/examples/notebooks/earthengine_js_to_ipynb.ipynb

.. image:: https://mybinder.org/badge_logo.svg
        :target: https://mybinder.org/v2/gh/giswqs/geemap/master?filepath=examples/notebooks/earthengine_js_to_ipynb.ipynb

.. image:: https://binder.pangeo.io/badge_logo.svg
        :target: https://binder.pangeo.io/v2/gh/giswqs/geemap/master?filepath=examples/notebooks/earthengine_js_to_ipynb.ipynb

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

.. _`conversion.py`: https://github.com/giswqs/geemap/blob/master/geemap/conversion.py


Interactive mapping using GEE Python API and geemap
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Launch an interactive notebook with **mybinder.org** or **binder.pangeo.io**. Note that **Google Colab** currently does not support ipyleaflet. Therefore, you should use ``import geemap.eefolium`` instead of ``import geemap``.

.. image:: https://colab.research.google.com/assets/colab-badge.svg
        :target: https://colab.research.google.com/github/giswqs/geemap/blob/master/examples/notebooks/geemap_and_folium.ipynb

.. image:: https://mybinder.org/badge_logo.svg
        :target: https://mybinder.org/v2/gh/giswqs/geemap/master?filepath=examples/notebooks/geemap_and_earthengine.ipynb

.. image:: https://binder.pangeo.io/badge_logo.svg
        :target: https://binder.pangeo.io/v2/gh/giswqs/geemap/master?filepath=examples/notebooks/geemap_and_earthengine.ipynb

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

* earthengine-api_
* ipyleaflet_
* ipywidgets_
* folium_
* bqplot_
* ipynb-py-convert_

.. _earthengine-api: https://github.com/google/earthengine-api
.. _ipyleaflet: https://github.com/jupyter-widgets/ipyleaflet
.. _ipywidgets: https://github.com/jupyter-widgets/ipywidgets
.. _folium: https://github.com/python-visualization/folium
.. _bqplot: https://github.com/bloomberg/bqplot
.. _ipynb-py-convert: https://github.com/kiwi0fruit/ipynb-py-convert

Reporting Bugs
--------------
Report bugs at https://github.com/giswqs/geemap/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
