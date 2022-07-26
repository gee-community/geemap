# Installation

## Earth Engine Account

To use **geemap**, you must first [sign up](https://earthengine.google.com/signup/) for a [Google Earth Engine](https://earthengine.google.com/) account.
You cannot use Google Earth Engine unless your application has been approved. Once you receive the application approval email, you can log in to
the [Earth Engine Code Editor](https://code.earthengine.google.com/) to get familiar with the JavaScript API.

![signup](https://i.imgur.com/ng0FzUT.png)

## Install from PyPI

**Geemap** is available on [PyPI](https://pypi.org/project/geemap/). To install **geemap**, run this command in your terminal:

```bash
    pip install geemap
```

## Install from conda-forge

**Geemap** is also available on [conda-forge](https://anaconda.org/conda-forge/geemap). If you have
[Anaconda](https://www.anaconda.com/distribution/#download-section) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installed on your computer, you can install geemap using the following command:

```bash
    conda install geemap -c conda-forge
```

The geemap package has some optional dependencies, such as [GeoPandas](https://geopandas.org) and [localtileserver](https://github.com/banesullivan/localtileserver). These optional dependencies can be challenging to install on some computers, especially Windows. It is highly recommended that you create a fresh conda environment to install geemap. Follow the commands below to set up a conda env and install geemap and [pygis](https://pygis.gishub.org/), which includes all the optional dependencies of geemap.

```bash
    conda create -n gee python
    conda activate gee
    conda install -c conda-forge mamba
    mamba install -c conda-forge geemap pygis
```

All the optional dependencies are listed in [requirements_dev.txt](https://github.com/giswqs/geemap/blob/master/requirements_dev.txt), which can be installed using one of the following:

-   `pip install geemap[all]`: installing all optional dependencies listed in [requirements_dev.txt](https://github.com/giswqs/geemap/blob/master/requirements_dev.txt).
-   `pip install geemap[backends]`: installing keplergl, pydeck.
-   `pip install geemap[lidar]`: installing ipygany, ipyvtklink, laspy, panel, pyntcloud[LAS], pyvista.
-   `pip install geemap[raster]`: installing localtileserver, rio-cogeo, rioxarray, netcdf4, xarray_leaflet.
-   `pip install geemap[sql]`: installing psycopg2, sqlalchemy.
-   `pip install geemap[streamlit]`: installing streamlit-folium.
-   `pip install geemap[vector]`: installing geopandas, osmnx.

Optionally, you can install some [Jupyter notebook extensions](https://github.com/ipython-contrib/jupyter_contrib_nbextensions), which can improve your productivity in the notebook environment. Some useful extensions include Table of Contents, Gist-it, Autopep8, Variable Inspector, etc. See this [post](https://towardsdatascience.com/jupyter-notebook-extensions-517fa69d2231) for more information.

```bash
    conda install jupyter_contrib_nbextensions -c conda-forge
```

Check the **YouTube** video below on how to install geemap using conda.

[![geemap](http://img.youtube.com/vi/h0pz3S6Tvx0/0.jpg)](http://www.youtube.com/watch?v=h0pz3S6Tvx0 "Install geemap")

## Install from GitHub

To install the development version from GitHub using [Git](https://git-scm.com/), run the following command in your terminal:

```bash
    pip install git+https://github.com/giswqs/geemap
```

## Upgrade geemap

If you have installed **geemap** before and want to upgrade to the latest version, you can run the following command in your terminal:

```bash
    pip install -U geemap
```

If you use conda, you can update geemap to the latest version by running the following command in your terminal:

```bash
    conda update -c conda-forge geemap
```

To install the development version from GitHub directly within Jupyter notebook without using Git, run the following code:

```python
    import geemap
    geemap.update_package()
```

## Use Docker

To use geemap in a Docker container, check out the following docker containers with geemap installed.

-   [gee-community/ee-jupyter-contrib](https://github.com/gee-community/ee-jupyter-contrib/tree/master/docker/gcp_ai_deep_learning_platform)
-   [bkavlak/geemap](https://hub.docker.com/r/bkavlak/geemap)
-   [giswqs/geemap](https://hub.docker.com/r/giswqs/geemap)
