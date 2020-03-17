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

.. image:: https://pepy.tech/badge/geemap
        :target: https://pepy.tech/project/geemap

.. image:: https://img.shields.io/travis/giswqs/geemap.svg
        :target: https://travis-ci.com/giswqs/geemap

.. image:: https://readthedocs.org/projects/geemap/badge/?version=latest
        :target: https://geemap.readthedocs.io/en/latest/?badge=latest

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
        :target: https://opensource.org/licenses/MIT


Authors: Dr. Qiusheng Wu (https://wetlands.io)

A Python package for interactive mapping using Google Earth Engine, ipyleaflet, and ipywidgets.

* GitHub repo: https://github.com/giswqs/geemap
* Documentation: https://geemap.readthedocs.io
* PyPI: https://pypi.org/project/geemap/
* Free software: MIT license


**Contents**

- `Features`_
- `Installation`_
- `Examples`_
- `Dependencies`_
- `Reporting Bugs`_
- `Credits`_



Features
--------

* Automatically converts Earth Engine JavaScripts to Python scripts and Jupyter Notebooks.
* Adds Earth Engine tile layers to ipyleaflet map for interactive mapping.
* Supports Earth Engine JavaScript API functions in Python, such as ``Map.AddLayer()``, ``Map.setCenter()``, ``Map.centerObject()``, ``Map.setOptions()``.
* Captures user inputs and query Earth Engine objects.
* Plots charts based on Earth Engine data.


Installation
------------
To install **geemap**  , run this command in your terminal:

.. code:: python

  pip install geemap


If you have Anaconda_ or Miniconda_ installed on your computer, you can use create conda Python environment to install geemap:

.. code:: python

  conda create -n gee python
  conda activate gee
  pip install geemap


If you have installed **geemap** before and want to upgrade to the latest version, you can use the following command:

.. code:: python

  pip install geemap -U


.. _Anaconda: https://www.anaconda.com/distribution/#download-section
.. _Miniconda: https://docs.conda.io/en/latest/miniconda.html


Examples
--------

The following examples require the geemap package, which can be installed using ``pip install geemap``. Check the `Installation`_ section for more information.

- `Converting GEE JavaScripts to Python scripts and Jupyter notebooks`_
- `Interactive mapping using GEE Python API and geemap`_

Converting GEE JavaScripts to Python scripts and Jupyter notebooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Lanch an interactive notebook with **Google Colab**, **mybinder.org**, or **binder.pangeo.io**:

.. image:: https://colab.research.google.com/assets/colab-badge.svg
        :target: https://colab.research.google.com/github/giswqs/geemap/blob/master/examples/earthengine_js_to_ipynb.ipynb

.. image:: https://mybinder.org/badge_logo.svg
        :target: https://mybinder.org/v2/gh/giswqs/geemap/master?filepath=examples/earthengine_js_to_ipynb.ipynb

.. image:: https://binder.pangeo.io/badge_logo.svg
        :target: https://binder.pangeo.io/v2/gh/giswqs/geemap/master?filepath=examples/earthengine_js_to_ipynb.ipynb

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
Lanch an interactive notebook with **mybinder.org** or **binder.pangeo.io**. Note that **Google Colab** currently does not support ipyleaflet. Therefore, geemap won't be able to display interactive maps on Google Colab.

.. image:: https://mybinder.org/badge_logo.svg
        :target: https://mybinder.org/v2/gh/giswqs/geemap/master?filepath=examples/geemap_and_earthengine.ipynb

.. image:: https://binder.pangeo.io/badge_logo.svg
        :target: https://binder.pangeo.io/v2/gh/giswqs/geemap/master?filepath=examples/geemap_and_earthengine.ipynb

.. code:: python

        import ee
        import geemap
        import ipyleaflet

        try:
                ee.Initialize()
        except Exception as e:
                ee.Authenticate()
                ee.Initialize()

        # Create an interactive map
        Map = ipyleaflet.Map(center=(40, -100), zoom=4, scroll_wheel_zoom=True)
        Map.setOptions('HYBRID') # Add Google Satellite basemap
        Map

        # Add Earth Engine dataset
        image = ee.Image('USGS/SRTMGL1_003')

        # Set visualization parameters.
        vis_params = {
                'min': 0,
                'max': 4000,
                'palette': ['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']
        }

        # Print the elevation of Mount Everest.
        xy = ee.Geometry.Point([86.9250, 27.9881])
        elev = image.sample(xy, 30).first().get('elevation').getInfo()
        print('Mount Everest elevation (m):', elev)

        # Add Earth Engine layers to Map
        Map.addLayer(image, vis_params, 'STRM DEM', True, 0.5)
        Map.addLayer(xy, {'color': 'red'}, 'Mount Everest')

        # Set center of the map
        Map.centerObject(ee_object=xy, zoom=13)
        Map.setCenter(lon=-100, lat=40, zoom=4)


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
