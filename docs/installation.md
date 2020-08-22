Installation
============

To use **geemap**, you must first [sign up](https://earthengine.google.com/signup/) for a [Google Earth
Engine](https://earthengine.google.com/) account.

![signup](https://i.imgur.com/ng0FzUT.png)

**geemap** is available on [PyPI](https://pypi.org/project/geemap/). To install **geemap**, run this
command in your terminal:

    pip install geemap

**geemap** is also available on [conda-forge](https://anaconda.org/conda-forge/geemap). If you have
[Anaconda](https://www.anaconda.com/distribution/#download-section) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installed on your computer, you can create a conda Python environment to install geemap:

    conda create -n gee python=3.7
    conda activate gee
    conda install mamba -c conda-forge
    mamba install geemap -c conda-forge 

Optionally, you can install [Jupyter notebook extensions](https://github.com/ipython-contrib/jupyter_contrib_nbextensions), which can improve your productivity in the notebook environment. Some useful extensions include Table of Contents, Gist-it, Autopep8, Variable Inspector, etc. See this [post](https://towardsdatascience.com/jupyter-notebook-extensions-517fa69d2231) for more information.

    mamba install jupyter_contrib_nbextensions -c conda-forge 

If you have installed **geemap** before and want to upgrade to the
latest version, you can run the following command in your terminal:

    pip install -U geemap

If you use conda, you can update geemap to the latest version by running
the following command in your terminal:

    mamba update -c conda-forge geemap

To install the development version from GitHub using [Git](https://git-scm.com/), run the
following command in your terminal:

    pip install git+https://github.com/giswqs/geemap

To install the development version from GitHub directly within Jupyter
notebook without using Git, run the following code:

    import geemap
    geemap.update_package()

To use geemap in a Docker container, check out this [page](https://hub.docker.com/r/bkavlak/geemap).
