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

A Python package for interactive mapping using Google Earth Engine, ipyleaflet, and ipywidgets

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

* Automatically convert Earth Engine JavaScripts to Python scripts and Jupyter Notebooks.
* Add Earth Engine tile layers to ipyleaflet map for interactive mapping.
* Capture user inputs and query Earth Engine objects.
* Plot charts bases on Earth Engine data


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

Open a Jupyter notebook and paste the follow code to a notebook cell. Alternatively, you can run the code interactively with **mybinder.org** or **binder.pangeo.io** now:

.. image:: https://mybinder.org/badge_logo.svg
        :target: https://mybinder.org/v2/gh/giswqs/geemap/master

.. image:: https://binder.pangeo.io/badge_logo.svg
        :target: https://binder.pangeo.io/v2/gh/giswqs/geemap/master

.. code:: python

        import ee
        import geemap

        try:
                ee.Initialize()
        except Exception as e:
                ee.Authenticate()
                ee.Initialize()

        # Create an interactive map
        Map = geemap.Map(center=(40, -100), zoom=4)
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
