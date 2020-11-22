# FAQ

## How do I report an issue or make a feature request

Please go to <https://github.com/giswqs/geemap/issues>.

## How do I cite geemap in publications

Wu, Q., (2020). geemap: A Python package for interactive mapping with Google Earth Engine. _The Journal of Open Source Software_, 5(51), 2305. <https://doi.org/10.21105/joss.02305>

```
Bibtex:
@article{wu2020geemap,
    title={geemap: A Python package for interactive mapping with Google Earth Engine},
    author={Wu, Qiusheng},
    journal={Journal of Open Source Software},
    volume={5},
    number={51},
    pages={2305},
    year={2020}
}
```

## Why does geemap use two plotting backends: folium and ipyleaflet

A key difference between [ipyleaflet](https://github.com/jupyter-widgets/ipyleaflet) and [folium](https://github.com/python-visualization/folium) is that ipyleaflet is built upon ipywidgets and allows bidirectional communication between the front-end and the backend enabling the use of the map to capture user input, while folium is meant for displaying static data only ([source](https://blog.jupyter.org/interactive-gis-in-jupyter-with-ipyleaflet-52f9657fa7a)). Note that [Google Colab](https://colab.research.google.com/) currently does not support ipyleaflet ([source](https://github.com/googlecolab/colabtools/issues/60#issuecomment-596225619)). Therefore, if you are using geemap
with Google Colab, you should use `import geemap.eefolium as geemap`. If you are using geemap with a local Jupyter notebook server, you can
use `import geemap`, which provides more functionalities for capturing user input (e.g., mouse-clicking and moving).

## Why the interactive map does not show up

If the interactive map does not show up on Jupyter notebook and JupyterLab, it is probably because the ipyleaflet extentsion is not installed properly.
For Jupyter notebook, try running the following two commands within your geemap conda environment:

```
jupyter nbextension install --py --symlink --sys-prefix ipyleaflet
jupyter nbextension enable --py --sys-prefix ipyleaflet
```

For JupyterLab, try running the following command within your geemap conda environment:

```
jupyter labextension install @jupyter-widgets/jupyterlab-manager jupyter-leaflet

```

## How to use geemap in countries where Google Services are blocked

If you are trying to use geemap in coutries where Gooogle Services are blocked (e.g., China), you will need a VPN. Use `geemap.set_proxy(port=your-port-number)` to connect to Earth Engine servers. Otherwise, you might encounter a connection timeout issue.

```
import geemap
geemap.set_proxy(port=your-port-number)
Map = geemap.Map()
Map
```

![](https://i.imgur.com/AHY9rT2.png)
