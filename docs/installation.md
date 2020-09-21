# Installation

## Earth Engine Account

To use **geemap**, you must first [sign up](https://earthengine.google.com/signup/) for a [Google Earth Engine](https://earthengine.google.com/) account. 
You cannot use Google Earth Engine unless your application has been approved. Once you receive the application approval email, you can log in to 
the [Earth Engine Code Editor](https://code.earthengine.google.com/) to get familiar with the JavaScript API.

![signup](https://i.imgur.com/ng0FzUT.png)

## Install from PyPI

**geemap** is available on [PyPI](https://pypi.org/project/geemap/). To install **geemap**, run this command in your terminal:

    pip install geemap

## Install from conda-forge

**geemap** is also available on [conda-forge](https://anaconda.org/conda-forge/geemap). If you have
[Anaconda](https://www.anaconda.com/distribution/#download-section) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installed on your computer, you can create a conda Python environment to install geemap:

    conda create -n gee python
    conda activate gee
    conda install mamba -c conda-forge
    mamba install geemap -c conda-forge

Optionally, you can install some [Jupyter notebook extensions](https://github.com/ipython-contrib/jupyter_contrib_nbextensions), which can improve your productivity in the notebook environment. Some useful extensions include Table of Contents, Gist-it, Autopep8, Variable Inspector, etc. See this [post](https://towardsdatascience.com/jupyter-notebook-extensions-517fa69d2231) for more information.

    conda install jupyter_contrib_nbextensions -c conda-forge

Check the **YouTube** video below on how to install geemap using conda.

[![geemap](http://img.youtube.com/vi/h0pz3S6Tvx0/0.jpg)](http://www.youtube.com/watch?v=h0pz3S6Tvx0 "Install geemap")

## Install from GitHub

To install the development version from GitHub using [Git](https://git-scm.com/), run the following command in your terminal:

    pip install git+https://github.com/giswqs/geemap

## Upgrade geemap

If you have installed **geemap** before and want to upgrade to the latest version, you can run the following command in your terminal:

    pip install -U geemap

If you use conda, you can update geemap to the latest version by running the following command in your terminal:

    mamba update -c conda-forge geemap

To install the development version from GitHub directly within Jupyter notebook without using Git, run the following code:

    import geemap
    geemap.update_package()

## Use Docker

To use geemap in a Docker container, check out this [page](https://hub.docker.com/r/bkavlak/geemap).
