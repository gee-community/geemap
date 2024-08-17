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
[Anaconda](https://www.anaconda.com/download) or [Miniconda](https://docs.anaconda.com/free/miniconda) installed on your computer, you can install geemap using the following command:

```bash
conda install geemap -c conda-forge
```

The geemap package has some optional dependencies, such as [GeoPandas](https://geopandas.org) and [localtileserver](https://github.com/banesullivan/localtileserver). These optional dependencies can be challenging to install on some computers, especially Windows. It is highly recommended that you create a fresh conda environment to install geemap. Follow the commands below to set up a conda env and install geemap:

```bash
conda create -n gee python=3.11
conda activate gee
conda install -n base mamba -c conda-forge
mamba install geemap -c conda-forge
mamba install geopandas localtileserver -c conda-forge
```

The optional dependencies can be installed using one of the following:

-   `pip install geemap[all]`: installing all optional dependencies.
-   `pip install geemap[backends]`: installing keplergl, pydeck.
-   `pip install geemap[lidar]`: installing ipygany, ipyvtklink, laspy, panel, pyntcloud[LAS], pyvista.
-   `pip install geemap[raster]`: installing localtileserver, rio-cogeo, rioxarray, netcdf4, xarray_leaflet.
-   `pip install geemap[sql]`: installing psycopg2, sqlalchemy.
-   `pip install geemap[streamlit]`: installing streamlit-folium.
-   `pip install geemap[vector]`: installing geopandas, osmnx.

Check the **YouTube** video below on how to install geemap using conda.

[![geemap](https://img.youtube.com/vi/h0pz3S6Tvx0/0.jpg)](https://www.youtube.com/watch?v=h0pz3S6Tvx0 "Install geemap")

## Install from GitHub

To install the development version from GitHub using [Git](https://git-scm.com/), run the following command in your terminal:

```bash
pip install git+https://github.com/gee-community/geemap
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

You can also use [Docker](https://hub.docker.com/r/gee-community/geemap/) to run geemap:

```bash
docker run -it -p 8888:8888 gee-community/geemap:latest
```
