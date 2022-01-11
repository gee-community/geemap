# Installation

## Earth Engine Account

To use **geemap**, you must first [sign up](https://earthengine.google.com/signup/) for a [Google Earth Engine](https://earthengine.google.com/) account.
You cannot use Google Earth Engine unless your application has been approved. Once you receive the application approval email, you can log in to
the [Earth Engine Code Editor](https://code.earthengine.google.com/) to get familiar with the JavaScript API.

![signup](https://i.imgur.com/ng0FzUT.png)

## Install from PyPI

**geemap** is available on [PyPI](https://pypi.org/project/geemap/). To install **geemap**, run this command in your terminal:

```bash
    pip install geemap
```

## Install from conda-forge

**geemap** is also available on [conda-forge](https://anaconda.org/conda-forge/geemap). If you have
[Anaconda](https://www.anaconda.com/distribution/#download-section) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installed on your computer, you can install geemap using the following command:

```bash
    conda install geemap -c conda-forge
```

The geemap package has an optional dependency - [geopandas](https://geopandas.org/), which can be challenging to install on some computers, especially Windows. It is highly recommended that you create a fresh conda environment to install geopandas and geemap. Follow the commands below to set up a conda env and install geopandas, xarray_leaflet, and geemap.

```bash
    conda create -n gee python=3.9
    conda activate gee
    conda install geopandas
    conda install mamba -c conda-forge
    mamba install geemap localtileserver -c conda-forge
```

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
    mamba update -c conda-forge geemap
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
